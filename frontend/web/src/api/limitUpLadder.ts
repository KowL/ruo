/**
 * 连板天梯 API
 * Limit Up Ladder API
 */
import client from './client';

export interface LimitUpStock {
  symbol: string;
  name: string;
  consecutive_days: number;
  change_pct: number;
  limit_time: string;
  last_limit_time: string;
  maintain_strength: number;
  reason: string;
  price: number;
}

export interface LimitUpStats {
  total_count: number;
  consecutive_2: number;
  consecutive_3: number;
  consecutive_4: number;
  consecutive_5_plus: number;
}

export interface LimitUpLadderLevel {
  level: number;
  name: string;
  count: number;
  stocks: {
    code: string;
    name: string;
    price: number;
    change_pct: number;
    turnover: number;
    reason: string;
    open_count: number;
    first_time: string;
    last_time: string;
    limit_up_count: number;
    seal_amount: number;
    industry: string;
  }[];
}

export interface LimitUpLadderData {
  levels: LimitUpLadderLevel[];
  total: number;
  max_level: number;
  update_time: string;
}

export interface LimitUpLadderResponse {
  success: boolean;
  data: LimitUpLadderData;
  count: number;
  message?: string;
}

export interface TodayLimitUpStock {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  reason: string;
  first_limit_time: string;
  last_limit_time: string;
  turnover: number;
}

export interface TodayLimitUpResponse {
  status: string;
  data: TodayLimitUpStock[];
  count: number;
  update_time: string;
  message?: string;
}

/**
 * 获取连板天梯数据
 * @param min_consecutive 最小连续涨停天数，默认 2
 * @param limit 返回数量限制，默认 50
 */
export const getLimitUpLadder = async (
  min_consecutive: number = 2,
  limit: number = 50,
  date: string = ''
): Promise<LimitUpLadderResponse> => {
  const params: any = { min_consecutive, limit };
  if (date) {
    params.date = date;
  }
  return client.get('/stock/limit-up-ladder', { params });
};

/**
 * 获取今日涨停板数据
 * @param limit 返回数量限制，默认 100
 */
export const getTodayLimitUp = async (
  limit: number = 100
): Promise<TodayLimitUpResponse> => {
  return client.get('/stock/today-limit-up', {
    params: { limit }
  });
};
