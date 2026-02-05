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
        
        优化：从本地数据库搜索，速度更快，支持离线
        """
        try:
            from app.core.database import get_db
            from app.models.stock import Stock
            from sqlalchemy.orm import Session
            
            # 使用 DB session
            db: Session = next(get_db())
            
            # 搜索匹配 (代码或名称)
            keyword = keyword.strip().upper()
            
            # 使用 ILIKE 进行模糊匹配，限制 10 条
            stocks = db.query(Stock).filter(
                (Stock.symbol.like(f"%{keyword}%")) | 
                (Stock.name.like(f"%{keyword}%"))
            ).limit(10).all()
            
            results = []
            for stock in stocks:
                results.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'market': stock.market if stock.market else self._get_market_name(stock.symbol),
                    'price': stock.current_price if stock.current_price is not None else 0.0,
                    'changePct': stock.change_pct if stock.change_pct is not None else 0.0,
                    'change': 0.0, 
                })
            
            db.close()



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
                'listingDate': info_dict.get('上市时间', ''),
                'totalShares': info_dict.get('总股本', ''),
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
                'changePct': float(row['涨跌幅']),
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
    def get_stock_price_xq(self, symbol: str) -> float:
        """
        获取股票当前价格（雪球接口，用于备用）

        Args:
            symbol: 股票代码

        Returns:
            当前价格，如果获取失败返回 0.0
        """
        try:
            # AkShare 雪球个股详情接口
            # ak.stock_individual_basic_info_xq(symbol="SH600519")
            # 需要转换代码格式：600519 -> SH600519, 000001 -> SZ000001
            market_code = ""
            if symbol.startswith("6"):
                market_code = f"SH{symbol}"
            elif symbol.startswith("0") or symbol.startswith("3"):
                market_code = f"SZ{symbol}"
            elif symbol.startswith("8") or symbol.startswith("4"):
                market_code = f"BJ{symbol}"
            else:
                logger.warning(f"无法识别的市场代码格式: {symbol}")
                return 0.0

            logger.debug(f"调用雪球接口: ak.stock_individual_basic_info_xq(symbol='{market_code}')")
            try:
                df = ak.stock_individual_basic_info_xq(symbol=market_code)
            except Exception as api_err:
                logger.warning(f"雪球接口调用异常: {api_err}")
                return 0.0
            
            if df.empty:
                logger.warning(f"雪球接口未获取到数据: {symbol}")
                return 0.0

            # df 通常包含 'item' 和 'value' 列，或者直接是宽表
            # 打印一下看看结构，通常是 current_price 字段
            # 根据文档，返回的是 DataFrame，字段可能包含 "current_price"
            
            # 使用 item/value 结构查找 (假设) 或者直接列名
            # 实测 akshare stock_individual_basic_info_xq 返回的是:
            # item      value
            # current_price 1700.0
            # ...
            
            # 查找 current_price
            price_row = df[df['item'] == 'current_price']
            if not price_row.empty:
                price = float(price_row.iloc[0]['value'])
                return price
            
            # 尝试查找 'last_close' 或其他
            logger.warning(f"雪球数据中未找到 current_price: {symbol}")
            return 0.0

        except Exception as e:
            logger.error(f"雪球接口获取价格失败: {symbol}, 错误: {e}")
            return 0.0

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

            # 计算开始日期（大致估算，多取一些以防节假日）
            # 每日数据：limit * 2 天
            # 每周数据：limit * 10 天
            # 每月数据：limit * 40 天
            days_map = {'daily': 2, 'weekly': 10, 'monthly': 40}
            delta_days = limit * days_map.get(period, 2) + 30  # 额外加30天缓冲
            start_date = (datetime.now() - timedelta(days=delta_days)).strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')

            # According to AkShare documentation: https://akshare.akfamily.xyz/data/stock/stock.html#id23
            # stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20210907', adjust="qfq")
            
            # 根据周期选择 AkShare 接口
            if period == 'daily':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='daily',
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'
                )
            elif period == 'weekly':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='weekly',
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'
                )
            elif period == 'monthly':
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period='monthly',
                    start_date=start_date,
                    end_date=end_date,
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
                    'change': float(row['涨跌额']) if '涨跌额' in row else 0,
                    'changePct': float(row['涨跌幅']) if '涨跌幅' in row else 0,
                    'turnover': float(row['换手率']) if '换手率' in row else 0,
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
                    'changePct': float(row['涨跌幅']),
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

    @retry_on_error(max_retries=3, delay=1.0)
    def get_intraday_data(self, symbol: str) -> List[Dict]:
        """
        获取分时数据

        Args:
            symbol: 股票代码

        Returns:
            分时数据列表
        """
        try:
            # 检查缓存（分时数据短期缓存）
            cache_key = f"intraday:{symbol}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                # 分时数据缓存30秒
                if time.time() - cached_time < 30:
                    logger.debug(f"从缓存返回分时数据: {symbol}")
                    return cached_data

            # 使用 AkShare 获取分时数据
            # 根据市场选择不同的接口
            if symbol.startswith('6') or symbol.startswith('688'):
                # 上海市场
                df = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1', adjust='')
            else:
                # 深圳市场
                df = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1', adjust='')

            if df.empty:
                logger.warning(f"未找到分时数据: {symbol}")
                return []

            # 转换为字典列表
            intraday_data = []
            total_volume = 0
            total_amount = 0

            for _, row in df.iterrows():
                volume = float(row['成交量']) if '成交量' in row else 0
                amount = float(row['成交额']) if '成交额' in row else 0
                total_volume += volume
                total_amount += amount

                # 计算均价
                avg_price = amount / volume if volume > 0 else 0

                intraday_data.append({
                    'time': row['时间'].strftime('%H:%M:%S') if '时间' in row else row.name.strftime('%H:%M:%S'),
                    'price': float(row['收盘']),
                    'volume': volume,
                    'avgPrice': avg_price
                })

            # 缓存结果
            self.cache[cache_key] = (intraday_data, time.time())

            return intraday_data

        except Exception as e:
            logger.error(f"获取分时数据失败: {symbol}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def get_order_book_data(self, symbol: str) -> Dict:
        """
        获取买卖盘数据（五档）

        Args:
            symbol: 股票代码

        Returns:
            买卖盘数据字典
        """
        try:
            # 买卖盘数据使用极短期缓存（5秒）
            cache_key = f"orderbook:{symbol}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < 5:
                    logger.debug(f"从缓存返回买卖盘数据: {symbol}")
                    return cached_data

            # 使用 AkShare 获取实时行情（包含买卖盘）
            spot_data = ak.stock_zh_a_spot_em()

            # 查找指定股票
            stock_data = spot_data[spot_data['代码'] == symbol]

            if stock_data.empty:
                logger.warning(f"未找到股票买卖盘数据: {symbol}")
                return {'buyOrders': [], 'sellOrders': []}

            row = stock_data.iloc[0]

            # 解析买一到买五
            buy_orders = []
            for i in range(1, 6):
                price_col = f'买{i}_价'
                volume_col = f'买{i}_量'
                if price_col in row and volume_col in row:
                    price = float(row[price_col]) if pd.notna(row[price_col]) else 0
                    volume = float(row[volume_col]) if pd.notna(row[volume_col]) else 0
                    if price > 0:
                        buy_orders.append({
                            'level': i,
                            'price': price,
                            'volume': int(volume)
                        })

            # 解析卖一到卖五
            sell_orders = []
            for i in range(1, 6):
                price_col = f'卖{i}_价'
                volume_col = f'卖{i}_量'
                if price_col in row and volume_col in row:
                    price = float(row[price_col]) if pd.notna(row[price_col]) else 0
                    volume = float(row[volume_col]) if pd.notna(row[volume_col]) else 0
                    if price > 0:
                        sell_orders.append({
                            'level': i,
                            'price': price,
                            'volume': int(volume)
                        })

            result = {
                'buyOrders': buy_orders,
                'sellOrders': sell_orders
            }

            # 缓存结果（5秒）
            self.cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            logger.error(f"获取买卖盘数据失败: {symbol}, 错误: {e}")
            raise

    @retry_on_error(max_retries=3, delay=1.0)
    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """
        获取股票完整详情（含基础行情、分时、买卖盘）

        Args:
            symbol: 股票代码

        Returns:
            股票完整详情字典
        """
        try:
            # 获取基础行情
            realtime = self.get_realtime_price(symbol)
            if not realtime:
                return None

            # 获取分时数据
            intraday = self.get_intraday_data(symbol)

            # 获取买卖盘数据
            order_book = self.get_order_book_data(symbol)

            # 计算换手率
            volume = realtime.get('volume', 0)
            amount = realtime.get('amount', 0)
            turnover = (amount / (volume * realtime.get('price', 1))) * 100 if volume > 0 and amount > 0 else 0

            result = {
                'symbol': realtime['symbol'],
                'name': realtime['name'],
                'price': realtime['price'],
                'change': realtime['change'],
                'changePct': realtime['changePct'],
                'open': realtime['open'],
                'high': realtime['high'],
                'low': realtime['low'],
                'volume': volume,
                'amount': amount,
                'turnover': round(turnover, 2),
                'timestamp': realtime['timestamp'],
                'intraday': intraday,
                'buyOrders': order_book.get('buyOrders', []),
                'sellOrders': order_book.get('sellOrders', [])
            }

            return result

        except Exception as e:
            logger.error(f"获取股票详情失败: {symbol}, 错误: {e}")
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
