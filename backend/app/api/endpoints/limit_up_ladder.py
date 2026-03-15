"""
连板天梯 API 端点
Limit Up Ladder API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
import logging

from app.services.stock_data import stock_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/limit-up-ladder", summary="连板天梯", tags=["股票分析"])
async def get_limit_up_ladder(
    date: Optional[str] = Query(None, description="查询日期，格式YYYY-MM-DD")
) -> Dict:
    """
    获取连板天梯数据
    
    按连板数分组展示涨停股票
    """
    try:
        ladder = stock_service.get_limit_up_ladder(date=date)
        return {
            "success": True,
            "data": ladder,
            "count": ladder.get("total", 0)
        }
    except Exception as e:
        logger.error(f"获取连板天梯失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取连板天梯失败: {str(e)}")


@router.get("/limit-up", summary="今日涨停", tags=["股票分析"])
async def get_limit_up_stocks(
    date: Optional[str] = Query(None, description="查询日期，格式YYYY-MM-DD")
) -> Dict:
    """
    获取今日涨停股票列表
    """
    try:
        stocks = stock_service.get_limit_up_stocks(date=date)
        return {
            "success": True,
            "data": stocks,
            "count": len(stocks)
        }
    except Exception as e:
        logger.error(f"获取涨停股票失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取涨停股票失败: {str(e)}")


@router.get("/limit-up/ladder", summary="连板天梯(新)", tags=["股票分析"])
async def get_limit_up_ladder_v2(
    date: Optional[str] = Query(None, description="查询日期，格式YYYY-MM-DD")
) -> Dict:
    """
    获取连板天梯数据 (v2 版本)
    """
    try:
        ladder = stock_service.get_limit_up_ladder(date=date)
        return {
            "success": True,
            "data": ladder,
            "count": ladder.get("total", 0)
        }
    except Exception as e:
        logger.error(f"获取连板天梯失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取连板天梯失败: {str(e)}")
