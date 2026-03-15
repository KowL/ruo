"""
预警设置模型
Alert/Notification Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class AlertRule(Base):
    """持仓预警规则表"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
    portfolio_id = Column(Integer, nullable=False)
    
    # 预警类型: price_change(涨跌幅), profit_loss(盈亏比例), target_price(目标价)
    alert_type = Column(String(20), nullable=False)
    
    # 触发条件
    threshold_value = Column(Float, nullable=False)  # 阈值
    compare_operator = Column(String(10), default=">=")  # 比较运算符: >=, <=, >, <
    
    # 是否启用
    is_active = Column(Integer, default=1)
    
    # 冷却时间(分钟) - 避免重复触发
    cooldown_minutes = Column(Integer, default=60)
    
    # 上次触发时间
    last_triggered_at = Column(DateTime(timezone=True))
    
    # 触发次数统计
    trigger_count = Column(Integer, default=0)
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AlertRule(portfolio_id={self.portfolio_id}, type={self.alert_type}, threshold={self.threshold_value})>"


class AlertLog(Base):
    """预警触发记录表"""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
    alert_rule_id = Column(Integer, nullable=False)
    portfolio_id = Column(Integer, nullable=False)
    
    # 触发时的数据快照
    symbol = Column(String(10), nullable=False)
    trigger_price = Column(Float, nullable=False)
    trigger_value = Column(Float, nullable=False)  # 实际触发的值
    
    # 预警消息
    message = Column(Text)
    
    # 是否已读
    is_read = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AlertLog(symbol={self.symbol}, price={self.trigger_price})>"
