# MVP v0.1 详细设计文档

> **版本**: v0.2
> **目标**: 实现基础持仓管理 + AI 新闻情报功能 + 股票详情页
> **开发周期**: 2-3 周
> **最后更新**: 2026-01-28

---

## 📋 目录

1. [功能需求](#功能需求)
2. [数据库设计](#数据库设计)
3. [API 接口设计](#api-接口设计)
4. [服务层设计](#服务层设计)
5. [任务进度追踪](#任务进度追踪)

---

## 1. 功能需求

### 1.1 P0 核心功能（必须完成）

| 功能ID | 模块 | 功能描述 | 验收标准 | 优先级 |
|--------|------|----------|----------|--------|
| F-01 | 数据层 | 基础行情接入 | 能调用 AkShare 获取股票代码、现价、涨跌幅 | P0 |
| F-02 | 自选管理 | 新增/删除自选股 | 输入代码自动补全名称，保存到数据库 | P0 |
| F-03 | 自选管理 | 持仓信息录入 | 支持输入成本价、股数、策略标签 | P0 |
| F-04 | 自选管理 | 首页卡片展示 | 显示股票名、现价、持仓盈亏比 | P0 |
| F-05 | 新闻引擎 | 资讯定时抓取 | 每小时抓取自选股新闻 | P0 |
| F-06 | AI 分析 | LLM 情感打分 | 输出一句话摘要 + 情感倾向 | P0 |

### 1.2 P1 功能（建议完成）

| 功能ID | 模块 | 功能描述 | 验收标准 | 优先级 |
|--------|------|----------|----------|--------|
| F-07 | 股票详情 | 股票详情页 | 点击持仓股票进入详情页，显示股票详细数据 | P1 |
| F-08 | 分时数据 | 分时图展示 | 展示当日分时价格走势图 | P1 |
| F-09 | 买卖盘 | 五档买卖盘 | 显示买一到买五、卖一到卖五的价格和手数 | P1 |

---

## 2. 数据库设计

### 2.1 表结构设计

#### **portfolios** - 持仓表
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    symbol VARCHAR(10) NOT NULL,        -- 股票代码，如 000001
    name VARCHAR(50) NOT NULL,          -- 股票名称，如 平安银行
    cost_price FLOAT NOT NULL,          -- 成本价
    quantity FLOAT NOT NULL,            -- 持仓数量
    strategy_tag VARCHAR(20),           -- 策略标签：打板/低吸/趋势
    notes TEXT,
    is_active INTEGER DEFAULT 1,       -- 软删除标记
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_user_id (user_id)
);
```

#### **stock_news** - 股票新闻表
```sql
CREATE TABLE stock_news (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,    -- 股票代码
    title VARCHAR(200) NOT NULL,        -- 新闻标题
    raw_content TEXT,                   -- 原始内容/摘要
    source VARCHAR(100),                -- 来源：财联社、新浪财经等
    url VARCHAR(500),                   -- 新闻链接
    publish_time TIMESTAMP NOT NULL,    -- 发布时间
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    INDEX idx_stock_code (stock_code),
    INDEX idx_publish_time (publish_time)
);
```

#### **news_analysis** - AI 分析结果表
```sql
CREATE TABLE news_analysis (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL UNIQUE,    -- 关联 stock_news.id
    ai_summary TEXT NOT NULL,           -- AI 生成的一句话摘要
    sentiment_label VARCHAR(20) NOT NULL, -- 利好/中性/利空
    sentiment_score FLOAT,              -- 情感分数 1-5 星
    llm_model VARCHAR(50),              -- 使用的模型
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (news_id) REFERENCES stock_news(id)
);
```

### 2.2 ER 图关系

```
users (1) ---< (N) portfolios
stock_news (1) --- (1) news_analysis
portfolios.symbol --- stocks.symbol (逻辑关联)
```

---

## 3. API 接口设计

### 3.1 持仓管理 API

#### **POST /api/v1/portfolio/add**
添加持仓

**请求体：**
```json
{
  "symbol": "000001",
  "cost_price": 10.5,
  "quantity": 1000,
  "strategy_tag": "趋势"
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "symbol": "000001",
    "name": "平安银行",
    "cost_price": 10.5,
    "quantity": 1000,
    "strategy_tag": "趋势",
    "current_price": 11.2,
    "profit_loss": 700.0,
    "profit_loss_ratio": 0.0667
  }
}
```

#### **GET /api/v1/portfolio/list**
获取持仓列表

**查询参数：**
- `user_id`: 用户ID（默认 1）

**响应：**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "symbol": "000001",
      "name": "平安银行",
      "cost_price": 10.5,
      "quantity": 1000,
      "current_price": 11.2,
      "profit_loss": 700.0,
      "profit_loss_ratio": 0.0667,
      "strategy_tag": "趋势",
      "has_new_news": true
    }
  ],
  "total_value": 11200.0,
  "total_cost": 10500.0,
  "total_profit_loss": 700.0
}
```

#### **DELETE /api/v1/portfolio/{portfolio_id}**
删除持仓（软删除）

**响应：**
```json
{
  "status": "success",
  "message": "持仓已删除"
}
```

### 3.2 股票查询 API

#### **GET /api/v1/stock/search**
搜索股票（自动补全）

**查询参数：**
- `keyword`: 股票代码或名称，如 "000001" 或 "平安"

**响应：**
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "market": "深圳主板"
    }
  ]
}
```

#### **GET /api/v1/stock/realtime/{symbol}**
获取实时行情

**响应：**
```json
{
  "status": "success",
  "data": {
    "symbol": "000001",
    "name": "平安银行",
    "price": 11.2,
    "change": 0.15,
    "change_pct": 1.36,
    "open": 11.0,
    "high": 11.5,
    "low": 10.9,
    "volume": 123456789,
    "timestamp": "2026-01-22 14:30:00"
  }
}
```

### 3.3 新闻情报 API

#### **GET /api/v1/news/{symbol}**
获取股票新闻及 AI 分析

**查询参数：**
- `limit`: 返回数量（默认 10）
- `hours`: 最近 N 小时内的新闻（默认 24）

**响应：**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "平安银行发布2025年财报",
      "source": "财联社",
      "publish_time": "2026-01-22 10:30:00",
      "ai_summary": "平安银行今日发布财报，净利润同比增长20%，超出市场预期，且不良率进一步降低。",
      "sentiment_label": "利好",
      "sentiment_score": 4.5,
      "url": "https://..."
    }
  ]
}
```

