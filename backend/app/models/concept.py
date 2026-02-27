"""
股票概念模块数据模型
Concept Models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class StockPositioning(str, enum.Enum):
    """股票在概念中的定位"""
    LEADER = "龙头"      # 板块龙头
    CORE = "中军"        # 中军/核心
    FOLLOWER = "补涨"    # 补涨股
    DEMON = "妖股"       # 妖股


class Concept(Base):
    """概念表 - 股票概念/板块"""
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # 概念名称
    description = Column(String(500))  # 概念描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    stocks = relationship("ConceptStock", back_populates="concept", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Concept(name='{self.name}')>"


class ConceptStock(Base):
    """概念股票关联表 - 股票与概念的多对多关系"""
    __tablename__ = "concept_stocks"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    stock_symbol = Column(String(10), nullable=False, index=True)  # 股票代码
    stock_name = Column(String(50))  # 股票名称（冗余存储）
    positioning = Column(String(20), default=StockPositioning.FOLLOWER.value)  # 定位：龙头/中军/补涨/妖股
    notes = Column(String(200))  # 备注
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    concept = relationship("Concept", back_populates="stocks")

    # 唯一约束：一个股票在一个概念中只能有一条记录
    __table_args__ = (
        UniqueConstraint('concept_id', 'stock_symbol', name='uix_concept_stock'),
    )

    def __repr__(self):
        return f"<ConceptStock(concept_id={self.concept_id}, symbol='{self.stock_symbol}', positioning='{self.positioning}')>"
