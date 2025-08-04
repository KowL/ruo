#!/usr/bin/env python3
"""
龙虎榜分析回测验证模块
用于验证分析建议的有效性
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
from tradingagents.dataflows.akshare_utils import get_akshare_provider

logger = logging.getLogger(__name__)

class LHBBacktestValidator:
    """龙虎榜分析回测验证器"""
    
    def __init__(self):
        self.ak_provider = get_akshare_provider()
        
    def validate_suggestions(self, suggestions: List[Dict[str, Any]], days_ahead: int = 1) -> Dict[str, Any]:
        """验证建议的准确性
        
        Args:
            suggestions: 龙虎榜分析建议列表
            days_ahead: 验证后续几天的表现
            
        Returns:
            验证结果字典
        """
        if not suggestions:
            return {"error": "没有建议需要验证"}
        
        results = {
            "total_suggestions": len(suggestions),
            "validated_count": 0,
            "successful_predictions": 0,
            "accuracy_rate": 0.0,
            "average_return": 0.0,
            "detailed_results": [],
            "summary": {}
        }
        
        total_return = 0.0
        successful_count = 0
        
        for suggestion in suggestions:
            try:
                stock_code = suggestion["stock_code"]
                stock_name = suggestion["stock_name"]
                action = suggestion["final_recommendation"]["action"]
                confidence = suggestion["final_recommendation"]["confidence"]
                score = suggestion["综合评分"]
                
                # 获取后续股价数据验证
                validation_result = self._validate_single_stock(
                    stock_code, action, days_ahead
                )
                
                if validation_result:
                    results["validated_count"] += 1
                    
                    # 判断预测是否成功
                    is_successful = self._is_prediction_successful(
                        action, validation_result["return_rate"]
                    )
                    
                    if is_successful:
                        successful_count += 1
                    
                    total_return += validation_result["return_rate"]
                    
                    # 记录详细结果
                    results["detailed_results"].append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "predicted_action": action,
                        "confidence": confidence,
                        "score": score,
                        "actual_return": validation_result["return_rate"],
                        "is_successful": is_successful,
                        "days_validated": days_ahead
                    })
                    
            except Exception as e:
                logger.error(f"验证股票 {stock_code} 失败: {str(e)}")
                continue
        
        # 计算统计指标
        if results["validated_count"] > 0:
            results["successful_predictions"] = successful_count
            results["accuracy_rate"] = successful_count / results["validated_count"]
            results["average_return"] = total_return / results["validated_count"]
        
        # 生成总结
        results["summary"] = self._generate_summary(results)
        
        return results
    
    def _validate_single_stock(self, stock_code: str, action: str, days_ahead: int) -> Optional[Dict[str, Any]]:
        """验证单只股票的表现
        
        Args:
            stock_code: 股票代码
            action: 预测的操作
            days_ahead: 验证天数
            
        Returns:
            验证结果或None
        """
        try:
            # 计算验证期间的日期范围
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days_ahead + 5)  # 多取几天以防节假日
            
            # 获取股价数据
            stock_data = self.ak_provider.get_stock_data(
                stock_code,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if stock_data is None or stock_data.empty:
                return None
            
            # 计算收益率
            if len(stock_data) >= days_ahead + 1:
                start_price = stock_data.iloc[0]['收盘']
                end_price = stock_data.iloc[days_ahead]['收盘']
                return_rate = (end_price - start_price) / start_price
                
                return {
                    "start_price": start_price,
                    "end_price": end_price,
                    "return_rate": return_rate,
                    "days_actual": days_ahead
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 验证数据失败: {str(e)}")
            return None
    
    def _is_prediction_successful(self, action: str, actual_return: float) -> bool:
        """判断预测是否成功
        
        Args:
            action: 预测的操作
            actual_return: 实际收益率
            
        Returns:
            是否预测成功
        """
        # 定义成功标准
        if action in ["强烈买入", "买入", "谨慎买入"]:
            return actual_return > 0.02  # 买入建议要求至少2%收益
        elif action in ["减仓"]:
            return actual_return < -0.01  # 减仓建议要求下跌超过1%
        elif action in ["持有观望", "观望"]:
            return abs(actual_return) < 0.05  # 观望建议要求波动不大
        
        return False
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """生成验证总结
        
        Args:
            results: 验证结果
            
        Returns:
            总结字典
        """
        accuracy = results["accuracy_rate"]
        avg_return = results["average_return"]
        
        summary = {}
        
        # 准确率评估
        if accuracy >= 0.7:
            summary["accuracy_assessment"] = "优秀"
        elif accuracy >= 0.6:
            summary["accuracy_assessment"] = "良好"
        elif accuracy >= 0.5:
            summary["accuracy_assessment"] = "一般"
        else:
            summary["accuracy_assessment"] = "需要改进"
        
        # 收益评估
        if avg_return >= 0.05:
            summary["return_assessment"] = "收益良好"
        elif avg_return >= 0.02:
            summary["return_assessment"] = "收益一般"
        elif avg_return >= 0:
            summary["return_assessment"] = "收益微弱"
        else:
            summary["return_assessment"] = "出现亏损"
        
        # 整体评估
        if accuracy >= 0.6 and avg_return >= 0.02:
            summary["overall_assessment"] = "分析模型表现良好"
        elif accuracy >= 0.5 or avg_return >= 0:
            summary["overall_assessment"] = "分析模型表现一般，需要优化"
        else:
            summary["overall_assessment"] = "分析模型需要重大改进"
        
        return summary
    
    def save_validation_results(self, results: Dict[str, Any], filepath: str):
        """保存验证结果到文件
        
        Args:
            results: 验证结果
            filepath: 保存路径
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"验证结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存验证结果失败: {str(e)}")

def create_backtest_validator() -> LHBBacktestValidator:
    """创建回测验证器实例"""
    return LHBBacktestValidator()