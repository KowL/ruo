#!/usr/bin/env python3
"""
行情数据补全脚本 - 基于交易日历
==============================
用途: 对比 Tushare 交易日历，自动找出并补全已挂牌股票的历史缺口。
"""

import os
import sys
import time
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Set, Tuple
from contextlib import contextmanager

import tushare as ts
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.market_price import DailyPrice
from app.core.config import settings

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fill_history_gaps.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 配置
TUSHARE_PROXY_URL = 'http://lianghua.nanyangqiankun.top'
DATA_RETENTION_YEARS = 10
RATE_LIMIT_PER_MINUTE = 100

# 数据库配置 - 本地执行默认使用 localhost
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # 尝试构造本地 URL
    host = os.getenv("POSTGRES_HOST", "localhost")
    user = os.getenv("POSTGRES_USER", "ruo_user")
    pw = os.getenv("POSTGRES_PASSWORD", "ruo_password")
    db_name = os.getenv("POSTGRES_DB", "ruo")
    DATABASE_URL = f"postgresql://{user}:{pw}@{host}:5432/{db_name}"

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_active_symbols(self) -> List[str]:
        """获取所有活跃股票代码"""
        with self.get_session() as session:
            result = session.execute(
                text("SELECT symbol FROM stocks WHERE is_active = true ORDER BY symbol")
            )
            return [row[0] for row in result.fetchall()]

    def get_existing_dates(self, symbol: str) -> Set[date]:
        """获取某股票已有的交易日期"""
        with self.get_session() as session:
            result = session.execute(
                text("SELECT trade_date FROM market_daily_price WHERE symbol = :symbol"),
                {"symbol": symbol}
            )
            return {row[0] for row in result.fetchall()}

    def upsert_prices(self, data_list: List[Dict]) -> int:
        if not data_list: return 0
        with self.get_session() as session:
            for item in data_list:
                stmt = insert(DailyPrice).values(**item)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['symbol', 'trade_date'],
                    set_={
                        'open': stmt.excluded.open,
                        'high': stmt.excluded.high,
                        'low': stmt.excluded.low,
                        'close': stmt.excluded.close,
                        'pre_close': stmt.excluded.pre_close,
                        'volume': stmt.excluded.volume,
                        'amount': stmt.excluded.amount,
                        'change': stmt.excluded.change,
                        'change_pct': stmt.excluded.change_pct,
                        'updated_at': datetime.now()
                    }
                )
                session.execute(stmt)
            session.commit()
        return len(data_list)

