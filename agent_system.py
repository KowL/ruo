# agent_system.py
from typing import TypedDict, Annotated, List, Dict, Literal, Optional
import operator
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi  # 或 ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import Tool
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
    # 使用实际的列名 '连板数'
    lianban_count = len(df[df['连板数'] > 1]) if '连板数' in df.columns else 0
    # 使用实际的列名 '所属行业'
    top_concepts = df['所属行业'].value_counts().head(3).index.tolist()

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

# =======================
# 🛠️ 打板教练分析工具
# =======================
def analyze_lhb_data(lhb_data_json: str) -> str:
    """分析龙虎榜数据，识别主力资金动向"""
    try:
        lhb_data = json.loads(lhb_data_json) if isinstance(lhb_data_json, str) else lhb_data_json
        
        if not lhb_data:
            return "龙虎榜数据为空，无法分析主力资金动向"
        
        analysis = []
        analysis.append(f"📊 龙虎榜数据分析（共{len(lhb_data)}条记录）：")
        
        # 分析净买入金额排名
        net_buy_stocks = []
        for item in lhb_data[:10]:  # 只分析前10条
            name = item.get('名称', '')
            net_buy = item.get('龙虎榜净买额', 0)
            reason = item.get('上榜原因', '')
            explanation = item.get('解读', '')
            
            net_buy_stocks.append({
                'name': name,
                'net_buy': net_buy,
                'reason': reason,
                'explanation': explanation
            })
        
        # 按净买入金额排序
        net_buy_stocks.sort(key=lambda x: x['net_buy'], reverse=True)
        
        analysis.append("\n🔥 主力资金净买入TOP5：")
        for i, stock in enumerate(net_buy_stocks[:5]):
            if stock['net_buy'] > 0:
                analysis.append(f"{i+1}. {stock['name']}: +{stock['net_buy']/10000:.0f}万元 ({stock['explanation']})")
        
        analysis.append("\n📉 主力资金净卖出TOP3：")
        negative_stocks = [s for s in net_buy_stocks if s['net_buy'] < 0]
        for i, stock in enumerate(negative_stocks[:3]):
            analysis.append(f"{i+1}. {stock['name']}: {stock['net_buy']/10000:.0f}万元 ({stock['explanation']})")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"龙虎榜数据分析失败: {str(e)}"

def analyze_candidate_stocks(candidates_json: str) -> str:
    """分析候选股票池，筛选优质标的"""
    try:
        candidates = json.loads(candidates_json) if isinstance(candidates_json, str) else candidates_json
        
        if not candidates:
            return "候选股票池为空"
        
        analysis = []
        analysis.append(f"🎯 候选股票分析（共{len(candidates)}只）：")
        
        # 按连板数排序
        lianban_stocks = [c for c in candidates if c.get('is_lianban', False)]
        analysis.append(f"\n🚀 连板股（{len(lianban_stocks)}只）：")
        
        lianban_stocks.sort(key=lambda x: x.get('turnover_rate', 0), reverse=True)
        for i, stock in enumerate(lianban_stocks[:5]):
            analysis.append(f"{i+1}. {stock['name']}({stock['code']}): 换手率{stock.get('turnover_rate', 0):.1f}%, 行业:{stock.get('concept', '')}")
        
        # 高换手率股票
        high_turnover = [c for c in candidates if c.get('turnover_rate', 0) > 10]
        analysis.append(f"\n💫 高换手率股票（>10%, 共{len(high_turnover)}只）：")
        
        high_turnover.sort(key=lambda x: x.get('turnover_rate', 0), reverse=True)
        for i, stock in enumerate(high_turnover[:5]):
            analysis.append(f"{i+1}. {stock['name']}({stock['code']}): {stock.get('turnover_rate', 0):.1f}%")
        
        # 行业分布
        industries = {}
        for stock in candidates:
            industry = stock.get('concept', '未知')
            industries[industry] = industries.get(industry, 0) + 1
        
        analysis.append(f"\n🏭 行业分布：")
        sorted_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)
        for industry, count in sorted_industries[:5]:
            analysis.append(f"- {industry}: {count}只")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"候选股票分析失败: {str(e)}"

