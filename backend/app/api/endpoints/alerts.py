"""
预警管理 API 端点
Alert Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.alert import AlertService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class AlertRuleCreateRequest(BaseModel):
    """创建预警规则请求"""
    portfolioId: int = Field(..., description="持仓ID")
    alertType: str = Field(..., description="预警类型: price_change/profit_loss/target_price")
    thresholdValue: float = Field(..., description="阈值")
    compareOperator: str = Field(default=">=", description="比较运算符: >=, <=, >, <")
    cooldownMinutes: int = Field(default=60, description="冷却时间(分钟)")
    notes: Optional[str] = Field(None, description="备注")


class AlertRuleUpdateRequest(BaseModel):
    """更新预警规则请求"""
    alertType: Optional[str] = Field(None, description="预警类型")
    thresholdValue: Optional[float] = Field(None, description="阈值")
    compareOperator: Optional[str] = Field(None, description="比较运算符")
    cooldownMinutes: Optional[int] = Field(None, description="冷却时间(分钟)")
    isActive: Optional[int] = Field(None, description="是否启用: 0/1")
    notes: Optional[str] = Field(None, description="备注")


# ==================== API 端点 ====================

@router.post("/rules", summary="创建预警规则", tags=["预警管理"])
async def create_alert_rule(
    request: AlertRuleCreateRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    创建持仓预警规则
    
    **预警类型说明:**
    - `price_change`: 涨跌幅预警（相对于成本价）
    - `profit_loss`: 盈亏比例预警
    - `target_price`: 目标价预警（当前价格触及设定值）
    
    **示例场景:**
    1. 设置止盈：profit_loss, >=, 15 (盈利15%时提醒)
    2. 设置止损：profit_loss, <=, -7 (亏损7%时提醒)
    3. 目标价：target_price, >=, 100 (股价达到100元时提醒)
    """
    try:
        service = AlertService(db)
        result = service.create_alert_rule(
            portfolio_id=request.portfolioId,
            alert_type=request.alertType,
            threshold_value=request.thresholdValue,
            compare_operator=request.compareOperator,
            cooldown_minutes=request.cooldownMinutes,
            notes=request.notes,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "预警规则创建成功",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建预警规则失败: {str(e)}")


@router.get("/rules", summary="获取预警规则列表", tags=["预警管理"])
async def get_alert_rules(
    portfolioId: Optional[int] = None,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取预警规则列表
    
    **参数:**
    - portfolioId: 按持仓ID筛选（可选）
    
    **返回:**
    - 预警规则列表，包含触发统计
    """
    try:
        service = AlertService(db)
        result = service.get_alert_rules(
            portfolio_id=portfolioId,
            user_id=userId
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警规则失败: {str(e)}")


@router.get("/rules/{rule_id}", summary="获取预警规则详情", tags=["预警管理"])
async def get_alert_rule_detail(
    rule_id: int,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取单个预警规则详情"""
    try:
        service = AlertService(db)
        rules = service.get_alert_rules(user_id=userId)
        rule = next((r for r in rules if r["id"] == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"预警规则不存在: {rule_id}")
        
        return {
            "status": "success",
            "data": rule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警规则失败: {str(e)}")


@router.put("/rules/{rule_id}", summary="更新预警规则", tags=["预警管理"])
async def update_alert_rule(
    rule_id: int,
    request: AlertRuleUpdateRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """更新预警规则"""
    try:
        service = AlertService(db)
        result = service.update_alert_rule(
            rule_id=rule_id,
            alert_type=request.alertType,
            threshold_value=request.thresholdValue,
            compare_operator=request.compareOperator,
            cooldown_minutes=request.cooldownMinutes,
            is_active=request.isActive,
            notes=request.notes,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "预警规则更新成功",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新预警规则失败: {str(e)}")


@router.delete("/rules/{rule_id}", summary="删除预警规则", tags=["预警管理"])
async def delete_alert_rule(
    rule_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """删除预警规则（软删除）"""
    try:
        service = AlertService(db)
        service.delete_alert_rule(rule_id=rule_id, user_id=user_id)
        
        return {
            "status": "success",
            "message": "预警规则已删除"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除预警规则失败: {str(e)}")


@router.post("/check", summary="手动检查预警", tags=["预警管理"])
async def check_alerts(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    手动触发预警检查
    
    **返回:**
    - 本次检查触发的所有预警列表
    """
    try:
        service = AlertService(db)
        triggered = service.check_alerts(user_id=user_id)
        
        return {
            "status": "success",
            "message": f"检查完成，触发 {len(triggered)} 条预警",
            "data": triggered
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查预警失败: {str(e)}")


@router.get("/logs", summary="获取预警记录", tags=["预警管理"])
async def get_alert_logs(
    portfolioId: Optional[int] = None,
    isRead: Optional[int] = None,
    limit: int = 50,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取预警触发记录
    
    **参数:**
    - portfolioId: 按持仓筛选
    - isRead: 按已读状态筛选 (0/1)
    - limit: 返回数量限制
    """
    try:
        service = AlertService(db)
        result = service.get_alert_logs(
            portfolio_id=portfolioId,
            is_read=isRead,
            limit=limit,
            user_id=userId
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警记录失败: {str(e)}")


@router.put("/logs/{log_id}/read", summary="标记预警已读", tags=["预警管理"])
async def mark_alert_read(
    log_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """标记预警记录为已读"""
    try:
        service = AlertService(db)
        service.mark_alert_read(log_id=log_id, user_id=user_id)
        
        return {
            "status": "success",
            "message": "已标记为已读"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记已读失败: {str(e)}")


@router.get("/unread-count", summary="获取未读预警数量", tags=["预警管理"])
async def get_unread_alert_count(
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取未读预警数量（用于小红点提示）"""
    try:
        service = AlertService(db)
        logs = service.get_alert_logs(is_read=0, limit=1000, user_id=userId)
        
        return {
            "status": "success",
            "data": {
                "unreadCount": len(logs)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未读数量失败: {str(e)}")
