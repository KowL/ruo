"""
策略师节点

负责结合涨停分布、连板情况和市场情绪，判断主线方向与操作策略
"""

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm_agent.state import ResearchState
import os


def node_strategist(state: ResearchState, llm=None) -> ResearchState:
    """策略师分析节点"""
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