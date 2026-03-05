#!/usr/bin/env python3
"""
测试脚本：单独运行node_day_trading_coach函数
使用2025-12-09的缓存数据
"""

import json
import pickle
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_agent.agents.day_trading_coach import node_day_trading_coach
from app.llm_agent.llm_factory import create_llm

def load_cached_state(date: str):
    """加载缓存的状态数据"""
    cache_dir = Path("cache/daily_research") / date
    state_file = cache_dir / "state.json"

    if not state_file.exists():
        print(f"❌ 缓存文件不存在: {state_file}")
        return None

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"✅ 成功加载缓存数据: {date}")
        return state
    except Exception as e:
        print(f"❌ 加载缓存失败: {e}")
        return None

def test_node_day_trading_coach():
    """测试node_day_trading_coach函数"""
    date = "2025-12-16"

    print("=" * 60)
    print(f"🧪 开始测试node_day_trading_coach")
    print(f"📅 使用日期: {date}")
    print("=" * 60)

    # 加载缓存状态
    state = load_cached_state(date)
    if not state:
        return False

    # 提取必要的数据
    required_fields = ['raw_limit_ups', 'lhb_data', 'f10_data', 'date']
    for field in required_fields:
        if field not in state:
            print(f"❌ 缓存数据中缺少必要字段: {field}")
            return False

    # 准备测试状态
    test_state = {
        'date': state['date'],
        'raw_limit_ups': state['raw_limit_ups'],
        'lhb_data': state['lhb_data'],
        'f10_data': state['f10_data'],
        'data_officer_report': state.get('data_officer_report', ''),
        'strategist_thinking': state.get('strategist_thinking', ''),
        'risk_controller_alerts': state.get('risk_controller_alerts', []),
        'day_trading_coach_advice': [],  # 这将被函数填充
        'final_report': '',
        'context_notes': [],
        'next_action': 'TO_DAY_TRADING_COACH',
        'error': None
    }

    # 打印输入数据概览
    print(f"📊 输入数据概览:")
    print(f"   - 涨停股票数量: {len(test_state['raw_limit_ups'])}")
    print(f"   - 龙虎榜记录数量: {len(test_state['lhb_data'])}")
    print(f"   - F10数据数量: {len(test_state['f10_data'])}")
    print()

    try:
        # 创建 LLM 实例
        print("🤖 正在创建 LLM 实例...")
        llm = create_llm(temperature=0.6)

        # 调用node_day_trading_coach函数
        print("🤖 正在调用node_day_trading_coach...")
        print("-" * 60)

        result = node_day_trading_coach(test_state, llm)

        print("-" * 60)
        print("✅ node_day_trading_coach执行完成！")
        print()

        # 打印结果
        advice_list = result.get('day_trading_coach_advice', [])
        print(f"📋 分析结果:")
        print(f"   - 生成的建议数量: {len(advice_list)}")
        print()

        if advice_list:
            print("=" * 60)
            print("🎯 详细的打板建议:")
            print("=" * 60)

            for idx, advice in enumerate(advice_list, 1):
                print(f"\n{idx}. {advice.get('name', '未知')} ({advice.get('code', '未知')})")
                print(f"   ├─ 操作建议: {advice.get('action', '无')}")
                print(f"   ├─ 梯队地位: {advice.get('tier_rank', '无')}")
                print(f"   ├─ 情绪周期: {advice.get('mood_cycle', '无')}")
                print(f"   ├─ 买点描述: {advice.get('entry_point', '无')}")
                print(f"   ├─ 止损价: {advice.get('stop_loss', '无')}元")
                print(f"   ├─ 目标价: {advice.get('take_profit', '无')}元")
                print(f"   ├─ 风险收益比: {advice.get('risk_reward_ratio', '无')}")
                print(f"   ├─ 风险信号: {advice.get('risk_signal', '无')}")
                print(f"   └─ 逻辑说明: {advice.get('reason', '无')}")
        else:
            print("⚠️ 没有生成任何建议")

        # 打印上下文笔记
        context_notes = result.get('context_notes', [])
        if context_notes:
            print("\n" + "=" * 60)
            print("📝 上下文笔记:")
            for note in context_notes:
                print(f"   - {note}")

        return True

    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_node_day_trading_coach()
    sys.exit(0 if success else 1)
