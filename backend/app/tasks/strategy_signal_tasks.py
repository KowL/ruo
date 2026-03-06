"""
策略信号生成任务 - Strategy Signal Tasks
负责定时为订阅用户生成交易信号
"""
import logging
from typing import Dict, List
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.strategy_signal_tasks.generate_signals_for_subscriptions')
def generate_signals_for_subscriptions() -> Dict:
    """
    为所有订阅用户生成信号

    执行频率：建议每日收盘后执行一次 (15:30)
    1. 查询所有活跃订阅
    2. 根据订阅的股票池获取股票列表
    3. 调用策略服务生成信号
    4. 保存信号并触发通知
    """
    try:
        from app.core.database import get_db
        from app.models.strategy_subscription import StrategySubscription
        from app.services.subscription_service import SubscriptionService
        from app.services.strategy import StrategyService

        logger.info("[信号生成] 开始为订阅用户生成信号")

        db: Session = next(get_db())
        subscription_service = SubscriptionService(db)
        strategy_service = StrategyService(db)

        # 1. 获取所有活跃订阅
        subscriptions = db.query(StrategySubscription).all()
        logger.info(f"[信号生成] 找到 {len(subscriptions)} 个订阅")

        total_signals = 0

        for subscription in subscriptions:
            try:
                # 获取股票池
                stock_symbols = subscription_service.get_stock_pool(
                    user_id=subscription.user_id,
                    stock_pool_type=subscription.stock_pool_type,
                    stock_group_id=subscription.stock_group_id,
                    custom_symbols=subscription.custom_symbols
                )

                if not stock_symbols:
                    logger.info(f"[信号生成] 用户 {subscription.user_id} 策略 {subscription.strategy_id} 股票池为空，跳过")
                    continue

                logger.info(f"[信号生成] 用户 {subscription.user_id} 策略 {subscription.strategy_id} 股票池: {len(stock_symbols)} 只")

                # 生成信号
                signals = strategy_service.generate_signals(
                    strategy_id=subscription.strategy_id,
                    symbols=stock_symbols,
                    user_id=subscription.user_id
                )

                total_signals += len(signals)

                # 发送通知
                if subscription.notify_enabled and signals:
                    _send_notification(subscription, signals)

            except Exception as e:
                logger.error(f"[信号生成] 处理订阅 {subscription.id} 失败: {e}")
                continue

        logger.info(f"[信号生成] 完成，共生成 {total_signals} 个信号")

        return {
            "status": "success",
            "subscriptions_count": len(subscriptions),
            "signals_generated": total_signals,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"[信号生成] 任务执行失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(name='app.tasks.strategy_signal_tasks.generate_signals_for_user')
def generate_signals_for_user(user_id: int, strategy_id: int, symbols: List[str]) -> Dict:
    """
    为指定用户生成信号（手动触发）

    参数:
        user_id: 用户ID
        strategy_id: 策略ID
        symbols: 股票代码列表
    """
    try:
        from app.core.database import get_db
        from app.services.strategy import StrategyService

        logger.info(f"[信号生成] 用户 {user_id} 手动触发信号生成，策略 {strategy_id}")

        db: Session = next(get_db())
        strategy_service = StrategyService(db)

        signals = strategy_service.generate_signals(
            strategy_id=strategy_id,
            symbols=symbols,
            user_id=user_id
        )

        return {
            "status": "success",
            "signals": signals,
            "count": len(signals)
        }

    except Exception as e:
        logger.error(f"[信号生成] 手动触发失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def _send_notification(subscription, signals: List[Dict]) -> None:
    """
    发送信号通知
    """
    try:
        channels = subscription.notify_channels or []

        # 构建通知内容
        buy_signals = [s for s in signals if s.get('signalType') == 'buy']
        sell_signals = [s for s in signals if s.get('signalType') == 'sell']

        if not buy_signals and not sell_signals:
            return

        title = "策略信号通知"
        content_parts = []
        if buy_signals:
            symbols = [s['symbol'] for s in buy_signals[:5]]
            content_parts.append(f"买入信号: {', '.join(symbols)}")
        if sell_signals:
            symbols = [s['symbol'] for s in sell_signals[:5]]
            content_parts.append(f"卖出信号: {', '.join(symbols)}")

        content = " | ".join(content_parts)

        # WebSocket 通知
        if "websocket" in channels:
            _send_websocket_notification(subscription.user_id, title, content)

        # 飞书通知（预留）
        if "feishu" in channels:
            logger.info(f"[通知] 飞书通知待实现: {title}")

    except Exception as e:
        logger.error(f"[通知] 发送通知失败: {e}")


def _send_websocket_notification(user_id: int, title: str, content: str) -> None:
    """
    通过 WebSocket 发送通知
    """
    try:
        # 这里可以复用现有的 WebSocket 通知逻辑
        # 或者通过 Redis 发布消息
        logger.info(f"[WebSocket] 用户 {user_id}: {title} - {content}")

        # TODO: 实现真正的 WebSocket 推送
        # 可以通过 Redis pub/sub 或直接访问连接管理器

    except Exception as e:
        logger.error(f"[WebSocket] 发送通知失败: {e}")
