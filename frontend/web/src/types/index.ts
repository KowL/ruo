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

// 股票新闻
export interface StockNews {
  id: number;
  title: string;
  source: string;
  publishTime: string;
  aiSummary?: string;
  sentimentLabel?: '利好' | '中性' | '利空';
  sentimentScore?: number;
  url?: string;
  stockSymbols?: string[];
  isFavorite?: boolean;
  symbol?: string;
  stockCode?: string;
  rawContent?: string;
  createdAt?: string;
}

// K线数据
export interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
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
}

// 策略标签类型
export type StrategyTag = '打板' | '低吸' | '趋势' | '其他';
