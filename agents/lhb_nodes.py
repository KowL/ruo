import os
import pandas as pd
import sqlite3
from typing import Any, Dict
from langgraph.graph import END

DB_PATH = os.path.join("data", "lhb.sqlite")

# 工具函数：获取龙虎榜数据
def lhb_data_tool() -> pd.DataFrame:
    # TODO: 实现真实数据抓取，这里用示例数据
    data = [
        {"code": "000001", "name": "平安银行", "buy": 2000000, "sell": 500000, "date": "2024-06-01"},
        {"code": "000002", "name": "万科A", "buy": 300000, "sell": 800000, "date": "2024-06-01"}
    ]
    df = pd.DataFrame(data)
    return df

# 节点1：数据获取
def fetch_lhb_data(state: Dict[str, Any]) -> Dict[str, Any]:
    df = lhb_data_tool()
    # 保存到sqlite
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("lhb", conn, if_exists="append", index=False)
    conn.close()
    state["df"] = df
    return state

# 节点2：数据分析
def analyze_lhb_data(state: Dict[str, Any]) -> Dict[str, Any]:
    df = state["df"]
    df["net_inflow"] = df["buy"] - df["sell"]
    state["df"] = df
    return state

# 节点3：建议生成
def generate_lhb_suggestion(state: Dict[str, Any]) -> Dict[str, Any]:
    df = state["df"]
    suggestions = []
    for _, row in df.iterrows():
        if row["net_inflow"] > 1_000_000:
            suggestion = "买入"
        elif row["net_inflow"] < -1_000_000:
            suggestion = "卖出"
        else:
            suggestion = "观望"
        suggestions.append({
            "code": row["code"],
            "name": row["name"],
            "suggestion": suggestion,
            "reason": f"净流入：{row['net_inflow']}"
        })
    state["suggestions"] = suggestions
    return state

# 节点4：输出
def output_lhb_result(state: Dict[str, Any]) -> Dict[str, Any]:
    for s in state["suggestions"]:
        print(f"{s['code']} {s['name']} 建议：{s['suggestion']}，理由：{s['reason']}")
    return END 