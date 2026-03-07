"""
行情数据 API 端点 - v1.1 东财+雪球双数据源
Market Data API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.services.market_data import get_market_data_service

router = APIRouter()


@router.get("/{symbol}/kline")
async def get_kline(
    symbol: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    获取 K 线数据

    Args:
        symbol: 股票代码
        period: 周期（daily, weekly, monthly）
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        K 线数据
    """
    try:
        # TODO: 调用数据服务获取 K 线
        return {
            "symbol": symbol,
            "period": period,
            "data": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/indicators")
async def get_indicators(symbol: str):
    """
    获取技术指标

    Args:
        symbol: 股票代码

    Returns:
        技术指标数据
    """
    try:
        # TODO: 计算技术指标
        return {
            "symbol": symbol,
            "indicators": {
                "ma5": None,
                "ma10": None,
                "ma20": None,
                "rsi": None,
                "macd": None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lhb")
async def get_dragon_tiger_list(date: Optional[str] = None):
    """
    获取龙虎榜数据

    Args:
        date: 日期

    Returns:
        龙虎榜数据
    """
    try:
        from app.utils.stock_tool import stock_tool

        lhb_data = stock_tool.get_lhb_data(date)
        return {
            "date": date,
            "data": lhb_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 新增接口 - 实时行情
# ============================================================

@router.get("/realtime/{symbol}")
async def get_realtime_quote(symbol: str):
    """
    获取单股实时行情（东财主力 + 雪球备用）

    Args:
        symbol: 股票代码，如 000001

    Returns:
        实时行情数据，包含 source 和 degraded 字段
    """
    try:
        market_service = get_market_data_service()
        data = market_service.get_realtime_price(symbol)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol} 的行情数据")
        
        return {
            "code": 200,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch-realtime")
async def get_batch_realtime_quotes(
    symbols: str = Query(..., description="股票代码列表，逗号分隔，如 000001,600000")
):
    """
    批量获取实时行情（东财批量接口）

    Args:
        symbols: 股票代码列表，逗号分隔

    Returns:
        批量实时行情数据
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        
        if len(symbol_list) > 100:
            raise HTTPException(status_code=400, detail="单次查询最多支持100只股票")
        
        market_service = get_market_data_service()
        data = market_service.batch_get_realtime_prices(symbol_list)
        
        # 统计降级情况
        degraded_count = sum(1 for d in data.values() if d.get("degraded"))
        
        return {
            "code": 200,
            "data": data,
            "meta": {
                "total": len(data),
                "requested": len(symbol_list),
                "degraded": degraded_count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_datasource_health():
    """
    获取数据源健康状态

    Returns:
        各数据源的熔断器状态和统计信息
    """
    try:
        market_service = get_market_data_service()
        health = market_service.get_datasource_health()
        
        # 汇总状态
        summary = {
            "all_healthy": all(
                stats["state"] == "closed" for stats in health.values()
            ),
            "total_sources": len(health),
            "healthy_sources": sum(
                1 for stats in health.values() if stats["state"] == "closed"
            )
        }
        
        return {
            "code": 200,
            "data": health,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
