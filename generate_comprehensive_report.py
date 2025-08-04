#!/usr/bin/env python3
"""
直接从数据生成龙虎榜分析报告
"""

from tradingagents.dataflows.akshare_utils import get_stock_lhb_data
from tradingagents.agents.analysts.lhb_nodes import calculate_stock_score, generate_trading_suggestion
from datetime import datetime
import json
import os

def analyze_single_stock(stock_code, stock_data):
    """分析单只股票"""
    try:
        # 计算量化评分
        scores = calculate_stock_score(stock_data)
        
        # 生成交易建议
        suggestion = generate_trading_suggestion(scores, stock_data)
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_data["股票名称"],
            "scores": scores,
            "suggestion": suggestion,
            "raw_data": stock_data
        }
    except Exception as e:
        print(f"分析股票 {stock_code} 失败: {e}")
        return None

def generate_comprehensive_report(analysis_results, report_date):
    """生成完整的分析报告"""
    
    # 统计信息
    total_stocks = len(analysis_results)
    avg_score = sum([r["scores"]["综合评分"] for r in analysis_results]) / total_stocks if total_stocks > 0 else 0
    
    # 按评分排序
    sorted_results = sorted(analysis_results, key=lambda x: x["scores"]["综合评分"], reverse=True)
    
    # 统计操作建议
    action_counts = {}
    high_confidence_count = 0
    
    for result in analysis_results:
        action = result["suggestion"]["操作建议"]
        confidence = result["suggestion"]["置信度"]
        
        action_counts[action] = action_counts.get(action, 0) + 1
        if confidence >= 0.7:
            high_confidence_count += 1
    
    # 生成市场情绪
    market_sentiment = "谨慎"
    if avg_score >= 70:
        market_sentiment = "积极"
    elif avg_score >= 50:
        market_sentiment = "中性"
    
    # 筛选重点股票
    top_stocks = sorted_results[:5]
    
    # 风险股票
    risk_stocks = [r for r in analysis_results if r["suggestion"]["风险等级"] == "高"]
    
    markdown_content = f"""# 龙虎榜分析报告

## 📊 基本信息
- **分析日期**: {report_date}
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据来源**: AKShare
- **分析股票数量**: {total_stocks}只
- **平均评分**: {avg_score:.1f}/100
- **市场情绪**: {market_sentiment}
- **高置信度建议**: {high_confidence_count}只

## 🔥 操作建议分布

| 操作建议 | 数量 | 占比 |
|----------|------|------|
"""
    
    for action, count in action_counts.items():
        percentage = (count / total_stocks * 100) if total_stocks > 0 else 0
        markdown_content += f"| {action} | {count}只 | {percentage:.1f}% |\n"
    
    markdown_content += f"""
## 🏆 重点关注股票（前5名）

| 排名 | 股票代码 | 股票名称 | 综合评分 | 操作建议 | 置信度 | 风险等级 | 涨跌幅 |
|------|----------|----------|----------|----------|---------|----------|--------|
"""
    
    for i, stock in enumerate(top_stocks, 1):
        markdown_content += f"| {i} | {stock['stock_code']} | {stock['stock_name']} | {stock['scores']['综合评分']:.1f} | {stock['suggestion']['操作建议']} | {stock['suggestion']['置信度']:.2f} | {stock['suggestion']['风险等级']} | {stock['raw_data']['涨跌幅']:.2f}% |\n"
    
    # 详细分析重点股票
    markdown_content += f"""
## 📈 重点股票详细分析

"""
    
    for i, stock in enumerate(top_stocks[:3], 1):  # 只详细分析前3名
        raw_data = stock["raw_data"]
        scores = stock["scores"]
        suggestion = stock["suggestion"]
        reasons = suggestion["决策依据"]
        
        markdown_content += f"""### {i}. {stock['stock_name']}({stock['stock_code']})

**基本信息**
- 收盘价: {raw_data['收盘价']}元
- 涨跌幅: {raw_data['涨跌幅']:.2f}%
- 龙虎榜净买额: {raw_data['龙虎榜净买额']:,.0f}万元
- 资金流向强度: {raw_data.get('资金流向强度', 0):.2%}
- 机构参与度: {raw_data.get('机构参与度', 0):.2%}

**量化评分**
- 资金流向: {scores['资金流向']}/100
- 机构参与: {scores['机构参与']}/100
- 技术指标: {scores['技术指标']}/100  
- 市场情绪: {scores['市场情绪']}/100
- 风险控制: {scores['风险控制']}/100
- **综合评分: {scores['综合评分']}/100**

**操作建议**
- 建议操作: **{suggestion['操作建议']}**
- 置信度: {suggestion['置信度']:.2f}
- 风险等级: {suggestion['风险等级']}

**主要优势**
{chr(10).join([f"- {advantage}" for advantage in reasons.get('主要优势', [])])}

**主要风险**  
{chr(10).join([f"- {risk}" for risk in reasons.get('主要风险', [])])}

---
"""
    
    # 风险提醒
    if risk_stocks:
        markdown_content += f"""
## ⚠️ 高风险股票提醒

以下股票风险等级较高，请谨慎操作：

| 股票代码 | 股票名称 | 综合评分 | 风险等级 | 主要风险 |
|----------|----------|----------|----------|----------|
"""
        for stock in risk_stocks[:5]:  # 只显示前5只高风险股票
            risks = stock["suggestion"]["决策依据"].get("主要风险", ["未知风险"])
            main_risk = risks[0] if risks else "未知风险"
            markdown_content += f"| {stock['stock_code']} | {stock['stock_name']} | {stock['scores']['综合评分']:.1f} | {stock['suggestion']['风险等级']} | {main_risk} |\n"
    
    # 市场总结
    markdown_content += f"""
## 📋 市场总结

### 整体表现
- 本日共有 {total_stocks} 只股票登上龙虎榜
- 平均综合评分 {avg_score:.1f} 分，市场情绪偏{market_sentiment}
- 高置信度操作建议占比 {(high_confidence_count/total_stocks*100):.1f}%

### 资金流向特征
"""
    
    # 统计资金流向
    net_inflow_count = len([r for r in analysis_results if r["raw_data"]["龙虎榜净买额"] > 0])
    strong_inflow_count = len([r for r in analysis_results if r["scores"]["资金流向"] >= 70])
    
    markdown_content += f"""- 净流入股票: {net_inflow_count}只 ({net_inflow_count/total_stocks*100:.1f}%)
- 资金流向强劲股票: {strong_inflow_count}只 ({strong_inflow_count/total_stocks*100:.1f}%)

### 机构参与情况
"""
    
    # 统计机构参与
    inst_active_count = len([r for r in analysis_results if r["scores"]["机构参与"] >= 60])
    markdown_content += f"""- 机构积极参与股票: {inst_active_count}只 ({inst_active_count/total_stocks*100:.1f}%)

## 🔧 技术说明

本报告基于改进的龙虎榜智能分析系统生成，包含以下核心功能：

### 量化评分体系
1. **资金流向分析** (权重30%): 基于净买入/卖出资金计算流向强度
2. **机构参与评估** (权重25%): 评估机构席位参与程度和资金规模  
3. **技术指标分析** (权重20%): MA5、MA20、RSI等技术指标综合判断
4. **市场情绪评估** (权重15%): 成交量和价格波动率分析
5. **风险控制评估** (权重10%): 多维度风险评估和预警

### 决策逻辑
- **强烈买入**: 综合评分≥75，且资金流向、机构参与、风险控制均达标
- **买入**: 综合评分≥75，但部分指标存在风险
- **谨慎买入**: 综合评分60-75，技术面和风险控制良好
- **持有观望**: 综合评分40-60，市场信号不明确
- **观望**: 综合评分<40，存在较多不确定因素
- **减仓**: 资金流出或风险控制评分过低

---
**免责声明**: 本报告基于公开数据和量化模型生成，仅供参考，不构成具体投资建议。投资有风险，决策需谨慎。

*报告由龙虎榜智能分析系统v2.0生成*
"""
    
    return markdown_content