def get_stock_lhb_data(stock_info_json: str) -> str:
    """获取特定股票的龙虎榜数据
    
    参数格式: JSON字符串，包含股票代码和名称
    例如: '{"code": "000001", "name": "平安银行", "date": "2025-11-26"}'
    """
    try:
        if isinstance(stock_info_json, str):
            stock_info = json.loads(stock_info_json)
        else:
            stock_info = stock_info_json
            
        code = stock_info.get('code', '')
        name = stock_info.get('name', '')
        date = stock_info.get('date', '')
        
        if not code or not name:
            return f"❌ 股票信息不完整: {stock_info}"
        
        # 从全局龙虎榜数据中查找该股票的记录
        # 这里需要访问state中的lhb_data，我们通过全局变量传递
        global current_lhb_data
        if not hasattr(get_stock_lhb_data, 'lhb_data'):
            return f"⚠️ {name}({code}) 未找到龙虎榜数据"
            
        lhb_data = getattr(get_stock_lhb_data, 'lhb_data', [])
        
        # 查找该股票的龙虎榜记录
        stock_lhb_records = []
        for record in lhb_data:
            if (record.get('代码') == code or 
                record.get('名称') == name or 
                name in record.get('名称', '')):
                stock_lhb_records.append(record)
        
        if not stock_lhb_records:
            return f"⚠️ {name}({code}) 未上龙虎榜"
        
        # 分析该股票的龙虎榜数据
        analysis = []
        analysis.append(f"🎯 {name}({code}) 龙虎榜分析：")
        
        for i, record in enumerate(stock_lhb_records):
            net_buy = record.get('龙虎榜净买额', 0)
            buy_amount = record.get('龙虎榜买入额', 0)
            sell_amount = record.get('龙虎榜卖出额', 0)
            reason = record.get('上榜原因', '')
            explanation = record.get('解读', '')
            
            analysis.append(f"\n📊 记录{i+1}:")
            analysis.append(f"- 上榜原因: {reason}")
            analysis.append(f"- 净买入: {net_buy/10000:.0f}万元")
            analysis.append(f"- 买入额: {buy_amount/10000:.0f}万元")
            analysis.append(f"- 卖出额: {sell_amount/10000:.0f}万元")
            analysis.append(f"- 市场解读: {explanation}")
            
            # 判断主力资金态度
            if net_buy > 0:
                attitude = "看多" if net_buy > buy_amount * 0.3 else "温和看多"
            elif net_buy < 0:
                attitude = "看空" if abs(net_buy) > sell_amount * 0.3 else "温和看空"
            else:
                attitude = "中性"
            analysis.append(f"- 主力态度: {attitude}")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"获取龙虎榜数据失败: {str(e)}"

