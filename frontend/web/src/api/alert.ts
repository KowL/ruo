import client from './client';
import type { 
  AlertRule, 
  AlertLog, 
  CreateAlertRuleRequest, 
  UpdateAlertRuleRequest,
  TriggeredAlert 
} from '@/types/alert';
import type { ApiResponse } from '@/types';

/**
 * 创建预警规则
 */
export function createAlertRule(data: CreateAlertRuleRequest) {
  return client.post<any, ApiResponse<AlertRule>>('/alerts/rules', data);
}

/**
 * 获取预警规则列表
 */
export function getAlertRules(portfolioId?: number) {
  const params = portfolioId ? { portfolioId } : {};
  return client.get<any, ApiResponse<AlertRule[]>>('/alerts/rules', { params });
}

/**
 * 获取预警规则详情
 */
export function getAlertRuleDetail(ruleId: number) {
  return client.get<any, ApiResponse<AlertRule>>(`/alerts/rules/${ruleId}`);
}

/**
 * 更新预警规则
 */
export function updateAlertRule(ruleId: number, data: UpdateAlertRuleRequest) {
  return client.put<any, ApiResponse<AlertRule>>(`/alerts/rules/${ruleId}`, data);
}

/**
 * 删除预警规则
 */
export function deleteAlertRule(ruleId: number) {
  return client.delete<any, ApiResponse<void>>(`/alerts/rules/${ruleId}`);
}

/**
 * 手动检查预警
 */
export function checkAlerts() {
  return client.post<any, ApiResponse<TriggeredAlert[]>>('/alerts/check');
}

/**
 * 获取预警记录
 */
export function getAlertLogs(params?: { portfolioId?: number; isRead?: number; limit?: number }) {
  return client.get<any, ApiResponse<AlertLog[]>>('/alerts/logs', { params });
}

/**
 * 标记预警已读
 */
export function markAlertRead(logId: number) {
  return client.put<any, ApiResponse<void>>(`/alerts/logs/${logId}/read`);
}

/**
 * 获取未读预警数量
 */
export function getUnreadAlertCount() {
  return client.get<any, ApiResponse<{ unreadCount: number }>>('/alerts/unread-count');
}
