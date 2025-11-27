import os
import json
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

# 加载密钥
load_dotenv()

# =======================
# 🧠 LLM 初始化（通义千问）
# =======================
llm = ChatTongyi(
    model="qwen-plus-latest",  # 推荐 qwen-plus 提升推理质量
    api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
    temperature=0.6,
)

# =======================
# 🧬 定义状态（State）
# =======================
class AnalysisState(TypedDict, total=False):
    """工作流状态字典"""
    yesterday_report: Optional[Any]  # pd.DataFrame
    limit_up_stocks: Optional[Any]  # pd.DataFrame - 昨日涨停股票
    coach_recommended: Optional[Any]  # pd.DataFrame - 打板教练建议股票
    today_opening_data: Optional[Any]  # pd.DataFrame
    merged_data: Optional[Any]  # pd.DataFrame
    coach_analysis: Optional[Dict[str, Any]]  # 打板教练股票特别分析
    general_analysis: Optional[Dict[str, Any]]  # 一般涨停股票分析
    final_report: Optional[str]
    error: Optional[str]

def read_yesterday_report(state: AnalysisState) -> AnalysisState:
    """读取昨日报告并筛选涨停股票"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        cache_dir = f'cache/daily_research/{yesterday}'
        report_path = os.path.join(cache_dir, "state.json")
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 转换为DataFrame
            if 'stocks' in report_data:
                df = pd.DataFrame(report_data['stocks'])
            else:
                df = pd.DataFrame(report_data)
            
            # 昨日涨停的股票 - 转换为DataFrame并标准化字段名
            raw_limit_ups = report_data.get('raw_limit_ups', [])
            if raw_limit_ups:
                limit_up_stocks = pd.DataFrame(raw_limit_ups)
                # 标准化字段名
                if '代码' in limit_up_stocks.columns:
                    limit_up_stocks.rename(columns={'代码': 'stock_code', '名称': 'stock_name', '涨跌幅': 'change_rate_yesterday'}, inplace=True)
                limit_up_stocks['stock_code'] = limit_up_stocks['stock_code'].astype(str).str.zfill(6)
            else:
                limit_up_stocks = pd.DataFrame()
            
            # 打板教练建议的涨停股票 - 转换为DataFrame
            coach_data = report_data.get('day_trading_coach_advice', [])
            if coach_data:
                coach_recommended = pd.DataFrame(coach_data)
                # 确保有stock_code字段
                if 'code' in coach_recommended.columns:
                    coach_recommended.rename(columns={'code': 'stock_code'}, inplace=True)
                if 'stock_code' in coach_recommended.columns:
                    coach_recommended['stock_code'] = coach_recommended['stock_code'].astype(str).str.zfill(6)
            else:
                coach_recommended = pd.DataFrame()
            
            print(f"✅ 成功读取昨日报告")
            print(f"📊 昨日涨停股票: {len(limit_up_stocks)} 只")
            print(f"🎯 打板教练建议股票: {len(coach_recommended)} 只")
            
            if len(limit_up_stocks) > 0:
                print("昨日涨停股票列表:")
                for _, stock in limit_up_stocks.head(5).iterrows():
                    print(f"  - {stock.get('stock_name', 'N/A')} ({stock.get('stock_code', 'N/A')})")
            
            return {
                **state,
                'yesterday_report': df,
                'limit_up_stocks': limit_up_stocks,
                'coach_recommended': coach_recommended,
                'error': None
            }
            
        else:
            error_msg = f"昨日报告文件 {report_path} 不存在"
            print(f"❌ {error_msg}")
            return {**state, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"读取昨日报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def get_today_opening_data(state: AnalysisState) -> AnalysisState:
    """获取今日竞价开盘数据，特别关注昨日涨停股票"""
    try:
        if state.get('error'):
            return state
            
        # 获取实时股票数据
        today_data = ak.stock_zh_a_spot_em()
        
        # 选择需要的列
        columns_needed = ['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额', '开盘价', '最高价', '最低价']
        available_columns = [col for col in columns_needed if col in today_data.columns]
        
        today_opening_data = today_data[available_columns].copy()
        today_opening_data.columns = [
            'stock_code', 'stock_name', 'current_price', 'change_rate', 
            'volume', 'amount', 'open_price', 'high_price', 'low_price'
        ]
        
        # 标准化股票代码格式
        today_opening_data['stock_code'] = today_opening_data['stock_code'].astype(str).str.zfill(6)
        
        print(f"✅ 成功获取今日开盘数据，共 {len(today_opening_data)} 只股票")
        
        return {**state, 'today_opening_data': today_opening_data, 'error': None}
        
    except Exception as e:
        error_msg = f"获取今日开盘数据失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def merge_and_analyze_data(state: AnalysisState) -> AnalysisState:
    """合并数据并进行分类分析"""
    try:
        if state.get('error') or state.get('limit_up_stocks') is None or state.get('today_opening_data') is None:
            return state
        
        limit_up_stocks = state['limit_up_stocks'].copy()
        today_opening_data = state['today_opening_data']
        
        # 确保股票代码格式一致
        limit_up_stocks['stock_code'] = limit_up_stocks['stock_code'].astype(str).str.zfill(6)
        
        # 合并昨日涨停股票与今日开盘数据
        merged_data = pd.merge(
            limit_up_stocks, 
            today_opening_data, 
            on='stock_code', 
            how='inner',
            suffixes=('_yesterday', '_today')
        )
        
        print(f"✅ 数据合并完成，共 {len(merged_data)} 只昨日涨停股票有今日数据")
        
        if len(merged_data) == 0:
            error_msg = "没有找到昨日涨停股票的今日开盘数据"
            return {**state, 'error': error_msg}
        
        # 分析打板教练建议的股票
        coach_stocks = pd.DataFrame()
        coach_recommended = state.get('coach_recommended')
        if coach_recommended is not None and len(coach_recommended) > 0:
            coach_codes = set(coach_recommended['stock_code'].astype(str).str.zfill(6))
            coach_stocks = merged_data[merged_data['stock_code'].isin(coach_codes)].copy()
        
        # 一般涨停股票（非打板教练建议）
        if len(coach_stocks) > 0:
            general_stocks = merged_data[~merged_data['stock_code'].isin(coach_stocks['stock_code'])].copy()
        else:
            general_stocks = merged_data.copy()
        
        # 打板教练股票分析
        coach_analysis = analyze_coach_stocks(coach_stocks)
        
        # 一般涨停股票分析
        general_analysis = analyze_general_stocks(general_stocks)
        
        print(f"🎯 打板教练股票分析完成: {len(coach_stocks)} 只")
        print(f"📊 一般涨停股票分析完成: {len(general_stocks)} 只")
        
        return {
            **state,
            'merged_data': merged_data,
            'coach_analysis': coach_analysis,
            'general_analysis': general_analysis,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"数据合并分析失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def analyze_coach_stocks(coach_stocks: pd.DataFrame) -> Dict:
    """分析打板教练建议的股票"""
    if len(coach_stocks) == 0:
        return {
            'count': 0,
            'summary': '今日无打板教练建议的涨停股票数据',
            'strong_continuation': [],
            'weak_continuation': [],
            'recommendations': []
        }
    
    analysis = {
        'count': len(coach_stocks),
        'strong_continuation': [],  # 强势连板
        'weak_continuation': [],    # 弱势调整
        'high_risk_high_reward': [], # 高风险高收益
        'recommendations': []
    }
    
    for _, stock in coach_stocks.iterrows():
        stock_analysis = {
            'code': stock['stock_code'],
            'name': stock.get('stock_name_yesterday', stock.get('stock_name_today', 'N/A')),
            'yesterday_change': stock.get('change_rate_yesterday', 0),
            'today_change': stock.get('change_rate', 0),
            'open_price': stock.get('open_price', 0),
            'current_price': stock.get('current_price', 0)
        }
        
        # 判断连板强度
        if stock_analysis['today_change'] > 3:  # 今日继续大涨
            stock_analysis['strength'] = '强势连板'
            stock_analysis['action'] = '重点关注，可考虑追涨'
            stock_analysis['risk_level'] = '中高风险'
            analysis['strong_continuation'].append(stock_analysis)
        
        elif stock_analysis['today_change'] > 0:  # 今日小幅上涨
            stock_analysis['strength'] = '温和上涨'
            stock_analysis['action'] = '持有观察，注意止盈'
            stock_analysis['risk_level'] = '中等风险'
            analysis['weak_continuation'].append(stock_analysis)
        
        else:  # 今日下跌
            stock_analysis['strength'] = '调整回调'
            stock_analysis['action'] = '谨慎观望，等待企稳'
            stock_analysis['risk_level'] = '高风险'
            analysis['high_risk_high_reward'].append(stock_analysis)
        
        analysis['recommendations'].append(stock_analysis)
    
    return analysis

def analyze_general_stocks(general_stocks: pd.DataFrame) -> Dict:
    """分析一般涨停股票"""
    if len(general_stocks) == 0:
        return {
            'count': 0,
            'summary': '今日无一般涨停股票数据',
            'continuation_rate': 0,
            'strong_stocks': [],
            'weak_stocks': []
        }
    
    # 计算连板率（今日继续上涨的股票比例）
    continuation_count = len(general_stocks[general_stocks['change_rate'] > 0])
    continuation_rate = continuation_count / len(general_stocks) * 100
    
    analysis = {
        'count': len(general_stocks),
        'continuation_rate': continuation_rate,
        'strong_stocks': [],  # 今日涨幅>2%
        'weak_stocks': [],    # 今日下跌
        'market_sentiment': ''
    }
    
    # 分类分析
    for _, stock in general_stocks.iterrows():
        stock_info = {
            'code': stock['stock_code'],
            'name': stock.get('stock_name_yesterday', stock.get('stock_name_today', 'N/A')),
            'yesterday_change': stock.get('change_rate_yesterday', 0),
            'today_change': stock.get('change_rate', 0),
            'action': ''
        }
        
        if stock_info['today_change'] > 2:
            stock_info['action'] = '强势延续，可关注'
            analysis['strong_stocks'].append(stock_info)
        else:
            stock_info['action'] = '走势疲软，谨慎'
            analysis['weak_stocks'].append(stock_info)
    
    # 市场情绪判断
    if continuation_rate > 60:
        analysis['market_sentiment'] = '强势市场，连板效应明显'
    elif continuation_rate > 40:
        analysis['market_sentiment'] = '中性市场，分化明显'
    else:
        analysis['market_sentiment'] = '弱势市场，获利了结压力大'
    
    return analysis

def ai_coach_analysis(state: AnalysisState) -> AnalysisState:
    """使用AI大模型对打板教练股票进行深度分析"""
    try:
        if state.get('error') or state.get('coach_analysis') is None:
            return state
        
        coach_analysis = state['coach_analysis']
        general_analysis = state.get('general_analysis', {})
        
        # 如果没有推荐股票，跳过AI分析
        if coach_analysis.get('count', 0) == 0 or len(coach_analysis.get('recommendations', [])) == 0:
            print("⚠️ 无打板教练建议股票，跳过AI分析")
            return state

        
        # 准备打板教练股票数据
        coach_data = coach_analysis['recommendations']
        
        prompt = f"""
        你是一名专业的打板策略分析师，请对以下打板教练昨日建议的涨停股票进行深度分析：

        ## 打板教练建议股票今日表现
        {json.dumps(coach_data, ensure_ascii=False, indent=2)}

        ## 市场环境参考
        - 一般涨停股票连板率: {general_analysis.get('continuation_rate', 0):.1f}%
        - 市场情绪: {general_analysis.get('market_sentiment', '未知')}

        ## 分析要求（重点）：
        1. **打板教练股票特别分析**：逐只分析每只股票的连板潜力和风险
        2. **操作策略建议**：针对每只股票给出具体的买入/持有/卖出建议
        3. **仓位管理**：建议的仓位配置和风险控制
        4. **连板概率评估**：评估每只股票继续涨停的概率
        5. **风险提示**：特别关注高开低走、获利盘压力等风险因素

        请以专业的打板分析报告格式回复，重点突出打板教练建议股票的特殊性。
        """
        
        messages = [
            SystemMessage(content="""你是一名顶级的打板策略专家，擅长分析涨停股票的连板潜力和风险控制。
            你的分析要专业、精准，特别关注打板教练建议股票的独特性和操作价值。"""),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # 将AI分析结果整合到教练分析中
        coach_analysis['ai_analysis'] = response.content
        print("✅ 打板教练股票AI分析完成")
        
        return {**state, 'coach_analysis': coach_analysis, 'error': None}
        
    except Exception as e:
        error_msg = f"打板教练股票AI分析失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def generate_final_report(state: AnalysisState) -> AnalysisState:
    """生成最终分析报告"""
    try:
        if state.get('error'):
            return state
        
        # 检查必要的分析数据是否存在
        coach_analysis = state.get('coach_analysis')
        general_analysis = state.get('general_analysis')
        
        if coach_analysis is None or general_analysis is None:
            error_msg = "缺少必要的分析数据，无法生成报告"
            print(f"❌ {error_msg}")
            return {**state, 'error': error_msg}
        
        report_parts = []
        
        # 报告标题
        today = datetime.now().strftime('%Y-%m-%d')
        report_parts.append(f"# 涨停股票开盘分析报告 - {today}")
        report_parts.append("=" * 60)
        
        # 市场概况
        report_parts.append("\n## 📊 市场概况")
        coach_count = coach_analysis.get('count', 0)
        general_count = general_analysis.get('count', 0)
        report_parts.append(f"- 昨日涨停股票总数: {coach_count + general_count}")
        report_parts.append(f"- 打板教练建议股票: {coach_count} 只")
        report_parts.append(f"- 一般涨停股票连板率: {general_analysis.get('continuation_rate', 0):.1f}%")
        report_parts.append(f"- 市场情绪: {general_analysis.get('market_sentiment', '未知')}")
        
        # 打板教练股票特别分析
        report_parts.append("\n## 🎯 打板教练建议股票特别分析")
        if coach_count > 0:
            strong_continuation = coach_analysis.get('strong_continuation', [])
            high_risk_high_reward = coach_analysis.get('high_risk_high_reward', [])
            
            report_parts.append(f"### 强势连板股票 ({len(strong_continuation)}只)")
            for stock in strong_continuation:
                report_parts.append(f"  - {stock['name']}({stock['code']}): 今日涨{stock['today_change']:.1f}% → {stock['action']}")
            
            report_parts.append(f"### 高风险高收益股票 ({len(high_risk_high_reward)}只)")
            for stock in high_risk_high_reward:
                report_parts.append(f"  - {stock['name']}({stock['code']}): 今日涨{stock['today_change']:.1f}% → {stock['action']}")
            
            # AI分析摘要
            if 'ai_analysis' in coach_analysis:
                ai_content = coach_analysis['ai_analysis']
                # 取前300字符作为摘要
                summary = ai_content[:300] + "..." if len(ai_content) > 300 else ai_content
                report_parts.append(f"\n### AI深度分析摘要")
                report_parts.append(summary)
        else:
            report_parts.append("今日无打板教练建议的涨停股票数据")
        
        # 一般涨停股票分析
        report_parts.append("\n## 📈 一般涨停股票分析")
        strong_stocks = general_analysis.get('strong_stocks', [])
        report_parts.append(f"### 强势股票 ({len(strong_stocks)}只)")
        if len(strong_stocks) > 0:
            for stock in strong_stocks[:5]:  # 只显示前5只
                report_parts.append(f"  - {stock['name']}({stock['code']}): 今日涨{stock['today_change']:.1f}%")
        else:
            report_parts.append("  暂无强势股票")
        
        # 操作建议总结
        report_parts.append("\n## 💡 操作建议总结")
        if coach_count > 0:
            report_parts.append("1. **重点关打板教练建议股票**，特别是强势连板品种")
            report_parts.append("2. **注意风险控制**，连板股票波动较大")
            report_parts.append("3. **结合市场情绪**调整仓位配置")
        else:
            report_parts.append("1. **关注一般涨停股票中的强势品种**")
            report_parts.append("2. **谨慎追涨**，注意市场整体情绪")
        
        final_report = "\n".join(report_parts)
        
        # 保存报告到文件
        cache_dir = f'cache/opening_analysis/{today}'
        os.makedirs(cache_dir, exist_ok=True)
        
        report_path = os.path.join(cache_dir, 'opening_analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(final_report)
        
        print(f"✅ 最终报告已生成并保存至: {report_path}")
        
        return {**state, 'final_report': final_report, 'error': None}
        
    except Exception as e:
        error_msg = f"生成最终报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def create_opening_analysis_workflow():
    """创建开盘分析工作流图"""
    workflow = StateGraph(AnalysisState)
    
    # 添加节点
    workflow.add_node("read_yesterday_report", read_yesterday_report)
    workflow.add_node("get_today_opening_data", get_today_opening_data)
    workflow.add_node("merge_and_analyze_data", merge_and_analyze_data)
    workflow.add_node("ai_coach_analysis", ai_coach_analysis)
    workflow.add_node("generate_final_report", generate_final_report)
    
    # 设置入口点
    workflow.set_entry_point("read_yesterday_report")
    
    # 添加边
    workflow.add_edge("read_yesterday_report", "get_today_opening_data")
    workflow.add_edge("get_today_opening_data", "merge_and_analyze_data")
    workflow.add_edge("merge_and_analyze_data", "ai_coach_analysis")
    workflow.add_edge("ai_coach_analysis", "generate_final_report")
    workflow.add_edge("generate_final_report", END)
    
    # 编译工作流
    app = workflow.compile()
    return app

def main():
    """主函数：运行开盘分析工作流"""
    print("=" * 60)
    print("🚀 启动涨停股票开盘分析工作流")
    print("=" * 60)
    
    try:
        # 创建工作流
        app = create_opening_analysis_workflow()
        
        # 初始化状态（字典格式）
        initial_state: AnalysisState = {
            'yesterday_report': None,
            'limit_up_stocks': None,
            'coach_recommended': None,
            'today_opening_data': None,
            'merged_data': None,
            'coach_analysis': None,
            'general_analysis': None,
            'final_report': None,
            'error': None
        }
        
        # 运行工作流
        final_state = app.invoke(initial_state)
        
        # 检查是否有错误
        if final_state.get('error'):
            print(f"\n❌ 工作流执行失败: {final_state['error']}")
            return
        
        # 输出最终报告
        if final_state.get('final_report'):
            print("\n" + "=" * 60)
            print("📄 最终分析报告")
            print("=" * 60)
            print(final_state['final_report'])
        
        print("\n✅ 工作流执行完成！")
        
    except Exception as e:
        print(f"\n❌ 工作流执行异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