def calculate_risk_reward(stock_data_json: str) -> str:
    """计算风险收益比和买卖点，包括止损价和目标价
    
    参数格式: JSON字符串，包含股票基本信息
    例如: '{"code": "000001", "name": "平安银行", "turnover_rate": 5.2, "pe": 6.5, "current_price": 10.5}'
    
    返回格式: JSON字符串，包含止损价、目标价和风险收益比
    """
    try:
        if isinstance(stock_data_json, str):
            stock_data = json.loads(stock_data_json)
        else:
            # 如果传入的不是字符串，尝试直接使用
            stock_data = stock_data_json
        
        name = stock_data.get('name', '未知股票')
        code = stock_data.get('code', '')
        current_price = float(stock_data.get('current_price', 0))
        
        # 如果没有价格信息，返回错误
        if current_price <= 0:
            return json.dumps({
                "code": code,
                "name": name,
                "stop_loss": 0,
                "take_profit": 0,
                "risk_reward_ratio": 0,
                "error": "缺少价格信息，无法计算止损价和目标价"
            }, ensure_ascii=False)
        
        # 基于换手率和PE估算风险等级
        turnover = float(stock_data.get('turnover_rate', 0))
        pe = stock_data.get('pe')
        
        if turnover > 15:
            risk_level = "高风险"
            risk_score = 3
            # 高风险：止损幅度更大（-8%），目标价更保守（+10%）
            stop_loss_pct = -0.08
            take_profit_pct = 0.10
        elif turnover > 8:
            risk_level = "中风险"
            risk_score = 2
            # 中风险：止损-5%，目标+15%
            stop_loss_pct = -0.05
            take_profit_pct = 0.15
        else:
            risk_level = "低风险"
            risk_score = 1
            # 低风险：止损-3%，目标+20%
            stop_loss_pct = -0.03
            take_profit_pct = 0.20
        
        # 根据PE调整目标价
        if pe and pe > 0:
            if pe > 100:
                valuation = "高估"
                val_score = 3
                # 高估值：降低目标价
                take_profit_pct *= 0.7
            elif pe > 30:
                valuation = "合理"
                val_score = 2
                # 合理估值：保持目标价
            else:
                valuation = "低估"
                val_score = 1
                # 低估值：提高目标价
                take_profit_pct *= 1.2
        else:
            valuation = "无法评估"
            val_score = 2
        
        # 计算止损价和目标价
        stop_loss = round(current_price * (1 + stop_loss_pct), 2)
        take_profit = round(current_price * (1 + take_profit_pct), 2)
        
        # 计算风险收益比
        risk = current_price - stop_loss
        reward = take_profit - current_price
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0
        
        # 返回JSON格式的结果
        result = {
            "code": code,
            "name": name,
            "current_price": current_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": risk_reward_ratio,
            "risk_level": risk_level,
            "valuation": valuation,
            "analysis": f"风险等级: {risk_level}, 估值: {valuation}, 换手率: {turnover:.1f}%"
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"风险收益分析失败: {str(e)}",
            "stop_loss": 0,
            "take_profit": 0,
            "risk_reward_ratio": 0
        }, ensure_ascii=False)

# 创建工具列表
coach_tools = [
    Tool(
        name="analyze_candidate_stocks", 
        func=analyze_candidate_stocks,
        description="分析候选股票池，筛选连板股、高换手率股票和强势板块。输入：候选股票数据的JSON字符串。这应该是你的第一步分析。"
    ),
    Tool(
        name="get_stock_lhb_data",
        func=get_stock_lhb_data,
        description="获取特定股票的龙虎榜数据和主力资金分析。输入：股票信息JSON字符串，格式如'{\"code\":\"000001\",\"name\":\"平安银行\",\"date\":\"2025-11-26\"}'"
    ),
    Tool(
        name="calculate_risk_reward",
        func=calculate_risk_reward,
        description="计算个股的风险收益比、止损价和目标价。输入：单个股票数据的JSON字符串，必须包含current_price字段，格式如'{\"code\":\"000001\",\"name\":\"平安银行\",\"turnover_rate\":5.2,\"pe\":6.5,\"current_price\":10.5}'。返回JSON格式，包含stop_loss（止损价）、take_profit（目标价）和risk_reward_ratio（风险收益比）字段。"
    ),
    Tool(
        name="analyze_lhb_data",
        func=analyze_lhb_data,
        description="分析整体龙虎榜数据，识别市场主力资金动向。输入：龙虎榜数据的JSON字符串。用于了解整体市场情况。"
    )
]

