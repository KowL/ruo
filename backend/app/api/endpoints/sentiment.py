"""
市场情绪指数 API
Market Sentiment Index API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.sentiment import get_sentiment_service

router = APIRouter()


@router.get("/latest", summary="获取最新情绪指数", tags=["情绪指数"])
async def get_latest_sentiment(
    db: Session = Depends(get_db)
):
    """
    获取今日市场情绪指数
    
    **返回:**
    - date: 日期
    - index: 情绪指数 (0-100, 50为中性)
    - change: 较昨日变化
    - label: 情绪标签 (极度恐慌/恐慌/谨慎/中性/谨慎乐观/乐观/极度乐观)
    - bullish/bearish/neutral: 利好/利空/中性新闻数量
    - avg_score: 平均情感评分 (1-5)
    - news_count: 新闻总数
    - top_factors: 主要影响因素
    """
    try:
        service = get_sentiment_service(db)
        result = service.get_latest_sentiment()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取情绪指数失败: {str(e)}")


@router.get("/history", summary="获取情绪指数历史", tags=["情绪指数"])
async def get_sentiment_history(
    days: int = Query(7, ge=1, le=30, description="返回最近 N 天的数据"),
    db: Session = Depends(get_db)
):
    """
    获取历史情绪指数走势
    
    **参数:**
    - days: 天数 (1-30, 默认7)
    
    **返回:**
    - 日期列表，包含每日情绪指数和标签
    """
    try:
        service = get_sentiment_service(db)
        result = service.get_sentiment_history(days=days)
        return {
            "status": "success",
            "data": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@router.get("/daily-report/opening", summary="获取开盘简报", tags=["情绪指数"])
async def get_opening_report(
    db: Session = Depends(get_db)
):
    """
    获取 AI 生成的每日开盘简报
    
    **返回:**
    - date: 日期
    - type: opening
    - sentiment_index: 情绪指数
    - sentiment_label: 情绪标签
    - report: AI 生成的开盘分析文字
    - key_factors: 主要影响因素
    """
    try:
        service = get_sentiment_service(db)
        result = service.generate_daily_report(report_type='opening')
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成开盘简报失败: {str(e)}")


@router.get("/daily-report/closing", summary="获取收盘简报", tags=["情绪指数"])
async def get_closing_report(
    db: Session = Depends(get_db)
):
    """
    获取 AI 生成的每日收盘简报
    
    **返回:**
    - date: 日期
    - type: closing
    - sentiment_index: 情绪指数
    - sentiment_label: 情绪标签
    - report: AI 生成的收盘总结文字
    - key_factors: 主要影响因素
    """
    try:
        service = get_sentiment_service(db)
        result = service.generate_daily_report(report_type='closing')
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成收盘简报失败: {str(e)}")
