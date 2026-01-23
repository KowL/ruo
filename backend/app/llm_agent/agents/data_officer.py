"""
数据官节点

负责采集原始数据：涨停股、龙虎榜、F10数据
"""

import pandas as pd
from state import ResearchState
from tools import get_limit_up_stocks, get_lhb_data, get_f10_data_for_stocks


def node_data_officer(state: ResearchState) -> ResearchState:
    """采集原始数据"""
    stocks = get_limit_up_stocks(state['date'])
    lhb = get_lhb_data(state['date'])
    f10 = get_f10_data_for_stocks(stocks)

    count = len(stocks)
    # 使用实际的列名 '所属行业' 而不是 '概念'
    concepts = ", ".join(pd.DataFrame(stocks)['所属行业'].value_counts().head(10).index.tolist()) if count > 0 else ""

    report = f"📊 数据官简报：{state['date']} 共 {count} 只个股涨停。\n主要热点概念：{concepts}。"

    return {
        "raw_limit_ups": stocks,
        "lhb_data": lhb,
        "f10_data": f10,
        "data_officer_report": report,
        "context_notes": [f"✅ 数据官完成，共采集 {count} 只涨停股"],
        "next_action": "TO_STRATEGIST"
    }