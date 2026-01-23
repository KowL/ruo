"""
最终报告生成器节点

负责汇总所有分析结果，生成最终的投研报告
"""

from state import ResearchState


def node_finalize_report(state: ResearchState) -> ResearchState:
    """生成最终报告"""
    coach_advice = [a for a in state.get("day_trading_coach_advice", []) if isinstance(a, dict) and "code" in a]

    # 格式化短线龙头助手建议，与report.md保持一致
    if coach_advice:
        coach_summary_parts = []
        for a in coach_advice[:100]:
            stock_summary = f"""
🎯 {a['name']} ({a['code']})
- **操作建议**：{a['action']}
- **梯队地位**：{a.get('tier_rank', '?')}
- **情绪周期**：{a.get('mood_cycle', '?')}
- **理想买点**：{a['entry_point']}
- **止损价**：{a.get('stop_loss', '?')} 元
- **目标价**：{a.get('take_profit', '?')} 元
- **风险收益比**：{a.get('risk_reward_ratio', '?')}
- **风险信号**：{a.get('risk_signal', '无')}
- **逻辑**：{a['reason']}"""
            coach_summary_parts.append(stock_summary)

        coach_summary = "\n".join(coach_summary_parts)
    else:
        coach_summary = "暂无推荐打板标的。"

    summary = f"""
🎯【AI投研日报】{state['date']}

📊 数据官简报：
{state['data_officer_report']}

💡 策略师观点：
{state['strategist_thinking']}

🛡️ 风控提醒：
{' '.join(state['risk_controller_alerts'])}

🥋 短线龙头助手建议：
{coach_summary}

📌 综合建议：短线选手可在控制仓位前提下参与高确定性机会，优先选择"机构+游资"共进品种，回避纯情绪博傻标的。
"""
    return {
        "final_report": summary,
        "context_notes": ["✅ 全流程完成，生成最终报告"],
        "next_action": "FINISH"
    }