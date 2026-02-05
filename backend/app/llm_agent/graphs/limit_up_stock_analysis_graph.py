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
from datetime import datetime, timezone, timedelta

# 加载密钥
load_dotenv()

from app.llm_agent.state import ResearchState
from app.llm_agent.agents import (
    node_data_officer,
    node_strategist,
    node_risk_controller,
    node_day_trading_coach,
    node_finalize_report
)
from app.core.llm_factory import get_shared_llm


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

# === 数据库与缓存逻辑 ===

def save_report_to_db(state: dict, date: str):
    """将分析结果持久化到数据库"""
    # 生成 Markdown 报告内容（用于兼容老版本或直接展示）
    md_content = f"""
# 📊 AI投研日报：{date}

📅 分析时间：{datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")}
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
- **逻辑**：{item['reason']}
"""

    md_content += f"\n\n---\n📌 综合建议：短线选手可在控制仓位前提下参与高确定性机会..."

    # ✅ 数据库持久化
    try:
        from app.core.database import SessionLocal
        from app.models.stock import AnalysisReport
        
        # 统一日期格式处理
        report_date = datetime.strptime(date, "%Y-%m-%d")
        
        db = SessionLocal()
        try:
            # 检查是否已存在
            existing = db.query(AnalysisReport).filter(
                AnalysisReport.symbol == "GLOBAL",
                AnalysisReport.report_date == report_date,
                AnalysisReport.report_type == "limit-up"
            ).first()
            
            # 将完整的 state 序列化为 JSON 字符串存入 content
            # 这样前端收到的 content 就是完整的分析结果，而不仅仅是 md
            state_json = json.dumps(state, ensure_ascii=False, indent=2, default=str)
            
            if existing:
                existing.content = md_content.strip()
                existing.data = state_json
                existing.summary = state.get('data_officer_report', '')
            else:
                new_report = AnalysisReport(
                    symbol="GLOBAL",
                    report_date=report_date,
                    report_type="limit-up",
                    content=md_content.strip(),
                    data=state_json,
                    summary=state.get('data_officer_report', ''),
                    confidence=1.0
                )
                db.add(new_report)
            
            db.commit()
            print(f"✅ 报告已同步到数据库: {date} (GLOBAL/limit-up)")
        except Exception as db_err:
            db.rollback()
            print(f"❌ 数据库保存失败: {db_err}")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 数据库保存异常: {e}")

def get_cached_report(date: str) -> dict:
    """从数据库获取已存在的分析报告"""
    try:
        from app.core.database import SessionLocal
        from app.models.stock import AnalysisReport
        
        report_date = datetime.strptime(date, "%Y-%m-%d")
        db = SessionLocal()
        try:
            report = db.query(AnalysisReport).filter(
                AnalysisReport.symbol == "GLOBAL",
                AnalysisReport.report_date == report_date,
                AnalysisReport.report_type == "limit-up"
            ).first()
            
            if report and report.content:
                try:
                    return json.loads(report.content)
                except:
                    return None
            return None
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 读取数据库缓存异常: {e}")
        return None

# 主入口函数：完全依赖数据库
def run_ai_research_analysis(date: str, force_rerun: bool = False, llm=None) -> dict:
    """
    启动完整的涨停股 AI 投研分析流程
    """
    # ✅ 检查数据库缓存是否存在
    if not force_rerun:
        cached_state = get_cached_report(date)
        if cached_state:
            return {
                "success": True,
                "result": cached_state,
                "cached": True,
                "message": f"使用数据库缓存结果（{date}）"
            }

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

        # ✅ 执行完成后立即存入数据库
        save_report_to_db(final_state, date)

        return {
            "success": True,
            "result": final_state,
            "cached": False,
            "message": f"新生成报告并已存入数据库"
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