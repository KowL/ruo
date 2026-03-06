"""
市场情绪指数服务
Market Sentiment Index Service

基于市场行情数据量化计算每日市场情绪指数，无新闻/LLM 依赖。

计算维度（5项加权）:
  - 涨跌比 (AD Ratio)          35%
  - 平均涨跌幅                  25%
  - 换手率热度                  20%
  - 成交额相对近5日均值          10%
  - 近3日趋势持续性             10%
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.market_price import DailyPrice
from app.models.portfolio import Portfolio


class SentimentService:
    """市场情绪指数服务（基于市场行情量化）"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    #  公开接口                                                            #
    # ------------------------------------------------------------------ #

    def get_latest_sentiment(self) -> Dict:
        """
        获取最新情绪指数
        """
        # 自动查找最近的有成交数据的日期
        symbols = self._get_tracked_symbols()
        latest_date_row = (
            self.db.query(DailyPrice.trade_date)
            .filter(DailyPrice.symbol.in_(symbols))
            .order_by(DailyPrice.trade_date.desc())
            .first()
        )
        
        target_date = latest_date_row[0] if latest_date_row else datetime.now().date()
        today_data = self._calculate_daily_sentiment(target_date)

        # 找到前一个有数据的日期计算变化
        prev_date_row = (
            self.db.query(DailyPrice.trade_date)
            .filter(
                DailyPrice.symbol.in_(symbols),
                DailyPrice.trade_date < target_date
            )
            .order_by(DailyPrice.trade_date.desc())
            .first()
        )
        
        if prev_date_row:
            yesterday_data = self._calculate_daily_sentiment(prev_date_row[0])
            change = today_data["index"] - yesterday_data["index"]
        else:
            change = 0.0

        result = dict(today_data)
        result["news_count"] = today_data.get("stock_count", 0) # 兼容接口期望
        result["change"] = round(change, 1)
        result["label"] = self._get_sentiment_label(today_data["index"])
        result["top_factors"] = self._build_top_factors(today_data)
        return result

    def get_sentiment_history(self, days: int = 7) -> List[Dict]:
        """
        获取历史情绪指数走势

        Args:
            days: 返回最近 N 天数据

        Returns:
            [
                {"date": "2026-03-04", "index": 62.3, "label": "谨慎乐观"},
                ...
            ]
        """
        results = []
        today = datetime.now().date()

        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            data = self._calculate_daily_sentiment(d)
            if data["stock_count"] > 0:
                results.append({
                    "date": d.isoformat(),
                    "index": round(data["index"], 1),
                    "label": self._get_sentiment_label(data["index"]),
                })

        return results

    def generate_daily_report(self, report_type: str = "opening") -> Dict:
        """
        生成每日简报（开盘/收盘）- 纯量化规则，无AI依赖

        Args:
            report_type: 'opening' | 'closing'
        """
        sentiment = self.get_latest_sentiment()
        history = self.get_sentiment_history(days=5)

        if report_type == "opening":
            report_content = self._generate_opening_report(sentiment, history)
        else:
            report_content = self._generate_closing_report(sentiment, history)

        return {
            "date": sentiment["date"],
            "type": report_type,
            "sentiment_index": sentiment["index"],
            "sentiment_label": sentiment["label"],
            "report": report_content,
            "key_factors": sentiment["top_factors"],
        }

    # ------------------------------------------------------------------ #
    #  核心计算                                                            #
    # ------------------------------------------------------------------ #

    def _calculate_daily_sentiment(self, target_date: date) -> Dict:
        """
        基于 DailyPrice 计算单日情绪数据
        """
        # 获取持仓股票列表（用于锁定计算范围）
        symbols = self._get_tracked_symbols()

        if not symbols:
            return self._default_sentiment(target_date)

        # 查询目标日期的日线K线
        klines = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.symbol.in_(symbols),
                DailyPrice.trade_date == target_date,
            )
            .all()
        )

        if not klines:
            return self._default_sentiment(target_date)

        # ---- 维度1：涨跌比 (AD Ratio) 权重35% ----
        advance = sum(1 for k in klines if (k.change_pct or 0) > 0)
        decline = sum(1 for k in klines if (k.change_pct or 0) < 0)
        flat = len(klines) - advance - decline
        total = len(klines)

        ad_ratio = advance / total if total > 0 else 0.5
        # 映射到0~100：50%上涨→50，100%上涨→100，0%上涨→0
        ad_score = ad_ratio * 100

        # ---- 维度2：平均涨跌幅 权重25% ----
        avg_chg = sum((k.change_pct or 0) for k in klines) / total
        # 将 -10% ~ +10% 映射到 0~100（±10%为极端）
        avg_chg_score = max(0.0, min(100.0, (avg_chg + 10) / 20 * 100))

        # ---- 维度3：换手率热度 权重20% ----
        turnover_values = [k.turnover for k in klines if k.turnover is not None]
        if turnover_values:
            avg_turnover = sum(turnover_values) / len(turnover_values)
            # 换手率 0~10%，活跃度与情绪正相关但中性为5%
            # 用 sigmoid-like 做映射：5% → 50，≥10% → 80，≤1% → 30
            turnover_score = max(20.0, min(90.0, avg_turnover * 10 + 35))
        else:
            avg_turnover = 0.0
            turnover_score = 50.0

        # ---- 维度4：成交额相对近5日均值 权重10% ----
        amount_score = self._calc_volume_ratio_score(symbols, target_date)
        volume_ratio = amount_score["ratio"]
        vol_score = amount_score["score"]

        # ---- 维度5：近3日趋势持续性 权重10% ----
        trend_score = self._calc_trend_score(symbols, target_date)

        # ---- 加权合成 ----
        composite = (
            ad_score * 0.35
            + avg_chg_score * 0.25
            + turnover_score * 0.20
            + vol_score * 0.10
            + trend_score * 0.10
        )
        composite = max(0.0, min(100.0, composite))

        return {
            "date": target_date.isoformat(),
            "index": round(composite, 1),
            "stock_count": total,
            "advance_count": advance,
            "decline_count": decline,
            "flat_count": flat,
            "avg_change_pct": round(avg_chg, 2),
            "avg_turnover": round(avg_turnover, 2),
            "volume_ratio": round(volume_ratio, 2),
            "market_mood": self._get_market_mood(avg_turnover, volume_ratio),
        }

    def _calc_volume_ratio_score(self, symbols: List[str], target_date: date) -> Dict:
        """计算成交额相对近5日均值的比率，转换为情绪分"""
        # 近5个交易日（不含当天）的均值
        hist_dates = [target_date - timedelta(days=i) for i in range(1, 8)]

        past_amounts = (
            self.db.query(func.avg(DailyPrice.amount))
            .filter(
                DailyPrice.symbol.in_(symbols),
                DailyPrice.trade_date.in_(hist_dates),
                DailyPrice.amount.isnot(None),
            )
            .scalar()
        )

        today_avg = (
            self.db.query(func.avg(DailyPrice.amount))
            .filter(
                DailyPrice.symbol.in_(symbols),
                DailyPrice.trade_date == target_date,
                DailyPrice.amount.isnot(None),
            )
            .scalar()
        )

        if not past_amounts or past_amounts == 0 or today_avg is None:
            return {"ratio": 1.0, "score": 50.0}

        ratio = today_avg / past_amounts
        # ratio 1.0→50, ≥2.0→80, ≤0.5→20
        score = max(20.0, min(80.0, (ratio - 1.0) * 30 + 50))
        return {"ratio": round(float(ratio), 2), "score": score}

    def _calc_trend_score(self, symbols: List[str], target_date: date) -> float:
        """计算近3日趋势持续性分数"""
        past_3 = [target_date - timedelta(days=i) for i in range(1, 4)]

        rows = (
            self.db.query(func.avg(DailyPrice.change_pct))
            .filter(
                DailyPrice.symbol.in_(symbols),
                DailyPrice.trade_date.in_(past_3),
            )
            .scalar()
        )

        if rows is None:
            return 50.0

        # 近3日均涨跌幅 -10~+10 → 0~100
        return max(0.0, min(100.0, (float(rows) + 10) / 20 * 100))

    def _get_tracked_symbols(self) -> List[str]:
        """获取需要计算情绪的股票列表（来自持仓）"""
        try:
            portfolios = self.db.query(Portfolio.symbol).distinct().all()
            return [p.symbol for p in portfolios]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    #  辅助方法                                                            #
    # ------------------------------------------------------------------ #

    def _default_sentiment(self, target_date: date) -> Dict:
        """无数据时返回默认中性"""
        return {
            "date": target_date.isoformat(),
            "index": 50.0,
            "stock_count": 0,
            "advance_count": 0,
            "decline_count": 0,
            "flat_count": 0,
            "avg_change_pct": 0.0,
            "avg_turnover": 0.0,
            "volume_ratio": 1.0,
            "market_mood": "正常",
        }

    def _get_sentiment_label(self, index: float) -> str:
        """根据指数获取情绪标签"""
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

    def _get_market_mood(self, avg_turnover: float, volume_ratio: float) -> str:
        """根据换手率和成交额比判断市场活跃度"""
        if avg_turnover >= 5 or volume_ratio >= 1.5:
            return "活跃"
        elif avg_turnover <= 1 or volume_ratio <= 0.6:
            return "低迷"
        else:
            return "正常"

    def _build_top_factors(self, data: Dict) -> List[str]:
        """基于行情数据构建主要特征描述"""
        factors = []
        adv = data.get("advance_count", 0)
        dec = data.get("decline_count", 0)
        total = data.get("stock_count", 0)

        if total > 0:
            if adv > dec:
                factors.append(f"持仓个股上涨居多（{adv}涨/{dec}跌）")
            elif dec > adv:
                factors.append(f"持仓个股下跌居多（{adv}涨/{dec}跌）")
            else:
                factors.append(f"持仓个股涨跌均衡（各{adv}只）")

        avg_chg = data.get("avg_change_pct", 0)
        if avg_chg > 1:
            factors.append(f"持仓平均涨幅{avg_chg:.2f}%")
        elif avg_chg < -1:
            factors.append(f"持仓平均跌幅{abs(avg_chg):.2f}%")

        mood = data.get("market_mood", "正常")
        if mood != "正常":
            factors.append(f"市场交投{mood}")

        return factors[:3]

    # ------------------------------------------------------------------ #
    #  报告生成                                                            #
    # ------------------------------------------------------------------ #

    def _generate_opening_report(self, sentiment: Dict, history: List[Dict]) -> str:
        index = sentiment["index"]
        change = sentiment["change"]
        label = sentiment["label"]

        if index >= 60:
            mood_desc = "市场情绪偏乐观，持仓股普遍走强"
        elif index >= 45:
            mood_desc = "市场情绪中性，持仓股多空均衡"
        elif index >= 30:
            mood_desc = "市场情绪偏谨慎，持仓股整体承压"
        else:
            mood_desc = "市场情绪低迷，持仓股普遍走弱"

        if change >= 10:
            trend_desc = f"情绪指数较昨日大幅回升(+{change})"
        elif change >= 5:
            trend_desc = f"情绪指数较昨日回升(+{change})"
        elif change > -5:
            trend_desc = f"情绪指数与昨日基本持平({change:+.1f})"
        elif change > -10:
            trend_desc = f"情绪指数较昨日回落({change:.1f})"
        else:
            trend_desc = f"情绪指数较昨日明显下降({change:.1f})"

        if index >= 70:
            suggestion = "建议积极布局，注意控制仓位避免追高"
        elif index >= 55:
            suggestion = "建议适度参与，关注强势持仓的机会"
        elif index >= 45:
            suggestion = "建议中性仓位，等待情绪方向明确"
        elif index >= 30:
            suggestion = "建议控制仓位，防御为主"
        else:
            suggestion = "建议减仓观望，等待情绪企稳"

        adv = sentiment.get("advance_count", 0)
        dec = sentiment.get("decline_count", 0)
        avg_chg = sentiment.get("avg_change_pct", 0)
        mood = sentiment.get("market_mood", "正常")

        report = f"""【开盘情绪简报】

{mood_desc}。{trend_desc}。

持仓股概况：{adv}只上涨、{dec}只下跌，平均涨跌幅{avg_chg:+.2f}%，市场交投{mood}。

操作建议：{suggestion}。"""

        return report

    def _generate_closing_report(self, sentiment: Dict, history: List[Dict]) -> str:
        index = sentiment["index"]
        change = sentiment["change"]
        label = sentiment["label"]

        if index >= 60:
            review = "今日持仓整体偏强，资金活跃度较高"
        elif index >= 45:
            review = "今日持仓多空相对均衡，震荡运行"
        elif index >= 30:
            review = "今日持仓整体承压，交投趋于谨慎"
        else:
            review = "今日持仓普遍走弱，避险情绪升温"

        if change >= 5:
            outlook = "情绪回暖态势有望延续"
        elif change <= -5:
            outlook = "需警惕情绪继续下行风险"
        else:
            outlook = "情绪或维持震荡格局"

        adv = sentiment.get("advance_count", 0)
        dec = sentiment.get("decline_count", 0)
        avg_chg = sentiment.get("avg_change_pct", 0)
        vol_ratio = sentiment.get("volume_ratio", 1.0)

        report = f"""【收盘情绪总结】

{review}。情绪指数收于{index}（{label}），持仓{adv}涨{dec}跌，平均涨跌幅{avg_chg:+.2f}%，成交额为近期均值的{vol_ratio:.1f}倍。

明日展望：{outlook}。"""

        return report


# ------------------------------------------------------------------ #
#  服务工厂                                                           #
# ------------------------------------------------------------------ #

def get_sentiment_service(db: Session) -> SentimentService:
    """获取情绪指数服务"""
    return SentimentService(db)
