"""
WebSocket推送任务 - WebSocket Push Tasks
实时推送价格更新、市场概览等
"""
import logging
import asyncio
from celery import shared_task
from typing import List

from app.core.websocket_manager import manager
from app.services.market_data import get_market_data_service

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.websocket_tasks.broadcast_price_update')
def broadcast_price_update(symbol: str, price_data: dict):
    """
    广播价格更新
    
    Args:
        symbol: 股票代码
        price_data: 价格数据
    """
    try:
        # 在Celery中需要创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            manager.broadcast_to_symbol(symbol, {
                "channel": "price",
                "symbol": symbol,
                "data": price_data
            })
        )
        loop.close()
        
        logger.debug(f"价格更新已广播: {symbol}")
        return {"status": "success", "symbol": symbol}
        
    except Exception as e:
        logger.error(f"广播价格更新失败: {symbol}, {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name='app.tasks.websocket_tasks.broadcast_market_overview')
def broadcast_market_overview():
    """广播市场概览更新"""
    try:
        market_service = get_market_data_service()
        
        # 获取市场概览数据
        # 这里简化处理，实际可以从market_service获取
        overview = {
            "up_count": 0,
            "down_count": 0,
            "flat_count": 0,
            "total_volume": 0,
            "total_amount": 0
        }
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            manager.broadcast({
                "channel": "market_overview",
                "data": overview
            })
        )
        loop.close()
        
        logger.debug("市场概览已广播")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"广播市场概览失败: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name='app.tasks.websocket_tasks.push_portfolio_updates')
def push_portfolio_updates(symbols: List[str]):
    """
    推送持仓股票价格更新
    
    Args:
        symbols: 股票代码列表
    """
    try:
        market_service = get_market_data_service()
        
        # 批量获取价格
        prices = market_service.batch_get_realtime_prices(symbols)
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 逐个推送
        for symbol, price_data in prices.items():
            try:
                loop.run_until_complete(
                    manager.broadcast_to_symbol(symbol, {
                        "channel": "price",
                        "symbol": symbol,
                        "data": price_data
                    })
                )
            except Exception as e:
                logger.warning(f"推送价格失败: {symbol}, {e}")
        
        loop.close()
        
        return {
            "status": "success",
            "updated_count": len(prices)
        }
        
    except Exception as e:
        logger.error(f"推送持仓更新失败: {e}")
        return {"status": "error", "message": str(e)}
