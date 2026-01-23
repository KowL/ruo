"""
投资决策者节点 - 综合所有分析给出最终投资建议
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from llm_factory import LLMFactory
from app.llm_agent.state.stock_analysis_state import StockAnalysisState, InvestmentDecision

logger = logging.getLogger(__name__)

class InvestmentDecisionMaker:
    """投资决策者"""

    def __init__(self):
        self.llm = LLMFactory.get_instance()

    def make_investment_decisions(self, state: StockAnalysisState) -> StockAnalysisState:
        """投资决策主函数"""
        try:
            logger.info("开始投资决策...")

            selected_stocks = state.get("selected_stocks", [])
            if not selected_stocks:
                state["error"] = "没有选中的股票进行投资决策"
                return state

            # 获取各项分析结果
            sector_analysis = state.get("sector_analysis", {})
            short_term_analysis = state.get("short_term_analysis", {})
            technical_analysis = state.get("technical_analysis", {})
            sentiment_analysis = state.get("sentiment_analysis", {})

            # 为每只股票做投资决策
            investment_decisions = []
            for stock in selected_stocks:
                try:
                    decision = self._make_single_stock_decision(
                        stock, sector_analysis, short_term_analysis,
                        technical_analysis, sentiment_analysis
                    )
                    investment_decisions.append(decision)
                except Exception as e:
                    logger.warning(f"为股票 {stock['code']} 做投资决策失败: {str(e)}")
                    # 添加默认决策
                    default_decision = self._get_default_decision(stock)
                    investment_decisions.append(default_decision)

            # 按推荐程度排序
            investment_decisions.sort(key=lambda x: self._get_recommendation_score(x["recommendation"]), reverse=True)

            # 生成最终报告
            final_report = self._generate_final_report(investment_decisions, state)

            # 更新状态
            state["investment_decisions"] = investment_decisions
            state["final_report"] = final_report
            state["next_action"] = "END"

            logger.info("投资决策完成")
            return state

        except Exception as e:
            logger.error(f"投资决策失败: {str(e)}")
            state["error"] = f"投资决策失败: {str(e)}"
            return state

    def _make_single_stock_decision(self, stock: Dict, sector_analysis: Dict,
                                  short_term_analysis: Dict, technical_analysis: Dict,
                                  sentiment_analysis: Dict) -> InvestmentDecision:
        """为单只股票做投资决策"""
        code = stock["code"]
        name = stock["name"]
        current_price = stock["price"]

        # 获取各项分析结果
        sector_result = self._get_sector_analysis_for_stock(stock, sector_analysis)
        short_term_result = short_term_analysis.get("individual_analysis", {}).get(code, {})
        technical_result = technical_analysis.get("individual_analysis", {}).get(code, {})
        sentiment_result = sentiment_analysis.get("individual_analysis", {}).get(code, {})

        # 计算综合评分
        comprehensive_score = self._calculate_comprehensive_score(
            stock, sector_result, short_term_result, technical_result, sentiment_result
        )

        # 确定推荐等级
        recommendation = self._determine_recommendation(comprehensive_score, stock)

        # 计算目标价和止损价
        target_price, stop_loss = self._calculate_price_targets(
            current_price, technical_result, short_term_result, comprehensive_score
        )

        # 确定持有期和仓位
        holding_period = self._determine_holding_period(recommendation, technical_result)
        position_size = self._determine_position_size(recommendation, comprehensive_score)

        # 评估风险等级
        risk_level = self._assess_risk_level(stock, sector_result, technical_result, sentiment_result)

        # 生成投资理由和风险提示
        key_reasons = self._generate_key_reasons(
            stock, sector_result, short_term_result, technical_result, sentiment_result
        )
        risk_warnings = self._generate_risk_warnings(
            stock, sector_result, technical_result, sentiment_result
        )

        # 制定操作计划
        operation_plan = self._create_operation_plan(
            recommendation, target_price, stop_loss, holding_period, position_size
        )

        # 计算信心水平
        confidence_level = self._calculate_confidence_level(comprehensive_score, risk_level)

        decision: InvestmentDecision = {
            "stock_code": code,
            "stock_name": name,
            "recommendation": recommendation,
            "confidence_level": confidence_level,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "holding_period": holding_period,
            "position_size": position_size,
            "risk_level": risk_level,
            "key_reasons": key_reasons,
            "risk_warnings": risk_warnings,
            "operation_plan": operation_plan
        }

        return decision

    def _get_sector_analysis_for_stock(self, stock: Dict, sector_analysis: Dict) -> Dict:
        """获取股票对应的板块分析结果"""
        stock_sector = stock.get("sector", "")
        detailed_analysis = sector_analysis.get("detailed_analysis", {})

        # 查找匹配的板块分析
        for sector_name, analysis in detailed_analysis.items():
            if sector_name in stock_sector or stock_sector in sector_name:
                return analysis

        return {}

    def _calculate_comprehensive_score(self, stock: Dict, sector_result: Dict,
                                     short_term_result: Dict, technical_result: Dict,
                                     sentiment_result: Dict) -> float:
        """计算综合评分"""
        try:
            # 基础分数
            base_score = 50.0

            # 板块分析贡献 (25%)
            sector_score = sector_result.get("sector_score", 50.0)
            sector_contribution = (sector_score - 50) * 0.25

            # 短线分析贡献 (25%)
            momentum_score = short_term_result.get("momentum_score", 50.0)
            short_term_contribution = (momentum_score - 50) * 0.25

            # 技术分析贡献 (30%)
            technical_score = technical_result.get("technical_score", 50.0)
            technical_contribution = (technical_score - 50) * 0.30

            # 舆论分析贡献 (20%)
            news_sentiment = sentiment_result.get("news_sentiment", 50.0)
            social_sentiment = sentiment_result.get("social_sentiment", 50.0)
            sentiment_avg = (news_sentiment + social_sentiment) / 2
            sentiment_contribution = (sentiment_avg - 50) * 0.20

            # 计算综合评分
            comprehensive_score = (base_score + sector_contribution + short_term_contribution +
                                 technical_contribution + sentiment_contribution)

            # 额外调整因子
            # 涨跌幅调整
            change_pct = stock.get("change_pct", 0)
            if change_pct > 9:  # 涨停或接近涨停
                comprehensive_score += 5
            elif change_pct > 5:
                comprehensive_score += 3
            elif change_pct < -9:  # 跌停或接近跌停
                comprehensive_score -= 5
            elif change_pct < -5:
                comprehensive_score -= 3

            # 换手率调整
            turnover_rate = stock.get("turnover_rate", 0)
            if turnover_rate > 15:  # 高换手率
                comprehensive_score += 2
            elif turnover_rate < 1:  # 低换手率
                comprehensive_score -= 2

            # 市值调整
            market_cap = stock.get("market_cap", 0)
            if market_cap > 1000e8:  # 大盘股
                comprehensive_score += 1
            elif market_cap < 50e8:  # 小盘股，风险较高
                comprehensive_score -= 1

            return max(0, min(comprehensive_score, 100))

        except Exception as e:
            logger.warning(f"计算综合评分失败: {str(e)}")
            return 50.0

    def _determine_recommendation(self, comprehensive_score: float, stock: Dict) -> str:
        """确定推荐等级"""
        # 基于综合评分确定推荐等级
        if comprehensive_score >= 80:
            return "强烈买入"
        elif comprehensive_score >= 65:
            return "买入"
        elif comprehensive_score >= 45:
            return "持有"
        elif comprehensive_score >= 30:
            return "卖出"
        else:
            return "强烈卖出"

    def _calculate_price_targets(self, current_price: float, technical_result: Dict,
                               short_term_result: Dict, comprehensive_score: float) -> tuple:
        """计算目标价和止损价"""
        try:
            # 获取技术分析中的关键价位
            key_levels = technical_result.get("key_levels", {})
            support_resistance = short_term_result.get("support_resistance", {})

            # 计算目标价
            if comprehensive_score >= 70:
                # 强势股，目标价设置较高
                target_multiplier = 1.15 + (comprehensive_score - 70) * 0.005
            elif comprehensive_score >= 50:
                # 中性股，目标价适中
                target_multiplier = 1.05 + (comprehensive_score - 50) * 0.005
            else:
                # 弱势股，目标价保守
                target_multiplier = 1.02

            target_price = current_price * target_multiplier

            # 考虑技术阻力位
            resistance = support_resistance.get("resistance", 0)
            if resistance > current_price:
                # 确保目标价不会低于当前价格
                adjusted_resistance_target = resistance * 0.95
                if adjusted_resistance_target > current_price:
                    target_price = min(target_price, adjusted_resistance_target)
                # 如果阻力位调整后仍低于当前价，则不调整目标价

            # 计算止损价
            if comprehensive_score >= 70:
                # 强势股，止损设置较松
                stop_loss_multiplier = 0.92
            elif comprehensive_score >= 50:
                # 中性股，止损适中
                stop_loss_multiplier = 0.90
            else:
                # 弱势股，止损较紧
                stop_loss_multiplier = 0.85

            stop_loss = current_price * stop_loss_multiplier

            # 考虑技术支撑位
            support = support_resistance.get("support", 0)
            if support > 0 and support < current_price:
                stop_loss = max(stop_loss, support * 0.98)

            # 最终安全检查：确保目标价高于当前价，止损价低于当前价
            if target_price <= current_price:
                target_price = current_price * 1.05  # 至少5%的上涨空间
            if stop_loss >= current_price:
                stop_loss = current_price * 0.95   # 至少5%的止损空间

            return round(target_price, 2), round(stop_loss, 2)

        except Exception as e:
            logger.warning(f"计算价格目标失败: {str(e)}")
            return round(current_price * 1.1, 2), round(current_price * 0.9, 2)

    def _determine_holding_period(self, recommendation: str, technical_result: Dict) -> str:
        """确定建议持有期"""
        if recommendation in ["强烈买入", "买入"]:
            # 检查技术形态
            patterns = technical_result.get("pattern_recognition", [])
            if any("突破" in pattern for pattern in patterns):
                return "1-2周"
            else:
                return "2-4周"
        elif recommendation == "持有":
            return "观察1-2周后决定"
        else:
            return "尽快减仓"

    def _determine_position_size(self, recommendation: str, comprehensive_score: float) -> str:
        """确定建议仓位"""
        if recommendation == "强烈买入":
            if comprehensive_score >= 85:
                return "重仓 (20-30%)"
            else:
                return "中等仓位 (10-20%)"
        elif recommendation == "买入":
            return "轻仓 (5-10%)"
        elif recommendation == "持有":
            return "维持现有仓位"
        else:
            return "减仓或清仓"

    def _assess_risk_level(self, stock: Dict, sector_result: Dict,
                          technical_result: Dict, sentiment_result: Dict) -> str:
        """评估风险等级"""
        risk_factors = 0

        # 估值风险
        pe_ratio = stock.get("pe_ratio")
        if pe_ratio and pe_ratio > 100:
            risk_factors += 1

        # 涨幅风险
        change_pct = stock.get("change_pct", 0)
        if change_pct > 15:
            risk_factors += 1

        # 换手率风险
        turnover_rate = stock.get("turnover_rate", 0)
        if turnover_rate > 20:
            risk_factors += 1

        # 技术风险
        rsi_level = technical_result.get("rsi_level", 50)
        if rsi_level > 80:
            risk_factors += 1

        # 板块风险
        sector_risks = sector_result.get("risk_factors", [])
        if len(sector_risks) > 2:
            risk_factors += 1

        # 市值风险
        market_cap = stock.get("market_cap", 0)
        if market_cap < 30e8:  # 小市值风险
            risk_factors += 1

        # 确定风险等级
        if risk_factors >= 4:
            return "高"
        elif risk_factors >= 2:
            return "中"
        else:
            return "低"

    def _generate_key_reasons(self, stock: Dict, sector_result: Dict,
                            short_term_result: Dict, technical_result: Dict,
                            sentiment_result: Dict) -> List[str]:
        """生成主要投资理由"""
        reasons = []

        try:
            # 板块优势
            sector_score = sector_result.get("sector_score", 0)
            if sector_score > 70:
                reasons.append(f"所属板块表现强势，评分{sector_score:.1f}")

            # 技术优势
            technical_score = technical_result.get("technical_score", 0)
            if technical_score > 70:
                ma_analysis = technical_result.get("ma_analysis", {})
                if ma_analysis.get("arrangement") == "完美多头排列":
                    reasons.append("技术面呈完美多头排列")
                else:
                    reasons.append(f"技术面强势，评分{technical_score:.1f}")

            # 动量优势
            momentum_score = short_term_result.get("momentum_score", 0)
            if momentum_score > 70:
                reasons.append(f"短线动量强劲，评分{momentum_score:.1f}")

            # 资金流入
            fund_flow = short_term_result.get("fund_flow", {})
            main_inflow = fund_flow.get("main_net_inflow", 0)
            if main_inflow > 0:
                reasons.append(f"主力资金净流入{abs(main_inflow/10000):.1f}万元")

            # 舆论支持
            news_sentiment = sentiment_result.get("news_sentiment", 50)
            if news_sentiment > 65:
                reasons.append("新闻舆论偏正面")

            # 成交量配合
            volume_analysis = short_term_result.get("volume_analysis", {})
            if volume_analysis.get("pattern") == "放量突破":
                reasons.append("放量突破，成交量配合良好")

            # 形态突破
            patterns = technical_result.get("pattern_recognition", [])
            breakthrough_patterns = [p for p in patterns if "突破" in p]
            if breakthrough_patterns:
                reasons.append(f"技术形态：{breakthrough_patterns[0]}")

            # 如果没有明显优势，添加基本理由
            if not reasons:
                if stock.get("change_pct", 0) > 0:
                    reasons.append("股价表现相对稳定")
                else:
                    reasons.append("当前价位具有一定投资价值")

            return reasons[:5]  # 最多返回5个理由

        except Exception as e:
            logger.warning(f"生成投资理由失败: {str(e)}")
            return ["综合分析后认为具有投资价值"]

    def _generate_risk_warnings(self, stock: Dict, sector_result: Dict,
                              technical_result: Dict, sentiment_result: Dict) -> List[str]:
        """生成风险提示"""
        warnings = []

        try:
            # 估值风险
            pe_ratio = stock.get("pe_ratio")
            if pe_ratio and pe_ratio > 100:
                warnings.append(f"市盈率过高({pe_ratio:.1f}倍)，估值风险较大")

            # 涨幅风险
            change_pct = stock.get("change_pct", 0)
            if change_pct > 15:
                warnings.append("短期涨幅过大，存在回调风险")

            # 技术风险
            rsi_level = technical_result.get("rsi_level", 50)
            if rsi_level > 80:
                warnings.append(f"RSI指标超买({rsi_level:.1f})，技术面存在调整压力")

            # 换手率风险
            turnover_rate = stock.get("turnover_rate", 0)
            if turnover_rate > 20:
                warnings.append("换手率过高，资金博弈激烈")

            # 板块风险
            sector_risks = sector_result.get("risk_factors", [])
            for risk in sector_risks[:2]:  # 最多显示2个板块风险
                if "风险" in risk:
                    warnings.append(f"板块风险：{risk}")

            # 市值风险
            market_cap = stock.get("market_cap", 0)
            if market_cap < 30e8:
                warnings.append("小市值股票，流动性风险较高")

            # 舆论风险
            news_sentiment = sentiment_result.get("news_sentiment", 50)
            if news_sentiment < 35:
                warnings.append("新闻舆论偏负面，市场情绪不佳")

            # 如果没有明显风险，添加通用风险提示
            if not warnings:
                warnings.append("股市有风险，投资需谨慎")

            return warnings[:5]  # 最多返回5个风险提示

        except Exception as e:
            logger.warning(f"生成风险提示失败: {str(e)}")
            return ["请注意市场风险，合理控制仓位"]

    def _create_operation_plan(self, recommendation: str, target_price: float,
                             stop_loss: float, holding_period: str, position_size: str) -> str:
        """制定操作计划"""
        try:
            if recommendation in ["强烈买入", "买入"]:
                plan = f"""
