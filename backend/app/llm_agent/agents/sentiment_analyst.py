"""
舆论分析师节点 - 分析市场情绪和新闻舆论
"""
import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import re
from llm_factory import LLMFactory
from app.llm_agent.state.stock_analysis_state import StockAnalysisState, SentimentAnalysisResult

logger = logging.getLogger(__name__)

class SentimentAnalyst:
    """舆论分析师"""

    def __init__(self):
        self.llm = LLMFactory.get_instance()

    def analyze_sentiment(self, state: StockAnalysisState) -> StockAnalysisState:
        """舆论分析主函数"""
        try:
            logger.info("开始舆论分析...")

            selected_stocks = state.get("selected_stocks", [])
            if not selected_stocks:
                state["error"] = "没有选中的股票进行舆论分析"
                return state

            # 分析每只股��的舆论情况
            sentiment_results = {}
            for stock in selected_stocks:
                try:
                    analysis = self._analyze_single_stock_sentiment(stock)
                    sentiment_results[stock["code"]] = analysis
                except Exception as e:
                    logger.warning(f"分析股票 {stock['code']} 舆论情况失败: {str(e)}")
                    sentiment_results[stock["code"]] = self._get_default_sentiment_analysis(stock)

            # 生成舆论分析报告
            sentiment_report = self._generate_sentiment_report(sentiment_results, selected_stocks)

            # 更新状态
            state["sentiment_analysis"] = {
                "individual_analysis": sentiment_results,
                "sentiment_report": sentiment_report,
                "analysis_time": datetime.now().isoformat()
            }
            state["next_action"] = "investment_decision"

            logger.info("舆论分析完成")
            return state

        except Exception as e:
            logger.error(f"舆论分析失败: {str(e)}")
            state["error"] = f"舆论分析失败: {str(e)}"
            return state

    def _analyze_single_stock_sentiment(self, stock: Dict) -> SentimentAnalysisResult:
        """分析单只股票的舆论情况"""
        code = stock["code"]
        name = stock["name"]

        # 获取新闻数据
        news_data = self._get_stock_news(code, name)

        # 分析新闻情绪
        news_sentiment = self._analyze_news_sentiment(news_data, name)

        # 获取社交媒体情绪（模拟）
        social_sentiment = self._analyze_social_sentiment(code, name)

        # 获取分析师评级
        analyst_ratings = self._get_analyst_ratings(code)

        # 计算市场关注度
        market_attention = self._calculate_market_attention(news_data, stock)

        # 判断情绪趋势
        sentiment_trend = self._determine_sentiment_trend(news_sentiment, social_sentiment)

        # 识别关键事件
        key_events = self._identify_key_events(news_data, name)

        result: SentimentAnalysisResult = {
            "news_sentiment": news_sentiment,
            "social_sentiment": social_sentiment,
            "analyst_ratings": analyst_ratings,
            "market_attention": market_attention,
            "sentiment_trend": sentiment_trend,
            "key_events": key_events
        }

        return result

    def _get_stock_news(self, code: str, name: str) -> List[Dict[str, Any]]:
        """获取股票相关新闻"""
        try:
            # 由于akshare新闻API可能不稳定，使用模拟数据
            # 实际应用中可以接入其他新闻API
            logger.info(f"尝试获取股票 {name}({code}) 的新闻信息")

            # 模拟新闻数据
            mock_news = [
                {
                    "title": f"{name}股价表现分析",
                    "content": f"市场对{name}的关注度持续上升，投资者对其未来发展前景保持乐观态度。",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "财经资讯",
                    "url": ""
                }
            ]

            return mock_news

        except Exception as e:
            logger.warning(f"获取股票 {code} 新闻失败: {str(e)}")
            return []

    def _analyze_news_sentiment(self, news_data: List[Dict], stock_name: str) -> float:
        """分析新闻情绪"""
        try:
            if not news_data:
                return 50.0  # 中性

            # 使用AI分析新闻情绪
            news_texts = []
            for news in news_data[:5]:  # 分析前5条新闻
                news_texts.append(f"标题: {news['title']}\n内容: {news['content'][:200]}")

            if not news_texts:
                return 50.0

            prompt = f"""
作为专业的金融情绪分析师，请分析以下关于{stock_name}的新闻情绪。

新闻内容：
{chr(10).join(news_texts)}

请从以下角度评估新闻情绪：
1. 整体情绪倾向（正面/负面/中性）
2. 对股价的潜在影响
3. 市场预期变化

请给出0-100的情绪评分：
- 0-30: 非常负面
- 30-45: 偏负面
- 45-55: 中性
- 55-70: 偏正面
- 70-100: 非常正面

只需要返回数字评分，不需要解释。
"""

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # 提取数字评分
            score_match = re.search(r'\d+', content)
            if score_match:
                score = float(score_match.group())
                return max(0, min(score, 100))

            # 如果无法提取数字，使用关键词分析
            return self._keyword_sentiment_analysis(news_texts)

        except Exception as e:
            logger.warning(f"分析新闻情绪失败: {str(e)}")
            return 50.0

    def _keyword_sentiment_analysis(self, news_texts: List[str]) -> float:
        """基于关键词的情绪分析"""
        positive_keywords = [
            "上涨", "增长", "利好", "突破", "创新", "合作", "收购", "业绩", "盈利",
            "扩张", "投资", "发展", "机会", "优势", "领先", "成功", "提升"
        ]

        negative_keywords = [
            "下跌", "下降", "利空", "风险", "亏损", "减少", "困难", "问题", "危机",
            "调查", "处罚", "违规", "退市", "停牌", "暂停", "警告", "下调"
        ]

        positive_count = 0
        negative_count = 0

        for text in news_texts:
            for keyword in positive_keywords:
                positive_count += text.count(keyword)
            for keyword in negative_keywords:
                negative_count += text.count(keyword)

        total_count = positive_count + negative_count
        if total_count == 0:
            return 50.0

        positive_ratio = positive_count / total_count
        return 50 + (positive_ratio - 0.5) * 100

    def _analyze_social_sentiment(self, code: str, name: str) -> float:
        """分析社交媒体情绪（模拟实现）"""
        try:
            # 由于无法直接获取社交媒体数据，这里基于股票表现进行模拟
            # 实际应用中可以接入微博、股吧等API

            # 获取股票基本信息
            try:
                df = ak.stock_zh_a_spot_em()
                stock_row = df[df["代码"] == code]

                if not stock_row.empty:
                    change_pct = float(stock_row.iloc[0].get("涨跌幅", 0))
                    turnover_rate = float(stock_row.iloc[0].get("换手率", 0))

                    # 基于涨跌幅和换手率模拟社交情绪
                    sentiment = 50.0

                    # 涨跌幅影响
                    if change_pct > 5:
                        sentiment += 20
                    elif change_pct > 2:
                        sentiment += 10
                    elif change_pct > 0:
                        sentiment += 5
                    elif change_pct < -5:
                        sentiment -= 20
                    elif change_pct < -2:
                        sentiment -= 10
                    elif change_pct < 0:
                        sentiment -= 5

                    # 换手率影响（高换手率表示关注度高）
                    if turnover_rate > 10:
                        sentiment += 5
                    elif turnover_rate > 5:
                        sentiment += 3

                    return max(0, min(sentiment, 100))

            except Exception:
                pass

            return 50.0  # 默认中性

        except Exception as e:
            logger.warning(f"分析社交媒体情绪失败: {str(e)}")
            return 50.0

    def _get_analyst_ratings(self, code: str) -> Dict[str, Any]:
        """获取分析师评级"""
        try:
            # 尝试获取分析师评级数据
            # 由于akshare可能没有直接的分析师评级接口，这里进行模拟

            return {
                "buy_count": 0,
                "hold_count": 0,
                "sell_count": 0,
                "average_target_price": 0.0,
                "rating_trend": "无数据",
                "last_update": datetime.now().strftime("%Y-%m-%d")
            }

        except Exception as e:
            logger.warning(f"获取分析师评级失败: {str(e)}")
            return {
                "buy_count": 0,
                "hold_count": 0,
                "sell_count": 0,
                "average_target_price": 0.0,
                "rating_trend": "获取失败",
                "last_update": datetime.now().strftime("%Y-%m-%d")
            }

    def _calculate_market_attention(self, news_data: List[Dict], stock: Dict) -> float:
        """计算市场关注度"""
        try:
            attention_score = 0.0

            # 新闻数量贡献 (40%)
            news_count = len(news_data)
            news_score = min(news_count * 10, 40)  # 每条新闻10分，最高40分
            attention_score += news_score

            # 换手率贡献 (30%)
            turnover_rate = stock.get("turnover_rate", 0)
            turnover_score = min(turnover_rate * 2, 30)  # 换手率*2，最高30分
            attention_score += turnover_score

            # 涨跌幅贡献 (20%)
            change_pct = abs(stock.get("change_pct", 0))
            change_score = min(change_pct * 2, 20)  # 涨跌幅绝对值*2，最高20分
            attention_score += change_score

            # 成交量贡献 (10%)
            volume = stock.get("volume", 0)
            if volume > 0:
                # 简化的成交量评分
                volume_score = min(10, 10)  # 有成交量就给10分
                attention_score += volume_score

            return min(attention_score, 100)

        except Exception as e:
            logger.warning(f"计算市场关注度失败: {str(e)}")
            return 50.0

    def _determine_sentiment_trend(self, news_sentiment: float, social_sentiment: float) -> str:
        """判断情绪趋势"""
        try:
            avg_sentiment = (news_sentiment + social_sentiment) / 2

            if avg_sentiment >= 70:
                return "情绪高涨"
            elif avg_sentiment >= 55:
                return "情绪偏乐观"
            elif avg_sentiment >= 45:
                return "情绪中性"
            elif avg_sentiment >= 30:
                return "情绪偏悲观"
            else:
                return "情绪低迷"

        except Exception as e:
            logger.warning(f"判断情绪趋势失败: {str(e)}")
            return "情绪不明"

    def _identify_key_events(self, news_data: List[Dict], stock_name: str) -> List[Dict[str, Any]]:
        """识别关键事件"""
        try:
            key_events = []

            # 关键词列表
            important_keywords = [
                "重组", "并购", "收购", "分拆", "上市", "退市",
                "业绩", "财报", "分红", "增发", "回购",
                "合作", "签约", "中标", "获得", "批准",
                "调查", "处罚", "违规", "停牌", "复牌",
                "涨停", "跌停", "突破", "创新高", "创新低"
            ]

            for news in news_data[:5]:  # 检查前5条新闻
                title = news.get("title", "")
                content = news.get("content", "")

                # 检查是否包含关键词
                found_keywords = []
                for keyword in important_keywords:
                    if keyword in title or keyword in content:
                        found_keywords.append(keyword)

                if found_keywords:
                    event = {
                        "title": title,
                        "time": news.get("time", ""),
                        "keywords": found_keywords,
                        "importance": len(found_keywords),  # 关键词数量表示重要性
                        "source": news.get("source", "")
                    }
                    key_events.append(event)

            # 按重要性排序
            key_events.sort(key=lambda x: x["importance"], reverse=True)

            return key_events[:5]  # 返回最多5个关键事件

        except Exception as e:
            logger.warning(f"识别关键事件失败: {str(e)}")
            return []

    def _get_default_sentiment_analysis(self, stock: Dict) -> SentimentAnalysisResult:
        """获取默认舆论分析结果"""
        return {
            "news_sentiment": 50.0,
            "social_sentiment": 50.0,
            "analyst_ratings": {
                "buy_count": 0,
                "hold_count": 0,
                "sell_count": 0,
                "average_target_price": 0.0,
                "rating_trend": "无数据",
                "last_update": datetime.now().strftime("%Y-%m-%d")
            },
            "market_attention": 50.0,
            "sentiment_trend": "数据不足",
            "key_events": []
        }

    def _generate_sentiment_report(self, results: Dict, stocks: List[Dict]) -> str:
        """生成舆论分析报告"""
        try:
            report_lines = ["# 舆论分析报告", ""]

            # 整体舆论概况
            total_stocks = len(stocks)
            positive_sentiment_count = sum(
                1 for r in results.values()
                if (r["news_sentiment"] + r["social_sentiment"]) / 2 > 60
            )
            negative_sentiment_count = sum(
                1 for r in results.values()
                if (r["news_sentiment"] + r["social_sentiment"]) / 2 < 40
            )

            report_lines.append("## 整体舆论概况")
            report_lines.append(f"- 分析股票总数：{total_stocks}只")
            report_lines.append(f"- 舆论偏正面股票：{positive_sentiment_count}只")
            report_lines.append(f"- 舆论偏负面股票：{negative_sentiment_count}只")
            report_lines.append("")

            # 市场关注度排行
            attention_ranking = sorted(
                [(stock, results[stock["code"]]) for stock in stocks],
                key=lambda x: x[1]["market_attention"],
                reverse=True
            )

            report_lines.append("## 市场关注度排行")
            for i, (stock, analysis) in enumerate(attention_ranking[:5], 1):
                attention = analysis["market_attention"]
                sentiment_avg = (analysis["news_sentiment"] + analysis["social_sentiment"]) / 2
                sentiment_desc = "正面" if sentiment_avg > 60 else "负面" if sentiment_avg < 40 else "中性"

                report_lines.append(f"{i}. **{stock['name']}({stock['code']})** - 关注度: {attention:.1f}, 情绪: {sentiment_desc}")

            report_lines.append("")

            # 重点股票舆论分析
            report_lines.append("## 重点股票舆论分析")

            for stock, analysis in attention_ranking[:3]:  # 显示前3只关注度最高的
                report_lines.append(f"### {stock['name']}({stock['code']})")

                # 情绪评分
                news_sentiment = analysis["news_sentiment"]
                social_sentiment = analysis["social_sentiment"]
                report_lines.append(f"**新闻情绪**: {news_sentiment:.1f}/100")
                report_lines.append(f"**社交情绪**: {social_sentiment:.1f}/100")
                report_lines.append(f"**情绪趋势**: {analysis['sentiment_trend']}")
                report_lines.append(f"**市场关注度**: {analysis['market_attention']:.1f}/100")

                # 关键事件
                key_events = analysis["key_events"]
                if key_events:
                    report_lines.append("**关键事件**:")
                    for event in key_events[:3]:
                        report_lines.append(f"- {event['title']} ({event['time']})")

                report_lines.append("")

            # 舆论特征总结
            report_lines.append("## 舆论特征总结")

            # 情绪趋势分布
            sentiment_trends = [r["sentiment_trend"] for r in results.values()]
            trend_counts = {}
            for trend in sentiment_trends:
                trend_counts[trend] = trend_counts.get(trend, 0) + 1

            if trend_counts:
                report_lines.append("- **情绪趋势分布**:")
                for trend, count in sorted(trend_counts.items(), key=lambda x: x[1], reverse=True):
                    if trend != "数据不足":
                        report_lines.append(f"  - {trend}: {count}只")

            # 关键事件统计
            all_events = []
            for analysis in results.values():
                all_events.extend(analysis["key_events"])

            if all_events:
                # 统计关键词频率
                keyword_counts = {}
                for event in all_events:
                    for keyword in event["keywords"]:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

                if keyword_counts:
                    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    report_lines.append("- **热门关键词**:")
                    for keyword, count in top_keywords:
                        report_lines.append(f"  - {keyword}: {count}次")

            return "\n".join(report_lines)

        except Exception as e:
            logger.error(f"生成舆论分析报告失败: {str(e)}")
            return "舆论分析报告生成失败"

def sentiment_analyst_node(state: StockAnalysisState) -> StockAnalysisState:
    """舆论分析师节点入口函数"""
    analyst = SentimentAnalyst()
    return analyst.analyze_sentiment(state)