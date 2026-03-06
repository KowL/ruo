"""
自选股票模型 - StockFavorite Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class StockFavorite(Base):
    """自选股票表"""
    __tablename__ = "stock_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("stock_groups.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<StockFavorite(id={self.id}, symbol='{self.symbol}', group_id={self.group_id})>"
