/**
 * 龙虎榜分析类型定义
 */

// 龙虎榜个股数据
export interface LhbStock {
  symbol: string;
  name: string;
  date: string;
  closePrice: number;
  changePct: number;
  netBuyAmount: number;
  buyAmount: number;
  sellAmount: number;
  totalAmount: number;
  reason: string;
}

// 个股龙虎榜历史
export interface LhbStockHistory {
  date: string;
  closePrice: number;
  changePct: number;
  netBuyAmount: number;
  buyAmount: number;
  sellAmount: number;
  totalAmount: number;
  turnover: number;
  reason: string;
}

// 机构交易数据
export interface InstitutionalTrading {
  symbol: string;
  name: string;
  date: string;
  closePrice: number;
  changePct: number;
  netBuyAmount: number;
  buyAmount: number;
  sellAmount: number;
  buyCount: number;
  sellCount: number;
}

// 热门席位
export interface HotSeat {
  seatName: string;
  traderName: string;
  buyCount: number;
  sellCount: number;
  totalBuy: number;
  totalSell: number;
  netAmount: number;
  avgBuy: number;
  avgSell: number;
  isFamous: boolean;
}

// 知名游资动向
export interface FamousTrader {
  traderName: string;
  buyCount: number;
  sellCount: number;
  totalBuy: number;
  totalSell: number;
  netAmount: number;
  seats: string[];
}

// 市场情绪
export interface LhbMarketSentiment {
  date: string;
  sentiment: 'very_positive' | 'positive' | 'neutral' | 'negative';
  sentimentName: string;
  score: number;
  totalNetBuy: number;
  institutionalNetBuy: number;
  limitUpCount: number;
  totalStocks: number;
  analysis: string;
}

// 龙虎榜仪表盘
export interface LhbDashboard {
  dailyData: LhbStock[];
  institutionalData: InstitutionalTrading[];
  hotSeats: HotSeat[];
  famousTraders: {
    famousTraders: FamousTrader[];
    topTrader: FamousTrader | null;
    analysisDays: number;
    updateTime: string;
  };
  marketSentiment: LhbMarketSentiment;
  updateTime: string;
}
