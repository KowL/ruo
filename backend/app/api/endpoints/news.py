"""
新闻情报 API 端点 - MVP v0.1
News Intelligence API Endpoints

实现功能：
- F-05: 资讯定时抓取
- F-06: AI 情感打分
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.news import NewsService
from app.services.ai_analysis import AIAnalysisService

router = APIRouter()


# ==================== API 端点 ====================

@router.get("/{symbol}", summary="获取股票新闻及 AI 分析", tags=["新闻情报"])
async def get_stock_news(
    symbol: str,
    hours: int = Query(24, description="最近 N 小时内的新闻", ge=1, le=168),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取股票新闻及 AI 分析

    **场景 B：查看 AI 资讯**
    1. 用户在首页看到某只股票卡片出现"红色小点"（有新利好）
    2. 点击卡片进入详情页 → 切换到"情报"Tab
    3. 看到 AI 生成的卡片：
       > **[利好 ★★★★]**
       > **AI 摘要**：平安银行今日发布财报，净利润同比增长 20%，超出市场预期，且不良率进一步降低。
       > *来源：财联社 10:30*

    **参数：**
    - symbol: 股票代码
    - hours: 最近 N 小时内的新闻（默认 24）
    - limit: 返回数量（默认 10）

    **返回：**
    - 新闻列表，包含 AI 分析结果
    """
    try:
        news_service = NewsService(db)
        news_list = news_service.get_news_with_analysis(symbol, hours, limit)

        return {
            "status": "success",
            "data": news_list,
            "count": len(news_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.post("/fetch/{symbol}", summary="手动抓取股票新闻", tags=["新闻情报"])
async def fetch_stock_news(
    symbol: str,
    limit: int = Query(10, description="抓取数量", ge=1, le=50),
    analyze: bool = Query(True, description="是否自动进行 AI 分析"),
    db: Session = Depends(get_db)
):
    """
    手动抓取股票新闻

    **用途：**
    - 管理员手动触发新闻抓取
    - 测试新闻抓取功能

    **参数：**
    - symbol: 股票代码
    - limit: 抓取数量
    - analyze: 是否自动进行 AI 分析

    **返回：**
    - 抓取和分析结果
    """
    try:
        # 1. 抓取新闻
        news_service = NewsService(db)
        fetch_result = news_service.fetch_and_save_news(symbol, limit)

        result = {
            "fetched": fetch_result['fetched'],
            "saved": fetch_result['saved']
        }

        # 2. 如果需要，自动进行 AI 分析
        if analyze and fetch_result['saved'] > 0:
            ai_service = AIAnalysisService(db)
            analysis_result = ai_service.batch_analyze_news(symbol, limit)
            result['analyzed'] = analysis_result['analyzed']
            result['analysis_failed'] = analysis_result['failed']

        return {
            "status": "success",
            "message": f"抓取成功: {result['fetched']} 条, 保存: {result['saved']} 条",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取新闻失败: {str(e)}")


@router.post("/analyze/{news_id}", summary="分析单条新闻", tags=["新闻情报"])
async def analyze_news(
    news_id: int,
    db: Session = Depends(get_db)
):
    """
    对单条新闻进行 AI 分析

    **参数：**
    - news_id: 新闻ID

    **返回：**
    - AI 分析结果
    """
    try:
        ai_service = AIAnalysisService(db)
        result = ai_service.analyze_news(news_id)

        if not result:
            raise HTTPException(status_code=500, detail="AI 分析失败")

        return {
            "status": "success",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析新闻失败: {str(e)}")


@router.post("/batch/analyze/{symbol}", summary="批量分析股票新闻", tags=["新闻情报"])
async def batch_analyze_news(
    symbol: str,
    limit: int = Query(10, description="最多分析 N 条", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    批量分析股票的未分析新闻

    **用途：**
    - 对已抓取但未分析的新闻进行批量分析
    - 补充分析历史新闻

    **参数：**
    - symbol: 股票代码
    - limit: 最多分析 N 条

    **返回：**
    - 分析结果统计
    """
    try:
        ai_service = AIAnalysisService(db)
        result = ai_service.batch_analyze_news(symbol, limit)

        return {
            "status": "success",
            "message": f"分析完成: 成功 {result['analyzed']} 条, 失败 {result['failed']} 条",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.get("/latest", summary="获取最新新闻汇总", tags=["新闻情报"])
async def get_latest_news_summary(
    symbols: str = Query(..., description="股票代码列表，逗号分隔，如: 000001,600519"),
    hours: int = Query(24, description="最近 N 小时", ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    获取多只股票的最新新闻汇总

    **用途：**
    - 首页显示所有持仓股票的最新消息
    - 标记哪些股票有新消息

    **参数：**
    - symbols: 股票代码列表（逗号分隔）
    - hours: 最近 N 小时内的新闻

    **返回：**
    - {symbol: [news_list]} 字典
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]

        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="一次最多查询 20 只股票")

        news_service = NewsService(db)
        result = {}

        for symbol in symbol_list:
            news_list = news_service.get_news_with_analysis(symbol, hours, limit=5)
            result[symbol] = news_list

        return {
            "status": "success",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻汇总失败: {str(e)}")
