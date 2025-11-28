# tools.py

import akshare as ak
import pandas as pd
import json
import requests
import urllib3
from typing import List, Dict, Optional

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_limit_up_stocks(date: str) -> List[dict]:
    try:
        df = ak.stock_zt_pool_em(date=date.replace("-", ""))
        return df.to_dict('records') if not df.empty else []
    except Exception as e:
        print(f"获取涨停股失败: {e}")
        return []

def get_lhb_data(date: str) -> List[dict]:
    """获取龙虎榜数据"""
    try:
        # akshare的龙虎榜函数需要start_date和end_date参数
        formatted_date = date.replace("-", "")
        
        # 尝试获取龙虎榜详情数据（更常用）
        df = ak.stock_lhb_detail_em(start_date=formatted_date, end_date=formatted_date)
        
        if not df.empty:
            print(f"✅ 获取到 {len(df)} 条龙虎榜数据")
            return df.to_dict('records')
        else:
            print(f"⚠️ {date} 无龙虎榜数据")
            return []
            
    except Exception as e:
        print(f"❌ 获取龙虎榜数据失败: {e}")
        
        # 如果龙虎榜详情失败，尝试机构买卖统计
        try:
            df = ak.stock_lhb_jgmmtj_em(start_date=formatted_date, end_date=formatted_date)
            if not df.empty:
                print(f"✅ 从机构买卖统计获取到 {len(df)} 条数据")
                return df.to_dict('records')
            else:
                print(f"⚠️ {date} 无机构买卖统计数据")
                return []
        except Exception as e2:
            print(f"❌ 获取机构买卖统计也失败: {e2}")
            return []

def get_f10_data_for_stocks(stocks: List[dict]) -> Dict[str, dict]:
    """使用stock_value_em接口获取股票估值数据"""
    result = {}
    codes = list(set(s['代码'] for s in stocks))
    
    for code in codes:
        try:
            # 使用stock_value_em获取估值分析数据
            df = ak.stock_value_em(symbol=code)
            
            if not df.empty:
                # 获取最新一条数据（最后一行）
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
                print(f"✅ 获取 {code} 估值数据成功")
            else:
                print(f"⚠️ {code} 估值数据为空")
                result[code] = {
                    'pe': None, 'pb': None, 'pe_static': None, 'peg': None,
                    'market_cap': None, 'float_market_cap': None, 
                    'ps_ratio': None, 'pcf_ratio': None,
                    'data_date': '', 'close_price': None
                }
                
        except Exception as e:
            print(f"❌ 获取 {code} 估值数据失败: {e}")
            result[code] = {
                'pe': None, 'pb': None, 'pe_static': None, 'peg': None,
                'market_cap': None, 'float_market_cap': None, 
                'ps_ratio': None, 'pcf_ratio': None,
                'data_date': '', 'close_price': None
            }
    
    return result

def safe_parse_json(content: str):
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

def get_stock_price_realtime(stock_code, retry_count=3):
    """
    东方财富实时数据API
    增加重试机制和更好的错误处理
    """
    import time
    
    # 构造URL
    if stock_code.startswith('6'):
        market = '1'
    else:
        market = '0'
    
    url = f"https://push2.eastmoney.com/api/qt/stock/get?ut=fa5fd1943c7b386f172d6893dbfba10b&invt=2&fltt=2&fields=f43,f46,f44,f45,f47,f48,f170&secid={market}.{stock_code}"
    
    # 添加请求头，模拟浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    # 尝试禁用代理（如果需要）
    proxies = None
    # 如果需要强制禁用代理，可以取消下面的注释
    # proxies = {
    #     'http': None,
    #     'https': None,
    # }
    
    for attempt in range(retry_count):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=10,
                proxies=proxies,
                verify=False  # 如果SSL证书有问题可以禁用验证
            )
            
            if response.status_code != 200:
                if attempt < retry_count - 1:
                    time.sleep(0.5 * (attempt + 1))  # 指数退避
                    continue
                return None
            
            result = response.json()
            
            # 检查返回数据
            if 'data' not in result or result['data'] is None:
                return None
            
            data = result['data']
            
            # 检查数据是否有效（至少要有当前价）
            if data.get('f43') is None:
                return None
            
            # 返回标准化的数据格式
            return {
                'open': data.get('f46'),  # 开盘价
                'current': data.get('f43'),  # 当前价
                'high': data.get('f44'),  # 最高价
                'low': data.get('f45'),  # 最低价
                'volume': data.get('f47'),  # 成交量
                'amount': data.get('f48'),  # 成交额
                'change_rate': data.get('f170')  # 涨跌幅
            }
            
        except requests.exceptions.ConnectionError as e:
            # 连接错误，包括 RemoteDisconnected
            if attempt < retry_count - 1:
                wait_time = 0.5 * (attempt + 1)
                time.sleep(wait_time)
                continue
            return None
            
        except requests.exceptions.Timeout:
            if attempt < retry_count - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
            
        except requests.exceptions.RequestException as e:
            # 其他请求异常
            if attempt < retry_count - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
            
        except (KeyError, ValueError, TypeError) as e:
            # JSON解析错误或数据格式错误
            return None
            
        except Exception as e:
            # 其他未知错误
            if attempt < retry_count - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
    
    return None