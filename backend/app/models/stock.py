"""
股票模型
Stock Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    sector = Column(String(50))  # 所属板块
    industry = Column(String(50))  # 所属行业
    market = Column(String(20))  # 市场（主板/创业板/科创板）
    is_active = Column(Boolean, default=True)  # 是否在交易

    # 扩展行情数据 (实时/今日)
    current_price = Column(Float)       # 最新价
    change_pct = Column(Float)          # 涨跌幅 (%)
    volume = Column(Float)              # 成交量 (手)
    amount = Column(Float)              # 成交额 (元)
    turnover_rate = Column(Float)       # 换手率 (%)
    pe_dynamic = Column(Float)          # 市盈率(动态)
    pb = Column(Float)                  # 市净率
    total_market_cap = Column(Float)    # 总市值 (元)
    circulating_market_cap = Column(Float) # 流通市值 (元)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class StockPrice(Base):
    """股票价格历史数据表"""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    amount = Column(Float)  # 成交额
    change_pct = Column(Float)  # 涨跌幅
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<StockPrice(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


class AnalysisReport(Base):
    """AI 分析报告表"""
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    report_date = Column(DateTime(timezone=True), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # daily/weekly/special
    content = Column(Text, nullable=False)  # 最终展示的 Markdown 报告
    data = Column(Text)  # 原始 JSON 格式的状态数据
    summary = Column(Text)  # 简要总结
    recommendation = Column(String(20))  # buy/hold/sell
    confidence = Column(Float)  # 置信度 0-1
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AnalysisReport(symbol='{self.symbol}', type='{self.report_type}', date='{self.report_date}')>"
