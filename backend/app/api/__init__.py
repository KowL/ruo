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
from .endpoints import portfolio, stock, news, favorite, subscriptions, dashboard, dragon_tiger, market, concept, concept_monitor

# 持仓管理
api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["持仓管理"]
)

# 自选管理
api_router.include_router(
    favorite.router,
    prefix="/favorite",
    tags=["自选管理"]
)

# 策略订阅
api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["策略订阅"]
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
    prefix="/strategy",
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

# 仪表盘
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["仪表盘"]
)

# 市场数据
api_router.include_router(
    market.router,
    prefix="/market",
    tags=["市场数据"]
)

# 概念管理
api_router.include_router(
    concept.router,
    prefix="/concept",
    tags=["概念管理"]
)

# 概念异动监控
api_router.include_router(
    concept_monitor.router,
    prefix="/concept-monitor",
    tags=["概念监控"]
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

# ========================================
# 股票分析
# ========================================
from .endpoints import limit_up_ladder

# 连板天梯
api_router.include_router(
    limit_up_ladder.router,
    prefix="/stock",
    tags=["股票分析"]
)

# ========================================
# OpenClaw 集成
# ========================================
from .endpoints import openclaw

api_router.include_router(
    openclaw.router,
    prefix="/openclaw",
    tags=["OpenClaw 集成"]
)

# ========================================
# 提示词广场
# ========================================
from .endpoints import prompt

api_router.include_router(
    prompt.router,
    prefix="/prompt",
    tags=["提示词广场"]
)
