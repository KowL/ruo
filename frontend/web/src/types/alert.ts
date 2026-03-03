/**
 * 预警管理 API 类型定义
 */

export interface AlertRule {
  id: number;
  portfolioId: number;
  symbol: string;
  name: string;
  alertType: 'price_change' | 'profit_loss' | 'target_price';
  alertTypeName: string;
  thresholdValue: number;
  compareOperator: '>=' | '<=' | '>' | '<';
  isActive: number;
  cooldownMinutes: number;
  lastTriggeredAt?: string;
  triggerCount: number;
  notes?: string;
  createdAt: string;
}

export interface AlertLog {
  id: number;
  alertRuleId: number;
  portfolioId: number;
  symbol: string;
  triggerPrice: number;
  triggerValue: number;
  message: string;
  isRead: number;
  createdAt: string;
}

export interface CreateAlertRuleRequest {
  portfolioId: number;
  alertType: 'price_change' | 'profit_loss' | 'target_price';
  thresholdValue: number;
  compareOperator?: '>=' | '<=' | '>' | '<';
  cooldownMinutes?: number;
  notes?: string;
}

export interface UpdateAlertRuleRequest {
  alertType?: 'price_change' | 'profit_loss' | 'target_price';
  thresholdValue?: number;
  compareOperator?: '>=' | '<=' | '>' | '<';
  cooldownMinutes?: number;
  isActive?: number;
  notes?: string;
}

export interface TriggeredAlert {
  ruleId: number;
  portfolioId: number;
  symbol: string;
  name: string;
  alertType: string;
  triggerValue: number;
  thresholdValue: number;
  currentPrice: number;
  message: string;
  triggeredAt: string;
}
