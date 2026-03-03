import client from './client';
import type {
  ConceptMovement,
  ConceptFundFlow,
  LimitUpStatistics,
  LeadingStock,
  MarketOverview,
  MonitorDashboard,
} from '../types/conceptMonitor';

interface ApiResponse<T> {
  status: string;
  data: T;
}

export const getMovementRanking = async (limit = 20): Promise<ConceptMovement[]> => {
  const response = await client.get<ApiResponse<ConceptMovement[]>>(`/concept-monitor/movement-ranking?limit=${limit}`);
  return response.data.data;
};

export const getFundFlowRanking = async (limit = 20): Promise<ConceptFundFlow[]> => {
  const response = await client.get<ApiResponse<ConceptFundFlow[]>>(`/concept-monitor/fund-flow?limit=${limit}`);
  return response.data.data;
};

export const getLimitUpStatistics = async (): Promise<LimitUpStatistics> => {
  const response = await client.get<ApiResponse<LimitUpStatistics>>('/concept-monitor/limit-up-statistics');
  return response.data.data;
};

export const getLeadingStocks = async (conceptName: string, limit = 5): Promise<LeadingStock[]> => {
  const response = await client.get<ApiResponse<LeadingStock[]>>(
    `/concept-monitor/leading-stocks?concept_name=${encodeURIComponent(conceptName)}&limit=${limit}`
  );
  return response.data.data;
};

export const getMarketOverview = async (): Promise<MarketOverview> => {
  const response = await client.get<ApiResponse<MarketOverview>>('/concept-monitor/market-overview');
  return response.data.data;
};

export const getMonitorDashboard = async (): Promise<MonitorDashboard> => {
  const response = await client.get<ApiResponse<MonitorDashboard>>('/concept-monitor/dashboard');
  return response.data.data;
};
