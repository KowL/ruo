"""
概念管理 API 端点
Concept Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.concept import Concept, ConceptStock, StockPositioning

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


class ConceptStockResponse(BaseModel):
    id: int
    stock_symbol: str
    stock_name: Optional[str]
    positioning: str
    notes: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ConceptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    stocks: List[ConceptStockResponse] = []

    class Config:
        from_attributes = True


class ConceptListItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    stock_count: int
    created_at: Optional[str]

    class Config:
        from_attributes = True


# ==================== API 端点 ====================

@router.get("/", summary="获取概念列表", tags=["概念管理"])
async def get_concepts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    获取概念列表

    **参数：**
    - skip: 跳过条数（分页）
    - limit: 返回条数（默认 100）

    **返回：**
    - 概念列表，包含每个概念的股票数量
    """
    concepts = db.query(Concept).offset(skip).limit(limit).all()
    
    result = []
    for concept in concepts:
        stock_count = db.query(ConceptStock).filter(ConceptStock.concept_id == concept.id).count()
        result.append({
            "id": concept.id,
            "name": concept.name,
            "description": concept.description,
            "stock_count": stock_count,
            "created_at": concept.created_at.isoformat() if concept.created_at else None
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
    """
    获取概念详情（包含股票列表）

    **参数：**
    - concept_id: 概念 ID

    **返回：**
    - 概念基本信息
    - 关联股票列表（含定位信息）
    """
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
            "created_at": concept.created_at.isoformat() if concept.created_at else None,
            "updated_at": concept.updated_at.isoformat() if concept.updated_at else None,
            "stocks": [
                {
                    "id": s.id,
                    "stock_symbol": s.stock_symbol,
                    "stock_name": s.stock_name,
                    "positioning": s.positioning,
                    "notes": s.notes,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in stocks
            ]
        }
    }


@router.post("/", summary="创建概念", tags=["概念管理"])
async def create_concept(
    concept_data: ConceptCreate,
    db: Session = Depends(get_db)
):
    """
    创建新概念

    **参数：**
    - name: 概念名称（必填，唯一）
    - description: 概念描述（可选）

    **返回：**
    - 创建的概念信息
    """
    # 检查名称是否已存在
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
            "description": concept.description,
            "created_at": concept.created_at.isoformat() if concept.created_at else None
        }
    }


@router.put("/{concept_id}", summary="更新概念", tags=["概念管理"])
async def update_concept(
    concept_id: int,
    concept_data: ConceptUpdate,
    db: Session = Depends(get_db)
):
    """
    更新概念信息

    **参数：**
    - concept_id: 概念 ID
    - name: 新名称（可选）
    - description: 新描述（可选）
    """
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    # 检查新名称是否冲突
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
            "description": concept.description,
            "updated_at": concept.updated_at.isoformat() if concept.updated_at else None
        }
    }


@router.delete("/{concept_id}", summary="删除概念", tags=["概念管理"])
async def delete_concept(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """
    删除概念（会同时删除关联的股票记录）

    **参数：**
    - concept_id: 概念 ID
    """
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
    """
    添加股票到概念

    **参数：**
    - concept_id: 概念 ID
    - stock_symbol: 股票代码
    - stock_name: 股票名称（可选）
    - positioning: 定位（可选，默认"补涨"）
    - notes: 备注（可选）
    """
    # 检查概念是否存在
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail=f"概念不存在: {concept_id}")
    
    # 验证定位值
    valid_positions = [p.value for p in StockPositioning]
    if stock_data.positioning not in valid_positions:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的定位值: {stock_data.positioning}，可选值: {valid_positions}"
        )
    
    # 检查是否已存在
    existing = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_data.stock_symbol
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"股票 {stock_data.stock_symbol} 已在概念 '{concept.name}' 中"
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
    """
    更新股票在概念中的定位

    **参数：**
    - concept_id: 概念 ID
    - stock_symbol: 股票代码
    - positioning: 新定位（可选）
    - notes: 新备注（可选）
    """
    concept_stock = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_symbol
    ).first()
    
    if not concept_stock:
        raise HTTPException(
            status_code=404, 
            detail=f"股票 {stock_symbol} 不在概念中"
        )
    
    # 验证定位值
    if stock_data.positioning:
        valid_positions = [p.value for p in StockPositioning]
        if stock_data.positioning not in valid_positions:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的定位值: {stock_data.positioning}，可选值: {valid_positions}"
            )
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
            "notes": concept_stock.notes,
            "updated_at": concept_stock.updated_at.isoformat() if concept_stock.updated_at else None
        }
    }


@router.delete("/{concept_id}/stocks/{stock_symbol}", summary="从概念中移除股票", tags=["概念管理"])
async def remove_stock_from_concept(
    concept_id: int,
    stock_symbol: str,
    db: Session = Depends(get_db)
):
    """
    从概念中移除股票

    **参数：**
    - concept_id: 概念 ID
    - stock_symbol: 股票代码
    """
    concept_stock = db.query(ConceptStock).filter(
        ConceptStock.concept_id == concept_id,
        ConceptStock.stock_symbol == stock_symbol
    ).first()
    
    if not concept_stock:
        raise HTTPException(
            status_code=404, 
            detail=f"股票 {stock_symbol} 不在概念中"
        )
    
    db.delete(concept_stock)
    db.commit()
    
    return {
        "status": "success",
        "message": f"股票 {stock_symbol} 已从概念中移除"
    }
