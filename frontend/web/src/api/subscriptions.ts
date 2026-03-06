/**
 * 策略订阅 API
 */
import client from './client';

// 类型定义
export interface Subscription {
  id: number;
  userId: number;
  strategyId: number;
  strategyName: string;
  stockPoolType: 'all' | 'group' | 'custom';
  stockGroupId?: number;
  customSymbols?: string[];
  notifyEnabled: boolean;
  notifyChannels: string[];
  stockPoolCount: number;
  createdAt: string;
  updatedAt?: string;
}

export interface StockGroup {
  id: number;
  userId: number;
  name: string;
  description?: string;
  isDefault: boolean;
  stockCount: number;
  createdAt: string;
  updatedAt?: string;
}

// 获取订阅列表
export function getSubscriptions(strategyId?: number) {
  const params = strategyId ? { strategy_id: strategyId } : {};
  return client.get<{ status: string; data: Subscription[] }>('/subscriptions', { params });
}

// 创建订阅
export function createSubscription(data: {
  strategyId: number;
  stockPoolType?: 'all' | 'group' | 'custom';
  stockGroupId?: number;
  customSymbols?: string[];
  notifyEnabled?: boolean;
  notifyChannels?: string[];
}) {
  return client.post<{ status: string; data: Subscription }>('/subscriptions', data);
}

// 更新订阅
export function updateSubscription(
  subscriptionId: number,
  data: {
    stockPoolType?: 'all' | 'group' | 'custom';
    stockGroupId?: number;
    customSymbols?: string[];
    notifyEnabled?: boolean;
    notifyChannels?: string[];
  }
) {
  return client.put<{ status: string; data: Subscription }>(`/subscriptions/${subscriptionId}`, data);
}

// 删除订阅
export function deleteSubscription(subscriptionId: number) {
  return client.delete<{ status: string }>(`/subscriptions/${subscriptionId}`);
}

// 获取订阅详情
export function getSubscription(subscriptionId: number) {
  return client.get<{ status: string; data: Subscription }>(`/subscriptions/${subscriptionId}`);
}

// 获取自选分组列表（订阅页面用）
export function getGroups() {
  return client.get<{ status: string; data: StockGroup[] }>('/favorites/groups');
}
