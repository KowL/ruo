"""
每日市场简报服务
Daily Market Report Service

自动生成开盘/收盘分析报告
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
import logging

from app.services.sentiment import SentimentService
from app.services.concept_monitor import ConceptMonitorService

logger = logging.getLogger(__name__)


class DailyReportService:
    """每日市场简报服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sentiment_service = SentimentService(db)
        self.concept_service = ConceptMonitorService()
    
    def generate_opening_report(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成开盘简报
        
        **包含内容:**
        - 情绪指数概览
        - 热门板块排行
        - 开盘建议
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        # 获取情绪指数（使用统一的 SentimentService）
        sentiment = self.sentiment_service.get_latest_sentiment()
        
        # 获取板块排行
        try:
            top_sectors = self.concept_service.get_concept_movement_ranking(5)
        except Exception as e:
            logger.warning(f"获取板块排行失败: {e}")
            top_sectors = []
        
        # 生成建议
        suggestion = self._generate_opening_suggestion(sentiment, top_sectors)
        
        return {
            'type': 'opening_report',
            'date': target_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'sentiment': {
                'index': sentiment.get('index', 50.0),
                'label': sentiment.get('label', '中性'),
                'change': sentiment.get('change', 0),
            },
            'top_sectors': top_sectors[:5],
            'suggestion': suggestion,
            'key_points': self._extract_key_points(sentiment)
        }
    
    def generate_closing_report(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成收盘简报
        
        **包含内容:**
        - 全天情绪回顾
        - 板块资金流向
        - 涨停概念统计
        - 明日展望
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        sentiment = self.sentiment_service.get_latest_sentiment()
        
        # 获取资金流向
        try:
            fund_flow = self.concept_service.get_fund_flow_ranking(5)
        except Exception as e:
            logger.warning(f"获取资金流向失败: {e}")
            fund_flow = []
        
        # 获取涨停统计
        try:
            limit_up = self.concept_service.get_limit_up_statistics()
        except Exception as e:
            logger.warning(f"获取涨停统计失败: {e}")
            limit_up = {}
        
        return {
            'type': 'closing_report',
            'date': target_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'sentiment': sentiment,
            'fund_flow': fund_flow[:5],
            'limit_up': limit_up,
            'outlook': self._generate_outlook(sentiment, fund_flow)
        }
    
    def _generate_opening_suggestion(self, sentiment: Dict, sectors: List) -> str:
        """生成开盘建议"""
        index = sentiment.get('index', 50.0)
        change = sentiment.get('change', 0)
        
        if index >= 70 and change > 0:
            return "市场情绪高涨，建议关注强势股，注意控制仓位避免追高。"
        elif index >= 60:
            return "市场情绪偏乐观，可适当参与热点板块，关注资金流入方向。"
        elif index >= 45:
            return "市场情绪中性，建议观望为主，等待明确方向。"
        elif index >= 30:
            return "市场情绪偏悲观，谨慎操作，关注防御性板块。"
        else:
            return "市场情绪低迷，建议控制仓位，等待企稳信号。"
    
    def _extract_key_points(self, sentiment: Dict) -> List[str]:
        """提取关键要点（基于市场行情数据）"""
        points = []
        adv = sentiment.get('advance_count', 0)
        dec = sentiment.get('decline_count', 0)
        avg_chg = sentiment.get('avg_change_pct', 0)
        mood = sentiment.get('market_mood', '正常')

        if adv > dec:
            points.append(f"持仓上涨居多（{adv}涨 / {dec}跌）")
        elif dec > adv:
            points.append(f"持仓下跌居多（{adv}涨 / {dec}跌）")
        else:
            points.append(f"持仓涨跌均衡（{adv}涨 / {dec}跌）")

        if avg_chg > 0.5:
            points.append(f"持仓平均涨幅{avg_chg:.2f}%")
        elif avg_chg < -0.5:
            points.append(f"持仓平均跌幅{abs(avg_chg):.2f}%")

        if mood != '正常':
            points.append(f"市场交投{mood}")

        change = sentiment.get('change', 0)
        if change > 3:
            points.append("情绪指数呈上升趋势")
        elif change < -3:
            points.append("情绪指数呈下降趋势")

        return points
    
    def _generate_outlook(self, sentiment: Dict, fund_flow: List) -> str:
        """生成明日展望"""
        index = sentiment.get('index', 50.0)
        
        if index >= 65:
            return "市场情绪积极，明日有望延续反弹，关注资金持续流入板块。"
        elif index >= 50:
            return "市场情绪平稳，明日可能维持震荡，关注板块轮动机会。"
        else:
            return "市场情绪偏弱，明日可能承压，关注支撑位和情绪修复信号。"


# 工厂函数
def get_daily_report_service(db: Session) -> DailyReportService:
    """获取每日简报服务"""
    return DailyReportService(db)
