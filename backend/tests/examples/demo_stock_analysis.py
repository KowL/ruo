"""
股票分析工作流完整示例
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from graph.stock_analysis_workflow import (
    analyze_specified_stocks,
    analyze_filtered_stocks,
    analyze_mixed_stocks
)

def demo_specified_stocks():
    """演示指定股票分析"""
    print("🎯 演示：指定股票分析")
    print("=" * 50)

    # 分析几只知名股票
    stock_codes = ["002792", "000905", "000592", "600151", "603601", "002149"]
    print(f"分析股票: {', '.join(stock_codes)}")

    try:
        result = analyze_specified_stocks(stock_codes)

        if result.get("success"):
            print("✅ 分析成功!")

            # 显示基本信息
            print(f"\n📊 基本信息:")
            print(f"- 分析ID: {result['analysis_id']}")
            print(f"- 分析日期: {result['date']}")
            print(f"- 分析类型: {result['analysis_type']}")

            # 显示选中股票
            selected_stocks = result.get('selected_stocks', [])
            print(f"\n📈 选中股票 ({len(selected_stocks)}只):")
            for stock in selected_stocks:
                print(f"- {stock['name']}({stock['code']})")
                print(f"  价格: {stock['price']}元, 涨跌: {stock['change_pct']:.2f}%")
                print(f"  换手率: {stock['turnover_rate']:.2f}%, 市值: {stock['market_cap']/1e8:.1f}亿")

            # 显示投资决策
            decisions = result.get('investment_decisions', [])
            print(f"\n💡 投资决策:")
            for decision in decisions:
                print(f"\n🏷️ {decision['stock_name']}({decision['stock_code']})")
                print(f"   推荐: {decision['recommendation']} (信心: {decision['confidence_level']:.1f}%)")
                print(f"   目标价: {decision['target_price']}元, 止损: {decision['stop_loss']}元")
                print(f"   风险等级: {decision['risk_level']}, 建议仓位: {decision['position_size']}")

                if decision['key_reasons']:
                    print(f"   投资理由: {decision['key_reasons'][0]}")
                if decision['risk_warnings']:
                    print(f"   风险提示: {decision['risk_warnings'][0]}")

            # 显示报告摘要
            final_report = result.get('final_report', '')
            if final_report:
                lines = final_report.split('\n')
                print(f"\n📋 报告摘要:")
                for line in lines[:10]:  # 显示前10行
                    if line.strip() and not line.startswith('#'):
                        print(f"   {line}")

        else:
            print(f"❌ 分析失败: {result.get('error')}")

    except Exception as e:
        print(f"❌ 演示异常: {str(e)}")

def demo_filtered_stocks():
    """演示条件筛选分析"""
    print("\n\n🔍 演示：条件筛选分析")
    print("=" * 50)

    # 设置筛选条件
    filter_conditions = {
        "market_cap_min": 100,     # 最小市值100亿
        "market_cap_max": 1000,    # 最大市值1000亿
        "change_pct_min": 2,       # 涨幅大于2%
        "change_pct_max": 10,      # 涨幅小于10%
        "turnover_rate_min": 3,    # 换手率大于3%
        "max_stocks": 3,           # 最多3只股票
        "exclude_st": True         # 排除ST股票
    }

    print("筛选条件:")
    for key, value in filter_conditions.items():
        print(f"- {key}: {value}")

    try:
        result = analyze_filtered_stocks(filter_conditions)

        if result.get("success"):
            print("\n✅ 筛选分析成功!")
            print(f"筛选说明: {result.get('filter_summary')}")

            # 显示筛选结果
            selected_stocks = result.get('selected_stocks', [])
            print(f"\n📈 筛选结果 ({len(selected_stocks)}只):")
            for stock in selected_stocks:
                print(f"- {stock['name']}({stock['code']})")
                print(f"  价格: {stock['price']}元, 涨跌: {stock['change_pct']:.2f}%")
                print(f"  换手率: {stock['turnover_rate']:.2f}%, 市值: {stock['market_cap']/1e8:.1f}亿")
                print(f"  板块: {stock['sector']}")

            # 显示推荐买入的股票
            decisions = result.get('investment_decisions', [])
            buy_decisions = [d for d in decisions if d['recommendation'] in ['强烈买入', '买入']]

            if buy_decisions:
                print(f"\n🎯 推荐买入 ({len(buy_decisions)}只):")
                for decision in buy_decisions:
                    print(f"- {decision['stock_name']}: {decision['recommendation']}")
                    print(f"  目标价: {decision['target_price']}元, 信心: {decision['confidence_level']:.1f}%")

        else:
            print(f"❌ 筛选分析失败: {result.get('error')}")

    except Exception as e:
        print(f"❌ 演示异常: {str(e)}")

def demo_mixed_analysis():
    """演示混合分析"""
    print("\n\n🔀 演示：混合分析")
    print("=" * 50)

    # 指定股票 + 筛选条件
    stock_codes = ["000001"]  # 指定平安银行
    filter_conditions = {
        "market_cap_min": 50,
        "change_pct_min": 1,
        "max_stocks": 2,
        "exclude_st": True
    }

    print(f"指定股票: {', '.join(stock_codes)}")
    print("筛选条件: 市值>50亿, 涨幅>1%, 最多2只")

    try:
        result = analyze_mixed_stocks(stock_codes, filter_conditions)

        if result.get("success"):
            print("\n✅ 混合分析成功!")
            print(f"筛选说明: {result.get('filter_summary')}")

            selected_stocks = result.get('selected_stocks', [])
            print(f"\n📈 最终选择 ({len(selected_stocks)}只):")
            for stock in selected_stocks:
                print(f"- {stock['name']}({stock['code']}): {stock['change_pct']:.2f}%")

        else:
            print(f"❌ 混合分析失败: {result.get('error')}")

    except Exception as e:
        print(f"❌ 演示异常: {str(e)}")

def main():
    """主演示函数"""
    print("🚀 股票分析工作流完整演示")
    print("=" * 60)

    print("\n📋 工作流包含以下分析模块:")
    print("1. 股票筛选器 - 根据条件筛选或处理指定股票")
    print("2. 板块分析师 - 分析股票所属板块的整体情况")
    print("3. 短线分析师 - 分析短期技术指标和资金流向")
    print("4. 技术分析师 - 深度技术分析(K线、指标、形态)")
    print("5. 舆论分析师 - 分析市场情绪和新闻舆论")
    print("6. 投资决策者 - 综合所有分析给出最终建议")

    # 演示指定股票分析
    demo_specified_stocks()

    # 演示条件筛选分析
    # demo_filtered_stocks()

    # 演示混合分析
    # demo_mixed_analysis()

    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("\n💡 使用提示:")
    print("1. 可以通过修改筛选条件来获取不同类型的股票")
    print("2. 工作流会自动进行多维度分析并给出投资建议")
    print("3. 每个分析结果都包含详细的理由和风险提示")
    print("4. 支持指定股票、条件筛选、混合分析三种模式")

if __name__ == "__main__":
    main()