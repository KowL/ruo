// 股票持仓类型（驼峰命名）
export interface Portfolio {
  id: number;
  symbol: string;
  name: string;
  costPrice: number;
  quantity: number;
  currentPrice: number;
  costValue: number;
  marketValue: number;
  profitLoss: number;
  profitLossRatio: number;
  changePct: number;
  strategyTag: string;
  notes?: string;
  hasNewNews: boolean;
  createdAt: string;
}

// 股票实时行情
export interface StockRealtime {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
}

// 新闻（按 DESIGN_NEWS.md）
export interface News {
  id: number;
  source: 'cls' | 'xueqiu';
  externalId: string;
  title: string;
  content: string;
  rawJson: string;
  publishTime: string;
  createdAt: string;
  relationStock?: string;  // 新闻关联的股票代码，逗号分隔，如 "600519,000001"
  relationStocks?: string[]; // 解析后的关联股票代码数组
  aiAnalysis?: string;    // AI 分析总结
  sentimentScore?: number; // 情绪分数 0-1,用于前端过滤
  isFavorite?: boolean;    // 是否收藏
  symbol?: string;         // 主要关联股票代码
}

// K线数据
export interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount?: number;
  change?: number;
  changePct?: number;
  turnover?: number;
}

// API 响应
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
}

// 持仓列表响应（与后端保持一致的命名）
export interface PortfolioListResponse {
  items: Portfolio[];
  totalValue: number;
  totalCost: number;
  totalProfitLoss: number;
  totalProfitLossRatio: number;
}

// 策略标签类型
// 策略标签类型
export type StrategyTag = '打板' | '低吸' | '趋势' | '其他';

// 股票搜索结果
export interface StockSearchResult {
  symbol: string;
  name: string;
  market: string;
  price?: number;
  changePct?: number;
}
