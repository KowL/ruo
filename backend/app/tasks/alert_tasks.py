"""
预警任务 - Alert Tasks
Celery 定时任务：检查持仓预警，触发实时推送
"""
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.alert import AlertService
from app.services.notification_service import get_notification_service
import logging

logger = logging.getLogger(__name__)


@shared_task(name="tasks.alert.check_alerts")
def check_alerts_task(user_id: int = 1):
    """
    检查持仓预警任务
    每5分钟执行一次，触发时发送推送通知
    """
    db = SessionLocal()
    try:
        logger.info(f"开始检查持仓预警，用户: {user_id}")
        
        service = AlertService(db)
        triggered = service.check_alerts(user_id=user_id)
        
        if triggered:
            logger.info(f"触发 {len(triggered)} 条预警")
            
            # 获取通知服务
            notification_service = get_notification_service()
            
            for alert in triggered:
                logger.info(f"  - {alert['symbol']}: {alert['message']}")
                
                # 1. 发送飞书通知
                try:
                    notification_service.send_feishu_notification(
                        title=f"持仓预警: {alert['name']} ({alert['symbol']})",
                        content=alert['message'],
                        message_type="card",
                        stock_name=alert['name'],
                        stock_symbol=alert['symbol'],
                        alert_type=alert['alertType'],
                        current_value=str(alert['triggerValue']),
                        threshold=str(alert['thresholdValue']),
                        detail_url=f"http://localhost:3000/chart?symbol={alert['symbol']}"
                    )
                except Exception as e:
                    logger.error(f"发送飞书通知失败: {e}")
                
                # 2. 发送WebSocket推送
                try:
                    import asyncio
                    from app.core.websocket_manager import manager
                    
                    # 创建异步任务发送WebSocket消息
                    asyncio.create_task(
                        manager.send_alert({
                            "type": "alert",
                            "symbol": alert['symbol'],
                            "stock_name": alert['name'],
                            "alert_type": alert['alertType'],
                            "current_value": alert['triggerValue'],
                            "threshold": alert['thresholdValue'],
                            "message": alert['message'],
                            "triggered_at": alert['triggeredAt']
                        })
                    )
                except Exception as e:
                    logger.error(f"发送WebSocket通知失败: {e}")
        else:
            logger.info("没有触发任何预警")
        
        return {
            "status": "success",
            "triggered_count": len(triggered),
            "triggered_alerts": triggered
        }
        
    except Exception as e:
        logger.error(f"检查预警任务失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


@shared_task(name="tasks.alert.clean_old_logs")
def clean_old_alert_logs(days: int = 30):
    """
    清理旧的预警记录
    每天执行一次，默认保留30天
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from app.models.alert import AlertLog
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 删除旧记录
        result = db.query(AlertLog).filter(
            AlertLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"清理了 {result} 条 {days} 天前的预警记录")
        return {
            "status": "success",
            "deleted_count": result
        }
        
    except Exception as e:
        logger.error(f"清理预警记录失败: {e}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()
