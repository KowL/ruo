import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.database import Base
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.services.portfolio import PortfolioService

# 获取内存数据库引擎
engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

class TestPortfolioService:

    def test_add_portfolio_with_strategy(self, db_session):
        service = PortfolioService(db_session)
        
        # 为了测试，这里可以通过 Mock 覆盖 xq 的逻辑，或者通过让价格获取报错转为默认成本价
        result = service.add_portfolio(
            symbol="000001",
            name="平安银行",
            cost_price=10.5,
            quantity=1000,
            strategy_tag="趋势",
            strategy_id=1,
            user_id=1
        )
        assert result["symbol"] == "000001"
        assert result["strategyId"] == 1
        assert result["quantity"] == 1000
        
    def test_update_portfolio_strategy(self, db_session):
        service = PortfolioService(db_session)
        
        # 先添加一个持仓
        add_result = service.add_portfolio(
            symbol="000858",
            name="五粮液",
            cost_price=150.0,
            quantity=100,
            user_id=1
        )
        portfolio_id = add_result["id"]
        
        # 更新策略 id
        update_result = service.update_portfolio(
            portfolio_id=portfolio_id,
            strategy_id=2,
            strategy_tag="白马股"
        )
        assert update_result["strategyId"] == 2
        assert update_result["strategyTag"] == "白马股"
        
        # 通过查询列表验证
        list_result = service.get_portfolio_list(1)
        found = next((item for item in list_result["items"] if item["id"] == portfolio_id), None)
        assert found is not None
        assert found["strategyId"] == 2
