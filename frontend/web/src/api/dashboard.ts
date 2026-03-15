import client from './client';

// 情绪分析结果
export interface SentimentData {
  score: number;  // 0-100
  label: string;  // 乐观/偏乐观/中性/偏悲观/悲观
  description: string;
  distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

// 市场广度
export interface MarketBreadth {
  up_count: number;
  down_count: number;
  flat_count: number;
  total: number;
  up_ratio: number;
  down_ratio: number;
  advance_decline_line: number;
}

// 板块轮动
export interface SectorRotation {
  name: string;
  change_pct: number;
  trend: 'up' | 'down' | 'neutral';
}

// 热门概念
export interface HotConcept {
  id: number;
  name: string;
  stock_count: number;
  description?: string;
}

// 仪表盘数据
export interface DashboardData {
  sentiment: SentimentData;
  market_breadth: MarketBreadth;
  sector_rotation: SectorRotation[];
  hot_concept: HotConcept[];
  stats: {
    recent_news_count: number;
    portfolio_count: number;
    update_time: string;
  };
}

// 获取市场情绪指数
export const getMarketSentiment = async (): Promise<SentimentData> => {
  const response = await client.get('/dashboard/sentiment');
  return response.data;
};

// 获取仪表盘完整数据
export const getDashboardData = async (): Promise<DashboardData> => {
  const response = await client.get('/dashboard/dashboard');
  return response.data;
};

// 获取市场广度
export const getMarketBreadth = async (): Promise<MarketBreadth> => {
  const response = await client.get('/dashboard/breadth');
  return response.data;
};

// 获取板块轮动
export const getSectorRotation = async (): Promise<SectorRotation[]> => {
  const response = await client.get('/dashboard/sector-rotation');
  return response.data;
};