### 3.4 股票详情数据 API

#### **GET /api/v1/stock/detail/{symbol}**
获取股票详细数据（包含分时和买卖盘）

**响应：**
```json
{
  "status": "success",
  "data": {
    "symbol": "000001",
    "name": "平安银行",
    "price": 11.2,
    "change": 0.15,
    "change_pct": 1.36,
    "open": 11.0,
    "high": 11.5,
    "low": 10.9,
    "volume": 123456789,
    "amount": 1385000000,
    "turnover": 2.5,
    "timestamp": "2026-01-22 14:30:00",
    "intraday": [
      {
        "time": "09:30:00",
        "price": 10.95,
        "volume": 125000,
        "avg_price": 10.92
      }
    ],
    "buy_orders": [
      {
        "level": 1,
        "price": 11.19,
        "volume": 125800
      },
      {
        "level": 2,
        "price": 11.18,
        "volume": 98500
      },
      {
        "level": 3,
        "price": 11.17,
        "volume": 75000
      },
      {
        "level": 4,
        "price": 11.16,
        "volume": 62000
      },
      {
        "level": 5,
        "price": 11.15,
        "volume": 58000
      }
    ],
    "sell_orders": [
      {
        "level": 1,
        "price": 11.20,
        "volume": 98500
      },
      {
        "level": 2,
        "price": 11.21,
        "volume": 125000
      },
      {
        "level": 3,
        "price": 11.22,
        "volume": 85000
      },
      {
        "level": 4,
        "price": 11.23,
        "volume": 78000
      },
      {
        "level": 5,
        "price": 11.24,
        "volume": 62000
      }
    ]
  }
}
```

---

## 4. 服务层设计

### 4.1 MarketDataService - 行情数据服务

**职责：** 调用 AkShare/Tushare 获取行情数据

**核心方法：**
```python
class MarketDataService:
    def get_stock_info(symbol: str) -> dict
    def get_realtime_price(symbol: str) -> dict
    def get_stock_detail(symbol: str) -> dict      # 获取股票完整详情（含分时、买卖盘）
    def get_intraday_data(symbol: str) -> list    # 获取分时数据
    def get_order_book_data(symbol: str) -> dict  # 获取买卖盘数据
    def search_stock(keyword: str) -> list
```

### 4.2 PortfolioService - 持仓管理服务

**职责：** 持仓 CRUD + 盈亏计算

**核心方法：**
```python
class PortfolioService:
    def add_portfolio(user_id: int, data: dict) -> Portfolio
    def get_portfolio_list(user_id: int) -> list
    def calculate_profit_loss(portfolio: Portfolio) -> dict
    def delete_portfolio(portfolio_id: int) -> bool
```

### 4.3 NewsService - 新闻服务

**职责：** 新闻抓取 + 存储

**核心方法：**
```python
class NewsService:
    def fetch_stock_news(symbol: str) -> list
    def save_news(news_list: list) -> None
    def get_latest_news(symbol: str, hours: int) -> list
```

### 4.4 AIAnalysisService - AI 分析服务

**职责：** 调用 LLM 进行情感分析

**核心方法：**
```python
class AIAnalysisService:
    def analyze_news(news: StockNews) -> NewsAnalysis
    def batch_analyze(news_list: list) -> list
```

