"""
策略订阅模型 - StrategySubscription Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class StrategySubscription(Base):
    """策略订阅表"""
    __tablename__ = "strategy_subscription"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    strategy_id = Column(Integer, nullable=False, index=True)

    # 股票池类型: "all" | "group" | "custom"
    stock_pool_type = Column(String(20), default="all")

    # 当 stock_pool_type 为 "group" 时使用
    stock_group_id = Column(Integer, nullable=True)

    # 当 stock_pool_type 为 "custom" 时使用
    custom_symbols = Column(JSON, nullable=True)  # 自定义股票列表 ["000001", "000002"]

    # 通知设置
    notify_enabled = Column(Boolean, default=True)
    notify_channels = Column(JSON, default=["websocket"])  # ["feishu", "websocket"]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<StrategySubscription(id={self.id}, user_id={self.user_id}, strategy_id={self.strategy_id})>"
