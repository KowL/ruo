import os
import json
import pandas as pd
import akshare as ak
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, TypedDict
from dotenv import load_dotenv
import urllib3

from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

# 导入工具函数
from tools import get_stock_price_realtime, get_previous_trading_day

# 加载密钥
load_dotenv()

# 禁用 SSL 警告和代理（如果需要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    coach_recommended: Optional[Any]  # pd.DataFrame - 短线龙头助手建议股票
    today_opening_data: Optional[Any]  # pd.DataFrame
    merged_data: Optional[Any]  # pd.DataFrame
    coach_analysis: Optional[Dict[str, Any]]  # 短线龙头助手股票特别分析
    general_analysis: Optional[Dict[str, Any]]  # 昨日涨停股票分析
    final_report: Optional[str]
    error: Optional[str]

def read_yesterday_report(state: AnalysisState) -> AnalysisState:
    """读取昨日报告并筛选涨停股票（从数据库读取）"""
    try:
        from app.core.database import SessionLocal
        from app.models.stock import AnalysisReport
        
        # 使用获取上一个交易日的方法（跳过周末和节假日）
        yesterday_str = get_previous_trading_day()
        yesterday_date = datetime.strptime(yesterday_str, "%Y-%m-%d")
        
        print(f"🔄 正在尝试从数据库读取昨日({yesterday_str})的涨停分析报告...")
        
        db = SessionLocal()
        try:
            # 查询昨日的 limit-up 报告
            report = db.query(AnalysisReport).filter(
                AnalysisReport.symbol == "GLOBAL",
                AnalysisReport.report_date == yesterday_date,
                AnalysisReport.report_type == "limit-up"
            ).first()
            
            if report and report.data:
                report_data = json.loads(report.data)
                
                # 昨日涨停的股票 - 转换为DataFrame并标准化字段名
                raw_limit_ups = report_data.get('raw_limit_ups', [])
                if raw_limit_ups and isinstance(raw_limit_ups, list) and len(raw_limit_ups) > 0:
                    try:
                        limit_up_stocks = pd.DataFrame(raw_limit_ups)
                        # 标准化字段名
                        if '代码' in limit_up_stocks.columns:
                            limit_up_stocks.rename(columns={'代码': 'stock_code', '名称': 'stock_name', '涨跌幅': 'change_rate_yesterday'}, inplace=True)
                        if 'stock_code' in limit_up_stocks.columns:
                            limit_up_stocks['stock_code'] = limit_up_stocks['stock_code'].astype(str).str.zfill(6)
                    except Exception as e:
                        print(f"⚠️ 转换涨停股票数据失败: {e}")
                        limit_up_stocks = pd.DataFrame()
                else:
                    limit_up_stocks = pd.DataFrame()
                
                # 短线龙头助手建议的涨停股票 - 转换为DataFrame
                coach_data = report_data.get('day_trading_coach_advice', [])
                if coach_data and isinstance(coach_data, list) and len(coach_data) > 0:
                    try:
                        coach_recommended = pd.DataFrame(coach_data)
                        # 确保有stock_code字段
                        if 'code' in coach_recommended.columns:
                            coach_recommended.rename(columns={'code': 'stock_code'}, inplace=True)
                        if 'stock_code' in coach_recommended.columns:
                            coach_recommended['stock_code'] = coach_recommended['stock_code'].astype(str).str.zfill(6)
                    except Exception as e:
                        print(f"⚠️ 转换短线龙头助手数据失败: {e}")
                        coach_recommended = pd.DataFrame()
                else:
                    coach_recommended = pd.DataFrame()
                
                # 创建 yesterday_report（可选，主要用于兼容性）
                yesterday_report = None
                if 'stocks' in report_data and isinstance(report_data['stocks'], list):
                    try:
                        yesterday_report = pd.DataFrame(report_data['stocks'])
                    except Exception as e:
                        print(f"⚠️ 转换 stocks 数据失败: {e}")
                        yesterday_report = pd.DataFrame()
                
                print(f"✅ 成功从数据库读取昨日报告")
                print(f"📊 昨日涨停股票: {len(limit_up_stocks)} 只")
                print(f"🎯 短线龙头助手建议股票: {len(coach_recommended)} 只")
                
                if len(limit_up_stocks) > 0:
                    print("昨日涨停股票列表:")
                    for _, stock in limit_up_stocks.head(5).iterrows():
                        print(f"  - {stock.get('stock_name', 'N/A')} ({stock.get('stock_code', 'N/A')})")
                
                return {
                    **state,
                    'yesterday_report': yesterday_report if yesterday_report is not None else pd.DataFrame(),
                    'limit_up_stocks': limit_up_stocks,
                    'coach_recommended': coach_recommended,
                    'error': None
                }
                
            else:
                error_msg = f"数据库中未找到昨日({yesterday_str})的 limit-up 报告"
                print(f"❌ {error_msg}")
                return {**state, 'error': error_msg}
                
        finally:
            db.close()
        
    except Exception as e:
        error_msg = f"读取昨日报告失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}

