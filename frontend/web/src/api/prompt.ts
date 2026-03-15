/**
 * 提示词广场 API
 */

import client from './client';

export interface Prompt {
  id: number;
  name: string;
  description: string | null;
  content: string;
  category: string;
  is_official: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface PromptCreate {
  name: string;
  description?: string;
  content: string;
  category?: string;
  is_official?: boolean;
}

export interface PromptUpdate {
  name?: string;
  description?: string;
  content?: string;
  category?: string;
  is_official?: boolean;
}

/**
 * 获取提示词列表
 */
export async function getPrompts(params?: {
  skip?: number;
  limit?: number;
  category?: string;
  is_official?: boolean;
}): Promise<Prompt[]> {
  return client.get('/prompt', { params });
}

/**
 * 获取单个提示词
 */
export async function getPrompt(id: number): Promise<Prompt> {
  return client.get(`/prompt/${id}`);
}

/**
 * 创建提示词
 */
export async function createPrompt(data: PromptCreate): Promise<Prompt> {
  return client.post('/prompt', data);
}

/**
 * 更新提示词
 */
export async function updatePrompt(id: number, data: PromptUpdate): Promise<Prompt> {
  return client.put(`/prompt/${id}`, data);
}

/**
 * 删除提示词
 */
export async function deletePrompt(id: number): Promise<{ success: boolean; message: string }> {
  return client.delete(`/prompt/${id}`);
}
