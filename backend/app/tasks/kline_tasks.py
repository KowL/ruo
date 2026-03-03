"""
K线数据定时任务 - KLine Celery Tasks
每日自动更新K线数据到数据库
"""
import logging
from datetime import datetime, timedelta
from typing import List

from app.celery_config import celery_app
from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.services.market_data import get_market_data_service
from app.services.kline_service import get_kline_service
import akshare as ak

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.kline_tasks.update_portfolio_kline')
def update_portfolio_kline():
    """
    更新持仓股票的K线数据
    每晚8点执行，拉取当日最新数据
    """
    logger.info("开始更新持仓股票K线数据...")
    
    try:
        # 获取所有持仓股票
        db = next(get_db())
        portfolios = db.query(Portfolio).all()
        symbols = list(set([p.symbol for p in portfolios]))
        
        if not symbols:
            logger.info("没有持仓股票，跳过K线更新")
            return {"status": "success", "message": "无持仓股票", "updated": 0}
        
        logger.info(f"发现{len(symbols)}只持仓股票: {symbols}")
        
        # 更新每个股票的K线数据
        updated_count = 0
        periods = ['daily', 'weekly', 'monthly']
        
        for symbol in symbols:
            try:
                for period in periods:
                    # 调用market_data服务获取K线数据（会自动缓存到数据库）
                    market_service = get_market_data_service()
                    market_service.get_kline_data(symbol, period, limit=120)
                    updated_count += 1
                    
                logger.info(f"已更新K线数据: {symbol}")
                
            except Exception as e:
                logger.error(f"更新K线数据失败: {symbol}, 错误: {e}")
                continue
        
        logger.info(f"持仓股票K线数据更新完成，共更新{updated_count}个周期")
        return {
            "status": "success",
            "message": f"更新完成",
            "symbols": len(symbols),
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"更新持仓股票K线数据任务失败: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name='app.tasks.kline_tasks.update_hot_stocks_kline')
def update_hot_stocks_kline(top_n: int = 100):
    """
    更新热门股票的K线数据（成交量前N）
    每晚8:30执行
    
    Args:
        top_n: 更新前N只热门股票
    """
    logger.info(f"开始更新热门股票K线数据（前{top_n}）...")
    
    try:
        # 获取今日热门股票（成交量排名）
        try:
            spot_data = ak.stock_zh_a_spot_em()
            # 按成交量排序，取前N
            hot_stocks = spot_data.nlargest(top_n, '成交量')
            symbols = hot_stocks['代码'].tolist()
            
            logger.info(f"获取到{len(symbols)}只热门股票")
            
        except Exception as e:
            logger.error(f"获取热门股票列表失败: {e}")
            return {"status": "error", "message": f"获取热门股票失败: {e}"}
        
        # 更新每个热门股票的K线数据
        updated_count = 0
        periods = ['daily']  # 热门股票只更新日线（减少负载）
        
        for symbol in symbols:
            try:
                for period in periods:
                    market_service = get_market_data_service()
                    market_service.get_kline_data(symbol, period, limit=60)
                    updated_count += 1
                    
            except Exception as e:
                logger.warning(f"更新热门股票K线失败: {symbol}, 错误: {e}")
                continue
        
        logger.info(f"热门股票K线数据更新完成，共更新{updated_count}个周期")
        return {
            "status": "success",
            "message": f"更新完成",
            "symbols": len(symbols),
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"更新热门股票K线数据任务失败: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name='app.tasks.kline_tasks.update_single_stock_kline')
def update_single_stock_kline(symbol: str, periods: List[str] = None):
    """
    更新单只股票的K线数据
    用于手动触发或特定股票更新
    
    Args:
        symbol: 股票代码
        periods: 周期列表，默认 ['daily', 'weekly', 'monthly']
    """
    if periods is None:
        periods = ['daily', 'weekly', 'monthly']
    
    logger.info(f"开始更新股票K线数据: {symbol}, 周期: {periods}")
    
    try:
        updated_count = 0
        market_service = get_market_data_service()
        
        for period in periods:
            try:
                market_service.get_kline_data(symbol, period, limit=120)
                updated_count += 1
                logger.info(f"已更新 {symbol} {period} K线数据")
            except Exception as e:
                logger.error(f"更新 {symbol} {period} 失败: {e}")
                continue
        
        # 计算均线
        kline_service = get_kline_service()
        for period in periods:
            try:
                kline_service.calculate_mas(symbol, period)
            except Exception as e:
                logger.warning(f"计算均线失败: {symbol} {period}: {e}")
        
        return {
            "status": "success",
            "symbol": symbol,
            "periods": periods,
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"更新股票K线数据失败: {symbol}, 错误: {e}")
        return {"status": "error", "symbol": symbol, "message": str(e)}


@celery_app.task(name='app.tasks.kline_tasks.batch_update_kline')
def batch_update_kline(symbols: List[str], periods: List[str] = None):
    """
    批量更新股票K线数据
    
    Args:
        symbols: 股票代码列表
        periods: 周期列表
    """
    if periods is None:
        periods = ['daily']
    
    logger.info(f"开始批量更新{len(symbols)}只股票的K线数据...")
    
    success_count = 0
    failed_symbols = []
    
    for symbol in symbols:
        try:
            result = update_single_stock_kline(symbol, periods)
            if result.get("status") == "success":
                success_count += 1
            else:
                failed_symbols.append(symbol)
        except Exception as e:
            logger.error(f"批量更新失败: {symbol}: {e}")
            failed_symbols.append(symbol)
    
    logger.info(f"批量更新完成: 成功{success_count}/{len(symbols)}")
    return {
        "status": "success",
        "total": len(symbols),
        "success": success_count,
        "failed": len(failed_symbols),
        "failed_symbols": failed_symbols
    }


@celery_app.task(name='app.tasks.kline_tasks.cleanup_old_kline_data')
def cleanup_old_kline_data(days_to_keep: int = 365):
    """
    清理过旧的K线数据（保留最近N天）
    每月执行一次
    
    Args:
        days_to_keep: 保留最近多少天的数据
    """
    logger.info(f"开始清理{days_to_keep}天前的K线数据...")
    
    try:
        from app.models.kline import KLineData
        from sqlalchemy import delete
        
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
        
        db = next(get_db())
        
        # 删除旧数据
        stmt = delete(KLineData).where(KLineData.trade_date < cutoff_date)
        result = db.execute(stmt)
        db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"清理完成，共删除{deleted_count}条旧K线数据")
        
        return {
            "status": "success",
            "deleted": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理旧K线数据失败: {e}")
        return {"status": "error", "message": str(e)}
