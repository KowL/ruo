"""
API 测试
API Tests
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "欢迎使用" in response.json()["message"]


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_limit_up_stocks():
    """测试涨停股票接口"""
    response = client.get("/api/v1/analysis/limit-up")
    assert response.status_code == 200


def test_portfolio_list():
    """测试持仓列表接口"""
    response = client.get("/api/v1/portfolio/")
    assert response.status_code == 200
