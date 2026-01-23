// 股票持仓类型
export interface Portfolio {
  id: number;
  symbol: string;
  name: string;
  cost_price: number;
  quantity: number;
  current_price?: number;
  profit_loss?: number;
  profit_loss_ratio?: number;
  strategy_tag?: string;
  has_new_news?: boolean;
  created_at?: string;
}

// 股票实时行情
export interface StockRealtime {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
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
  publish_time: string;
  ai_summary?: string;
  sentiment_label?: '利好' | '中性' | '利空';
  sentiment_score?: number;
  url?: string;
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

// 持仓列表响应
export interface PortfolioListResponse {
  items: Portfolio[];
  total_value: number;
  total_cost: number;
  total_profit_loss: number;
}

// 策略标签类型
export type StrategyTag = '打板' | '低吸' | '趋势' | '其他';
