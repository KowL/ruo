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
