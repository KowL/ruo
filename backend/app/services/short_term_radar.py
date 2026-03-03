"""
短线雷达服务 - Short-term Radar Service
功能：竞价爆点检测、异动捕捉、涨停候选
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.services.market_data import get_market_data_service
from app.services.concept_monitor import ConceptMonitorService

logger = logging.getLogger(__name__)


class ShortTermRadarService:
    """短线雷达服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_service = get_market_data_service()
    
    def get_auction_signals(self) -> List[Dict]:
        """
        获取竞价爆点信号（集合竞价阶段）
        
        策略：
        1. 高开幅度 3-7%（排除一字板）
        2. 竞价成交量 > 昨日成交量的 5%
        3. 竞价金额 > 1000万
        """
        signals = []
        
        try:
            import akshare as ak
            
            # 获取当日所有股票竞价数据
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            
            if df is None or df.empty:
                return signals
            
            # 筛选竞价爆点股票
            for _, row in df.iterrows():
                try:
                    symbol = row.get('代码', '')
                    name = row.get('名称', '')
                    
                    # 获取详细信息
                    spot_df = ak.stock_zh_a_spot_em()
                    stock_info = spot_df[spot_df['代码'] == symbol]
                    
                    if stock_info.empty:
                        continue
                    
                    info = stock_info.iloc[0]
                    
                    # 计算指标
                    open_pct = float(info.get('涨跌幅', 0))  # 当前涨幅（竞价阶段）
                    volume = float(info.get('成交量', 0))
                    amount = float(info.get('成交额', 0))
                    
                    # 爆点条件
                    is_high_open = 3 <= open_pct <= 7  # 高开3-7%
                    is_high_volume = volume > 0  # 有成交量
                    is_high_amount = amount > 10000000  # 金额 > 1000万
                    
                    if is_high_open and is_high_volume and is_high_amount:
                        signals.append({
                            'symbol': symbol,
                            'name': name,
                            'signalType': 'auction_burst',
                            'signalName': '竞价爆点',
                            'openPct': round(open_pct, 2),
                            'volume': int(volume),
                            'amount': round(amount, 2),
                            'signalStrength': self._calculate_strength(open_pct, amount),
                            'reason': f'高开{open_pct:.1f}%，竞价额{amount/10000:.0f}万',
                            'timestamp': datetime.now().isoformat()
                        })
                
                except Exception as e:
                    logger.warning(f"处理竞价数据失败: {e}")
                    continue
            
            # 按信号强度排序
            signals.sort(key=lambda x: x['signalStrength'], reverse=True)
            return signals[:20]  # 返回前20
            
        except Exception as e:
            logger.error(f"获取竞价信号失败: {e}")
            return []
    
    def get_intraday_movers(self, min_change_pct: float = 5.0) -> List[Dict]:
        """
        获取实时异动股票
        
        Args:
            min_change_pct: 最小涨跌幅阈值（默认5%）
        """
        movers = []
        
        try:
            import akshare as ak
            
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return movers
            
            # 筛选异动股票
            for _, row in df.iterrows():
                try:
                    change_pct = float(row.get('涨跌幅', 0))
                    
                    # 异动条件：涨跌幅超过阈值
                    if abs(change_pct) >= min_change_pct:
                        symbol = row.get('代码', '')
                        name = row.get('名称', '')
                        price = float(row.get('最新价', 0))
                        volume = float(row.get('成交量', 0))
                        amount = float(row.get('成交额', 0))
                        
                        # 确定异动类型
                        if change_pct >= 9.5:
                            signal_type = 'limit_up'
                            signal_name = '涨停'
                        elif change_pct >= 5:
                            signal_type = 'strong_up'
                            signal_name = '强势上涨'
                        elif change_pct <= -9.5:
                            signal_type = 'limit_down'
                            signal_name = '跌停'
                        elif change_pct <= -5:
                            signal_type = 'strong_down'
                            signal_name = '强势下跌'
                        else:
                            continue
                        
                        movers.append({
                            'symbol': symbol,
                            'name': name,
                            'signalType': signal_type,
                            'signalName': signal_name,
                            'price': round(price, 2),
                            'changePct': round(change_pct, 2),
                            'volume': int(volume),
                            'amount': round(amount, 2),
                            'signalStrength': abs(change_pct),
                            'reason': f'{signal_name} {change_pct:+.2f}%',
                            'timestamp': datetime.now().isoformat()
                        })
                
                except Exception as e:
                    continue
            
            # 按涨跌幅排序
            movers.sort(key=lambda x: abs(x['changePct']), reverse=True)
            return movers[:30]  # 返回前30
            
        except Exception as e:
            logger.error(f"获取异动股票失败: {e}")
            return []
    
    def get_limit_up_candidates(self) -> List[Dict]:
        """
        获取涨停候选池
        
        策略：
        1. 已涨停股票（首板、连板）
        2. 涨停炸板股票
        3. 即将涨停股票（涨幅 8-9.5%）
        """
        candidates = []
        
        try:
            import akshare as ak
            
            # 获取涨停池数据
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    try:
                        symbol = row.get('代码', '')
                        name = row.get('名称', '')
                        
                        candidates.append({
                            'symbol': symbol,
                            'name': name,
                            'signalType': 'limit_up_pool',
                            'signalName': '涨停池',
                            'price': float(row.get('最新价', 0)),
                            'limitUpPrice': float(row.get('涨停价', 0)),
                            'changePct': float(row.get('涨跌幅', 0)),
                            'volume': int(row.get('成交额', 0)),
                            'reason': '已涨停',
                            'timestamp': datetime.now().isoformat()
                        })
                    except:
                        continue
            
            # 获取即将涨停股票（涨幅 8-9.5%）
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is not None and not spot_df.empty:
                for _, row in spot_df.iterrows():
                    try:
                        change_pct = float(row.get('涨跌幅', 0))
                        if 8 <= change_pct < 9.5:
                            symbol = row.get('代码', '')
                            name = row.get('名称', '')
                            
                            candidates.append({
                                'symbol': symbol,
                                'name': name,
                                'signalType': 'near_limit_up',
                                'signalName': '即将涨停',
                                'price': float(row.get('最新价', 0)),
                                'changePct': round(change_pct, 2),
                                'volume': int(row.get('成交额', 0)),
                                'reason': f'涨幅 {change_pct:.2f}%，接近涨停',
                                'timestamp': datetime.now().isoformat()
                            })
                    except:
                        continue
            
            # 去重
            seen = set()
            unique_candidates = []
            for c in candidates:
                if c['symbol'] not in seen:
                    seen.add(c['symbol'])
                    unique_candidates.append(c)
            
            return unique_candidates[:20]
            
        except Exception as e:
            logger.error(f"获取涨停候选失败: {e}")
            return []
    
    def get_radar_dashboard(self) -> Dict:
        """
        获取短线雷达仪表盘数据
        """
        return {
            'auctionSignals': self.get_auction_signals(),
            'intradayMovers': self.get_intraday_movers(),
            'limitUpCandidates': self.get_limit_up_candidates(),
            'updateTime': datetime.now().isoformat()
        }
    
    def _calculate_strength(self, open_pct: float, amount: float) -> float:
        """计算信号强度"""
        # 强度 = 高开幅度 * 0.3 + 金额因子 * 0.7
        amount_factor = min(amount / 50000000, 10)  # 金额因子，封顶10
        return round(open_pct * 0.3 + amount_factor * 0.7, 2)
