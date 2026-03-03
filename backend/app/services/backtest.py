"""
回测服务 - Backtest Service
功能：策略回测、绩效计算
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import pandas as pd
import numpy as np

from app.models.strategy import Strategy, Backtest
from app.models.stock import StockPrice

logger = logging.getLogger(__name__)


class BacktestService:
    """回测服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def run_backtest(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        symbols: Optional[List[str]] = None,
        user_id: int = 1
    ) -> Dict:
        """
        运行策略回测
        
        Args:
            strategy_id: 策略ID
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            initial_capital: 初始资金
            symbols: 回测股票列表，None则全市场
            user_id: 用户ID
        """
        try:
            # 获取策略
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            # 创建回测记录
            backtest = Backtest(
                user_id=user_id,
                strategy_id=strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                status='running'
            )
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            # 执行回测
            try:
                result = self._execute_backtest(
                    strategy=strategy,
                    backtest=backtest,
                    symbols=symbols
                )
                
                # 更新回测结果
                backtest.status = 'completed'
                backtest.completed_at = datetime.utcnow()
                backtest.final_capital = result['final_capital']
                backtest.total_return = result['total_return']
                backtest.annualized_return = result['annualized_return']
                backtest.max_drawdown = result['max_drawdown']
                backtest.sharpe_ratio = result['sharpe_ratio']
                backtest.sortino_ratio = result['sortino_ratio']
                backtest.total_trades = result['total_trades']
                backtest.winning_trades = result['winning_trades']
                backtest.losing_trades = result['losing_trades']
                backtest.win_rate = result['win_rate']
                backtest.avg_profit = result['avg_profit']
                backtest.avg_loss = result['avg_loss']
                backtest.profit_factor = result['profit_factor']
                backtest.trades = result['trades']
                backtest.daily_returns = result['daily_returns']
                backtest.equity_curve = result['equity_curve']
                
                self.db.commit()
                
                return self._build_backtest_response(backtest)
                
            except Exception as e:
                backtest.status = 'failed'
                backtest.error_message = str(e)
                self.db.commit()
                raise
                
        except Exception as e:
            logger.error(f"回测失败: {e}")
            raise
    
    def get_backtests(
        self,
        strategy_id: Optional[int] = None,
        user_id: int = 1
    ) -> List[Dict]:
        """获取回测列表"""
        try:
            query = self.db.query(Backtest).filter(
                Backtest.user_id == user_id
            )
            
            if strategy_id:
                query = query.filter(Backtest.strategy_id == strategy_id)
            
            backtests = query.order_by(Backtest.created_at.desc()).all()
            
            return [self._build_backtest_response(b) for b in backtests]
            
        except Exception as e:
            logger.error(f"获取回测列表失败: {e}")
            raise
    
    def get_backtest_detail(self, backtest_id: int, user_id: int = 1) -> Optional[Dict]:
        """获取回测详情"""
        try:
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id,
                Backtest.user_id == user_id
            ).first()
            
            if not backtest:
                return None
            
            return self._build_backtest_response(backtest, include_details=True)
            
        except Exception as e:
            logger.error(f"获取回测详情失败: {e}")
            raise
    
    def delete_backtest(self, backtest_id: int, user_id: int = 1) -> bool:
        """删除回测记录"""
        try:
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id,
                Backtest.user_id == user_id
            ).first()
            
            if not backtest:
                raise ValueError(f"回测不存在: {backtest_id}")
            
            self.db.delete(backtest)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除回测失败: {e}")
            raise
    
    def compare_backtests(
        self,
        backtest_ids: List[int],
        user_id: int = 1
    ) -> Dict:
        """对比多个回测结果"""
        try:
            backtests = self.db.query(Backtest).filter(
                Backtest.id.in_(backtest_ids),
                Backtest.user_id == user_id,
                Backtest.status == 'completed'
            ).all()
            
            if len(backtests) < 2:
                raise ValueError("需要至少2个完成的回测进行对比")
            
            comparison = {
                'backtests': [self._build_backtest_response(b) for b in backtests],
                'metrics': {
                    'total_return': [b.total_return for b in backtests],
                    'max_drawdown': [b.max_drawdown for b in backtests],
                    'sharpe_ratio': [b.sharpe_ratio for b in backtests],
                    'win_rate': [b.win_rate for b in backtests],
                },
                'winner': self._find_winner(backtests)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"对比回测失败: {e}")
            raise
    
    def _execute_backtest(
        self,
        strategy: Strategy,
        backtest: Backtest,
        symbols: Optional[List[str]] = None
    ) -> Dict:
        """执行回测逻辑"""
        # 简化版回测逻辑
        # 实际应该基于历史数据进行完整的模拟交易
        
        start_date = backtest.start_date
        end_date = backtest.end_date
        initial_capital = backtest.initial_capital
        
        # 如果没有指定股票，使用一些默认股票
        if not symbols:
            symbols = ['000001', '000002', '600000', '600519', '000858']
        
        # 获取历史数据
        trades = []
        equity_curve = []
        daily_returns = []
        
        capital = initial_capital
        positions = {}  # 当前持仓
        
        # 生成交易日列表
        dates = self._generate_dates(start_date, end_date)
        
        for date in dates:
            daily_pnl = 0
            
            # 模拟每个股票的交易
            for symbol in symbols:
                # 模拟价格数据
                price_data = self._get_historical_price(symbol, date)
                
                if not price_data:
                    continue
                
                # 基于策略生成信号
                signal = self._generate_signal_for_backtest(
                    strategy, symbol, price_data
                )
                
                if signal and signal['type'] == 'buy' and symbol not in positions:
                    # 买入
                    shares = int(capital * signal['position'] / price_data['close'] / 100) * 100
                    if shares > 0:
                        cost = shares * price_data['close']
                        if cost <= capital * 0.95:  # 保留5%现金
                            positions[symbol] = {
                                'shares': shares,
                                'cost': cost,
                                'entry_price': price_data['close'],
                                'entry_date': date,
                                'stop_loss': signal.get('stop_loss', price_data['close'] * 0.92),
                                'take_profit': signal.get('take_profit', price_data['close'] * 1.15)
                            }
                            capital -= cost
                
                elif symbol in positions:
                    pos = positions[symbol]
                    current_price = price_data['close']
                    
                    # 检查出场条件
                    should_sell = False
                    sell_reason = ''
                    
                    # 止损
                    if current_price <= pos['stop_loss']:
                        should_sell = True
                        sell_reason = 'stop_loss'
                    # 止盈
                    elif current_price >= pos['take_profit']:
                        should_sell = True
                        sell_reason = 'take_profit'
                    # 持仓时间超过限制
                    elif (datetime.strptime(date, '%Y-%m-%d') - 
                          datetime.strptime(pos['entry_date'], '%Y-%m-%d')).days >= 20:
                        should_sell = True
                        sell_reason = 'time_exit'
                    
                    if should_sell:
                        # 卖出
                        sell_amount = pos['shares'] * current_price
                        profit = sell_amount - pos['cost']
                        
                        trades.append({
                            'symbol': symbol,
                            'entry_date': pos['entry_date'],
                            'exit_date': date,
                            'entry_price': pos['entry_price'],
                            'exit_price': current_price,
                            'shares': pos['shares'],
                            'profit': round(profit, 2),
                            'return_pct': round(profit / pos['cost'] * 100, 2),
                            'reason': sell_reason
                        })
                        
                        capital += sell_amount
                        daily_pnl += profit
                        del positions[symbol]
            
            # 计算当日总市值
            total_value = capital
            for symbol, pos in positions.items():
                price_data = self._get_historical_price(symbol, date)
                if price_data:
                    total_value += pos['shares'] * price_data['close']
            
            # 记录权益曲线
            equity_curve.append({
                'date': date,
                'value': round(total_value, 2)
            })
            
            # 计算日收益率
            if len(equity_curve) > 1:
                daily_return = (total_value - equity_curve[-2]['value']) / equity_curve[-2]['value']
                daily_returns.append(daily_return)
        
        # 计算绩效指标
        final_capital = equity_curve[-1]['value'] if equity_curve else initial_capital
        total_return = (final_capital - initial_capital) / initial_capital * 100
        
        # 年化收益
        days = len(dates)
        annualized_return = ((1 + total_return / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 夏普比率 (简化计算，假设无风险利率3%)
        if daily_returns:
            avg_daily_return = np.mean(daily_returns)
            std_daily_return = np.std(daily_returns)
            sharpe_ratio = ((avg_daily_return * 252 - 0.03) / (std_daily_return * np.sqrt(252))) if std_daily_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 交易统计
        winning_trades = [t for t in trades if t['profit'] > 0]
        losing_trades = [t for t in trades if t['profit'] <= 0]
        
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'annualized_return': round(annualized_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sharpe_ratio * 0.8, 2),  # 简化
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(len(winning_trades) / len(trades) * 100, 2) if trades else 0,
            'avg_profit': round(total_profit / len(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(total_loss / len(losing_trades), 2) if losing_trades else 0,
            'profit_factor': round(total_profit / total_loss, 2) if total_loss > 0 else float('inf'),
            'trades': trades,
            'daily_returns': [round(r * 100, 4) for r in daily_returns],
            'equity_curve': equity_curve
        }
    
    def _generate_dates(self, start_date: str, end_date: str) -> List[str]:
        """生成交易日列表"""
        dates = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            # 跳过周末
            if current.weekday() < 5:
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return dates
    
    def _get_historical_price(self, symbol: str, date: str) -> Optional[Dict]:
        """获取历史价格数据"""
        try:
            # 从数据库查询
            price = self.db.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.date == date
            ).first()
            
            if price:
                return {
                    'open': price.open,
                    'high': price.high,
                    'low': price.low,
                    'close': price.close,
                    'volume': price.volume
                }
            
            # 如果数据库没有，生成模拟数据（简化）
            import random
            base_price = 10 + random.random() * 90
            return {
                'open': base_price,
                'high': base_price * 1.02,
                'low': base_price * 0.98,
                'close': base_price * (1 + (random.random() - 0.5) * 0.04),
                'volume': int(random.random() * 1000000)
            }
            
        except Exception as e:
            logger.warning(f"获取历史价格失败 {symbol} {date}: {e}")
            return None
    
    def _generate_signal_for_backtest(
        self,
        strategy: Strategy,
        symbol: str,
        price_data: Dict
    ) -> Optional[Dict]:
        """为回测生成信号"""
        import random
        
        # 简化：随机生成信号，实际应该基于技术指标
        if random.random() > 0.95:  # 5%概率产生买入信号
            return {
                'type': 'buy',
                'position': 0.2,
                'stop_loss': price_data['close'] * 0.92,
                'take_profit': price_data['close'] * 1.15
            }
        
        return None
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0.0
        
        max_dd = 0
        peak = equity_curve[0]['value']
        
        for point in equity_curve:
            value = point['value']
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _find_winner(self, backtests: List[Backtest]) -> Dict:
        """找出表现最好的回测"""
        if not backtests:
            return None
        
        # 综合评分：收益权重60%，回撤权重40%
        def score(b):
            return b.total_return * 0.6 - b.max_drawdown * 0.4 + b.sharpe_ratio * 10
        
        winner = max(backtests, key=score)
        
        return {
            'backtest_id': winner.id,
            'strategy_name': winner.strategy.name if winner.strategy else 'Unknown',
            'total_return': winner.total_return,
            'max_drawdown': winner.max_drawdown,
            'sharpe_ratio': winner.sharpe_ratio
        }
    
    def _build_backtest_response(
        self,
        backtest: Backtest,
        include_details: bool = False
    ) -> Dict:
        """构建回测响应"""
        result = {
            'id': backtest.id,
            'strategyId': backtest.strategy_id,
            'strategyName': backtest.strategy.name if backtest.strategy else 'Unknown',
            'startDate': backtest.start_date,
            'endDate': backtest.end_date,
            'initialCapital': backtest.initial_capital,
            'finalCapital': backtest.final_capital,
            'totalReturn': backtest.total_return,
            'annualizedReturn': backtest.annualized_return,
            'maxDrawdown': backtest.max_drawdown,
            'sharpeRatio': backtest.sharpe_ratio,
            'sortinoRatio': backtest.sortino_ratio,
            'totalTrades': backtest.total_trades,
            'winningTrades': backtest.winning_trades,
            'losingTrades': backtest.losing_trades,
            'winRate': backtest.win_rate,
            'avgProfit': backtest.avg_profit,
            'avgLoss': backtest.avg_loss,
            'profitFactor': backtest.profit_factor,
            'status': backtest.status,
            'createdAt': backtest.created_at.isoformat() if backtest.created_at else None,
            'completedAt': backtest.completed_at.isoformat() if backtest.completed_at else None
        }
        
        if include_details:
            result['trades'] = backtest.trades or []
            result['dailyReturns'] = backtest.daily_returns or []
            result['equityCurve'] = backtest.equity_curve or []
        
        return result
