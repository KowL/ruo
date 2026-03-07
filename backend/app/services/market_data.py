"""
行情数据服务 - Market Data Service
v1.1 - 集成东财/雪球双数据源 + 熔断降级机制

功能：
- 基础行情接入（东财主力 + 雪球备用）
- 获取股票信息、实时价格、K线数据
- 股票搜索和自动补全
- 熔断降级自动切换
"""
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import time
from functools import wraps

from app.utils.stock_tool import stock_tool
from app.core.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


# 数据源熔断器配置
eastmoney_breaker = CircuitBreaker(
    name="eastmoney",
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=3
)

xueqiu_breaker = CircuitBreaker(
    name="xueqiu",
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=3
)


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
    """行情数据服务类 - 集成双数据源 + 熔断降级"""

    def __init__(self):
        self.cache = {}  # 内存缓存
        
        # 分级缓存TTL配置（秒）
        self.cache_ttl = {
            'realtime': 5,      # 实时价格: 5秒
            'batch_realtime': 5,  # 批量行情: 5秒
            'orderbook': 3,     # 盘口: 3秒
            'intraday': 30,     # 分时: 30秒
            'info': 3600,       # 股票信息: 1小时
            'default': 300      # 默认: 5分钟
        }
        
        # 熔断器引用
        self.breakers = {
            'eastmoney': eastmoney_breaker,
            'xueqiu': xueqiu_breaker
        }

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

            # 从 StockTool 获取股票信息
            info_dict = stock_tool.get_stock_info(symbol)

            if not info_dict:
                logger.warning(f"股票不存在或获取失败: {symbol}")
                return None

            result = {
                'symbol': symbol,
                'name': info_dict.get('name', ''),
                'industry': info_dict.get('industry', ''),
                'market': self._get_market_name(symbol),
                'listingDate': info_dict.get('listingDate', ''),
                'totalShares': info_dict.get('totalShares', ''),
            }

            # 缓存结果
            self.cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, 错误: {e}")
            raise

    def _get_cache(self, key: str, ttl_type: str = 'default'):
        """获取缓存数据"""
        if key in self.cache:
            cached_data, cached_time = self.cache[key]
            ttl = self.cache_ttl.get(ttl_type, self.cache_ttl['default'])
            if time.time() - cached_time < ttl:
                return cached_data
        return None
    
    def _set_cache(self, key: str, data):
        """设置缓存数据"""
        self.cache[key] = (data, time.time())

    @retry_on_error(max_retries=3, delay=1.0)
    def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        """
        获取实时行情（东财主力 + 雪球备用）

        Args:
            symbol: 股票代码

        Returns:
            实时行情数据，包含 source 和 degraded 字段
        """
        cache_key = f"realtime:{symbol}"
        cached = self._get_cache(cache_key, 'realtime')
        if cached:
            logger.debug(f"从缓存返回实时行情: {symbol}")
            return cached

        # 优先使用东财（通过熔断器保护）
        if eastmoney_breaker.can_execute():
            try:
                data = stock_tool.get_realtime_eastmoney_single(symbol)
                if data:
                    eastmoney_breaker.record_success()
                    result = {
                        'symbol': symbol,
                        'name': data.get('name', ''),
                        'price': data.get('price', 0),
                        'change': data.get('change', 0),
                        'changePct': data.get('changePct', 0),
                        'open': data.get('open', 0),
                        'high': data.get('high', 0),
                        'low': data.get('low', 0),
                        'close': data.get('preClose', 0),
                        'volume': data.get('volume', 0),
                        'amount': data.get('amount', 0),
                        'marketCap': data.get('marketCap', 0),
                        'floatMarketCap': data.get('floatMarketCap', 0),
                        'source': 'eastmoney',
                        'degraded': False,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                eastmoney_breaker.record_failure()
                logger.warning(f"东财单股接口失败，尝试雪球: {e}")
        
        # 降级到雪球
        if xueqiu_breaker.can_execute():
            try:
                data = stock_tool.get_realtime_xueqiu_single(symbol)
                if data:
                    xueqiu_breaker.record_success()
                    result = {
                        'symbol': symbol,
                        'name': data.get('name', ''),
                        'price': data.get('price', 0),
                        'change': data.get('change', 0),
                        'changePct': data.get('changePct', 0),
                        'open': data.get('open', 0),
                        'high': data.get('high', 0),
                        'low': data.get('low', 0),
                        'close': data.get('preClose', 0),
                        'volume': data.get('volume', 0),
                        'amount': data.get('amount', 0),
                        'marketCap': data.get('marketCap', 0),
                        'floatMarketCap': data.get('floatMarketCap', 0),
                        'source': 'xueqiu',
                        'degraded': True,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                xueqiu_breaker.record_failure()
                logger.error(f"雪球单股接口也失败: {e}")
        
        logger.error(f"所有数据源均不可用: {symbol}")
        return None

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
            # 雪球个股详情接口
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

            logger.debug(f"调用雪球接口: ak.stock_individual_spot_xq(symbol='{market_code}')")
            try:
                # 使用 stock_individual_spot_xq 获取实时行情
                df = ak.stock_individual_spot_xq(symbol=market_code)
            except Exception as api_err:
                logger.warning(f"雪球接口调用异常: {api_err}")
                return 0.0
            
            if df.empty:
                logger.warning(f"雪球接口未获取到数据: {symbol}")
                return 0.0

            # df columns: [item, value]
            # 查找 '现价'
            price_row = df[df['item'] == '现价']
            if not price_row.empty:
                val = price_row.iloc[0]['value']
                # 处理可能的非数字情况
                try:
                    price = float(val)
                    return price
                except (ValueError, TypeError):
                    logger.warning(f"雪球价格无法转换为浮点数: {val}")
                    return 0.0
            
            logger.warning(f"雪球数据中未找到 '现价': {symbol}")
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
        获取行情数据（优先从数据库读取，不足时从 stock_tool 补充并缓存）

        Args:
            symbol: 股票代码
            period: 周期（daily/weekly/monthly）
            limit: 返回条数

        Returns:
            行情数据列表（与原 K线接口格式相同）
        """
        try:
            from app.services.market_price_service import get_market_price_service

            price_service = get_market_price_service()

            # 1. 优先从数据库读取
            db_data = price_service.get_price_data(symbol, period, limit)

            if len(db_data) >= limit:
                logger.debug(f"从数据库返回行情数据: {symbol} {period}, {len(db_data)} 条")
                return db_data

            # 2. 数据不足，调用 StockTool 拉取
            logger.info(f"数据库行情数据不足，从数据源拉取: {symbol} {period}")
            days_map = {'daily': 2, 'weekly': 10, 'monthly': 40}
            delta_days = limit * days_map.get(period, 2) + 30
            start_date = (datetime.now() - timedelta(days=delta_days)).strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')

            df = stock_tool.get_market_data_list(
                symbol=symbol, period=period,
                start_date=start_date, end_date=end_date, adjust='qfq'
            )

            if df is None or df.empty:
                logger.warning(f"未找到行情数据: {symbol} {period}")
                return db_data

            market_data = df.to_dict('records')

            # 3. 保存到数据库
            saved = price_service.save_price_data(symbol, period, market_data)
            if saved > 0:
                price_service.calculate_mas(symbol, period)

            # 4. 再次从数据库读取（确保有序且有均线）
            final = price_service.get_price_data(symbol, period, limit)
            logger.info(f"行情数据已更新: {symbol} {period}, 返回 {len(final)} 条")
            return final

        except ValueError as e:
            logger.error(f"参数错误: {e}")
            raise
        except Exception as e:
            logger.error(f"获取行情数据失败: {symbol}, 错误: {e}")
            try:
                from app.services.market_price_service import get_market_price_service
                return get_market_price_service().get_price_data(symbol, period, limit)
            except Exception:
                raise

    @retry_on_error(max_retries=3, delay=1.0)
    def batch_get_realtime_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时行情（东财批量 + 熔断降级）

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: price_data} 字典，包含 source 和 degraded 字段
        """
        if not symbols:
            return {}
        
        # 检查缓存
        cache_key = f"batch_realtime:{','.join(sorted(symbols))}"
        cached = self._get_cache(cache_key, 'batch_realtime')
        if cached:
            logger.debug("从缓存返回批量实时行情")
            return cached

        # 使用统一接口（自动处理主备切换）
        results = stock_tool.get_realtime_quotes_unified(symbols, prefer_source='eastmoney')
        
        # 格式化返回数据
        formatted_results = {}
        for symbol, data in results.items():
            formatted_results[symbol] = {
                'symbol': symbol,
                'name': data.get('name', ''),
                'price': data.get('price', 0),
                'change': data.get('change', 0),
                'changePct': data.get('changePct', 0),
                'volume': data.get('volume', 0),
                'amount': data.get('amount', 0),
                'high': data.get('high', 0),
                'low': data.get('low', 0),
                'open': data.get('open', 0),
                'preClose': data.get('preClose', 0),
                'source': data.get('source', 'unknown'),
                'degraded': data.get('degraded', False),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
        
        # 更新熔断器状态
        if any(d.get('source') == 'eastmoney' and not d.get('degraded') for d in results.values()):
            eastmoney_breaker.record_success()
        elif results:
            # 如果全部降级，说明东财可能有问题
            pass
        
        # 缓存结果
        self._set_cache(cache_key, formatted_results)
        
        logger.info(f"批量行情获取完成: {len(formatted_results)} 只, " +
                   f"降级: {sum(1 for d in formatted_results.values() if d.get('degraded'))} 只")
        
        return formatted_results
    
    def get_datasource_health(self) -> Dict:
        """
        获取数据源健康状态
        
        Returns:
            各数据源熔断器状态
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }

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

            # 优先从新浪财经获取分时数据
            intraday_data = stock_tool.get_intraday_from_sina(symbol)
            
            # 如果新浪失败，尝试东方财富
            if not intraday_data:
                intraday_data = stock_tool.get_intraday_from_eastmoney(symbol)

            if not intraday_data:
                logger.warning(f"获取分时数据失败: {symbol}")
                return []

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

            # 使用 StockTool 获取实时行情快照（包含买卖盘）
            spot_data = stock_tool.get_realtime_quotes()
            
            if spot_data is None or spot_data.empty:
                return {'buyOrders': [], 'sellOrders': []}

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
