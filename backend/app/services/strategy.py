"""
策略管理服务 - Strategy Management Service
功能：策略CRUD、策略信号生成
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import json

from app.models.strategy import Strategy, StrategySignal

logger = logging.getLogger(__name__)


class StrategyService:
    """策略管理服务"""
    
    # 预设策略模板
    STRATEGY_TEMPLATES = {
        'trend_following': {
            'name': '趋势跟踪策略',
            'description': '跟随趋势，买入强势股，跌破趋势卖出',
            'entry_rules': [
                {'indicator': 'ma', 'condition': 'price_above_ma20', 'weight': 30},
                {'indicator': 'volume', 'condition': 'volume_increase_50', 'weight': 20},
                {'indicator': 'momentum', 'condition': 'rsi_between_50_80', 'weight': 30},
            ],
            'exit_rules': [
                {'indicator': 'ma', 'condition': 'price_below_ma10', 'weight': 50},
                {'indicator': 'stop_loss', 'condition': 'loss_8_percent', 'weight': 50},
            ],
            'position_rules': {
                'max_position_per_stock': 0.2,  # 单票最大20%
                'max_total_position': 0.8,       # 总仓位最大80%
            },
            'risk_rules': {
                'stop_loss': 0.08,  # 8%止损
                'take_profit': 0.15,  # 15%止盈
                'max_hold_days': 20,
            }
        },
        'mean_reversion': {
            'name': '均值回归策略',
            'description': '超跌反弹，买入超卖股票',
            'entry_rules': [
                {'indicator': 'rsi', 'condition': 'rsi_below_30', 'weight': 40},
                {'indicator': 'bollinger', 'condition': 'price_below_lower', 'weight': 30},
                {'indicator': 'volume', 'condition': 'volume_shrink', 'weight': 20},
            ],
            'exit_rules': [
                {'indicator': 'rsi', 'condition': 'rsi_above_70', 'weight': 50},
                {'indicator': 'bollinger', 'condition': 'price_above_middle', 'weight': 30},
            ],
            'position_rules': {
                'max_position_per_stock': 0.15,
                'max_total_position': 0.6,
            },
            'risk_rules': {
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'max_hold_days': 10,
            }
        },
        'breakout': {
            'name': '突破策略',
            'description': '突破新高或平台突破买入',
            'entry_rules': [
                {'indicator': 'price', 'condition': 'new_20day_high', 'weight': 40},
                {'indicator': 'volume', 'condition': 'volume_breakout', 'weight': 30},
                {'indicator': 'momentum', 'condition': 'strong_momentum', 'weight': 20},
            ],
            'exit_rules': [
                {'indicator': 'price', 'condition': 'fallback_below_breakout', 'weight': 50},
                {'indicator': 'stop_loss', 'condition': 'loss_5_percent', 'weight': 30},
            ],
            'position_rules': {
                'max_position_per_stock': 0.25,
                'max_total_position': 0.7,
            },
            'risk_rules': {
                'stop_loss': 0.05,
                'take_profit': 0.20,
                'max_hold_days': 15,
            }
        },
        'multi_factor': {
            'name': '多因子选股策略',
            'description': '综合基本面、技术面、资金面多因子选股',
            'entry_rules': [
                {'indicator': 'fundamental', 'condition': 'pe_below_30', 'weight': 20},
                {'indicator': 'technical', 'condition': 'ma_bullish', 'weight': 30},
                {'indicator': 'fund_flow', 'condition': 'main_force_inflow', 'weight': 30},
                {'indicator': 'sentiment', 'condition': 'positive_news', 'weight': 20},
            ],
            'exit_rules': [
                {'indicator': 'technical', 'condition': 'ma_bearish', 'weight': 40},
                {'indicator': 'fundamental', 'condition': 'valuation_high', 'weight': 30},
            ],
            'position_rules': {
                'max_position_per_stock': 0.2,
                'max_total_position': 0.8,
            },
            'risk_rules': {
                'stop_loss': 0.10,
                'take_profit': 0.20,
                'max_hold_days': 30,
            }
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_strategy(
        self,
        name: str,
        strategy_type: str,
        description: Optional[str] = None,
        entry_rules: Optional[List[Dict]] = None,
        exit_rules: Optional[List[Dict]] = None,
        position_rules: Optional[Dict] = None,
        risk_rules: Optional[Dict] = None,
        user_id: int = 1
    ) -> Dict:
        """创建策略"""
        try:
            # 获取模板
            template = self.STRATEGY_TEMPLATES.get(strategy_type, {})
            
            strategy = Strategy(
                user_id=user_id,
                name=name,
                description=description or template.get('description', ''),
                strategy_type=strategy_type,
                entry_rules=entry_rules or template.get('entry_rules', []),
                exit_rules=exit_rules or template.get('exit_rules', []),
                position_rules=position_rules or template.get('position_rules', {}),
                risk_rules=risk_rules or template.get('risk_rules', {}),
                is_active=1
            )
            
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            
            return self._build_strategy_response(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建策略失败: {e}")
            raise
    
    def get_strategies(self, user_id: int = 1) -> List[Dict]:
        """获取策略列表"""
        try:
            strategies = self.db.query(Strategy).filter(
                Strategy.user_id == user_id,
                Strategy.is_active == 1
            ).order_by(Strategy.created_at.desc()).all()
            
            return [self._build_strategy_response(s) for s in strategies]
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            raise
    
    def get_strategy(self, strategy_id: int, user_id: int = 1) -> Optional[Dict]:
        """获取策略详情"""
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                return None
            
            return self._build_strategy_response(strategy)
            
        except Exception as e:
            logger.error(f"获取策略详情失败: {e}")
            raise
    
    def update_strategy(
        self,
        strategy_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        entry_rules: Optional[List[Dict]] = None,
        exit_rules: Optional[List[Dict]] = None,
        position_rules: Optional[Dict] = None,
        risk_rules: Optional[Dict] = None,
        is_active: Optional[int] = None,
        user_id: int = 1
    ) -> Dict:
        """更新策略"""
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            if name is not None:
                strategy.name = name
            if description is not None:
                strategy.description = description
            if entry_rules is not None:
                strategy.entry_rules = entry_rules
            if exit_rules is not None:
                strategy.exit_rules = exit_rules
            if position_rules is not None:
                strategy.position_rules = position_rules
            if risk_rules is not None:
                strategy.risk_rules = risk_rules
            if is_active is not None:
                strategy.is_active = is_active
            
            self.db.commit()
            self.db.refresh(strategy)
            
            return self._build_strategy_response(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新策略失败: {e}")
            raise
    
    def delete_strategy(self, strategy_id: int, user_id: int = 1) -> bool:
        """删除策略（软删除）"""
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            strategy.is_active = 0
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除策略失败: {e}")
            raise
    
    def get_strategy_templates(self) -> List[Dict]:
        """获取策略模板列表"""
        templates = []
        for key, template in self.STRATEGY_TEMPLATES.items():
            templates.append({
                'type': key,
                'name': template['name'],
                'description': template['description']
            })
        return templates
    
    def generate_signals(
        self,
        strategy_id: int,
        symbols: List[str],
        user_id: int = 1
    ) -> List[Dict]:
        """
        基于策略生成交易信号
        注：这是简化版，实际应该基于历史数据和技术指标计算
        """
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            signals = []
            
            # 获取市场数据服务
            from app.services.market_data import get_market_data_service
            market_service = get_market_data_service()
            
            for symbol in symbols:
                try:
                    # 获取实时数据
                    price_data = market_service.get_stock_price_realtime(symbol)
                    
                    if not price_data:
                        continue
                    
                    # 简化：基于策略类型生成信号
                    signal = self._calculate_signal(
                        strategy, symbol, price_data
                    )
                    
                    if signal:
                        # 保存信号
                        db_signal = StrategySignal(
                            user_id=user_id,
                            strategy_id=strategy_id,
                            symbol=symbol,
                            name=price_data.get('name', ''),
                            signal_type=signal['type'],
                            strength=signal['strength'],
                            suggested_position=signal['position'],
                            trigger_price=price_data.get('current'),
                            stop_loss_price=signal.get('stop_loss'),
                            take_profit_price=signal.get('take_profit'),
                            reason=signal['reason'],
                            status='pending'
                        )
                        
                        self.db.add(db_signal)
                        signals.append(self._build_signal_response(db_signal))
                
                except Exception as e:
                    logger.warning(f"生成信号失败 {symbol}: {e}")
                    continue
            
            self.db.commit()
            return signals
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"生成信号失败: {e}")
            raise
    
    def get_signals(
        self,
        strategy_id: Optional[int] = None,
        status: Optional[str] = None,
        user_id: int = 1
    ) -> List[Dict]:
        """获取策略信号列表"""
        try:
            query = self.db.query(StrategySignal).filter(
                StrategySignal.user_id == user_id
            )
            
            if strategy_id:
                query = query.filter(StrategySignal.strategy_id == strategy_id)
            if status:
                query = query.filter(StrategySignal.status == status)
            
            signals = query.order_by(StrategySignal.created_at.desc()).all()
            
            return [self._build_signal_response(s) for s in signals]
            
        except Exception as e:
            logger.error(f"获取信号列表失败: {e}")
            raise
    
    def update_signal_status(
        self,
        signal_id: int,
        status: str,
        user_id: int = 1
    ) -> bool:
        """更新信号状态"""
        try:
            signal = self.db.query(StrategySignal).filter(
                StrategySignal.id == signal_id,
                StrategySignal.user_id == user_id
            ).first()
            
            if not signal:
                raise ValueError(f"信号不存在: {signal_id}")
            
            signal.status = status
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新信号状态失败: {e}")
            raise
    
    def _calculate_signal(
        self,
        strategy: Strategy,
        symbol: str,
        price_data: Dict
    ) -> Optional[Dict]:
        """计算交易信号（简化版）"""
        current_price = price_data.get('current', 0)
        change_rate = price_data.get('change_rate', 0)
        
        # 获取风控规则
        risk_rules = strategy.risk_rules or {}
        stop_loss_pct = risk_rules.get('stop_loss', 0.08)
        take_profit_pct = risk_rules.get('take_profit', 0.15)
        
        signal = None
        
        # 基于策略类型判断
        if strategy.strategy_type == 'trend_following':
            # 趋势跟踪：涨幅3-7%可能突破
            if 3 <= change_rate <= 7:
                signal = {
                    'type': 'buy',
                    'strength': min(int(change_rate), 10),
                    'position': 0.2,
                    'stop_loss': round(current_price * (1 - stop_loss_pct), 2),
                    'take_profit': round(current_price * (1 + take_profit_pct), 2),
                    'reason': f'趋势突破，涨幅{change_rate:.1f}%'
                }
        
        elif strategy.strategy_type == 'mean_reversion':
            # 均值回归：超跌-5%以下
            if change_rate <= -5:
                signal = {
                    'type': 'buy',
                    'strength': min(int(abs(change_rate)), 10),
                    'position': 0.15,
                    'stop_loss': round(current_price * (1 - stop_loss_pct), 2),
                    'take_profit': round(current_price * (1 + take_profit_pct / 2), 2),
                    'reason': f'超跌反弹机会，跌幅{abs(change_rate):.1f}%'
                }
        
        elif strategy.strategy_type == 'breakout':
            # 突破：涨幅>7%可能涨停
            if change_rate >= 7:
                signal = {
                    'type': 'buy',
                    'strength': min(int(change_rate), 10),
                    'position': 0.25,
                    'stop_loss': round(current_price * (1 - stop_loss_pct), 2),
                    'take_profit': round(current_price * (1 + take_profit_pct * 1.5), 2),
                    'reason': f'强势突破，涨幅{change_rate:.1f}%'
                }
        
        return signal
    
    def _build_strategy_response(self, strategy: Strategy) -> Dict:
        """构建策略响应"""
        return {
            'id': strategy.id,
            'name': strategy.name,
            'description': strategy.description,
            'strategyType': strategy.strategy_type,
            'entryRules': strategy.entry_rules,
            'exitRules': strategy.exit_rules,
            'positionRules': strategy.position_rules,
            'riskRules': strategy.risk_rules,
            'isActive': strategy.is_active,
            'totalTrades': strategy.total_trades,
            'winningTrades': strategy.winning_trades,
            'losingTrades': strategy.losing_trades,
            'totalReturn': strategy.total_return,
            'maxDrawdown': strategy.max_drawdown,
            'sharpeRatio': strategy.sharpe_ratio,
            'createdAt': strategy.created_at.isoformat() if strategy.created_at else None
        }
    
    def _build_signal_response(self, signal: StrategySignal) -> Dict:
        """构建信号响应"""
        return {
            'id': signal.id,
            'strategyId': signal.strategy_id,
            'symbol': signal.symbol,
            'name': signal.name,
            'signalType': signal.signal_type,
            'strength': signal.strength,
            'suggestedPosition': signal.suggested_position,
            'triggerPrice': signal.trigger_price,
            'stopLossPrice': signal.stop_loss_price,
            'takeProfitPrice': signal.take_profit_price,
            'reason': signal.reason,
            'status': signal.status,
            'isRead': signal.is_read,
            'createdAt': signal.created_at.isoformat() if signal.created_at else None
        }
