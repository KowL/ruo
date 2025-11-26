# agent_system.py
from typing import TypedDict, Annotated, List, Dict, Literal, Optional
import operator
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatTongyi  # 或 ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import json
import pandas as pd
import traceback
from pathlib import Path
import os
import pickle
from datetime import datetime

# 加载密钥
load_dotenv()

# 导入工具函数
from tools import get_limit_up_stocks, get_lhb_data, get_f10_data_for_stocks, safe_parse_json

# =======================
# 🧠 LLM 初始化（通义千问）
# =======================
llm = ChatTongyi(
    model="qwen-plus-latest",  # 推荐 qwen-plus 提升推理质量
    api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
    temperature=0.6,
)

# =======================
# 🧬 定义状态（State）
# =======================
class ResearchState(TypedDict):
    date: str
    raw_limit_ups: List[dict]
    lhb_data: List[dict]
    f10_data: Dict[str, dict]
    data_officer_report: str
    strategist_thinking: str
    risk_controller_alerts: List[str]
    day_trading_coach_advice: List[dict]
    final_report: str
    context_notes: Annotated[List[str], operator.add]
    next_action: Literal[
        "TO_DATA_OFFICER",
        "TO_STRATEGIST",
        "TO_RISK_CONTROLLER",
        "TO_DAY_TRADING_COACH",
        "TO_FINALIZER",
        "FINISH"
    ]
    error: Optional[str]

# =======================
# 🤖 Node 1: 数据官
# =======================
def node_data_officer(state: ResearchState) -> ResearchState:
    """采集原始数据"""
    stocks = get_limit_up_stocks(state['date'])
    lhb = get_lhb_data(state['date'])
    f10 = get_f10_data_for_stocks(stocks)

    count = len(stocks)
    concepts = ", ".join(pd.DataFrame(stocks)['概念'].str.split(',').sum()[:10]) if count > 0 else ""

    report = f"📊 数据官简报：{state['date']} 共 {count} 只个股涨停。\n主要热点概念：{concepts}。"

    return {
        "raw_limit_ups": stocks,
        "lhb_data": lhb,
        "f10_data": f10,
        "data_officer_report": report,
        "context_notes": [f"✅ 数据官完成，共采集 {count} 只涨停股"],
        "next_action": "TO_STRATEGIST"
    }

# =======================
# 🧠 Node 2: 策略师
# =======================
def node_strategist(state: ResearchState) -> ResearchState:
    prompt = ChatPromptTemplate.from_template("""
你是资深策略师，请结合当前涨停分布、连板情况和市场情绪，判断主线方向与操作策略。
输入信息：
- 涨停总数：{total}
- 连板数量：{lianban_count}
- 热点概念：{top_concepts}

请输出你的思考过程，控制在100字以内。
""")
    chain = prompt | llm

    df = pd.DataFrame(state['raw_limit_ups'])
    lianban_count = len(df[df['连续涨停天数'] > 1])
    top_concepts = df['概念'].str.split(',').explode().value_counts().head(3).index.tolist()

    resp = chain.invoke({
        "total": len(state['raw_limit_ups']),
        "lianban_count": lianban_count,
        "top_concepts": ", ".join(top_concepts)
    })

    return {
        "strategist_thinking": resp.content.strip(),
        "context_notes": ["💡 策略师完成分析"],
        "next_action": "TO_RISK_CONTROLLER"
    }

# =======================
# 🛡️ Node 3: 风控员
# =======================
def node_risk_controller(state: ResearchState) -> ResearchState:
    alerts = []
    df = pd.DataFrame(state['raw_limit_ups'])

    # 高估值检查
    high_pe_stocks = df[pd.to_numeric(df['市盈率-动态'], errors='coerce') > 150]
    if len(high_pe_stocks) > 0:
        names = ",".join(high_pe_stocks['名称'][:3])
        alerts.append(f"⚠️ 高估值警示：{names} 等 {len(high_pe_stocks)} 只个股 PE > 150")

    # 板块过热检查
    concept_grouped = df['概念'].str.split(',').explode().value_counts()
    overheated = concept_grouped[concept_grouped > 5].index.tolist()
    if overheated:
        alerts.append(f"⚠️ 板块过热：'{overheated[0]}' 概念有 {concept_grouped[overheated[0]]} 只涨停股，注意分化风险")

    return {
        "risk_controller_alerts": alerts,
        "context_notes": ["🛡️ 风控员完成扫描"] + ([f"🔴 发现风险: {a}" for a in alerts] if alerts else []),
        "next_action": "TO_DAY_TRADING_COACH"
    }

# =======================
# 🥋 Node 4: 打板教练
# =======================
def node_day_trading_coach(state: ResearchState) -> ResearchState:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
你是一名经验丰富的【打板教练】，擅长识别强势股临盘信号。
请根据以下信息，对今日涨停股中具备潜力的标的给出具体操作建议。

⚠️ 必须输出标准 JSON 数组，每项必须包含以下字段：
- code: 股票代码（如 '600389'）
- name: 名称（如 '剑桥科技'）
- action: 动作（"可打板"/"关注"/"观望"/"回避"）
- entry_point: 买点描述（如 '9:25集合竞价'）
- stop_loss: 止损价（单位：元）
- take_profit: 目标价（单位：元）
- risk_reward_ratio: 风险收益比（如 '1:3'）
- reason: 不超过50字的逻辑说明

