# AI Console 接入 OpenClaw Gateway - 详细设计文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    AI Console                                       │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                              前端 (React)                                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │  │
│  │  │   Chat     │  │ Marketplace │  │  Settings │  │   Agent Cards          │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                          │                                          │
│                              ┌───────────▼───────────┐                              │
│                              │      API Gateway      │                              │
│                              │     (Express/Nest)    │                              │
│                              └───────────┬───────────┘                              │
└──────────────────────────────────────────┼──────────────────────────────────────────┘
                                           │
                       ┌───────────────────┼───────────────────┐
                       │                   │                   │
               ┌───────▼───────┐  ┌────────▼────────┐  ┌──────▼──────┐
               │  /api/agents  │  │ /api/chat      │  │ /api/health │
               │  /api/sessions│  │ /api/stream    │  │ /api/config │
               └───────────────┘  └─────────────────┘  └─────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │         OpenClaw Gateway (远程)             │
                    │         http://<host>:19000                │
                    └──────────────────────┬──────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼──────┐      ┌────────▼────────┐      ┌──────▼──────┐
            │  coder       │      │   trader       │      │   news      │
            │  Agent       │      │   Agent        │      │   Agent     │
            └──────────────┘      └────────────────┘      └─────────────┘
```

## 2. API 接口设计

### 2.1 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://<gateway-host>:18789` |
| 协议 | HTTP / HTTPS |
| 认证方式 | API Key (Header) |
| 响应格式 | JSON |
| 字符编码 | UTF-8 |

### 2.2 接口列表

#### 2.2.1 健康检查

```http
GET /health

Response:
{
  "status": "ok",
  "version": "2026.3.1",
  "uptime": 3600
}
```

#### 2.2.2 获取 Agents 列表

```http
GET /api/v1/agents
Authorization: Bearer <api-key>

Response:
{
  "status": "success",
  "data": [
    {
      "id": "main",
      "name": "ruo",
      "emoji": "🐟",
      "description": "默认主代理",
      "model": "kimi-coding/k2p5",
      "workspace": "/Users/lijun/.openclaw/workspace/main",
      "capabilities": ["对话", "推理", "任务执行"],
      "isDefault": true
    },
    {
      "id": "coder",
      "name": "CTO",
      "emoji": "💻",
      "description": "代码助手，擅长代码编写、调试、重构和代码审查",
      "model": "minimax-portal/MiniMax-M2.5",
      "workspace": "/Users/lijun/.openclaw/workspace/coder",
      "capabilities": ["代码", "架构", "技术审查"],
      "isDefault": false
    }
  ]
}
```

#### 2.2.3 获取单个 Agent 详情

```http
GET /api/v1/agents/:id
Authorization: Bearer <api-key>

Response:
{
  "status": "success",
  "data": {
    "id": "coder",
    "name": "CTO",
    "emoji": "💻",
    "description": "代码助手",
    "model": "minimax-portal/MiniMax-M2.5",
    "capabilities": ["代码", "架构", "技术审查"],
    "config": {
      "temperature": 0.7,
      "maxTokens": 4096,
      "thinking": "medium"
    },
    "systemPrompt": "你是李军的技术合伙人，负责...",
    "identity": {
      "name": "CTO",
      "emoji": "💻",
      "role": "AI技术合伙人",
      "vibe": "专业、直接、高效"
    }
  }
}
```

#### 2.2.4 发送消息（非流式）

```http
POST /api/v1/agents/:id/chat
Authorization: Bearer <api-key>
Content-Type: application/json

{
  "message": "帮我写一个快速排序算法",
  "sessionId": "optional-session-id",
  "thinking": "medium",
  "timeout": 120
}

Response:
{
  "status": "success",
  "data": {
    "sessionId": "abc123def456",
    "reply": "好的，这是一个快速排序算法的实现...\n\n```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    ...\n```",
    "thinking": "medium",
    "usage": {
      "inputTokens": 1200,
      "outputTokens": 800,
      "totalTokens": 2000
    },
    "durationMs": 3500
  }
}
```

#### 2.2.5 发送消息（流式）

```http
POST /api/v1/agents/:id/chat/stream
Authorization: Bearer <api-key>
Content-Type: application/json

{
  "message": "帮我写一个快速排序算法",
  "sessionId": "optional-session-id"
}

Response: text/event-stream

data: {"type": "start", "sessionId": "abc123"}
data: {"type": "chunk", "content": "好的"}
data: {"type": "chunk", "content": "，这是"}
data: {"type": "chunk", "content": "一个快速排序"}
...
data: {"type": "end", "usage": {...}}
```

#### 2.2.6 获取会话历史

```http
GET /api/v1/agents/:id/sessions/:sessionId/messages
Authorization: Bearer <api-key>

Response:
{
  "status": "success",
  "data": {
    "sessionId": "abc123",
    "agentId": "coder",
    "messages": [
      {
        "role": "user",
        "content": "你好",
        "timestamp": "2026-03-07T20:45:00Z"
      },
      {
        "role": "assistant",
        "content": "你好！我是 Coder，你的代码助手。",
        "timestamp": "2026-03-07T20:45:01Z"
      }
    ],
    "createdAt": "2026-03-07T20:45:00Z",
    "updatedAt": "2026-03-07T20:45:10Z"
  }
}
```

#### 2.2.7 列出所有会话

```http
GET /api/v1/agents/:id/sessions
Authorization: Bearer <api-key>

Response:
{
  "status": "success",
  "data": [
    {
      "sessionId": "abc123",
      "title": "排序算法",
      "messageCount": 5,
      "createdAt": "2026-03-07T20:45:00Z",
      "updatedAt": "2026-03-07T20:50:00Z"
    }
  ]
}
```

## 3. 后端服务设计

### 3.1 项目结构

