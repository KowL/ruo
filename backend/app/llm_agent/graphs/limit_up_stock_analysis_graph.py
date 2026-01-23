# limit_up_stock_analysis_graph.py
"""
涨停股分析工作流图

专门用于涨停股 AI 投研分析的 LangGraph 工作流定义
重构后的模块化架构，使用独立的 state 和 agent 模块
"""

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import json
import traceback
from pathlib import Path
import pandas as pd
from datetime import datetime

# 加载密钥
load_dotenv()

# 导入模块化组件
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from state import ResearchState
from agent import (
    node_data_officer,
    node_strategist,
    node_risk_controller,
    node_day_trading_coach,
    node_finalize_report
)
from llm_factory import get_shared_llm

# =======================
# 🧭 条件路由函数
# =======================
def route_next_step(state: ResearchState) -> str:
    """根据状态决定下一步执行的节点"""
    return state["next_action"]

# =======================
# 🌐 构建涨停股分析工作流图
# =======================
def create_research_graph(llm=None):
    """
    创建涨停股研究工作流图

    Args:
        llm: 可选的 LLM 实例，如果不提供则使用共享实例

    Returns:
        编译后的工作流图
    """
    if llm is None:
        llm = get_shared_llm()

    workflow = StateGraph[ResearchState, None, ResearchState, ResearchState](ResearchState)

    # 创建包装函数来传递 LLM 实例
    def wrapped_data_officer(state):
        return node_data_officer(state)

    def wrapped_strategist(state):
        return node_strategist(state, llm)

    def wrapped_risk_controller(state):
        return node_risk_controller(state)

    def wrapped_day_trading_coach(state):
        return node_day_trading_coach(state, llm)

    def wrapped_finalize_report(state):
        return node_finalize_report(state)

    # 添加所有节点
    workflow.add_node("node_data_officer", wrapped_data_officer)
    workflow.add_node("node_strategist", wrapped_strategist)
    workflow.add_node("node_risk_controller", wrapped_risk_controller)
    workflow.add_node("node_day_trading_coach", wrapped_day_trading_coach)
    workflow.add_node("node_finalize_report", wrapped_finalize_report)

    # 设置入口点
    workflow.set_entry_point("node_data_officer")

    # 添加条件边（Condition Edge）
    workflow.add_conditional_edges(
        "node_data_officer",
        route_next_step,
        {
            "TO_STRATEGIST": "node_strategist"
        }
    )
    workflow.add_conditional_edges(
        "node_strategist",
        route_next_step,
        {
            "TO_RISK_CONTROLLER": "node_risk_controller"
        }
    )
    workflow.add_conditional_edges(
        "node_risk_controller",
        route_next_step,
        {
            "TO_DAY_TRADING_COACH": "node_day_trading_coach"
        }
    )
    workflow.add_conditional_edges(
        "node_day_trading_coach",
        route_next_step,
        {
            "TO_FINALIZER": "node_finalize_report"
        }
    )
    workflow.add_conditional_edges(
        "node_finalize_report",
        route_next_step,
        {
            "FINISH": END
        }
    )

    # 编译图
    app = workflow.compile()
    return app

# === 缓存配置 ===
CACHE_DIR = Path("cache/daily_research")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 新增函数：保存报告到本地
def save_report_to_cache(state: dict, date: str):
    """将分析结果持久化到本地缓存"""
    # 创建日期子目录
    date_dir = CACHE_DIR / date
    date_dir.mkdir(exist_ok=True)

    # 保存完整状态（用于调试和后续工作流）
    state_path = date_dir / "state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)

    # 生成并保存 Markdown 报告（给人看）
    md_content = f"""
# 📊 AI投研日报：{date}

📅 分析时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'-'*50}

## 📈 数据官简报
{state.get('data_officer_report', '无')}

## 💡 策略师观点
> {state.get('strategist_thinking', '无')}

## 🛡️ 风控提醒
"""
    for alert in state.get("risk_controller_alerts", []):
        md_content += f"- {alert}\n"

    md_content += "\n## 🥋 短线龙头助手建议\n"
    for item in state.get("day_trading_coach_advice", []):
        if isinstance(item, dict) and "name" in item:
            md_content += f"""
### {item['name']} ({item['code']})
- **操作建议**：{item['action']}
- **梯队地位**：{item.get('tier_rank', '?')}
- **情绪周期**：{item.get('mood_cycle', '?')}
- **理想买点**：{item['entry_point']}
- **止损价**：{item.get('stop_loss', '?')} 元
- **目标价**：{item.get('take_profit', '?')} 元
- **风险收益比**：{item.get('risk_reward_ratio', '?')}
- **风险信号**：{item.get('risk_signal', '无')}
- **逻辑**：{item['reason']}
"""

    md_content += f"\n\n---\n📌 综合建议：短线选手可在控制仓位前提下参与高确定性机会..."

    md_path = date_dir / "report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content.strip())

    # （可选）保存原始数据
    if "raw_limit_ups" in state:
        import pickle
        pkl_path = date_dir / "raw_data.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump(pd.DataFrame(state["raw_limit_ups"]), f)

    print(f"✅ 报告已缓存至: {date_dir}")

# 新增函数：检查是否已有缓存
def is_cached(date: str) -> bool:
    """判断某日的分析报告是否已存在"""
    date_dir = CACHE_DIR / date
    return date_dir.exists() and (date_dir / "report.md").exists()

# 主入口函数：支持缓存读取与写入
def run_ai_research_analysis(date: str, force_rerun: bool = False, llm=None) -> dict:
    """
    启动完整的涨停股 AI 投研分析流程
    支持缓存机制：若已存在且未强制重跑，则直接返回缓存结果

    Args:
        date: 分析日期，格式为 YYYY-MM-DD
        force_rerun: 是否强制重新运行，忽略缓存
        llm: 可选的 LLM 实例，如果不提供则使用共享实例

    Returns:
        包含分析结果的字典
    """
    cache_file = CACHE_DIR / date / "state.json"

    # ✅ 检查缓存是否存在
    if not force_rerun and is_cached(date):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_state = json.load(f)
            return {
                "success": True,
                "result": cached_state,
                "cached": True,
                "message": f"使用缓存结果（{date}）"
            }
        except Exception as e:
            print(f"读取缓存失败: {e}")

    # 🔁 否则执行完整分析流程
    try:
        graph = create_research_graph(llm)
        initial_state = {
            "date": date,
            "raw_limit_ups": [],
            "lhb_data": [],
            "f10_data": {},
            "context_notes": [],
            "next_action": "TO_DATA_OFFICER"
        }

        # 收集完整的状态信息
        accumulated_state = initial_state.copy()

        for output in graph.stream(initial_state):
            # 更新累积状态
            for node_name, node_output in output.items():
                if isinstance(node_output, dict):
                    accumulated_state.update(node_output)

            # 如果到达终点，保存最终状态
            if END in output:
                final_state = accumulated_state
                break
        else:
            # 如果没有到达END，使用累积状态
            final_state = accumulated_state

        if final_state is None:
            raise ValueError("图执行未产生任何输出")

        # ✅ 执行完成后立即缓存
        save_report_to_cache(final_state, date)

        return {
            "success": True,
            "result": final_state,
            "cached": False,
            "message": f"新生成报告并已缓存"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    run_ai_research_analysis(today, force_rerun=True)