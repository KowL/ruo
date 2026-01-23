"""
技术分析师节点 - 深度技术分析（K线、指标、形态）
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import sys
import os

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.data_converter import safe_convert_to_python_types, safe_float, safe_int, safe_str

from llm_factory import LLMFactory
from app.llm_agent.state.stock_analysis_state import StockAnalysisState, TechnicalAnalysisResult

logger = logging.getLogger(__name__)

class TechnicalAnalyst:
    """技术分析师"""

    def __init__(self):
        self.llm = LLMFactory.get_instance()

    def analyze_technical(self, state: StockAnalysisState) -> StockAnalysisState:
        """技术分析主函数"""
        try:
            logger.info("开始技术分析...")

            selected_stocks = state.get("selected_stocks", [])
            if not selected_stocks:
                state["error"] = "没有选中的股票进行技术分析"
                return state

            # 分析每只股票的技术情况
            technical_results = {}
            for stock in selected_stocks:
                try:
                    analysis = self._analyze_single_stock_technical(stock)
                    technical_results[stock["code"]] = analysis
                except Exception as e:
                    logger.warning(f"分析股票 {stock['code']} 技术情况失败: {str(e)}")
                    technical_results[stock["code"]] = self._get_default_technical_analysis(stock)

            # 生成技术分析报告
            technical_report = self._generate_technical_report(technical_results, selected_stocks)

            # 更新状态
            state["technical_analysis"] = {
                "individual_analysis": technical_results,
                "technical_report": technical_report,
                "analysis_time": datetime.now().isoformat()
            }
            state["next_action"] = "sentiment_analysis"

            logger.info("技术分析完成")
            return state

        except Exception as e:
            logger.error(f"技术分析失败: {str(e)}")
            state["error"] = f"技术分析失败: {str(e)}"
            return state

    def _analyze_single_stock_technical(self, stock: Dict) -> TechnicalAnalysisResult:
        """分析单只股票的技术情况"""
        code = stock["code"]

        # 获取更长期的历史数据用于技术分析
        hist_data = self._get_stock_history_data(code, days=120)

        # 均线分析
        ma_analysis = self._analyze_moving_averages(hist_data, stock)

        # MACD分析
        macd_signal = self._analyze_macd(hist_data)

        # RSI分析
        rsi_level = self._calculate_rsi(hist_data)

        # 布林带分析
        bollinger_position = self._analyze_bollinger_bands(hist_data, stock)

        # 形态识别
        pattern_recognition = self._recognize_patterns(hist_data, stock)

        # 计算技术评分
        technical_score = self._calculate_technical_score(
            ma_analysis, macd_signal, rsi_level, bollinger_position, pattern_recognition
        )

        # 关键价位
        key_levels = self._calculate_key_levels(hist_data, ma_analysis)

        result: TechnicalAnalysisResult = {
            "ma_analysis": ma_analysis,
            "macd_signal": macd_signal,
            "rsi_level": rsi_level,
            "bollinger_position": bollinger_position,
            "pattern_recognition": pattern_recognition,
            "technical_score": technical_score,
            "key_levels": key_levels
        }

        # 确保所有数据都是Python原生类型
        result = safe_convert_to_python_types(result)
        return result

    def _get_stock_history_data(self, code: str, days: int = 120) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

            # 获取日K线数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date)

            if df.empty:
                return pd.DataFrame()

            # 数据清洗
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount"
            })

            # 确保数据类型正确
            numeric_columns = ["open", "close", "high", "low", "volume", "amount"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            logger.warning(f"获取股票 {code} 历史数据失败: {str(e)}")
            return pd.DataFrame()

    def _analyze_moving_averages(self, hist_data: pd.DataFrame, stock: Dict) -> Dict[str, Any]:
        """均线分析"""
        try:
            if hist_data.empty or len(hist_data) < 60:
                return {"status": "数据不足", "signals": []}

            closes = hist_data["close"].values
            current_price = stock["price"]

            # 计算各周期均线
            ma5 = np.mean(closes[-5:]) if len(closes) >= 5 else current_price
            ma10 = np.mean(closes[-10:]) if len(closes) >= 10 else current_price
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else current_price
            ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else current_price

            # 均线排列
            ma_arrangement = self._get_ma_arrangement(current_price, ma5, ma10, ma20, ma60)

            # 均线趋势
            ma_trends = {}
            for period, ma_value in [("MA5", ma5), ("MA10", ma10), ("MA20", ma20), ("MA60", ma60)]:
                period_num = int(period.replace("MA", ""))
                if len(closes) >= period_num:
                    if len(closes) >= period_num + 5:
                        prev_ma = np.mean(closes[-(period_num+5):-5])
                        trend = "上升" if ma_value > prev_ma else "下降" if ma_value < prev_ma else "平稳"
                    else:
                        trend = "平稳"
                    ma_trends[period] = trend

            # 均线支撑阻力
            support_levels = [ma for ma in [ma5, ma10, ma20, ma60] if ma < current_price]
            resistance_levels = [ma for ma in [ma5, ma10, ma20, ma60] if ma > current_price]

            # 生成均线信号
            signals = []
            if current_price > ma5 > ma10 > ma20 > ma60:
                signals.append("多头排列")
            elif current_price < ma5 < ma10 < ma20 < ma60:
                signals.append("空头排列")

            if abs(current_price - ma5) / current_price < 0.02:
                signals.append("接近5日均线")
            if abs(current_price - ma20) / current_price < 0.03:
                signals.append("接近20日均线")

            return {
                "ma5": round(ma5, 2),
                "ma10": round(ma10, 2),
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "arrangement": ma_arrangement,
                "trends": ma_trends,
                "support_levels": [round(s, 2) for s in support_levels],
                "resistance_levels": [round(r, 2) for r in resistance_levels],
                "signals": signals
            }

        except Exception as e:
            logger.warning(f"均线分析失败: {str(e)}")
            return {"status": "分析失败", "signals": []}

    def _get_ma_arrangement(self, price: float, ma5: float, ma10: float, ma20: float, ma60: float) -> str:
        """判断均线排列"""
        if price > ma5 > ma10 > ma20 > ma60:
            return "完美多头排列"
        elif price > ma5 > ma10 > ma20:
            return "短期多头排列"
        elif price < ma5 < ma10 < ma20 < ma60:
            return "完美空头排列"
        elif price < ma5 < ma10 < ma20:
            return "短期空头排列"
        else:
            return "均线纠缠"

    def _analyze_macd(self, hist_data: pd.DataFrame) -> Dict[str, Any]:
        """MACD分析"""
        try:
            if hist_data.empty or len(hist_data) < 26:
                return {"status": "数据不足", "signal": "无信号"}

            closes = hist_data["close"].values

            # 计算MACD
            exp1 = pd.Series(closes).ewm(span=12).mean()
            exp2 = pd.Series(closes).ewm(span=26).mean()
            dif = exp1 - exp2
            dea = dif.ewm(span=9).mean()
            macd = (dif - dea) * 2

            # 当前值
            current_dif = dif.iloc[-1]
            current_dea = dea.iloc[-1]
            current_macd = macd.iloc[-1]

            # 前一日值
            prev_dif = dif.iloc[-2] if len(dif) > 1 else current_dif
            prev_dea = dea.iloc[-2] if len(dea) > 1 else current_dea
            prev_macd = macd.iloc[-2] if len(macd) > 1 else current_macd

            # 信号判断
            signals = []

            # 金叉死叉
            if current_dif > current_dea and prev_dif <= prev_dea:
                signals.append("DIF上穿DEA金叉")
            elif current_dif < current_dea and prev_dif >= prev_dea:
                signals.append("DIF下穿DEA死叉")

            # 零轴穿越
            if current_dif > 0 and prev_dif <= 0:
                signals.append("DIF上穿零轴")
            elif current_dif < 0 and prev_dif >= 0:
                signals.append("DIF下穿零轴")

            # MACD柱状图
            if current_macd > 0 and prev_macd <= 0:
                signals.append("MACD柱转正")
            elif current_macd < 0 and prev_macd >= 0:
                signals.append("MACD柱转负")

            # 背离检测（简化版）
            if len(closes) >= 10:
                recent_price_high = np.max(closes[-10:])
                recent_dif_high = np.max(dif.iloc[-10:])
                if closes[-1] >= recent_price_high * 0.98 and current_dif < recent_dif_high * 0.9:
                    signals.append("可能存在顶背离")

            return {
                "dif": round(current_dif, 4),
                "dea": round(current_dea, 4),
                "macd": round(current_macd, 4),
                "signal": "买入信号" if current_dif > current_dea and current_dif > 0 else
                         "卖出信号" if current_dif < current_dea and current_dif < 0 else "观望",
                "signals": signals if signals else ["无明显信号"]
            }

        except Exception as e:
            logger.warning(f"MACD分析失败: {str(e)}")
            return {"status": "分析失败", "signal": "无信号"}

    def _calculate_rsi(self, hist_data: pd.DataFrame, period: int = 14) -> float:
        """计算RSI指标"""
        try:
            if hist_data.empty or len(hist_data) < period + 1:
                return 50.0

            closes = hist_data["close"].values
            deltas = np.diff(closes)

            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return round(rsi, 2)

        except Exception as e:
            logger.warning(f"RSI计算失败: {str(e)}")
            return 50.0

    def _analyze_bollinger_bands(self, hist_data: pd.DataFrame, stock: Dict, period: int = 20) -> str:
        """布林带分析"""
        try:
            if hist_data.empty or len(hist_data) < period:
                return "数据不足"

            closes = hist_data["close"].values
            current_price = stock["price"]

            # 计算布林带
            ma = np.mean(closes[-period:])
            std = np.std(closes[-period:])

            upper_band = ma + 2 * std
            lower_band = ma - 2 * std

            # 判断位置
            if current_price > upper_band:
                return "突破上轨"
            elif current_price < lower_band:
                return "跌破下轨"
            elif current_price > ma + std:
                return "上轨附近"
            elif current_price < ma - std:
                return "下轨附近"
            elif current_price > ma:
                return "中轨上方"
            else:
                return "中轨下方"

        except Exception as e:
            logger.warning(f"布林带分析失败: {str(e)}")
            return "分析失败"

    def _recognize_patterns(self, hist_data: pd.DataFrame, stock: Dict) -> List[str]:
        """形态识别"""
        patterns = []

        try:
            if hist_data.empty or len(hist_data) < 20:
                return ["数据不足"]

            closes = hist_data["close"].values
            highs = hist_data["high"].values
            lows = hist_data["low"].values
            current_price = stock["price"]

            # 突破形态
            recent_high = np.max(highs[-20:])
            recent_low = np.min(lows[-20:])

            if current_price >= recent_high * 0.99:
                patterns.append("突破前期高点")
            elif current_price <= recent_low * 1.01:
                patterns.append("跌破前期低点")

            # 整理形态
            if len(closes) >= 10:
                recent_range = np.max(closes[-10:]) - np.min(closes[-10:])
                avg_price = np.mean(closes[-10:])
                if recent_range / avg_price < 0.05:
                    patterns.append("窄幅整理")

            # 趋势形态
            if len(closes) >= 5:
                # 连续上涨
                if all(closes[i] > closes[i-1] for i in range(-4, 0)):
                    patterns.append("连续上涨")
                # 连续下跌
                elif all(closes[i] < closes[i-1] for i in range(-4, 0)):
                    patterns.append("连续下跌")

            # V型反转
            if len(closes) >= 10:
                mid_point = len(closes) // 2
                left_min = np.min(closes[:mid_point])
                right_min = np.min(closes[mid_point:])
                if current_price > left_min * 1.1 and current_price > right_min * 1.1:
                    patterns.append("V型反转形态")

            # 双底/双顶（简化版）
            if len(lows) >= 20:
                low_indices = []
                for i in range(1, len(lows)-1):
                    if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                        low_indices.append(i)

                if len(low_indices) >= 2:
                    last_two_lows = [lows[i] for i in low_indices[-2:]]
                    if abs(last_two_lows[0] - last_two_lows[1]) / last_two_lows[0] < 0.03:
                        patterns.append("疑似双底形态")

            return patterns if patterns else ["无明显形态"]

        except Exception as e:
            logger.warning(f"形态识别失败: {str(e)}")
            return ["识别失败"]

    def _calculate_technical_score(self, ma_analysis: Dict, macd_signal: Dict,
                                 rsi_level: float, bollinger_position: str,
                                 patterns: List[str]) -> float:
        """计算技术评分"""
        try:
            score = 50.0  # 基础分

            # 均线贡献 (30%)
            if ma_analysis.get("arrangement") == "完美多头排列":
                score += 15
            elif ma_analysis.get("arrangement") == "短期多头排列":
                score += 10
            elif ma_analysis.get("arrangement") == "完美空头排列":
                score -= 15
            elif ma_analysis.get("arrangement") == "短期空头排列":
                score -= 10

            ma_signals = ma_analysis.get("signals", [])
            if "多头排列" in ma_signals:
                score += 5

            # MACD贡献 (25%)
            macd_sig = macd_signal.get("signal", "观望")
            if macd_sig == "买入信号":
                score += 12
            elif macd_sig == "卖出信号":
                score -= 12

            macd_signals = macd_signal.get("signals", [])
            if "DIF上穿DEA金叉" in macd_signals:
                score += 8
            elif "DIF下穿DEA死叉" in macd_signals:
                score -= 8

            # RSI贡献 (20%)
            if 30 <= rsi_level <= 70:
                score += 10  # 正常区间
            elif rsi_level < 30:
                score += 5   # 超卖，可能反弹
            elif rsi_level > 70:
                score -= 5   # 超买，可能回调

            # 布林带贡献 (15%)
            if bollinger_position == "突破上轨":
                score += 7
            elif bollinger_position == "跌破下轨":
                score -= 7
            elif bollinger_position == "中轨上方":
                score += 3

            # 形态贡献 (10%)
            positive_patterns = ["突破前期高点", "V型反转形态", "疑似双底形态", "连续上涨"]
            negative_patterns = ["跌破前期低点", "连续下跌"]

            for pattern in patterns:
                if any(p in pattern for p in positive_patterns):
                    score += 3
                elif any(p in pattern for p in negative_patterns):
                    score -= 3

            return max(0, min(score, 100))

        except Exception as e:
            logger.warning(f"计算技术评分失败: {str(e)}")
            return 50.0

    def _calculate_key_levels(self, hist_data: pd.DataFrame, ma_analysis: Dict) -> Dict[str, float]:
        """计算关键价位"""
        try:
            if hist_data.empty:
                return {}

            key_levels = {}

            # 均线价位
            if "ma5" in ma_analysis:
                key_levels["MA5"] = ma_analysis["ma5"]
            if "ma10" in ma_analysis:
                key_levels["MA10"] = ma_analysis["ma10"]
            if "ma20" in ma_analysis:
                key_levels["MA20"] = ma_analysis["ma20"]
            if "ma60" in ma_analysis:
                key_levels["MA60"] = ma_analysis["ma60"]

            # 历史高低点
            if len(hist_data) >= 60:
                key_levels["60日高点"] = hist_data["high"].tail(60).max()
                key_levels["60日低点"] = hist_data["low"].tail(60).min()

            if len(hist_data) >= 20:
                key_levels["20日高点"] = hist_data["high"].tail(20).max()
                key_levels["20日低点"] = hist_data["low"].tail(20).min()

            return key_levels

        except Exception as e:
            logger.warning(f"计算关键价位失败: {str(e)}")
            return {}

    def _get_default_technical_analysis(self, stock: Dict) -> TechnicalAnalysisResult:
        """获取默认技术分析结果"""
        return {
            "ma_analysis": {"status": "数据不足", "signals": []},
            "macd_signal": {"status": "数据不足", "signal": "无信号"},
            "rsi_level": 50.0,
            "bollinger_position": "数据不足",
            "pattern_recognition": ["数据不足"],
            "technical_score": 50.0,
            "key_levels": {}
        }

    def _generate_technical_report(self, results: Dict, stocks: List[Dict]) -> str:
        """生成技术分析报告"""
        try:
            report_lines = ["# 技术分析报告", ""]

            # 整体技术面概况
            total_stocks = len(stocks)
            high_score_count = sum(1 for r in results.values() if r["technical_score"] > 70)
            low_score_count = sum(1 for r in results.values() if r["technical_score"] < 40)

            report_lines.append("## 技术面整体概况")
            report_lines.append(f"- 分析股票总数：{total_stocks}只")
            report_lines.append(f"- 技术面强势股票：{high_score_count}只")
            report_lines.append(f"- 技术面弱势股票：{low_score_count}只")
            report_lines.append("")

            # 重点股票技术分析
            report_lines.append("## 重点股票技术分析")

            # 按技术评分排序
            sorted_stocks = sorted(
                [(stock, results[stock["code"]]) for stock in stocks],
                key=lambda x: x[1]["technical_score"],
                reverse=True
            )

            for stock, analysis in sorted_stocks[:5]:  # 显示前5只
                report_lines.append(f"### {stock['name']}({stock['code']})")
                report_lines.append(f"**技术评分**: {analysis['technical_score']:.1f}/100")

                # 均线分析
                ma_analysis = analysis["ma_analysis"]
                if "arrangement" in ma_analysis:
                    report_lines.append(f"**均线排列**: {ma_analysis['arrangement']}")

                # MACD信号
                macd_signal = analysis["macd_signal"]
                if "signal" in macd_signal:
                    report_lines.append(f"**MACD信号**: {macd_signal['signal']}")

                # RSI水平
                rsi = analysis["rsi_level"]
                rsi_desc = "超买" if rsi > 70 else "超卖" if rsi < 30 else "正常"
                report_lines.append(f"**RSI**: {rsi:.1f} ({rsi_desc})")

                # 布林带位置
                report_lines.append(f"**布林带位置**: {analysis['bollinger_position']}")

                # 形态识别
                patterns = analysis["pattern_recognition"]
                if patterns and patterns != ["数据不足"]:
                    report_lines.append(f"**技术形态**: {'; '.join(patterns[:3])}")

                report_lines.append("")

            # 技术指标统计
            report_lines.append("## 技术指标统计")

            # RSI分布
            rsi_values = [r["rsi_level"] for r in results.values()]
            oversold_count = sum(1 for rsi in rsi_values if rsi < 30)
            overbought_count = sum(1 for rsi in rsi_values if rsi > 70)

            report_lines.append(f"- **RSI超卖股票**: {oversold_count}只 (RSI < 30)")
            report_lines.append(f"- **RSI超买股票**: {overbought_count}只 (RSI > 70)")

            # 均线排列统计
            arrangements = [r["ma_analysis"].get("arrangement", "未知") for r in results.values()]
            arrangement_counts = {}
            for arr in arrangements:
                arrangement_counts[arr] = arrangement_counts.get(arr, 0) + 1

            if arrangement_counts:
                report_lines.append("- **均线排列分布**:")
                for arr, count in sorted(arrangement_counts.items(), key=lambda x: x[1], reverse=True):
                    if arr != "未知":
                        report_lines.append(f"  - {arr}: {count}只")

            # MACD信号统计
            macd_signals = [r["macd_signal"].get("signal", "观望") for r in results.values()]
            buy_signals = sum(1 for sig in macd_signals if sig == "买入信号")
            sell_signals = sum(1 for sig in macd_signals if sig == "卖出信号")

            report_lines.append(f"- **MACD买入信号**: {buy_signals}只")
            report_lines.append(f"- **MACD卖出信号**: {sell_signals}只")

            return "\n".join(report_lines)

        except Exception as e:
            logger.error(f"生成技术分析报告失败: {str(e)}")
            return "技术分析报告生成失败"

def technical_analyst_node(state: StockAnalysisState) -> StockAnalysisState:
    """技术分析师节点入口函数"""
    analyst = TechnicalAnalyst()
    return analyst.analyze_technical(state)