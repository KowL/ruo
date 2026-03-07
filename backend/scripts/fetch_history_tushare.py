#!/usr/bin/env python3
"""
行情历史数据拉取脚本 - 仅使用 Tushare (优化版，10000积分权限)
==========================================================
用途: 一次性拉取所有股票近10年的日线/周线/月线数据
特点: 
- 只使用 Tushare，不使用 akshare
- 支持批量获取（每次最多 8000 条数据）
- 10000 积分权限优化（每分钟 100 次调用）

用法:
    cd /Volumes/mm/项目/ruo/backend
    python scripts/fetch_history_tushare.py

环境变量:
    TUSHARE_TOKEN: Tushare API Token (必填)
    DATABASE_URL: 数据库连接字符串 (可选)
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
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)
print(env_file)
print(os.getenv("TUSHARE_TOKEN"))

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.market_price import DailyPrice, WeeklyPrice, MonthlyPrice

# =============================================================================
# 配置
# =============================================================================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fetch_history_tushare.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Tushare 代理配置
TUSHARE_PROXY_URL = 'http://lianghua.nanyangqiankun.top'

# 数据保留年限
DATA_RETENTION_YEARS = 10

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ruo_user:ruo_password@localhost:5432/ruo"
)

# Tushare 限制（10000 积分权限）
# 每分钟限制 100 次调用，每次最多返回 8000 条数据
RATE_LIMIT_PER_MINUTE = 100  # 每分钟最大调用次数
BATCH_SIZE_TUSHARE = 2       # 每次请求的股票数量（2只 * 10年约4000条，不超8000条限制）
MAX_ROWS_PER_REQUEST = 6000  # Tushare 每次最多返回 8000 条

# 批量插入大小
DB_BATCH_SIZE = 6000

# =============================================================================
# 数据库操作
# =============================================================================

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_size=10, max_overflow=20)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        
    @contextmanager
    def get_session(self):
        """获取数据库会话上下文"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_symbols(self) -> List[str]:
        """获取所有活跃股票代码"""
        with self.get_session() as session:
            result = session.execute(
                text("SELECT symbol FROM stocks WHERE is_active = true ORDER BY symbol")
            )
            return [row[0] for row in result.fetchall()]
    
    def get_existing_dates(self, symbol: str, period: str) -> Set[date]:
        """获取某股票某周期已存在的日期"""
        table_map = {
            'daily': 'market_daily_price',
            'weekly': 'market_weekly_price', 
            'monthly': 'market_monthly_price'
        }
        table = table_map.get(period)
        if not table:
            return set()
            
        with self.get_session() as session:
            result = session.execute(
                text(f"SELECT trade_date FROM {table} WHERE symbol = :symbol"),
                {"symbol": symbol}
            )
            return {row[0] for row in result.fetchall()}
    
    def bulk_insert_prices(self, period: str, data_list: List[Dict]) -> int:
        """批量插入价格数据，冲突时更新"""
        if not data_list:
            return 0
            
        model_map = {
            'daily': DailyPrice,
            'weekly': WeeklyPrice,
            'monthly': MonthlyPrice
        }
        model = model_map.get(period)
        if not model:
            return 0
        
        with self.get_session() as session:
            for i in range(0, len(data_list), DB_BATCH_SIZE):
                batch = data_list[i:i + DB_BATCH_SIZE]
                
                for item in batch:
                    stmt = insert(model).values(**item)
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
                            'turnover': stmt.excluded.turnover,
                            'updated_at': datetime.now()
                        }
                    )
                    session.execute(stmt)
                
                session.commit()
        
        return len(data_list)


# =============================================================================
# Tushare 数据获取（批量优化版）
# =============================================================================

