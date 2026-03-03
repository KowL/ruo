import client from './client';
import type { ApiResponse } from '@/types';
import type { RadarDashboard, RadarSignal } from '@/types/radar';

/**
 * 获取竞价爆点信号
 */
export function getAuctionSignals() {
  return client.get<any, ApiResponse<RadarSignal[]>>('/radar/auction-signals');
}

/**
 * 获取实时异动股票
 */
export function getIntradayMovers(minChangePct?: number) {
  const params = minChangePct ? { minChangePct } : {};
  return client.get<any, ApiResponse<RadarSignal[]>>('/radar/intraday-movers', { params });
}

/**
 * 获取涨停候选池
 */
export function getLimitUpCandidates() {
  return client.get<any, ApiResponse<RadarSignal[]>>('/radar/limit-up-candidates');
}

/**
 * 获取短线雷达仪表盘
 */
export function getRadarDashboard() {
  return client.get<any, ApiResponse<RadarDashboard>>('/radar/dashboard');
}
