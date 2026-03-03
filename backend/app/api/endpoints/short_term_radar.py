"""
短线雷达 API 端点
Short-term Radar API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.short_term_radar import ShortTermRadarService

router = APIRouter()


@router.get("/auction-signals", summary="获取竞价爆点信号", tags=["短线雷达"])
async def get_auction_signals(
    db: Session = Depends(get_db)
):
    """
    获取竞价爆点信号（开盘前集合竞价）
    
    **筛选条件：**
    - 高开幅度 3-7%
    - 竞价成交额 > 1000万
    - 按信号强度排序
    
    **返回：**
    - symbol: 股票代码
    - name: 股票名称
    - openPct: 高开幅度
    - amount: 竞价成交额
    - signalStrength: 信号强度
    """
    try:
        service = ShortTermRadarService(db)
        result = service.get_auction_signals()
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取竞价信号失败: {str(e)}")


@router.get("/intraday-movers", summary="获取实时异动股票", tags=["短线雷达"])
async def get_intraday_movers(
    minChangePct: float = 5.0,
    db: Session = Depends(get_db)
):
    """
    获取实时异动股票
    
    **参数：**
    - minChangePct: 最小涨跌幅阈值（默认5%）
    
    **异动类型：**
    - limit_up: 涨停（>=9.5%）
    - strong_up: 强势上涨（5-9.5%）
    - limit_down: 跌停（<=-9.5%）
    - strong_down: 强势下跌（-5% to -9.5%）
    """
    try:
        service = ShortTermRadarService(db)
        result = service.get_intraday_movers(min_change_pct=minChangePct)
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取异动股票失败: {str(e)}")


@router.get("/limit-up-candidates", summary="获取涨停候选池", tags=["短线雷达"])
async def get_limit_up_candidates(
    db: Session = Depends(get_db)
):
    """
    获取涨停候选池
    
    **包含：**
    - 已涨停股票（涨停池）
    - 即将涨停股票（涨幅8-9.5%）
    """
    try:
        service = ShortTermRadarService(db)
        result = service.get_limit_up_candidates()
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停候选失败: {str(e)}")


@router.get("/dashboard", summary="获取短线雷达仪表盘", tags=["短线雷达"])
async def get_radar_dashboard(
    db: Session = Depends(get_db)
):
    """
    获取短线雷达完整仪表盘数据
    
    **返回：**
    - auctionSignals: 竞价爆点
    - intradayMovers: 实时异动
    - limitUpCandidates: 涨停候选
    - updateTime: 更新时间
    """
    try:
        service = ShortTermRadarService(db)
        result = service.get_radar_dashboard()
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘失败: {str(e)}")
