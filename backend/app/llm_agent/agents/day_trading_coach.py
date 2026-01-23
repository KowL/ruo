"""
短线龙头助手节点

使用 ReAct Agent 进行深度分析，输出详细的投资建议
"""

import json
import os
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from state import ResearchState
from tools import safe_parse_json
from .tools import analyze_candidate_stocks, get_stock_lhb_data, calculate_risk_reward, analyze_lhb_data


def node_day_trading_coach(state: ResearchState, llm=None) -> ResearchState:
    """使用ReAct Agent的短线龙头助手，输出详细思考过程"""

    # 如果没有传入 LLM，则使用默认初始化
    if llm is None:
        llm = ChatOpenAI(
            model="deepseek-v3-1-terminus",
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
            openai_api_key=os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        )

    # 构建候选池
    all_candidates = []
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

        all_candidates.append({
            "code": code,
            "name": name,
            "limit_time": s.get("首次封板时间", "未知"),
            "is_lianban": s.get("连板数", 0) > 1,
            "lianban_count": s.get("连板数", 0),
            "turnover_rate": s.get("换手率", 0),
            "volume_ratio": 1.0,  # 量比列不存在，使用默认值
            "concept": s.get("所属行业", ""),
            "pe": pe,
            "current_price": current_price  # 添加当前价格
        })

    # 优先选择连板股和高换手率股票，限制总数量以避免AI处理过载
    priority_candidates = []

    # 1. 所有连板股（按连板数排序）
    lianban_stocks = [c for c in all_candidates if c['is_lianban']]
    lianban_stocks.sort(key=lambda x: x['lianban_count'], reverse=True)
    priority_candidates.extend(lianban_stocks[:10])  # 最多10只连板股

    # 2. 高换手率首板股（>15%）
    high_turnover_stocks = [c for c in all_candidates
                           if not c['is_lianban'] and c['turnover_rate'] > 15]
    high_turnover_stocks.sort(key=lambda x: x['turnover_rate'], reverse=True)
    priority_candidates.extend(high_turnover_stocks[:8])  # 最多8只高换手率首板股

    # 3. 其他首板股（换手率5-15%）
    other_stocks = [c for c in all_candidates
                   if not c['is_lianban'] and 5 <= c['turnover_rate'] <= 15]
    other_stocks.sort(key=lambda x: x['turnover_rate'], reverse=True)
    priority_candidates.extend(other_stocks[:7])  # 最多7只其他首板股

    # 去重（基于股票代码）
    seen_codes = set()
    candidates = []
    for candidate in priority_candidates:
        if candidate['code'] not in seen_codes:
            candidates.append(candidate)
            seen_codes.add(candidate['code'])

    print(f"📊 候选股票筛选：总数{len(all_candidates)} -> 优选{len(candidates)}")
    print(f"   连板股: {len([c for c in candidates if c['is_lianban']])}只")
    print(f"   高换手率首板股: {len([c for c in candidates if not c['is_lianban'] and c['turnover_rate'] > 15])}只")

    try:
        # 创建ReAct Agent
        system_prompt = """你是一名经验丰富的A 股短线情绪龙头助手，精通龙头战法 6 大维度：题材强度、身位、盘口强度、梯队地位、情绪周期、风险信号。

**重要：你必须完成完整的分析流程，并在最后输出标准的JSON数组格式结果。**

你的分析流程：
1. 首先使用analyze_candidate_stocks工具分析候选股票池，了解整体情况
2. 对于重点关注的股票，使用get_stock_lhb_data工具查询其龙虎榜数据
3. 使用calculate_risk_reward工具计算重点股票的风险收益比
4. 如需了解整体市场情况，可使用analyze_lhb_data工具
5. **最后必须输出JSON数组格式的投资建议**

分析重点：
- 优先关注连板股和高换手率股票
- 对重点股票深入分析其龙虎榜数据，识别主力资金参与情况
- **重要**：对于每只重点股票，必须使用calculate_risk_reward工具计算止损价和目标价
- 优先推荐有主力资金参与且技术面强势的标的
- 针对所有连板股输出操作建议

**最终输出要求：**
你必须在分析完成后，输出一个JSON数组，每个元素包含以下字段：
```json
[
  {
    "code": "股票代码",
    "name": "股票名称",
    "tier_rank": "龙头/跟风/独立",
    "mood_cycle": "冰点/回暖/主升/高潮/退潮",
    "action": "可打板/关注/观望/回避",
    "entry_point": "买点描述",
    "stop_loss": 止损价格数值,
    "take_profit": 目标价格数值,
    "risk_signal": "风险信号描述",
    "risk_reward_ratio": 风险收益比数值,
    "reason": "逻辑说明（不超过30字）"
  }
]
```

**注意：**
- 如果没有合适的打板标的，输出空数组 []
- 必须确保输出的是有效的JSON格式
- 不要在JSON前后添加任何说明文字
- 完成工具调用后，直接输出JSON数组

请开始你的分析。"""

        # 创建Agent
        agent = create_agent(
            llm,
            tools=[analyze_candidate_stocks, get_stock_lhb_data, calculate_risk_reward, analyze_lhb_data],
            system_prompt=system_prompt
        )

        # 准备输入数据 - 不再限制数据量
        candidates_str = json.dumps(candidates, ensure_ascii=False, default=str)

        user_query = f"""请分析以下候选股票池并给出操作建议：

候选股票池（共{len(candidates)}只）：
{candidates_str}

龙虎榜数据已准备就绪，可以通过get_stock_lhb_data工具查询任何股票的龙虎榜信息。

分析日期：{state['date']}

请严格按照你的分析流程执行：
1. 先使用analyze_candidate_stocks分析候选股票池的整体情况
2. 对重点关注的股票（特别是连板股），使用get_stock_lhb_data查询其龙虎榜数据
3. 对重点股票使用calculate_risk_reward计算风险收益比、止损价和目标价
4. **最后必须输出JSON数组格式的投资建议**

**重要提醒：**
- 完成所有工具调用后，你必须输出一个JSON数组
- 如果没有合适的打板标的，输出空数组 []
- 不要输出任何解释文字，只输出JSON数组
- 确保JSON格式正确，可以被解析

现在开始分析："""
        print("🤖 短线龙头助手开始分析...")

        response = agent.invoke({
            "messages": [HumanMessage(content=user_query)]
        })

        # 打印工具使用（从消息历史中提取）
        for message in response["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    print(f"Tool: {tool_call.get('name', 'unknown')}")
                    print(f"Args: {tool_call.get('args', {})}")
                    print(f"ID: {tool_call.get('id', '')}")
                    print("-" * 40)

        # 提取最终的AI消息
        final_message = ""
        thinking_process = []

        for message in response["messages"]:
            if isinstance(message, AIMessage):
                thinking_process.append(f"🤔 思考: {message.content}")
                final_message = message.content

        # 打印思考过程
        print("\n" + "="*50)
        print("🧠 短线龙头助手思考过程：")
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
        "context_notes": ["🥋 短线龙头助手(ReAct)完成深度分析"],
        "next_action": "TO_FINALIZER"
    }