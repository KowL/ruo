"""
策略模型 - Strategy Model
定义交易策略、回测记录、策略绩效
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Strategy(Base):
    """交易策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 策略类型: trend_following(趋势跟踪), mean_reversion(均值回归), breakout(突破), multi_factor(多因子)
    strategy_type = Column(String(50), nullable=False)
    
    # 策略配置 (JSON格式存储具体参数)
    config = Column(JSON, default={})
    
    # 入场条件规则
    entry_rules = Column(JSON, default=[])
    
    # 出场条件规则
    exit_rules = Column(JSON, default=[])
    
    # 仓位管理规则
    position_rules = Column(JSON, default={})
    
    # 风控规则
    risk_rules = Column(JSON, default={})
    
    # 是否启用
    is_active = Column(Integer, default=1)
    
    # 绩效统计 (缓存)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_return = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.strategy_type}')>"


class Backtest(Base):
    """回测记录表"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # 回测参数
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)
    initial_capital = Column(Float, nullable=False, default=1000000.0)
    
    # 回测结果
    final_capital = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    annualized_return = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    sortino_ratio = Column(Float, default=0.0)
    
    # 交易统计
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_profit = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    
    # 详细结果 (JSON)
    trades = Column(JSON, default=[])
    daily_returns = Column(JSON, default=[])
    equity_curve = Column(JSON, default=[])
    
    # 状态: running, completed, failed
    status = Column(String(20), default='running')
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Backtest(strategy_id={self.strategy_id}, return={self.total_return:.2f}%)>"


class StrategySignal(Base):
    """策略信号表 (实盘/模拟)"""
    __tablename__ = "strategy_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    symbol = Column(String(10), nullable=False)
    name = Column(String(50))
    
    # 信号类型: buy, sell, hold
    signal_type = Column(String(10), nullable=False)
    
    # 信号强度: 1-10
    strength = Column(Integer, default=5)
    
    # 建议仓位 (0-100%)
    suggested_position = Column(Float, default=0.0)
    
    # 触发价格
    trigger_price = Column(Float)
    
    # 止损价
    stop_loss_price = Column(Float)
    
    # 止盈价
    take_profit_price = Column(Float)
    
    # 信号原因
    reason = Column(Text)
    
    # 信号状态: pending, executed, expired, cancelled
    status = Column(String(20), default='pending')
    
    # 是否已读
    is_read = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expired_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<StrategySignal({self.symbol}: {self.signal_type})>"
