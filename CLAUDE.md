# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ruo** is an AI agent-based personal information and decision-making system focused on Chinese stock market analysis, specifically leveraging Dragon and Tiger List (龙虎榜, LHB) data for trading decisions. The system uses multiple AI agents to collect, analyze, and generate trading recommendations.

## Core Architecture

### Enhanced Trading Agents Framework
- **LHBAgentsGraph**: Main workflow for Dragon and Tiger List analysis using LangGraph with quantitative scoring
- **TradingAgentsGraph**: General trading analysis framework (currently commented out in main.py)
- **Quantitative Analysis**: Comprehensive scoring system for capital flow, institutional participation, technical indicators, market sentiment, and risk control
- **Backtest Validation**: Built-in validation system to verify prediction accuracy
- **Agent Types**: Analysts, Managers, Researchers, Risk Management, Traders organized in modular structure

### Advanced Data Pipeline
- **Enhanced AKShare Integration**: Primary data source with technical indicators and historical analysis
- **Technical Indicators**: MA5, MA20, RSI, MACD, volume analysis using stockstats
- **Multi-layer Caching**: Adaptive, integrated, and database cache managers
- **Risk Assessment**: Automated risk scoring and alert system
- **Data Quality**: Comprehensive error handling and data validation

### Intelligent Analysis Engine
- **Quantitative Scoring**: 5-dimensional scoring system (0-100 scale)
  - Capital Flow Strength (资金流向): Net inflow/outflow analysis
  - Institutional Participation (机构参与): Institution involvement assessment  
  - Technical Indicators (技术指标): MA, RSI, MACD analysis
  - Market Sentiment (市场情绪): Volume and volatility assessment
  - Risk Control (风险控制): Comprehensive risk evaluation
- **Structured Decision Logic**: Rule-based recommendation engine
- **LLM Validation**: AI verification of quantitative recommendations

### LLM Integration
- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, DashScope (Alibaba Cloud)
- **Configuration**: Flexible provider switching via config
- **Current Setup**: Uses DashScope with Qwen models (qwen-plus, qwen-turbo)

## Common Commands

### Package Management
```bash
# Install dependencies (project uses uv, not nv as mentioned in README)
uv sync

# Run with requirements.txt fallback
pip install -r requirements.txt
```

### Running the Application
```bash
# Main entry point - currently runs LHB analysis
python main.py

# The main script is configured to run LHBAgentsGraph analysis for a specific date
```

### Development Commands
```bash
# Run analysis with validation
python -c "
from tradingagents.graph import LHBAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config['llm_provider'] = 'dashscope'
config['deep_think_llm'] = 'qwen-plus'
config['quick_think_llm'] = 'qwen-turbo'

# Run with backtest validation
final_state, signal, validation = LHBAgentsGraph(debug=True, config=config).run_with_validation('2025-07-24', validate_days=1)
"

# Run standard analysis  
python main.py

# Check logs
tail -f logs/lhb_analysis.log
```

### Analysis Workflow
1. **Data Fetching**: Retrieve LHB data via AKShare with error handling
2. **Technical Analysis**: Calculate MA, RSI, MACD indicators
3. **Quantitative Scoring**: Multi-dimensional evaluation (0-100 scale)
4. **LLM Analysis**: Deep analysis of market dynamics
5. **Decision Generation**: Structured recommendations with confidence scores
6. **Validation**: Backtest verification of prediction accuracy
7. **Risk Assessment**: Comprehensive risk alerts and warnings

## Key Configuration

### LLM Provider Configuration
- Set in `main.py` and `tradingagents/default_config.py`
- Current setup uses DashScope with Qwen models
- Supports OpenAI, Anthropic, Google, and other providers

### Data Sources Configuration  
- Primary: AKShare for Chinese market data
- Cache directories managed automatically in `dataflows/data_cache/`
- Database: SQLite (`ruo.db`)

## Important Files and Directories

### Core Entry Points
- `main.py`: Main application entry point
- `tradingagents/graph/lhb_graph.py`: Dragon and Tiger List analysis workflow
- `tradingagents/default_config.py`: System configuration

### Agent Implementation
- `tradingagents/agents/analysts/lhb_nodes.py`: LHB-specific analysis nodes
- `tradingagents/agents/analysts/`: Various market analysts
- `tradingagents/agents/managers/`: Research and risk managers

### Data Management
- `tradingagents/dataflows/`: Data source adapters and utilities
- `tradingagents/dataflows/akshare_utils.py`: AKShare integration
- `config/`: JSON configuration files for models, pricing, settings

## Architecture Notes

### State Management
- Uses `AgentState` from `tradingagents.agents.utils.agent_states`
- LangGraph state flow for agent orchestration

### Data Flow
1. Fetch LHB data via AKShare
2. Filter out ST stocks
3. Analyze capital flow and institutional movements  
4. Generate trading recommendations
5. Output structured results

### Agent Workflow
The system implements a multi-agent approach where:
- **Analysts** process market data and news
- **Researchers** provide bull/bear perspectives  
- **Risk Management** agents debate and validate decisions
- **Managers** coordinate overall research and risk assessment

## Development Focus

This is a financial analysis system focused on:
- Chinese stock market Dragon and Tiger List analysis
- Multi-agent AI decision making
- Real-time data processing and caching
- Trading recommendation generation
- Risk assessment and management

The codebase emphasizes modularity, with clear separation between data sources, analysis agents, and decision-making workflows.