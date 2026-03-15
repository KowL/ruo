"""
概念/题材库 API 端点
统一管理：概念 CRUD + 题材库数据
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
import urllib.parse

from app.core.database import get_db
from app.models.concept import Concept, ConceptStock, StockPositioning
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic 模型 ====================

class ConceptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="概念名称")
    description: Optional[str] = Field(None, max_length=500, description="概念描述")


class ConceptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class ConceptStockCreate(BaseModel):
    stock_symbol: str = Field(..., min_length=1, max_length=10, description="股票代码")
    stock_name: Optional[str] = Field(None, max_length=50, description="股票名称")
    positioning: str = Field(default="补涨", description="定位：龙头/中军/补涨/妖股")
    notes: Optional[str] = Field(None, max_length=200, description="备注")


class ConceptStockUpdate(BaseModel):
    positioning: Optional[str] = Field(None, description="定位：龙头/中军/补涨/妖股")
    notes: Optional[str] = Field(None, max_length=200)


# ==================== 题材库 (行情统计) API ====================

@router.get("/ranking", summary="概念排行", tags=["题材库"])
async def get_concept_ranking(
    db: Session = Depends(get_db),
    sort_by: str = "hot_score",
    limit: int = 20
):
    """获取概念排行"""
    concepts = db.query(Concept).limit(limit).all()
    
    result = []
    for concept in concepts:
        stock_count = db.query(ConceptStock).filter(ConceptStock.concept_id == concept.id).count()
        leader_stock = db.query(ConceptStock).filter(
            ConceptStock.concept_id == concept.id,
            ConceptStock.positioning == "龙头"
        ).first()
        
        result.append({
            "id": concept.id,
            "theme_name": concept.name, # 前端期望 theme_name
            "name": concept.name,
            "description": concept.description or "",
            "stock_count": stock_count,
            "hot_score": 50,
            "limit_up_count": 0,
            "continuous_days": 0,
            "change_pct": 0,
            "lifecycle": "震荡期",
            "leader_stocks": [
                {
                    "name": leader_stock.stock_name or leader_stock.stock_symbol,
                    "positioning": leader_stock.positioning,
                    "change_pct": 0
                }
            ] if leader_stock else []
        })
    
    return {
        "status": "success",
        "data": result,
        "count": len(result),
        "sort_by": sort_by,
        "update_time": datetime.datetime.now().isoformat()
    }


@router.get("/distribution", summary="概念分布", tags=["题材库"])
async def get_concept_distribution(db: Session = Depends(get_db)):
    """获取概念分布统计"""
    all_concepts = db.query(Concept).all()
    
    distribution = []
    for concept in all_concepts[:12]:
        stock_count = db.query(ConceptStock).filter(
            ConceptStock.concept_id == concept.id
        ).count()
        
        distribution.append({
            "theme_name": concept.name,
            "limit_up_count": stock_count,
            "percentage": stock_count * 10 if stock_count > 0 else 0,
            "lifecycle": "震荡期",
            "hot_score": 50
        })
    
    lifecycle_stats = {
        "高潮期": 0,
        "发酵期": 0,
        "退潮期": 0,
        "震荡期": len(all_concepts)
    }
    
    return {
        "status": "success",
        "data": {
            "distribution": distribution,
            "lifecycle_stats": lifecycle_stats,
            "total_limit_up": 0,
            "theme_count": len(all_concepts)
        },
        "update_time": datetime.datetime.now().isoformat()
    }


# ==================== 概念管理 API ====================

@router.get("/list", summary="获取概念列表", tags=["概念管理"])
async def get_concepts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取概念列表，包含股票数量"""
    concepts = db.query(Concept).offset(skip).limit(limit).all()
    
    result = []
    for concept in concepts:
        stock_count = db.query(ConceptStock).filter(ConceptStock.concept_id == concept.id).count()
        result.append({
            "id": concept.id,
            "name": concept.name,
            "description": concept.description,
            "stock_count": stock_count,
            "change_pct": 0,
            "lead_stock": "",
            "lead_change": 0,
            "code": f"BK{concept.id:04d}",
            
        })
    
    return {
        "status": "success",
        "data": result,
        "count": len(result)
    }


