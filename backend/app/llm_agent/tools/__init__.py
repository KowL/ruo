"""
智能体工具模块
Agent Tools Module
"""

from .agent_tools import (
    analyze_lhb_data,
    analyze_candidate_stocks,
    get_stock_lhb_data,
    calculate_risk_reward
)

from app.utils.stock_tool import stock_tool, safe_parse_json

get_limit_up_stocks = stock_tool.get_limit_up_stocks
get_lhb_data = stock_tool.get_lhb_data
get_f10_data_for_stocks = stock_tool.get_f10_data_for_stocks

__all__ = [
    'analyze_lhb_data',
    'analyze_candidate_stocks',
    'get_stock_lhb_data',
    'calculate_risk_reward',
    'get_limit_up_stocks',
    'get_lhb_data',
    'get_f10_data_for_stocks',
    'safe_parse_json'
]
