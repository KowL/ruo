import client from './client';

// 情绪指数数据
export interface SentimentIndex {
  date: string;
  index: number;        // 0-100，50为中性
  change: number;       // 较昨日变化
  label: string;        // 情绪标签
  bullish: number;      // 利好数量
  bearish: number;      // 利空数量
  neutral: number;      // 中性数量
  avg_score: number;    // 平均评分 1-5
  news_count: number;   // 新闻总数
  top_factors: string[]; // 主要影响因素
}

// 历史情绪数据
export interface SentimentHistoryItem {
  date: string;
  index: number;
  label: string;
  news_count: number;
}

// 每日简报
export interface DailyReport {
  date: string;
  type: 'opening' | 'closing';
  sentiment_index: number;
  sentiment_label: string;
  report: string;       // 报告内容
  key_factors: string[];
}

// 获取最新情绪指数
export const getLatestSentiment = async (): Promise<SentimentIndex> => {
  const response = await client.get('/sentiment/latest');
  return response.data;
};

// 获取历史情绪走势
export const getSentimentHistory = async (days: number = 7): Promise<SentimentHistoryItem[]> => {
  const response = await client.get('/sentiment/history', { params: { days } });
  return response.data;
};

// 获取开盘简报
export const getOpeningReport = async (): Promise<DailyReport> => {
  const response = await client.get('/sentiment/daily-report/opening');
  return response.data;
};

// 获取收盘简报
export const getClosingReport = async (): Promise<DailyReport> => {
  const response = await client.get('/sentiment/daily-report/closing');
  return response.data;
};
