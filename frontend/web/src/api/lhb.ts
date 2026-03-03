import client from './client';
import type { ApiResponse } from '@/types';
import type { 
  LhbStock, 
  LhbStockHistory, 
  InstitutionalTrading, 
  HotSeat, 
  FamousTrader,
  LhbMarketSentiment,
  LhbDashboard 
} from '@/types/lhb';

/**
 * 获取每日龙虎榜
 */
export function getDailyLhb(date?: string) {
  const params = date ? { date } : {};
  return client.get<any, ApiResponse<LhbStock[]>>('/lhb/daily', { params });
}

/**
 * 获取个股龙虎榜详情
 */
export function getStockLhb(symbol: string, days?: number) {
  const params = days ? { days } : {};
  return client.get<any, ApiResponse<LhbStockHistory[]>>(`/lhb/stock/${symbol}`, { params });
}

/**
 * 获取机构交易数据
 */
export function getInstitutionalTrading(date?: string) {
  const params = date ? { date } : {};
  return client.get<any, ApiResponse<InstitutionalTrading[]>>('/lhb/institutional', { params });
}

/**
 * 获取热门游资席位
 */
export function getHotSeats(days?: number) {
  const params = days ? { days } : {};
  return client.get<any, ApiResponse<HotSeat[]>>('/lhb/hot-seats', { params });
}

/**
 * 获取知名游资动向
 */
export function getFamousTraders(days?: number) {
  const params = days ? { days } : {};
  return client.get<any, ApiResponse<{ famousTraders: FamousTrader[]; topTrader: FamousTrader | null; analysisDays: number; updateTime: string }>>('/lhb/famous-traders', { params });
}

/**
 * 获取龙虎榜市场情绪
 */
export function getLhbMarketSentiment(date?: string) {
  const params = date ? { date } : {};
  return client.get<any, ApiResponse<LhbMarketSentiment>>('/lhb/market-sentiment', { params });
}

/**
 * 获取龙虎榜仪表盘
 */
export function getLhbDashboard(date?: string) {
  const params = date ? { date } : {};
  return client.get<any, ApiResponse<LhbDashboard>>('/lhb/dashboard', { params });
}
