"""
股票分析 API 端点
Stock Analysis API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.post("/analyze/{symbol}")
async def analyze_stock(
    symbol: str,
    date: Optional[str] = None
):
    """
    分析单只股票

    Args:
        symbol: 股票代码
        date: 分析日期，格式 YYYY-MM-DD，默认为今天

    Returns:
        分析结果
    """
    try:
        # TODO: 调用 LLM Agent 进行分析
        # from app.llm_agent.graphs.stock_analysis_workflow import run_stock_analysis
        # result = await run_stock_analysis(symbol, date)

        return {
            "symbol": symbol,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "status": "success",
            "message": "分析功能开发中"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limit-up")
async def get_limit_up_stocks(date: Optional[str] = None):
    """
    获取涨停股票列表

    Args:
        date: 日期，格式 YYYY-MM-DD

    Returns:
        涨停股票列表
    """
    try:
        from app.services.data_fetch import get_limit_up_stocks as fetch_limit_up

        stocks = fetch_limit_up(date)
        return {
            "date": date,
            "count": len(stocks) if stocks else 0,
            "stocks": stocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/{symbol}")
async def get_realtime_price(symbol: str):
    """
    获取股票实时价格

    Args:
        symbol: 股票代码

    Returns:
        实时价格信息
    """
    try:
        from app.services.data_fetch import get_stock_price_realtime

        price_data = get_stock_price_realtime(symbol)
        return {
            "symbol": symbol,
            "data": price_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
