"""
预警服务 - Alert Service
提供持仓预警规则的CRUD和检查触发功能
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.alert import AlertRule, AlertLog
from app.models.portfolio import Portfolio
from app.services.market_data import get_market_data_service

logger = logging.getLogger(__name__)


class AlertService:
    """预警服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_service = get_market_data_service()
    
    def create_alert_rule(
        self,
        portfolio_id: int,
        alert_type: str,
        threshold_value: float,
        compare_operator: str = ">=",
        cooldown_minutes: int = 60,
        notes: Optional[str] = None,
        user_id: int = 1
    ) -> Dict:
        """
        创建预警规则
        
        Args:
            portfolio_id: 持仓ID
            alert_type: 预警类型 (price_change/profit_loss/target_price)
            threshold_value: 阈值
            compare_operator: 比较运算符 (>=, <=, >, <)
            cooldown_minutes: 冷却时间(分钟)
            notes: 备注
            user_id: 用户ID
        """
        try:
            # 验证持仓存在
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.is_active == 1
            ).first()
            
            if not portfolio:
                raise ValueError(f"持仓不存在: {portfolio_id}")
            
            # 验证预警类型
            valid_types = ["price_change", "profit_loss", "target_price"]
            if alert_type not in valid_types:
                raise ValueError(f"不支持的预警类型: {alert_type}, 支持: {valid_types}")
            
            # 创建规则
            rule = AlertRule(
                user_id=user_id,
                portfolio_id=portfolio_id,
                alert_type=alert_type,
                threshold_value=threshold_value,
                compare_operator=compare_operator,
                cooldown_minutes=cooldown_minutes,
                notes=notes,
                is_active=1
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            return self._build_rule_response(rule, portfolio)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建预警规则失败: {e}")
            raise
    
    def get_alert_rules(
        self,
        portfolio_id: Optional[int] = None,
        user_id: int = 1
    ) -> List[Dict]:
        """获取预警规则列表"""
        try:
            query = self.db.query(AlertRule).filter(
                AlertRule.user_id == user_id,
                AlertRule.is_active == 1
            )
            
            if portfolio_id:
                query = query.filter(AlertRule.portfolio_id == portfolio_id)
            
            rules = query.order_by(AlertRule.created_at.desc()).all()
            
            result = []
            for rule in rules:
                portfolio = self.db.query(Portfolio).filter(
                    Portfolio.id == rule.portfolio_id
                ).first()
                result.append(self._build_rule_response(rule, portfolio))
            
            return result
            
        except Exception as e:
            logger.error(f"获取预警规则失败: {e}")
            raise
    
    def update_alert_rule(
        self,
        rule_id: int,
        alert_type: Optional[str] = None,
        threshold_value: Optional[float] = None,
        compare_operator: Optional[str] = None,
        cooldown_minutes: Optional[int] = None,
        is_active: Optional[int] = None,
        notes: Optional[str] = None,
        user_id: int = 1
    ) -> Dict:
        """更新预警规则"""
        try:
            rule = self.db.query(AlertRule).filter(
                AlertRule.id == rule_id,
                AlertRule.user_id == user_id
            ).first()
            
            if not rule:
                raise ValueError(f"预警规则不存在: {rule_id}")
            
            if alert_type is not None:
                valid_types = ["price_change", "profit_loss", "target_price"]
                if alert_type not in valid_types:
                    raise ValueError(f"不支持的预警类型: {alert_type}")
                rule.alert_type = alert_type
            
            if threshold_value is not None:
                rule.threshold_value = threshold_value
            if compare_operator is not None:
                rule.compare_operator = compare_operator
            if cooldown_minutes is not None:
                rule.cooldown_minutes = cooldown_minutes
            if is_active is not None:
                rule.is_active = is_active
            if notes is not None:
                rule.notes = notes
            
            self.db.commit()
            self.db.refresh(rule)
            
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == rule.portfolio_id
            ).first()
            
            return self._build_rule_response(rule, portfolio)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新预警规则失败: {e}")
            raise
    
    def delete_alert_rule(self, rule_id: int, user_id: int = 1) -> bool:
        """删除预警规则(软删除)"""
        try:
            rule = self.db.query(AlertRule).filter(
                AlertRule.id == rule_id,
                AlertRule.user_id == user_id
            ).first()
            
            if not rule:
                raise ValueError(f"预警规则不存在: {rule_id}")
            
            rule.is_active = 0
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除预警规则失败: {e}")
            raise
    
    def check_alerts(self, user_id: int = 1) -> List[Dict]:
        """
        检查所有预警规则，返回触发的预警
        """
        triggered_alerts = []
        
        try:
            # 获取所有活跃的预警规则
            rules = self.db.query(AlertRule).filter(
                AlertRule.user_id == user_id,
                AlertRule.is_active == 1
            ).all()
            
            for rule in rules:
                # 检查冷却时间
                if rule.last_triggered_at:
                    cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                    if datetime.utcnow() < cooldown_end:
                        continue
                
                # 获取持仓信息
                portfolio = self.db.query(Portfolio).filter(
                    Portfolio.id == rule.portfolio_id,
                    Portfolio.is_active == 1
                ).first()
                
                if not portfolio:
                    continue
                
                # 获取实时价格
                try:
                    current_price = self.market_service.get_stock_price(portfolio.symbol)
                    if current_price <= 0:
                        continue
                except Exception as e:
                    logger.warning(f"获取价格失败 {portfolio.symbol}: {e}")
                    continue
                
                # 计算触发值
                trigger_value = self._calculate_trigger_value(
                    rule.alert_type, portfolio, current_price
                )
                
                # 检查是否触发
                if self._is_triggered(trigger_value, rule.threshold_value, rule.compare_operator):
                    # 创建预警记录
                    alert_log = self._create_alert_log(rule, portfolio, current_price, trigger_value)
                    
                    # 更新规则触发信息
                    rule.last_triggered_at = datetime.utcnow()
                    rule.trigger_count += 1
                    self.db.commit()
                    
                    triggered_alerts.append({
                        "ruleId": rule.id,
                        "portfolioId": portfolio.id,
                        "symbol": portfolio.symbol,
                        "name": portfolio.name,
                        "alertType": rule.alert_type,
                        "triggerValue": trigger_value,
                        "thresholdValue": rule.threshold_value,
                        "currentPrice": current_price,
                        "message": alert_log.message,
                        "triggeredAt": alert_log.created_at.isoformat()
                    })
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"检查预警失败: {e}")
            raise
    
    def get_alert_logs(
        self,
        portfolio_id: Optional[int] = None,
        is_read: Optional[int] = None,
        limit: int = 50,
        user_id: int = 1
    ) -> List[Dict]:
        """获取预警触发记录"""
        try:
            query = self.db.query(AlertLog).filter(
                AlertLog.user_id == user_id
            )
            
            if portfolio_id:
                query = query.filter(AlertLog.portfolio_id == portfolio_id)
            if is_read is not None:
                query = query.filter(AlertLog.is_read == is_read)
            
            logs = query.order_by(AlertLog.created_at.desc()).limit(limit).all()
            
            return [{
                "id": log.id,
                "alertRuleId": log.alert_rule_id,
                "portfolioId": log.portfolio_id,
                "symbol": log.symbol,
                "triggerPrice": log.trigger_price,
                "triggerValue": log.trigger_value,
                "message": log.message,
                "isRead": log.is_read,
                "createdAt": log.created_at.isoformat()
            } for log in logs]
            
        except Exception as e:
            logger.error(f"获取预警记录失败: {e}")
            raise
    
    def mark_alert_read(self, log_id: int, user_id: int = 1) -> bool:
        """标记预警为已读"""
        try:
            log = self.db.query(AlertLog).filter(
                AlertLog.id == log_id,
                AlertLog.user_id == user_id
            ).first()
            
            if not log:
                raise ValueError(f"预警记录不存在: {log_id}")
            
            log.is_read = 1
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"标记已读失败: {e}")
            raise
    
    def _calculate_trigger_value(self, alert_type: str, portfolio: Portfolio, current_price: float) -> float:
        """计算触发值"""
        if alert_type == "price_change":
            # 当日涨跌幅(使用当前价 vs 成本价作为近似)
            return round((current_price - portfolio.cost_price) / portfolio.cost_price * 100, 2)
        elif alert_type == "profit_loss":
            # 盈亏比例
            return round((current_price - portfolio.cost_price) / portfolio.cost_price * 100, 2)
        elif alert_type == "target_price":
            # 目标价 - 直接比较当前价格
            return current_price
        return 0.0
    
    def _is_triggered(self, value: float, threshold: float, operator: str) -> bool:
        """检查是否触发条件"""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        return False
    
    def _create_alert_log(
        self,
        rule: AlertRule,
        portfolio: Portfolio,
        current_price: float,
        trigger_value: float
    ) -> AlertLog:
        """创建预警触发记录"""
        # 生成消息
        type_names = {
            "price_change": "涨跌幅",
            "profit_loss": "盈亏比例",
            "target_price": "目标价"
        }
        type_name = type_names.get(rule.alert_type, rule.alert_type)
        
        message = f"{portfolio.name}({portfolio.symbol}) {type_name}触发预警: 当前{trigger_value}, 阈值{rule.compare_operator}{rule.threshold_value}"
        
        log = AlertLog(
            user_id=rule.user_id,
            alert_rule_id=rule.id,
            portfolio_id=portfolio.id,
            symbol=portfolio.symbol,
            trigger_price=current_price,
            trigger_value=trigger_value,
            message=message
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def _build_rule_response(self, rule: AlertRule, portfolio: Optional[Portfolio]) -> Dict:
        """构建规则响应"""
        type_names = {
            "price_change": "涨跌幅",
            "profit_loss": "盈亏比例",
            "target_price": "目标价"
        }
        
        return {
            "id": rule.id,
            "portfolioId": rule.portfolio_id,
            "symbol": portfolio.symbol if portfolio else None,
            "name": portfolio.name if portfolio else None,
            "alertType": rule.alert_type,
            "alertTypeName": type_names.get(rule.alert_type, rule.alert_type),
            "thresholdValue": rule.threshold_value,
            "compareOperator": rule.compare_operator,
            "isActive": rule.is_active,
            "cooldownMinutes": rule.cooldown_minutes,
            "lastTriggeredAt": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            "triggerCount": rule.trigger_count,
            "notes": rule.notes,
            "createdAt": rule.created_at.isoformat() if rule.created_at else None
        }
