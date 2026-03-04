"""
API 路由模块 - MVP v0.1
API Routes Module
"""
from fastapi import APIRouter
from .endpoints import (
    portfolio, stock, news, concepts, dashboard, 
    concept_monitor, sentiment, daily_report, alerts,
    short_term_radar, dragon_tiger, strategy, backtest
)

api_router = APIRouter()

# 短线雷达 API
api_router.include_router(
    short_term_radar.router,
    prefix="/radar",
    tags=["短线雷达"]
)

# 龙虎榜分析 API
api_router.include_router(
    dragon_tiger.router,
    prefix="/lhb",
    tags=["龙虎榜分析"]
)

# 策略管理 API
api_router.include_router(
    strategy.router,
    prefix="/strategies",
    tags=["策略管理"]
)

# 回测系统 API
api_router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["回测系统"]
)

# 注册各个子路由

# 持仓管理 API (F-02, F-03, F-04)
api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["持仓管理"]
)

# 股票查询 API (F-01, F-07)
api_router.include_router(
    stock.router,
    prefix="/stock",
    tags=["股票查询"]
)

# 新闻情报 API (F-05, F-06) - 待实现
api_router.include_router(
    news.router,
    prefix="/news",
    tags=["新闻情报"]
)

try:
    from .endpoints import analysis
    # 市场分析 API
    api_router.include_router(
        analysis.router,
        prefix="/analysis",
        tags=["市场分析"]
    )
except ImportError as e:
    import logging
    logging.warning(f"Failed to import analysis module: {e}")

# 概念管理 API
api_router.include_router(
    concepts.router,
    prefix="/concepts",
    tags=["概念管理"]
)

# 仪表盘 API
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["仪表盘"]
)

# 概念异动监控 API
api_router.include_router(
    concept_monitor.router,
    prefix="/concept-monitor",
    tags=["概念监控"]
)

# 情绪指数 API
api_router.include_router(
    sentiment.router,
    prefix="/sentiment",
    tags=["情绪指数"]
)

# 每日简报 API
api_router.include_router(
    daily_report.router,
    prefix="/daily-report",
    tags=["每日简报"]
)

# 预警管理 API
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["预警管理"]
)
