"""
市场情绪与仪表盘 API
Market Sentiment & Dashboard API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

from app.core.database import get_db
from app.models.news import News
from app.models.portfolio import Portfolio
from app.models.concept import Concept, ConceptStock
from app.services.sentiment import get_sentiment_service

router = APIRouter()


def calculate_news_sentiment(news_list: List[News]) -> Dict[str, Any]:
    """
    基于新闻计算情绪得分
    简版：基于关键词匹配计算情绪
    """
    if not news_list:
        return {"score": 50, "label": "中性", "description": "暂无新闻数据"}

    positive_keywords = [
        "上涨", "增长", "利好", "突破", "创新", "合作", "收购", "业绩", "盈利",
        "扩张", "投资", "发展", "机会", "优势", "领先", "成功", "提升", "涨停",
        "新高", "强势", "反弹", "回升", "回暖", "火爆", "热潮", "追捧"
    ]

    negative_keywords = [
        "下跌", "下降", "利空", "风险", "亏损", "减少", "困难", "问题", "危机",
        "调查", "处罚", "违规", "退市", "停牌", "暂停", "警告", "下调", "跌停",
        "新低", "弱势", "暴跌", "重挫", "抛售", "恐慌", "跳水", "闪崩"
    ]

    total_score = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for news in news_list:
        content = (news.title or "") + " " + (news.content or "")
        pos_score = sum(1 for kw in positive_keywords if kw in content)
        neg_score = sum(1 for kw in negative_keywords if kw in content)

        if pos_score > neg_score:
            positive_count += 1
            total_score += min(50 + pos_score * 10, 90)
        elif neg_score > pos_score:
            negative_count += 1
            total_score += max(50 - neg_score * 10, 10)
        else:
            neutral_count += 1
            total_score += 50

    avg_score = total_score / len(news_list) if news_list else 50

    # 确定标签和描述
    if avg_score >= 70:
        label = "乐观"
        description = "市场情绪高涨，多头占优"
    elif avg_score >= 55:
        label = "偏乐观"
        description = "市场情绪偏暖，谨慎乐观"
    elif avg_score >= 45:
        label = "中性"
        description = "市场情绪中性，分歧较大"
    elif avg_score >= 30:
        label = "偏悲观"
        description = "市场情绪偏冷，谨慎防守"
    else:
        label = "悲观"
        description = "市场情绪低迷，空头占优"

    return {
        "score": round(avg_score, 1),
        "label": label,
        "description": description,
        "distribution": {
            "positive": positive_count,
            "neutral": neutral_count,
            "negative": negative_count
        }
    }


def get_market_breadth() -> Dict[str, Any]:
    """
    计算市场广度（涨跌家数统计）
    使用模拟数据，后续接入真实行情
    """
    # 模拟涨跌家数
    up_count = random.randint(1500, 3500)
    down_count = random.randint(1000, 2500)
    flat_count = random.randint(200, 800)
    total = up_count + down_count + flat_count

    return {
        "up_count": up_count,
        "down_count": down_count,
        "flat_count": flat_count,
        "total": total,
        "up_ratio": round(up_count / total * 100, 2),
        "down_ratio": round(down_count / total * 100, 2),
        "advance_decline_line": up_count - down_count
    }


def get_sector_rotation(concepts: List[Concept]) -> List[Dict[str, Any]]:
    """
    获取板块轮动数据
    返回涨幅前5的概念板块
    """
    # 模拟数据，后续接入真实概念涨幅
    rotation_data = [
        {"name": "人工智能", "change_pct": round(random.uniform(2, 8), 2), "trend": "up"},
        {"name": "新能源", "change_pct": round(random.uniform(1, 5), 2), "trend": "up"},
        {"name": "半导体", "change_pct": round(random.uniform(0.5, 4), 2), "trend": "up"},
        {"name": "医药", "change_pct": round(random.uniform(-2, 2), 2), "trend": "neutral"},
        {"name": "银行", "change_pct": round(random.uniform(-1, 1), 2), "trend": "neutral"},
    ]

    # 按涨幅排序
    rotation_data.sort(key=lambda x: x["change_pct"], reverse=True)
    return rotation_data[:5]


def get_hot_concepts(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """获取热门概念（按关联股票数排序）"""
    concepts = db.query(Concept).limit(limit).all()
    result = []
    for concept in concepts:
        stock_count = db.query(ConceptStock).filter(
            ConceptStock.concept_id == concept.id
        ).count()
        result.append({
            "id": concept.id,
            "name": concept.name,
            "stock_count": stock_count,
            "description": concept.description
        })
    return sorted(result, key=lambda x: x["stock_count"], reverse=True)


# ==================== API 端点 ====================

@router.get("/sentiment", summary="获取市场情绪指数", tags=["仪表盘"])
async def get_market_sentiment(
    db: Session = Depends(get_db)
):
    """
    获取市场情绪指数（基于AI分析的新闻情感数据）

    **返回:**
    - score: 情绪得分 (0-100, 50为中性)
    - label: 情绪标签
    - description: 情绪描述
    - change: 较昨日变化
    - distribution: 新闻情绪分布
    """
    try:
        service = get_sentiment_service(db)
        sentiment = service.get_latest_sentiment()

        return {
            "status": "success",
            "data": {
                "score": sentiment['index'],
                "label": sentiment['label'],
                "description": f"今日市场情绪{sentiment['label']}，较昨日{'+' if sentiment['change'] > 0 else ''}{sentiment['change']}",
                "change": sentiment['change'],
                "distribution": {
                    "positive": sentiment['bullish'],
                    "neutral": sentiment['neutral'],
                    "negative": sentiment['bearish']
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取情绪指数失败: {str(e)}")


@router.get("/dashboard", summary="获取仪表盘数据", tags=["仪表盘"])
async def get_dashboard_data(
    db: Session = Depends(get_db)
):
    """
    获取首页仪表盘完整数据

    **返回:**
    - sentiment: 市场情绪
    - market_breadth: 市场广度（涨跌家数）
    - sector_rotation: 板块轮动
    - hot_concepts: 热门概念
    - recent_news_count: 最近新闻数量
    """
    try:
        # 情绪数据（使用新的情绪指数服务）
        service = get_sentiment_service(db)
        sentiment_data = service.get_latest_sentiment()
        sentiment = {
            "score": sentiment_data['index'],
            "label": sentiment_data['label'],
            "description": f"今日市场情绪{sentiment_data['label']}，较昨日{'+' if sentiment_data['change'] > 0 else ''}{sentiment_data['change']}",
            "change": sentiment_data['change']
        }

        # 市场广度
        market_breadth = get_market_breadth()

        # 板块轮动
        sector_rotation = get_sector_rotation([])

        # 热门概念
        hot_concepts = get_hot_concepts(db)

        # 持仓统计
        portfolio_count = db.query(Portfolio).filter(
            Portfolio.is_active == 1
        ).count()

        return {
            "status": "success",
            "data": {
                "sentiment": sentiment,
                "market_breadth": market_breadth,
                "sector_rotation": sector_rotation,
                "hot_concepts": hot_concepts,
                "stats": {
                    "recent_news_count": sentiment_data['news_count'],
                    "portfolio_count": portfolio_count,
                    "update_time": datetime.now().isoformat()
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘数据失败: {str(e)}")


@router.get("/breadth", summary="获取市场广度", tags=["仪表盘"])
async def get_breadth():
    """
    获取市场广度数据（涨跌家数统计）
    """
    try:
        breadth = get_market_breadth()
        return {
            "status": "success",
            "data": breadth
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场广度失败: {str(e)}")


@router.get("/sector-rotation", summary="获取板块轮动", tags=["仪表盘"])
async def get_sector_rotation_data():
    """
    获取板块轮动数据
    """
    try:
        sectors = get_sector_rotation([])
        return {
            "status": "success",
            "data": sectors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取板块轮动失败: {str(e)}")
