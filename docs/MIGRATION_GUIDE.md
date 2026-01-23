# 项目架构迁移指南

## 📋 迁移概览

本指南帮助您将现有代码迁移到新的 FastAPI 标准架构中。

## 🗂️ 文件迁移映射

### 1. AI 智能体模块

**原路径** → **新路径**

```
/agent/
├── technical_analyst.py     → backend/app/llm_agent/agents/technical_analyst.py
├── sentiment_analyst.py     → backend/app/llm_agent/agents/sentiment_analyst.py
├── risk_controller.py       → backend/app/llm_agent/agents/risk_controller.py
├── investment_decision_maker.py → backend/app/llm_agent/agents/investment_decision_maker.py
├── strategist.py            → backend/app/llm_agent/agents/strategist.py
├── sector_analyst.py        → backend/app/llm_agent/agents/sector_analyst.py
├── data_officer.py          → backend/app/llm_agent/agents/data_officer.py
├── finalizer.py             → backend/app/llm_agent/agents/finalizer.py
└── tools.py                 → backend/app/llm_agent/tools/agent_tools.py
```

### 2. LangGraph 工作流

```
/graph/
├── stock_analysis_workflow.py    → backend/app/llm_agent/graphs/stock_analysis.py
├── opening_analysis_workflow.py  → backend/app/llm_agent/graphs/opening_analysis.py
└── limit_up_stock_analysis_graph.py → backend/app/llm_agent/graphs/limit_up_analysis.py
```

### 3. 工具函数

```
/tools/
├── stock_tools.py           → backend/app/services/data_fetch.py
├── report_export.py         → backend/app/services/report.py
└── __init__.py              → 合并到 services
```

### 4. 工具类

```
/utils/
├── data_converter.py        → backend/app/core/utils.py
└── 其他工具                 → backend/app/core/helpers.py
```

### 5. 状态管理

```
/state/
└── __init__.py              → backend/app/llm_agent/state/
```

### 6. 测试文件

```
/test/
├── test_coach.py            → backend/tests/test_agents.py
└── llm_usage_examples.py    → backend/tests/examples/
```

### 7. 核心文件

```
根目录:
├── main.py                  → 拆分到 backend/app/api/endpoints/
├── agent_system.py          → backend/app/llm_agent/system.py
├── llm_factory.py           → backend/app/core/llm_factory.py
├── demo_stock_analysis.py   → backend/tests/examples/
└── final_test.py            → backend/tests/integration/
```

## 🔧 迁移步骤

### 第一步：创建新目录结构

```bash
# 已完成
mkdir -p backend/app/{api,core,services,models,llm_agent}
mkdir -p backend/app/llm_agent/{agents,graphs,tools,state}
mkdir -p backend/tests/{unit,integration,examples}
mkdir -p frontend docs
```

### 第二步：迁移核心配置

```bash
# 移动配置相关
mv llm_factory.py backend/app/core/
mv .env backend/
mv .env.example backend/
```

### 第三步：迁移 AI 智能体

```bash
# 创建 agents 目录并移动文件
mkdir -p backend/app/llm_agent/agents
cp agent/*.py backend/app/llm_agent/agents/

# 创建 graphs 目录并移动工作流
mkdir -p backend/app/llm_agent/graphs
cp graph/*.py backend/app/llm_agent/graphs/

# 创建 tools 目录
mkdir -p backend/app/llm_agent/tools
cp agent/tools.py backend/app/llm_agent/tools/agent_tools.py
```

### 第四步：迁移业务服务

```bash
# 将 tools 转为 services
mkdir -p backend/app/services
cp tools/stock_tools.py backend/app/services/data_fetch.py
cp tools/report_export.py backend/app/services/report.py
```

### 第五步：迁移工具类

```bash
# 移动工具函数
cp utils/*.py backend/app/core/
```

### 第六步：迁移测试

```bash
# 移动测试文件
cp test/test_coach.py backend/tests/unit/
cp test/llm_usage_examples.py backend/tests/examples/
cp demo_stock_analysis.py backend/tests/examples/
cp final_test.py backend/tests/integration/
```

### 第七步：创建 API 端点

需要根据现有 main.py 的功能创建 API 端点：

```python
# backend/app/api/endpoints/analysis.py
from fastapi import APIRouter, Depends
from app.llm_agent.graphs.stock_analysis import run_stock_analysis

router = APIRouter()

@router.post("/stock/{symbol}")
async def analyze_stock(symbol: str):
    """分析单只股票"""
    result = await run_stock_analysis(symbol)
    return result
```

### 第八步：更新导入路径

所有文件的导入需要更新：

**原来：**
```python
from agent.technical_analyst import TechnicalAnalyst
from tools.stock_tools import get_stock_data
```

**现在：**
```python
from app.llm_agent.agents.technical_analyst import TechnicalAnalyst
from app.services.data_fetch import get_stock_data
```

## ⚠️ 注意事项

### 1. 环境变量
确保 `.env` 文件在 `backend/` 目录下，并更新路径配置：

```env
# 更新路径
BASE_DIR=/app/backend
CACHE_DIR=/app/cache
REPORTS_DIR=/app/reports
```

### 2. 数据库模型
需要为持仓、新闻等创建 SQLAlchemy 模型：

```python
# backend/app/models/portfolio.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    shares = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    # ...
```

### 3. 依赖项
更新 `requirements.txt`，添加 FastAPI 相关依赖：

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
redis>=5.0.0
celery>=5.3.0
pydantic-settings>=2.0.0
```

## 🧪 测试迁移

### 运行测试确保功能正常

```bash
# 单元测试
pytest backend/tests/unit/

# 集成测试
pytest backend/tests/integration/

# 检查 API
uvicorn backend.main:app --reload
# 访问 http://localhost:8000/docs
```

## 📦 保留旧代码

在完全迁移前，建议保留原有代码：

```bash
# 创建备份分支
git checkout -b backup/old-structure

# 在新分支进行迁移
git checkout -b feature/new-architecture
```

## ✅ 迁移检查清单

- [ ] 创建新目录结构
- [ ] 迁移 AI 智能体到 `llm_agent/agents/`
- [ ] 迁移工作流到 `llm_agent/graphs/`
- [ ] 迁移工具到 `llm_agent/tools/`
- [ ] 创建 API 端点
- [ ] 创建数据库模型
- [ ] 更新所有导入路径
- [ ] 配置 Docker
- [ ] 更新环境变量
- [ ] 运行测试
- [ ] 更新文档

## 🚀 下一步

完成迁移后，您可以：
1. 添加数据库迁移（Alembic）
2. 配置 Celery 定时任务
3. 实现用户认证
4. 开发前端应用
5. 部署到生产环境
