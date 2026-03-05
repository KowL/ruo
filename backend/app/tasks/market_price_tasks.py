"""
行情数据定时任务 - Market Price Celery Tasks
每日通过 stock_tool 拉取行情数据，缓存至三张独立行情表，近10年保留
"""
import logging
import time
import random
from datetime import datetime, timedelta, date
from typing import List

from app.core.config import settings

from app.utils.stock_tool import stock_tool

from app.celery_config import celery_app
from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.stock import Stock
from app.services.market_price_service import MarketPriceService

logger = logging.getLogger(__name__)

# 保留近10年数据
DATA_RETENTION_YEARS = 10


def _get_start_date(years: int = DATA_RETENTION_YEARS) -> str:
    """返回近 N 年的起始日期字符串（格式：20160304）"""
    d = date.today().replace(year=date.today().year - years)
    return d.strftime('%Y%m%d')


def _get_all_symbols() -> List[str]:
    """获取所有股票代码"""
    db = next(get_db())
    try:
        stocks = db.query(Stock.symbol).filter(Stock.is_active == True).all()  # 只获取活跃股票
        return [s.symbol for s in stocks]
    finally:
        db.close()


def _fetch_and_save(symbol: str, period: str, service: MarketPriceService, start_date: str = None, end_date: str = None) -> int:
    """
    从数据源拉取指定股票/周期的数据并 upsert 到数据库

    Returns:
        保存的记录数
    """
    if not start_date:
        start_date = _get_start_date(DATA_RETENTION_YEARS)
    if not end_date:
        end_date = date.today().strftime('%Y%m%d')

    try:
        df = stock_tool.get_market_data_list(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )

        if df is None or df.empty:
            logger.debug(f"无数据: {symbol} {period}")
            return 0

        data = df.to_dict('records')

        saved = service.save_price_data(symbol, period, data)
        if saved > 0:
            service.calculate_mas(symbol, period)
        return saved

    except Exception as e:
        logger.error(f"任务拉取行情数据异常: {symbol} {period}, 错误: {e}")
        return 0


# ------------------------------------------------------------------ #
#  任务：日线更新（每天17:00）                                          #
# ------------------------------------------------------------------ #

@celery_app.task(name='app.tasks.market_price_tasks.sync_daily_price_task')
def sync_daily_price_task():
    """
    更新全量股票的日线行情（仅今日）
    每天 17:00 执行
    """
    logger.info("开始同步日线行情数据(今日)...")
    service = MarketPriceService()

    symbols = _get_all_symbols()

    if not symbols:
        logger.info("无需更新的股票")
        return {"status": "success", "updated": 0}

    today_str = date.today().strftime('%Y%m%d')
    success = failed = 0
    for symbol in symbols:
        try:
            saved = _fetch_and_save(symbol, 'daily', service, start_date=today_str, end_date=today_str)
            if saved >= 0:
                success += 1
        except Exception as e:
            logger.error(f"同步日线失败: {symbol}, {e}")
            failed += 1

    logger.info(f"日线同步完成: 成功 {success}/{len(symbols)}, 失败 {failed}")
    service.close()
    return {"status": "success", "period": "daily", "total": len(symbols), "success": success, "failed": failed}


# ------------------------------------------------------------------ #
#  任务：周线更新（每天17:00）                                        #
# ------------------------------------------------------------------ #

@celery_app.task(name='app.tasks.market_price_tasks.sync_weekly_price_task')
def sync_weekly_price_task():
    """
    更新全量股票的周线行情（仅本周）
    每天 17:00 执行
    """
    logger.info("开始同步周线行情数据(本周)...")
    service = MarketPriceService()
    symbols = _get_all_symbols()

    if not symbols:
        return {"status": "success", "updated": 0}

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start_date = monday.strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')

    success = failed = 0
    for symbol in symbols:
        try:
            saved = _fetch_and_save(symbol, 'weekly', service, start_date=start_date, end_date=end_date)
            if saved >= 0:
                success += 1
        except Exception as e:
            logger.error(f"同步周线失败: {symbol}, {e}")
            failed += 1

    logger.info(f"周线同步完成: {success}/{len(symbols)}")
    service.close()
    return {"status": "success", "period": "weekly", "total": len(symbols), "success": success, "failed": failed}


# ------------------------------------------------------------------ #
#  任务：月线更新（每天17:00）                                       #
# ------------------------------------------------------------------ #

@celery_app.task(name='app.tasks.market_price_tasks.sync_monthly_price_task')
def sync_monthly_price_task():
    """
    更新全量股票的月线行情（仅本月）
    每天 17:00 执行
    """
    logger.info("开始同步月线行情数据(本月)...")
    service = MarketPriceService()
    symbols = _get_all_symbols()

    if not symbols:
        return {"status": "success", "updated": 0}

    today = date.today()
    first_day = today.replace(day=1)
    start_date = first_day.strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')

    success = failed = 0
    for symbol in symbols:
        try:
            saved = _fetch_and_save(symbol, 'monthly', service, start_date=start_date, end_date=end_date)
            if saved >= 0:
                success += 1
        except Exception as e:
            logger.error(f"同步月线失败: {symbol}, {e}")
            failed += 1

    logger.info(f"月线同步完成: {success}/{len(symbols)}")
    service.close()
    return {"status": "success", "period": "monthly", "total": len(symbols), "success": success, "failed": failed}


# ------------------------------------------------------------------ #
#  任务：历史数据全量缓存（手动触发，仅执行1次）                            #
# ------------------------------------------------------------------ #

@celery_app.task(name='app.tasks.market_price_tasks.sync_historical_price_task')
def sync_historical_price_task():
    """
    全量获取过去10年的日线、周线、月线行情并缓存。
    执行时间较长，建议仅执行1次。
    """
    logger.info("开始同步历史行情数据 (近10年)...")
    service = MarketPriceService()
    symbols = _get_all_symbols()

    if not symbols:
        logger.info("无需更新的股票")
        return {"status": "success", "updated": 0}

    results = {'daily': 0, 'weekly': 0, 'monthly': 0}
    for i, symbol in enumerate(symbols):
        # 增加随机延迟 1-3 秒，避开频率限制
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        # 每处理 50 只股票，额外休息 30 秒
        if i > 0 and i % 50 == 0:
            logger.info(f"已同步 {i}/{len(symbols)} 只股票，深度休息 30s...")
            time.sleep(30)

        for period in ('daily', 'weekly', 'monthly'):
            try:
                saved = _fetch_and_save(symbol, period, service)
                if saved > 0:
                    results[period] += 1
            except Exception as e:
                logger.error(f"同步历史数据失败: {symbol} {period}, {e}")

    logger.info(f"历史数据同步完成: {results}")
    service.close()
    return {"status": "success", "total_symbols": len(symbols), "results": results}


# ------------------------------------------------------------------ #
#  任务：清理超10年旧数据（每月1日3:00）                               #
# ------------------------------------------------------------------ #

@celery_app.task(name='app.tasks.market_price_tasks.cleanup_old_price_task')
def cleanup_old_price_task(years: int = DATA_RETENTION_YEARS):
    """
    清理超过 N 年的行情数据，保持数据库精简
    每月1日 03:00 执行
    """
    logger.info(f"开始清理 {years} 年前的行情数据...")
    service = MarketPriceService()
    results = {}
    for period in ('daily', 'weekly', 'monthly'):
        deleted = service.cleanup_old_data(period, years)
        results[period] = deleted
        logger.info(f"清理 {period}: 删除 {deleted} 条")
    service.close()
    return {"status": "success", "deleted": results}
