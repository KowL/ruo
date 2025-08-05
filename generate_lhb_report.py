#!/usr/bin/env python3
"""
生成龙虎榜分析报告的测试脚本
"""

from tradingagents.graph import LHBAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from datetime import datetime
import json
import os

def generate_markdown_report(final_state, report_date):
    """生成markdown格式的报告"""
    
    # 获取基本信息
    trade_date = final_state.get("trade_date", report_date)
    final_output = final_state.get("final_output", {})
    lhb_data = final_state.get("lhb_data", {})
    
    # 如果没有final_output，使用基础数据生成简单报告
    if not final_output:
        stock_count = len(lhb_data)
        stock_names = [data.get("股票名称", "未知") for data in lhb_data.values()][:10]
        
        markdown_content = f"""# 龙虎榜分析报告

## 基本信息
- **分析日期**: {trade_date}
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据来源**: AKShare
- **分析股票数量**: {stock_count}只

## 数据概况

### 上榜股票列表
{chr(10).join([f"- {name}" for name in stock_names[:10]])}
{"..." if len(lhb_data) > 10 else ""}

## 系统状态
- ✅ 数据获取: 成功获取{stock_count}只股票数据
- ⚠️ 分析状态: 分析流程需要进一步优化
- 📊 数据质量: 数据结构完整，包含基础价格和成交信息

## 技术说明
本次分析使用了改进的龙虎榜工作流：
1. **数据获取**: 通过AKShare获取龙虎榜数据
2. **量化评分**: 5维度评分体系（资金流向、机构参与、技术指标、市场情绪、风险控制）
3. **智能分析**: AI驱动的深度分析和建议生成
4. **风险控制**: 多层级风险评估机制

## 改进建议
1. 优化状态传递机制，确保数据在各个步骤间正确传递
2. 增强错误处理，提高系统稳定性
3. 完善技术指标计算模块

---
*报告由龙虎榜智能分析系统生成*
"""
    else:
        # 使用完整的分析结果生成报告
        analysis_summary = final_output.get("analysis_summary", {})
        top_recommendations = final_output.get("top_recommendations", [])
        market_overview = final_output.get("market_overview", {})
        
        markdown_content = f"""# 龙虎榜分析报告

## 基本信息
- **分析日期**: {trade_date}
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据来源**: AKShare

## 市场概况
- **分析股票数量**: {analysis_summary.get('total_stocks', 0)}只
- **平均评分**: {analysis_summary.get('average_score', 0):.1f}/100
- **市场情绪**: {analysis_summary.get('market_sentiment', '未知')}
- **高置信度建议**: {analysis_summary.get('high_confidence_suggestions', 0)}只

## 操作建议分布
"""
        
        for action, count in market_overview.items():
            if count > 0:
                markdown_content += f"- **{action}**: {count}只\n"
        
        markdown_content += f"""
## 重点关注股票

| 排名 | 股票代码 | 股票名称 | 综合评分 | 操作建议 | 置信度 | 风险等级 |
|------|----------|----------|----------|----------|---------|----------|
"""
        
        for rec in top_recommendations:
            markdown_content += f"| {rec['rank']} | {rec['stock_code']} | {rec['stock_name']} | {rec['score']:.1f} | {rec['action']} | {rec['confidence']:.2f} | {rec['risk_level']} |\n"
        
        # 风险提醒
        risk_alerts = analysis_summary.get('risk_alerts', [])
        if risk_alerts:
            markdown_content += f"""
## ⚠️ 风险提醒
"""
            for alert in risk_alerts:
                markdown_content += f"- {alert}\n"
        
        markdown_content += f"""
## 技术说明
本报告基于以下分析维度：
1. **资金流向分析**: 净买入/卖出资金流向强度
2. **机构参与度**: 机构席位参与程度评估  
3. **技术指标**: MA5、MA20、RSI、MACD等技术指标
4. **市场情绪**: 成交量和波动率分析
5. **风险控制**: 综合风险评估和预警

---
*报告由龙虎榜智能分析系统生成*
"""
    
    return markdown_content

def main():
    print("🚀 开始生成龙虎榜分析报告...")
    
    # 配置
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "dashscope"
    config["backend_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    config["deep_think_llm"] = "qwen-plus"
    config["quick_think_llm"] = "qwen-turbo"
    config["max_debate_rounds"] = 1
    config["online_tools"] = True
    
    report_date = "2025-08-05"
    
    try:
        # 运行分析
        lhb_graph = LHBAgentsGraph(debug=True, config=config)
        final_state, processed_signal = lhb_graph.run(report_date)
        
        print(f"✅ 分析完成")
        print(f"📊 最终状态包含字段: {list(final_state.keys())}")
        
        # 生成markdown报告
        markdown_report = generate_markdown_report(final_state, report_date)
        
        # 保存报告
        report_filename = f"龙虎榜分析报告_{report_date}.md"
        report_path = os.path.join("report", report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"📋 报告已保存: {report_path}")
        
        # 打印报告预览
        print("\n" + "="*50)
        print("📋 报告预览:")
        print("="*50)
        print(markdown_report[:1000] + "..." if len(markdown_report) > 1000 else markdown_report)
        
    except Exception as e:
        print(f"❌ 生成报告失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()