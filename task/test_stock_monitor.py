#!/usr/bin/env python3
"""
股票监控系统测试脚本
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task.stock_monitor import (
    initialize_llm, 
    load_config, 
    get_portfolio_stocks,
    get_current_price,
    call_ai_agent,
    init_database
)

def test_stock_monitor():
    """测试股票监控系统功能"""
    print("🔧 测试股票监控系统...")
    
    # 初始化数据库
    init_database()
    print("✅ 数据库初始化完成")
    
    # 加载配置
    config = load_config()
    print(f"✅ 配置加载完成: {config.get('llm_provider')}")
    
    # 初始化LLM
    llm_instance = initialize_llm(config)
    if llm_instance:
        print(f"✅ LLM初始化成功: {config.get('llm_provider')} - {config.get('quick_think_llm')}")
    else:
        print("⚠️ LLM初始化失败，将使用简单规则")
    
    # 获取投资组合
    stocks = get_portfolio_stocks()
    print(f"✅ 获取投资组合: {len(stocks)} 只股票")
    
    if stocks:
        # 测试获取价格
        stock, name, hold_num, available, cost = stocks[0]
        print(f"📊 测试股票: {stock}({name})")
        
        current_price = get_current_price(stock)
        if current_price:
            print(f"✅ 获取价格成功: {current_price}")
            
            # 测试AI分析
            ai_response = call_ai_agent(
                stock, name, current_price, cost, 
                5.0, hold_num, available, cost, llm_instance
            )
            print(f"✅ AI分析完成: {ai_response}")
        else:
            print(f"❌ 无法获取 {stock} 的价格")
    else:
        print("⚠️ 没有找到投资组合数据")
    
    print("🎉 测试完成!")

if __name__ == "__main__":
    # 设置日志级别为INFO以显示详细信息
    logging.basicConfig(level=logging.INFO)
    test_stock_monitor()