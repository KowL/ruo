"""
风控员节点

负责识别市场风险，包括高估值警示、板块过热检查等
"""

import pandas as pd
from state import ResearchState


def node_risk_controller(state: ResearchState) -> ResearchState:
    """风控员分析节点"""
    alerts = []
    df = pd.DataFrame(state['raw_limit_ups'])

    # 高估值检查 - 使用 f10_data 中的市盈率信息
    high_pe_stocks = []
    f10_data = state.get('f10_data', {})

    if f10_data:  # 只有当F10数据存在时才进行检查
        for _, row in df.iterrows():
            code = row['代码']
            name = row['名称']
            pe_info = f10_data.get(code, {})
            pe = pe_info.get('pe')

            if isinstance(pe, (int, float)) and pe > 150:
                high_pe_stocks.append(name)

        if len(high_pe_stocks) > 0:
            names = ",".join(high_pe_stocks[:3])
            alerts.append(f"⚠️ 高估值警示：{names} 等 {len(high_pe_stocks)} 只个股 PE > 150")
    else:
        # 如果没有F10数据，可以基于其他指标进行风险提示
        if len(df) > 50:  # 如果涨停股数量过多
            alerts.append("⚠️ 市场过热：涨停股数量过多，注意追高风险")

    # 板块过热检查 - 使用实际的列名 '所属行业'
    if '所属行业' in df.columns:
        concept_grouped = df['所属行业'].value_counts()
        overheated = concept_grouped[concept_grouped > 5].index.tolist()
        if overheated:
            alerts.append(f"⚠️ 板块过热：'{overheated[0]}' 行业有 {concept_grouped[overheated[0]]} 只涨停股，注意分化风险")

    return {
        "risk_controller_alerts": alerts,
        "context_notes": ["🛡️ 风控员完成扫描"] + ([f"🔴 发现风险: {a}" for a in alerts] if alerts else []),
        "next_action": "TO_DAY_TRADING_COACH"
    }