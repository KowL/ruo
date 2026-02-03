"""
新闻表模型 - News Model
根据 DESIGN_NEWS.md 设计文档创建
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class News(Base):
    """新闻表 - 按设计文档规范"""
    __tablename__ = "news"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 来源和唯一标识
    source = Column(String(20), nullable=False, index=True)  # cls / xueqiu
    external_id = Column(String(100), nullable=False)  # 原始平台 ID (用于唯一性校验)

    # 新闻内容
    title = Column(String(500))  # 新闻标题 (部分快讯可能无标题)
    content = Column(Text)  # 新闻正文内容
    raw_json = Column(Text)  # 存储原始响应数据 (备查)

    # 关联和分析字段
    relation_stock = Column(Text)  # 新闻关联的股票代码，逗号分隔，如 "600519,000001"
    ai_analysis = Column(Text)  # AI 分析总结

    # 时间字段
    publish_time = Column(DateTime(timezone=True), nullable=False, index=True)  # 原始发布时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 系统入库时间

    # 唯一约束：防止同一条新闻被重复写入
    __table_args__ = (
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
        Index('idx_publish_time', 'publish_time'),
        Index('idx_source', 'source'),
    )

    def __repr__(self):
        return f"<News(source='{self.source}', external_id='{self.external_id}', title='{self.title[:30] if self.title else 'N/A'}...')>"
