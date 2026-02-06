# Ruo

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**Ruo** 是一款面向个人投资者的 AI 智能投顾副驾。它结合了传统量化数据的严谨与 LLM (大语言模型) 的语义理解能力，旨在解决散户“信息过载”和“交易无纪律”的痛点。

## 核心功能 (Core Features)

1.  **📊 智能持仓 (Smart Portfolio)**: 不仅仅是记账，支持绑定“交易策略”与“成本动态推演”。
2.  **🤖 AI 情报分析 (AI News)**: 每日自动抓取自选股新闻，利用 LLM 进行摘要与情感打分（利好/利空）。
3.  **📈 K 线实验室 (Chart Lab)**: 基础行情展示及自动化技术形态识别，支持 AI 辅助 K 线分析。
4.  **🐉 资金透视 (Smart Money)**: 龙虎榜游资追踪与主力资金流向分析。
5.  **⚡ 短线雷达 (Short-term Radar)**: 盘中异动监控与竞价爆点捕捉。

## 技术栈 (Tech Stack)

### Backend (后端)
- **Framework**: Python FastAPI (高性能，便于处理异步任务)
- **Database**: PostgreSQL (业务数据) + Redis (行情缓存 & 消息队列)
- **Data Source**: AkShare (开源财经数据) / Tushare Pro
- **AI Engine**: LangChain + LangGraph + OpenAI API / 国内大模型 API (DeepSeek/Kimi/通义)
- **Task Queue**: Celery (用于定时抓取新闻和盘后分析)

### Frontend (前端)
- **Framework**: Flutter (跨平台 iOS/Android) 或 Uni-app (Vue生态)
- **Charts**: ECharts / MPAndroidChart

## 目录结构 (Directory Structure)

```text
/ruo
├── /backend
│   ├── /app
│   │   ├── /api           # API 路由接口
│   │   ├── /core          # 核心配置
│   │   ├── /crawlers      # 爬虫模块 (雪球/财联社)
│   │   ├── /services      # 业务逻辑 (AI Analysis, News Cleaner)
│   │   ├── /models        # 数据库模型
│   │   └── /llm_agent     # AI Agent (LangGraph 工作流)
│   ├── /tests             # 单元测试
│   └── main.py            # 启动入口
├── /frontend/web          # Web 前端代码
├── /docs                  # 产品文档与设计图
└── docker-compose.yml     # 容器编排

## 🚀 快速开始 (Getting Started)

### 环境要求 (Prerequisites)

- **Python**: >= 3.10 (建议使用 `uv` 管理依赖)
- **Node.js**: >= 18 (用于前端构建)
- **PostgreSQL**: >= 15
- **Redis**: >= 6

### 安装 (Installation)

1.  **克隆代码库**

    ```bash
    git clone <repository_url>
    cd ruo
    ```

2.  **后端环境配置**

    推荐使用 `uv` 进行快速依赖管理：

    ```bash
    cd backend
    # 安装依赖
    uv sync
    ```

    或者使用传统的 pip：

    ```bash
    cd backend
    pip install -r requirements.txt # 如果有 requirements.txt
    # 或者直接安装 pyproject.toml 依赖
    pip install .
    ```

3.  **前端环境配置**

    ```bash
    cd frontend/web
    npm install
    ```

### 配置 (Configuration)

在 `backend` 目录下创建 `.env` 文件：

```ini
# backend/.env

# 数据库配置
DATABASE_URL=postgresql://ruo:123456@localhost:5432/ruo

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# API 密钥 (按需配置)
DASHSCOPE_API_KEY=your_dashscope_key
OPENAI_API_KEY=your_openai_key
```

### 运行 (Running)

1.  **启动后端服务**

    ```bash
    cd backend
    # 使用 uv 运行
    uv run uvicorn main:app --reload --port 8000
    ```

    API 文档地址: http://localhost:8000/docs

2.  **启动前端服务**

    ```bash
    cd frontend/web
    npm run dev
    ```

    访问地址: http://localhost:5173

## 🐳 Docker 部署

使用 Docker Compose 一键启动所有服务（数据库、缓存、后端）：

```bash
docker-compose up -d
```

## 🤝 贡献指南 (Contributing)

欢迎提交 Pull Request 或 Issue！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证 (License)

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
