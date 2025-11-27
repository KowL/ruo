# tools.py

import akshare as ak
import pandas as pd
import json
from typing import List, Dict, Optional

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
