import client from './client';
import { ApiResponse, StockRealtime, KLineData } from '@/types';

// 分时数据
export interface TimeShareData {
  time: string;
  price: number;
  volume: number;
  avgPrice: number;
}

// 搜索股票
export const searchStock = async (keyword: string): Promise<any[]> => {
  const response = await client.get<any, ApiResponse<any[]>>('/stock/search', {
    params: { keyword },
  });
  return response.data || [];
};

// 获取实时行情
export const getStockRealtime = async (symbol: string): Promise<StockRealtime> => {
  const response = await client.get<any, ApiResponse<StockRealtime>>(
    `/stock/realtime/${symbol}`
  );
  return response.data!;
};

// 获取K线数据
export const getKLineData = async (
  symbol: string,
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  limit: number = 60
): Promise<KLineData[]> => {
  const response = await client.get<any, ApiResponse<KLineData[]>>(`/kline/${symbol}`, {
    params: { period, limit },
  });
  return response.data || [];
};

// 获取分时数据
export const getTimeShareData = async (symbol: string): Promise<TimeShareData[]> => {
  const response = await client.get<any, ApiResponse<TimeShareData[]>>(`/timeshare/${symbol}`);
  return response.data || [];
};
