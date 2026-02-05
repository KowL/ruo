"""
股票数据同步任务 - Stock Tasks
负责定时同步股票基础信息
"""
import logging
from typing import Dict
import time
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session
import akshare as ak

logger = logging.getLogger(__name__)

@shared_task(name='app.tasks.stock_tasks.sync_stocks_task')
def sync_stocks_task() -> Dict:
    """
    同步所有A股基础信息及实时行情
    
    1. 调用 ak.stock_zh_a_spot_em() 获取所有A股实时数据
    2. 更新 stocks 表 (基础信息 + 行情数据)
    """
    try:
        from app.core.database import get_db
        from app.models.stock import Stock

        logger.info("[股票同步] 开始同步A股数据 (含行情)")
        
        # 1. 获取所有A股实时行情 (Sina接口)
        # columns: 代码, 名称, 最新价, 涨跌额, 涨跌幅, 买入, 卖出, 昨收, 今开, 最高, 最低, 成交量, 成交额, 时间戳
        # 注意: Sina接口可能不包含市盈率、市净率、市值等数据，需做容错处理
        start_time = time.time()
        # ak.stock_zh_a_spot() 返回的数据列名通常为: 代码, 名称, 最新价, 涨跌额, 涨跌幅, ...
        # 代码列可能包含前缀, 如 sh600000, sz000001
        df = ak.stock_zh_a_spot()
        
        if df.empty:
            logger.warning("[股票同步] 获取到的股票列表为空")
            return {"status": "empty"}

        logger.info(f"[股票同步] 获取到 {len(df)} 条数据，耗时: {time.time() - start_time:.2f}s")

        db: Session = next(get_db())
        
        added_count = 0
        updated_count = 0
        
        # 获取现有所有股票，构建字典映射 {symbol: stock_obj}
        # 数据库中保存的是纯数字代码
        existing_stocks = db.query(Stock).all()
        stock_map = {s.symbol: s for s in existing_stocks}
        
        batch_size = 500
        for i, (_, row) in enumerate(df.iterrows()):
            raw_symbol = str(row['代码'])
            # Sina返回的代码可能带字母前缀(sh/sz/bj)，去除非数字字符以获取纯数字ID
            import re
            symbol = re.sub(r'\D', '', raw_symbol)
            
            name = str(row['名称'])
            
            # 数据转换 (处理非数字情况)
            def safe_float(val):
                try:
                    return float(val)
                except:
                    return 0.0

            current_price = safe_float(row.get('最新价', 0))
            change_pct = safe_float(row.get('涨跌幅', 0)) # Sina通常有涨跌幅
            volume = safe_float(row.get('成交量', 0))
            amount = safe_float(row.get('成交额', 0))
            
            # Sina接口缺失的字段，默认为0
            turnover_rate = 0.0 
            pe_dynamic = 0.0
            pb = 0.0
            total_market_cap = 0.0
            circulating_market_cap = 0.0

            # 简单判断市场
            market = 'Unknown'
            if symbol.startswith('6'):
                market = 'SH' # 上海
            elif symbol.startswith('0') or symbol.startswith('3'):
                market = 'SZ' # 深圳
            elif symbol.startswith('8') or symbol.startswith('4'):
                market = 'BJ' # 北京
                
            if symbol in stock_map:
                # 更新
                stock = stock_map[symbol]
                # 更新基础信息 + 行情
                stock.name = name
                stock.current_price = current_price
                stock.change_pct = change_pct
                stock.volume = volume
                stock.amount = amount
                # stock.turnover_rate = turnover_rate # 缺失不更新，避免覆盖已有数据
                # stock.pe_dynamic = pe_dynamic
                # stock.pb = pb
                # stock.total_market_cap = total_market_cap
                # stock.circulating_market_cap = circulating_market_cap
                stock.updated_at = datetime.now()
                updated_count += 1
            else:
                # 新增
                new_stock = Stock(
                    symbol=symbol,
                    name=name,
                    market=market,
                    is_active=True,
                    current_price=current_price,
                    change_pct=change_pct,
                    volume=volume,
                    amount=amount,
                    turnover_rate=turnover_rate,
                    pe_dynamic=pe_dynamic,
                    pb=pb,
                    total_market_cap=total_market_cap,
                    circulating_market_cap=circulating_market_cap
                )
                db.add(new_stock)
                added_count += 1
            
            # 批量提交
            if (i + 1) % batch_size == 0:
                try:
                    db.commit()
                except Exception as e:
                    logger.error(f"[股票同步] 批量提交失败 (row {i}): {e}")
                    db.rollback()
        
        db.commit()
        db.close()
        
        logger.info(f"[股票同步] 完成。新增: {added_count}, 更新: {updated_count}, 总数: {len(df)}")

        return {
            "status": "success",
            "added": added_count,
            "updated": updated_count,
            "total": len(df)
        }

    except Exception as e:
        logger.error(f"[股票同步] 任务失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
