"""
自选管理 API 端点 - Favorites API
功能：自选分组和自选股票的 CRUD 操作
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stock_favorite_service import StockFavoriteService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class StockGroupCreate(BaseModel):
    """创建分组请求模型"""
    name: str = Field(..., description="分组名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分组描述", max_length=200)
    isDefault: bool = Field(False, description="是否为默认分组")


class StockGroupUpdate(BaseModel):
    """更新分组请求模型"""
    name: Optional[str] = Field(None, description="分组名称", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分组描述", max_length=200)
    isDefault: Optional[bool] = Field(None, description="是否为默认分组")


class StockFavoriteAdd(BaseModel):
    """添加自选股票请求模型"""
    groupId: int = Field(..., description="分组ID")
    symbol: str = Field(..., description="股票代码", min_length=6, max_length=10)
    name: str = Field(..., description="股票名称")


class StockMove(BaseModel):
    """移动股票请求模型"""
    newGroupId: int = Field(..., description="目标分组ID")


# ==================== 分组管理 ====================

@router.get("/groups", summary="获取自选分组列表", tags=["自选管理"])
async def get_groups(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """获取用户自选分组列表"""
    try:
        service = StockFavoriteService(db)
        groups = service.get_groups(user_id)

        return {
            "status": "success",
            "data": groups
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分组列表失败: {str(e)}")


@router.post("/groups", summary="创建自选分组", tags=["自选管理"])
async def create_group(
    request: StockGroupCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """创建新的自选分组"""
    try:
        service = StockFavoriteService(db)
        group = service.create_group(
            user_id=user_id,
            name=request.name,
            description=request.description,
            is_default=request.isDefault
        )

        return {
            "status": "success",
            "message": f"分组 {request.name} 创建成功",
            "data": group
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/groups/{group_id}", summary="获取分组详情", tags=["自选管理"])
async def get_group(
    group_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """获取分组详情"""
    try:
        service = StockFavoriteService(db)
        group = service.get_group(group_id, user_id)

        if not group:
            raise HTTPException(status_code=404, detail=f"分组不存在: {group_id}")

        return {
            "status": "success",
            "data": group
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分组详情失败: {str(e)}")


@router.put("/groups/{group_id}", summary="更新分组", tags=["自选管理"])
async def update_group(
    group_id: int,
    request: StockGroupUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """更新分组信息"""
    try:
        service = StockFavoriteService(db)
        group = service.update_group(
            group_id=group_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            is_default=request.isDefault
        )

        return {
            "status": "success",
            "message": "分组更新成功",
            "data": group
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/groups/{group_id}", summary="删除分组", tags=["自选管理"])
async def delete_group(
    group_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """删除分组（同时删除组内自选股票）"""
    try:
        service = StockFavoriteService(db)
        service.delete_group(group_id, user_id)

        return {
            "status": "success",
            "message": "分组删除成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 自选股票管理 ====================

@router.get("/stocks", summary="获取自选股票列表", tags=["自选管理"])
async def get_stocks(
    group_id: Optional[int] = Query(None, description="分组ID"),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """获取自选股票列表（支持分组筛选）"""
    try:
        service = StockFavoriteService(db)
        stocks = service.get_stocks(user_id, group_id)

        return {
            "status": "success",
            "data": stocks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股票列表失败: {str(e)}")


@router.post("/stocks", summary="添加自选股票", tags=["自选管理"])
async def add_stock(
    request: StockFavoriteAdd,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """添加自选股票到指定分组"""
    try:
        service = StockFavoriteService(db)
        stock = service.add_stock(
            user_id=user_id,
            group_id=request.groupId,
            symbol=request.symbol,
            name=request.name
        )

        return {
            "status": "success",
            "message": f"股票 {request.symbol} 添加成功",
            "data": stock
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stocks/{favorite_id}", summary="删除自选股票", tags=["自选管理"])
async def delete_stock(
    favorite_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """删除自选股票"""
    try:
        service = StockFavoriteService(db)
        service.delete_stock(favorite_id, user_id)

        return {
            "status": "success",
            "message": "自选股票删除成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stocks/{favorite_id}/move", summary="移动自选股票", tags=["自选管理"])
async def move_stock(
    favorite_id: int,
    request: StockMove,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """移动自选股票到其他分组"""
    try:
        service = StockFavoriteService(db)
        stock = service.move_stock(
            favorite_id=favorite_id,
            user_id=user_id,
            new_group_id=request.newGroupId
        )

        return {
            "status": "success",
            "message": "股票移动成功",
            "data": stock
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/search", summary="搜索股票", tags=["自选管理"])
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词（代码或名称）"),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """搜索股票（从数据库）"""
    try:
        service = StockFavoriteService(db)
        stocks = service.search_stocks(keyword, user_id)

        return {
            "status": "success",
            "data": stocks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索股票失败: {str(e)}")