@router.get("/{concept_id}", summary="获取概念详情", tags=["概念管理"])
async def get_concept(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """获取概念详情（包含股票列表）"""
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    stocks = db.query(ConceptStock).filter(ConceptStock.concept_id == concept_id).all()
    
    return {
        "status": "success",
        "data": {
            "id": concept.id,
            "name": concept.name,
            "description": concept.description,
            "stock_count": len(stocks),
            "stocks": [
                {
                    "id": s.id,
                    "symbol": s.stock_symbol,
                    "name": s.stock_name or s.stock_symbol,
                    "positioning": s.positioning,
                    "notes": s.notes,
                    "is_highlight": 0
                }
                for s in stocks
            ],
            
            "updated_at": concept.updated_at.isoformat() if concept.updated_at else None
        }
    }


@router.post("/", summary="创建概念", tags=["概念管理"])
async def create_concept(
    concept_data: ConceptCreate,
    db: Session = Depends(get_db)
):
    """创建新概念"""
    existing = db.query(Concept).filter(Concept.name == concept_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"概念已存在: {concept_data.name}")
    
    concept = Concept(
        name=concept_data.name,
        description=concept_data.description
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    
    return {
        "status": "success",
        "data": {
            "id": concept.id,
            "name": concept.name,
            "description": concept.description
        }
    }


@router.put("/{concept_id}", summary="更新概念", tags=["概念管理"])
async def update_concept(
    concept_id: int,
    concept_data: ConceptUpdate,
    db: Session = Depends(get_db)
):
    """更新概念信息"""
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    if concept_data.name and concept_data.name != concept.name:
        existing = db.query(Concept).filter(Concept.name == concept_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"概念名称已存在: {concept_data.name}")
        concept.name = concept_data.name
    
    if concept_data.description is not None:
        concept.description = concept_data.description
    
    db.commit()
    db.refresh(concept)
    
    return {
        "status": "success",
        "data": {
            "id": concept.id,
            "name": concept.name,
            "description": concept.description
        }
    }


@router.delete("/{concept_id}", summary="删除概念", tags=["概念管理"])
async def delete_concept(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """删除概念"""
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    db.delete(concept)
    db.commit()
    
    return {
        "status": "success",
        "message": f"概念 '{concept.name}' 已删除"
    }


# ==================== 概念股票管理 ====================

@router.post("/{concept_id}/stocks", summary="添加股票到概念", tags=["概念管理"])
async def add_stock_to_concept(
    concept_id: int,
    stock_data: ConceptStockCreate,
    db: Session = Depends(get_db)
):
    """添加股票到概念"""
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    valid_positions = [p.value for p in StockPositioning]
    if stock_data.positioning not in valid_positions:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的定位值: {stock_data.positioning}，可选值: {valid_positions}"
        )
    
    existing = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_data.stock_symbol
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"股票 {stock_data.stock_symbol} 已在概念中"
        )
    
    concept_stock = ConceptStock(
        concept_id=concept_id,
        stock_symbol=stock_data.stock_symbol,
        stock_name=stock_data.stock_name,
        positioning=stock_data.positioning,
        notes=stock_data.notes
    )
    db.add(concept_stock)
    db.commit()
    db.refresh(concept_stock)
    
    return {
        "status": "success",
        "data": {
            "id": concept_stock.id,
            "stock_symbol": concept_stock.stock_symbol,
            "stock_name": concept_stock.stock_name,
            "positioning": concept_stock.positioning,
            "notes": concept_stock.notes
        }
    }


@router.put("/{concept_id}/stocks/{stock_symbol}", summary="更新股票定位", tags=["概念管理"])
async def update_stock_positioning(
    concept_id: int,
    stock_symbol: str,
    stock_data: ConceptStockUpdate,
    db: Session = Depends(get_db)
):
    """更新股票在概念中的定位"""
    concept_stock = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_symbol
    ).first()
    
    if not concept_stock:
        raise HTTPException(status_code=404, detail=f"股票不存在")
    
    if stock_data.positioning:
        valid_positions = [p.value for p in StockPositioning]
        if stock_data.positioning not in valid_positions:
            raise HTTPException(status_code=400, detail=f"无效的定位值")
        concept_stock.positioning = stock_data.positioning
    
    if stock_data.notes is not None:
        concept_stock.notes = stock_data.notes
    
    db.commit()
    db.refresh(concept_stock)
    
    return {
        "status": "success",
        "data": {
            "id": concept_stock.id,
            "stock_symbol": concept_stock.stock_symbol,
            "stock_name": concept_stock.stock_name,
            "positioning": concept_stock.positioning,
            "notes": concept_stock.notes
        }
    }


@router.delete("/{concept_id}/stocks/{stock_symbol}", summary="从概念中移除股票", tags=["概念管理"])
async def remove_stock_from_concept(
    concept_id: int,
    stock_symbol: str,
    db: Session = Depends(get_db)
):
    """从概念中移除股票"""
    concept_stock = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_symbol
    ).first()
    
    if not concept_stock:
        raise HTTPException(status_code=404, detail=f"股票不存在")
    
    db.delete(concept_stock)
    db.commit()
    
    return {
        "status": "success",
        "message": f"股票已移除"
    }




@router.get("/{concept_name}", summary="概念详情", tags=["题材库"])
async def get_concept_detail(
    concept_name: str,
    db: Session = Depends(get_db)
):
    """获取概念详情及成分股"""
    decoded_name = urllib.parse.unquote(concept_name)
    
    concept = db.query(Concept).filter(Concept.name == decoded_name).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {decoded_name}")
    
    stocks = db.query(ConceptStock).filter(ConceptStock.concept_id == concept.id).all()
    
    # 区分龙头和成分股
    leader_stocks = []
    follower_stocks = []
    
    for s in stocks:
        stock_item = {
            "symbol": s.stock_symbol,
            "name": s.stock_name or s.stock_symbol,
            "positioning": s.positioning,
            "notes": s.notes,
            "change_pct": 0.0,
            "price": 0.0,
            "limit_up_days": 0,
            "reason": s.notes or "",
            "first_limit_time": "",
            "last_limit_time": "",
            "turnover": 0.0
        }
        if s.positioning == "龙头":
            leader_stocks.append(stock_item)
        else:
            follower_stocks.append(stock_item)
            
    return {
        "status": "success",
        "data": {
            "theme_name": concept.name,
            "theme_level": 1,
            "parent_theme": None,
            "hot_score": 50,
            "limit_up_count": len(leader_stocks),
            "continuous_days": 1,
            "leader_stocks": leader_stocks,
            "follower_stocks": follower_stocks,
            "lifecycle": "发酵期",
            "change_pct": 0.0,
            "turnover": 0.0,
            "fund_flow": 0.0,
            "update_time": datetime.datetime.now().isoformat()
        }
    }
