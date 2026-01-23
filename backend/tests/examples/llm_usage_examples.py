"""
LLM 使用示例

展示如何使用新的 LLM 管理功能进行不同场景的配置
"""

from agent.llm_factory import create_llm, get_shared_llm, reset_shared_llm
from graph import run_ai_research_analysis, create_research_graph


def example_1_basic_usage():
    """示例 1: 基本使用 - 使用默认共享 LLM"""
    print("📝 示例 1: 基本使用")

    # 直接使用，会自动使用共享的 LLM 实例
    result = run_ai_research_analysis('2025-12-09')
    print(f"✅ 使用默认 LLM 完成分析: {result['success']}")


def example_2_custom_llm():
    """示例 2: 使用自定义 LLM 配置"""
    print("\n📝 示例 2: 自定义 LLM 配置")

    # 创建保守型 LLM（低温度，更确定性的输出）
    conservative_llm = create_llm(
        temperature=0.1,
        model="deepseek-v3-1-terminus"
    )

    # 使用自定义 LLM 运行分析
    result = run_ai_research_analysis('2025-12-09', llm=conservative_llm)
    print(f"✅ 使用保守型 LLM 完成分析: {result['success']}")


def example_3_creative_llm():
    """示例 3: 使用创造性 LLM 配置"""
    print("\n📝 示例 3: 创造性 LLM 配置")

    # 创建创造型 LLM（高温度，更有创造性的输出）
    creative_llm = create_llm(
        temperature=0.9,
        model="deepseek-v3-1-terminus"
    )

    # 使用创造性 LLM 运行分析
    result = run_ai_research_analysis('2025-12-09', llm=creative_llm)
    print(f"✅ 使用创造型 LLM 完成分析: {result['success']}")


def example_4_ab_testing():
    """示例 4: A/B 测试不同的 LLM 配置"""
    print("\n📝 示例 4: A/B 测试不同配置")

    # 配置 A: 保守型
    llm_a = create_llm(temperature=0.2)

    # 配置 B: 平衡型
    llm_b = create_llm(temperature=0.6)

    # 分别测试两种配置
    result_a = run_ai_research_analysis('2025-12-09', llm=llm_a)
    result_b = run_ai_research_analysis('2025-12-09', llm=llm_b)

    print(f"✅ 配置 A (保守型) 结果: {result_a['success']}")
    print(f"✅ 配置 B (平衡型) 结果: {result_b['success']}")

    # 比较结果
    if result_a['success'] and result_b['success']:
        len_a = len(result_a['result'].get('strategist_thinking', ''))
        len_b = len(result_b['result'].get('strategist_thinking', ''))
        print(f"📊 策略师思考长度对比: A={len_a}, B={len_b}")


def example_5_shared_llm_management():
    """示例 5: 共享 LLM 实例管理"""
    print("\n📝 示例 5: 共享 LLM 管理")

    # 获取共享实例
    shared_llm_1 = get_shared_llm()
    shared_llm_2 = get_shared_llm()

    print(f"✅ 共享实例是同一个对象: {shared_llm_1 is shared_llm_2}")

    # 重置共享实例
    reset_shared_llm()
    shared_llm_3 = get_shared_llm()

    print(f"✅ 重置后是新实例: {shared_llm_1 is not shared_llm_3}")


def example_6_graph_level_llm():
    """示例 6: 图级别的 LLM 配置"""
    print("\n📝 示例 6: 图级别 LLM 配置")

    # 创建专门用于某个分析任务的 LLM
    analysis_llm = create_llm(
        temperature=0.4,
        model="deepseek-v3-1-terminus"
    )

    # 创建使用特定 LLM 的图
    graph = create_research_graph(analysis_llm)
    print("✅ 创建使用特定 LLM 的工作流图")

    # 这个图中的所有需要 LLM 的节点都会使用 analysis_llm


if __name__ == "__main__":
    print("🚀 LLM 管理功能使用示例")
    print("=" * 50)

    # 运行所有示例
    example_1_basic_usage()
    example_2_custom_llm()
    example_3_creative_llm()
    example_4_ab_testing()
    example_5_shared_llm_management()
    example_6_graph_level_llm()

    print("\n🎯 总结:")
    print("✅ LLM 实例现在可以灵活配置和管理")
    print("✅ 支持不同场景的参数优化")
    print("✅ 便于进行 A/B 测试和性能调优")
    print("✅ 统一的 LLM 管理，避免重复初始化")