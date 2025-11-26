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
    try:
        df = ak.stock_lhb_jgmmtj_em(date=date.replace("-", ""))
        return df.to_dict('records') if not df.empty else []
    except Exception as e:
        return []

def get_f10_data_for_stocks(stocks: List[dict]) -> Dict[str, dict]:
    result = {}
    codes = list(set(s['代码'] for s in stocks))
    for code in codes:
        try:
            info = ak.stock_individual_info_em(symbol=code)
            if info is not None:
                d = dict(zip(info['item'], info['value']))
                result[code] = {
                    'pe': float(d.get('市盈率-动态', 0)) if d.get('市盈率-动态') else None,
                    'pb': float(d.get('市净率', 0)) if d.get('市净率') else None,
                    'holders': d.get('股东总数', ''),
                    'industry': d.get('所属行业', '')
                }
        except:
            result[code] = {'pe': None, 'pb': None, 'holders': '', 'industry': ''}
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
