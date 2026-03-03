/**
 * 策略管理类型定义
 */

export interface Strategy {
  id: number;
  name: string;
  description?: string;
  strategyType: 'trend_following' | 'mean_reversion' | 'breakout' | 'multi_factor';
  entryRules: StrategyRule[];
  exitRules: StrategyRule[];
  positionRules: PositionRules;
  riskRules: RiskRules;
  isActive: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  createdAt: string;
}

export interface StrategyRule {
  indicator: string;
  condition: string;
  weight: number;
}

export interface PositionRules {
  maxPositionPerStock: number;
  maxTotalPosition: number;
}

export interface RiskRules {
  stopLoss: number;
  takeProfit: number;
  maxHoldDays: number;
}

export interface StrategyTemplate {
  type: string;
  name: string;
  description: string;
}

export interface StrategySignal {
  id: number;
  strategyId: number;
  symbol: string;
  name?: string;
  signalType: 'buy' | 'sell' | 'hold';
  strength: number;
  suggestedPosition: number;
  triggerPrice?: number;
  stopLossPrice?: number;
  takeProfitPrice?: number;
  reason?: string;
  status: 'pending' | 'executed' | 'expired' | 'cancelled';
  isRead: number;
  createdAt: string;
}

export interface Backtest {
  id: number;
  strategyId: number;
  strategyName: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  profitFactor: number;
  status: 'running' | 'completed' | 'failed';
  createdAt: string;
  completedAt?: string;
}

export interface BacktestDetail extends Backtest {
  trades: TradeRecord[];
  dailyReturns: number[];
  equityCurve: EquityPoint[];
}

export interface TradeRecord {
  symbol: string;
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  shares: number;
  profit: number;
  returnPct: number;
  reason: string;
}

export interface EquityPoint {
  date: string;
  value: number;
}
