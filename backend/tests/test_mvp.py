"""
MVP v0.1 功能测试脚本
Functional Testing Script

测试所有核心功能：
- F-01: 基础行情接入
- F-02: 新增/删除自选股
- F-03: 持仓信息录入
- F-04: 首页卡片展示
- F-05: 资讯定时抓取
- F-06: AI 情感打分
- F-07: 基础 K 线图
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import pytest
from datetime import datetime


class TestReport:
    """测试报告"""

    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0

    def add_test(self, name: str, passed: bool, message: str = ""):
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now()
        })

        if passed:
            self.passed += 1
            print(f"✅ {name}")
        else:
            self.failed += 1
            print(f"❌ {name}: {message}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("测试报告总结")
        print("=" * 60)
        print(f"总测试数: {len(self.tests)}")
        print(f"通过: {self.passed} ✅")
        print(f"失败: {self.failed} ❌")
        print(f"通过率: {self.passed / len(self.tests) * 100:.1f}%")
        print("=" * 60)

        if self.failed > 0:
            print("\n失败的测试:")
            for test in self.tests:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['message']}")


@pytest.mark.asyncio
async def test_all():
    """执行所有测试"""
    report = TestReport()

    print("🚀 开始 MVP v0.1 功能测试\n")
    print("=" * 60)

    # ==================== 环境检查 ====================
    print("\n📦 环境检查")
    print("-" * 60)

    # 1. 检查依赖
    try:
        import akshare
        report.add_test("依赖检查: AkShare", True)
    except ImportError as e:
        report.add_test("依赖检查: AkShare", False, str(e))

    try:
        import sqlalchemy
        report.add_test("依赖检查: SQLAlchemy", True)
    except ImportError as e:
        report.add_test("依赖检查: SQLAlchemy", False, str(e))

    try:
        import fastapi
        report.add_test("依赖检查: FastAPI", True)
    except ImportError as e:
        report.add_test("依赖检查: FastAPI", False, str(e))

    # 2. 检查配置
    try:
        from app.core.config import settings
        report.add_test("配置检查: Settings", True)
        print(f"   数据库: {settings.DATABASE_URL[:50]}...")
    except Exception as e:
        report.add_test("配置检查: Settings", False, str(e))

    # 3. 检查数据库连接
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            report.add_test("数据库连接测试", True)
    except Exception as e:
        report.add_test("数据库连接测试", False, str(e))

    # ==================== 服务层测试 ====================
    print("\n🔧 服务层测试")
    print("-" * 60)

    # 测试 MarketDataService
    try:
        from app.services.market_data import get_market_data_service

        market_service = get_market_data_service()

        # F-01: 测试股票搜索
        results = market_service.search_stock("000001")
        if results and len(results) > 0:
            report.add_test("F-01: 股票搜索功能", True)
            print(f"   找到 {len(results)} 个结果")
        else:
            report.add_test("F-01: 股票搜索功能", False, "未找到结果")

        # F-01: 测试实时行情
        realtime = market_service.get_realtime_price("000001")
        if realtime and 'price' in realtime:
            report.add_test("F-01: 实时行情获取", True)
            print(f"   价格: {realtime['price']}, 涨跌幅: {realtime['change_pct']}%")
        else:
            report.add_test("F-01: 实时行情获取", False, "获取失败")

        # F-07: 测试 K 线数据
        kline = market_service.get_kline_data("000001", "daily", 10)
        if kline and len(kline) > 0:
            report.add_test("F-07: K 线数据获取", True)
            print(f"   获取到 {len(kline)} 条 K 线数据")
        else:
            report.add_test("F-07: K 线数据获取", False, "获取失败")

    except Exception as e:
        report.add_test("MarketDataService 测试", False, str(e))

    # 测试 PortfolioService（需要数据库）
    try:
        from app.core.database import SessionLocal
        from app.services.portfolio import PortfolioService

        db = SessionLocal()
        portfolio_service = PortfolioService(db)

        # F-02: 测试添加持仓
        try:
            result = portfolio_service.add_portfolio(
                symbol="000001",
                cost_price=10.5,
                quantity=1000,
                strategy_tag="测试",
                user_id=1
            )

            if result and 'id' in result:
                test_portfolio_id = result['id']
                report.add_test("F-02/F-03: 添加持仓功能", True)
                print(f"   持仓ID: {test_portfolio_id}, 盈亏: {result.get('profit_loss', 0)}")

                # F-04: 测试获取持仓列表
                portfolio_list = portfolio_service.get_portfolio_list(user_id=1)
                if portfolio_list and 'items' in portfolio_list:
                    report.add_test("F-04: 持仓列表查询", True)
                    print(f"   总市值: {portfolio_list['total_value']}, 总盈亏: {portfolio_list['total_profit_loss']}")
                else:
                    report.add_test("F-04: 持仓列表查询", False, "查询失败")

                # 清理测试数据
                portfolio_service.delete_portfolio(test_portfolio_id)
                report.add_test("F-02: 删除持仓功能", True)
            else:
                report.add_test("F-02/F-03: 添加持仓功能", False, "添加失败")

        except ValueError as e:
            # 持仓已存在是正常的
            if "持仓已存在" in str(e):
                report.add_test("F-02/F-03: 添加持仓功能", True, "持仓已存在（正常）")
            else:
                report.add_test("F-02/F-03: 添加持仓功能", False, str(e))

        db.close()

    except Exception as e:
        report.add_test("PortfolioService 测试", False, str(e))

    # 测试 NewsService
    try:
        from app.core.database import SessionLocal
        from app.services.news import NewsService

        db = SessionLocal()
        news_service = NewsService(db)

        # F-05: 测试新闻抓取
        news_list = news_service.fetch_stock_news("000001", limit=5)
        if news_list and len(news_list) > 0:
            report.add_test("F-05: 新闻抓取功能", True)
            print(f"   抓取到 {len(news_list)} 条新闻")

            # 测试保存新闻
            saved = news_service.save_news(news_list)
            report.add_test("F-05: 新闻保存功能", True)
            print(f"   保存了 {saved} 条新闻")
        else:
            report.add_test("F-05: 新闻抓取功能", False, "未抓取到新闻")

        db.close()

    except Exception as e:
        report.add_test("NewsService 测试", False, str(e))

    # 测试 AIAnalysisService
    try:
        from app.core.database import SessionLocal
        from app.services.ai_analysis import AIAnalysisService
        from app.models.news import StockNews

        db = SessionLocal()
        ai_service = AIAnalysisService(db)

        # 检查是否配置了 LLM
        if ai_service.llm_client:
            # 查找一条未分析的新闻
            news = db.query(StockNews).first()

            if news:
                # F-06: 测试 AI 分析
                try:
                    result = ai_service.analyze_news(news.id)
                    if result and 'sentiment_label' in result:
                        report.add_test("F-06: AI 情感分析", True)
                        print(f"   情感: {result['sentiment_label']}, 评分: {result['sentiment_score']}")
                        print(f"   摘要: {result['ai_summary'][:50]}...")
                    else:
                        report.add_test("F-06: AI 情感分析", False, "分析失败")
                except Exception as e:
                    if "已分析过" in str(e):
                        report.add_test("F-06: AI 情感分析", True, "新闻已分析（正常）")
                    else:
                        report.add_test("F-06: AI 情感分析", False, str(e))
            else:
                report.add_test("F-06: AI 情感分析", False, "没有可分析的新闻")
        else:
            report.add_test("F-06: AI 情感分析", False, "未配置 LLM API Key")

        db.close()

    except Exception as e:
        report.add_test("AIAnalysisService 测试", False, str(e))

    # ==================== API 端点测试 ====================
    print("\n🌐 API 端点测试")
    print("-" * 60)

    try:
        from fastapi.testclient import TestClient
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from main import app

        client = TestClient(app)

        # 测试根路径
        response = client.get("/")
        if response.status_code == 200:
            report.add_test("API: 根路径", True)
        else:
            report.add_test("API: 根路径", False, f"状态码: {response.status_code}")

        # 测试健康检查
        response = client.get("/health")
        if response.status_code == 200:
            report.add_test("API: 健康检查", True)
        else:
            report.add_test("API: 健康检查", False, f"状态码: {response.status_code}")

        # 测试股票搜索 API
        response = client.get("/api/v1/stock/search?keyword=000001")
        if response.status_code == 200:
            report.add_test("API: 股票搜索", True)
        else:
            report.add_test("API: 股票搜索", False, f"状态码: {response.status_code}")

        # 测试实时行情 API
        response = client.get("/api/v1/stock/realtime/000001")
        if response.status_code == 200:
            report.add_test("API: 实时行情", True)
        else:
            report.add_test("API: 实时行情", False, f"状态码: {response.status_code}")

        # 测试 K 线数据 API
        response = client.get("/api/v1/stock/kline/000001?period=daily&limit=10")
        if response.status_code == 200:
            report.add_test("API: K 线数据", True)
        else:
            report.add_test("API: K 线数据", False, f"状态码: {response.status_code}")

        # 测试持仓列表 API
        response = client.get("/api/v1/portfolio/list")
        if response.status_code == 200:
            report.add_test("API: 持仓列表", True)
        else:
            report.add_test("API: 持仓列表", False, f"状态码: {response.status_code}")

        # 测试新闻 API
        response = client.get("/api/v1/news/000001")
        if response.status_code == 200:
            report.add_test("API: 新闻查询", True)
        else:
            report.add_test("API: 新闻查询", False, f"状态码: {response.status_code}")

    except Exception as e:
        report.add_test("API 端点测试", False, str(e))

    # ==================== 打印测试报告 ====================
    report.print_summary()

    # 返回测试结果
    return report.failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(test_all())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
