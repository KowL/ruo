import client from './client';
import type { ApiResponse } from '@/types';
import type { 
  Strategy, 
  StrategyTemplate, 
  StrategySignal, 
  Backtest, 
  BacktestDetail 
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

/**
 * 运行回测
 */
export function runBacktest(data: {
  strategyId: number;
  startDate: string;
  endDate: string;
  initialCapital?: number;
  symbols?: string[];
}) {
  return client.post<any, ApiResponse<Backtest>>('/backtest/run', data);
}

/**
 * 获取回测列表
 */
export function getBacktests(strategyId?: number) {
  const params = strategyId ? { strategyId } : {};
  return client.get<any, ApiResponse<Backtest[]>>('/backtest', { params });
}

/**
 * 获取回测详情
 */
export function getBacktestDetail(backtestId: number) {
  return client.get<any, ApiResponse<BacktestDetail>>(`/backtest/${backtestId}`);
}

/**
 * 删除回测
 */
export function deleteBacktest(backtestId: number) {
  return client.delete<any, ApiResponse<void>>(`/backtest/${backtestId}`);
}

/**
 * 对比回测
 */
export function compareBacktests(backtestIds: number[]) {
  return client.post<any, ApiResponse<{
    backtests: Backtest[];
    metrics: {
      total_return: number[];
      max_drawdown: number[];
      sharpe_ratio: number[];
      win_rate: number[];
    };
    winner: {
      backtest_id: number;
      strategy_name: string;
      total_return: number;
      max_drawdown: number;
      sharpe_ratio: number;
    };
  }>>('/backtest/compare', { backtestIds });
}
