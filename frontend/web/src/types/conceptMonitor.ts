export interface ConceptMovement {
  name: string;
  change_pct: number;
  total_mv: number;
  turnover: number;
  leading_stocks: string[];
  up_count: number;
  down_count: number;
  limit_up_count: number;
}

export interface ConceptFundFlow {
  name: string;
  main_net_inflow: number;
  main_net_inflow_pct: number;
  retail_net_inflow: number;
  total_amount: number;
}

export interface LimitUpStock {
  symbol: string;
  name: string;
  price: number;
  limit_up_days: number;
}

export interface ConceptLimitUp {
  name: string;
  limit_up_count: number;
  stocks: LimitUpStock[];
}

export interface LimitUpStatistics {
  total_limit_up: number;
  update_time: string;
  concept_ranking: ConceptLimitUp[];
}

export interface LeadingStock {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  turnover: number;
  market_cap: number;
}

export interface MarketOverview {
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up_count: number;
  limit_down_count: number;
  total: number;
  update_time: string;
}

export interface MonitorDashboard {
  movement_ranking: ConceptMovement[];
  fund_flow_ranking: ConceptFundFlow[];
  limit_up_statistics: LimitUpStatistics;
  market_overview: MarketOverview;
}
