import client from './client';
import type { ApiResponse } from '@/types';
import type {
  Strategy,
  StrategyTemplate,
  StrategySignal
} from '@/types/strategy';

/**
 * 获取策略模板
 */
export function getStrategyTemplates() {
  return client.get<any, ApiResponse<StrategyTemplate[]>>('/strategies/templates');
}

/**
 * 创建策略
 */
export function createStrategy(data: {
  name: string;
  strategyType: string;
  description?: string;
  entryRules?: any[];
  exitRules?: any[];
  positionRules?: any;
  riskRules?: any;
}) {
  return client.post<any, ApiResponse<Strategy>>('/strategies', data);
}

/**
 * 获取策略列表
 */
export function getStrategies() {
  return client.get<any, ApiResponse<Strategy[]>>('/strategies');
}

/**
 * 获取策略详情
 */
export function getStrategy(strategyId: number) {
  return client.get<any, ApiResponse<Strategy>>(`/strategies/${strategyId}`);
}

/**
 * 更新策略
 */
export function updateStrategy(strategyId: number, data: Partial<Strategy>) {
  return client.put<any, ApiResponse<Strategy>>(`/strategies/${strategyId}`, data);
}

/**
 * 删除策略
 */
export function deleteStrategy(strategyId: number) {
  return client.delete<any, ApiResponse<void>>(`/strategies/${strategyId}`);
}

/**
 * 生成策略信号
 */
export function generateSignals(strategyId: number, symbols: string[]) {
  return client.post<any, ApiResponse<StrategySignal[]>>(`/strategies/${strategyId}/signals`, { symbols });
}

/**
 * 获取策略信号
 */
export function getSignals(strategyId: number, status?: string) {
  const params = status ? { status } : {};
  return client.get<any, ApiResponse<StrategySignal[]>>(`/strategies/${strategyId}/signals`, { params });
}

/**
 * 更新信号状态
 */
export function updateSignalStatus(signalId: number, status: string) {
  return client.put<any, ApiResponse<void>>(`/strategies/signals/${signalId}?status=${status}`);
}
