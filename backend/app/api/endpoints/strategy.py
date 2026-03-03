"""
策略管理 API 端点
Strategy Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.strategy import StrategyService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class CreateStrategyRequest(BaseModel):
    """创建策略请求"""
    name: str = Field(..., description="策略名称")
    strategyType: str = Field(..., description="策略类型: trend_following/mean_reversion/breakout/multi_factor")
    description: Optional[str] = Field(None, description="策略描述")
    entryRules: Optional[List[dict]] = Field(None, description="入场规则")
    exitRules: Optional[List[dict]] = Field(None, description="出场规则")
    positionRules: Optional[dict] = Field(None, description="仓位规则")
    riskRules: Optional[dict] = Field(None, description="风控规则")


class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    entryRules: Optional[List[dict]] = None
    exitRules: Optional[List[dict]] = None
    positionRules: Optional[dict] = None
    riskRules: Optional[dict] = None
    isActive: Optional[int] = None


class GenerateSignalsRequest(BaseModel):
    """生成信号请求"""
    symbols: List[str] = Field(..., description="股票代码列表")


# ==================== API 端点 ====================

@router.get("/templates", summary="获取策略模板", tags=["策略管理"])
async def get_strategy_templates(
    db: Session = Depends(get_db)
):
    """获取预设策略模板列表"""
    try:
        service = StrategyService(db)
        templates = service.get_strategy_templates()
        
        return {
            "status": "success",
            "data": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


@router.post("", summary="创建策略", tags=["策略管理"])
async def create_strategy(
    request: CreateStrategyRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    创建交易策略
    
    **策略类型：**
    - `trend_following`: 趋势跟踪
    - `mean_reversion`: 均值回归
    - `breakout`: 突破策略
    - `multi_factor`: 多因子选股
    """
    try:
        service = StrategyService(db)
        result = service.create_strategy(
            name=request.name,
            strategy_type=request.strategyType,
            description=request.description,
            entry_rules=request.entryRules,
            exit_rules=request.exitRules,
            position_rules=request.positionRules,
            risk_rules=request.riskRules,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "策略创建成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")


@router.get("", summary="获取策略列表", tags=["策略管理"])
async def get_strategies(
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取策略列表"""
    try:
        service = StrategyService(db)
        result = service.get_strategies(user_id=userId)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.get("/{strategy_id}", summary="获取策略详情", tags=["策略管理"])
async def get_strategy(
    strategy_id: int,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取策略详情"""
    try:
        service = StrategyService(db)
        result = service.get_strategy(strategy_id=strategy_id, user_id=userId)
        
        if not result:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.put("/{strategy_id}", summary="更新策略", tags=["策略管理"])
async def update_strategy(
    strategy_id: int,
    request: UpdateStrategyRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """更新策略"""
    try:
        service = StrategyService(db)
        result = service.update_strategy(
            strategy_id=strategy_id,
            name=request.name,
            description=request.description,
            entry_rules=request.entryRules,
            exit_rules=request.exitRules,
            position_rules=request.positionRules,
            risk_rules=request.riskRules,
            is_active=request.isActive,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "策略更新成功",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略失败: {str(e)}")


@router.delete("/{strategy_id}", summary="删除策略", tags=["策略管理"])
async def delete_strategy(
    strategy_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """删除策略"""
    try:
        service = StrategyService(db)
        service.delete_strategy(strategy_id=strategy_id, user_id=user_id)
        
        return {
            "status": "success",
            "message": "策略已删除"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除策略失败: {str(e)}")


@router.post("/{strategy_id}/signals", summary="生成策略信号", tags=["策略管理"])
async def generate_signals(
    strategy_id: int,
    request: GenerateSignalsRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    基于策略生成交易信号
    
    **说明：**
    - 分析指定股票列表
    - 根据策略规则生成买入/卖出信号
    - 包含建议仓位、止损止盈价
    """
    try:
        service = StrategyService(db)
        result = service.generate_signals(
            strategy_id=strategy_id,
            symbols=request.symbols,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成信号失败: {str(e)}")


@router.get("/{strategy_id}/signals", summary="获取策略信号", tags=["策略管理"])
async def get_signals(
    strategy_id: int,
    status: Optional[str] = None,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取策略信号列表"""
    try:
        service = StrategyService(db)
        result = service.get_signals(
            strategy_id=strategy_id,
            status=status,
            user_id=userId
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信号失败: {str(e)}")


@router.put("/signals/{signal_id}", summary="更新信号状态", tags=["策略管理"])
async def update_signal_status(
    signal_id: int,
    status: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """更新信号状态 (pending/executed/expired/cancelled)"""
    try:
        service = StrategyService(db)
        service.update_signal_status(
            signal_id=signal_id,
            status=status,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "信号状态已更新"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新信号失败: {str(e)}")
