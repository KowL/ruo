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

import akshare as ak
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
        self.ts_pro = None

        if self.use_tushare and ts:
            try:
                self.ts_pro = ts.pro_api(settings.TUSHARE_TOKEN)
                # Tushare pro_api custom http config if required
                if hasattr(self.ts_pro, '_DataApi__http_url'):
                    self.ts_pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
            except Exception as e:
                logger.error(f"Tushare pro api init failed: {e}")
                self.use_tushare = False

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
                logger.warning(f"Tushare 获取历史行情失败: {symbol} {period}, 原因此: {e}, 即将回退到 Akshare")
        
        # 回退至 akshare
        try:
            logger.debug(f"[AkShare] Get {period} kline: {symbol}")
            period_map = {'daily': 'daily', 'weekly': 'weekly', 'monthly': 'monthly'}
            ak_period = period_map.get(period, 'daily')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            
            if df is not None and not df.empty:
                res = []
                for _, row in df.iterrows():
                    d_str = row['日期'].strftime('%Y-%m-%d') if hasattr(row['日期'], 'strftime') else str(row['日期'])
                    # AkShare volume 本身是股，amount是元
                    item = {
                        'date': d_str,
                        'open': float(row['开盘']),
                        'high': float(row['最高']),
                        'low': float(row['最低']),
                        'close': float(row['收盘']),
                        'volume': float(row['成交量']),
                        'amount': float(row['成交额']) if '成交额' in row.index else 0.0,
                        'change': float(row['涨跌额']) if '涨跌额' in row.index else 0.0,
                        'changePct': float(row['涨跌幅']) if '涨跌幅' in row.index else 0.0,
                        'turnover': float(row['换手率']) if '换手率' in row.index else 0.0,
                    }
                    res.append(item)
                return pd.DataFrame(res)
            return None
        except Exception as e:
            logger.error(f"AkShare 获取历史行情也失败: {symbol} {period}, 错误: {e}")
            return None


    def get_realtime_quotes(self) -> Optional[pd.DataFrame]:
        """
        获取全市场最新实时行情。
        因为实时数据 Tushare 接口有一定的延迟或积分限制，通常 AkShare `stock_zh_a_spot_em` 足够稳定。
        （默认使用 Akshare 提供实时快照）
        """
        try:
            # 内部优先使用东财快照获取全量最新行情
            logger.debug("[AkShare] Get all realtime spot.")
            df = ak.stock_zh_a_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取全量实时行情失败: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单一股票的基本信息（利用 akshare，因为其返回的信息比较丰富易用）
        """
        try:
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            if stock_info.empty:
                return None
            
            info_dict = {}
            for _, row in stock_info.iterrows():
                info_dict[row['item']] = row['value']
                
            return {
                'symbol': symbol,
                'name': info_dict.get('股票简称', ''),
                'industry': info_dict.get('行业', ''),
                'listingDate': info_dict.get('上市时间', ''),
                'totalShares': info_dict.get('总股本', ''),
            }
        except Exception as e:
            logger.error(f"AkShare 获取个股信息失败: {symbol}, 错误: {e}")
            return None

    def get_intraday_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取分时数据"""
        try:
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1', adjust='')
            return df
        except Exception as e:
            logger.error(f"AkShare 获取分时失败: {symbol}, 错误: {e}")
            return None

    def get_dragon_tiger_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取龙虎榜详情"""
        try:
            df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取龙虎榜详情失败: {e}")
            return None

    def get_stock_dragon_tiger_detail(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取个股龙虎榜详情"""
        try:
            df = ak.stock_lhb_stock_detail_em(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol
            )
            return df
        except Exception as e:
            logger.error(f"AkShare 获取个股龙虎榜详情失败: {symbol}, 错误: {e}")
            return None

    def get_institutional_dragon_tiger(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取机构专用席位龙虎榜"""
        try:
            df = ak.stock_lhb_jgmmtj_em(start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取机构龙虎榜失败: {e}")
            return None

    def get_dragon_tiger_yyb_rank(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取龙虎榜营业部排行"""
        try:
            df = ak.stock_lhb_yybph_em(start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取龙虎营业部排行失败: {e}")
            return None

    def get_board_industry_name(self) -> Optional[pd.DataFrame]:
        """获取板块行业行情"""
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            logger.error(f"AkShare 获取板块行情失败: {e}")
            return None

    def get_sector_fund_flow_rank(self) -> Optional[pd.DataFrame]:
        """获取行业资金流向排行"""
        try:
            df = ak.stock_sector_fund_flow_rank()
            return df
        except Exception as e:
            logger.error(f"AkShare 获取行业资金流向失败: {e}")
            return None
            
    def get_limit_up_pool(self, date: str) -> Optional[pd.DataFrame]:
        """获取涨停股池数据"""
        try:
            df = ak.stock_zt_pool_em(date=date)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取涨停池失败: {e}, {date}")
            return None

    def get_board_industry_cons(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取板块成分股"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取板块成分股失败: {symbol}, 错误: {e}")
            return None

    def get_trade_date_hist(self) -> Optional[pd.DataFrame]:
        """获取历史交易日历"""
        try:
            df = ak.tool_trade_date_hist_sina()
            return df
        except Exception as e:
            logger.error(f"AkShare 获取历史交易日历失败: {e}")
            return None
            
    def get_stock_value(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取股票估值数据"""
        try:
            df = ak.stock_value_em(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取股票估值失败: {symbol}, 错误: {e}")
            return None

    def get_board_industry_spot(self) -> Optional[pd.DataFrame]:
        """获取板块行情数据(实时)"""
        try:
            df = ak.stock_board_industry_spot_em()
            return df
        except Exception as e:
            logger.error(f"AkShare 获取板块实时行情失败: {e}")
            return None

    def get_stock_news(self) -> Optional[pd.DataFrame]:
        """获取个股新闻"""
        try:
            df = ak.stock_news_em()
            return df
        except Exception as e:
            logger.error(f"AkShare 获取个股新闻失败: {e}")
            return None

    def get_board_concept_cons(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取概念板块成分股"""
        try:
            df = ak.stock_board_concept_cons_em(symbol=symbol)
            return df
        except Exception as e:
            logger.error(f"AkShare 获取概念板块成分股失败: {symbol}, 错误: {e}")
            return None


    def get_previous_trading_day(self, target_date: Optional[str] = None, days_back: int = 1) -> str:
        """
        获取上一个交易日（跳过周末和节假日）
        """
        try:
            if target_date is None:
                current_date = datetime.now()
            else:
                from datetime import datetime as dt
                # 兼容传字符串的情况
                if isinstance(target_date, str):
                    current_date = dt.strptime(target_date, '%Y-%m-%d')
                else:
                    current_date = target_date

            trade_date_df = self.get_trade_date_hist()
            
            if trade_date_df is None or trade_date_df.empty:
                logger.warning("交易日历数据不足，使用简单日期推算")
                return self._get_previous_date_skip_weekend(current_date, days_back)

            trade_date_df['trade_date'] = pd.to_datetime(trade_date_df['trade_date'])
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
