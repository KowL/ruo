"""
行情数据服务 - Market Price Service
提供日线/周线/月线数据的查询、保存、均线计算和历史清理功能

替代原 kline_service.py，适配三表结构。
"""
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Type
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sql_func

from app.core.database import get_db
from app.models.market_price import DailyPrice, WeeklyPrice, MonthlyPrice, PERIOD_MODEL_MAP

logger = logging.getLogger(__name__)

# 近10年保留限制
DATA_RETENTION_YEARS = 10


def _get_model(period: str):
    """根据周期返回对应 ORM 模型"""
    model = PERIOD_MODEL_MAP.get(period)
    if model is None:
        raise ValueError(f"不支持的周期: {period}，可选: daily / weekly / monthly")
    return model


class MarketPriceService:
    """行情数据服务（日线/周线/月线三表）"""

    def __init__(self):
        self._db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = next(get_db())
        return self._db

    # ------------------------------------------------------------------ #
    #  查询                                                                #
    # ------------------------------------------------------------------ #

    def get_price_data(
        self,
        symbol: str,
        period: str = 'daily',
        limit: int = 60,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        从数据库获取行情数据

        Args:
            symbol: 股票代码
            period: 周期 daily/weekly/monthly
            limit: 返回条数
            end_date: 结束日期，默认今天

        Returns:
            行情数据列表（按日期正序）
        """
        try:
            model = _get_model(period)
            if end_date is None:
                end_date = datetime.now()

            results = (
                self.db.query(model)
                .filter(
                    model.symbol == symbol,
                    model.trade_date <= end_date.date(),
                )
                .order_by(desc(model.trade_date))
                .limit(limit)
                .all()
            )

            return [r.to_dict() for r in reversed(results)]

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"查询行情数据失败: {symbol} {period}, 错误: {e}")
            return []

    def get_date_range(self, symbol: str, period: str = 'daily'):
        """获取数据库中该股票某周期的时间范围，返回 (min_date, max_date)"""
        try:
            model = _get_model(period)
            result = self.db.query(
                sql_func.min(model.trade_date),
                sql_func.max(model.trade_date),
            ).filter(model.symbol == symbol).first()

            if result and result[0] and result[1]:
                return result[0], result[1]
            return None, None

        except Exception as e:
            logger.error(f"获取日期范围失败: {symbol} {period}, 错误: {e}")
            return None, None

    def get_record_count(self, symbol: str, period: str = 'daily') -> int:
        """获取数据库中该股票某周期的记录数"""
        try:
            model = _get_model(period)
            return self.db.query(model).filter(model.symbol == symbol).count()
        except Exception as e:
            logger.error(f"获取记录数失败: {symbol} {period}, 错误: {e}")
            return 0

    # ------------------------------------------------------------------ #
    #  保存                                                                #
    # ------------------------------------------------------------------ #

    def save_price_data(
        self,
        symbol: str,
        period: str,
        data: List[Dict],
    ) -> int:
        """
        upsert 行情数据到对应表

        Args:
            symbol: 股票代码
            period: 周期
            data: 行情数据列表，每条需含 date/open/high/low/close/volume 字段

        Returns:
            保存/更新的记录数
        """
        model = _get_model(period)
        saved = 0
        try:
            for item in data:
                try:
                    trade_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                    existing = (
                        self.db.query(model)
                        .filter(model.symbol == symbol, model.trade_date == trade_date)
                        .first()
                    )
                    if existing:
                        existing.open = item['open']
                        existing.high = item['high']
                        existing.low = item['low']
                        existing.close = item['close']
                        existing.pre_close = item.get('preClose')
                        existing.volume = item['volume']
                        existing.amount = item.get('amount')
                        existing.change = item.get('change')
                        existing.change_pct = item.get('changePct')
                        existing.turnover = item.get('turnover')
                    else:
                        record = model(
                            symbol=symbol,
                            trade_date=trade_date,
                            open=item['open'],
                            high=item['high'],
                            low=item['low'],
                            close=item['close'],
                            pre_close=item.get('preClose'),
                            volume=item['volume'],
                            amount=item.get('amount'),
                            change=item.get('change'),
                            change_pct=item.get('changePct'),
                            turnover=item.get('turnover'),
                        )
                        self.db.add(record)
                    saved += 1
                except Exception as e:
                    logger.warning(f"保存单条数据失败: {symbol} {item.get('date')}, 错误: {e}")
                    continue

            self.db.commit()
            logger.info(f"保存行情数据: {symbol} {period}, 共 {saved} 条")
            return saved

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存行情数据失败: {symbol} {period}, 错误: {e}")
            return 0

    # ------------------------------------------------------------------ #
    #  均线计算                                                            #
    # ------------------------------------------------------------------ #

    def calculate_mas(self, symbol: str, period: str = 'daily') -> int:
        """
        计算并更新 ma5/ma10/ma20/ma60

        Returns:
            更新的记录数
        """
        model = _get_model(period)
        try:
            records = (
                self.db.query(model)
                .filter(model.symbol == symbol)
                .order_by(model.trade_date)
                .all()
            )

            if len(records) < 5:
                return 0

            closes = [r.close for r in records]
            updated = 0

            for i, record in enumerate(records):
                if i >= 4:
                    record.ma5 = round(sum(closes[i - 4:i + 1]) / 5, 4)
                if i >= 9:
                    record.ma10 = round(sum(closes[i - 9:i + 1]) / 10, 4)
                if i >= 19:
                    record.ma20 = round(sum(closes[i - 19:i + 1]) / 20, 4)
                if i >= 59:
                    record.ma60 = round(sum(closes[i - 59:i + 1]) / 60, 4)
                updated += 1

            self.db.commit()
            logger.info(f"均线计算完成: {symbol} {period}, {updated} 条")
            return updated

        except Exception as e:
            self.db.rollback()
            logger.error(f"计算均线失败: {symbol} {period}, 错误: {e}")
            return 0

    # ------------------------------------------------------------------ #
    #  清理旧数据                                                          #
    # ------------------------------------------------------------------ #

    def cleanup_old_data(self, period: str, years: int = DATA_RETENTION_YEARS) -> int:
        """
        删除超过 N 年的行情数据

        Args:
            period: 周期
            years: 保留最近 N 年，默认10年

        Returns:
            删除的记录数
        """
        model = _get_model(period)
        cutoff = date.today().replace(year=date.today().year - years)
        try:
            deleted = (
                self.db.query(model)
                .filter(model.trade_date < cutoff)
                .delete(synchronize_session=False)
            )
            self.db.commit()
            logger.info(f"清理旧数据: {period} {cutoff} 之前共 {deleted} 条")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"清理旧数据失败: {period}, 错误: {e}")
            return 0

    # ------------------------------------------------------------------ #
    #  统计                                                                #
    # ------------------------------------------------------------------ #

    def get_latest_date(self, symbol: str, period: str = 'daily') -> Optional[date]:
        """获取数据库中该股票某周期的最新日期"""
        _, latest = self.get_date_range(symbol, period)
        return latest

    def close(self):
        if self._db:
            self._db.close()
            self._db = None


# ------------------------------------------------------------------ #
#  工厂函数                                                            #
# ------------------------------------------------------------------ #

_service: Optional[MarketPriceService] = None


def get_market_price_service() -> MarketPriceService:
    """获取行情数据服务（懒加载单例）"""
    global _service
    if _service is None:
        _service = MarketPriceService()
    return _service
