"""
Stock Data Service - AKShare Integration
Provides stock data including limit-up stocks, hot stocks, and sector data
"""

import akshare as ak
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
import random
import time
import requests
from requests.adapters import HTTPAdapter
from collections import defaultdict


# 禁用代理配置
def _disable_proxy():
    """清除所有代理环境变量"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        os.environ.pop(var, None)
        if var in os.environ:
            del os.environ[var]
    # 设置空代理环境变量防止继承
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'


# 初始化时禁用代理
_disable_proxy()

# 禁用 urllib 的代理支持
import urllib.request
urllib.request._opener = None  # Reset opener

# 配置 requests 禁用代理
import requests
session = requests.Session()
session.trust_env = False
original_session = requests.sessions.Session
def no_proxy_session():
    s = original_session()
    s.trust_env = False
    return s
requests.Session = no_proxy_session


class FileCache:
    """本地文件缓存"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str, max_age_seconds: int = 300) -> Optional[any]:
        """获取缓存数据"""
        filepath = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(filepath):
            return None
        
        # 检查是否过期
        mtime = os.path.getmtime(filepath)
        age = time.time() - mtime
        if age > max_age_seconds:
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def set(self, key: str, data: any):
        """设置缓存"""
        filepath = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Cache write error: {e}")


class StockDataService:
    """Stock data service using AKShare"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes memory cache
        self.file_cache = FileCache("cache")
        
        # 连板天梯缓存
        self.ladder_cache = None
        self.ladder_cache_time = None
        
        # 备用数据源映射
        self.fallback_sources = {
            "stock_board_industry_name_em": self._get_industry_fallback,
            "stock_zh_a_spot_em": self._get_spot_fallback,
        }
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data from memory"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.cache_timeout:
                return data
        return None
    
    def _set_cache(self, key: str, data: any):
        """Set memory cache with timestamp"""
        self.cache[key] = (data, datetime.now())
        # 同时写入文件缓存
        self.file_cache.set(key, data)
    
    def _get_file_cached(self, key: str, max_age: int = 300) -> Optional[any]:
        """Get data from file cache"""
        return self.file_cache.get(key, max_age_seconds=max_age)
    
    def _get_industry_fallback(self) -> List[Dict]:
        """行业板块备用数据源 - 使用本地缓存或返回空"""
        # 尝试读取文件缓存
        cached = self.file_cache.get("sectors", max_age_seconds=3600)  # 1小时过期
        if cached:
            return cached
        
        # 返回空列表（前端可以显示"暂无数据"）
        return []
    
    def _get_spot_fallback(self) -> pd.DataFrame:
        """实时行情备用数据源"""
        cached = self.file_cache.get("market_all", max_age_seconds=3600)
        if cached:
            # 转换为 DataFrame
            if cached:
                return pd.DataFrame(cached)
        return pd.DataFrame()
    
    def _calculate_limit_up_ladder(self, df: pd.DataFrame) -> List[Dict]:
        """
        计算连板天梯
        根据涨停数据分析每只股票的连板数
        """
        if df is None or df.empty:
            return []
        
        stocks = []
        for _, row in df.iterrows():
            # 获取连板数 - 优先使用数据中的连板数字段
            limit_count = 1
            if '连板数' in row:
                try:
                    limit_count = int(row.get('连板数', 1))
                except:
                    limit_count = 1
            elif '涨停天数' in row:
                try:
                    limit_count = int(row.get('涨停天数', 1))
                except:
                    limit_count = 1
            
            stock = {
                "code": str(row.get("代码", "")),
                "name": str(row.get("名称", "")),
                "price": float(row.get("最新价", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "turnover": float(row.get("成交额", 0)),
                "reason": str(row.get("涨停原因", "")).strip(),
                "open_count": int(row.get("开板次数", 0)),
                "first_time": str(row.get("首次封板时间", "")),
                "last_time": str(row.get("最后封板时间", "")),
                "limit_up_count": limit_count,  # 连板数
                "seal_amount": float(row.get("封单金额", 0)) * 10000 if row.get("封单金额", 0) else 0,
                "industry": str(row.get("所属行业", "")).strip()
            }
            stocks.append(stock)
        
        # 按连板数降序，然后按封单金额降序
        stocks.sort(key=lambda x: (-x["limit_up_count"], -x["seal_amount"], -x["turnover"]))
        return stocks
    
    def get_limit_up_stocks(self, date: str = None) -> List[Dict]:
        """
        Get stocks with consecutive limit-ups (连板天梯)
        返回按连板数分层的涨停股票列表
        Args:
            date: optional date string in YYYY-MM-DD format
        """
        # 如果指定了日期，使用不同的缓存key
        if date:
            cache_key = f"limit_up_{date.replace('-', '')}"
        else:
            cache_key = "limit_up"
        
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # 检查文件缓存
        file_cached = self._get_file_cached(cache_key, max_age=600)
        if file_cached:
            self._set_cache(cache_key, file_cached)
            return file_cached
        
        try:
            # Get limit-up stocks for specified date or today
            _disable_proxy()
            if date:
                target_date = date.replace('-', '')
            else:
                target_date = datetime.now().strftime("%Y%m%d")
            
            df = ak.stock_zt_pool_em(date=target_date)
            
            if df is None or df.empty:
                return file_cached if file_cached else []
            
            # 处理连板天梯数据
            stocks = self._calculate_limit_up_ladder(df)
            
            self._set_cache(cache_key, stocks)
            return stocks
            
        except Exception as e:
            print(f"Error fetching limit-up stocks: {e}")
            # 返回文件缓存
            return file_cached if file_cached else []
    
    def get_limit_up_ladder(self, date: str = None) -> Dict:
        """
        获取连板天梯分层数据
        按连板数分组展示
        Args:
            date: optional date string in YYYY-MM-DD format
        """
        # 如果指定了日期，使用不同的缓存key
        if date:
            cache_key = f"limit_up_ladder_{date}"
        else:
            cache_key = "limit_up_ladder"
        
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        stocks = self.get_limit_up_stocks(date=date)
        if not stocks:
            return {"levels": [], "total": 0}
        
        # 按连板数分组
        levels = defaultdict(list)
        for stock in stocks:
            count = stock.get("limit_up_count", 1)
            levels[count].append(stock)
        
        # 构建天梯层级（从高到低）
        sorted_levels = sorted(levels.keys(), reverse=True)
        result = []
        for level in sorted_levels:
            level_stocks = levels[level]
            result.append({
                "level": level,
                "name": f"{level}连板" if level >= 2 else "首板",
                "count": len(level_stocks),
                "stocks": level_stocks
            })
        
        ladder_data = {
            "levels": result,
            "total": len(stocks),
            "max_level": max(sorted_levels) if sorted_levels else 0,
            "update_time": datetime.now().isoformat()
        }
        
        self._set_cache(cache_key, ladder_data)
        return ladder_data
    
    def get_hot_stocks(self) -> Dict:
        """
        Get hot stocks from multiple platforms (股票热榜)
        """
        cache_key = "hot_stocks"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # 检查文件缓存
        file_cached = self._get_file_cached(cache_key, max_age=600)
        if file_cached:
            self._set_cache(cache_key, file_cached)
            return file_cached
        
        result = {
            "eastmoney": [],  # 东方财富
            "tonghuashun": [],  # 同花顺
            "xueqiu": [],  # 雪球
            "sectors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            _disable_proxy()
            # Get EastMoney hot stocks
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                for _, row in df.head(10).iterrows():
                    result["eastmoney"].append({
                        "name": str(row.get("板块名称", "")),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "lead_stock": str(row.get("领涨股票", "")),
                        "lead_change": float(row.get("涨跌幅.1", 0))
                    })
        except Exception as e:
            print(f"Error fetching EastMoney data: {e}")
        
        try:
            _disable_proxy()
            # Get sector hot list
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                for _, row in df.head(15).iterrows():
                    result["sectors"].append({
                        "name": str(row.get("板块名称", "")),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "turnover": float(row.get("成交额", 0))
                    })
        except Exception as e:
            print(f"Error fetching sector data: {e}")
        
        self._set_cache(cache_key, result)
        return result
    
    def get_sector_data(self) -> List[Dict]:
        """Get sector/industry data"""
        cache_key = "sectors"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # 检查文件缓存
        file_cached = self._get_file_cached(cache_key, max_age=600)
        if file_cached:
            self._set_cache(cache_key, file_cached)
            return file_cached
        
        # 尝试直接 API 调用（备用域名）
        try:
            _disable_proxy()
            url = 'https://push2delay.eastmoney.com/api/qt/clist/get'
            params = {
                'pn': 1, 'pz': 500, 'po': 1, 'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2, 'invt': 2, 'fid': 'f12',
                'fs': 'm:90+t:2+f:!50',
                'fields': 'f2,f3,f4,f8,f12,f14,f15,f16,f17,f18,f20,f21,f24,f25,f22,f33,f11,f62,f128,f124,f107,f104,f105,f136'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/',
            }
            
            session = requests.Session()
            session.trust_env = False
            resp = session.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            
            if data.get('rc') == 0 and 'data' in data and 'diff' in data['data']:
                sectors = []
                for item in data['data']['diff']:
                    sector = {
                        "name": item.get('f14', ''),
                        "change_pct": round(item.get('f3', 0), 2),
                        "turnover": item.get('f20', 0),
                        "stock_count": item.get('f107', 0)
                    }
                    sectors.append(sector)
                
                sectors.sort(key=lambda x: -x["change_pct"])
                self._set_cache(cache_key, sectors)
                return sectors
                
        except Exception as e:
            print(f"Error fetching sector data from backup API: {e}")
        
        # 回退到 akshare
        try:
            _disable_proxy()
            df = ak.stock_board_industry_name_em()
            if df is None or df.empty:
                return self._get_industry_fallback()
            
            sectors = []
            for _, row in df.iterrows():
                sector = {
                    "name": str(row.get("板块名称", "")),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "turnover": float(row.get("成交额", 0)),
                    "stock_count": int(row.get("股票数量", 0))
                }
                sectors.append(sector)
            
            sectors.sort(key=lambda x: -x["change_pct"])
            self._set_cache(cache_key, sectors)
            return sectors
            
        except Exception as e:
            print(f"Error fetching sector data: {e}")
            return self._get_industry_fallback()
    
    def get_concept_data(self) -> List[Dict]:
        """
        Get concept/theme data (题材库)
        使用 Tushare 同花顺指数数据
        """
        cache_key = "concepts"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # 检查文件缓存
        file_cached = self._get_file_cached(cache_key, max_age=600)
        if file_cached:
            self._set_cache(cache_key, file_cached)
            return file_cached
        
        # 尝试使用 Tushare 同花顺指数数据
        try:
            _disable_proxy()
            import tushare as ts
            pro = ts.pro_api()
            
            # 获取同花顺指数（概念板块）
            df = pro.ths_index(market='BJ')
            
            if df is None or df.empty:
                # 尝试其他市场
                for market in ['SH', 'SZ']:
                    df = pro.ths_index(market=market)
                    if df is not None and not df.empty:
                        break
            
            if df is not None and not df.empty:
                concepts = []
                for _, row in df.iterrows():
                    concept = {
                        "name": str(row.get("name", "")),
                        "code": str(row.get("symbol", "")),
                        "change_pct": 0,  # Tushare 同花顺数据可能没有实时涨跌幅
                        "stock_count": 0,
                        "hot_score": 50
                    }
                    concepts.append(concept)
                
                concepts.sort(key=lambda x: x.get("name", ""))
                self._set_cache(cache_key, concepts)
                return concepts
                
        except Exception as e:
            print(f"Error fetching concept data from Tushare: {e}")
        
        # 回退到东方财富 akshare 方法
        try:
            _disable_proxy()
            df = ak.stock_board_concept_name_em()
            if df is None or df.empty:
                return file_cached if file_cached else []
            
            concepts = []
            for _, row in df.iterrows():
                concept = {
                    "name": str(row.get("板块名称", "")),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "lead_stock": str(row.get("领涨股票", "")),
                    "lead_change": float(row.get("涨跌幅.1", 0)) if "涨跌幅.1" in row else 0,
                    "stock_count": int(row.get("股票数量", 0)) if "股票数量" in row else 0
                }
                concepts.append(concept)
            
            concepts.sort(key=lambda x: -x["change_pct"])
            self._set_cache(cache_key, concepts)
            return concepts
            
        except Exception as e:
            print(f"Error fetching concept data: {e}")
            return file_cached if file_cached else []
    
    def get_concept_detail(self, concept_name: str) -> Dict:
        """
        获取题材详情（包含成分股）
        """
        cache_key = f"concept_detail_{concept_name}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            _disable_proxy()
            # 获取题材成分股
            df = ak.stock_board_concept_cons_em(symbol=concept_name)
            
            if df is None or df.empty:
                return {"error": "未找到该题材数据"}
            
            stocks = []
            for _, row in df.iterrows():
                stock = {
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "price": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "turnover": float(row.get("成交额", 0)) if "成交额" in row else 0
                }
                stocks.append(stock)
            
            # 按涨跌幅排序
            stocks.sort(key=lambda x: -x["change_pct"])
            
            result = {
                "name": concept_name,
                "stocks": stocks,
                "count": len(stocks),
                "update_time": datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"Error fetching concept detail: {e}")
            return {"error": str(e)}
    
    def get_stock_detail(self, code: str) -> Dict:
        """Get individual stock details"""
        cache_key = f"stock_{code}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            _disable_proxy()
            # Stock info
            df = ak.stock_individual_info_em(symbol=code)
            
            if df is None or df.empty:
                return {"error": "Stock not found"}
            
            info = {}
            for _, row in df.iterrows():
                key = row.get("item", "")
                value = row.get("value", "")
                info[key] = value
            
            # Get real-time quote - with retry
            try:
                _disable_proxy()
                df_quote = ak.stock_zh_a_spot_em()
                if df_quote is not None:
                    stock_data = df_quote[df_quote["代码"] == code]
                    if not stock_data.empty:
                        row = stock_data.iloc[0]
                        info.update({
                            "最新价": row.get("最新价", 0),
                            "涨跌幅": row.get("涨跌幅", 0),
                            "涨跌额": row.get("涨跌额", 0),
                            "成交量": row.get("成交量", 0),
                            "成交额": row.get("成交额", 0),
                            "振幅": row.get("振幅", 0),
                            "最高": row.get("最高", 0),
                            "最低": row.get("最低", 0),
                            "今开": row.get("今开", 0),
                            "昨收": row.get("昨收", 0),
                        })
            except Exception as e:
                print(f"Error fetching quote: {e}")
            
            self._set_cache(cache_key, info)
            return info
            
        except Exception as e:
            print(f"Error fetching stock detail: {e}")
            return {"error": str(e)}
    
    def get_market_summary(self) -> Dict:
        """Get overall market summary"""
        cache_key = "market_summary"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        file_cached = self._get_file_cached(cache_key, max_age=600)

        result = None
        # 尝试备用 API 获取指数数据
        try:
            _disable_proxy()
            url = 'https://push2delay.eastmoney.com/api/qt/ulist.np/get'
            params = {
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fields': 'f2,f3,f4,f12,f14',
                'secids': '1.000001,0.399001,0.399006'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/',
            }
            session = requests.Session()
            session.trust_env = False
            resp = session.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()

            indices = []
            total_up = 0
            total_down = 0
            if data.get('rc') == 0 and 'data' in data and 'diff' in data['data']:
                for item in data['data']['diff']:
                    code = item.get('f12', '')
                    name_map = {'000001': '上证指数', '399001': '深证成指', '399006': '创业板指'}
                    if code in name_map:
                        change_pct = round(item.get('f3', 0), 2)
                        indices.append({
                            "name": name_map[code],
                            "close": round(item.get('f2', 0), 2),
                            "change_pct": change_pct
                        })
                        if change_pct > 0:
                            total_up += 1
                        elif change_pct < 0:
                            total_down += 1

            result = {
                "total": 0,
                "up": 0,
                "down": 0,
                "flat": 0,
                "up_pct": 0,
                "down_pct": 0,
                "indices": indices,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error fetching market summary from backup API: {e}")

        if result:
            self._set_cache(cache_key, result)
            return result

        # 回退到 akshare
        try:
            _disable_proxy()
            df = ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                return self._get_market_summary_fallback(file_cached)

            total = len(df)
            up = len(df[df["涨跌幅"] > 0])
            down = len(df[df["涨跌幅"] < 0])
            flat = total - up - down

            indices = []
            try:
                _disable_proxy()
                df_index = ak.stock_zh_index_daily(symbol="sh000001")
                if df_index is not None and not df_index.empty:
                    latest = df_index.iloc[-1]
                    prev = df_index.iloc[-2] if len(df_index) > 1 else latest
                    change_pct = (float(latest.get("close", 0)) / float(prev.get("close", 1)) - 1) * 100
                    indices.append({
                        "name": "上证指数",
                        "close": float(latest.get("close", 0)),
                        "change_pct": round(change_pct, 2)
                    })
            except:
                pass

            result = {
                "total": total,
                "up": up,
                "down": down,
                "flat": flat,
                "up_pct": round(up / total * 100, 2) if total > 0 else 0,
                "down_pct": round(down / total * 100, 2) if total > 0 else 0,
                "indices": indices,
                "timestamp": datetime.now().isoformat()
            }

            self._set_cache(cache_key, result)
            self.file_cache.set("market_all", df.to_dict('records'))
            return result

        except Exception as e:
            print(f"Error fetching market summary: {e}")
            return self._get_market_summary_fallback(file_cached)
    
    def _get_market_summary_fallback(self, cached: dict = None) -> Dict:
        """市场摘要备用方案"""
        if cached:
            return cached
        
        # 尝试获取指数数据作为后备
        try:
            _disable_proxy()
            df_index = ak.stock_zh_index_daily(symbol="sh000001")
            if df_index is not None and not df_index.empty:
                latest = df_index.iloc[-1]
                prev = df_index.iloc[-2] if len(df_index) > 1 else latest
                change_pct = (float(latest.get("close", 0)) / float(prev.get("close", 1)) - 1) * 100
                return {
                    "total": 0,
                    "up": 0,
                    "down": 0,
                    "flat": 0,
                    "up_pct": 0,
                    "down_pct": 0,
                    "indices": [{
                        "name": "上证指数",
                        "close": float(latest.get("close", 0)),
                        "change_pct": round(change_pct, 2)
                    }],
                    "timestamp": datetime.now().isoformat(),
                    "warning": "实时行情暂时无法获取"
                }
        except Exception as e:
            print(f"Fallback index error: {e}")
        
        return {
            "total": 0,
            "up": 0,
            "down": 0,
            "flat": 0,
            "up_pct": 0,
            "down_pct": 0,
            "indices": [],
            "timestamp": datetime.now().isoformat(),
            "warning": "数据暂时无法获取"
        }


# Singleton instance
stock_service = StockDataService()
