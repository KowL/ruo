"""
板块分析师节点 - 分析股票所属板块的整体情况
"""
import akshare as ak
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from collections import Counter
from llm_factory import LLMFactory
from app.llm_agent.state.stock_analysis_state import StockAnalysisState, SectorAnalysisResult

logger = logging.getLogger(__name__)

class SectorAnalyst:
    """板块分析师"""

    def __init__(self):
        self.llm = LLMFactory.get_instance()

    def analyze_sectors(self, state: StockAnalysisState) -> StockAnalysisState:
        """板块分析主函数"""
        try:
            logger.info("开始板块分析...")

            selected_stocks = state.get("selected_stocks", [])
            if not selected_stocks:
                state["error"] = "没有选中的股票进行板块分析"
                return state

            # 统计板块分布
            sector_distribution = self._analyze_sector_distribution(selected_stocks)

            # 分析主要板块
            sector_analysis = {}
            for sector, stocks in sector_distribution.items():
                if len(stocks) >= 2:  # 只分析包含2只以上股票的板块
                    analysis = self._analyze_single_sector(sector, stocks)
                    sector_analysis[sector] = analysis

            # 生成板块分析报告
            sector_report = self._generate_sector_report(sector_analysis, sector_distribution)

            # 更新状态
            state["sector_analysis"] = {
                "sector_distribution": sector_distribution,
                "detailed_analysis": sector_analysis,
                "sector_report": sector_report,
                "analysis_time": datetime.now().isoformat()
            }
            state["next_action"] = "short_term_analysis"

            logger.info("板块分析完成")
            return state

        except Exception as e:
            logger.error(f"板块分析失败: {str(e)}")
            state["error"] = f"板块分析失败: {str(e)}"
            return state

    def _analyze_sector_distribution(self, stocks: List[Dict]) -> Dict[str, List[Dict]]:
        """分析板块分布"""
        sector_stocks = {}

        for stock in stocks:
            sector = stock.get("sector", "未知")
            if sector not in sector_stocks:
                sector_stocks[sector] = []
            sector_stocks[sector].append(stock)

        # 按股票数量排序
        sorted_sectors = dict(sorted(sector_stocks.items(), key=lambda x: len(x[1]), reverse=True))

        return sorted_sectors

    def _analyze_single_sector(self, sector_name: str, stocks: List[Dict]) -> SectorAnalysisResult:
        """分析单个板块"""
        try:
            # 获取板块整体数据
            sector_performance = self._get_sector_performance(sector_name)

            # 分析板块内股票表现
            stock_performance = self._analyze_stocks_in_sector(stocks)

            # 获取板块新闻
            sector_news = self._get_sector_news(sector_name)

            # 识别龙头股票
            leading_stocks = self._identify_leading_stocks(stocks)

            # 计算板块评分
            sector_score = self._calculate_sector_score(sector_performance, stock_performance)

            # 识别风险因素
            risk_factors = self._identify_risk_factors(sector_name, stocks, sector_performance)

            # AI分析板块趋势
            sector_trend = self._analyze_sector_trend_with_ai(
                sector_name, sector_performance, stock_performance, sector_news
            )

            result: SectorAnalysisResult = {
                "sector_name": sector_name,
                "sector_performance": sector_performance,
                "sector_trend": sector_trend,
                "leading_stocks": leading_stocks,
                "sector_news": sector_news,
                "sector_score": sector_score,
                "risk_factors": risk_factors
            }

            return result

        except Exception as e:
            logger.error(f"分析板块 {sector_name} 失败: {str(e)}")
            return {
                "sector_name": sector_name,
                "sector_performance": {},
                "sector_trend": f"分析失败: {str(e)}",
                "leading_stocks": [],
                "sector_news": [],
                "sector_score": 0.0,
                "risk_factors": ["数据获取失败"]
            }

    def _get_sector_performance(self, sector_name: str) -> Dict[str, float]:
        """获取板块整体表现"""
        try:
            # 获取板块指数数据
            df = ak.stock_board_industry_spot_em()

            # 查找对应板块
            if "板块名称" in df.columns:
                sector_row = df[df["板块名称"].str.contains(sector_name, na=False)]
            else:
                # 如果列名不匹配，返回默认值
                logger.warning(f"板块数据列名不匹配，无法获取 {sector_name} 板块数据")
                return {"change_pct": 0.0, "volume_ratio": 1.0, "leading_change": 0.0}

            if sector_row.empty:
                return {"change_pct": 0.0, "volume_ratio": 1.0, "leading_change": 0.0}

            row = sector_row.iloc[0]

            performance = {
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume_ratio": float(row.get("换手率", 1)),
                "leading_change": float(row.get("领涨股涨跌幅", 0)),
                "up_count": int(row.get("上涨家数", 0)),
                "down_count": int(row.get("下跌家数", 0)),
                "total_count": int(row.get("总家数", 1))
            }

            return performance

        except Exception as e:
            logger.warning(f"获取板块 {sector_name} 表现数据失败: {str(e)}")
            return {"change_pct": 0.0, "volume_ratio": 1.0, "leading_change": 0.0}

    def _analyze_stocks_in_sector(self, stocks: List[Dict]) -> Dict[str, Any]:
        """分析板块内股票表现"""
        if not stocks:
            return {}

        changes = [stock["change_pct"] for stock in stocks]
        turnovers = [stock["turnover_rate"] for stock in stocks]
        market_caps = [stock["market_cap"] for stock in stocks]

        return {
            "avg_change": sum(changes) / len(changes),
            "max_change": max(changes),
            "min_change": min(changes),
            "avg_turnover": sum(turnovers) / len(turnovers),
            "total_market_cap": sum(market_caps),
            "stock_count": len(stocks),
            "up_count": len([c for c in changes if c > 0]),
            "down_count": len([c for c in changes if c < 0])
        }

    def _get_sector_news(self, sector_name: str) -> List[Dict[str, Any]]:
        """获取板块相关新闻"""
        try:
            # 获取财经新闻
            news_df = ak.stock_news_em()

            # 筛选相关新闻
            related_news = []
            for _, row in news_df.head(20).iterrows():
                title = str(row.get("新闻标题", ""))
                content = str(row.get("新闻内容", ""))

                if sector_name in title or sector_name in content:
                    news_item = {
                        "title": title,
                        "content": content[:200] + "..." if len(content) > 200 else content,
                        "time": str(row.get("发布时间", "")),
                        "source": str(row.get("新闻来源", ""))
                    }
                    related_news.append(news_item)

            return related_news[:5]  # 返回最多5条相关新闻

        except Exception as e:
            logger.warning(f"获取板块 {sector_name} 新闻失败: {str(e)}")
            return []

    def _identify_leading_stocks(self, stocks: List[Dict]) -> List[str]:
        """识别板块龙头股票"""
        if not stocks:
            return []

        # 按市值和涨幅综合排序
        scored_stocks = []
        for stock in stocks:
            # 综合评分：市值权重40% + 涨幅权重30% + 换手率权重30%
            market_cap_score = min(stock["market_cap"] / 1e10, 10)  # 市值评分，最高10分
            change_score = max(0, stock["change_pct"])  # 涨幅评分
            turnover_score = min(stock["turnover_rate"], 20)  # 换手率评分，最高20分

            total_score = market_cap_score * 0.4 + change_score * 0.3 + turnover_score * 0.3

            scored_stocks.append({
                "code": stock["code"],
                "name": stock["name"],
                "score": total_score
            })

        # 排序并返回前3名
        scored_stocks.sort(key=lambda x: x["score"], reverse=True)
        return [f"{stock['name']}({stock['code']})" for stock in scored_stocks[:3]]

    def _calculate_sector_score(self, sector_perf: Dict, stock_perf: Dict) -> float:
        """计算板块评分"""
        try:
            score = 50.0  # 基础分

            # 板块涨幅贡献 (30%)
            change_pct = sector_perf.get("change_pct", 0)
            if change_pct > 5:
                score += 15
            elif change_pct > 2:
                score += 10
            elif change_pct > 0:
                score += 5
            elif change_pct < -5:
                score -= 15
            elif change_pct < -2:
                score -= 10

            # 上涨股票比例贡献 (25%)
            up_ratio = stock_perf.get("up_count", 0) / max(stock_perf.get("stock_count", 1), 1)
            score += up_ratio * 25

            # 平均换手率贡献 (20%)
            avg_turnover = stock_perf.get("avg_turnover", 0)
            if avg_turnover > 10:
                score += 20
            elif avg_turnover > 5:
                score += 15
            elif avg_turnover > 2:
                score += 10

            # 股票数量贡献 (15%)
            stock_count = stock_perf.get("stock_count", 0)
            if stock_count >= 5:
                score += 15
            elif stock_count >= 3:
                score += 10
            elif stock_count >= 2:
                score += 5

            # 市值规模贡献 (10%)
            total_cap = stock_perf.get("total_market_cap", 0)
            if total_cap > 1000e8:  # 1000亿以上
                score += 10
            elif total_cap > 500e8:
                score += 7
            elif total_cap > 100e8:
                score += 5

            return min(max(score, 0), 100)  # 限制在0-100之间

        except Exception as e:
            logger.warning(f"计算板块评分失败: {str(e)}")
            return 50.0

    def _identify_risk_factors(self, sector_name: str, stocks: List[Dict], sector_perf: Dict) -> List[str]:
        """识别风险因素"""
        risk_factors = []

        try:
            # 估值风险
            high_pe_stocks = [s for s in stocks if s.get("pe_ratio") and s["pe_ratio"] > 100]
            if len(high_pe_stocks) > len(stocks) * 0.5:
                risk_factors.append("板块整体估值偏高，超过50%股票PE>100")

            # 涨幅过大风险
            avg_change = sum(s["change_pct"] for s in stocks) / len(stocks)
            if avg_change > 8:
                risk_factors.append("板块平均涨幅过大，存在回调风险")

            # 换手率异常
            avg_turnover = sum(s["turnover_rate"] for s in stocks) / len(stocks)
            if avg_turnover > 15:
                risk_factors.append("板块换手率过高，资金博弈激烈")

            # 板块集中度风险
            if len(stocks) < 3:
                risk_factors.append("板块股票数量较少，集中度风险较高")

            # 市场环境风险
            sector_change = sector_perf.get("change_pct", 0)
            if sector_change < -3:
                risk_factors.append("板块整体表现疲弱，市场情绪偏空")

        except Exception as e:
            logger.warning(f"识别风险因素失败: {str(e)}")
            risk_factors.append("风险评估数据不完整")

        return risk_factors if risk_factors else ["暂无明显风险"]

    def _analyze_sector_trend_with_ai(self, sector_name: str, sector_perf: Dict,
                                    stock_perf: Dict, news: List[Dict]) -> str:
        """使用AI分析板块趋势"""
        try:
            prompt = f"""
作为专业的板块分析师，请分析{sector_name}板块的当前趋势和未来走向。

板块整体表现：
- 板块涨跌幅：{sector_perf.get('change_pct', 0):.2f}%
- 上涨股票数：{sector_perf.get('up_count', 0)}
- 下跌股票数：{sector_perf.get('down_count', 0)}
- 总股票数：{sector_perf.get('total_count', 0)}

选中股票表现：
- 平均涨跌幅：{stock_perf.get('avg_change', 0):.2f}%
- 平均换手率：{stock_perf.get('avg_turnover', 0):.2f}%
- 上涨股票比例：{stock_perf.get('up_count', 0)}/{stock_perf.get('stock_count', 0)}

相关新闻：
{chr(10).join([f"- {news_item['title']}" for news_item in news[:3]])}

请从以下角度分析：
1. 板块当前所处的市场周期阶段
2. 主要驱动因素和催化剂
3. 短期（1-2周）和中期（1-2月）趋势判断
4. 关键关注点和风险提示

要求：分析简洁专业，控制在200字以内。
"""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            logger.warning(f"AI板块趋势分析失败: {str(e)}")
            return f"板块趋势分析：{sector_name}板块当前表现{'积极' if sector_perf.get('change_pct', 0) > 0 else '疲弱'}，需要关注后续资金流向和政策变化。"

    def _generate_sector_report(self, sector_analysis: Dict, sector_distribution: Dict) -> str:
        """生成板块分析报告"""
        try:
            report_lines = ["# 板块分析报告", ""]

            # 板块分布概况
            report_lines.append("## 板块分布概况")
            for sector, stocks in list(sector_distribution.items())[:5]:
                report_lines.append(f"- **{sector}**: {len(stocks)}只股票")
            report_lines.append("")

            # 重点板块分析
            if sector_analysis:
                report_lines.append("## 重点板块分析")
                for sector, analysis in sector_analysis.items():
                    report_lines.append(f"### {sector}")
                    report_lines.append(f"**评分**: {analysis['sector_score']:.1f}/100")
                    report_lines.append(f"**龙头股票**: {', '.join(analysis['leading_stocks'])}")
                    report_lines.append(f"**趋势分析**: {analysis['sector_trend']}")

                    if analysis['risk_factors']:
                        report_lines.append(f"**风险提示**: {'; '.join(analysis['risk_factors'])}")
                    report_lines.append("")

            # 总结建议
            report_lines.append("## 板块投资建议")
            if sector_analysis:
                # 找出评分最高的板块
                best_sector = max(sector_analysis.items(), key=lambda x: x[1]['sector_score'])
                report_lines.append(f"- **推荐关注**: {best_sector[0]}板块，评分{best_sector[1]['sector_score']:.1f}")

                # 风险提示
                all_risks = []
                for analysis in sector_analysis.values():
                    all_risks.extend(analysis['risk_factors'])

                common_risks = [risk for risk, count in Counter(all_risks).items() if count > 1]
                if common_risks:
                    report_lines.append(f"- **共同风险**: {'; '.join(common_risks[:3])}")

            return "\n".join(report_lines)

        except Exception as e:
            logger.error(f"生成板块分析报告失败: {str(e)}")
            return "板块分析报告生成失败"

def sector_analyst_node(state: StockAnalysisState) -> StockAnalysisState:
    """板块分析师节点入口函数"""
    analyst = SectorAnalyst()
    return analyst.analyze_sectors(state)