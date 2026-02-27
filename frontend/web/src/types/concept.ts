// 概念相关类型定义

export type StockPositioning = '龙头' | '中军' | '补涨' | '妖股';

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
];
