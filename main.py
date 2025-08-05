from tradingagents.graph import TradingAgentsGraph, LHBAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "dashscope"  # Use a different model
config["backend_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # Use a different backend
config["deep_think_llm"] = "qwen-plus"  # Use a different model
config["quick_think_llm"] = "qwen-turbo"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Increase debate rounds

# Initialize with custom config
# ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
# _, decision = ta.propagate("300543", "2025-07-23")
# print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns


# Initialize with custom config
_, lhb_report = LHBAgentsGraph(debug=True, config=config).run("2025-08-05")
print(lhb_report)
