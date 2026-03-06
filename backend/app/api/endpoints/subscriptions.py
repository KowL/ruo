"""
策略订阅 API 端点 - Subscriptions API
功能：策略订阅的 CRUD 操作
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.subscription_service import SubscriptionService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class SubscriptionCreate(BaseModel):
    """创建订阅请求模型"""
    strategyId: int = Field(..., description="策略ID")
    stockPoolType: str = Field("all", description="股票池类型: all/group/custom")
    stockGroupId: Optional[int] = Field(None, description="分组ID（当stockPoolType为group时使用）")
    customSymbols: Optional[List[str]] = Field(None, description="自定义股票列表（当stockPoolType为custom时使用）")
    notifyEnabled: bool = Field(True, description="是否启用通知")
    notifyChannels: Optional[List[str]] = Field(["websocket"], description="通知渠道")


class SubscriptionUpdate(BaseModel):
    """更新订阅请求模型"""
    stockPoolType: Optional[str] = Field(None, description="股票池类型: all/group/custom")
    stockGroupId: Optional[int] = Field(None, description="分组ID")
    customSymbols: Optional[List[str]] = Field(None, description="自定义股票列表")
    notifyEnabled: Optional[bool] = Field(None, description="是否启用通知")
    notifyChannels: Optional[List[str]] = Field(None, description="通知渠道")


# ==================== 订阅管理 ====================

@router.get("", summary="获取订阅列表", tags=["策略订阅"])
async def get_subscriptions(
    strategy_id: Optional[int] = Query(None, description="策略ID筛选"),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """获取用户订阅列表"""
    try:
        service = SubscriptionService(db)
        subscriptions = service.get_subscriptions(user_id, strategy_id)

        return {
            "status": "success",
            "data": subscriptions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅列表失败: {str(e)}")


@router.post("", summary="创建订阅", tags=["策略订阅"])
async def create_subscription(
    request: SubscriptionCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """订阅策略"""
    try:
        service = SubscriptionService(db)
        subscription = service.create_subscription(
            user_id=user_id,
            strategy_id=request.strategyId,
            stock_pool_type=request.stockPoolType,
            stock_group_id=request.stockGroupId,
            custom_symbols=request.customSymbols,
            notify_enabled=request.notifyEnabled,
            notify_channels=request.notifyChannels
        )

        return {
            "status": "success",
            "message": "订阅成功",
            "data": subscription
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subscription_id}", summary="获取订阅详情", tags=["策略订阅"])
async def get_subscription(
    subscription_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """获取订阅详情"""
    try:
        service = SubscriptionService(db)
        subscription = service.get_subscription(subscription_id, user_id)

        if not subscription:
            raise HTTPException(status_code=404, detail=f"订阅不存在: {subscription_id}")

        return {
            "status": "success",
            "data": subscription
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅详情失败: {str(e)}")


@router.put("/{subscription_id}", summary="更新订阅", tags=["策略订阅"])
async def update_subscription(
    subscription_id: int,
    request: SubscriptionUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """更新订阅设置"""
    try:
        service = SubscriptionService(db)
        subscription = service.update_subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            stock_pool_type=request.stockPoolType,
            stock_group_id=request.stockGroupId,
            custom_symbols=request.customSymbols,
            notify_enabled=request.notifyEnabled,
            notify_channels=request.notifyChannels
        )

        return {
            "status": "success",
            "message": "订阅更新成功",
            "data": subscription
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{subscription_id}", summary="取消订阅", tags=["策略订阅"])
async def delete_subscription(
    subscription_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """取消订阅"""
    try:
        service = SubscriptionService(db)
        service.delete_subscription(subscription_id, user_id)

        return {
            "status": "success",
            "message": "取消订阅成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
