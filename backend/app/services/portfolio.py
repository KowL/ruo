"""
持仓管理服务 - Portfolio Service
MVP v0.1

功能：
- F-02: 新增/删除自选股
- F-03: 持仓信息录入
- F-04: 首页卡片展示（盈亏计算）
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.portfolio import Portfolio
from app.services.market_data import get_market_data_service

logger = logging.getLogger(__name__)


class PortfolioService:
    """持仓管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.market_service = get_market_data_service()

    def add_portfolio(
        self,
        symbol: str,
        cost_price: float,
        quantity: float,
        strategy_tag: Optional[str] = None,
        user_id: int = 1,
        notes: Optional[str] = None
    ) -> Dict:
        """
        添加持仓（快速响应，不获取实时行情）

        Args:
            symbol: 股票代码
            cost_price: 成本价
            quantity: 持仓数量
            strategy_tag: 策略标签（打板/低吸/趋势）
            user_id: 用户ID（默认1）
            notes: 备注

        Returns:
            添加成功的持仓基本信息（不含实时行情）
        """
        try:
            # 1. 获取股票基本信息（只需要名称）
            stock_info = self.market_service.get_stock_info(symbol)
            if not stock_info:
                # 如果获取不到详细信息，使用代码作为名称
                stock_name = symbol
                logger.warning(f"无法获取股票信息: {symbol}，使用代码作为名称")
            else:
                stock_name = stock_info['name']

            # 2. 检查是否已存在（同一用户同一股票）
            existing = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol,
                Portfolio.is_active == 1
            ).first()

            if existing:
                raise ValueError(f"持仓已存在: {stock_name} ({symbol})")

            # 3. 获取实时价格作为初始 current_price
            initial_current_price = cost_price
            try:
                realtime_info = self.market_service.get_realtime_price(symbol)
                if realtime_info and realtime_info.get('price', 0) > 0:
                    initial_current_price = realtime_info['price']
                    logger.info(f"获取到实时价格: {symbol} = {initial_current_price}")
            except Exception as e:
                logger.warning(f"添加持仓时获取实时价格失败，使用成本价: {e}")

            # 4. 创建持仓记录
            portfolio = Portfolio(
                user_id=user_id,
                symbol=symbol,
                name=stock_name,
                cost_price=cost_price,
                quantity=quantity,
                strategy_tag=strategy_tag,
                notes=notes,
                is_active=1,
                current_price=initial_current_price # 使用实时价格
            )

            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)

            # 4. 返回基本信息（不获取实时行情，提升响应速度）
            logger.info(f"添加持仓成功: {stock_name} ({symbol})")
            return self._build_simple_response(portfolio)

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加持仓失败: {symbol}, 错误: {e}")
            raise Exception(f"添加持仓失败: {str(e)}")

    def get_portfolio_list(self, user_id: int = 1) -> Dict:
        """
        获取持仓列表（不包含实时价格，前端单独获取）

        Args:
            user_id: 用户ID

        Returns:
            {
                "items": [...],
                "total_value": 0.0,
                "total_cost": 0.0
            }
        """
        try:
            # 1. 查询所有激活的持仓
            portfolios = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.is_active == 1
            ).all()

            if not portfolios:
                return {
                    "items": [],
                    "totalValue": 0.0,
                    "totalCost": 0.0
                }

            # 2. 构建持仓列表（使用实时价格）
            items = []
            total_cost = 0.0
            total_market_value = 0.0

            for portfolio in portfolios:
                # 计算实时盈亏
                pl_data = self.calculate_profit_loss(portfolio)
                
                total_cost += pl_data['costValue']
                total_market_value += pl_data['marketValue']

                items.append({
                    "id": portfolio.id,
                    "symbol": portfolio.symbol,
                    "name": portfolio.name,
                    "costPrice": portfolio.cost_price,
                    "quantity": portfolio.quantity,
                    "currentPrice": pl_data['currentPrice'],
                    "marketValue": round(pl_data['marketValue'], 2),
                    "costValue": round(pl_data['costValue'], 2),
                    "profitLoss": round(pl_data['profitLoss'], 2),
                    "profitLossRatio": round(pl_data['profitLossRatio'], 4),
                    "changePct": pl_data['changePct'],
                    "strategyTag": portfolio.strategy_tag,
                    "notes": portfolio.notes,
                    "createdAt": portfolio.created_at.strftime('%Y-%m-%d %H:%M:%S') if portfolio.created_at else None,
                    "hasNewNews": False
                })

            total_profit_loss = total_market_value - total_cost
            total_profit_loss_ratio = (total_profit_loss / total_cost) if total_cost > 0 else 0

            return {
                "items": items,
                "totalValue": round(total_market_value, 2),
                "totalCost": round(total_cost, 2),
                "totalProfitLoss": round(total_profit_loss, 2),
                "totalProfitLossRatio": round(total_profit_loss_ratio, 4)
            }

        except Exception as e:
            logger.error(f"获取持仓列表失败: 用户{user_id}, 错误: {e}")
            raise Exception(f"获取持仓列表失败: {str(e)}")

    def get_portfolio_detail(self, portfolio_id: int) -> Dict:
        """
        获取单个持仓详情

        Args:
            portfolio_id: 持仓ID

        Returns:
            持仓详情（包含盈亏）
        """
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active == 1
            ).first()

            if not portfolio:
                raise ValueError(f"持仓不存在: ID={portfolio_id}")

            return self._build_portfolio_response(portfolio)

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"获取持仓详情失败: ID={portfolio_id}, 错误: {e}")
            raise Exception(f"获取持仓详情失败: {str(e)}")

    def update_portfolio(
        self,
        portfolio_id: int,
        cost_price: Optional[float] = None,
        quantity: Optional[float] = None,
        strategy_tag: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        更新持仓信息（快速响应，不获取实时行情）

        Args:
            portfolio_id: 持仓ID
            cost_price: 新的成本价
            quantity: 新的持仓数量
            strategy_tag: 新的策略标签
            notes: 新的备注

        Returns:
            更新后的持仓基本信息（不含实时行情）
        """
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active == 1
            ).first()

            if not portfolio:
                raise ValueError(f"持仓不存在: ID={portfolio_id}")

            # 更新字段
            if cost_price is not None:
                portfolio.cost_price = cost_price
            if quantity is not None:
                portfolio.quantity = quantity
            if strategy_tag is not None:
                portfolio.strategy_tag = strategy_tag
            if notes is not None:
                portfolio.notes = notes

            portfolio.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(portfolio)

            logger.info(f"更新持仓成功: {portfolio.name} ({portfolio.symbol})")
            return self._build_simple_response(portfolio)

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新持仓失败: ID={portfolio_id}, 错误: {e}")
            raise Exception(f"更新持仓失败: {str(e)}")

    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        删除持仓（软删除）

        Args:
            portfolio_id: 持仓ID

        Returns:
            是否删除成功
        """
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active == 1
            ).first()

            if not portfolio:
                raise ValueError(f"持仓不存在: ID={portfolio_id}")

            # 软删除
            portfolio.is_active = 0
            portfolio.updated_at = datetime.now()

            self.db.commit()

            logger.info(f"删除持仓成功: {portfolio.name} ({portfolio.symbol})")
            return True

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除持仓失败: ID={portfolio_id}, 错误: {e}")
            raise Exception(f"删除持仓失败: {str(e)}")

    def calculate_profit_loss(self, portfolio: Portfolio) -> Dict:
        """
        计算持仓盈亏

        Args:
            portfolio: 持仓对象

        Returns:
            盈亏信息
        """
        try:
            # 直接从数据库获取缓存的实时价格
            current_price = portfolio.current_price if portfolio.current_price > 0 else portfolio.cost_price
            
            # 涨跌幅计算 (API不再直接提供，需自行计算或从其他地方获取，为了MVP简单起见，这里简化处理)
            # 如果后台任务能同步更新 changePct 到数据库最好，但目前只添加了 current_price
            # 我们动态计算 changePct
            if portfolio.cost_price > 0:
                 # 注意：这里计算的是相对于成本的涨跌幅，实际上 PortfolioListResponse 需要的是当日涨跌幅
                 # 这是一个妥协：因为我们不调用 API 了，所以无法获得准确的 "今日涨跌幅" (ChangePct)
                 # 除非数据库也缓存了 changePct, open_price 等。
                 # 用户需求是 "不要调用获取行情接口"，意味着接受一定的时效延迟或数据缺失。
                 # 为了保持 UI 不报错，我们这里只能计算【持仓盈亏比例】或者 0。
                 # 更好的做法是 DB 增加 change_pct 字段。
                 # 既然只加了 current_price，我们暂时返回 0 或估算值。
                 
                 # 修正：前端显示的 changePct 通常指今日涨跌幅。没有实时数据无法计算。
                 # 暂时设置为 0，或者如果用户允许，我们可以在 price_task 里顺便把 change_pct 也存了。
                 # 鉴于只加了 current_price 列，这里暂且设为 0，或者基于昨日收盘价(未知)。
                 change_pct = 0.0
            else:
                 change_pct = 0.0

            # 计算盈亏
            cost = portfolio.cost_price * portfolio.quantity
            value = current_price * portfolio.quantity
            profit_loss = value - cost
            profit_loss_ratio = (current_price - portfolio.cost_price) / portfolio.cost_price if portfolio.cost_price > 0 else 0

            return {
                "currentPrice": current_price,
                "marketValue": value,
                "costValue": cost,
                "profitLoss": profit_loss,
                "profitLossRatio": profit_loss_ratio,
                "changePct": change_pct
            }

        except Exception as e:
            logger.error(f"计算盈亏失败: {portfolio.symbol}, 错误: {e}")
            # 返回默认值
            return {
                "currentPrice": portfolio.cost_price,
                "marketValue": portfolio.cost_price * portfolio.quantity,
                "costValue": portfolio.cost_price * portfolio.quantity,
                "profitLoss": 0,
                "profitLossRatio": 0,
                "changePct": 0
            }

    def _build_simple_response(self, portfolio: Portfolio) -> Dict:
        """
        构建持仓简单响应数据（不含实时行情，快速返回）

        Args:
            portfolio: 持仓对象

        Returns:
            基本持仓信息（使用成本价作为当前价）
        """
        cost_value = portfolio.cost_price * portfolio.quantity

        return {
            "id": portfolio.id,
            "symbol": portfolio.symbol,
            "name": portfolio.name,
            "costPrice": portfolio.cost_price,
            "quantity": portfolio.quantity,
            "currentPrice": portfolio.cost_price,  # 暂时使用成本价
            "marketValue": round(cost_value, 2),
            "costValue": round(cost_value, 2),
            "profitLoss": 0.0,  # 暂无盈亏
            "profitLossRatio": 0.0,
            "changePct": 0.0,
            "strategyTag": portfolio.strategy_tag,
            "notes": portfolio.notes,
            "createdAt": portfolio.created_at.strftime('%Y-%m-%d %H:%M:%S') if portfolio.created_at else None,
            "updatedAt": portfolio.updated_at.strftime('%Y-%m-%d %H:%M:%S') if portfolio.updated_at else None
        }

    def _build_portfolio_response(self, portfolio: Portfolio) -> Dict:
        """
        构建持仓响应数据（包含实时行情）

        Args:
            portfolio: 持仓对象

        Returns:
            完整的持仓信息（包含盈亏）
        """
        profit_loss_data = self.calculate_profit_loss(portfolio)

        return {
            "id": portfolio.id,
            "symbol": portfolio.symbol,
            "name": portfolio.name,
            "costPrice": portfolio.cost_price,
            "quantity": portfolio.quantity,
            "currentPrice": profit_loss_data['current_price'],
            "marketValue": round(profit_loss_data['market_value'], 2),
            "costValue": round(profit_loss_data['cost_value'], 2),
            "profitLoss": round(profit_loss_data['profit_loss'], 2),
            "profitLossRatio": round(profit_loss_data['profit_loss_ratio'], 4),
            "changePct": profit_loss_data['change_pct'],
            "strategyTag": portfolio.strategy_tag,
            "notes": portfolio.notes,
            "createdAt": portfolio.created_at.strftime('%Y-%m-%d %H:%M:%S') if portfolio.created_at else None,
            "updatedAt": portfolio.updated_at.strftime('%Y-%m-%d %H:%M:%S') if portfolio.updated_at else None
        }
