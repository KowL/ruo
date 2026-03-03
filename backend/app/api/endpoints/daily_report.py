"""
每日简报 API 路由
Daily Report API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.services.daily_report import get_daily_report_service

router = APIRouter()


@router.get("/opening", summary="获取开盘简报", tags=["每日简报"])
async def get_opening_report(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取每日开盘简报
    
    **参数:**
    - date: 日期 (YYYY-MM-DD)，不传则返回今天
    
    **返回:**
    - sentiment: 情绪指数概览
    - top_sectors: 热门板块排行
    - suggestion: 开盘建议
    - key_points: 关键要点
    """
    try:
        service = get_daily_report_service(db)
        target_date = date.fromisoformat(date) if date else None
        result = service.generate_opening_report(target_date)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取开盘简报失败: {str(e)}")


@router.get("/closing", summary="获取收盘简报", tags=["每日简报"])
async def get_closing_report(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取每日收盘简报
    
    **参数:**
    - date: 日期 (YYYY-MM-DD)，不传则返回今天
    
    **返回:**
    - sentiment: 全天情绪回顾
    - fund_flow: 板块资金流向
    - limit_up: 涨停概念统计
    - outlook: 明日展望
    """
    try:
        service = get_daily_report_service(db)
        target_date = date.fromisoformat(date) if date else None
        result = service.generate_closing_report(target_date)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收盘简报失败: {str(e)}")