def get_today_opening_data(state: AnalysisState) -> AnalysisState:
    """获取今日竞价开盘数据，特别关注昨日涨停股票（使用东方财富API）"""
    if state.get('error'):
        return state
    
    # 检查是否有昨日涨停股票数据
    limit_up_stocks = state.get('limit_up_stocks')
    if limit_up_stocks is None or len(limit_up_stocks) == 0:
        error_msg = "没有昨日涨停股票数据，无法获取今日开盘数据"
        print(f"❌ {error_msg}")
        return {**state, 'error': error_msg}
    
    print(f"🔄 开始获取 {len(limit_up_stocks)} 只昨日涨停股票的今日开盘数据...")
    
    # 获取股票代码列表
    stock_codes = limit_up_stocks['stock_code'].astype(str).str.zfill(6).tolist()
    # 获取股票名称，如果列不存在则使用空字符串列表
    if 'stock_name' in limit_up_stocks.columns:
        stock_names = limit_up_stocks['stock_name'].tolist()
    else:
        stock_names = [''] * len(stock_codes)
    
    # 存储获取到的数据
    opening_data_list = []
    failed_codes = []
    
    # 逐个获取股票实时数据
    for idx, stock_code in enumerate(stock_codes):
        try:
            # 调用东方财富API获取实时数据（带重试）
            realtime_data = get_stock_price_realtime(stock_code, retry_count=2)
            
            if realtime_data is None:
                failed_codes.append(stock_code)
                if idx < 3:  # 前3只失败时打印详细信息用于调试
                    print(f"  ⚠️ {stock_code} 数据获取失败（可能原因：API错误、网络问题或股票停牌）")
                continue
            
            # 构建数据记录（处理可能的None值和数据格式）
            def safe_get(value, default=0):
                """安全获取值，处理None值"""
                if value is None:
                    return default
                try:
                    return float(value) if float(value) != 0 else default
                except (ValueError, TypeError):
                    return default
            
            # 注意：API返回的数据已经是正确格式
            # - 价格：已经是元为单位
            # - 涨跌幅：已经是百分比
            # - 成交额：已经是元为单位
            record = {
                'stock_code': stock_code,
                'stock_name': stock_names[idx] if idx < len(stock_names) and stock_names[idx] else 'N/A',
                'current_price': safe_get(realtime_data.get('current')),  # 已经是元
                'change_rate': safe_get(realtime_data.get('change_rate')),  # 已经是百分比
                'volume': safe_get(realtime_data.get('volume')),  # 成交量（手）
                'amount': safe_get(realtime_data.get('amount')) / 10000,  # 转换为万元（API返回的是元）
                'open_price': safe_get(realtime_data.get('open')),  # 已经是元
                'high_price': safe_get(realtime_data.get('high')),  # 已经是元
                'low_price': safe_get(realtime_data.get('low')),  # 已经是元
            }
            
            opening_data_list.append(record)
            
            # 每10只股票显示一次进度
            if (idx + 1) % 10 == 0:
                print(f"  📊 已获取 {idx + 1}/{len(stock_codes)} 只股票数据...")
            
            # 添加小延迟，避免请求过快
            time.sleep(0.1)
            
        except Exception as e:
            print(f"⚠️ 获取 {stock_code} 数据失败: {str(e)[:50]}")
            failed_codes.append(stock_code)
            continue
    
    today_opening_data = pd.DataFrame(opening_data_list)
    
    # 标准化股票代码格式
    today_opening_data['stock_code'] = today_opening_data['stock_code'].astype(str).str.zfill(6)
    
    success_count = len(opening_data_list)
    print(f"✅ 成功获取今日开盘数据: {success_count}/{len(stock_codes)} 只股票")
    if failed_codes:
        print(f"⚠️ 失败股票代码: {', '.join(failed_codes[:5])}{'...' if len(failed_codes) > 5 else ''}")
    
    return {**state, 'today_opening_data': today_opening_data, 'error': None}

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
        
        if len(merged_data) == 0:
            error_msg = "没有找到昨日涨停股票的今日开盘数据"
            return {**state, 'error': error_msg}
        
        # 分析短线龙头助手建议的股票
        coach_stocks = pd.DataFrame()
        coach_recommended = state.get('coach_recommended')
        if coach_recommended is not None and len(coach_recommended) > 0:
            coach_codes = set(coach_recommended['stock_code'].astype(str).str.zfill(6))
            coach_stocks = merged_data[merged_data['stock_code'].isin(coach_codes)].copy()
        
        # 昨日涨停股票（包含所有昨日涨停股票，不排除短线龙头助手股票）
        all_limit_up_stocks = merged_data.copy()
        
        # 短线龙头助手股票分析
        coach_analysis = analyze_coach_stocks(coach_stocks)
        
        # 昨日涨停股票分析（包含所有股票）
        general_analysis = analyze_general_stocks(all_limit_up_stocks)
        
        print(f"🎯 短线龙头助手股票分析完成: {len(coach_stocks)} 只")
        print(f"📊 昨日涨停股票分析完成: {len(all_limit_up_stocks)} 只")
        
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
    """分析短线龙头助手建议的股票"""
    if len(coach_stocks) == 0:
        return {
            'count': 0,
            'summary': '今日无短线龙头助手建议的涨停股票数据',
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
    """分析昨日涨停股票"""
    if len(general_stocks) == 0:
        return {
            'count': 0,
            'summary': '今日无昨日涨停股票数据',
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
    """使用AI大模型对短线龙头助手股票进行深度分析"""
    try:
        if state.get('error') or state.get('coach_analysis') is None:
            return state
        
        coach_analysis = state['coach_analysis']
        general_analysis = state.get('general_analysis', {})
        
        # 如果没有推荐股票，跳过AI分析
        if coach_analysis.get('count', 0) == 0 or len(coach_analysis.get('recommendations', [])) == 0:
            print("⚠️ 无短线龙头助手建议股票，跳过AI分析")
            return state

        
        # 准备短线龙头助手股票数据
        coach_data = coach_analysis['recommendations']
        
        prompt = f"""
        你是一名专业的打板策略分析师，请对以下短线龙头助手昨日建议的涨停股票进行深度分析：

        ## 短线龙头助手建议股票今日表现
        {json.dumps(coach_data, ensure_ascii=False, indent=2)}

        ## 市场环境参考
        - 昨日涨停股票连板率: {general_analysis.get('continuation_rate', 0):.1f}%
        - 市场情绪: {general_analysis.get('market_sentiment', '未知')}

        ## 分析要求（重点）：
        1. **短线龙头助手股票特别分析**：逐只分析每只股票的连板潜力和风险
        2. **操作策略建议**：针对每只股票给出具体的买入/持有/卖出建议
        3. **仓位管理**：建议的仓位配置和风险控制
        4. **连板概率评估**：评估每只股票继续涨停的概率
        5. **风险提示**：特别关注高开低走、获利盘压力等风险因素

        请以专业的打板分析报告格式回复，重点突出短线龙头助手建议股票的特殊性。
        """
        
        messages = [
            SystemMessage(content="""你是一名顶级的打板策略专家，擅长分析涨停股票的连板潜力和风险控制。
            你的分析要专业、精准，特别关注短线龙头助手建议股票的独特性和操作价值。"""),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        # 将AI分析结果整合到教练分析中
        coach_analysis['ai_analysis'] = response.content
        print("✅ 短线龙头助手股票AI分析完成")
        
        return {**state, 'coach_analysis': coach_analysis, 'error': None}
        
    except Exception as e:
        error_msg = f"短线龙头助手股票AI分析失败: {str(e)}"
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
        
        # 从原始数据获取昨日涨停股票总数
        limit_up_stocks = state.get('limit_up_stocks')
        total_limit_up_count = len(limit_up_stocks) if limit_up_stocks is not None and len(limit_up_stocks) > 0 else 0
        
        # 从原始数据获取短线龙头助手建议股票数量
        coach_recommended = state.get('coach_recommended')
        total_coach_recommended_count = len(coach_recommended) if coach_recommended is not None and len(coach_recommended) > 0 else 0
        
        # 合并后有今日数据的股票数量
        coach_count = coach_analysis.get('count', 0)  # 短线龙头助手建议股票中有今日数据的数量
        
        report_parts.append(f"- 昨日涨停股票总数: {total_limit_up_count} 只")
        report_parts.append(f"- 短线龙头助手建议股票: {total_coach_recommended_count} 只（有今日数据: {coach_count} 只）")
        report_parts.append(f"- 昨日涨停股票连板率: {general_analysis.get('continuation_rate', 0):.1f}%")
        report_parts.append(f"- 市场情绪: {general_analysis.get('market_sentiment', '未知')}")
        
        # 短线龙头助手股票特别分析
        report_parts.append("\n## 🎯 短线龙头助手建议股票特别分析")
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
            report_parts.append("今日无短线龙头助手建议的涨停股票数据")
        
        # 昨日涨停股票分析
        report_parts.append("\n## 📈 昨日涨停股票分析")
        strong_stocks = general_analysis.get('strong_stocks', [])
        report_parts.append(f"### 强势股票 ({len(strong_stocks)}只)")
        if len(strong_stocks) > 0:
            for stock in strong_stocks:  
                report_parts.append(f"  - {stock['name']}({stock['code']}): 今日涨{stock['today_change']:.1f}%")
        else:
            report_parts.append("  暂无强势股票")
        
        # 操作建议总结
        report_parts.append("\n## 💡 操作建议总结")
        if coach_count > 0:
            report_parts.append("1. **重点关短线龙头助手建议股票**，特别是强势连板品种")
            report_parts.append("2. **注意风险控制**，连板股票波动较大")
            report_parts.append("3. **结合市场情绪**调整仓位配置")
        else:
            report_parts.append("1. **关注昨日涨停股票中的强势品种**")
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

def save_report_to_db(state: dict, date: str):
    """将分析结果持久化到数据库"""
    # 生成 Markdown 报告内容（用于兼容老版本或直接展示）
    md_content = state.get('final_report', '')
    if not md_content:
        # 如果没有生成报告，尝试重新构建
        pass

    # ✅ 数据库持久化
    try:
        from app.core.database import SessionLocal
        from app.models.stock import AnalysisReport
        
        # 统一日期格式处理
        report_date = datetime.strptime(date, "%Y-%m-%d")
        
        db = SessionLocal()
        try:
            # 检查是否已存在
            existing = db.query(AnalysisReport).filter(
                AnalysisReport.symbol == "GLOBAL",
                AnalysisReport.report_date == report_date,
                AnalysisReport.report_type == "opening_analysis"
            ).first()
            
            # 将完整的 state 序列化为 JSON 字符串存入 content
            state_json = json.dumps(state, ensure_ascii=False, indent=2, default=str)
            
            if existing:
                existing.content = md_content.strip()
                existing.data = state_json
                existing.summary = "开盘分析报告"
            else:
                new_report = AnalysisReport(
                    symbol="GLOBAL",
                    report_date=report_date,
                    report_type="opening_analysis",
                    content=md_content.strip(),
                    data=state_json,
                    summary="开盘分析报告",
                    confidence=1.0
                )
                db.add(new_report)
            
            db.commit()
            print(f"✅ 报告已同步到数据库: {date} (GLOBAL/opening_analysis)")
        except Exception as db_err:
            db.rollback()
            print(f"❌ 数据库保存失败: {db_err}")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 数据库保存异常: {e}")

def get_cached_report(date: str) -> dict:
    """从数据库获取已存在的分析报告"""
    try:
        from app.core.database import SessionLocal
        from app.models.stock import AnalysisReport
        
        report_date = datetime.strptime(date, "%Y-%m-%d")
        db = SessionLocal()
        try:
            report = db.query(AnalysisReport).filter(
                AnalysisReport.symbol == "GLOBAL",
                AnalysisReport.report_date == report_date,
                AnalysisReport.report_type == "opening_analysis"
            ).first()
            
            if report and report.data:
                try:
                    return json.loads(report.data)
                except:
                    return None
            return None
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 读取数据库缓存异常: {e}")
        return None

def run_opening_analysis(date: str, force_rerun: bool = False) -> dict:
    """
    启动开盘分析工作流
    """
    # ✅ 检查数据库缓存是否存在
    if not force_rerun:
        cached_state = get_cached_report(date)
        if cached_state:
            return {
                "success": True,
                "result": cached_state,
                "cached": True,
                "message": f"使用数据库缓存结果（{date}）"
            }

    # 🔁 否则执行完整分析流程
    try:
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
            return {
                "success": False,
                "error": final_state['error'],
                "message": f"工作流执行失败: {final_state['error']}"
            }
        
        # ✅ 执行完成后立即存入数据库
        save_report_to_db(final_state, date)

        return {
            "success": True,
            "result": final_state,
            "cached": False,
            "message": f"新生成报告并已存入数据库"
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "执行异常"
        }

def main():
    """主函数：测试运行"""
    print("=" * 60)
    print("🚀 启动涨停股票开盘分析工作流")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    result = run_opening_analysis(today, force_rerun=True)
    
    if result['success']:
        print("\n✅ 分析完成")
        if result['result'].get('final_report'):
             print(result['result']['final_report'][:500] + "...")
    else:
        print(f"\n❌ 分析失败: {result.get('error')}")

if __name__ == "__main__":
    main()
