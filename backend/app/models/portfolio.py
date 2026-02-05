"""
持仓模型
Portfolio Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Portfolio(Base):
    """持仓表 - MVP v0.1"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)  # MVP 默认用户
    symbol = Column(String(10), nullable=False, index=True)  # 股票代码，如 000001
    name = Column(String(50), nullable=False)  # 股票名称，如 平安银行
    market = Column(String(50))  # 市场：上海主板/深圳主板等
    cost_price = Column(Float, nullable=False)  # 成本价
    quantity = Column(Float, nullable=False)  # 持仓数量（股数）
    strategy_tag = Column(String(20))  # 策略标签：打板/低吸/趋势

    # 计算字段（可以在查询时计算）
    # current_price - 缓存的实时价格（由后台任务更新）
    current_price = Column(Float, default=0.0)
    
    # profit_loss - 盈亏金额 = (current_price - cost_price) * quantity
    # profit_loss_ratio - 盈亏比 = (current_price - cost_price) / cost_price

    notes = Column(Text)  # 备注
    is_active = Column(Integer, default=1)  # 是否激活（软删除）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Portfolio(symbol='{self.symbol}', name='{self.name}', quantity={self.quantity}, cost={self.cost_price})>"


class Trade(Base):
    """交易记录表"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(10), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)  # buy/sell
    shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # 总金额
    commission = Column(Float, default=0.0)  # 手续费
    trade_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Trade(symbol='{self.symbol}', type='{self.trade_type}', shares={self.shares})>"
