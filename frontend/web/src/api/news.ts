import client from './client';
import { ApiResponse, News } from '@/types';

// ==================== 新闻 API（按 DESIGN_NEWS.md） ====================

/**
 * 获取新闻列表
 */
export const getRawNews = async (
  source?: 'cls' | 'xueqiu',
  hours: number = 24,
  limit: number = 50
): Promise<News[]> => {
  const response = await client.get<any, ApiResponse<News[]>>(`/news/raw`, {
    params: { source, hours, limit },
  });
  return response.data || [];
};

/**
 * 获取财联社新闻
 */
export const getClsNews = async (
  hours: number = 24,
  limit: number = 50
): Promise<News[]> => {
  const response = await client.get<any, ApiResponse<News[]>>(`/news/raw/cls`, {
    params: { hours, limit },
  });
  return response.data || [];
};

/**
 * 获取雪球新闻
 */
export const getXueqiuNews = async (
  hours: number = 24,
  limit: number = 50
): Promise<News[]> => {
  const response = await client.get<any, ApiResponse<News[]>>(`/news/raw/xueqiu`, {
    params: { hours, limit },
  });
  return response.data || [];
};

/**
 * AI 分析新闻
 */
export const analyzeRawNews = async (
  newsId: number,
  aiAnalysis: string,
  relationStock?: string
): Promise<any> => {
  const response = await client.post<any, ApiResponse<any>>(
    `/news/raw/analyze/${newsId}`,
    null,
    {
      params: { ai_analysis: aiAnalysis, relation_stock: relationStock },
    }
  );
  return response.data || {};
};

/**
 * 获取股票相关新闻
 * 注意:这是一个临时实现,使用 getRawNews 并在前端过滤
 * TODO: 后端应该提供专门的股票新闻接口
 */
export const getStockNews = async (
  symbol: string,
  limit: number = 20,
  hours: number = 24
): Promise<News[]> => {
  // 获取所有新闻
  const allNews = await getRawNews(undefined, hours, limit * 2);
  
  // 过滤出与指定股票相关的新闻
  const filtered = allNews.filter(news => {
    if (!news.relationStock) return false;
    const stocks = news.relationStock.split(',').map(s => s.trim());
    return stocks.includes(symbol);
  });
  
  // 限制返回数量
  return filtered.slice(0, limit);
};
