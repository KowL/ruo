"""
行情数据服务 - Market Data Service
MVP v0.1

功能：
- F-01: 基础行情接入（AkShare/Tushare）
- 获取股票信息、实时价格、K线数据
- 股票搜索和自动补全
"""
import akshare as ak
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    错误重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} 第 {attempt + 1} 次调用失败: {e}, "
                            f"{delay} 秒后重试..."
                        )
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        logger.error(
                            f"{func.__name__} 重试 {max_retries} 次后仍然失败: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


class MarketDataService:
    """行情数据服务类"""

    def __init__(self):
        self.cache = {}  # 简单缓存，后续可以替换为 Redis
        self.cache_ttl = 300  # 缓存过期时间（秒）

    @retry_on_error(max_retries=3, delay=1.0)
    def search_stock(self, keyword: str) -> List[Dict]:
        """
        搜索股票（自动补全）

        Args:
            keyword: 股票代码或名称，如 "000001" 或 "平安"

        Returns:
            股票列表
        """
        try:
            # 检查缓存
            cache_key = f"search:{keyword}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    logger.debug(f"从缓存返回搜索结果: {keyword}")
                    return cached_data

            # 获取股票列表
            stock_info = ak.stock_info_a_code_name()

            # 搜索匹配
            keyword = keyword.strip().upper()
            results = []

            for _, row in stock_info.iterrows():
                code = row['code']
                name = row['name']

                # 匹配代码或名称
                if keyword in code or keyword in name:
                    results.append({
                        'symbol': code,
                        'name': name,
                        'market': self._get_market_name(code)
                    })

                    # 限制返回数量
                    if len(results) >= 10:
                        break

            # 缓存结果
            self.cache[cache_key] = (results, time.time())

            return results

        except Exception as e:
            logger.error(f"搜索股票失败: {keyword}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码，如 "000001"

        Returns:
            股票信息字典
        """
        try:
            # 检查缓存
            cache_key = f"info:{symbol}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    logger.debug(f"从缓存返回股票信息: {symbol}")
                    return cached_data

            # 从 AkShare 获取股票信息
            stock_info = ak.stock_individual_info_em(symbol=symbol)

            if stock_info.empty:
                logger.warning(f"股票不存在: {symbol}")
                return None

            # 转换为字典
            info_dict = {}
            for _, row in stock_info.iterrows():
                info_dict[row['item']] = row['value']

            result = {
                'symbol': symbol,
                'name': info_dict.get('股票简称', ''),
                'industry': info_dict.get('行业', ''),
                'market': self._get_market_name(symbol),
                'listing_date': info_dict.get('上市时间', ''),
                'total_shares': info_dict.get('总股本', ''),
            }

            # 缓存结果
            self.cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        """
        获取实时行情

        Args:
            symbol: 股票代码

        Returns:
            实时行情数据
        """
        try:
            # 实时行情不使用长期缓存，只使用短期缓存（10秒）
            cache_key = f"realtime:{symbol}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < 10:  # 10秒缓存
                    logger.debug(f"从缓存返回实时行情: {symbol}")
                    return cached_data

            # 使用 AkShare 获取实时行情
            realtime_data = ak.stock_zh_a_spot_em()

            # 查找指定股票
            stock_data = realtime_data[realtime_data['代码'] == symbol]

            if stock_data.empty:
                logger.warning(f"未找到股票行情: {symbol}")
                return None

            row = stock_data.iloc[0]

            result = {
                'symbol': symbol,
                'name': row['名称'],
                'price': float(row['最新价']),
                'change': float(row['涨跌额']),
                'change_pct': float(row['涨跌幅']),
                'open': float(row['今开']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'close': float(row['昨收']),
                'volume': float(row['成交量']),
                'amount': float(row['成交额']),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 缓存结果（10秒）
            self.cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            logger.error(f"获取实时行情失败: {symbol}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def get_kline_data(
        self,
        symbol: str,
        period: str = 'daily',
        limit: int = 60
    ) -> List[Dict]:
        """
        获取 K 线数据

        Args:
            symbol: 股票代码
            period: 周期（daily/weekly/monthly）
            limit: 返回数量

        Returns:
            K 线数据列表
        """
        try:
            # 检查缓存（K线数据可以缓存较长时间）
            cache_key = f"kline:{symbol}:{period}:{limit}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                # K线数据缓存1小时
                if time.time() - cached_time < 3600:
                    logger.debug(f"从缓存返回K线数据: {symbol} {period}")
                    return cached_data

            # 根据周期选择 AkShare 接口
            if period == 'daily':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='daily',
                    adjust='qfq'  # 前复权
                )
            elif period == 'weekly':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='weekly',
                    adjust='qfq'
                )
            elif period == 'monthly':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='monthly',
                    adjust='qfq'
                )
            else:
                raise ValueError(f"不支持的周期: {period}")

            if df.empty:
                logger.warning(f"未找到K线数据: {symbol} {period}")
                return []

            # 只取最近 N 条
            df = df.tail(limit)

            # 转换为字典列表
            kline_data = []
            for _, row in df.iterrows():
                kline_data.append({
                    'date': row['日期'].strftime('%Y-%m-%d'),
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': float(row['成交量']),
                    'amount': float(row['成交额']) if '成交额' in row else 0,
                })

            # 缓存结果
            self.cache[cache_key] = (kline_data, time.time())

            return kline_data

        except ValueError as e:
            logger.error(f"参数错误: {e}")
            raise
        except Exception as e:
            logger.error(f"获取K线数据失败: {symbol}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def batch_get_realtime_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: price_data} 字典
        """
        try:
            # 检查缓存
            cache_key = "batch_realtime"
            cached_all_data = None

            if cache_key in self.cache:
                cached_all_data, cached_time = self.cache[cache_key]
                # 批量数据缓存10秒
                if time.time() - cached_time < 10:
                    logger.debug("从缓存返回批量实时行情")
                    # 从缓存中筛选需要的股票
                    result = {}
                    for symbol in symbols:
                        if symbol in cached_all_data:
                            result[symbol] = cached_all_data[symbol]
                    if len(result) == len(symbols):
                        return result

            # 获取所有A股实时行情
            realtime_data = ak.stock_zh_a_spot_em()

            # 构建所有股票的字典（用于缓存）
            all_data = {}
            for _, row in realtime_data.iterrows():
                symbol = row['代码']
                all_data[symbol] = {
                    'price': float(row['最新价']),
                    'change': float(row['涨跌额']),
                    'change_pct': float(row['涨跌幅']),
                    'name': row['名称']
                }

            # 缓存所有数据
            self.cache[cache_key] = (all_data, time.time())

            # 筛选需要的股票
            result = {}
            for symbol in symbols:
                if symbol in all_data:
                    result[symbol] = all_data[symbol]
                else:
                    logger.warning(f"未找到股票行情: {symbol}")

            return result

        except Exception as e:
            logger.error(f"批量获取实时行情失败, 错误: {e}")
            raise

    def _get_market_name(self, symbol: str) -> str:
        """
        根据代码判断市场

        Args:
            symbol: 股票代码

        Returns:
            市场名称
        """
        if symbol.startswith('6'):
            return '上海主板'
        elif symbol.startswith('000') or symbol.startswith('001'):
            return '深圳主板'
        elif symbol.startswith('002'):
            return '深圳中小板'
        elif symbol.startswith('300'):
            return '深圳创业板'
        elif symbol.startswith('688'):
            return '上海科创板'
        elif symbol.startswith('8'):
            return '北京交易所'
        else:
            return '未知市场'


# 单例模式
_market_data_service = None

def get_market_data_service() -> MarketDataService:
    """获取行情数据服务单例"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service
