"""
股票查询 API 端点 - MVP v0.1
Stock Query API Endpoints

实现功能：
- F-01: 基础行情接入
- F-02: 股票搜索（自动补全）
- F-07: K 线数据查询
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.market_data import get_market_data_service

router = APIRouter()

# 获取行情数据服务
market_service = get_market_data_service()


# ==================== API 端点 ====================

@router.get("/search", summary="搜索股票（自动补全）", tags=["股票查询"])
async def search_stock(
    keyword: str = Query(..., description="股票代码或名称，如 '000001' 或 '平安'", min_length=1)
):
    """
    搜索股票（自动补全）

    **使用场景：**
    - 用户输入股票代码或名称时，实时提示匹配结果
    - 支持模糊搜索

    **参数：**
    - keyword: 搜索关键词（代码或名称）

    **返回：**
    - 股票列表（最多 10 条）
    - 包含代码、名称、市场信息
    """
    try:
        results = market_service.search_stock(keyword)

        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索股票失败: {str(e)}")


@router.get("/info/{symbol}", summary="获取股票基本信息", tags=["股票查询"])
async def get_stock_info(
    symbol: str
):
    """
    获取股票基本信息

    **参数：**
    - symbol: 股票代码，如 '000001'

    **返回：**
    - 股票名称、行业、市场、上市时间等基本信息
    """
    try:
        info = market_service.get_stock_info(symbol)

        if not info:
            raise HTTPException(status_code=404, detail=f"股票不存在: {symbol}")

        return {
            "status": "success",
            "data": info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


@router.get("/realtime/{symbol}", summary="获取实时行情", tags=["股票查询"])
async def get_realtime_price(
    symbol: str
):
    """
    获取股票实时行情

    **参数：**
    - symbol: 股票代码

    **返回：**
    - 实时价格、涨跌幅、开高低收、成交量等
    """
    try:
        realtime = market_service.get_realtime_price(symbol)

        if not realtime:
            raise HTTPException(status_code=404, detail=f"未找到股票行情: {symbol}")

        return {
            "status": "success",
            "data": realtime
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {str(e)}")


@router.get("/kline/{symbol}", summary="获取 K 线数据", tags=["股票查询"])
async def get_kline_data(
    symbol: str,
    period: str = Query("daily", description="周期：daily/weekly/monthly"),
    limit: int = Query(60, description="返回数量", ge=1, le=500)
):
    """
    获取 K 线数据

    **参数：**
    - symbol: 股票代码
    - period: 周期（daily=日K, weekly=周K, monthly=月K）
    - limit: 返回数量（默认 60）

    **返回：**
    - K 线数据列表
    - 包含日期、开高低收、成交量
    """
    try:
        # 验证周期参数
        if period not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="周期参数错误，支持：daily/weekly/monthly")

        kline_data = market_service.get_kline_data(symbol, period, limit)

        if not kline_data:
            raise HTTPException(status_code=404, detail=f"未找到 K 线数据: {symbol}")

        return {
            "status": "success",
            "data": kline_data,
            "count": len(kline_data),
            "period": period
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 K 线数据失败: {str(e)}")


@router.post("/batch/realtime", summary="批量获取实时行情", tags=["股票查询"])
async def batch_get_realtime_prices(
    symbols: list[str]
):
    """
    批量获取实时行情

    **用途：**
    - 首页持仓列表一次性获取所有股票价格
    - 提高性能

    **参数：**
    - symbols: 股票代码列表

    **返回：**
    - {symbol: price_data} 字典
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="股票列表不能为空")

        if len(symbols) > 100:
            raise HTTPException(status_code=400, detail="一次最多查询 100 只股票")

        results = market_service.batch_get_realtime_prices(symbols)

        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量获取实时行情失败: {str(e)}")
