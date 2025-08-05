from typing import Dict, Any, List
from datetime import date
import pandas as pd
import logging
import traceback
from tradingagents.dataflows.akshare_utils import get_stock_lhb_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lhb_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def safe_execute(func_name: str, func, *args, **kwargs):
    """安全执行函数，包含错误处理和日志记录
    
    Args:
        func_name: 函数名称
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或错误信息
    """
    try:
        logger.info(f"开始执行 {func_name}")
        result = func(*args, **kwargs)
        logger.info(f"{func_name} 执行成功")
        return result
    except Exception as e:
        error_msg = f"{func_name} 执行失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 返回包含错误信息的状态，保持原有状态数据
        if args and isinstance(args[0], dict):
            state = args[0].copy()
            state["error"] = {
                "function": func_name,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            # 确保必要的字段存在
            if func_name == "fetch_lhb_data" and "lhb_data" not in state:
                state["lhb_data"] = {}
            elif func_name == "analyze_lhb_data" and "analysis_result" not in state:
                state["analysis_result"] = {}
            elif func_name == "generate_lhb_suggestion" and "suggestions" not in state:
                state["suggestions"] = []
            return state
        return {"error": {"function": func_name, "message": str(e)}}

def calculate_stock_score(data: Dict[str, Any]) -> Dict[str, float]:
    """计算股票综合评分
    
    Args:
        data: 龙虎榜数据
        
    Returns:
        各项评分字典
    """
    scores = {}
    
    # 1. 资金流向评分 (0-100)
    net_flow_ratio = data.get("资金流向强度", 0)
    if net_flow_ratio > 0.3:
        scores["资金流向"] = 90
    elif net_flow_ratio > 0.1:
        scores["资金流向"] = 70
    elif net_flow_ratio > 0:
        scores["资金流向"] = 50
    elif net_flow_ratio > -0.1:
        scores["资金流向"] = 30
    else:
        scores["资金流向"] = 10
    
    # 2. 机构参与评分 (0-100)
    inst_participation = data.get("机构参与度", 0)
    inst_net_amount = data.get("机构净买额", 0)
    if inst_participation > 0.5 and inst_net_amount > 0:
        scores["机构参与"] = 90
    elif inst_participation > 0.3:
        scores["机构参与"] = 70
    elif inst_participation > 0.1:
        scores["机构参与"] = 50
    else:
        scores["机构参与"] = 30
    
    # 3. 技术指标评分 (0-100)
    tech_indicators = data.get("技术指标", {})
    tech_score = 50  # 默认中性
    
    if tech_indicators:
        ma5 = tech_indicators.get("ma5")
        ma20 = tech_indicators.get("ma20") 
        rsi = tech_indicators.get("rsi")
        close_price = data.get("收盘价", 0)
        
        # 均线判断
        if ma5 and ma20 and close_price:
            if close_price > ma5 > ma20:
                tech_score += 20  # 多头排列
            elif close_price < ma5 < ma20:
                tech_score -= 20  # 空头排列
        
        # RSI判断
        if rsi:
            if 30 <= rsi <= 70:
                tech_score += 10  # RSI健康
            elif rsi > 80:
                tech_score -= 15  # 超买
            elif rsi < 20:
                tech_score += 15  # 超卖反弹机会
    
    scores["技术指标"] = max(0, min(100, tech_score))
    
    # 4. 市场情绪评分 (0-100)
    change_pct = abs(data.get("涨跌幅", 0))
    analysis_indicators = data.get("分析指标", {})
    
    sentiment_score = 50
    if analysis_indicators.get("成交活跃", False):
        sentiment_score += 20
    if change_pct > 7:
        sentiment_score += 15  # 强势突破
    elif change_pct < 3:
        sentiment_score -= 10  # 缺乏动能
    
    scores["市场情绪"] = max(0, min(100, sentiment_score))
    
    # 5. 风险评分 (0-100, 数值越高风险越低)
    risk_score = 60  # 默认中等风险
    
    # ST股票已被过滤
    if change_pct > 9.5:
        risk_score -= 30  # 接近涨停，风险较高
    elif change_pct < -7:
        risk_score -= 20  # 大幅下跌，风险较高
    
    if analysis_indicators.get("机构净流入", False):
        risk_score += 20  # 机构资金降低风险
    
    scores["风险控制"] = max(0, min(100, risk_score))
    
    # 计算综合评分
    weights = {
        "资金流向": 0.3,
        "机构参与": 0.25, 
        "技术指标": 0.2,
        "市场情绪": 0.15,
        "风险控制": 0.1
    }
    
    total_score = sum(scores[key] * weights[key] for key in scores.keys())
    scores["综合评分"] = round(total_score, 2)
    
    return scores

def fetch_lhb_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取龙虎榜数据"""
    def _fetch_data(state):
        trade_date = state["trade_date"]
        logger.info(f"开始获取龙虎榜数据，日期: {trade_date}")
        
        # 获取龙虎榜数据
        lhb_data = get_stock_lhb_data(trade_date)
        
        if not lhb_data:
            logger.warning(f"未获取到 {trade_date} 的龙虎榜数据")
            state["lhb_data"] = {}
            return state
        
        logger.info(f"原始数据包含 {len(lhb_data)} 只股票")
        
        # 过滤ST股票
        filtered_lhb_data = {
            code: data 
            for code, data in lhb_data.items() 
            if not any(prefix in data["股票名称"] for prefix in ("ST", "*ST"))
        }
        
        logger.info(f"过滤ST股票后剩余 {len(filtered_lhb_data)} 只股票")
        
        # 更新状态
        state["lhb_data"] = filtered_lhb_data
        return state
    
    return safe_execute("fetch_lhb_data", _fetch_data, state)

def analyze_lhb_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """分析龙虎榜数据"""
    def _analyze_data(state):
        if "error" in state:
            logger.warning("检测到上游错误，跳过分析步骤")
            return state
        
        # 确保lhb_data存在
        if "lhb_data" not in state:
            logger.warning("状态中缺少lhb_data字段")
            state["analysis_result"] = {}
            return state
            
        lhb_data = state["lhb_data"]
        deep_thinking_llm = state["llm"]["deep_thinking"]
        
        if not lhb_data:
            logger.warning("没有可分析的龙虎榜数据")
            state["analysis_result"] = {}
            return state
        
        logger.info(f"开始分析 {len(lhb_data)} 只股票")
        
        analysis_results = {}
        successful_count = 0
        failed_count = 0
        
        for stock_code, data in lhb_data.items():
            try:
                logger.info(f"分析股票: {data['股票名称']}({stock_code})")
                
                # 计算量化评分
                scores = calculate_stock_score(data)
                
                # 构建分析提示（简化版，避免过长）
                prompt = f"""请分析以下龙虎榜数据：

股票：{data['股票名称']}({stock_code})
收盘价：{data['收盘价']} 涨跌幅：{data['涨跌幅']}%
净买额：{data['龙虎榜净买额']:,.0f}万元
资金流向强度：{data.get('资金流向强度', 0):.2%}
机构参与度：{data.get('机构参与度', 0):.2%}

量化评分：
- 资金流向：{scores['资金流向']}/100
- 机构参与：{scores['机构参与']}/100  
- 技术指标：{scores['技术指标']}/100
- 市场情绪：{scores['市场情绪']}/100
- 风险控制：{scores['风险控制']}/100
- 综合评分：{scores['综合评分']}/100

请提供简要分析，包括：
1. 主要优势和风险
2. 后市预判
3. 操作建议

要求：简洁明了，突出要点。"""
                
                # 使用LLM分析
                response = deep_thinking_llm.invoke(prompt)
                
                analysis_results[stock_code] = {
                    "raw_data": data,
                    "quantitative_scores": scores,
                    "analysis": response.content,
                    "综合评分": scores["综合评分"]
                }
                
                successful_count += 1
                logger.info(f"股票 {stock_code} 分析完成，评分: {scores['综合评分']}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"分析股票 {stock_code} 失败: {str(e)}")
                # 继续处理其他股票
                continue
        
        logger.info(f"分析完成: 成功 {successful_count} 只，失败 {failed_count} 只")
        
        # 按综合评分排序
        sorted_results = dict(sorted(
            analysis_results.items(), 
            key=lambda x: x[1]["综合评分"], 
            reverse=True
        ))
        
        # 更新状态
        state["analysis_result"] = sorted_results
        return state
    
    return safe_execute("analyze_lhb_data", _analyze_data, state)

def generate_lhb_suggestion(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成龙虎榜分析建议"""
    def _generate_suggestions(state):
        if "error" in state:
            logger.warning("检测到上游错误，跳过建议生成步骤")
            return state
        
        # 确保analysis_result存在
        if "analysis_result" not in state:
            logger.warning("状态中缺少analysis_result字段")
            state["suggestions"] = []
            return state
            
        analysis_result = state["analysis_result"]
        quick_thinking_llm = state["llm"]["quick_thinking"]
        
        if not analysis_result:
            logger.warning("没有可生成建议的分析结果")
            state["suggestions"] = []
            return state
        
        suggestions = []
        
        for stock_code, result in analysis_result.items():
            try:
                # 生成量化建议
                quantitative_suggestion = generate_trading_suggestion(
                    result["quantitative_scores"], 
                    result["raw_data"]
                )
                
                # 构建LLM验证提示（简化版）
                prompt = f"""验证交易建议：

股票：{result['raw_data']['股票名称']}({stock_code})
量化建议：{quantitative_suggestion['操作建议']}
置信度：{quantitative_suggestion['置信度']}
风险等级：{quantitative_suggestion['风险等级']}

分析结果：{result['analysis'][:500]}...

请简要验证并补充：
1. 是否同意量化建议？
2. 操作时机建议
3. 风险提醒

要求简洁专业。"""
                
                # 使用LLM验证和补充
                response = quick_thinking_llm.invoke(prompt)
                
                suggestions.append({
                    "stock_code": stock_code,
                    "stock_name": result['raw_data']['股票名称'],
                    "quantitative_suggestion": quantitative_suggestion,
                    "llm_validation": response.content,
                    "综合评分": result["综合评分"],
                    "final_recommendation": {
                        "action": quantitative_suggestion["操作建议"],
                        "confidence": quantitative_suggestion["置信度"],
                        "risk_level": quantitative_suggestion["风险等级"],
                        "reasons": quantitative_suggestion["决策依据"]
                    }
                })
                
            except Exception as e:
                logger.error(f"生成股票 {stock_code} 建议失败: {str(e)}")
                continue
        
        # 按综合评分排序
        suggestions.sort(key=lambda x: x["综合评分"], reverse=True)
        
        # 更新状态
        state["suggestions"] = suggestions
        return state
    
    return safe_execute("generate_lhb_suggestion", _generate_suggestions, state)

def generate_trading_suggestion(scores: Dict[str, float], data: Dict[str, Any]) -> Dict[str, Any]:
    """基于量化评分生成交易建议
    
    Args:
        scores: 量化评分
        data: 原始数据
        
    Returns:
        交易建议字典
    """
    综合评分 = scores["综合评分"]
    资金流向分 = scores["资金流向"]
    机构参与分 = scores["机构参与"]
    技术指标分 = scores["技术指标"]
    风险控制分 = scores["风险控制"]
    
    # 决策逻辑
    if 综合评分 >= 75:
        if 资金流向分 >= 70 and 机构参与分 >= 60 and 风险控制分 >= 50:
            action = "强烈买入"
            confidence = 0.85
            risk_level = "中低"
        else:
            action = "买入"
            confidence = 0.7
            risk_level = "中"
    elif 综合评分 >= 60:
        if 技术指标分 >= 60 and 风险控制分 >= 60:
            action = "谨慎买入"
            confidence = 0.6
            risk_level = "中"
        else:
            action = "持有观望"
            confidence = 0.5
            risk_level = "中"
    elif 综合评分 >= 40:
        action = "持有观望"
        confidence = 0.4
        risk_level = "中高"
    else:
        if 资金流向分 < 30 or 风险控制分 < 40:
            action = "减仓"
            confidence = 0.7
            risk_level = "高"
        else:
            action = "观望"
            confidence = 0.5
            risk_level = "高"
    
    # 特殊情况调整
    涨跌幅 = abs(data.get("涨跌幅", 0))
    if 涨跌幅 > 9:  # 接近涨停
        if action in ["强烈买入", "买入"]:
            action = "谨慎买入"
            confidence *= 0.8
            risk_level = "高"
    
    机构净买额 = data.get("机构净买额", 0)
    if 机构净买额 < -10000000:  # 机构大幅净卖出超过1亿
        if action in ["强烈买入", "买入", "谨慎买入"]:
            action = "观望"
            confidence *= 0.6
    
    return {
        "操作建议": action,
        "置信度": round(confidence, 2),
        "风险等级": risk_level,
        "评分详情": scores,
        "决策依据": {
            "综合评分": 综合评分,
            "主要优势": _get_strengths(scores),
            "主要风险": _get_risks(scores, data),
            "关键指标": {
                "资金流向": f"{data.get('资金流向强度', 0):.2%}",
                "机构参与": f"{data.get('机构参与度', 0):.2%}", 
                "净买额": f"{data.get('龙虎榜净买额', 0):,.0f}万元",
                "涨跌幅": f"{data.get('涨跌幅', 0):.2f}%"
            }
        }
    }

def _get_strengths(scores: Dict[str, float]) -> List[str]:
    """获取主要优势"""
    strengths = []
    if scores["资金流向"] >= 70:
        strengths.append("资金净流入强劲")
    if scores["机构参与"] >= 70:
        strengths.append("机构积极参与")
    if scores["技术指标"] >= 70:
        strengths.append("技术面向好")
    if scores["市场情绪"] >= 70:
        strengths.append("市场情绪积极")
    return strengths or ["无明显优势"]

def _get_risks(scores: Dict[str, float], data: Dict[str, Any]) -> List[str]:
    """获取主要风险"""
    risks = []
    if scores["风险控制"] < 50:
        risks.append("风险控制评分偏低")
    if scores["资金流向"] < 40:
        risks.append("资金流出压力")
    if abs(data.get("涨跌幅", 0)) > 8:
        risks.append("价格波动剧烈")
    if data.get("机构净买额", 0) < -5000000:
        risks.append("机构资金撤离")
    
    # 检查技术指标风险
    tech_indicators = data.get("技术指标", {})
    if tech_indicators.get("rsi") and tech_indicators["rsi"] > 80:
        risks.append("技术指标超买")
    
    return risks or ["风险可控"]

def output_lhb_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """输出最终的龙虎榜分析结果"""
    def _output_result(state):
        # 确保suggestions存在
        if "suggestions" not in state:
            logger.warning("状态中缺少suggestions字段")
            state["suggestions"] = []
        
        suggestions = state["suggestions"]
        
        if not suggestions:
            logger.warning("没有可输出的建议结果")
            final_output = {
                "trade_date": state.get("trade_date", "未知"),
                "analysis_summary": {
                    "total_stocks": 0,
                    "average_score": 0,
                    "market_sentiment": "无数据",
                    "high_confidence_suggestions": 0,
                    "action_distribution": {},
                    "risk_alerts": ["无数据可分析"]
                },
                "top_recommendations": [],
                "detailed_suggestions": [],
                "market_overview": {}
            }
            state["final_output"] = final_output
            return state
        
        # 统计各类建议数量
        action_counts = {}
        total_score = 0
        high_confidence_count = 0
        
        for suggestion in suggestions:
            action = suggestion["final_recommendation"]["action"]
            confidence = suggestion["final_recommendation"]["confidence"]
            score = suggestion["综合评分"]
            
            action_counts[action] = action_counts.get(action, 0) + 1
            total_score += score
            
            if confidence >= 0.7:
                high_confidence_count += 1
        
        # 计算平均评分
        avg_score = total_score / len(suggestions) if suggestions else 0
        
        # 生成市场概况
        market_sentiment = "谨慎"
        if avg_score >= 70:
            market_sentiment = "积极"
        elif avg_score >= 50:
            market_sentiment = "中性"
        
        # 筛选高评分股票（前3名或评分>70的）
        top_picks = [s for s in suggestions if s["综合评分"] >= 70][:3]
        if not top_picks:
            top_picks = suggestions[:3]
        
        # 风险提醒
        risk_alerts = []
        high_risk_count = len([s for s in suggestions if s["final_recommendation"]["risk_level"] == "高"])
        if high_risk_count > len(suggestions) * 0.5:
            risk_alerts.append("超过半数股票风险等级较高，建议谨慎操作")
        
        low_confidence_count = len([s for s in suggestions if s["final_recommendation"]["confidence"] < 0.5])
        if low_confidence_count > len(suggestions) * 0.3:
            risk_alerts.append("多只股票建议置信度偏低，市场不确定性较大")
        
        # 格式化输出
        final_output = {
            "trade_date": state.get("trade_date", "未知"),
            "analysis_summary": {
                "total_stocks": len(suggestions),
                "average_score": round(avg_score, 2),
                "market_sentiment": market_sentiment,
                "high_confidence_suggestions": high_confidence_count,
                "action_distribution": action_counts,
                "risk_alerts": risk_alerts
            },
            "top_recommendations": [
                {
                    "rank": i + 1,
                    "stock_code": pick["stock_code"],
                    "stock_name": pick["stock_name"],
                    "score": pick["综合评分"],
                    "action": pick["final_recommendation"]["action"],
                    "confidence": pick["final_recommendation"]["confidence"],
                    "risk_level": pick["final_recommendation"]["risk_level"],
                    "key_reasons": pick["final_recommendation"]["reasons"]["主要优势"][:2]
                }
                for i, pick in enumerate(top_picks)
            ],
            "detailed_suggestions": suggestions,
            "market_overview": {
                "强烈买入": action_counts.get("强烈买入", 0),
                "买入": action_counts.get("买入", 0),
                "谨慎买入": action_counts.get("谨慎买入", 0),
                "持有观望": action_counts.get("持有观望", 0),
                "观望": action_counts.get("观望", 0),
                "减仓": action_counts.get("减仓", 0)
            }
        }
        
        # 更新状态
        state["final_output"] = final_output
        
        # 打印简要报告
        print(f"\n=== 龙虎榜分析报告 ({state.get('trade_date', '未知')}) ===")
        print(f"📊 分析股票数量: {len(suggestions)}")
        print(f"📈 平均评分: {avg_score:.1f}")
        print(f"🎯 市场情绪: {market_sentiment}")
        print(f"⭐ 高置信度建议: {high_confidence_count}")
        
        print(f"\n🔥 操作建议分布:")
        for action, count in action_counts.items():
            print(f"  {action}: {count}只")
        
        if top_picks:
            print(f"\n🏆 重点关注 (前{len(top_picks)}名):")
            for i, pick in enumerate(top_picks):
                print(f"  {i+1}. {pick['stock_name']}({pick['stock_code']}) - 评分:{pick['综合评分']:.1f} - {pick['final_recommendation']['action']}")
        
        if risk_alerts:
            print(f"\n⚠️  风险提醒:")
            for alert in risk_alerts:
                print(f"  • {alert}")
        
        return state
    
    return safe_execute("output_lhb_result", _output_result, state) 