```
ai-console-backend/
├── src/
│   ├── main.ts
│   ├── app.module.ts
│   │
│   ├── config/
│   │   └── configuration.ts
│   │
│   ├── common/
│   │   ├── guards/
│   │   │   └── api-key.guard.ts
│   │   └── interceptors/
│   │       └── logging.interceptor.ts
│   │
│   ├── modules/
│   │   ├── agents/
│   │   │   ├── agents.controller.ts
│   │   │   ├── agents.service.ts
│   │   │   ├── agents.module.ts
│   │   │   └── dto/
│   │   │       ├── chat.dto.ts
│   │   │       └── agent.dto.ts
│   │   │
│   │   ├── chat/
│   │   │   ├── chat.controller.ts
│   │   │   ├── chat.service.ts
│   │   │   └── chat.module.ts
│   │   │
│   │   ├── sessions/
│   │   │   ├── sessions.controller.ts
│   │   │   ├── sessions.service.ts
│   │   │   └── sessions.module.ts
│   │   │
│   │   └── health/
│   │       ├── health.controller.ts
│   │       └── health.module.ts
│   │
│   └── services/
│       ├── openclaw.service.ts
│       └── cache.service.ts
│
├── Dockerfile
├── docker-compose.yml
└── package.json
```

### 3.2 核心服务实现

#### 3.2.1 OpenClaw Gateway 调用服务

```typescript
// src/services/openclaw.service.ts
import { Injectable } from '@nestjs/common';
import axios, { AxiosInstance } from 'axios';

@Injectable()
export class OpenClawService {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.OPENCLAW_GATEWAY_URL || 'http://localhost:19000';
    this.apiKey = process.env.OPENCLAW_API_KEY || '';
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
    });
  }

  async listAgents() {
    const response = await this.client.get('/api/v1/agents');
    return response.data.data;
  }

  async getAgent(id: string) {
    const response = await this.client.get(`/api/v1/agents/${id}`);
    return response.data.data;
  }

  async chat(agentId: string, message: string, options = {}) {
    const response = await this.client.post(
      `/api/v1/agents/${agentId}/chat`,
      { message, ...options },
      { timeout: (options.timeout || 120) * 1000 }
    );
    return response.data.data;
  }

  async chatStream(agentId: string, message: string, options = {}) {
    const response = await this.client.post(
      `/api/v1/agents/${agentId}/chat/stream`,
      { message, ...options },
      { responseType: 'stream' }
    );
    return response.data;
  }
}
```

## 4. 前端设计

### 4.1 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript |
| 构建工具 | Vite |
| 状态管理 | Zustand |
| HTTP Client | Axios |
| UI 组件 | 自定义 + Tailwind CSS |
| 实时通信 | Server-Sent Events (SSE) |

### 4.2 页面结构

```
src/
├── App.tsx
├── api/
│   └── openclaw.ts
├── components/
│   ├── Layout/MainLayout.tsx
│   ├── Chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageList.tsx
│   │   └── MessageInput.tsx
│   └── Agents/
│       ├── AgentList.tsx
│       └── AgentSettings.tsx
├── pages/
│   ├── ChatPage.tsx
│   ├── MarketplacePage.tsx
│   └── SettingsPage.tsx
├── stores/
│   ├── agentStore.ts
│   └── chatStore.ts
└── hooks/
    ├── useChat.ts
    └── useAgents.ts
```

## 5. 部署配置

### 5.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-console-backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - OPENCLAW_GATEWAY_URL=http://192.168.1.100:19000
      - OPENCLAW_API_KEY=${OPENCLAW_API_KEY}
    restart: unless-stopped

  ai-console-frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - ai-console-backend
    environment:
      - VITE_API_URL=http://localhost:3001
    restart: unless-stopped
```

### 5.2 环境变量

#### Backend (.env)
```bash
OPENCLAW_GATEWAY_URL=http://192.168.1.100:19000
OPENCLAW_API_KEY=your-api-key-here
PORT=3001
NODE_ENV=production
```

#### Frontend (.env)
```bash
VITE_API_URL=http://localhost:3001
```

## 6. 安全设计

### 6.1 API Key 认证

```
1. 客户端发起请求
   GET /api/v1/agents
   Authorization: Bearer <api-key>

2. Gateway 验证 API Key

3. 转发到 OpenClaw Gateway

4. 返回响应
```

### 6.2 生成 API Key

```bash
# 在 OpenClaw Gateway 机器上
openclaw config set gateway.apiKey <your-secret-key>
```

## 7. OpenClaw 可用 Agents

| Agent ID | 名称 | 描述 | 模型 |
|----------|------|------|------|
| main | 🐟 ruo | 默认主代理 | kimi-coding/k2p5 |
| coder | 💻 CTO | 代码助手 | minimax-portal/MiniMax-M2.5 |
| trader | 📈 Trader | 交易员 | minimax-portal/MiniMax-M2.5 |
| news | 📰 News | 新闻助手 | minimax-portal/MiniMax-M2.5 |
| cxq_trader | 🐉 陈小群 | 交易代理 | kimi-coding/k2p5 |
| paopao | 🫧 Paopao | 泡泡助手 | minimax-portal/MiniMax-M2.5 |

## 8. 实施计划

| 阶段 | 任务 | 预估时间 |
|------|------|----------|
| 1 | 需求确认与原型设计 | 1天 |
| 2 | 后端 API 开发 | 2天 |
| 3 | 前端框架搭建 | 1天 |
| 4 | Chat 页面开发 | 2天 |
| 5 | Marketplace 页面 | 1天 |
| 6 | Agent 设置面板 | 1天 |
| 7 | 部署与测试 | 1天 |
| **总计** | | **9天** |

---

*文档创建时间: 2026-03-07*
