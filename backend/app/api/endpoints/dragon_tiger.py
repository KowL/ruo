"""
龙虎榜分析 API 端点
Dragon-Tiger List Analysis API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dragon_tiger import DragonTigerService

router = APIRouter()


@router.get("/daily", summary="获取每日龙虎榜", tags=["龙虎榜分析"])
async def get_daily_lhb(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取每日龙虎榜数据
    
    **参数：**
    - date: 日期（YYYY-MM-DD），默认为今天
    
    **返回：**
    - symbol: 股票代码
    - name: 股票名称
    - closePrice: 收盘价
    - changePct: 涨跌幅
    - netBuyAmount: 龙虎榜净买额
    - reason: 上榜原因
    """
    try:
        service = DragonTigerService(db)
        result = service.get_daily_lhb(date=date)
        
        return {
            "status": "success",
            "count": len(result),
            "date": date or "today",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙虎榜失败: {str(e)}")


@router.get("/stock/{symbol}", summary="获取个股龙虎榜详情", tags=["龙虎榜分析"])
async def get_stock_lhb(
    symbol: str,
    days: int = 5,
    db: Session = Depends(get_db)
):
    """
    获取个股近期龙虎榜详情
    
    **参数：**
    - symbol: 股票代码
    - days: 查询天数（默认5天）
    """
    try:
        service = DragonTigerService(db)
        result = service.get_stock_lhb_detail(symbol=symbol, days=days)
        
        return {
            "status": "success",
            "symbol": symbol,
            "days": days,
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取个股龙虎榜失败: {str(e)}")


@router.get("/institutional", summary="获取机构交易数据", tags=["龙虎榜分析"])
async def get_institutional_trading(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取机构专用席位交易数据
    
    **返回：**
    - symbol: 股票代码
    - netBuyAmount: 机构净买额
    - buyCount: 机构买入次数
    - sellCount: 机构卖出次数
    """
    try:
        service = DragonTigerService(db)
        result = service.get_institutional_trading(date=date)
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取机构数据失败: {str(e)}")


@router.get("/hot-seats", summary="获取热门游资席位", tags=["龙虎榜分析"])
async def get_hot_seats(
    days: int = 5,
    db: Session = Depends(get_db)
):
    """
    分析热门游资席位
    
    **参数：**
    - days: 分析天数（默认5天）
    
    **返回：**
    - seatName: 营业部名称
    - traderName: 游资名称（知名游资会识别）
    - netAmount: 净买入金额
    - isFamous: 是否为知名游资
    """
    try:
        service = DragonTigerService(db)
        result = service.analyze_hot_seats(days=days)
        
        return {
            "status": "success",
            "days": days,
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析热门席位失败: {str(e)}")


@router.get("/famous-traders", summary="获取知名游资动向", tags=["龙虎榜分析"])
async def get_famous_traders(
    days: int = 3,
    db: Session = Depends(get_db)
):
    """
    获取知名游资近期动向
    
    **识别游资：**
    - 拉萨军团、作手新一、桑田路、炒股养家
    - 赵老哥、章盟主、方新侠等
    
    **返回：**
    - traderName: 游资名称
    - netAmount: 净买入金额
    - buyCount/sellCount: 买卖次数
    """
    try:
        service = DragonTigerService(db)
        result = service.get_famous_traders_activity(days=days)
        
        return {
            "status": "success",
            "days": days,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取游资动向失败: {str(e)}")


@router.get("/market-sentiment", summary="获取龙虎榜市场情绪", tags=["龙虎榜分析"])
async def get_market_sentiment(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    基于龙虎榜分析市场情绪
    
    **情绪等级：**
    - very_positive: 非常积极（净买入 > 5亿）
    - positive: 积极（净买入 > 1亿）
    - neutral: 中性
    - negative: 消极（净卖出 > 1亿）
    """
    try:
        service = DragonTigerService(db)
        result = service.analyze_market_sentiment(date=date)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析市场情绪失败: {str(e)}")


@router.get("/dashboard", summary="获取龙虎榜仪表盘", tags=["龙虎榜分析"])
async def get_lhb_dashboard(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取龙虎榜完整仪表盘数据
    
    **返回：**
    - dailyData: 每日龙虎榜
    - institutionalData: 机构交易数据
    - hotSeats: 热门席位
    - famousTraders: 知名游资动向
    - marketSentiment: 市场情绪分析
    """
    try:
        service = DragonTigerService(db)
        result = service.get_lhb_dashboard(date=date)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘失败: {str(e)}")
