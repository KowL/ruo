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
  const res = await client.get<any, ApiResponse<any[]>>('/stock/search', {
    params: { keyword },
  });
  // client 拦截器已返回 response.data
  return res?.data || [];
};

// 获取实时行情
export const getStockRealtime = async (symbol: string): Promise<StockRealtime> => {
  const res = await client.get<any, ApiResponse<StockRealtime>>(
    `/stock/realtime/${symbol}`
  );
  // client 拦截器已返回 response.data = { status, data }
  return res?.data!;
};

// 获取K线数据
export const getKLineData = async (
  symbol: string,
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  limit: number = 60
): Promise<KLineData[]> => {
  const res = await client.get<any, ApiResponse<KLineData[]>>(`/stock/kline/${symbol}`, {
    params: { period, limit },
  });
  // client 拦截器已返回 response.data = { status, data }
  return res?.data || [];
};

// 获取分时数据 (Backend)
export const getTimeShareData = async (symbol: string): Promise<TimeShareData[]> => {
  const res = await client.get<any, ApiResponse<TimeShareData[]>>(`/stock/timeshare/${symbol}`);
  // client 拦截器已返回 response.data = { status, data }
  return res?.data || [];
};

// --- Eastmoney Direct API Helpers ---

// 获取分时数据 (Eastmoney Direct)
// URL: https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market}.{code}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&cb=cb
// 获取分时数据 (Eastmoney Direct)
// URL: https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market}.{code}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&cb=cb
export const fetchIntradayData = async (symbol: string): Promise<{ name: string; preClose: number; trends: TimeShareData[] }> => {
  // 使用后端 API 获取分时数据
  try {
    const res = await client.get<any, ApiResponse<any>>(`/stock/timeshare/${symbol}`);
    // client 拦截器已返回 response.data = { status, data }
    const data = res?.data || [];

    // 转换后端数据格式为前端需要的格式
    const trends = data.map((item: any) => ({
      time: item.time,
      price: item.price,
      volume: item.volume,
      avgPrice: item.avgPrice || 0
    }));

    // 从第一条数据获取昨收价（如果存在）
    const preClose = trends.length > 0 ? trends[0].price - (data[0]?.change || 0) : 0;

    return { name: '', preClose, trends };
  } catch (error) {
    console.error("获取分时数据失败:", error);
    return { name: '', preClose: 0, trends: [] };
  }
};
