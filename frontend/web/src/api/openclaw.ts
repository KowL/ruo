/**
 * OpenClaw API 客户端
 * 直接调用宿主机上的 OpenClaw Gateway
 */
import axios from 'axios';
import { useSettingsStore } from '@/store/settingsStore';

// 获取动态配置
const getGatewayConfig = () => {
  const store = useSettingsStore.getState();
  return {
    wsUrl: store.openclaw.gatewayWsUrl || 'ws://localhost:18789',
    token: store.openclaw.token || '',
  };
};

// 创建专用 axios 实例（动态配置）
const createGatewayClient = () => {
  const config = getGatewayConfig();
  return axios.create({
    baseURL: config.wsUrl.replace('ws://', 'http://').replace('wss://', 'https://'),
    timeout: 120000,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.token}`,
    },
    responseType: 'json',
  });
};

// ========================================
// 类型定义
// ========================================

export interface Agent {
  id: string;
  name: string;
  emoji: string;
  description: string;
  model: string;
  workspace?: string;
  capabilities?: string[];
  isDefault?: boolean;
  config?: {
    temperature: number;
    maxTokens: number;
    thinking: string;
  };
  systemPrompt?: string;
  identity?: {
    name: string;
    emoji: string;
    role: string;
    vibe: string;
  };
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface Session {
  sessionId: string;
  title?: string;
  messageCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  thinking?: string;
  timeout?: number;
}

export interface ChatResponse {
  sessionId: string;
  reply: string;
  thinking?: string;
  usage?: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  durationMs?: number;
}

// ========================================
// API 函数
// ========================================

// 默认 agents 列表
const DEFAULT_AGENTS: Agent[] = [];

/**
 * 测试 Gateway 连接
 */
export async function testConnection(): Promise<{ status: string; message: string }> {
  try {
    const config = getGatewayConfig();
    const client = createGatewayClient();
    // 尝试获取 agents 列表来测试连接
    const result = await client.get('/openclaw/agents');
    if (result.data?.status === 'success') {
      const agentCount = result.data.data?.length || 0;
      return { status: 'success', message: `连接成功 (${agentCount} 个 agents)` };
    }
    return { status: 'error', message: '连接失败' };
  } catch (error: any) {
    console.error('testConnection error:', error);
    return { status: 'error', message: error.message || '连接失败' };
  }
}

/**
 * 获取 Agents 列表 - 通过 CLI
 */
export async function listAgents(): Promise<{ status: string; data: Agent[] }> {
  try {
    // 通过后端 API 获取 agents 列表
    const client = createGatewayClient();
    const result = await client.get('/openclaw/agents');
    if (result.data?.status === 'success') {
      return result.data;
    }
    throw new Error('Invalid response');
  } catch (error: any) {
    console.error('listAgents error:', error);
    // 返回默认 agents 列表
    return {
      status: 'success',
      data: DEFAULT_AGENTS,
    };
  }
}

/**
 * 获取单个 Agent 详情
 */
export async function getAgent(agentId: string): Promise<{ status: string; data: Agent }> {
  const result = await listAgents();
  const agent = result.data.find(a => a.id === agentId);
  if (agent) {
    return { status: 'success', data: agent };
  }
  return { status: 'error', message: 'Agent not found' };
}

/**
 * 发送消息（非流式）
 */
export async function chat(
  agentId: string,
  request: ChatRequest
): Promise<{ status: string; data: ChatResponse }> {
  try {
    const config = getGatewayConfig();
    const client = createGatewayClient();
    const response = await client.post('/v1/chat/completions', {
      model: `openclaw:${agentId}`,
      messages: [{ role: 'user', content: request.message }],
      max_tokens: 4096,
      user: request.session_id,
    });

    const data = response.data;
    const content = data.choices?.[0]?.message?.content || '';
    const usage = data.usage || {};

    return {
      status: 'success',
      data: {
        sessionId: request.session_id || '',
        reply: content,
        usage: {
          inputTokens: usage.prompt_tokens || 0,
          outputTokens: usage.completion_tokens || 0,
          totalTokens: usage.total_tokens || 0,
        },
        durationMs: 0,
      },
    };
  } catch (error: any) {
    console.error('chat error:', error);
    return {
      status: 'error',
      data: {
        sessionId: request.session_id || '',
        reply: `请求失败: ${error.message}`,
      },
    };
  }
}

/**
 * 发送消息（流式）- 返回可读流
 */
export async function* chatStream(
  agentId: string,
  request: ChatRequest
): AsyncGenerator<string> {
  try {
    const config = getGatewayConfig();
    const response = await fetch(`${config.wsUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.token}`,
      },
      body: JSON.stringify({
        model: `openclaw:${agentId}`,
        messages: [{ role: 'user', content: request.message }],
        max_tokens: 4096,
        stream: true,
        user: request.session_id,
      }),
    });

    if (!response.ok) {
      yield `data: {"type": "error", "message": "Request failed"}\n\n`;
      return;
    }

    if (!response.body) {
      yield `data: {"type": "error", "message": "No response body"}\n\n`;
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    yield `data: {"type": "start", "sessionId": "${request.session_id || ''}"}\n\n`;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data !== '[DONE]') {
            yield `data: ${data}\n\n`;
          }
        }
      }
    }
  } catch (error: any) {
    console.error('chatStream error:', error);
    yield `data: {"type": "error", "message": "${error.message}"}\n\n`;
  }
}

/**
 * 列出所有会话（暂不支持，返回空列表）
 */
export async function listSessions(
  agentId: string
): Promise<{ status: string; data: Session[] }> {
  return { status: 'success', data: [] };
}

/**
 * 获取会话历史（暂不支持，返回空）
 */
export async function getSessionMessages(
  agentId: string,
  sessionId: string
): Promise<{
  status: string;
  data: {
    sessionId: string;
    agentId: string;
    messages: Message[];
    createdAt: string;
    updatedAt: string;
  };
}> {
  return {
    status: 'success',
    data: {
      sessionId,
      agentId,
      messages: [],
      createdAt: '',
      updatedAt: '',
    },
  };
}
