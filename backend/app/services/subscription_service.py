"""
策略订阅服务 - Subscription Service
功能：策略订阅的 CRUD 操作
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from app.models.strategy_subscription import StrategySubscription
from app.models.stock_group import StockGroup
from app.models.stock_favorite import StockFavorite

logger = logging.getLogger(__name__)


class SubscriptionService:
    """策略订阅服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_subscription(
        self,
        user_id: int,
        strategy_id: int,
        stock_pool_type: str = "all",
        stock_group_id: Optional[int] = None,
        custom_symbols: Optional[List[str]] = None,
        notify_enabled: bool = True,
        notify_channels: Optional[List[str]] = None
    ) -> Dict:
        """创建订阅"""
        try:
            # 验证策略存在
            from app.models.strategy import Strategy
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()

            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 验证分组存在（如果指定了分组）
            if stock_pool_type == "group" and stock_group_id:
                group = self.db.query(StockGroup).filter(
                    StockGroup.id == stock_group_id,
                    StockGroup.user_id == user_id
                ).first()
                if not group:
                    raise ValueError(f"分组不存在: {stock_group_id}")

            # 检查是否已订阅
            existing = self.db.query(StrategySubscription).filter(
                StrategySubscription.user_id == user_id,
                StrategySubscription.strategy_id == strategy_id
            ).first()

            if existing:
                raise ValueError(f"已订阅该策略")

            subscription = StrategySubscription(
                user_id=user_id,
                strategy_id=strategy_id,
                stock_pool_type=stock_pool_type,
                stock_group_id=stock_group_id if stock_pool_type == "group" else None,
                custom_symbols=custom_symbols if stock_pool_type == "custom" else None,
                notify_enabled=notify_enabled,
                notify_channels=notify_channels or ["websocket"]
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

            return self._build_subscription_response(subscription)

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建订阅失败: {e}")
            raise

    def get_subscriptions(
        self,
        user_id: int,
        strategy_id: Optional[int] = None
    ) -> List[Dict]:
        """获取订阅列表"""
        try:
            query = self.db.query(StrategySubscription).filter(
                StrategySubscription.user_id == user_id
            )

            if strategy_id:
                query = query.filter(StrategySubscription.strategy_id == strategy_id)

            subscriptions = query.order_by(
                StrategySubscription.created_at.desc()
            ).all()

            return [self._build_subscription_response(s) for s in subscriptions]

        except Exception as e:
            logger.error(f"获取订阅列表失败: {e}")
            raise

    def get_subscription(self, subscription_id: int, user_id: int) -> Optional[Dict]:
        """获取订阅详情"""
        try:
            subscription = self.db.query(StrategySubscription).filter(
                StrategySubscription.id == subscription_id,
                StrategySubscription.user_id == user_id
            ).first()

            if not subscription:
                return None

            return self._build_subscription_response(subscription)

        except Exception as e:
            logger.error(f"获取订阅详情失败: {e}")
            raise

    def update_subscription(
        self,
        subscription_id: int,
        user_id: int,
        stock_pool_type: Optional[str] = None,
        stock_group_id: Optional[int] = None,
        custom_symbols: Optional[List[str]] = None,
        notify_enabled: Optional[bool] = None,
        notify_channels: Optional[List[str]] = None
    ) -> Dict:
        """更新订阅"""
        try:
            subscription = self.db.query(StrategySubscription).filter(
                StrategySubscription.id == subscription_id,
                StrategySubscription.user_id == user_id
            ).first()

            if not subscription:
                raise ValueError(f"订阅不存在: {subscription_id}")

            # 验证分组存在（如果指定了分组）
            if stock_group_id:
                group = self.db.query(StockGroup).filter(
                    StockGroup.id == stock_group_id,
                    StockGroup.user_id == user_id
                ).first()
                if not group:
                    raise ValueError(f"分组不存在: {stock_group_id}")

            if stock_pool_type is not None:
                subscription.stock_pool_type = stock_pool_type

            if stock_pool_type == "group" and stock_group_id:
                subscription.stock_group_id = stock_group_id
            else:
                subscription.stock_group_id = None

            if stock_pool_type == "custom" and custom_symbols:
                subscription.custom_symbols = custom_symbols
            else:
                subscription.custom_symbols = None

            if notify_enabled is not None:
                subscription.notify_enabled = notify_enabled

            if notify_channels is not None:
                subscription.notify_channels = notify_channels

            self.db.commit()
            self.db.refresh(subscription)

            return self._build_subscription_response(subscription)

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新订阅失败: {e}")
            raise

    def delete_subscription(self, subscription_id: int, user_id: int) -> bool:
        """取消订阅"""
        try:
            subscription = self.db.query(StrategySubscription).filter(
                StrategySubscription.id == subscription_id,
                StrategySubscription.user_id == user_id
            ).first()

            if not subscription:
                raise ValueError(f"订阅不存在: {subscription_id}")

            self.db.delete(subscription)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"取消订阅失败: {e}")
            raise

    def get_stock_pool(
        self,
        user_id: int,
        stock_pool_type: str,
        stock_group_id: Optional[int] = None,
        custom_symbols: Optional[List[str]] = None
    ) -> List[str]:
        """获取股票池"""
        try:
            if stock_pool_type == "all":
                # 所有自选股
                stocks = self.db.query(StockFavorite.symbol).filter(
                    StockFavorite.user_id == user_id
                ).all()
                return [s[0] for s in stocks]

            elif stock_pool_type == "group" and stock_group_id:
                # 指定分组的股票
                stocks = self.db.query(StockFavorite.symbol).filter(
                    StockFavorite.user_id == user_id,
                    StockFavorite.group_id == stock_group_id
                ).all()
                return [s[0] for s in stocks]

            elif stock_pool_type == "custom" and custom_symbols:
                # 自定义股票列表
                return custom_symbols

            return []

        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            raise

    def _build_subscription_response(self, subscription: StrategySubscription) -> Dict:
        """构建订阅响应"""
        # 获取策略信息
        from app.models.strategy import Strategy
        strategy = self.db.query(Strategy).filter(
            Strategy.id == subscription.strategy_id
        ).first()

        # 获取股票池信息
        stock_pool_type = subscription.stock_pool_type
        stock_symbols = []

        if stock_pool_type == "all":
            stocks = self.db.query(StockFavorite.symbol).filter(
                StockFavorite.user_id == subscription.user_id
            ).all()
            stock_symbols = [s[0] for s in stocks]
        elif stock_pool_type == "group" and subscription.stock_group_id:
            stocks = self.db.query(StockFavorite.symbol).filter(
                StockFavorite.user_id == subscription.user_id,
                StockFavorite.group_id == subscription.stock_group_id
            ).all()
            stock_symbols = [s[0] for s in stocks]
        elif stock_pool_type == "custom":
            stock_symbols = subscription.custom_symbols or []

        return {
            'id': subscription.id,
            'userId': subscription.user_id,
            'strategyId': subscription.strategy_id,
            'strategyName': strategy.name if strategy else None,
            'stockPoolType': subscription.stock_pool_type,
            'stockGroupId': subscription.stock_group_id,
            'customSymbols': subscription.custom_symbols,
            'notifyEnabled': subscription.notify_enabled,
            'notifyChannels': subscription.notify_channels,
            'stockPoolCount': len(stock_symbols),
            'createdAt': subscription.created_at.isoformat() if subscription.created_at else None,
            'updatedAt': subscription.updated_at.isoformat() if subscription.updated_at else None
        }
