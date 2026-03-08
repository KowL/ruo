/**
 * OpenClaw API 客户端
 */
import client from './client';

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

/**
 * 获取 Agents 列表
 */
export async function listAgents(): Promise<{ status: string; data: Agent[] }> {
  return client.get('/openclaw/agents');
}

/**
 * 获取单个 Agent 详情
 */
export async function getAgent(agentId: string): Promise<{ status: string; data: Agent }> {
  return client.get(`/openclaw/agents/${agentId}`);
}

/**
 * 发送消息（非流式）
 */
export async function chat(
  agentId: string,
  request: ChatRequest
): Promise<{ status: string; data: ChatResponse }> {
  return client.post(`/openclaw/agents/${agentId}/chat`, request);
}

/**
 * 发送消息（流式）- 返回原始 response 用于处理流
 */
export function chatStream(agentId: string, request: ChatRequest) {
  return client.post(`/openclaw/agents/${agentId}/chat/stream`, request, {
    responseType: 'stream',
  });
}

/**
 * 列出所有会话
 */
export async function listSessions(
  agentId: string
): Promise<{ status: string; data: Session[] }> {
  return client.get(`/openclaw/agents/${agentId}/sessions`);
}

/**
 * 获取会话历史
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
  return client.get(`/openclaw/agents/${agentId}/sessions/${sessionId}/messages`);
}
