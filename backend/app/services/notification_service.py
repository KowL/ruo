"""
通知服务 - Notification Service
支持飞书、邮件等多种通知渠道
"""
import logging
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务类"""
    
    def __init__(self):
        self.feishu_webhook_url: Optional[str] = None
        self.email_enabled: bool = False
    
    def set_feishu_webhook(self, webhook_url: str):
        """设置飞书Webhook地址"""
        self.feishu_webhook_url = webhook_url
        logger.info(f"飞书Webhook已设置: {webhook_url[:50]}...")
    
    def send_feishu_notification(
        self,
        title: str,
        content: str,
        message_type: str = "text",
        **kwargs
    ) -> bool:
        """
        发送飞书通知
        
        Args:
            title: 通知标题
            content: 通知内容
            message_type: 消息类型 (text/post/card)
            **kwargs: 额外参数
            
        Returns:
            是否发送成功
        """
        if not self.feishu_webhook_url:
            logger.warning("飞书Webhook未配置，跳过发送")
            return False
        
        try:
            if message_type == "text":
                payload = {
                    "msg_type": "text",
                    "content": {
                        "text": f"{title}\n\n{content}"
                    }
                }
            elif message_type == "post":
                payload = {
                    "msg_type": "post",
                    "content": {
                        "post": {
                            "zh_cn": {
                                "title": title,
                                "content": [
                                    [{"tag": "text", "text": content}]
                                ]
                            }
                        }
                    }
                }
            elif message_type == "card":
                # 卡片消息 - 用于预警通知
                stock_name = kwargs.get('stock_name', '')
                stock_symbol = kwargs.get('stock_symbol', '')
                alert_type = kwargs.get('alert_type', '')
                current_value = kwargs.get('current_value', '')
                threshold = kwargs.get('threshold', '')
                
                payload = {
                    "msg_type": "interactive",
                    "card": {
                        "config": {"wide_screen_mode": True},
                        "header": {
                            "title": {
                                "tag": "plain_text",
                                "content": f"🚨 {title}"
                            },
                            "template": "red" if alert_type in ['limit_down', 'price_drop'] else "orange"
                        },
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**股票:** {stock_name} ({stock_symbol})\n**类型:** {self._get_alert_type_name(alert_type)}\n**当前值:** {current_value}\n**阈值:** {threshold}\n**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                }
                            },
                            {
                                "tag": "action",
                                "actions": [
                                    {
                                        "tag": "button",
                                        "text": {"tag": "plain_text", "content": "查看详情"},
                                        "type": "primary",
                                        "url": kwargs.get('detail_url', '')
                                    }
                                ]
                            }
                        ]
                    }
                }
            else:
                logger.error(f"不支持的消息类型: {message_type}")
                return False
            
            response = requests.post(
                self.feishu_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"飞书通知发送成功: {title}")
                    return True
                else:
                    logger.error(f"飞书API返回错误: {result}")
                    return False
            else:
                logger.error(f"飞书HTTP错误: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")
            return False
    
    def _get_alert_type_name(self, alert_type: str) -> str:
        """获取预警类型中文名称"""
        type_names = {
            'price_above': '价格上破',
            'price_below': '价格下破',
            'rise_above': '涨幅超过',
            'fall_below': '跌幅超过',
            'limit_up': '涨停',
            'limit_down': '跌停',
            'volume_surge': '成交量异动',
            'turnover_high': '换手率过高',
            'market_cap_change': '市值变动',
        }
        return type_names.get(alert_type, alert_type)
    
    def send_alert_notification(
        self,
        alert_rule: Any,
        triggered_value: float,
        stock_name: str = "",
        **kwargs
    ) -> bool:
        """
        发送预警通知
        
        Args:
            alert_rule: 预警规则对象
            triggered_value: 触发的值
            stock_name: 股票名称
            **kwargs: 额外参数
            
        Returns:
            是否发送成功
        """
        try:
            symbol = alert_rule.symbol
            alert_type = alert_rule.alert_type
            threshold = alert_rule.threshold
            
            title = f"持仓预警触发: {stock_name or symbol}"
            content = f"""
股票代码: {symbol}
预警类型: {self._get_alert_type_name(alert_type)}
当前值: {triggered_value}
设定阈值: {threshold}
触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            # 发送飞书卡片消息
            success = self.send_feishu_notification(
                title=title,
                content=content,
                message_type="card",
                stock_name=stock_name or symbol,
                stock_symbol=symbol,
                alert_type=alert_type,
                current_value=str(triggered_value),
                threshold=str(threshold),
                detail_url=f"http://localhost:3000/chart?symbol={symbol}"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"发送预警通知失败: {e}")
            return False
    
    def send_daily_report(
        self,
        report_type: str = "opening",
        content: str = "",
        **kwargs
    ) -> bool:
        """
        发送每日报告（开盘/收盘简报）
        
        Args:
            report_type: 报告类型 (opening/closing)
            content: 报告内容
            **kwargs: 额外参数
            
        Returns:
            是否发送成功
        """
        try:
            if report_type == "opening":
                title = "📈 开盘简报"
                template = "blue"
            else:
                title = "📊 收盘简报"
                template = "green"
            
            # 构建卡片消息
            sentiment = kwargs.get('sentiment', {})
            sentiment_score = sentiment.get('score', 50)
            sentiment_label = sentiment.get('label', '中性')
            
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": template
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**市场情绪:** {sentiment_label} ({sentiment_score})\n\n{content[:500]}"
                            }
                        },
                        {
                            "tag": "action",
                            "actions": [
                                {
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "查看详情"},
                                    "type": "primary",
                                    "url": "http://localhost:3000"
                                }
                            ]
                        }
                    ]
                }
            }
            
            if not self.feishu_webhook_url:
                logger.warning("飞书Webhook未配置，跳过发送")
                return False
            
            response = requests.post(
                self.feishu_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"{title}发送成功")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"发送每日报告失败: {e}")
            return False


# 单例模式
_notification_service = None

def get_notification_service() -> NotificationService:
    """获取通知服务单例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
        # 从环境变量加载配置
        import os
        feishu_webhook = os.getenv('FEISHU_WEBHOOK_URL')
        if feishu_webhook:
            _notification_service.set_feishu_webhook(feishu_webhook)
    return _notification_service
