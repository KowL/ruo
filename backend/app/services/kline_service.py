"""
K线数据服务 - KLine Data Service
提供K线数据的缓存、查询和更新功能
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sql_func
from app.core.database import get_db
from app.models.kline import KLineData as KLineModel

logger = logging.getLogger(__name__)


class KLineService:
    """K线数据服务类"""
    
    def __init__(self):
        self._db: Optional[Session] = None
    
    @property
    def db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    def get_kline_data(
        self,
        symbol: str,
        period: str = 'daily',
        limit: int = 60,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        从数据库获取K线数据
        
        Args:
            symbol: 股票代码
            period: 周期 (daily/weekly/monthly)
            limit: 返回条数
            end_date: 结束日期，默认今天
            
        Returns:
            K线数据列表
        """
        try:
            if end_date is None:
                end_date = datetime.now()
            
            query = self.db.query(KLineModel).filter(
                KLineModel.symbol == symbol,
                KLineModel.period == period,
                KLineModel.trade_date <= end_date.date()
            ).order_by(desc(KLineModel.trade_date)).limit(limit)
            
            results = query.all()
            
            # 按日期正序返回
            return [r.to_dict() for r in reversed(results)]
            
        except Exception as e:
            logger.error(f"从数据库获取K线数据失败: {symbol} {period}, 错误: {e}")
            return []
    
    def get_date_range(
        self,
        symbol: str,
        period: str = 'daily'
    ) -> tuple:
        """
        获取数据库中该股票K线数据的时间范围
        
        Returns:
            (最早日期, 最晚日期) 或 (None, None)
        """
        try:
            result = self.db.query(
                sql_func.min(KLineModel.trade_date),
                sql_func.max(KLineModel.trade_date)
            ).filter(
                KLineModel.symbol == symbol,
                KLineModel.period == period
            ).first()
            
            if result and result[0] and result[1]:
                return result[0], result[1]
            return None, None
            
        except Exception as e:
            logger.error(f"获取K线日期范围失败: {symbol} {period}, 错误: {e}")
            return None, None
    
    def get_missing_dates(
        self,
        symbol: str,
        period: str = 'daily',
        days: int = 60
    ) -> tuple:
        """
        获取缺失的数据日期范围
        
        Args:
            symbol: 股票代码
            period: 周期
            days: 需要多少天的数据
            
        Returns:
            (需要拉取的起始日期, 需要拉取的结束日期) 或 (None, None)
        """
        try:
            end_date = datetime.now().date()
            
            # 根据周期计算需要的起始日期
            if period == 'daily':
                start_date = end_date - timedelta(days=days * 2)  # 乘以2考虑周末节假日
            elif period == 'weekly':
                start_date = end_date - timedelta(days=days * 10)
            elif period == 'monthly':
                start_date = end_date - timedelta(days=days * 40)
            else:
                start_date = end_date - timedelta(days=days * 2)
            
            # 获取数据库中已有的最新日期
            _, latest_date = self.get_date_range(symbol, period)
            
            if latest_date is None:
                # 数据库没有数据，需要拉取全部
                return start_date, end_date
            
            if latest_date >= end_date:
                # 数据已是最新，无需拉取
                return None, None
            
            # 需要从最新日期的下一天拉取到结束日期
            return latest_date + timedelta(days=1), end_date
            
        except Exception as e:
            logger.error(f"计算缺失日期失败: {symbol} {period}, 错误: {e}")
            return None, None
    
    def save_kline_data(
        self,
        symbol: str,
        period: str,
        data: List[Dict]
    ) -> int:
        """
        保存K线数据到数据库
        
        Args:
            symbol: 股票代码
            period: 周期
            data: K线数据列表
            
        Returns:
            保存的条数
        """
        try:
            saved_count = 0
            
            for item in data:
                try:
                    # 解析日期
                    trade_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                    
                    # 检查是否已存在
                    existing = self.db.query(KLineModel).filter(
                        KLineModel.symbol == symbol,
                        KLineModel.period == period,
                        KLineModel.trade_date == trade_date
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.open = item['open']
                        existing.high = item['high']
                        existing.low = item['low']
                        existing.close = item['close']
                        existing.volume = item['volume']
                        existing.amount = item.get('amount')
                        existing.change = item.get('change')
                        existing.change_pct = item.get('changePct')
                        existing.turnover = item.get('turnover')
                    else:
                        # 创建新记录
                        kline = KLineModel(
                            symbol=symbol,
                            period=period,
                            trade_date=trade_date,
                            open=item['open'],
                            high=item['high'],
                            low=item['low'],
                            close=item['close'],
                            volume=item['volume'],
                            amount=item.get('amount'),
                            change=item.get('change'),
                            change_pct=item.get('changePct'),
                            turnover=item.get('turnover')
                        )
                        self.db.add(kline)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"保存单条K线数据失败: {symbol} {item.get('date')}, 错误: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"成功保存K线数据: {symbol} {period}, 共{saved_count}条")
            return saved_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存K线数据失败: {symbol} {period}, 错误: {e}")
            return 0
    
    def calculate_mas(self, symbol: str, period: str = 'daily') -> int:
        """
        计算并更新均线数据
        
        Args:
            symbol: 股票代码
            period: 周期
            
        Returns:
            更新的条数
        """
        try:
            # 获取该股票该周期的所有数据，按日期排序
            records = self.db.query(KLineModel).filter(
                KLineModel.symbol == symbol,
                KLineModel.period == period
            ).order_by(KLineModel.trade_date).all()
            
            if len(records) < 5:
                return 0
            
            updated_count = 0
            closes = [r.close for r in records]
            
            for i, record in enumerate(records):
                # 计算MA5
                if i >= 4:
                    record.ma5 = sum(closes[i-4:i+1]) / 5
                # 计算MA10
                if i >= 9:
                    record.ma10 = sum(closes[i-9:i+1]) / 10
                # 计算MA20
                if i >= 19:
                    record.ma20 = sum(closes[i-19:i+1]) / 20
                # 计算MA60
                if i >= 59:
                    record.ma60 = sum(closes[i-59:i+1]) / 60
                
                updated_count += 1
            
            self.db.commit()
            logger.info(f"成功计算均线: {symbol} {period}, 共{updated_count}条")
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"计算均线失败: {symbol} {period}, 错误: {e}")
            return 0
    
    def get_symbols_needing_update(
        self,
        min_days: int = 5
    ) -> List[str]:
        """
        获取需要更新K线数据的股票列表（数据缺失或过期）
        
        Args:
            min_days: 最少需要多少天的数据
            
        Returns:
            股票代码列表
        """
        try:
            # 获取所有有K线数据记录的股票
            results = self.db.query(
                KLineModel.symbol,
                sql_func.count(KLineModel.id).label('count'),
                sql_func.max(KLineModel.trade_date).label('latest_date')
            ).group_by(KLineModel.symbol).all()
            
            symbols_to_update = []
            today = datetime.now().date()
            
            for symbol, count, latest_date in results:
                # 数据不足或最近数据超过2天（考虑周末）
                if count < min_days or (today - latest_date).days > 2:
                    symbols_to_update.append(symbol)
            
            return symbols_to_update
            
        except Exception as e:
            logger.error(f"获取需要更新的股票列表失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self._db:
            self._db.close()
            self._db = None


# 单例模式
_kline_service = None

def get_kline_service() -> KLineService:
    """获取K线服务单例"""
    global _kline_service
    if _kline_service is None:
        _kline_service = KLineService()
    return _kline_service
