"""
K线数据模型
KLine Data Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class KLineData(Base):
    """K线数据表 - 支持日线/周线/月线"""
    __tablename__ = "kline_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    period = Column(String(10), nullable=False, index=True)  # daily/weekly/monthly
    trade_date = Column(Date, nullable=False, index=True)  # 使用Date类型便于查询
    
    # K线数据
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)  # 成交量
    amount = Column(Float)  # 成交额
    change = Column(Float)  # 涨跌额
    change_pct = Column(Float)  # 涨跌幅
    turnover = Column(Float)  # 换手率
    
    # 预计算的均线指标（可选，加速查询）
    ma5 = Column(Float)   # 5日均线
    ma10 = Column(Float)  # 10日均线
    ma20 = Column(Float)  # 20日均线
    ma60 = Column(Float)  # 60日均线
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一约束：同一股票同一天同一周期只有一条记录
    __table_args__ = (
        UniqueConstraint('symbol', 'period', 'trade_date', name='uix_kline_symbol_period_date'),
    )

    def __repr__(self):
        return f"<KLineData(symbol='{self.symbol}', period='{self.period}', date='{self.trade_date}', close={self.close})>"

    def to_dict(self) -> dict:
        """转换为字典格式，与现有API兼容"""
        return {
            'date': self.trade_date.strftime('%Y-%m-%d'),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
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
