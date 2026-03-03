/**
 * 短线雷达类型定义
 */

export interface RadarSignal {
  symbol: string;
  name: string;
  signalType: string;
  signalName: string;
  price?: number;
  openPct?: number;
  changePct?: number;
  volume: number;
  amount: number;
  signalStrength: number;
  reason: string;
  timestamp: string;
}

export interface RadarDashboard {
  auctionSignals: RadarSignal[];
  intradayMovers: RadarSignal[];
  limitUpCandidates: RadarSignal[];
  updateTime: string;
}
