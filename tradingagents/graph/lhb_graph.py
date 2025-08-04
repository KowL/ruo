import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from tradingagents.llm_adapters import ChatDashScope, ChatDashScopeOpenAI
from langgraph.graph import StateGraph, END
from tradingagents.agents.utils.agent_states import LhbState

from tradingagents.agents.analysts.lhb_nodes import (
    fetch_lhb_data,
    analyze_lhb_data,
    generate_lhb_suggestion,
    output_lhb_result
)
from tradingagents.agents.analysts.backtest_validator import create_backtest_validator
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.interface import set_config

class LHBAgentsGraph:
    """龙虎榜分析智能体图结构"""

    def __init__(
        self,
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """初始化龙虎榜分析智能体

        Args:
            debug: 是否启用调试模式
            config: 配置字典，如果为None则使用默认配置
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # 更新接口配置
        set_config(self.config)

        # 创建必要的目录
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # 初始化LLM
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            google_api_key = os.getenv('GOOGLE_API_KEY')
            self.deep_thinking_llm = ChatGoogleGenerativeAI(
                model=self.config["deep_think_llm"],
                google_api_key=google_api_key,
                temperature=0.1,
                max_tokens=2000
            )
            self.quick_thinking_llm = ChatGoogleGenerativeAI(
                model=self.config["quick_think_llm"],
                google_api_key=google_api_key,
                temperature=0.1,
                max_tokens=2000
            )
        elif (self.config["llm_provider"].lower() == "dashscope" or
              self.config["llm_provider"].lower() == "alibaba" or
              "dashscope" in self.config["llm_provider"].lower() or
              "阿里百炼" in self.config["llm_provider"]):
            print("🔧 使用阿里百炼 OpenAI 兼容适配器 (支持原生工具调用)")
            self.deep_thinking_llm = ChatDashScopeOpenAI(
                model=self.config["deep_think_llm"],
                temperature=0.1,
                max_tokens=2000
            )
            self.quick_thinking_llm = ChatDashScopeOpenAI(
                model=self.config["quick_think_llm"],
                temperature=0.1,
                max_tokens=2000
            )
        else:
            raise ValueError(f"不支持的LLM提供商: {self.config['llm_provider']}")

        # 状态追踪
        self.curr_state = None
        self.log_states_dict = {}  # date to full state dict

        # 设置图结构
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建龙虎榜分析流程图"""
        graph = StateGraph(LhbState)

        # 添加节点
        graph.add_node("fetch", fetch_lhb_data)
        graph.add_node("analyze", analyze_lhb_data)
        graph.add_node("suggest", generate_lhb_suggestion)
        graph.add_node("output", output_lhb_result)

        # 添加边
        graph.add_edge("fetch", "analyze")
        graph.add_edge("analyze", "suggest")
        graph.add_edge("suggest", "output")
        graph.add_edge("output", END)

        # 设置入口和出口
        graph.set_entry_point("fetch")

        return graph.compile()

    def run_with_validation(self, trade_date, validate_days: int = 1):
        """运行龙虎榜分析并进行回测验证
        
        Args:
            trade_date: 交易日期
            validate_days: 验证天数
            
        Returns:
            final_state: 最终状态
            processed_signal: 处理后的信号
            validation_results: 验证结果
        """
        # 先运行正常分析
        final_state, processed_signal = self.run(trade_date)
        
        # 如果有建议，进行回测验证
        validation_results = None
        if final_state.get("suggestions"):
            try:
                validator = create_backtest_validator()
                validation_results = validator.validate_suggestions(
                    final_state["suggestions"], 
                    validate_days
                )
                
                # 保存验证结果
                validation_filepath = f"eval_results/lhb/validation_{trade_date}.json"
                validator.save_validation_results(validation_results, validation_filepath)
                
                # 添加验证结果到最终状态
                final_state["validation_results"] = validation_results
                
                print(f"\n📊 回测验证结果:")
                print(f"验证准确率: {validation_results.get('accuracy_rate', 0):.2%}")
                print(f"平均收益率: {validation_results.get('average_return', 0):.2%}")
                print(f"整体评估: {validation_results.get('summary', {}).get('overall_assessment', '未知')}")
                
            except Exception as e:
                print(f"⚠️ 回测验证失败: {str(e)}")
        
        return final_state, processed_signal, validation_results

    def run(self, trade_date):
        """运行龙虎榜分析

        Args:
            trade_date: 交易日期，如果为None则使用当前日期

        Returns:
            final_state: 最终状态
            processed_signal: 处理后的信号
        """
        # 初始化状态
        init_state = {
            "trade_date": trade_date or date.today().strftime("%Y-%m-%d"),
            "llm": {
                "deep_thinking": self.deep_thinking_llm,
                "quick_thinking": self.quick_thinking_llm
            },
            "config": self.config
        }

        final_state = self.graph.invoke(init_state)

        # 存储当前状态用于反思
        self.curr_state = final_state

        # 记录状态
        self._log_state(trade_date or date.today(), final_state)

        return final_state, self._process_signal(final_state)

    def _log_state(self, trade_date: str, final_state: Dict[str, Any]):
        """记录最终状态到JSON文件

        Args:
            trade_date: 交易日期
            final_state: 最终状态字典
        """
        self.log_states_dict[str(trade_date)] = {
            "trade_date": str(trade_date),
            "lhb_data": final_state.get("lhb_data", {}),
            "analysis_result": final_state.get("analysis_result", {}),
            "suggestions": final_state.get("suggestions", []),
            "final_output": final_state.get("final_output", {})
        }

        # 保存到文件
        directory = Path("eval_results/lhb/LHBAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            directory / "full_states_log.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(self.log_states_dict, f, indent=4, ensure_ascii=False)

    def _process_signal(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """处理最终信号

        Args:
            final_state: 最终状态字典

        Returns:
            处理后的信号字典
        """
        return {
            "date": str(final_state.get("trade_date")),
            "suggestions": final_state.get("suggestions", []),
            "risk_level": final_state.get("risk_level", "medium"),
            "confidence_score": final_state.get("confidence_score", 0.5)
        } 