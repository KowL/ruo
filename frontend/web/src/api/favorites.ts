/**
 * 自选管理 API
 */
import client from './client';

// 类型定义
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

export interface StockFavorite {
  id: number;
  userId: number;
  groupId: number;
  symbol: string;
  name: string;
  addedAt: string;
}

export interface SearchStock {
  symbol: string;
  name: string;
  sector?: string;
  industry?: string;
  market?: string;
  isFavorited: boolean;
}

// ==================== 分组管理 ====================

// 获取分组列表
export function getGroups() {
  return client.get<{ status: string; data: StockGroup[] }>('/favorite/groups');
}

// 创建分组
export function createGroup(data: { name: string; description?: string; isDefault?: boolean }) {
  return client.post<{ status: string; data: StockGroup }>('/favorite/groups', data);
}

// 更新分组
export function updateGroup(groupId: number, data: { name?: string; description?: string; isDefault?: boolean }) {
  return client.put<{ status: string; data: StockGroup }>(`/favorite/groups/${groupId}`, data);
}

// 删除分组
export function deleteGroup(groupId: number) {
  return client.delete<{ status: string }>(`/favorite/groups/${groupId}`);
}

// ==================== 自选股票管理 ====================

// 获取自选股票列表
export function getStocks(groupId?: number) {
  const params = groupId ? { group_id: groupId } : {};
  return client.get<{ status: string; data: StockFavorite[] }>('/favorite/stocks', { params });
}

// 添加自选股票
export function addStock(data: { groupId: number; symbol: string; name: string }) {
  return client.post<{ status: string; data: StockFavorite }>('/favorite/stocks', data);
}

// 删除自选股票
export function deleteStock(favoriteId: number) {
  return client.delete<{ status: string }>(`/favorite/stocks/${favoriteId}`);
}

// 移动自选股票到其他分组
export function moveStock(favoriteId: number, newGroupId: number) {
  return client.put<{ status: string; data: StockFavorite }>(`/favorite/stocks/${favoriteId}/move`, { newGroupId });
}

// 搜索股票
export function searchStocks(keyword: string) {
  return client.get<{ status: string; data: SearchStock[] }>('/favorite/stocks/search', {
    params: { keyword },
  });
}