class TushareFetcher:
    def __init__(self, token: str):
        self.pro = ts.pro_api(token)
        self.pro._DataApi__http_url = TUSHARE_PROXY_URL
        self.call_count = 0
        self.last_reset = time.time()

    def _rate_limit(self):
        now = time.time()
        if now - self.last_reset >= 60:
            self.call_count = 0
            self.last_reset = now
        if self.call_count >= RATE_LIMIT_PER_MINUTE:
            sleep_time = 60 - (now - self.last_reset) + 1
            logger.info(f"Rate limited, sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            self.call_count = 0
            self.last_reset = time.time()

    def get_trading_calendar(self, start_date: str, end_date: str) -> Set[date]:
        """获取交易日历"""
        self._rate_limit()
        self.call_count += 1
        df = self.pro.trade_cal(exchange='SSE', is_open='1', start_date=start_date, end_date=end_date)
        return {datetime.strptime(d, '%Y%m%d').date() for d in df['cal_date']}

    def get_stock_basic_mapping(self) -> Dict[str, date]:
        """获取所有股票的上市日期映射"""
        self._rate_limit()
        self.call_count += 1
        df = self.pro.stock_basic(fields='symbol,list_date')
        mapping = {}
        for _, row in df.iterrows():
            try:
                mapping[row['symbol']] = datetime.strptime(str(row['list_date']), '%Y%m%d').date()
            except:
                mapping[row['symbol']] = date(2000, 1, 1)
        return mapping

    def fetch_daily_batch(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        self._rate_limit()
        self.call_count += 1
        ts_codes = []
        for symbol in symbols:
            ts_code = f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ" if (symbol.startswith('0') or symbol.startswith('3')) else f"{symbol}.BJ"
            ts_codes.append(ts_code)
        try:
            return self.pro.daily(ts_code=','.join(ts_codes), start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"Fetch continuous daily for {symbols} failed: {e}")
            return pd.DataFrame()

def main():
    load_dotenv()
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        token = settings.TUSHARE_TOKEN
    if not token:
        logger.error("TUSHARE_TOKEN not found")
        return

    db = DatabaseManager(DATABASE_URL)
    fetcher = TushareFetcher(token)

    # 1. 准备全局交易日历和股票基本信息
    today_str = date.today().strftime('%Y%m%d')
    start_point_str = (date.today() - timedelta(days=365*DATA_RETENTION_YEARS)).strftime('%Y%m%d')
    logger.info(f"Fetching trading calendar from {start_point_str} to {today_str}...")
    global_cal = sorted(list(fetcher.get_trading_calendar(start_point_str, today_str)))
    logger.info(f"Trading days found: {len(global_cal)}")
    
    logger.info("Fetching stock basic info for list dates...")
    list_date_mapping = fetcher.get_stock_basic_mapping()
    
    # 2. 获取股票任务
    symbols = db.get_active_symbols()
    logger.info(f"Scanning {len(symbols)} stocks for gaps...")

    # 为了效率，我们按 50 只股票一组分析缺口。如果都有缺口，则取并集的区间进行拉取。
    batch_size = 50
    total_added = 0
    
    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i:i + batch_size]
        logger.info(f"Analyzing batch [{i//batch_size + 1}/{(len(symbols)+batch_size-1)//batch_size}] ({len(batch_symbols)} symbols)...")
        
        # 记录每只股票已有的日期和应有的日期
        all_missing_dates = set()
        stock_existing_dates = {}
        stock_expected_dates = {}
        
        for symbol in batch_symbols:
            list_date = list_date_mapping.get(symbol, date(2000, 1, 1))
            limit_date = date.today() - timedelta(days=365*DATA_RETENTION_YEARS)
            actual_start = max(list_date, limit_date)
            
            existing = db.get_existing_dates(symbol)
            stock_existing_dates[symbol] = existing
            
            expected = {d for d in global_cal if d >= actual_start and d < date.today()}
            stock_expected_dates[symbol] = expected
            
            missing = expected - existing
            if missing:
                all_missing_dates.update(missing)
        
        if not all_missing_dates:
            continue
            
        # 找出本批股票缺失日期的最小和最大值，形成大区间
        min_missing = min(all_missing_dates)
        max_missing = max(all_missing_dates)
        
        logger.info(f"  Gap range: {min_missing} to {max_missing}, total unique missing days across batch: {len(all_missing_dates)}")
        
        # 将大区间切分为更小的区间（比如每 2 年一段），避免单次结果超过 8000 条
        # 限制：50只股票 * 2年(500天) = 25000条，还是可能超。
        # 改为每半年一段更安全：50 * 120 = 6000条。
        cur_start = min_missing
        while cur_start <= max_missing:
            cur_end = min(cur_start + timedelta(days=180), max_missing)
            
            logger.info(f"  Fetching range {cur_start} to {cur_end} for batch...")
            df = fetcher.fetch_daily_batch(batch_symbols, cur_start.strftime('%Y%m%d'), cur_end.strftime('%Y%m%d'))
            
            if not df.empty:
                data_to_save = []
                for _, row in df.iterrows():
                    sym = row['ts_code'].split('.')[0]
                    t_date = datetime.strptime(str(row['trade_date']), '%Y%m%d').date()
                    
                    # 检查是否是真的缺失（因为是大区间，可能包含非缺失日期）
                    if t_date in stock_expected_dates.get(sym, set()) and t_date not in stock_existing_dates.get(sym, set()):
                        data_to_save.append({
                            'symbol': sym,
                            'trade_date': t_date,
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'pre_close': float(row.get('pre_close', 0)) if pd.notna(row.get('pre_close')) else 0,
                            'volume': float(row['vol']) * 100,
                            'amount': float(row['amount']) * 1000,
                            'change': float(row.get('change', 0)),
                            'change_pct': float(row.get('pct_chg', 0)),
                            'turnover': 0.0
                        })
                
                if data_to_save:
                    saved = db.upsert_prices(data_to_save)
                    total_added += saved
                    logger.info(f"    -> Added {saved} records.")
            
            cur_start = cur_end + timedelta(days=1)

    logger.info(f"Gap filling completed. Total records added: {total_added}")

if __name__ == "__main__":
    main()

    logger.info(f"Gap filling completed. Total records added: {total_added}")

if __name__ == "__main__":
    main()
