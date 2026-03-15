// 概念相关类型定义

export type StockPositioning = '龙头' | '中军' | '补涨' | '妖股' | '先锋';

export interface Concept {
  id: number;
  name: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ConceptStock {
  id: number;
  stock_symbol: string;
  stock_name?: string;
  positioning: StockPositioning;
  notes?: string;
  updated_at?: string;
}

export interface ConceptDetail extends Concept {
  stocks: ConceptStock[];
}

export interface ConceptListItem extends Concept {
  stock_count: number;
}

export interface CreateConceptRequest {
  name: string;
  description?: string;
}

export interface UpdateConceptRequest {
  name?: string;
  description?: string;
}

export interface AddStockToConceptRequest {
  stock_symbol: string;
  stock_name?: string;
  positioning?: StockPositioning;
  notes?: string;
}

export interface UpdateStockPositioningRequest {
  positioning?: StockPositioning;
  notes?: string;
}

// 定位选项
export const POSITIONING_OPTIONS: { value: StockPositioning; label: string; color: string }[] = [
  { value: '龙头', label: '龙头', color: '#ef4444' }, // red-500
  { value: '中军', label: '中军', color: '#3b82f6' }, // blue-500
  { value: '补涨', label: '补涨', color: '#22c55e' }, // green-500
  { value: '妖股', label: '妖股', color: '#a855f7' }, // purple-500
  { value: '先锋', label: '先锋', color: '#06b6d4' }, // cyan-500
];

// ==================== 市场数据/题材库相关类型 ====================

/** 概念/题材时长生命周期 */
export type ConceptLifecycle = '发酵期' | '高潮期' | '退潮期';

/** 概念库数据 - 用于市场行情分析 */
export interface ConceptMarketData {
  theme_name: string;
  theme_level: number;
  parent_theme: string | null;
  hot_score: number;
  limit_up_count: number;
  continuous_days: number;
  leader_stocks: ConceptMarketStock[];
  follower_stocks: ConceptMarketStock[];
  lifecycle: ConceptLifecycle;
  change_pct: number;
  turnover: number;
  fund_flow: number;
  update_time: string;
}

/** 概念库关联股票 */
export interface ConceptMarketStock {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  limit_up_days: number;
  reason: string;
  first_limit_time: string;
  last_limit_time: string;
  turnover: number;
  positioning?: StockPositioning;
}

/** 概念列表项 - 市场热度视图 */
export interface ConceptMarketListItem {
  theme_name: string;
  hot_score: number;
  limit_up_count: number;
  continuous_days: number;
  lifecycle: ConceptLifecycle;
  leader_stocks: ConceptMarketStock[];
  update_time: string;
}

/** 概念排行项 */
export interface ConceptRankingItem extends ConceptMarketListItem {}

/** 概念分布项 */
export interface ConceptDistributionItem {
  theme_name: string;
  limit_up_count: number;
  percentage: number;
  lifecycle: string;
  hot_score: number;
}

/** 涨停概念分布统计 */
export interface LimitUpConceptDistribution {
  total_limit_up: number;
  theme_count: number;
  distribution: ConceptDistributionItem[];
  lifecycle_stats: {
    发酵期: number;
    高潮期: number;
    退潮期: number;
  };
}

/** 概念库响应 */
export interface ConceptLibraryResponse {
  status: string;
  data: ConceptMarketListItem[];
  count: number;
  update_time: string;
}

/** 概念排行响应 */
export interface ConceptRankingResponse {
  status: string;
  data: ConceptRankingItem[];
  count: number;
  sort_by: string;
  update_time: string;
}

/** 概念市场详情响应 */
export interface ConceptMarketDetailResponse {
  status: string;
  data: ConceptMarketData;
}

/** 概念分布响应 */
export interface ConceptDistributionResponse {
  status: string;
  data: LimitUpConceptDistribution;
  update_time: string;
}
