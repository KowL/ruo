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
  const response = await client.get<any, ApiResponse<KLineData[]>>(`/stock/kline/${symbol}`, {
    params: { period, limit },
  });
  return response.data || [];
};

// 获取分时数据 (Backend)
export const getTimeShareData = async (symbol: string): Promise<TimeShareData[]> => {
  const response = await client.get<any, ApiResponse<TimeShareData[]>>(`/timeshare/${symbol}`);
  return response.data || [];
};

// --- Eastmoney Direct API Helpers ---

// JSONP Helper
const jsonp = (url: string, callbackName: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    const name = `jsonp_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

    // Explicitly set the callback parameter if needed, but Eastmoney often hardcodes 'cb' or similar in query key
    // Here we assume the URL already has the callback placeholder or we append it.
    // Eastmoney typical format: ...&cb=jQuery...

    // We'll attach the callback to window
    (window as any)[name] = (data: any) => {
      resolve(data);
      document.body.removeChild(script);
      delete (window as any)[name];
    };

    // Replace 'cb=?' or append it
    const finalUrl = url.replace('cb=?', `cb=${name}`).replace('cb=cb', `cb=${name}`);

    script.src = finalUrl;
    script.onerror = (e) => {
      document.body.removeChild(script);
      delete (window as any)[name];
      reject(e);
    };
    document.body.appendChild(script);
  });
};

const getMarketId = (code: string) => {
  // 6 starts -> SH (1), others -> SZ (0) (Includes BJ usually as 0 in Eastmoney for trends, validation needed but 0 covers 0/3/4/8 usually)
  // Actually simpler rule: 6xx is SH (1), else SZ/BJ (0)
  if (code.startsWith('6')) return 1;
  return 0;
};

// 获取分时数据 (Eastmoney Direct)
// URL: https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market}.{code}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&cb=cb
// 获取分时数据 (Eastmoney Direct)
// URL: https://push2.eastmoney.com/api/qt/stock/trends2/get?secid={market}.{code}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&cb=cb
export const fetchIntradayData = async (symbol: string): Promise<{ name: string; preClose: number; trends: TimeShareData[] }> => {
  const market = getMarketId(symbol);
  // fields1: f1-f13. preClose is f4? Let's check Eastmoney docs or assumption.
  // Common Eastmoney fields1: 
  // f1=code, f2=market?, f3=name, f4=decimal_places?, f4=preClose? 
  // Let's rely on `data.prePrice`. Eastmoney usually returns `prePrice` in the root `data` object.
  const url = `https://push2.eastmoney.com/api/qt/stock/trends2/get?secid=${market}.${symbol}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&cb=cb`;

  try {
    const res = await jsonp(url, 'cb');
    if (res && res.data && res.data.trends) {
      const preClose = res.data.prePrice;
      const name = res.data.name;
      const trends = res.data.trends.map((line: string) => {
        const parts = line.split(',');
        return {
          time: parts[0],
          price: parseFloat(parts[2]),
          volume: parseFloat(parts[5]),
          avgPrice: parseFloat(parts[7])
        };
      });
      return { name, preClose, trends };
    }
  } catch (error) {
    console.error("Eastmoney fetch failed:", error);
  }
  return { name: '', preClose: 0, trends: [] };
};
