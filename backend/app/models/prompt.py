"""
提示词模型
Prompt Model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Prompt(Base):
    """提示词表"""
    __tablename__ = "prompt"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # 名称
    description = Column(Text)  # 描述
    content = Column(Text, nullable=False)  # 提示词内容
    category = Column(String(50), default="用户分享")  # 分类：官方示例/用户分享
    is_official = Column(Boolean, default=False)  # 是否官方
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Prompt(id={self.id}, name='{self.name}', is_official={self.is_official})>"