**Prompt 模板：**
```python
SENTIMENT_ANALYSIS_PROMPT = """
你是一位专业的股票分析师。请分析以下新闻，并给出：

新闻标题：{title}
新闻内容：{content}

请输出 JSON 格式：
{
  "ai_summary": "一句话总结（不超过50字）",
  "sentiment_label": "利好/中性/利空",
  "sentiment_score": 1-5 星级评分
}
"""
```

---

## 5. 任务进度追踪

### 5.1 开发任务清单

| 任务ID | 任务描述 | 负责模块 | 预计工时 | 状态 | 完成时间 |
|--------|----------|----------|----------|------|----------|
| T-01 | 数据库表设计与创建 | Models | 2h | ✅ 已完成 | 2026-01-22 |
| T-02 | 实现 MarketDataService | Services | 4h | 🔄 进行中 | - |
| T-03 | 实现 PortfolioService | Services | 3h | 🔜 待开始 | - |
| T-04 | 实现持仓管理 API | API | 4h | 🔜 待开始 | - |
| T-05 | 实现股票查询 API | API | 2h | 🔜 待开始 | - |
| T-06 | 实现 NewsService | Services | 3h | 🔜 待开始 | - |
| T-07 | 实现 AIAnalysisService | Services | 4h | 🔜 待开始 | - |
| T-08 | 实现新闻情报 API | API | 3h | 🔜 待开始 | - |
| T-09 | 实现股票详情 API（分时+买卖盘）| API | 4h | 🔜 待开始 | - |
| T-10 | 创建 Celery 定时任务 | Tasks | 3h | 🔜 待开始 | - |
| T-11 | 集成测试 | Tests | 4h | 🔜 待开始 | - |

**总预计工时**: 36h
**当前进度**: 5%

### 5.2 里程碑

- [ ] **里程碑 1**: 完成数据库和基础服务（T-01 ~ T-03）
- [ ] **里程碑 2**: 完成持仓管理功能（T-04 ~ T-05）
- [ ] **里程碑 3**: 完成新闻和 AI 分析（T-06 ~ T-08）
- [ ] **里程碑 4**: 完成股票详情和定时任务（T-09 ~ T-10）
- [ ] **里程碑 5**: 完成集成测试和部署（T-11）

---

## 6. 技术栈

### 6.1 后端技术

- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis 7
- **任务队列**: Celery 5.3
- **数据源**: AkShare 1.12+
- **LLM**: DeepSeek API / OpenAI API

### 6.2 数据源选择

**行情数据：**
- 优先使用 AkShare（免费、数据全）
- 备用 Tushare Pro（需要积分）

**新闻数据：**
- 东方财富网 API
- 新浪财经 RSS
- 财联社（爬虫）

**LLM 选择：**
- 开发环境：DeepSeek API（成本低、中文好）
- 生产环境：根据预算选择

---

## 7. 部署方案

### 7.1 开发环境

```bash
# 启动数据库和 Redis
docker-compose up -d postgres redis

# 启动后端
cd backend
uvicorn main:app --reload

# 启动 Celery Worker
celery -A app.tasks worker --loglevel=info

# 启动 Celery Beat
celery -A app.tasks beat --loglevel=info
```

### 7.2 生产环境

使用 Docker Compose 一键部署：
```bash
docker-compose up -d
```

---

## 8. 测试计划

### 8.1 单元测试

- [ ] 测试 MarketDataService
- [ ] 测试 PortfolioService
- [ ] 测试 AIAnalysisService

### 8.2 集成测试

- [ ] 测试持仓添加流程
- [ ] 测试新闻抓取和分析流程
- [ ] 测试定时任务

### 8.3 手动测试场景

**场景 A：添加持仓**
1. POST /api/v1/portfolio/add
2. 验证数据库记录
3. GET /api/v1/portfolio/list
4. 验证盈亏计算

**场景 B：查看 AI 新闻**
1. 触发新闻抓取任务
2. GET /api/v1/news/{symbol}
3. 验证 AI 分析结果

---

## 9. 风险与问题

### 9.1 已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AkShare API 限流 | 高 | 添加缓存、限制请求频率 |
| LLM API 成本 | 中 | 使用 DeepSeek 降低成本 |
| 数据实时性 | 中 | 明确告知用户延迟 |

### 9.2 待确认问题

- [ ] 实时数据刷新频率？（建议：30 秒轮询）
- [ ] LLM 选择？（建议：DeepSeek）
- [ ] 新闻来源优先级？

---

## 10. 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-01-28 | v0.2 | 移除 K 线设计，新增股票详情页（分时图+买卖盘）|
| 2026-01-22 | v0.1 | 初始版本，完成需求分析和数据库设计 |

---

**文档维护者**: AI Assistant
**审核状态**: 待审核