示例输出：
[{"code":"600389","name":"剑桥科技","action":"可打板","entry_point":"9:25集合竞价","stop_loss":"118.5","take_profit":"140","risk_reward_ratio":"1:3","reason":"CPO龙头+机构加仓"}]

只推荐最多 3 只最有把握的股票。
不得推荐 ST 股或 PE > 200 的个股。
""")
    ])

    # 构建候选池
    candidates = []
    for s in state['raw_limit_ups']:
        code = s['代码']
        name = s['名称']
        if 'ST' in name:
            continue
        pe = (state['f10_data'].get(code) or {}).get('pe', None)
        if isinstance(pe, (int, float)) and (pe or 0) > 200:
            continue

        yoyou_buy_in = False
        top_keywords = ["国盛证券宁波桑田路", "东方财富拉萨团结路", "华鑫证券上海分公司"]
        for item in state['lhb_data']:
            if item.get("证券简称") == name and any(kw in item.get("买入总额名称与营业部", "") for kw in top_keywords):
                yoyou_buy_in = True
                break

        candidates.append({
            "code": code,
            "name": name,
            "limit_time": s.get("涨停时间", "未知"),
            "is_lianban": s.get("连续涨停天数", 0) > 1,
            "turnover_rate": s.get("换手率", 0),
            "volume_ratio": s.get("量比", 1.0),
            "concept": s.get("概念", ""),
            "pe": pe,
            "yoyou_buy_in": yoyou_buy_in
        })

    try:
        response = llm.invoke([
            HumanMessage(content=f"候选股:\n{json.dumps(candidates[:10], ensure_ascii=False, indent=2)}\n\n请输出建议")
        ])
        content = response.content.strip()
        advice_list = safe_parse_json(content)
    except Exception as e:
        advice_list = [{"error": str(e), "fallback": "生成失败"}]

    return {
        "day_trading_coach_advice": advice_list,
        "context_notes": ["🥋 打板教练提供建议"],
        "next_action": "TO_FINALIZER"
    }

# =======================
# 📝 Node 5: 最终报告生成器
# =======================
def node_finalize_report(state: ResearchState) -> ResearchState:
    coach_advice = [a for a in state.get("day_trading_coach_advice", []) if isinstance(a, dict) and "code" in a]

    coach_summary = "\n".join([
        f"🎯 {a['name']}({a['code']}): {a['action']} | 买点:{a['entry_point']} | 目标:{a.get('take_profit','?')}元 | R/R:{a.get('risk_reward_ratio','?')}"
        for a in coach_advice[:3]
    ]) if coach_advice else "暂无推荐打板标的。"

    summary = f"""
🎯【AI投研日报】{state['date']}

📊 数据官简报：
{state['data_officer_report']}

💡 策略师观点：
{state['strategist_thinking']}

🛡️ 风控提醒：
{' '.join(state['risk_controller_alerts'])}

🥋 打板教练建议：
{coach_summary}

📌 综合建议：短线选手可在控制仓位前提下参与高确定性机会，优先选择“机构+游资”共进品种，回避纯情绪博傻标的。
"""
    return {
        "final_report": summary,
        "context_notes": ["✅ 全流程完成，生成最终报告"],
        "next_action": "FINISH"
    }

# =======================
# 🧭 条件路由函数
# =======================
def route_next_step(state: ResearchState) -> str:
    return state["next_action"]

# =======================
# 🌐 构建 Graph
# =======================
def create_research_graph():
    workflow = StateGraph(ResearchState)

    # 添加所有节点
    workflow.add_node("node_data_officer", node_data_officer)
    workflow.add_node("node_strategist", node_strategist)
    workflow.add_node("node_risk_controller", node_risk_controller)
    workflow.add_node("node_day_trading_coach", node_day_trading_coach)
    workflow.add_node("node_finalize_report", node_finalize_report)

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

    md_content += "\n## 🥋 打板教练建议\n"
    for item in state.get("day_trading_coach_advice", []):
        if isinstance(item, dict) and "name" in item:
            md_content += f"""
### {item['name']} ({item['code']})
- **操作建议**：{item['action']}
- **理想买点**：{item['entry_point']}
- **止损价**：{item.get('stop_loss', '?')} 元
- **目标价**：{item.get('take_profit', '?')} 元
- **风险收益比**：{item.get('risk_reward_ratio', '?')}
- **逻辑**：{item['reason']}
"""

    md_content += f"\n\n---\n📌 综合建议：短线选手可在控制仓位前提下参与高确定性机会..."

    md_path = date_dir / "report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content.strip())

    # （可选）保存原始数据
    if "raw_limit_ups" in state:
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
def run_ai_research_analysis(date: str, force_rerun: bool = False) -> Dict:
    """
    启动完整的 LangGraph 多 Agent 分析流程
    支持缓存机制：若已存在且未强制重跑，则直接返回缓存结果
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
        graph = create_research_graph()
        initial_state = {
            "date": date,
            "raw_limit_ups": [],
            "lhb_data": [],
            "f10_data": {},
            "context_notes": [],
            "next_action": "TO_DATA_OFFICER"
        }

        final_state = None
        for output in graph.stream(initial_state):
            final_state = output.get(END, output)

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
