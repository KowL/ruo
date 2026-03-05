"""
数据类型转换工具 - 修复numpy序列化问题
"""
import numpy as np
import pandas as pd
from typing import Any, Union

def safe_convert_to_python_types(data: Any) -> Any:
    """
    安全转换数据类型为Python原生类型，避免numpy序列化问题
    """
    if isinstance(data, dict):
        return {key: safe_convert_to_python_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [safe_convert_to_python_types(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(safe_convert_to_python_types(item) for item in data)
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    else:
        return data

def safe_float(value: Any) -> Union[float, None]:
    """安全转换为浮点数"""
    try:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.floating)):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int(value: Any) -> Union[int, None]:
    """安全转换为整数"""
    try:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.floating)):
            return int(value)
        return int(float(value))
    except (ValueError, TypeError):
        return None

def safe_str(value: Any) -> str:
    """安全转换为字符串"""
    try:
        if value is None or pd.isna(value):
            return ""
        return str(value)
    except:
        return ""