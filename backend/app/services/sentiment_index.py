"""
市场情绪指数计算服务
Market Sentiment Index Service

计算方法:
1. 基于AI分析的新闻情绪
2. 加权计算每日情绪指数 (0-100)
3. 支持多维度情绪指标
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import func
from sqlalchemy.orm import Session
import json
import logging

from app.models.news import News

logger = logging.getLogger(__name__)


class SentimentIndexService:
    """市场情绪指数服务"""
    
    # 情感标签映射到基础分数
    SENTIMENT_SCORE_MAP = {
        '重大利好': 100,
        '利好': 70,
        '中性': 50,
        '利空': 30,
        '重大利空': 0
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_daily_sentiment(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        计算每日市场情绪指数
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            {
                'date': '2026-03-02',
                'overall_index': 58.5,  # 0-100 总体情绪指数
                'label': '中性偏乐观',   # 情绪标签
                'news_count': 45,        # 参与计算的新闻数
                'breakdown': {
                    'positive': 20,      # 利好新闻数
                    'neutral': 15,       # 中性新闻数
                    'negative': 10       # 利空新闻数
                },
                'avg_score': 3.2,        # 平均星级 (1-5)
                'trend': 'up',           # 趋势 up/down/flat
                'sectors': {             # 分板块情绪
                    '科技': 65.0,
                    '金融': 52.0,
                    '能源': 48.0
                }
            }
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        # 获取当日已分析的新闻
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        
        news_list = self.db.query(News).filter(
            News.publish_time >= start_dt,
            News.publish_time < end_dt,
            News.ai_analysis != None
        ).all()
        
        if not news_list:
            logger.warning(f"{target_date} 没有已分析的新闻数据")
            return self._generate_default_sentiment(target_date)
        
        # 解析情感数据
        sentiment_data = []
        for news in news_list:
            try:
                analysis = json.loads(news.ai_analysis)
                sentiment_data.append({
                    'label': analysis.get('sentiment_label', '中性'),
                    'score': analysis.get('sentiment_score', 3),
                    'source': news.source,
                    'time': news.publish_time
                })
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"解析新闻分析结果失败: {e}")
                continue
        
        if not sentiment_data:
            return self._generate_default_sentiment(target_date)
        
        # 计算总体指数 (0-100)
        total_score = sum(d['score'] for d in sentiment_data)
        avg_score = total_score / len(sentiment_data)
        overall_index = (avg_score / 5) * 100  # 转换为 0-100
        
        # 统计分布
        breakdown = {'positive': 0, 'neutral': 0, 'negative': 0}
        for d in sentiment_data:
            label = d['label']
            if label in ['利好', '重大利好']:
                breakdown['positive'] += 1
            elif label in ['利空', '重大利空']:
                breakdown['negative'] += 1
            else:
                breakdown['neutral'] += 1
        
        # 生成情绪标签
        label = self._get_sentiment_label(overall_index)
        
        # 计算趋势 (与前一天比较)
        trend = self._calculate_trend(target_date, overall_index)
        
        return {
            'date': target_date.isoformat(),
            'overall_index': round(overall_index, 1),
            'label': label,
            'news_count': len(sentiment_data),
            'breakdown': breakdown,
            'avg_score': round(avg_score, 2),
            'trend': trend,
            'sectors': {}  # TODO: 按板块分类
        }
    
    def get_sentiment_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取历史情绪指数
        
        Args:
            days: 天数
            
        Returns:
            历史情绪指数列表
        """
        results = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            sentiment = self.calculate_daily_sentiment(date)
            results.append(sentiment)
        
        return results
    
    def get_latest_sentiment(self) -> Dict[str, Any]:
        """获取最新情绪指数"""
        return self.calculate_daily_sentiment()
    
    def _get_sentiment_label(self, index: float) -> str:
        """根据指数生成情绪标签"""
        if index >= 80:
            return '极度乐观'
        elif index >= 65:
            return '乐观'
        elif index >= 55:
            return '中性偏乐观'
        elif index >= 45:
            return '中性'
        elif index >= 35:
            return '中性偏悲观'
        elif index >= 20:
            return '悲观'
        else:
            return '极度悲观'
    
    def _calculate_trend(self, target_date: date, current_index: float) -> str:
        """计算趋势 (与前一天比较)"""
        prev_date = target_date - timedelta(days=1)
        prev_sentiment = self.calculate_daily_sentiment(prev_date)
        
        if prev_sentiment['news_count'] == 0:
            return 'flat'
        
        prev_index = prev_sentiment['overall_index']
        diff = current_index - prev_index
        
        if diff > 5:
            return 'up'
        elif diff < -5:
            return 'down'
        else:
            return 'flat'
    
    def _generate_default_sentiment(self, target_date: date) -> Dict[str, Any]:
        """生成默认情绪数据"""
        return {
            'date': target_date.isoformat(),
            'overall_index': 50.0,
            'label': '中性',
            'news_count': 0,
            'breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
            'avg_score': 3.0,
            'trend': 'flat',
            'sectors': {}
        }


# 单例服务
_sentiment_service = None

def get_sentiment_service(db: Session) -> SentimentIndexService:
    """获取情绪指数服务"""
    return SentimentIndexService(db)