**买入计划**：
1. 建议{position_size}分批买入
2. 目标价位：{target_price}元
3. 止损价位：{stop_loss}元
4. 持有期：{holding_period}
5. 操作要点：关注成交量配合，如放量上涨可适当加仓

**风控措施**：
- 严格执行止损纪律
- 如跌破止损位立即减仓
- 定期评估持仓合理性
"""
            elif recommendation == "持有":
                plan = f"""
**持有计划**：
1. 维持现有仓位不变
2. 观察期：{holding_period}
3. 上涨目标：{target_price}元
4. 止损位：{stop_loss}元
5. 操作要点：密切关注技术面和基本面变化

**调整策略**：
- 如技术面转强可考虑加仓
- 如基本面恶化应及时减仓
"""
            else:  # 卖出或强烈卖出
                plan = f"""
**减仓计划**：
1. 建议逐步减仓或清仓
2. 减仓目标：{position_size}
3. 操作要点：分批卖出，避免集中抛售
4. 时间安排：{holding_period}

**注意事项**：
- 如有反弹可适当减仓
- 避免追涨杀跌
- 保持理性投资心态
"""

            return plan.strip()

        except Exception as e:
            logger.warning(f"制定操作计划失败: {str(e)}")
            return f"建议{recommendation}，请根据个人风险承受能力调整仓位"

    def _calculate_confidence_level(self, comprehensive_score: float, risk_level: str) -> float:
        """计算信心水平"""
        try:
            # 基于综合评分的信心水平
            base_confidence = comprehensive_score

            # 风险等级调整
            if risk_level == "低":
                confidence_adjustment = 5
            elif risk_level == "中":
                confidence_adjustment = 0
            else:  # 高风险
                confidence_adjustment = -10

            confidence = base_confidence + confidence_adjustment

            return max(0, min(confidence, 100))

        except Exception as e:
            logger.warning(f"计算信心水平失败: {str(e)}")
            return 50.0

    def _get_recommendation_score(self, recommendation: str) -> int:
        """获取推荐等级对应的分数（用于排序）"""
        score_map = {
            "强烈买入": 5,
            "买入": 4,
            "持有": 3,
            "卖出": 2,
            "强烈卖出": 1
        }
        return score_map.get(recommendation, 0)

    def _get_default_decision(self, stock: Dict) -> InvestmentDecision:
        """获取默认投资决策"""
        return {
            "stock_code": stock["code"],
            "stock_name": stock["name"],
            "recommendation": "持有",
            "confidence_level": 50.0,
            "target_price": stock["price"] * 1.05,
            "stop_loss": stock["price"] * 0.95,
            "holding_period": "观察1-2周",
            "position_size": "轻仓",
            "risk_level": "中",
            "key_reasons": ["数据分析不完整，建议谨慎操作"],
            "risk_warnings": ["数据获取失败，请注意投资风险"],
            "operation_plan": "由于数据不完整，建议暂时观望，等待更多信息后再做决策"
        }

    def _generate_final_report(self, decisions: List[InvestmentDecision], state: StockAnalysisState) -> str:
        """生成最终投资报告"""
        try:
            report_lines = ["# 股票分析投资报告", ""]

            # 报告基本信息
            report_lines.append("## 报告概要")
            report_lines.append(f"- **分析日期**: {datetime.now().strftime('%Y年%m月%d日')}")
            report_lines.append(f"- **分析股票数量**: {len(decisions)}只")
            report_lines.append(f"- **分析类型**: {state.get('analysis_type', '未知')}")

            # 筛选条件
            filter_summary = state.get("filter_summary", "")
            if filter_summary:
                report_lines.append(f"- **筛选说明**: {filter_summary}")
            report_lines.append("")

            # 投资建议汇总
            recommendation_counts = {}
            for decision in decisions:
                rec = decision["recommendation"]
                recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

            report_lines.append("## 投资建议分布")
            for rec, count in sorted(recommendation_counts.items(), key=lambda x: self._get_recommendation_score(x[0]), reverse=True):
                report_lines.append(f"- **{rec}**: {count}只")
            report_lines.append("")

            # 重点推荐股票
            buy_recommendations = [d for d in decisions if d["recommendation"] in ["强烈买入", "买入"]]
            if buy_recommendations:
                report_lines.append("## 🔥 重点推荐股票")
                for i, decision in enumerate(buy_recommendations[:5], 1):
                    report_lines.append(f"### {i}. {decision['stock_name']}({decision['stock_code']})")
                    report_lines.append(f"**推荐等级**: {decision['recommendation']}")
                    report_lines.append(f"**信心水平**: {decision['confidence_level']:.1f}%")
                    report_lines.append(f"**目标价格**: {decision['target_price']}元")
                    report_lines.append(f"**止损价格**: {decision['stop_loss']}元")
                    report_lines.append(f"**风险等级**: {decision['risk_level']}")

                    # 投资理由
                    if decision['key_reasons']:
                        report_lines.append("**投资理由**:")
                        for reason in decision['key_reasons'][:3]:
                            report_lines.append(f"- {reason}")

                    # 风险提示
                    if decision['risk_warnings']:
                        report_lines.append("**风险提示**:")
                        for warning in decision['risk_warnings'][:2]:
                            report_lines.append(f"- {warning}")

                    report_lines.append("")

            # 需要关注的股票
            hold_recommendations = [d for d in decisions if d["recommendation"] == "持有"]
            if hold_recommendations:
                report_lines.append("## 📊 需要关注的股票")
                for decision in hold_recommendations[:3]:
                    report_lines.append(f"- **{decision['stock_name']}({decision['stock_code']})**: {decision['operation_plan'][:50]}...")
                report_lines.append("")

            # 风险警示股票
            sell_recommendations = [d for d in decisions if d["recommendation"] in ["卖出", "强烈卖出"]]
            if sell_recommendations:
                report_lines.append("## ⚠️ 风险警示股票")
                for decision in sell_recommendations:
                    report_lines.append(f"- **{decision['stock_name']}({decision['stock_code']})**: {decision['recommendation']}")
                    if decision['risk_warnings']:
                        report_lines.append(f"  风险: {decision['risk_warnings'][0]}")
                report_lines.append("")

            # 市场环境分析
            report_lines.append("## 📈 市场环境分析")

            # 板块分析总结
            sector_analysis = state.get("sector_analysis", {})
            if sector_analysis.get("sector_report"):
                report_lines.append("### 板块情况")
                sector_lines = sector_analysis["sector_report"].split("\n")
                # 提取关键信息
                for line in sector_lines:
                    if "推荐关注" in line or "共同风险" in line:
                        report_lines.append(f"- {line.replace('- **', '').replace('**:', ':')}")

            # 技术面总结
            technical_analysis = state.get("technical_analysis", {})
            if technical_analysis.get("technical_report"):
                report_lines.append("### 技术面情况")
                high_score_count = sum(1 for d in decisions if d["confidence_level"] > 70)
                report_lines.append(f"- 技术面强势股票: {high_score_count}只")

            report_lines.append("")

            # 投资策略建议
            report_lines.append("## 💡 投资策略建议")

            strong_buy_count = recommendation_counts.get("强烈买入", 0)
            buy_count = recommendation_counts.get("买入", 0)
            total_positive = strong_buy_count + buy_count

            if total_positive >= len(decisions) * 0.6:
                report_lines.append("- **市场环境**: 相对乐观，可适当增加仓位")
                report_lines.append("- **操作策略**: 重点关注推荐股票，分批建仓")
            elif total_positive >= len(decisions) * 0.3:
                report_lines.append("- **市场环境**: 中性偏好，保持谨慎乐观")
                report_lines.append("- **操作策略**: 精选个股，控制仓位")
            else:
                report_lines.append("- **市场环境**: 相对谨慎，以防守为主")
                report_lines.append("- **操作策略**: 降低仓位，等待更好机会")

            report_lines.append("- **风险控制**: 严格执行止损纪律，分散投资风险")
            report_lines.append("- **持仓管理**: 定期评估持仓，及时调整策略")
            report_lines.append("")

            # 免责声明
            report_lines.append("## ⚠️ 免责声明")
            report_lines.append("本报告仅供参考，不构成投资建议。投资者应根据自身情况独立决策，并承担相应风险。")
            report_lines.append("股市有风险，投资需谨慎。")

            return "\n".join(report_lines)

        except Exception as e:
            logger.error(f"生成最终报告失败: {str(e)}")
            return "最终投资报告生成失败"

def investment_decision_maker_node(state: StockAnalysisState) -> StockAnalysisState:
    """投资决策者节点入口函数"""
    decision_maker = InvestmentDecisionMaker()
    return decision_maker.make_investment_decisions(state)