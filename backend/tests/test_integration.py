"""
集成测试 - Integration Tests
测试核心功能 API 端点的正常工作
"""
import pytest
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestPortfolioAPI:
    """测试持仓管理 API"""

    def test_add_portfolio(self):
        """测试添加持仓"""
        payload = {
            "symbol": "000001",
            "cost_price": 10.5,
            "quantity": 1000,
            "strategy_tag": "趋势"
        }

        response = client.post("/api/v1/portfolio/add", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["symbol"] == "000001"
        assert data["data"]["quantity"] == 1000
        assert "profit_loss" in data["data"]

    def test_portfolio_list(self):
        """测试获取持仓列表"""
        response = client.get("/api/v1/portfolio/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "total_value" in data

    def test_portfolio_detail(self):
        """测试获取持仓详情"""
        # 先添加一个持仓
        payload = {
            "symbol": "000001",
            "cost_price": 10.5,
            "quantity": 1000,
            "strategy_tag": "趋势"
        }
        add_response = client.post("/api/v1/portfolio/add", json=payload)
        portfolio_id = add_response.json()["data"]["id"]

        # 获取详情
        response = client.get(f"/api/v1/portfolio/{portfolio_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == portfolio_id


class TestStockAPI:
    """测试股票查询 API"""

    def test_search_stock(self):
        """测试股票搜索"""
        response = client.get("/api/v1/stock/search?keyword=000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert len(data["data"]) >= 1

    def test_get_stock_info(self):
        """测试获取股票基本信息"""
        response = client.get("/api/v1/stock/info/000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["symbol"] == "000001"
        assert "name" in data["data"]

    def test_get_realtime_price(self):
        """测试获取实时行情"""
        response = client.get("/api/v1/stock/realtime/000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["symbol"] == "000001"
        assert "price" in data["data"]
        assert "change" in data["data"]
        assert "change_pct" in data["data"]

    def test_get_stock_detail(self):
        """测试获取股票详细数据（分时+买卖盘）"""
        response = client.get("/api/v1/stock/detail/000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        # 验证返回的数据结构
        stock_detail = data["data"]
        assert stock_detail["symbol"] == "000001"

        # 验证分时数据
        assert "intraday" in stock_detail
        intraday = stock_detail["intraday"]
        if intraday:  # 可能为空
            assert isinstance(intraday, list)
            if len(intraday) > 0:
                assert "time" in intraday[0]
                assert "price" in intraday[0]
                assert "volume" in intraday[0]

        # 验证买卖盘数据
        assert "buy_orders" in stock_detail
        assert "sell_orders" in stock_detail

        # 验证买盘数据
        buy_orders = stock_detail["buy_orders"]
        if buy_orders:
            assert len(buy_orders) <= 5  # 最多 5 档
            assert "level" in buy_orders[0]
            assert "price" in buy_orders[0]
            assert "volume" in buy_orders[0]

        # 验证卖盘数据
        sell_orders = stock_detail["sell_orders"]
        if sell_orders:
            assert len(sell_orders) <= 5  # 最多 5 档
            assert "level" in sell_orders[0]
            assert "price" in sell_orders[0]
            assert "volume" in sell_orders[0]

    def test_batch_get_realtime_prices(self):
        """测试批量获取实时行情"""
        payload = ["000001", "000002", "000858"]

        response = client.post("/api/v1/stock/batch/realtime", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert len(data["data"]) > 0

    def test_invalid_stock_code(self):
        """测试无效的股票代码"""
        response = client.get("/api/v1/stock/info/INVALID")
        # 应该返回 404 或 200 但 data 为空
        assert response.status_code in [200, 404]


class TestNewsAPI:
    """测试新闻 API"""

    def test_get_stock_news(self):
        """测试获取股票新闻"""
        response = client.get("/api/v1/news/000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "data" in data

    def test_manual_fetch_news(self):
        """测试手动抓取新闻"""
        response = client.post("/api/v1/news/fetch/000001")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

    def test_batch_analyze_news(self):
        """测试批量分析新闻"""
        payload = {"symbol": "000001"}

        response = client.post("/api/v1/news/batch/analyze/000001", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"


class TestSystemAPI:
    """测试系统相关 API"""

    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "欢迎使用" in data["message"]

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_docs(self):
        """测试 API 文档"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_portfolio_data(self):
        """测试无效的持仓数据"""
        payload = {
            "symbol": "",  # 空的股票代码
            "cost_price": -1,  # 负价格
            "quantity": -1  # 负数量
        }

        response = client.post("/api/v1/portfolio/add", json=payload)
        # 应该返回 422 参数验证错误
        assert response.status_code == 422

    def test_empty_stock_search(self):
        """测试空搜索词"""
        response = client.get("/api/v1/stock/search?keyword=")
        # 应该返回 422 参数验证错误
        assert response.status_code == 422

    def test_batch_too_many_stocks(self):
        """测试批量查询超过限制的股票数量"""
        # 创建超过 100 个股票代码的列表
        payload = [f"0000{i}" for i in range(150)]

        response = client.post("/api/v1/stock/batch/realtime", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "一次最多查询" in data["detail"]


# 性能测试
class TestPerformance:
    """性能测试"""

    @pytest.mark.skip(reason="性能测试可选")
    def test_concurrent_requests(self):
        """测试并发请求性能"""
        import threading
        import time

        def make_request():
            client.get("/api/v1/stock/realtime/000001")

        # 创建 10 个并发线程
        threads = []
        start_time = time.time()

        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        duration = end_time - start_time

        # 所有请求应该在 5 秒内完成
        assert duration < 5.0
        print(f"并发 10 个请求耗时: {duration:.2f} 秒")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])