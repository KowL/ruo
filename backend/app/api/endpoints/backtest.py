"""
回测 API 端点
Backtest API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.backtest import BacktestService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class RunBacktestRequest(BaseModel):
    """运行回测请求"""
    strategyId: int = Field(..., description="策略ID")
    startDate: str = Field(..., description="开始日期 YYYY-MM-DD")
    endDate: str = Field(..., description="结束日期 YYYY-MM-DD")
    initialCapital: float = Field(default=1000000.0, description="初始资金")
    symbols: Optional[List[str]] = Field(None, description="回测股票列表")


class CompareBacktestsRequest(BaseModel):
    """对比回测请求"""
    backtestIds: List[int] = Field(..., description="回测ID列表")


# ==================== API 端点 ====================

@router.post("/run", summary="运行回测", tags=["回测系统"])
async def run_backtest(
    request: RunBacktestRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    运行策略回测
    
    **参数说明：**
    - strategyId: 要回测的策略ID
    - startDate/endDate: 回测时间范围
    - initialCapital: 初始资金（默认100万）
    - symbols: 指定回测股票，None则使用默认股票池
    
    **回测指标：**
    - 总收益率、年化收益率
    - 最大回撤
    - 夏普比率、索提诺比率
    - 胜率、盈亏比
    """
    try:
        service = BacktestService(db)
        result = service.run_backtest(
            strategy_id=request.strategyId,
            start_date=request.startDate,
            end_date=request.endDate,
            initial_capital=request.initialCapital,
            symbols=request.symbols,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "回测完成",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


@router.get("", summary="获取回测列表", tags=["回测系统"])
async def get_backtests(
    strategyId: Optional[int] = None,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取回测列表"""
    try:
        service = BacktestService(db)
        result = service.get_backtests(
            strategy_id=strategyId,
            user_id=userId
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回测失败: {str(e)}")


@router.get("/{backtest_id}", summary="获取回测详情", tags=["回测系统"])
async def get_backtest_detail(
    backtest_id: int,
    userId: int = 1,
    db: Session = Depends(get_db)
):
    """获取回测详情（包含交易明细、权益曲线）"""
    try:
        service = BacktestService(db)
        result = service.get_backtest_detail(
            backtest_id=backtest_id,
            user_id=userId
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="回测不存在")
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回测详情失败: {str(e)}")


@router.delete("/{backtest_id}", summary="删除回测", tags=["回测系统"])
async def delete_backtest(
    backtest_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """删除回测记录"""
    try:
        service = BacktestService(db)
        service.delete_backtest(
            backtest_id=backtest_id,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "message": "回测已删除"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除回测失败: {str(e)}")


@router.post("/compare", summary="对比回测", tags=["回测系统"])
async def compare_backtests(
    request: CompareBacktestsRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    对比多个回测结果
    
    **说明：**
    - 对比不同策略的回测表现
    - 综合评分选出最佳策略
    """
    try:
        service = BacktestService(db)
        result = service.compare_backtests(
            backtest_ids=request.backtestIds,
            user_id=user_id
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比回测失败: {str(e)}")