class TushareDataFetcher:
    """Tushare 数据获取器 - 批量优化版"""
    
    def __init__(self, token: str):
        if not token:
            raise ValueError("TUSHARE_TOKEN 环境变量未设置")
        
        self.token = token
        self.pro = ts.pro_api(token)
        self.pro._DataApi__http_url = TUSHARE_PROXY_URL
        
        # 频率控制
        self.call_count = 0
        self.last_reset = time.time()
        
        logger.info(f"Tushare API 初始化完成，代理: {TUSHARE_PROXY_URL}")
        logger.info(f"权限: 10000 积分，每分钟限制 {RATE_LIMIT_PER_MINUTE} 次调用")
    
    def _rate_limit(self):
        """频率限制控制"""
        now = time.time()
        elapsed = now - self.last_reset
        
        # 每分钟重置计数
        if elapsed >= 60:
            self.call_count = 0
            self.last_reset = now
        
        # 如果达到限制，等待
        if self.call_count >= RATE_LIMIT_PER_MINUTE:
            sleep_time = 60 - elapsed + 1
            logger.info(f"达到频率限制，等待 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)
            self.call_count = 0
            self.last_reset = time.time()
    
    def symbol_to_ts_code(self, symbol: str) -> str:
        """将股票代码转换为 Tushare ts_code 格式"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"{symbol}.SZ"
        elif symbol.startswith('4') or symbol.startswith('8') or symbol.startswith('9'):
            return f"{symbol}.BJ"
        else:
            return symbol
    
    def ts_code_to_symbol(self, ts_code: str) -> str:
        """将 ts_code 转换回 symbol"""
        return ts_code.split('.')[0]
    
    def fetch_batch_data(
        self, 
        symbols: List[str], 
        period: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        批量获取多只股票数据
        
        Args:
            symbols: 股票代码列表
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            DataFrame 或 None
        """
        # 频率控制
        self._rate_limit()
        
        # 转换为 ts_code 列表
        ts_codes = [self.symbol_to_ts_code(s) for s in symbols]
        ts_code_str = ','.join(ts_codes)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.call_count += 1
                
                if period == 'daily':
                    df = self.pro.daily(
                        ts_code=ts_code_str,
                        start_date=start_date,
                        end_date=end_date
                    )
                elif period == 'weekly':
                    df = self.pro.weekly(
                        ts_code=ts_code_str,
                        start_date=start_date,
                        end_date=end_date
                    )
                elif period == 'monthly':
                    df = self.pro.monthly(
                        ts_code=ts_code_str,
                        start_date=start_date,
                        end_date=end_date
                    )
                else:
                    logger.error(f"不支持的周期: {period}")
                    return None
                
                if df is not None and not df.empty:
                    return df
                return pd.DataFrame()  # 空结果也返回空 DataFrame
                
            except Exception as e:
                logger.warning(f"Tushare 请求失败 ({attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
        
        return None


# =============================================================================
# 数据转换
# =============================================================================

def convert_tushare_to_model(
    df: pd.DataFrame, 
    existing_dates_map: Dict[str, Set[date]]
) -> Dict[str, List[Dict]]:
    """
    将 Tushare DataFrame 转换为模型数据，按周期分组
    
    Returns:
        {symbol: [data_items]}
    """
    result = {}
    
    for _, row in df.iterrows():
        try:
            # 解析股票代码和日期
            ts_code = str(row['ts_code'])
            symbol = ts_code.split('.')[0]
            trade_date_str = str(row['trade_date'])
            trade_date = datetime.strptime(trade_date_str, '%Y%m%d').date()
            
            # 检查是否已存在
            existing_dates = existing_dates_map.get(symbol, set())
            if trade_date in existing_dates:
                continue
            
            item = {
                'symbol': symbol,
                'trade_date': trade_date,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'pre_close': float(row.get('pre_close', 0)) if pd.notna(row.get('pre_close')) else None,
                'volume': float(row['vol']) * 100,  # 手 -> 股
                'amount': float(row['amount']) * 1000,  # 千元 -> 元
                'change': float(row.get('change', 0)) if pd.notna(row.get('change')) else None,
                'change_pct': float(row.get('pct_chg', 0)) if pd.notna(row.get('pct_chg')) else None,
                'turnover': 0.0,
                'ma5': None,
                'ma10': None,
                'ma20': None,
                'ma60': None,
            }
            
            if symbol not in result:
                result[symbol] = []
            result[symbol].append(item)
            
        except Exception as e:
            logger.debug(f"解析行失败: {e}")
            continue
    
    return result


# =============================================================================
# 主逻辑
# =============================================================================

def calculate_date_range(years: int = DATA_RETENTION_YEARS) -> Tuple[str, str]:
    """计算日期范围"""
    end_date = date.today()
    start_date = end_date.replace(year=end_date.year - years)
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')


def fetch_all_data_for_period(
    fetcher: TushareDataFetcher,
    db: DatabaseManager,
    symbols: List[str],
    period: str,
    start_date: str,
    end_date: str
) -> int:
    """
    批量获取某周期的所有股票数据
    
    Returns:
        保存的记录总数
    """
    logger.info(f"开始获取 {period} 数据，共 {len(symbols)} 只股票...")
    
    total_saved = 0
    batch_count = 0
    
    # 分批处理
    for i in range(0, len(symbols), BATCH_SIZE_TUSHARE):
        batch_symbols = symbols[i:i + BATCH_SIZE_TUSHARE]
        batch_num = i // BATCH_SIZE_TUSHARE + 1
        total_batches = (len(symbols) + BATCH_SIZE_TUSHARE - 1) // BATCH_SIZE_TUSHARE
        
        logger.info(f"  [{batch_num}/{total_batches}] 处理 {len(batch_symbols)} 只股票...")
        
        # 获取这批股票的已存在日期（优化：只查这批）
        existing_dates_map = {}
        for symbol in batch_symbols:
            existing_dates_map[symbol] = db.get_existing_dates(symbol, period)
        
        # 批量获取数据
        df = fetcher.fetch_batch_data(batch_symbols, period, start_date, end_date)
        
        if df is None:
            logger.error(f"    获取失败，跳过这批")
            continue
        
        logger.info(f"    获取到 {len(df)} 条数据")
        
        if df.empty:
            logger.info(f"    这批无新数据")
            continue
        
        # 转换数据
        data_by_symbol = convert_tushare_to_model(df, existing_dates_map)
        
        # 批量保存
        batch_saved = 0
        for symbol, data_list in data_by_symbol.items():
            if data_list:
                saved = db.bulk_insert_prices(period, data_list)
                batch_saved += saved
        
        total_saved += batch_saved
        batch_count += 1
        
        logger.info(f"    ✓ 保存 {batch_saved} 条数据")
        
        # 每 10 批显示一次总进度
        if batch_count % 10 == 0:
            progress = min(100, (i + len(batch_symbols)) / len(symbols) * 100)
            logger.info(f"  总进度: {progress:.1f}%，已保存 {total_saved} 条")
    
    return total_saved


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("行情历史数据拉取 - Tushare 优化版 (10000积分权限)")
    logger.info("=" * 70)
    
    # 检查环境变量
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        logger.error("错误: TUSHARE_TOKEN 环境变量未设置")
        sys.exit(1)
    
    # 初始化
    logger.info(f"数据库: {DATABASE_URL}")
    db = DatabaseManager(DATABASE_URL)
    fetcher = TushareDataFetcher(token)
    
    # 获取股票列表
    logger.info("获取股票列表...")
    symbols = db.get_all_symbols()
    if not symbols:
        logger.error("没有找到股票列表，请先初始化股票基础数据")
        sys.exit(1)
    
    logger.info(f"共 {len(symbols)} 只股票需要处理")
    logger.info(f"批量大小: 每批 {BATCH_SIZE_TUSHARE} 只")
    logger.info(f"频率限制: 每分钟 {RATE_LIMIT_PER_MINUTE} 次调用")
    
    # 计算日期范围
    start_date, end_date = calculate_date_range()
    logger.info(f"日期范围: {start_date} 至 {end_date}")
    
    # 统计
    stats = {
        'daily': 0,
        'weekly': 0,
        'monthly': 0
    }
    
    # 开始处理
    start_time = time.time()
    
    # 分别处理三个周期
    for period in ['daily', 'weekly', 'monthly']:
        logger.info("")
        logger.info(f"{'='*70}")
        logger.info(f"处理 {period} 周期")
        logger.info(f"{'='*70}")
        
        saved = fetch_all_data_for_period(
            fetcher, db, symbols, period, start_date, end_date
        )
        stats[period] = saved
        
        logger.info(f"{period} 完成，共保存 {saved} 条")
    
    # 总结
    elapsed = time.time() - start_time
    total = sum(stats.values())
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("处理完成!")
    logger.info("=" * 70)
    logger.info(f"总用时: {elapsed/60:.1f} 分钟 ({elapsed/3600:.2f} 小时)")
    logger.info(f"日线保存: {stats['daily']:,} 条")
    logger.info(f"周线保存: {stats['weekly']:,} 条")
    logger.info(f"月线保存: {stats['monthly']:,} 条")
    logger.info(f"总计: {total:,} 条")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
