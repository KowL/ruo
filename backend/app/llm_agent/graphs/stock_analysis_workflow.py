"""
股票分析工作流 - 主工作流文件
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any
import logging
from datetime import datetime
import uuid

# 导入状态定义
from app.llm_agent.state.stock_analysis_state import StockAnalysisState

# 导入各个节点
from app.llm_agent.agents.stock_filter import stock_filter_node
from app.llm_agent.agents.sector_analyst import sector_analyst_node
from app.llm_agent.agents.short_term_analyst import short_term_analyst_node
from app.llm_agent.agents.technical_analyst import technical_analyst_node
from app.llm_agent.agents.sentiment_analyst import sentiment_analyst_node
from app.llm_agent.agents.investment_decision_maker import investment_decision_maker_node

logger = logging.getLogger(__name__)

class StockAnalysisWorkflow:
    """股票分析工作流"""

    def __init__(self):
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        # 创建状态图
        workflow = StateGraph(StockAnalysisState)

        # 添加节点
        workflow.add_node("stock_filter", stock_filter_node)
        workflow.add_node("sector_analysis", sector_analyst_node)
        workflow.add_node("short_term_analysis", short_term_analyst_node)
        workflow.add_node("technical_analysis", technical_analyst_node)
        workflow.add_node("sentiment_analysis", sentiment_analyst_node)
        workflow.add_node("investment_decision", investment_decision_maker_node)

        # 设置入口点
        workflow.set_entry_point("stock_filter")

        # 添加边（定义节点之间的流转）
        workflow.add_edge("stock_filter", "sector_analysis")
        workflow.add_edge("sector_analysis", "short_term_analysis")
        workflow.add_edge("short_term_analysis", "technical_analysis")
        workflow.add_edge("technical_analysis", "sentiment_analysis")
        workflow.add_edge("sentiment_analysis", "investment_decision")
        workflow.add_edge("investment_decision", END)

        # 编译图
        return workflow.compile(checkpointer=self.memory)

    def run_analysis(self,
                    target_stocks: list = None,
                    filter_conditions: dict = None,
                    analysis_type: str = "filtered",
                    use_cache: bool = True,
                    force_refresh: bool = False,
                    config: dict = None) -> Dict[str, Any]:
        """
        运行股票分析工作流

        Args:
            target_stocks: 指定的股票代码列表
            filter_conditions: 筛选条件
            analysis_type: 分析类型 ("specified", "filtered", "mixed")
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新
            config: 配置参数

        Returns:
            分析结果字典
        """
        try:
            logger.info("开始股票分析工作流...")

            # 生成分析ID
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # 初始化状态
            initial_state: StockAnalysisState = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_id": analysis_id,
                "target_stocks": target_stocks,
                "filter_conditions": filter_conditions or {},
                "analysis_type": analysis_type,
                "selected_stocks": [],
                "filter_summary": None,
                "sector_analysis": {},
                "short_term_analysis": {},
                "technical_analysis": {},
                "sentiment_analysis": {},
                "investment_decisions": [],
                "final_report": "",
                "context_notes": [],
                "next_action": "stock_filter",
                "error": None,
                "use_cache": use_cache,
                "force_refresh": force_refresh,
                "config": config or {}
            }

            # 运行工作流
            thread_config = {"configurable": {"thread_id": analysis_id}}
            result = self.graph.invoke(initial_state, config=thread_config)

            # 检查是否有错误
            if result.get("error"):
                logger.error(f"工作流执行失败: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "analysis_id": analysis_id
                }

            # 返回成功结果
            logger.info("股票分析工作流完成")
            return {
                "success": True,
                "analysis_id": analysis_id,
                "date": result["date"],
                "analysis_type": result["analysis_type"],
                "selected_stocks": result["selected_stocks"],
                "filter_summary": result["filter_summary"],
                "sector_analysis": result["sector_analysis"],
                "short_term_analysis": result["short_term_analysis"],
                "technical_analysis": result["technical_analysis"],
                "sentiment_analysis": result["sentiment_analysis"],
                "investment_decisions": result["investment_decisions"],
                "final_report": result["final_report"],
                "context_notes": result["context_notes"]
            }

        except Exception as e:
            logger.error(f"股票分析工作流执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"工作流执行异常: {str(e)}",
                "analysis_id": analysis_id if 'analysis_id' in locals() else "unknown"
            }

    def run_specified_stocks_analysis(self, stock_codes: list, config: dict = None) -> Dict[str, Any]:
        """
        分析指定股票

        Args:
            stock_codes: 股票代码列表
            config: 配置参数

        Returns:
            分析结果
        """
        return self.run_analysis(
            target_stocks=stock_codes,
            analysis_type="specified",
            config=config
        )

    def run_filtered_stocks_analysis(self, filter_conditions: dict, config: dict = None) -> Dict[str, Any]:
        """
        根据条件筛选并分析股票

        Args:
            filter_conditions: 筛选条件
            config: 配置参数

        Returns:
            分析结果
        """
        return self.run_analysis(
            filter_conditions=filter_conditions,
            analysis_type="filtered",
            config=config
        )

    def run_mixed_analysis(self, stock_codes: list, filter_conditions: dict, config: dict = None) -> Dict[str, Any]:
        """
        混合分析：指定股票 + 条件筛选

        Args:
            stock_codes: 指定股票代码列表
            filter_conditions: 筛选条件
            config: 配置参数

        Returns:
            分析结果
        """
        return self.run_analysis(
            target_stocks=stock_codes,
            filter_conditions=filter_conditions,
            analysis_type="mixed",
            config=config
        )

    def get_analysis_history(self, analysis_id: str) -> Dict[str, Any]:
        """
        获取分析历史记录

        Args:
            analysis_id: 分析ID

        Returns:
            历史记录
        """
        try:
            thread_config = {"configurable": {"thread_id": analysis_id}}
            # 这里可以实现从checkpointer获取历史记录的逻辑
            # 目前返回空结果
            return {"analysis_id": analysis_id, "history": []}
        except Exception as e:
            logger.error(f"获取分析历史失败: {str(e)}")
            return {"error": str(e)}

# 创建全局工作流实例
stock_analysis_workflow = StockAnalysisWorkflow()

def create_stock_analysis_workflow() -> StockAnalysisWorkflow:
    """创建股票分析工作流实例"""
    return StockAnalysisWorkflow()

# 便捷函数
def analyze_stocks(stock_codes: list = None,
                  filter_conditions: dict = None,
                  analysis_type: str = "filtered",
                  **kwargs) -> Dict[str, Any]:
    """
    便捷的股票分析函数

    Args:
        stock_codes: 股票代码列表
        filter_conditions: 筛选条件
        analysis_type: 分析类型
        **kwargs: 其他参数

    Returns:
        分析结果
    """
    return stock_analysis_workflow.run_analysis(
        target_stocks=stock_codes,
        filter_conditions=filter_conditions,
        analysis_type=analysis_type,
        **kwargs
    )

def analyze_specified_stocks(stock_codes: list, **kwargs) -> Dict[str, Any]:
    """分析指定股票的便捷函数"""
    return stock_analysis_workflow.run_specified_stocks_analysis(stock_codes, **kwargs)

def analyze_filtered_stocks(filter_conditions: dict, **kwargs) -> Dict[str, Any]:
    """根据条件筛选分析股票的便捷函数"""
    return stock_analysis_workflow.run_filtered_stocks_analysis(filter_conditions, **kwargs)

def analyze_mixed_stocks(stock_codes: list, filter_conditions: dict, **kwargs) -> Dict[str, Any]:
    """混合分析的便捷函数"""
    return stock_analysis_workflow.run_mixed_analysis(stock_codes, filter_conditions, **kwargs)

if __name__ == "__main__":
    # 测试工作流
    import logging
    logging.basicConfig(level=logging.INFO)

    # 示例1：分析指定股票
    print("=== 测试指定股票分析 ===")
    result1 = analyze_specified_stocks(["000001", "000002"])
    print(f"分析结果: {result1.get('success', False)}")
    if result1.get('success'):
        print(f"选中股票数量: {len(result1.get('selected_stocks', []))}")

    # 示例2：条件筛选分析
    print("\n=== 测试条件筛选分析 ===")
    filter_conditions = {
        "market_cap_min": 100,  # 最小市值100亿
        "market_cap_max": 1000,  # 最大市值1000亿
        "change_pct_min": 0,     # 涨幅大于0
        "max_stocks": 5          # 最多5只股票
    }
    result2 = analyze_filtered_stocks(filter_conditions)
    print(f"分析结果: {result2.get('success', False)}")
    if result2.get('success'):
        print(f"筛选股票数量: {len(result2.get('selected_stocks', []))}")
        print(f"筛选说明: {result2.get('filter_summary', '')}")