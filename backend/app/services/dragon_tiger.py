"""
龙虎榜分析服务 - Dragon-Tiger List Analysis Service
功能：龙虎榜数据获取、游资动向分析、热门席位识别
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
import logging
import pandas as pd

from app.utils.stock_tool import stock_tool

logger = logging.getLogger(__name__)


class DragonTigerService:
    """龙虎榜分析服务"""
    
    # 知名游资席位映射
    FAMOUS_SEATS = {
        '东方财富证券股份有限公司拉萨团结路第一证券营业部': '拉萨军团',
        '东方财富证券股份有限公司拉萨团结路第二证券营业部': '拉萨军团',
        '东方财富证券股份有限公司拉萨东环路第一证券营业部': '拉萨军团',
        '东方财富证券股份有限公司拉萨东环路第二证券营业部': '拉萨军团',
        '国泰君安证券股份有限公司南京太平南路证券营业部': '作手新一',
        '国盛证券股份有限公司宁波桑田路证券营业部': '桑田路',
        '华鑫证券有限责任公司上海分公司': '炒股养家',
        '华鑫证券有限责任公司上海宛平南路证券营业部': '炒股养家',
        '中国银河证券股份有限公司绍兴证券营业部': '赵老哥',
        '华泰证券股份有限公司深圳益田路荣超商务中心证券营业部': '荣超投资',
        '中信证券股份有限公司上海溧阳路证券营业部': '溧阳路',
        '中信证券股份有限公司上海瑞金南路证券营业部': '瑞金南路',
        '国泰君安证券股份有限公司上海江苏路证券营业部': '章盟主',
        '招商证券股份有限公司深圳深南东路证券营业部': '深南东路',
        '兴业证券股份有限公司陕西分公司': '方新侠',
        '中信证券股份有限公司深圳分公司': '中信深圳',
        '华鑫证券有限责任公司深圳分公司': '华鑫深圳',
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_lhb(self, date: Optional[str] = None) -> List[Dict]:
        """
        获取每日龙虎榜数据
        
        Args:
            date: 日期，格式 YYYY-MM-DD，默认为今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        formatted_date = date.replace('-', '')
        
        try:
            # 获取龙虎榜详情
            df = stock_tool.get_dragon_tiger_data(start_date=formatted_date, end_date=formatted_date)
            
            if df is None or df.empty:
                return []
            
            results = []
            for _, row in df.iterrows():
                try:
                    results.append({
                        'symbol': str(row.get('代码', '')),
                        'name': row.get('名称', ''),
                        'date': date,
                        'closePrice': float(row.get('收盘价', 0)),
                        'changePct': float(row.get('涨跌幅', 0)),
                        'netBuyAmount': float(row.get('净买额', 0)),
                        'buyAmount': float(row.get('买入额', 0)),
                        'sellAmount': float(row.get('卖出额', 0)),
                        'totalAmount': float(row.get('龙虎榜成交额', 0)),
                        'reason': row.get('上榜原因', ''),
                    })
                except Exception as e:
                    logger.warning(f"处理龙虎榜数据失败: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            return []
    
    def get_stock_lhb_detail(self, symbol: str, days: int = 5) -> List[Dict]:
        """
        获取个股近期龙虎榜详情
        
        Args:
            symbol: 股票代码
            days: 查询天数
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = stock_tool.get_stock_dragon_tiger_detail(
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                symbol=symbol
            )
            
            if df is None or df.empty:
                return []
            
            results = []
            for _, row in df.iterrows():
                try:
                    results.append({
                        'date': row.get('日期', ''),
                        'closePrice': float(row.get('收盘价', 0)),
                        'changePct': float(row.get('涨跌幅', 0)),
                        'netBuyAmount': float(row.get('龙虎榜净买额', 0)),
                        'buyAmount': float(row.get('龙虎榜买入额', 0)),
                        'sellAmount': float(row.get('龙虎榜卖出额', 0)),
                        'totalAmount': float(row.get('龙虎榜成交额', 0)),
                        'turnover': float(row.get('市场总成交额', 0)),
                        'reason': row.get('上榜原因', ''),
                    })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"获取个股龙虎榜失败: {e}")
            return []
    
    def get_institutional_trading(self, date: Optional[str] = None) -> List[Dict]:
        """
        获取机构专用席位交易数据
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        formatted_date = date.replace('-', '')
        
        try:
            df = stock_tool.get_institutional_dragon_tiger(start_date=formatted_date, end_date=formatted_date)
            
            if df is None or df.empty:
                return []
            
            results = []
            for _, row in df.iterrows():
                try:
                    results.append({
                        'symbol': str(row.get('代码', '')),
                        'name': row.get('名称', ''),
                        'date': date,
                        'closePrice': float(row.get('收盘价', 0)),
                        'changePct': float(row.get('涨跌幅', 0)),
                        'netBuyAmount': float(row.get('机构净买额', 0)),
                        'buyAmount': float(row.get('机构买入额', 0)),
                        'sellAmount': float(row.get('机构卖出额', 0)),
                        'buyCount': int(row.get('机构买入次数', 0)),
                        'sellCount': int(row.get('机构卖出次数', 0)),
                    })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"获取机构交易数据失败: {e}")
            return []
    
    def analyze_hot_seats(self, days: int = 5) -> List[Dict]:
        """
        分析热门游资席位
        
        Args:
            days: 分析天数
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取营业部排行数据
            df = stock_tool.get_dragon_tiger_yyb_rank(
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            
            if df is None or df.empty:
                return []
            
            results = []
            for _, row in df.head(20).iterrows():
                try:
                    seat_name = row.get('营业部名称', '')
                    
                    # 识别知名游资
                    trader_name = self.FAMOUS_SEATS.get(seat_name, '未知')
                    
                    results.append({
                        'seatName': seat_name,
                        'traderName': trader_name,
                        'buyCount': int(row.get('买入次数', 0)),
                        'sellCount': int(row.get('卖出次数', 0)),
                        'totalBuy': float(row.get('买入金额', 0)),
                        'totalSell': float(row.get('卖出金额', 0)),
                        'netAmount': float(row.get('净买额', 0)),
                        'avgBuy': float(row.get('买入额均值', 0)),
                        'avgSell': float(row.get('卖出额均值', 0)),
                        'isFamous': trader_name != '未知'
                    })
                except Exception as e:
                    continue
            
            # 按净买入金额排序
            results.sort(key=lambda x: x['netAmount'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"分析热门席位失败: {e}")
            return []
    
    def get_famous_traders_activity(self, days: int = 3) -> Dict:
        """
        获取知名游资近期动向
        """
        try:
            hot_seats = self.analyze_hot_seats(days=days)
            
            # 筛选知名游资
            famous_traders = [s for s in hot_seats if s['isFamous']]
            
            # 按游资分组统计
            trader_stats = defaultdict(lambda: {
                'buyCount': 0,
                'sellCount': 0,
                'totalBuy': 0,
                'totalSell': 0,
                'netAmount': 0,
                'seats': []
            })
            
            for seat in hot_seats:
                if seat['isFamous']:
                    name = seat['traderName']
                    trader_stats[name]['buyCount'] += seat['buyCount']
                    trader_stats[name]['sellCount'] += seat['sellCount']
                    trader_stats[name]['totalBuy'] += seat['totalBuy']
                    trader_stats[name]['totalSell'] += seat['totalSell']
                    trader_stats[name]['netAmount'] += seat['netAmount']
                    trader_stats[name]['seats'].append(seat['seatName'])
            
            # 转换为列表
            results = []
            for name, stats in trader_stats.items():
                results.append({
                    'traderName': name,
                    **stats,
                    'seats': list(set(stats['seats']))  # 去重
                })
            
            # 按净买入排序
            results.sort(key=lambda x: x['netAmount'], reverse=True)
            
            return {
                'famousTraders': results,
                'topTrader': results[0] if results else None,
                'analysisDays': days,
                'updateTime': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取游资动向失败: {e}")
            return {'famousTraders': [], 'topTrader': None}
    
    def analyze_market_sentiment(self, date: Optional[str] = None) -> Dict:
        """
        基于龙虎榜分析市场情绪
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        daily_data = self.get_daily_lhb(date)
        institutional_data = self.get_institutional_trading(date)
        
        if not daily_data:
            return {'sentiment': 'neutral', 'score': 50}
        
        # 计算总净买入
        total_net_buy = sum(d['netBuyAmount'] for d in daily_data)
        
        # 计算机构净买入
        inst_net_buy = sum(d['netBuyAmount'] for d in institutional_data)
        
        # 统计涨停股数量
        limit_up_count = sum(1 for d in daily_data if d['changePct'] >= 9.5)
        
        # 情绪判断
        if total_net_buy > 500000000:  # 净买入 > 5亿
            sentiment = 'very_positive'
            score = 85
        elif total_net_buy > 100000000:  # 净买入 > 1亿
            sentiment = 'positive'
            score = 70
        elif total_net_buy < -100000000:  # 净卖出 > 1亿
            sentiment = 'negative'
            score = 30
        else:
            sentiment = 'neutral'
            score = 50
        
        return {
            'date': date,
            'sentiment': sentiment,
            'sentimentName': {
                'very_positive': '非常积极',
                'positive': '积极',
                'neutral': '中性',
                'negative': '消极'
            }.get(sentiment, '中性'),
            'score': score,
            'totalNetBuy': round(total_net_buy, 2),
            'institutionalNetBuy': round(inst_net_buy, 2),
            'limitUpCount': limit_up_count,
            'totalStocks': len(daily_data),
            'analysis': f'龙虎榜净买入{total_net_buy/100000000:.2f}亿，{"机构" if inst_net_buy > 0 else "游资"}主导'
        }
    
    def get_lhb_dashboard(self, date: Optional[str] = None) -> Dict:
        """
        获取龙虎榜仪表盘数据
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'dailyData': self.get_daily_lhb(date),
            'institutionalData': self.get_institutional_trading(date),
            'hotSeats': self.analyze_hot_seats(days=5),
            'famousTraders': self.get_famous_traders_activity(days=3),
            'marketSentiment': self.analyze_market_sentiment(date),
            'updateTime': datetime.now().isoformat()
        }
