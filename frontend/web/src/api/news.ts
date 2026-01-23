import client from './client';
import { ApiResponse, StockNews } from '@/types';

// 获取股票新闻
export const getStockNews = async (
  symbol: string,
  limit: number = 10,
  hours: number = 24
): Promise<StockNews[]> => {
  const response = await client.get<any, ApiResponse<StockNews[]>>(`/news/${symbol}`, {
    params: { limit, hours },
  });
  return response.data || [];
};
