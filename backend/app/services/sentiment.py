"""
市场情绪指数服务
Market Sentiment Index Service

基于 AI 分析的新闻情感数据，计算每日市场情绪指数（纯量化，无LLM依赖）
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
import json
from collections import defaultdict

from app.models.news import News


class SentimentService:
    """市场情绪指数服务"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_latest_sentiment(self) -> Dict:
        """
        获取最新情绪指数
        
        Returns:
            {
                "date": "2026-03-02",
                "index": 54.4,  # 0-100，50为中性
                "change": 21.3,  # 较昨日变化
                "label": "谨慎乐观",  # 极度恐慌/恐慌/谨慎/中性/谨慎乐观/乐观/极度乐观
                "bullish": 107,  # 利好数量
                "bearish": 85,   # 利空数量  
                "neutral": 60,   # 中性数量
                "avg_score": 3.13,  # 平均评分 1-5
                "news_count": 252,  # 新闻总数
                "top_factors": ["中东局势", "AI技术突破", "新能源政策"]  # 主要影响因素
            }
        """
        today = datetime.now().date()
        
        # 获取今日数据
        today_data = self._calculate_daily_sentiment(today)
        
        # 获取昨日数据计算变化
        yesterday = today - timedelta(days=1)
        yesterday_data = self._calculate_daily_sentiment(yesterday)
        
        change = today_data['index'] - yesterday_data['index']
        
        return {
            "date": today.isoformat(),
            "index": round(today_data['index'], 1),
            "change": round(change, 1),
            "label": self._get_sentiment_label(today_data['index']),
            "bullish": today_data['bullish'],
            "bearish": today_data['bearish'],
            "neutral": today_data['neutral'],
            "avg_score": round(today_data['avg_score'], 2),
            "news_count": today_data['count'],
            "top_factors": today_data.get('top_factors', [])
        }
    
    def get_sentiment_history(self, days: int = 7) -> List[Dict]:
        """
        获取历史情绪指数走势
        
        Args:
            days: 返回最近 N 天的数据
            
        Returns:
            [
                {"date": "2026-03-02", "index": 54.4, "label": "谨慎乐观"},
                {"date": "2026-03-01", "index": 33.1, "label": "恐慌"},
                ...
            ]
        """
        results = []
        today = datetime.now().date()
        
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            data = self._calculate_daily_sentiment(d)
            if data['count'] > 0:  # 只返回有数据的日子
                results.append({
                    "date": d.isoformat(),
                    "index": round(data['index'], 1),
                    "label": self._get_sentiment_label(data['index']),
                    "news_count": data['count']
                })
        
        return results
    
    def _calculate_daily_sentiment(self, target_date: date) -> Dict:
        """
        计算单日情绪数据
        """
        # 查询目标日期的新闻（按 publish_time 或 created_at）
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
        
        news_list = self.db.query(News).filter(
            News.ai_analysis != None,
            ((News.publish_time >= start_dt) & (News.publish_time < end_dt)) |
            ((News.publish_time == None) & (News.created_at >= start_dt) & (News.created_at < end_dt))
        ).all()
        
        if not news_list:
            return {
                'index': 50.0,
                'bullish': 0,
                'bearish': 0,
                'neutral': 0,
                'avg_score': 3.0,
                'count': 0,
                'top_factors': []
            }
        
        bullish = bearish = neutral = 0
        total_score = 0
        
        for news in news_list:
            try:
                analysis = json.loads(news.ai_analysis)
                label = analysis.get('sentiment_label', '中性')
                score = analysis.get('sentiment_score', 3)
                
                if label == '利好':
                    bullish += 1
                elif label == '利空':
                    bearish += 1
                else:
                    neutral += 1
                    
                total_score += score
            except:
                pass
        
        total = bullish + bearish + neutral
        
        # 计算情绪指数 (0-100)，50为中性基准
        if total > 0:
            # 基于利好利空差的指数计算
            sentiment_index = 50 + (bullish - bearish) / total * 50
            # 结合平均分进行微调
            avg_score = total_score / total
            # 将 1-5 分映射到 -10~+10 的微调
            score_adjustment = (avg_score - 3) * 5
            sentiment_index = max(0, min(100, sentiment_index + score_adjustment))
        else:
            sentiment_index = 50.0
            avg_score = 3.0
        
        # 提取主要影响因素（通过 LLM 或关键词统计）
        top_factors = self._extract_key_factors(news_list[:20]) if news_list else []
        
        return {
            'index': sentiment_index,
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'avg_score': avg_score,
            'count': total,
            'top_factors': top_factors
        }
    
    def _get_sentiment_label(self, index: float) -> str:
        """
        根据指数获取情绪标签
        """
        if index >= 90:
            return "极度乐观"
        elif index >= 75:
            return "乐观"
        elif index >= 60:
            return "谨慎乐观"
        elif index >= 45:
            return "中性"
        elif index >= 30:
            return "谨慎"
        elif index >= 15:
            return "恐慌"
        else:
            return "极度恐慌"
    
    def _extract_key_factors(self, news_list: List[News]) -> List[str]:
        """
        提取主要影响因素
        简单实现：基于关键词频率统计
        """
        # 关键词映射
        keyword_mapping = {
            '中东': '中东局势',
            '伊朗': '中东局势',
            '以色列': '中东局势',
            'AI': 'AI技术突破',
            '人工智能': 'AI技术突破',
            '光模块': 'AI技术突破',
            '新能源': '新能源政策',
            '光伏': '新能源政策',
            '锂电': '新能源政策',
            '美联储': '美联储政策',
            '加息': '美联储政策',
            '降息': '美联储政策',
            '通胀': '通胀数据',
            'CPI': '通胀数据',
            '关税': '贸易政策',
            '中美': '贸易政策',
        }
        
        factor_counts = defaultdict(int)
        
        for news in news_list:
            title = news.title or ''
            for keyword, factor in keyword_mapping.items():
                if keyword in title:
                    factor_counts[factor] += 1
        
        # 返回前3个主要因素
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_factors[:3]]
    
    def generate_daily_report(self, report_type: str = 'opening') -> Dict:
        """
        生成每日简报（开盘/收盘）- 量化规则生成，无AI依赖
        
        Args:
            report_type: 'opening' 开盘简报 | 'closing' 收盘简报
        """
        sentiment = self.get_latest_sentiment()
        history = self.get_sentiment_history(days=5)
        
        # 基于量化数据生成报告（规则模板）
        if report_type == 'opening':
            report_content = self._generate_opening_report(sentiment, history)
        else:
            report_content = self._generate_closing_report(sentiment, history)
        
        return {
            "date": sentiment['date'],
            "type": report_type,
            "sentiment_index": sentiment['index'],
            "sentiment_label": sentiment['label'],
            "report": report_content,
            "key_factors": sentiment['top_factors']
        }
    
    def _generate_opening_report(self, sentiment: Dict, history: List[Dict]) -> str:
        """生成开盘简报 - 量化规则"""
        index = sentiment['index']
        change = sentiment['change']
        label = sentiment['label']
        
        # 情绪状态解读
        if index >= 60:
            mood_desc = "市场情绪偏乐观，投资者信心较足"
        elif index >= 45:
            mood_desc = "市场情绪中性，投资者保持观望"
        elif index >= 30:
            mood_desc = "市场情绪偏谨慎，投资者风险偏好下降"
        else:
            mood_desc = "市场情绪低迷，投资者情绪偏悲观"
        
        # 变化趋势
        if change >= 10:
            trend_desc = f"情绪指数较昨日大幅回升(+{change})，情绪明显改善"
        elif change >= 5:
            trend_desc = f"情绪指数较昨日有所回升(+{change})，情绪转暖"
        elif change > -5:
            trend_desc = f"情绪指数与昨日基本持平({change})，情绪稳定"
        elif change > -10:
            trend_desc = f"情绪指数较昨日有所下降({change})，情绪转冷"
        else:
            trend_desc = f"情绪指数较昨日明显下降({change})，情绪恶化"
        
        # 操作建议
        if index >= 70:
            suggestion = "建议积极布局，但需警惕过热风险"
        elif index >= 55:
            suggestion = "建议适度参与，关注结构性机会"
        elif index >= 45:
            suggestion = "建议中性仓位，等待方向明确"
        elif index >= 30:
            suggestion = "建议控制仓位，防御为主"
        else:
            suggestion = "建议减仓观望，等待情绪修复"
        
        # 主要因素
        factors = sentiment['top_factors']
        factor_text = "、".join(factors) if factors else "暂无明确主导因素"
        
        report = f"""【开盘情绪简报】

{mood_desc}。{trend_desc}。

主要影响因素：{factor_text}。今日市场共采集{sentiment['news_count']}条新闻，其中利好{sentiment['bullish']}条、利空{sentiment['bearish']}条、中性{sentiment['neutral']}条，平均评分{sentiment['avg_score']}/5.0。

操作建议：{suggestion}。"""
        
        return report
    
    def _generate_closing_report(self, sentiment: Dict, history: List[Dict]) -> str:
        """生成收盘简报 - 量化规则"""
        index = sentiment['index']
        change = sentiment['change']
        label = sentiment['label']
        
        # 今日回顾
        if index >= 60:
            review = "今日市场情绪偏暖，资金活跃度较高"
        elif index >= 45:
            review = "今日市场情绪平稳，多空双方相对均衡"
        elif index >= 30:
            review = "今日市场情绪偏冷，交投趋于谨慎"
        else:
            review = "今日市场情绪低迷，避险情绪升温"
        
        # 关键因素
        factors = sentiment['top_factors']
        if factors:
            key_events = f"主要驱动因素：{factors[0]}"
            if len(factors) > 1:
                key_events += f"、{factors[1]}"
        else:
            key_events = "市场暂无重大事件驱动"
        
        # 明日展望
        if change >= 5:
            outlook = "情绪回暖态势有望延续"
        elif change <= -5:
            outlook = "需警惕情绪继续下行风险"
        else:
            outlook = "情绪或维持震荡格局"
        
        # 策略建议
        if index >= 55:
            strategy = "保持适度仓位，关注业绩确定性强的标的"
        elif index >= 45:
            strategy = "灵活控制仓位，逢低布局优质标的"
        else:
            strategy = "降低仓位，等待情绪企稳后再介入"
        
        report = f"""【收盘情绪总结】

{review}。情绪指数收于{index}（{label}），{key_events}。全天{sentiment['news_count']}条新闻中，利好{sentiment['bullish']}条、利空{sentiment['bearish']}条。

明日展望：{outlook}。

策略建议：{strategy}。"""
        
        return report


# 服务单例
_sentiment_service = None

def get_sentiment_service(db: Session) -> SentimentService:
    """获取情绪指数服务"""
    return SentimentService(db)
