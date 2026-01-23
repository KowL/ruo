"""
新闻模型
News Model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class StockNews(Base):
    """股票新闻表 - MVP v0.1"""
    __tablename__ = "stock_news"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)  # 股票代码
    title = Column(String(200), nullable=False)  # 新闻标题
    raw_content = Column(Text)  # 原始内容/摘要
    source = Column(String(100))  # 来源（如：财联社、新浪财经）
    url = Column(String(500))  # 新闻链接
    publish_time = Column(DateTime(timezone=True), nullable=False)  # 发布时间

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<StockNews(code='{self.stock_code}', title='{self.title[:30]}...')>"


class NewsAnalysis(Base):
    """AI 新闻分析结果表 - MVP v0.1"""
    __tablename__ = "news_analysis"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("stock_news.id"), nullable=False, unique=True)

    # AI 分析结果
    ai_summary = Column(Text, nullable=False)  # AI 生成的一句话摘要
    sentiment_label = Column(String(20), nullable=False)  # 利好/中性/利空
    sentiment_score = Column(Float)  # 情感分数 1-5 星

    # 元数据
    llm_model = Column(String(50))  # 使用的模型（如 deepseek-chat）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<NewsAnalysis(news_id={self.news_id}, sentiment='{self.sentiment_label}')>"
