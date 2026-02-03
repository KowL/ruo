"""
新闻情报 API 端点 - News Intelligence API Endpoints
根据 DESIGN_NEWS.md 设计文档

只保留 News 相关接口，原有的 StockNews/NewsAnalysis 已移除
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.news import News

router = APIRouter()


# ==================== 新闻 API ====================

@router.get("/raw", summary="获取原始新闻", tags=["新闻"])
async def get_raw_news(
    source: Optional[str] = Query(None, description="来源过滤 (cls/xueqiu)"),
    hours: int = Query(24, description="最近 N 小时内的新闻", ge=1, le=168),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取新闻（从 news 表）

    **参数：**
    - source: 来源过滤 (cls/xueqiu)，不传则返回所有来源
    - hours: 最近 N 小时内的新闻
    - limit: 返回数量

    **返回：**
    - 新闻列表
    """
    try:
        # 计算时间范围
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # 构建查询
        query = db.query(News).filter(
            News.publish_time >= start_time
        )

        # 来源过滤
        if source:
            query = query.filter(News.source == source)

        # 排序和限制
        query = query.order_by(News.publish_time.desc()).limit(limit)

        news_list = query.all()

        # 转换为字典（使用驼峰命名）
        result = []
        for news in news_list:
            # 解析关联股票（逗号分隔转数组）
            relation_stocks = []
            if news.relation_stock:
                relation_stocks = [s.strip() for s in news.relation_stock.split(',') if s.strip()]

            news_dict = {
                'id': news.id,
                'source': news.source,
                'externalId': news.external_id,
                'title': news.title,
                'content': news.content,
                'rawJson': news.raw_json,
                'publishTime': news.publish_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if news.publish_time else None,
                'createdAt': news.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if news.created_at else None,
                'relationStock': news.relation_stock,  # 原始字符串，逗号分隔
                'relationStocks': relation_stocks,    # 解析后的数组
                'aiAnalysis': news.ai_analysis,
            }
            result.append(news_dict)

        return {
            "status": "success",
            "data": result,
            "count": len(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.get("/raw/cls", summary="获取财联社新闻", tags=["新闻"])
async def get_cls_news(
    hours: int = Query(24, description="最近 N 小时内的新闻", ge=1, le=168),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取财联社新闻快捷入口"""
    return await get_raw_news(source='cls', hours=hours, limit=limit, db=db)


@router.get("/raw/xueqiu", summary="获取雪球新闻", tags=["新闻"])
async def get_xueqiu_news(
    hours: int = Query(24, description="最近 N 小时内的新闻", ge=1, le=168),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取雪球新闻快捷入口"""
    return await get_raw_news(source='xueqiu', hours=hours, limit=limit, db=db)


@router.post("/raw/analyze/{news_id}", summary="AI 分析新闻", tags=["新闻"])
async def analyze_raw_news(
    news_id: int,
    ai_analysis: str = Query(..., description="AI 分析结果"),
    relation_stock: Optional[str] = Query(None, description="关联的股票代码，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    更新新闻的 AI 分析结果

    **参数：**
    - news_id: 新闻 ID
    - ai_analysis: AI 分析结果
    - relation_stock: 关联的股票代码（逗号分隔，如 "600519,000001"）

    **返回：**
    - 更新后的新闻
    """
    try:
        news = db.query(News).filter(News.id == news_id).first()
        if not news:
            raise HTTPException(status_code=404, detail="新闻不存在")

        # 更新字段
        news.ai_analysis = ai_analysis
        if relation_stock:
            news.relation_stock = relation_stock

        db.commit()
        db.refresh(news)

        # 解析关联股票
        relation_stocks = []
        if news.relation_stock:
            relation_stocks = [s.strip() for s in news.relation_stock.split(',') if s.strip()]

        return {
            "status": "success",
            "data": {
                'id': news.id,
                'source': news.source,
                'externalId': news.external_id,
                'title': news.title,
                'content': news.content,
                'aiAnalysis': news.ai_analysis,
                'relationStock': news.relation_stock,
                'relationStocks': relation_stocks,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"分析新闻失败: {str(e)}")
