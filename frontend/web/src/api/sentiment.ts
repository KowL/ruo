import client from './client';

// 情绪指数数据（基于市场行情量化，无新闻依赖）
export interface SentimentIndex {
  date: string;
  index: number;           // 0-100，50为中性
  change: number;          // 较昨日变化
  label: string;           // 情绪标签
  advance_count: number;   // 持仓上涨股数
  decline_count: number;   // 持仓下跌股数
  flat_count: number;      // 持仓平盘股数
  avg_change_pct: number;  // 持仓平均涨跌幅 (%)
  avg_turnover: number;    // 持仓平均换手率 (%)
  volume_ratio: number;    // 成交额相对近5日均值倍数
  market_mood: '活跃' | '正常' | '低迷'; // 市场活跃度
  top_factors: string[];   // 主要特征描述
}

// 历史情绪数据
export interface SentimentHistoryItem {
  date: string;
  index: number;
  label: string;
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
