"""
API 路由模块
API Routes Module
"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ========================================
# 核心业务
# ========================================
from .endpoints import portfolio, stock, news

# 持仓管理
api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["持仓管理"]
)

# 股票查询
api_router.include_router(
    stock.router,
    prefix="/stock",
    tags=["股票查询"]
)

# 新闻情报
api_router.include_router(
    news.router,
    prefix="/news",
    tags=["新闻情报"]
)

# ========================================
# 策略与回测
# ========================================
from .endpoints import strategy, backtest

# 策略管理
api_router.include_router(
    strategy.router,
    prefix="/strategies",
    tags=["策略管理"]
)

# 回测系统
api_router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["回测系统"]
)

# ========================================
# 行情与市场数据
# ========================================
from .endpoints import concepts, concept_monitor, dashboard, dragon_tiger, short_term_radar

# 仪表盘
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["仪表盘"]
)

# 概念管理
api_router.include_router(
    concepts.router,
    prefix="/concepts",
    tags=["概念管理"]
)

# 概念异动监控
api_router.include_router(
    concept_monitor.router,
    prefix="/concept-monitor",
    tags=["概念监控"]
)

# 短线雷达
api_router.include_router(
    short_term_radar.router,
    prefix="/radar",
    tags=["短线雷达"]
)

# 龙虎榜分析
api_router.include_router(
    dragon_tiger.router,
    prefix="/lhb",
    tags=["龙虎榜分析"]
)

# ========================================
# 分析与智能
# ========================================
from .endpoints import sentiment, daily_report, alerts

# 情绪指数
api_router.include_router(
    sentiment.router,
    prefix="/sentiment",
    tags=["情绪指数"]
)

# 每日简报
api_router.include_router(
    daily_report.router,
    prefix="/daily-report",
    tags=["每日简报"]
)

# 预警管理
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["预警管理"]
)

# 市场分析（可选模块，LLM 依赖可能不可用）
try:
    from .endpoints import analysis
    api_router.include_router(
        analysis.router,
        prefix="/analysis",
        tags=["市场分析"]
    )
except ImportError as e:
    logger.warning(f"市场分析模块未加载（LLM 依赖不可用）: {e}")
