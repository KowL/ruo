"""
通用行情数据工具 - StockTool

统一封装所有获取股票外部数据源（Tushare/AkShare/EastMoney/Xueqiu等）的方法。
按配置优先级回退：
  历史数据: 优先 Tushare -> 回退 AkShare
  实时数据: 优先 EastMoney(批量) -> 回退 Xueqiu(批量) -> 回退单股接口
"""
import logging
import time
import json
import requests
import urllib3
from functools import wraps
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

try:
    import tushare as ts
except ImportError:
    ts = None

from app.core.config import settings

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class StockTool:
    """内部行情调用工具，封装回退降级逻辑"""

    def __init__(self):
        self.use_tushare = settings.USE_TUSHARE and bool(settings.TUSHARE_TOKEN)
        self.ts_pro = ts.pro_api(settings.TUSHARE_TOKEN)
        self.ts_pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
        
        # HTTP 会话复用
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 东财接口基础配置
        self._eastmoney_base_url = "https://push2.eastmoney.com/api/qt"
        
        # 雪球接口基础配置
        self._xueqiu_base_url = "https://stock.xueqiu.com/v5/stock"
        self._xueqiu_cookie = None  # 雪球需要登录态

    def _to_ts_code(self, symbol: str) -> str:
        """转换代码到 Tushare 格式"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"{symbol}.SZ"
        elif symbol.startswith('4') or symbol.startswith('8') or symbol.startswith('9'):
            return f"{symbol}.BJ"
        return symbol
    
    def _to_eastmoney_code(self, symbol: str) -> str:
        """
        转换代码到东财格式
        市场代码: 0=深圳, 1=上海
        """
        if symbol.startswith('6'):
            return f"1.{symbol}"
        else:
            # 0, 3, 2 开头都是深圳
            return f"0.{symbol}"
    
    def _from_eastmoney_code(self, em_code: str) -> str:
        """从东财格式转换回标准代码"""
        return em_code.split('.')[-1] if '.' in em_code else em_code
    
    def _to_xueqiu_code(self, symbol: str) -> str:
        """
        转换代码到雪球格式
        SH600519, SZ000001
        """
        if symbol.startswith('6'):
            return f"SH{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3') or symbol.startswith('2'):
            return f"SZ{symbol}"
        elif symbol.startswith('4') or symbol.startswith('8') or symbol.startswith('9'):
            return f"BJ{symbol}"
        return symbol
    
    def _retry_on_error(self, max_retries: int = 3, delay: float = 0.5):
        """错误重试装饰器"""
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
                            sleep_time = delay * (attempt + 1)
                            logger.warning(f"{func.__name__} 第 {attempt + 1} 次失败: {e}, {sleep_time}s 后重试...")
                            time.sleep(sleep_time)
                        else:
                            logger.error(f"{func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                raise last_exception
            return wrapper
        return decorator

    def get_market_data_list(
        self,
        symbol: str,
        period: str = 'daily',
        start_date: str = None,
        end_date: str = None,
        adjust: str = 'qfq'
    ) -> Optional[pd.DataFrame]:
        """
        获取历史 K 线数据
        
        Args:
           symbol: 股票代码，如 '000001'
           period: 周期 'daily', 'weekly', 'monthly'
           start_date: YYYYMMDD
           end_date: YYYYMMDD
           adjust: 复权类型
           
        Returns:
            统一格式的 DataFrame，或获取失败时返回 None/Empty DataFrame。
            保证包含基本列: 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change', 'changePct', 'turnover' (如果有)
        """
        if self.use_tushare and self.ts_pro:
            try:
                ts_code = self._to_ts_code(symbol)
                logger.debug(f"[Tushare] Get {period} kline: {ts_code}")
                if period == 'daily':
                    df = self.ts_pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                elif period == 'weekly':
                    df = self.ts_pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
                elif period == 'monthly':
                    df = self.ts_pro.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date)
                else:
                    df = None
                    
                if df is not None and not df.empty:
                    # 统一列名映射
                    res = []
                    for _, row in df.iterrows():
                        t_date = str(row['trade_date'])
                        formatted_date = f"{t_date[:4]}-{t_date[4:6]}-{t_date[6:]}"
                        
                        # Tushare vol->手(100股)，需要*100; amount->千元，需要*1000
                        item = {
                            'date': formatted_date,
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': float(row.get('vol', 0)) * 100,
                            'amount': float(row.get('amount', 0)) * 1000,
                            'change': float(row.get('change', 0)),
                            'changePct': float(row.get('pct_chg', 0)),
                            'turnover': 0.0, # 如果没有换手率，给 0
                        }
                        res.append(item)
                    return pd.DataFrame(res)
            except Exception as e:
                logger.error(f"Tushare 获取历史行情失败: {symbol} {period}, 原因此: {e}")
                import traceback
                traceback.print_exc()
                
        return None


    def get_realtime_quotes(self) -> pd.DataFrame:
        """
        获取全市场部分最新行情数据（优先使用 Tushare 返回日线级别快照）。
        如果在非交易时间，Tushare 会由于最新一天不存在导致空返回，内部可能需要拿到上个交易日快照。
        """
        if self.use_tushare and self.ts_pro:
            try:
                # 尝试获取当天或上一个交易日的行情快照
                # 使用 daily 接口拉取最新日期的横截面
                logger.debug("[Tushare] Get all realtime/daily cross-section data.")
                
                # 获取上一个交易日
                trade_date = self.get_previous_trading_day(days_back=1).replace('-', '')
                
                # Tushare daily 支持按 trade_date 获取所有股票当天切片
                df = self.ts_pro.daily(trade_date=trade_date)
                
                if df is not None and not df.empty:
                    # Tushare daily 里不包含股票名称，需要拉取 basic 信息补充 'name'
                    try:
                        basic_df = self.ts_pro.stock_basic(fields='ts_code,name')
                        if basic_df is not None and not basic_df.empty:
                            df = pd.merge(df, basic_df, on='ts_code', how='left')
                    except Exception as e:
                        logger.warning(f"Tushare 补充股票名称失败: {e}")
                        df['name'] = '' # 如果失败则用空字符串代替

                    # 转换列名以兼容原有的解析代码 expect 格式 (例如 Sina: 代码, 名称, 最新价, 涨跌幅, 成交量, 成交额)
                    # Tushare 字段: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount, name
                    df = df.rename(columns={
                        'ts_code': '代码',
                        'name': '名称',
                        'close': '最新价',
                        'pct_chg': '涨跌幅',
                        'vol': '成交量',
                        'amount': '成交额',
                    })
                    # Tushare vol->手, amount->千元，而在 stock_tasks 中为了兼容将要转换为股和元，或者直接使用
                    # tushare 的 ts_code 也需要拆分，由原有 stock_tasks 处理
                    return df
            except Exception as e:
                logger.error(f"Tushare 获取全量实时/日线切片失败: {e}")
                # 打印详细异常
                import traceback
                traceback.print_exc()
        else:
             logger.error("USE_TUSHARE 未开启或 ts_pro 未初始化")
        
        # 返回空 DataFrame 而不是 None
        return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单一股票的基本信息（利用 Tushare stock_basic 接口）
        """
        if not self.use_tushare or not self.ts_pro:
             return None
             
        try:
            ts_code = self._to_ts_code(symbol)
            # Tushare 字段：ts_code, symbol, name, area, industry, fullname, enname, cnspell, market, exchange, curr_type, list_status, list_date, delist_date, is_hs
            stock_info = self.ts_pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,industry,list_date')
            if stock_info.empty:
                return None
            
            row = stock_info.iloc[0]
            
            # 使用 daily_basic 获取总股本等额外信息
            try:
                trade_date = self.get_previous_trading_day(days_back=1).replace('-', '')
                daily_info = self.ts_pro.daily_basic(ts_code=ts_code, trade_date=trade_date, fields='total_share')
                total_shares_val = daily_info.iloc[0]['total_share'] * 10000 if not daily_info.empty else ''
            except Exception:
                total_shares_val = ''
                
            return {
                'symbol': symbol,
                'name': str(row.get('name', '')),
                'industry': str(row.get('industry', '')),
                'listingDate': str(row.get('list_date', '')),
                'totalShares': total_shares_val,
            }
        except Exception as e:
            logger.error(f"Tushare 获取个股信息失败: {symbol}, 错误: {e}")
            return None

    def get_intraday_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取分时数据"""
        # Tushare 的分时(min)数据门槛较高（需要数千积分），这里暂不实现，或者如果后续允许可以直接写为空
        logger.warning(f"获取分时失败: {symbol}, Tushare 分时数据接口受积分限制/未实现")
        return None

    def get_dragon_tiger_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取龙虎榜详情"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.top_list(trade_date=end_date.replace('-', ''))
            return df
        except Exception as e:
            logger.error(f"Tushare 获取龙虎榜详情失败: {e}")
            return None

    def get_stock_dragon_tiger_detail(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取个股龙虎榜详情"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            ts_code = self._to_ts_code(symbol)
            df = self.ts_pro.top_list(ts_code=ts_code, start_date=start_date.replace('-',''), end_date=end_date.replace('-',''))
            return df
        except Exception as e:
            logger.error(f"Tushare 获取个股龙虎榜详情失败: {symbol}, 错误: {e}")
            return None

    def get_institutional_dragon_tiger(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取机构专用席位龙虎榜"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.top_inst(trade_date=end_date.replace('-', ''))
            return df
        except Exception as e:
            logger.error(f"Tushare 获取机构龙虎榜失败: {e}")
            return None

    def get_dragon_tiger_yyb_rank(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取龙虎榜营业部排行"""
        # Tushare top_list 无统一的 yyb 榜单汇总排行，暂时返回空
        logger.warning("获取龙虎营业部排行失败: Tushare 未直接提供同等汇总接口返回")
        return None

    def get_board_industry_name(self) -> Optional[pd.DataFrame]:
        """获取板块行业行情"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            # tushare index_classify 或 ths_index 等接口存在
            df = self.ts_pro.ths_index() 
            return df
        except Exception as e:
            logger.error(f"Tushare 获取板块行情失败: {e}")
            return None

    def get_sector_fund_flow_rank(self) -> Optional[pd.DataFrame]:
        """获取行业资金流向排行"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            # moneyflow_ths 需要积分
            trade_date = self.get_previous_trading_day(days_back=1).replace('-', '')
            df = self.ts_pro.moneyflow_ths(trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"Tushare 获取行业资金流向失败: {e}")
            return None
            
    def get_limit_up_pool(self, date: str) -> Optional[pd.DataFrame]:
        """获取涨停股池数据"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.limit_list(trade_date=date.replace('-', ''), limit_type='U')
            return df
        except Exception as e:
            logger.error(f"Tushare 获取涨停池失败: {e}, {date}")
            return None

    def get_board_industry_cons(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取板块成分股"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.ths_member(ts_code=symbol)
            return df
        except Exception as e:
            logger.error(f"Tushare 获取板块成分股失败: {symbol}, 错误: {e}")
            return None

    def get_trade_date_hist(self) -> Optional[pd.DataFrame]:
        """获取历史交易日历"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            # Tushare 交易日历
            df = self.ts_pro.trade_cal(exchange='SSE', is_open='1')
            df['trade_date'] = pd.to_datetime(df['cal_date'])
            return df
        except Exception as e:
            logger.error(f"Tushare 获取历史交易日历失败: {e}")
            return None
            
    def get_stock_value(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取股票估值数据"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            ts_code = self._to_ts_code(symbol)
            # Tushare daily_basic 含有 pe, pb, ps, dv 等估值指标
            trade_date = self.get_previous_trading_day(days_back=1).replace('-', '')
            df = self.ts_pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            return df
        except Exception as e:
            logger.error(f"Tushare 获取股票估值失败: {symbol}, 错误: {e}")
            return None

    def get_board_industry_spot(self) -> Optional[pd.DataFrame]:
        """获取板块行情数据(实时)"""
        # Tushare 实时板块指数接口受限，暂时为空
        logger.warning(f"获取板块实时行情失败: 基于 Tushare 目前无免积分实时指数数据返回")
        return None

    def get_stock_news(self) -> Optional[pd.DataFrame]:
        """获取个股新闻"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.news(src='sina')
            return df
        except Exception as e:
            logger.error(f"Tushare 获取个股新闻失败: {e}")
            return None

    def get_board_concept_cons(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取概念板块成分股"""
        if not self.use_tushare or not self.ts_pro: return None
        try:
            df = self.ts_pro.concept_detail(id=symbol)
            return df
        except Exception as e:
            logger.error(f"Tushare 获取概念板块成分股失败: {symbol}, 错误: {e}")
            return None


    def get_previous_trading_day(self, target_date: Optional[str] = None, days_back: int = 1) -> str:
        """
        获取上一个交易日（跳过周末和节假日）
        """
        try:
            if target_date is None:
                current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                from datetime import datetime as dt
                # 兼容传字符串的情况
                if isinstance(target_date, str):
                    current_date = dt.strptime(target_date, '%Y-%m-%d')
                else:
                    current_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

            trade_date_df = self.get_trade_date_hist()
            
            if trade_date_df is None or trade_date_df.empty:
                logger.warning("交易日历数据不足，使用简单日期推算")
                return self._get_previous_date_skip_weekend(current_date, days_back)

            trade_date_df['trade_date'] = pd.to_datetime(trade_date_df['trade_date']).dt.normalize()
            valid_dates = trade_date_df[trade_date_df['trade_date'] < current_date].sort_values('trade_date', ascending=False)

            if len(valid_dates) < days_back:
                logger.warning("交易日历数据不足，使用简单日期推算")
                return self._get_previous_date_skip_weekend(current_date, days_back)

            previous_trading_day = valid_dates.iloc[days_back - 1]['trade_date']
            return previous_trading_day.strftime('%Y-%m-%d')

        except Exception as e:
            logger.warning(f"获取交易日历失败: {e}，使用简单日期推算")
            if target_date is None:
                current_date = datetime.now()
            else:
                from datetime import datetime as dt
                if isinstance(target_date, str):
                    current_date = dt.strptime(target_date, '%Y-%m-%d')
                else:
                    current_date = target_date
            return self._get_previous_date_skip_weekend(current_date, days_back)

    def _get_previous_date_skip_weekend(self, current_date: datetime, days_back: int = 1) -> str:
        """简单的日期推算方法（跳过周末，不考虑节假日）"""
        from datetime import timedelta
        count = 0
        check_date = current_date

        while count < days_back:
            check_date -= timedelta(days=1)
            # 跳过周末（周六=5, 周日=6）
            if check_date.weekday() < 5:  # 周一到周五
                count += 1

        return check_date.strftime('%Y-%m-%d')

    def get_limit_up_stocks(self, date: str) -> List[dict]:
        """获取涨停股数据"""
        try:
            df = self.get_limit_up_pool(date=date.replace("-", ""))
            return df.to_dict('records') if (df is not None and not df.empty) else []
        except Exception as e:
            logger.error(f"获取涨停股失败: {e}")
            return []

    def get_lhb_data(self, date: str) -> List[dict]:
        """获取龙虎榜数据"""
        try:
            formatted_date = date.replace("-", "")
            df = self.get_dragon_tiger_data(start_date=formatted_date, end_date=formatted_date)

            if df is not None and not df.empty:
                logger.debug(f"获取到 {len(df)} 条龙虎榜数据")
                return df.to_dict('records')
            else:
                logger.warning(f"{date} 无龙虎榜数据")
                return []
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            try:
                df = self.get_institutional_dragon_tiger(start_date=formatted_date, end_date=formatted_date)
                if df is not None and not df.empty:
                    logger.debug(f"从机构买卖统计获取到 {len(df)} 条数据")
                    return df.to_dict('records')
                else:
                    logger.warning(f"{date} 无机构买卖统计数据")
                    return []
            except Exception as e2:
                logger.error(f"获取机构买卖统计也失败: {e2}")
                return []

    def get_f10_data_for_stocks(self, stocks: List[dict]) -> Dict[str, dict]:
        """使用stock_value_em接口获取股票估值数据"""
        result = {}
        codes = list(set(s['代码'] for s in stocks))

        for code in codes:
            try:
                df = self.get_stock_value(symbol=code)

                if df is not None and not df.empty:
                    latest_data = df.iloc[-1]
                    result[code] = {
                        'pe': float(latest_data.get('PE(TTM)', 0)) if pd.notna(latest_data.get('PE(TTM)')) else None,
                        'pb': float(latest_data.get('市净率', 0)) if pd.notna(latest_data.get('市净率')) else None,
                        'pe_static': float(latest_data.get('PE(静)', 0)) if pd.notna(latest_data.get('PE(静)')) else None,
                        'peg': float(latest_data.get('PEG值', 0)) if pd.notna(latest_data.get('PEG值')) else None,
                        'market_cap': float(latest_data.get('总市值', 0)) if pd.notna(latest_data.get('总市值')) else None,
                        'float_market_cap': float(latest_data.get('流通市值', 0)) if pd.notna(latest_data.get('流通市值')) else None,
                        'ps_ratio': float(latest_data.get('市销率', 0)) if pd.notna(latest_data.get('市销率')) else None,
                        'pcf_ratio': float(latest_data.get('市现率', 0)) if pd.notna(latest_data.get('市现率')) else None,
                        'data_date': latest_data.get('数据日期', ''),
                        'close_price': float(latest_data.get('当日收盘价', 0)) if pd.notna(latest_data.get('当日收盘价')) else None
                    }
                else:
                    logger.warning(f"{code} 估值数据为空")
                    result[code] = {
                        'pe': None, 'pb': None, 'pe_static': None, 'peg': None,
                        'market_cap': None, 'float_market_cap': None,
                        'ps_ratio': None, 'pcf_ratio': None,
                        'data_date': '', 'close_price': None
                    }
            except Exception as e:
                logger.error(f"获取 {code} 估值数据失败: {e}")
                result[code] = {
                    'pe': None, 'pb': None, 'pe_static': None, 'peg': None,
                    'market_cap': None, 'float_market_cap': None,
                    'ps_ratio': None, 'pcf_ratio': None,
                    'data_date': '', 'close_price': None
                }
        return result

    # ============================================================
    # 东财批量实时行情接口 (新增)
    # ============================================================
    
    def get_batch_realtime_eastmoney(self, symbols: List[str]) -> Dict[str, dict]:
        """
        东财批量实时行情接口
        
        支持一次查询最多100只股票，返回实时价格、涨跌幅、成交量等
        
        Args:
            symbols: 股票代码列表，如 ['000001', '600000']
            
        Returns:
            {symbol: {price, changePct, volume, ...}}
        """
        if not symbols:
            return {}
        
        # 东财限制一次最多100只
        batch_size = 100
        all_results = {}
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_result = self._fetch_eastmoney_batch(batch)
            all_results.update(batch_result)
            
            # 批次间短暂延时，避免触发限流
            if i + batch_size < len(symbols):
                time.sleep(0.1)
        
        return all_results
    
    def _fetch_eastmoney_batch(self, symbols: List[str]) -> Dict[str, dict]:
        """单次获取东财批量数据"""
        # 转换代码格式
        secids = [self._to_eastmoney_code(s) for s in symbols]
        secids_str = ','.join(secids)
        
        # 关键字段: 
        # f12=代码, f13=市场, f14=名称, f2=最新价, f3=涨跌幅, f4=涨跌额
        # f5=成交量(手), f6=成交额, f15=最高, f16=最低, f17=开盘, f18=昨收
        # f20=总市值, f21=流通市值
        fields = "f12,f13,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18,f20,f21"
        
        url = f"{self._eastmoney_base_url}/ulist.np/get"
        params = {
            "secids": secids_str,
            "fields": fields,
            "fltt": 2,  # 2位小数
            "invt": 2,  # JSON格式
        }
        
        try:
            response = self._session.get(url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or 'diff' not in data['data']:
                logger.warning("东财批量接口返回数据格式异常")
                return {}
            
            results = {}
            for item in data['data']['diff']:
                # 解析东财数据格式
                symbol = item.get('f12')
                if not symbol:
                    continue
                
                # 东财成交量是手，需要转换为股 (*100)
                volume = item.get('f5', 0)
                if volume:
                    volume = volume * 100
                
                results[symbol] = {
                    'symbol': symbol,
                    'name': item.get('f14', ''),
                    'price': item.get('f2'),  # 最新价
                    'changePct': item.get('f3'),  # 涨跌幅%
                    'change': item.get('f4'),  # 涨跌额
                    'volume': volume,  # 成交量(股)
                    'amount': item.get('f6'),  # 成交额(元)
                    'high': item.get('f15'),  # 最高
                    'low': item.get('f16'),  # 最低
                    'open': item.get('f17'),  # 开盘
                    'preClose': item.get('f18'),  # 昨收
                    'marketCap': item.get('f20'),  # 总市值
                    'floatMarketCap': item.get('f21'),  # 流通市值
                    'source': 'eastmoney',
                    'timestamp': datetime.now().isoformat()
                }
            
            return results
            
        except Exception as e:
            logger.error(f"东财批量接口请求失败: {e}")
            return {}
    
    def get_realtime_eastmoney_single(self, symbol: str) -> Optional[dict]:
        """
        东财单股实时行情（带完整字段）
        
        相比 get_stock_price_realtime，返回更完整的数据
        """
        batch_result = self._fetch_eastmoney_batch([symbol])
        return batch_result.get(symbol)
    
    # ============================================================
    # 雪球接口优化 (增强备用能力 + Token 管理)
    # ============================================================
    
    def _refresh_xueqiu_token(self) -> bool:
        """
        刷新雪球 Token
        
        雪球接口需要有效的 xq_a_token，通过访问首页获取
        返回 True 表示成功获取/刷新 token
        """
        try:
            # 先清除旧的 cookie，避免干扰
            self._session.cookies.clear(domain='.xueqiu.com')
            
            # 访问雪球首页获取新 token
            # 需要设置完整的请求头模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            resp = self._session.get(
                "https://xueqiu.com",
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            
            # 检查是否获取到 token
            cookies = self._session.cookies.get_dict(domain='.xueqiu.com')
            xq_token = cookies.get('xq_a_token')
            
            if xq_token:
                logger.info(f"雪球 Token 刷新成功: {xq_token[:10]}...")
                self._xueqiu_token = xq_token
                self._xueqiu_token_time = time.time()
                return True
            else:
                # 有些情况下 token 在响应头 Set-Cookie 中
                if 'set-cookie' in resp.headers:
                    set_cookie = resp.headers.get('set-cookie', '')
                    if 'xq_a_token' in set_cookie:
                        logger.info("雪球 Token 从响应头获取成功")
                        self._xueqiu_token = "present"  # 标记存在
                        self._xueqiu_token_time = time.time()
                        return True
                
                logger.warning("雪球 Token 刷新失败：响应中未找到 xq_a_token")
                return False
                
        except Exception as e:
            logger.error(f"刷新雪球 Token 异常: {e}")
            return False
    
    def _is_xueqiu_token_valid(self) -> bool:
        """检查当前 Token 是否有效"""
        # 如果没有 token，无效
        if not hasattr(self, '_xueqiu_token') or not self._xueqiu_token:
            return False
        
        # 如果 token 超过 30 分钟，认为可能过期（雪球的 token 通常持续较久，但为了保险）
        if hasattr(self, '_xueqiu_token_time'):
            elapsed = time.time() - self._xueqiu_token_time
            if elapsed > 1800:  # 30 分钟
                logger.debug(f"雪球 Token 已使用 {elapsed:.0f} 秒，尝试刷新")
                return False
        
        return True
    
    def _ensure_xueqiu_token(self, force_refresh: bool = False) -> bool:
        """
        确保雪球 Token 有效
        
        Args:
            force_refresh: 强制刷新 token
            
        Returns:
            True: Token 有效
            False: 获取 Token 失败
        """
        if not force_refresh and self._is_xueqiu_token_valid():
            return True
        
        # 最多重试 3 次
        for attempt in range(3):
            if self._refresh_xueqiu_token():
                return True
            time.sleep(0.5 * (attempt + 1))
        
        logger.error("雪球 Token 获取失败，无法访问雪球接口")
        return False
    
    def _handle_xueqiu_error(self, response) -> bool:
        """
        处理雪球接口错误，检测 token 失效
        
        Returns:
            True: 需要重试（token 已刷新）
            False: 其他错误
        """
        try:
            data = response.json()
            # 检查常见的 token 失效错误码
            if 'error_code' in data:
                error_code = data.get('error_code')
                if error_code in [401, 403, -1, '401', '403']:
                    logger.warning(f"雪球 Token 可能失效，错误码: {error_code}")
                    # 尝试刷新 token
                    if self._ensure_xueqiu_token(force_refresh=True):
                        return True
            
            # 检查错误信息中的关键词
            error_desc = str(data.get('error_description', '')).lower()
            if any(k in error_desc for k in ['token', 'unauthorized', '登录', '权限']):
                logger.warning("雪球接口返回 token 相关错误，尝试刷新")
                if self._ensure_xueqiu_token(force_refresh=True):
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def get_batch_realtime_xueqiu(self, symbols: List[str]) -> Dict[str, dict]:
        """
        雪球批量实时行情接口（备用数据源）
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            {symbol: {price, changePct, ...}}
        """
        if not symbols:
            return {}
        
        # 确保 token 有效
        if not self._ensure_xueqiu_token():
            logger.error("雪球 Token 无效，无法获取数据")
            return {}
        
        # 雪球限制一次最多30只
        batch_size = 30
        all_results = {}
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_result = self._fetch_xueqiu_batch(batch)
            all_results.update(batch_result)
            
            if i + batch_size < len(symbols):
                time.sleep(0.2)  # 雪球限流更严格
        
        return all_results
    
    def _fetch_xueqiu_batch(self, symbols: List[str], retry_on_auth_error: bool = True) -> Dict[str, dict]:
        """
        单次获取雪球批量数据
        
        Args:
            symbols: 股票代码列表
            retry_on_auth_error: 认证错误时是否重试
        """
        # 转换代码格式
        symbol_params = ','.join([self._to_xueqiu_code(s) for s in symbols])
        
        url = f"{self._xueqiu_base_url}/batch/quote.json"
        params = {
            "symbol": symbol_params,
        }
        headers = {
            'Referer': 'https://xueqiu.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        
        try:
            response = self._session.get(url, params=params, headers=headers, timeout=10)
            
            # 检查是否需要刷新 token 后重试
            if retry_on_auth_error and (response.status_code == 401 or response.status_code == 403):
                logger.warning(f"雪球接口返回 {response.status_code}，尝试刷新 token 后重试")
                if self._ensure_xueqiu_token(force_refresh=True):
                    return self._fetch_xueqiu_batch(symbols, retry_on_auth_error=False)
            
            # 检查响应内容中的错误
            if retry_on_auth_error and self._handle_xueqiu_error(response):
                return self._fetch_xueqiu_batch(symbols, retry_on_auth_error=False)
            
            response.raise_for_status()
            
            data = response.json()
            
            # 检查数据结构
            if 'data' not in data or 'items' not in data.get('data', {}):
                # 可能是错误响应
                if 'error_code' in data:
                    logger.warning(f"雪球接口返回错误: {data}")
                return {}
            
            results = {}
            for item in data['data']['items']:
                quote = item.get('quote', {})
                symbol_raw = quote.get('symbol', '')
                symbol = symbol_raw.replace('SH', '').replace('SZ', '').replace('BJ', '')
                
                if not symbol:
                    continue
                
                # 雪球涨跌幅是百分比值，如 2.35 表示 2.35%
                percent = quote.get('percent', 0)
                current = quote.get('current', 0)
                
                results[symbol] = {
                    'symbol': symbol,
                    'name': quote.get('name', ''),
                    'price': current,
                    'changePct': percent,  # 已经是%
                    'change': quote.get('change', 0),
                    'volume': quote.get('volume', 0),  # 雪球返回股数
                    'amount': quote.get('amount', 0),
                    'high': quote.get('high', 0),
                    'low': quote.get('low', 0),
                    'open': quote.get('open', 0),
                    'preClose': quote.get('last_close', 0),
                    'marketCap': quote.get('market_capital', 0),
                    'floatMarketCap': quote.get('float_market_capital', 0),
                    'pe': quote.get('pe_ttm', 0),
                    'pb': quote.get('pb', 0),
                    'source': 'xueqiu',
                    'timestamp': datetime.now().isoformat()
                }
            
            return results
            
        except Exception as e:
            logger.error(f"雪球批量接口请求失败: {e}")
            return {}
    
    def get_realtime_xueqiu_single(self, symbol: str) -> Optional[dict]:
        """
        雪球单股实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票行情数据或 None
        """
        batch_result = self._fetch_xueqiu_batch([symbol])
        return batch_result.get(symbol)
    
    # ============================================================
    # 统一实时行情接口（带自动降级）
    # ============================================================
    
    def get_realtime_quotes_unified(
        self, 
        symbols: List[str],
        prefer_source: str = 'eastmoney'
    ) -> Dict[str, dict]:
        """
        统一实时行情获取接口（主入口）
        
        自动处理主备数据源切换:
        1. 优先使用东财批量接口
        2. 东财失败时自动降级到雪球
        3. 都失败时返回空字典
        
        Args:
            symbols: 股票代码列表
            prefer_source: 优先数据源 ('eastmoney' | 'xueqiu')
            
        Returns:
            {symbol: {price, changePct, volume, ..., source, degraded}}
        """
        if not symbols:
            return {}
        
        # 去重并保持顺序
        unique_symbols = list(dict.fromkeys(symbols))
        
        if prefer_source == 'eastmoney':
            # 先尝试东财
            results = self.get_batch_realtime_eastmoney(unique_symbols)
            if results:
                # 标记数据来源
                for symbol in results:
                    results[symbol]['degraded'] = False
                
                # 检查是否有缺失的股票
                missing = [s for s in unique_symbols if s not in results]
                if missing:
                    logger.warning(f"东财返回缺失 {len(missing)} 只股票，尝试雪球补全")
                    # 尝试用雪球补全
                    xueqiu_results = self.get_batch_realtime_xueqiu(missing)
                    for symbol, data in xueqiu_results.items():
                        data['degraded'] = True
                        results[symbol] = data
                
                return results
            
            # 东财完全失败，降级到雪球
            logger.warning("东财接口失败，降级到雪球")
            results = self.get_batch_realtime_xueqiu(unique_symbols)
            for data in results.values():
                data['degraded'] = True
            return results
        
        else:
            # 优先雪球
            results = self.get_batch_realtime_xueqiu(unique_symbols)
            if results:
                for data in results.values():
                    data['degraded'] = False
                return results
            
            # 雪球失败，回退东财
            logger.warning("雪球接口失败，回退到东财")
            results = self.get_batch_realtime_eastmoney(unique_symbols)
            for data in results.values():
                data['degraded'] = True
            return results

    def get_stock_price_realtime(self, stock_code: str, retry_count: int=3) -> Optional[dict]:
        """东方财富实时数据API"""
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        if stock_code.startswith('6'):
            market = '1'
        else:
            market = '0'

        url = f"https://push2.eastmoney.com/api/qt/stock/get?ut=fa5fd1943c7b386f172d6893dbfba10b&invt=2&fltt=2&fields=f43,f46,f44,f45,f47,f48,f170&secid={market}.{stock_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        for attempt in range(retry_count):
            try:
                response = requests.get(url, headers=headers, timeout=10, verify=False)
                if response.status_code != 200:
                    if attempt < retry_count - 1:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    return None
                
                result = response.json()
                if 'data' not in result or result['data'] is None:
                    return None
                
                data = result['data']
                if data.get('f43') is None:
                    return None
                    
                return {
                    'open': data.get('f46'),
                    'current': data.get('f43'),
                    'high': data.get('f44'),
                    'low': data.get('f45'),
                    'volume': data.get('f47'),
                    'amount': data.get('f48'),
                    'change_rate': data.get('f170')
                }
            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return None
        return None

    def get_intraday_from_eastmoney(self, stock_code: str) -> Optional[List[Dict]]:
        """从东方财富获取分时数据"""
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        if stock_code.startswith('6'):
            market = '1'
        else:
            market = '0'
        
        url = f"https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market}.{stock_code}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': '*/*',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            if response.status_code != 200:
                return None
            
            result = response.json()
            if 'data' not in result or not result.get('data'):
                return None
            
            data = result['data']
            trends = data.get('trends', [])
            
            if not trends:
                return None
            
            intraday_data = []
            for line in trends:
                parts = line.split(',')
                if len(parts) >= 8:
                    intraday_data.append({
                        'time': parts[0],
                        'price': float(parts[2]) if parts[2] else 0,
                        'volume': float(parts[5]) if parts[5] else 0,
                        'avgPrice': float(parts[7]) if parts[7] else 0,
                        'change': float(parts[3]) if parts[3] else 0
                    })
            
            return intraday_data
        except Exception as e:
            logger.error(f"东方财富分时数据获取失败: {stock_code}, {e}")
            return None

    def get_intraday_from_sina(self, stock_code: str) -> Optional[List[Dict]]:
        """从新浪财经获取分时数据（使用分钟K线接口）"""
        import requests
        import urllib3
        import re
        import json
        from datetime import datetime
        urllib3.disable_warnings()
        
        # 确定市场前缀
        if stock_code.startswith('6'):
            market = 'sh'
        else:
            market = 'sz'
        
        # 获取5分钟K线数据
        url = 'https://quotes.sina.cn/cn/api/json.php/CN_MarketDataService.getKLineData'
        params = {
            'symbol': f'{market}{stock_code}',
            'scale': '5',  # 5分钟K线
            'ma': 'no'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/',
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
            if response.status_code != 200:
                return None
            
            # 解析返回数据
            content = response.text
            
            # 直接解析 JSON 数组
            if content.startswith('['):
                klines = json.loads(content)
            else:
                return None
            
            if not klines:
                return None
            
            # 转换为分时数据格式（获取最新的数据，不限制日期）
            intraday_data = []
            
            for kline in klines:
                day = kline.get('day', '')
                if not day:
                    continue
                    
                intraday_data.append({
                    'time': day,  # 格式: "2026-03-07 09:35:00"
                    'price': float(kline.get('close', 0)),
                    'volume': float(kline.get('volume', 0)),
                    'avgPrice': float(kline.get('close', 0)),  # 近似
                    'change': 0
                })
            
            # 返回最新的48条数据（约4小时的交易时间）
            return intraday_data[-48:] if len(intraday_data) > 48 else intraday_data
            
        except Exception as e:
            logger.error(f"新浪财经分时数据获取失败: {stock_code}, {e}")
            return None


def safe_parse_json(content: str):
    """安全解析 JSON 字符串"""
    import json
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if "None" in content:
            content = content.replace("None", "null")
        try:
            return json.loads(content)
        except:
            return [{"error": "parse_failed", "raw": content[:200]}]
    return []

# 全局单例
stock_tool = StockTool()
