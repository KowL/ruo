"""
行情数据模型 - Market Price Models
拆分日线/周线/月线三张独立数据表

表名:
  - market_daily_price   日线行情
  - market_weekly_price  周线行情
  - market_monthly_price 月线行情
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base


class _BasePrice:
    """行情数据公共字段 Mixin"""

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)

    # OHLCV 核心数据
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    pre_close = Column(Float)               # 昨收价
    volume = Column(Float, nullable=False)   # 成交量（手）
    amount = Column(Float)                   # 成交额（元）
    change = Column(Float)                   # 涨跌额
    change_pct = Column(Float)              # 涨跌幅（%）
    turnover = Column(Float)                # 换手率（%）

    # 预计算均线（加速前端查询）
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    ma60 = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        """转换为字典格式（与原 KLineData.to_dict 兼容）"""
        return {
            'date': self.trade_date.strftime('%Y-%m-%d'),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'preClose': self.pre_close,
            'volume': self.volume,
            'amount': self.amount or 0,
            'change': self.change or 0,
            'changePct': self.change_pct or 0,
            'turnover': self.turnover or 0,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
        }


class DailyPrice(_BasePrice, Base):
    """日线行情数据表"""
    __tablename__ = "market_daily_price"

    __table_args__ = (
        UniqueConstraint('symbol', 'trade_date', name='uix_daily_symbol_date'),
        Index('ix_daily_symbol_date', 'symbol', 'trade_date'),
    )

    def __repr__(self):
        return f"<DailyPrice(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


class WeeklyPrice(_BasePrice, Base):
    """周线行情数据表"""
    __tablename__ = "market_weekly_price"

    __table_args__ = (
        UniqueConstraint('symbol', 'trade_date', name='uix_weekly_symbol_date'),
        Index('ix_weekly_symbol_date', 'symbol', 'trade_date'),
    )

    def __repr__(self):
        return f"<WeeklyPrice(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


class MonthlyPrice(_BasePrice, Base):
    """月线行情数据表"""
    __tablename__ = "market_monthly_price"

    __table_args__ = (
        UniqueConstraint('symbol', 'trade_date', name='uix_monthly_symbol_date'),
        Index('ix_monthly_symbol_date', 'symbol', 'trade_date'),
    )

    def __repr__(self):
        return f"<MonthlyPrice(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


# 周期 → 模型 映射（便于动态路由）
PERIOD_MODEL_MAP = {
    'daily': DailyPrice,
    'weekly': WeeklyPrice,
    'monthly': MonthlyPrice,
}