# =======================
# 🥋 Node 4: 打板教练 (ReAct Agent优化版)
# =======================
def node_day_trading_coach(state: ResearchState) -> ResearchState:
    """使用ReAct Agent的打板教练，输出详细思考过程"""
    
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

        # 获取价格信息：优先使用最新价，其次使用f10_data中的close_price
        current_price = s.get("最新价") or (state['f10_data'].get(code) or {}).get('close_price') or 0

        candidates.append({
            "code": code,
            "name": name,
            "limit_time": s.get("首次封板时间", "未知"),
            "is_lianban": s.get("连板数", 0) > 1,
            "turnover_rate": s.get("换手率", 0),
            "volume_ratio": 1.0,  # 量比列不存在，使用默认值
            "concept": s.get("所属行业", ""),
            "pe": pe,
            "current_price": current_price  # 添加当前价格
        })

    try:
        # 设置全局龙虎榜数据，供工具函数使用
        get_stock_lhb_data.lhb_data = state['lhb_data']
        
        # 创建ReAct Agent
        system_prompt = """你是一名经验丰富的【打板教练】，擅长识别强势股临盘信号。

你的分析流程：
1. 首先使用analyze_candidate_stocks工具分析候选股票池，了解整体情况
2. 对于重点关注的股票，使用get_stock_lhb_data工具查询其龙虎榜数据
3. 使用calculate_risk_reward工具计算重点股票的风险收益比
4. 如需了解整体市场情况，可使用analyze_lhb_data工具
5. 最后综合所有分析结果，给出最终的打板建议

分析重点：
- 优先关注连板股和高换手率股票
- 对重点股票深入分析其龙虎榜数据，识别主力资金参与情况
- **重要**：对于每只重点股票，必须使用calculate_risk_reward工具计算止损价和目标价
- calculate_risk_reward工具会返回JSON格式，包含stop_loss（止损价）、take_profit（目标价）和risk_reward_ratio（风险收益比）字段
- 你必须从工具返回的JSON中提取这些值，并在最终输出中使用这些具体的数值
- 如果工具返回的stop_loss或take_profit为0，说明缺少价格信息，你应该在reason中说明
- 优先推荐有主力资金参与且技术面强势的标的
- 针对所有连板股输出操作建议

最终输出格式必须是JSON数组，包含以下字段：
- code: 股票代码
- name: 股票名称  
- action: 操作建议（"可打板"/"关注"/"观望"/"回避"）
- entry_point: 买点描述
- stop_loss: 止损价（必须是从calculate_risk_reward工具返回的数值，不能为0，除非确实缺少价格信息）
- take_profit: 目标价（必须是从calculate_risk_reward工具返回的数值，不能为0，除非确实缺少价格信息）
- risk_reward_ratio: 风险收益比（必须是从calculate_risk_reward工具返回的数值）
- reason: 逻辑说明（不超过30字）

请开始你的分析。"""

        # 创建ReAct Agent
        react_agent = create_react_agent(
            model=llm,
            tools=coach_tools,
            prompt=system_prompt
        )
        
        # 准备输入数据 - 不再限制数据量
        candidates_str = json.dumps(candidates, ensure_ascii=False, default=str)
        
        user_query = f"""请分析以下候选股票池并给出打板建议：

候选股票池（共{len(candidates)}只）：
{candidates_str}

分析日期：{state['date']}

请按照你的分析流程：
1. 先分析候选股票池的整体情况
2. 对重点股票逐一查询龙虎榜数据
3. 计算风险收益比
4. 给出最终的投资建议

注意：龙虎榜数据已准备就绪，你可以通过get_stock_lhb_data工具查询任何股票的龙虎榜信息。"""

        # 执行ReAct Agent
        print("🤖 打板教练开始分析...")
        
        response = react_agent.invoke({
            "messages": [HumanMessage(content=user_query)]
        })
        
        # 提取最终的AI消息
        final_message = ""
        thinking_process = []
        
        for message in response["messages"]:
            if isinstance(message, AIMessage):
                thinking_process.append(f"🤔 思考: {message.content}")
                final_message = message.content
        
        # 打印思考过程
        print("\n" + "="*50)
        print("🧠 打板教练思考过程：")
        for step in thinking_process:
            print(step)
        print("="*50 + "\n")
        
        # 从消息历史中提取工具调用结果，构建价格信息映射
        price_info_map = {}  # {code: {stop_loss, take_profit, risk_reward_ratio}}
        
        for message in response["messages"]:
            # 查找工具调用的结果消息
            if hasattr(message, 'content') and isinstance(message.content, str):
                # 尝试从工具返回结果中提取价格信息
                try:
                    # calculate_risk_reward工具返回的是JSON字符串
                    if '"stop_loss"' in message.content and '"take_profit"' in message.content:
                        tool_result = safe_parse_json(message.content)
                        if isinstance(tool_result, dict) and 'code' in tool_result:
                            code = tool_result.get('code', '')
                            if code and tool_result.get('stop_loss', 0) > 0:
                                price_info_map[code] = {
                                    'stop_loss': tool_result.get('stop_loss', 0),
                                    'take_profit': tool_result.get('take_profit', 0),
                                    'risk_reward_ratio': tool_result.get('risk_reward_ratio', 0)
                                }
                except:
                    pass
        
        # 尝试从最终消息中提取JSON
        advice_list = []
        if final_message:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\[.*?\]', final_message, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                advice_list = safe_parse_json(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个消息
                advice_list = safe_parse_json(final_message)
        
        # 后处理：补充缺失的价格信息
        for advice in advice_list:
            if isinstance(advice, dict) and 'code' in advice:
                code = advice.get('code', '')
                # 如果止损价或目标价为0，尝试从工具调用结果中获取
                if (advice.get('stop_loss', 0) == 0 or advice.get('take_profit', 0) == 0) and code in price_info_map:
                    price_info = price_info_map[code]
                    if advice.get('stop_loss', 0) == 0:
                        advice['stop_loss'] = price_info.get('stop_loss', 0)
                    if advice.get('take_profit', 0) == 0:
                        advice['take_profit'] = price_info.get('take_profit', 0)
                    if advice.get('risk_reward_ratio', 0) == 0:
                        advice['risk_reward_ratio'] = price_info.get('risk_reward_ratio', 0)
                
                # 如果仍然没有价格信息，尝试从候选池中获取当前价格并计算
                if (advice.get('stop_loss', 0) == 0 or advice.get('take_profit', 0) == 0):
                    # 从候选池中查找该股票
                    candidate = next((c for c in candidates if c.get('code') == code), None)
                    if candidate and candidate.get('current_price', 0) > 0:
                        current_price = candidate.get('current_price', 0)
                        turnover = candidate.get('turnover_rate', 0)
                        pe = candidate.get('pe')
                        
                        # 使用与calculate_risk_reward相同的逻辑计算
                        if turnover > 15:
                            stop_loss_pct = -0.08
                            take_profit_pct = 0.10
                        elif turnover > 8:
                            stop_loss_pct = -0.05
                            take_profit_pct = 0.15
                        else:
                            stop_loss_pct = -0.03
                            take_profit_pct = 0.20
                        
                        # 根据PE调整
                        if pe and pe > 100:
                            take_profit_pct *= 0.7
                        elif pe and pe <= 30:
                            take_profit_pct *= 1.2
                        
                        if advice.get('stop_loss', 0) == 0:
                            advice['stop_loss'] = round(current_price * (1 + stop_loss_pct), 2)
                        if advice.get('take_profit', 0) == 0:
                            advice['take_profit'] = round(current_price * (1 + take_profit_pct), 2)
                        if advice.get('risk_reward_ratio', 0) == 0:
                            risk = current_price - advice.get('stop_loss', current_price * 0.05)
                            reward = advice.get('take_profit', current_price * 1.15) - current_price
                            advice['risk_reward_ratio'] = round(reward / risk, 2) if risk > 0 else 0
        
        if not advice_list:
            print("⚠️ 未能解析出有效的建议，返回空列表")
            advice_list = []
            
    except Exception as e:
        print(f"❌ ReAct Agent执行失败: {e}")
        advice_list = []

    return {
        "day_trading_coach_advice": advice_list,
        "context_notes": ["🥋 打板教练(ReAct)完成深度分析"],
        "next_action": "TO_FINALIZER"
    }

# =======================
# 📝 Node 5: 最终报告生成器
# =======================
def node_finalize_report(state: ResearchState) -> ResearchState:
    coach_advice = [a for a in state.get("day_trading_coach_advice", []) if isinstance(a, dict) and "code" in a]

    # 格式化打板教练建议，与report.md保持一致
    if coach_advice:
        coach_summary_parts = []
        for a in coach_advice[:100]:
            stock_summary = f"""
🎯 {a['name']} ({a['code']})
- **操作建议**：{a['action']}
- **理想买点**：{a['entry_point']}
- **止损价**：{a.get('stop_loss', '?')} 元
- **目标价**：{a.get('take_profit', '?')} 元
- **风险收益比**：{a.get('risk_reward_ratio', '?')}
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
