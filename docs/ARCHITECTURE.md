# Ruo 架构设计文档

## 1. 系统架构概览

Ruo 是一款 AI 智能投顾副驾系统，采用前后端分离架构：

```
┌─────────────┐
│   Flutter   │  移动端
│   Frontend  │  (iOS/Android)
└──────┬──────┘
       │ REST API
┌──────▼──────┐
│   FastAPI   │  后端服务
│   Backend   │
└──────┬──────┘
       │
┌──────▼──────┬──────────┬──────────┐
│ PostgreSQL  │  Redis   │  Celery  │
│   数据库    │  缓存    │ 任务队列 │
└─────────────┴──────────┴──────────┘
```

## 2. 后端架构

### 2.1 目录结构

```
/backend
├── /app
│   ├── /api                # API 路由层
│   │   ├── /endpoints      # 具体端点
│   │   │   ├── portfolio.py   # 持仓管理
│   │   │   ├── news.py        # 新闻情报
│   │   │   ├── market.py      # 行情数据
│   │   │   └── analysis.py    # 分析报告
│   │   └── __init__.py
│   │
│   ├── /core               # 核心配置
│   │   ├── config.py       # 应用配置
│   │   ├── database.py     # 数据库连接
│   │   └── security.py     # 安全认证
│   │
│   ├── /services           # 业务逻辑层
│   │   ├── data_fetch.py   # 数据获取服务
│   │   ├── analysis.py     # 分析服务
│   │   └── portfolio.py    # 持仓管理服务
│   │
│   ├── /models             # 数据模型层
│   │   ├── user.py         # 用户模型
│   │   ├── portfolio.py    # 持仓模型
│   │   ├── news.py         # 新闻模型
│   │   └── stock.py        # 股票模型
│   │
│   └── /llm_agent          # AI 智能体
│       ├── /agents         # 各类智能体
│       ├── /graphs         # LangGraph 工作流
│       ├── /tools          # 工具函数
│       └── prompts.py      # 提示词模板
│
├── /tests                  # 测试代码
└── main.py                 # 应用入口
```

### 2.2 核心模块

#### API 层 (`/api`)
- **职责**: 处理 HTTP 请求，参数验证，返回响应
- **技术**: FastAPI, Pydantic
- **示例端点**:
  - `GET /api/v1/portfolio` - 获取持仓列表
  - `POST /api/v1/news/analyze` - 分析新闻
  - `GET /api/v1/market/{symbol}` - 获取行情

#### 服务层 (`/services`)
- **职责**: 业务逻辑处理，数据转换
- **技术**: Python, AkShare/Tushare
- **核心服务**:
  - `DataFetchService` - 数据抓取
  - `AnalysisService` - 技术分析
  - `NewsService` - 新闻处理

#### 模型层 (`/models`)
- **职责**: 数据库模型定义，ORM 映射
- **技术**: SQLAlchemy
- **核心模型**:
  - `User` - 用户
  - `Portfolio` - 持仓
  - `News` - 新闻
  - `Trade` - 交易记录

#### LLM 智能体 (`/llm_agent`)
- **职责**: AI 分析，智能推荐
- **技术**: LangChain, LangGraph
- **核心组件**:
  - `SentimentAnalyst` - 情感分析师
  - `TechnicalAnalyst` - 技术分析师
  - `RiskController` - 风险控制师
  - `InvestmentDecisionMaker` - 投资决策师

## 3. 数据流

### 3.1 新闻分析流程

```
用户请求 → API → NewsService → DataFetch → LLM Agent → 结果返回
                    ↓
                 存储到 DB
                    ↓
                缓存到 Redis
```

### 3.2 定时任务流程

```
Celery Beat → 触发任务 → Celery Worker → 执行分析 → 存储结果
                                ↓
                           更新缓存
                                ↓
                           推送通知
```

## 4. 技术选型说明

### 4.1 为什么选择 FastAPI?
- ✅ 高性能（基于 Starlette 和 Pydantic）
- ✅ 异步支持（适合 I/O 密集型任务）
- ✅ 自动文档生成（OpenAPI/Swagger）
- ✅ 类型提示（提高代码质量）

### 4.2 为什么选择 PostgreSQL?
- ✅ 强大的 JSON 支持（存储分析结果）
- ✅ 事务支持（保证数据一致性）
- ✅ 丰富的扩展（如时序数据）

### 4.3 为什么选择 Redis?
- ✅ 行情数据缓存（减少 API 调用）
- ✅ Celery 消息队列
- ✅ 分布式锁（防止重复任务）

### 4.4 为什么选择 LangGraph?
- ✅ 复杂工作流编排
- ✅ 多智能体协作
- ✅ 状态管理和回溯

## 5. 部署方案

### 5.1 开发环境
```bash
# 启动数据库和缓存
docker-compose up -d postgres redis

# 启动后端
cd backend
uvicorn main:app --reload
```

### 5.2 生产环境
```bash
# 使用 Docker Compose 一键部署
docker-compose up -d
```

## 6. 安全考虑

- 🔐 JWT 认证
- 🔐 API 密钥加密存储
- 🔐 SQL 注入防护（ORM）
- 🔐 CORS 配置
- 🔐 敏感数据脱敏

## 7. 监控与日志

- 📊 应用性能监控（APM）
- 📊 错误追踪（Sentry）
- 📊 日志聚合（ELK）
- 📊 数据库监控

## 8. 未来规划

- [ ] WebSocket 实时推送
- [ ] GraphQL 支持
- [ ] 微服务拆分
- [ ] K8s 部署
- [ ] CI/CD 流水线
