"""
通用行情数据工具 - StockTool

统一封装所有获取股票外部数据源（Tushare/AkShare/EastMoney等）的方法。
按配置优先级回退：优先 Tushare -> 回退 AkShare。
"""
import logging
import time
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

try:
    import tushare as ts
except ImportError:
    ts = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class StockTool:
    """内部行情调用工具，封装回退降级逻辑"""

    def __init__(self):
        self.use_tushare = settings.USE_TUSHARE and bool(settings.TUSHARE_TOKEN)
        self.ts_pro = ts.pro_api(settings.TUSHARE_TOKEN)
        self.ts_pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'

    def _to_ts_code(self, symbol: str) -> str:
        """转换代码到 Tushare 格式"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"{symbol}.SZ"
        elif symbol.startswith('4') or symbol.startswith('8') or symbol.startswith('9'):
            return f"{symbol}.BJ"
        return symbol

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