def main():
    print("🚀 开始生成龙虎榜综合分析报告...")
    
    report_date = "2025-08-01"
    
    try:
        # 1. 获取龙虎榜数据
        print("📊 获取龙虎榜数据...")
        lhb_data = get_stock_lhb_data(report_date)
        
        if not lhb_data:
            print("❌ 未获取到龙虎榜数据")
            return
        
        print(f"✅ 成功获取 {len(lhb_data)} 只股票数据")
        
        # 2. 分析每只股票
        print("🔍 开始量化分析...")
        analysis_results = []
        
        for stock_code, stock_data in lhb_data.items():
            result = analyze_single_stock(stock_code, stock_data)
            if result:
                analysis_results.append(result)
        
        print(f"✅ 完成 {len(analysis_results)} 只股票分析")
        
        # 3. 生成报告
        print("📋 生成分析报告...")
        markdown_report = generate_comprehensive_report(analysis_results, report_date)
        
        # 4. 保存报告
        report_filename = f"龙虎榜综合分析报告_{report_date}.md"
        report_path = os.path.join("report", report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"📋 报告已保存: {report_path}")
        
        # 5. 保存JSON数据供后续分析
        json_filename = f"龙虎榜分析数据_{report_date}.json"
        json_path = os.path.join("report", json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 数据已保存: {json_path}")
        
        # 6. 打印简要统计
        total_stocks = len(analysis_results)
        avg_score = sum([r["scores"]["综合评分"] for r in analysis_results]) / total_stocks if total_stocks > 0 else 0
        high_score_count = len([r for r in analysis_results if r["scores"]["综合评分"] >= 70])
        
        print(f"\n📈 分析统计:")
        print(f"  总股票数: {total_stocks}")
        print(f"  平均评分: {avg_score:.1f}/100")
        print(f"  高分股票: {high_score_count}只 ({high_score_count/total_stocks*100:.1f}%)")
        
        # 显示前3名
        top_3 = sorted(analysis_results, key=lambda x: x["scores"]["综合评分"], reverse=True)[:3]
        print(f"  前3名:")
        for i, stock in enumerate(top_3, 1):
            print(f"    {i}. {stock['stock_name']}({stock['stock_code']}) - {stock['scores']['综合评分']:.1f}分 - {stock['suggestion']['操作建议']}")
        
    except Exception as e:
        print(f"❌ 生成报告失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()