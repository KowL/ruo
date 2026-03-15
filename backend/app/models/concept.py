"""
股票概念模块数据模型
Concept Models
"""
from sqlalchemy import Column, Integer, String, Enum, UniqueConstraint
from app.core.database import Base
import enum


class StockPositioning(str, enum.Enum):
    """股票在概念中的定位"""
    LEADER = "龙头"      # 板块龙头
    CORE = "中军"        # 中军/核心
    FOLLOWER = "补涨"    # 补涨股
    DEMON = "妖股"       # 妖股


class Concept(Base):
    """概念/题材表"""
    __tablename__ = "concept"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500))

    def __repr__(self):
        return f"<Concept(name='{self.name}')>"


class ConceptStock(Base):
    """概念股票关联表"""
    __tablename__ = "concept_stock"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, nullable=False, index=True)
    stock_symbol = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50))
    positioning = Column(String(20), default=StockPositioning.FOLLOWER.value)
    notes = Column(String(200))

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('concept_id', 'stock_symbol', name='uix_concept_stock'),
    )

    def __repr__(self):
        return f"<ConceptStock(concept_id={self.concept_id}, symbol='{self.stock_symbol}')>"
