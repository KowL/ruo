"""
API 路由模块 - MVP v0.1
API Routes Module
"""
from fastapi import APIRouter
from .endpoints import portfolio, stock, news

api_router = APIRouter()

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

from .endpoints import analysis
# 市场分析 API
api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["市场分析"]
)
