"""
持仓管理 API 端点 - MVP v0.1
Portfolio Management API Endpoints

实现功能：
- F-02: 新增/删除自选股
- F-03: 持仓信息录入
- F-04: 首页卡片展示
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.portfolio import PortfolioService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class PortfolioAddRequest(BaseModel):
    """添加持仓请求模型"""
    symbol: str = Field(..., description="股票代码，如 000001", min_length=6, max_length=6)
    costPrice: float = Field(..., description="成本价", gt=0)
    quantity: float = Field(..., description="持仓数量", gt=0)
    strategyTag: Optional[str] = Field(None, description="策略标签：打板/低吸/趋势")
    notes: Optional[str] = Field(None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "000001",
                "costPrice": 10.5,
                "quantity": 1000,
                "strategyTag": "趋势",
                "notes": "长期持有"
            }
        }


class PortfolioUpdateRequest(BaseModel):
    """更新持仓请求模型"""
    costPrice: Optional[float] = Field(None, description="成本价", gt=0)
    quantity: Optional[float] = Field(None, description="持仓数量", gt=0)
    strategyTag: Optional[str] = Field(None, description="策略标签")
    notes: Optional[str] = Field(None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "costPrice": 10.8,
                "quantity": 1200,
                "strategyTag": "低吸"
            }
        }


# ==================== API 端点 ====================

@router.post("/add", summary="添加持仓", tags=["持仓管理"])
async def add_portfolio(
    request: PortfolioAddRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    添加持仓

    **场景 A：用户添加一只持仓股**
    1. 用户点击"+"号 → 输入 `000001` → 系统返回"平安银行"
    2. 用户填写：成本 `10.5`，股数 `1000`，策略标签选 `趋势跟踪`
    3. 点击保存
    4. 首页列表出现卡片，显示当前盈亏状态

    **参数：**
    - symbol: 股票代码（6位数字）
    - cost_price: 成本价
    - quantity: 持仓数量
    - strategy_tag: 策略标签（打板/低吸/趋势）
    - notes: 备注（可选）

    **返回：**
    - 持仓详情，包含实时盈亏
    """
    try:
        service = PortfolioService(db)
        result = service.add_portfolio(
            symbol=request.symbol,
            cost_price=request.costPrice,
            quantity=request.quantity,
            strategy_tag=request.strategyTag,
            user_id=user_id,
            notes=request.notes
        )

        return {
            "status": "success",
            "message": f"持仓添加成功: {result['name']} ({result['symbol']})",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加持仓失败: {str(e)}")


@router.get("/list", summary="获取持仓列表", tags=["持仓管理"])
async def get_portfolio_list(
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取持仓列表（首页卡片展示）

    **返回数据包含：**
    - items: 持仓列表
      - 股票名称、代码
      - 成本价、当前价
      - 市值、盈亏金额、盈亏比
      - 策略标签
      - 是否有新消息
    - total_value: 总市值
    - total_cost: 总成本
    - total_profit_loss: 总盈亏
    - total_profit_loss_ratio: 总盈亏比
    """
    try:
        service = PortfolioService(db)
        result = service.get_portfolio_list(user_id=userId)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓列表失败: {str(e)}")


@router.get("/{portfolio_id}", summary="获取持仓详情", tags=["持仓管理"])
async def get_portfolio_detail(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个持仓详情

    **参数：**
    - portfolio_id: 持仓ID

    **返回：**
    - 持仓完整信息，包含实时盈亏
    """
    try:
        service = PortfolioService(db)
        result = service.get_portfolio_detail(portfolio_id)

        return {
            "status": "success",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓详情失败: {str(e)}")


@router.put("/{portfolio_id}", summary="更新持仓", tags=["持仓管理"])
async def update_portfolio(
    portfolio_id: int,
    request: PortfolioUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新持仓信息

    **参数：**
    - portfolio_id: 持仓ID
    - cost_price: 新的成本价（可选）
    - quantity: 新的持仓数量（可选）
    - strategy_tag: 新的策略标签（可选）
    - notes: 新的备注（可选）

    **返回：**
    - 更新后的持仓信息
    """
    try:
        service = PortfolioService(db)
        result = service.update_portfolio(
            portfolio_id=portfolio_id,
            cost_price=request.costPrice,
            quantity=request.quantity,
            strategy_tag=request.strategyTag,
            notes=request.notes
        )

        return {
            "status": "success",
            "message": "持仓更新成功",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新持仓失败: {str(e)}")


@router.delete("/{portfolio_id}", summary="删除持仓", tags=["持仓管理"])
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    删除持仓（软删除）

    **参数：**
    - portfolio_id: 持仓ID

    **返回：**
    - 删除结果
    """
    try:
        service = PortfolioService(db)
        success = service.delete_portfolio(portfolio_id)

        if success:
            return {
                "status": "success",
                "message": "持仓已删除"
            }
        else:
            raise HTTPException(status_code=500, detail="删除失败")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除持仓失败: {str(e)}")
