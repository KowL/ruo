"""
自选分组模型 - StockGroup Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class StockGroup(Base):
    """自选分组表"""
    __tablename__ = "stock_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)  # 分组名称，如"科技股"、"龙头股"
    description = Column(String(200))  # 描述
    is_default = Column(Boolean, default=False)  # 是否为默认分组
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<StockGroup(id={self.id}, name='{self.name}', user_id={self.user_id})>"
