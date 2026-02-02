import client from './client';
import { ApiResponse, Portfolio, PortfolioListResponse } from '@/types';

// 获取持仓列表
export const getPortfolioList = async (userId: number = 1): Promise<PortfolioListResponse> => {
  const response = await client.get<any, ApiResponse<PortfolioListResponse>>('/portfolio/list', {
    params: { userId: userId },
  });
  return response.data!;
};

// 添加持仓
export const addPortfolio = async (data: {
  symbol: string;
  costPrice: number;
  quantity: number;
  strategyTag?: string;
}): Promise<Portfolio> => {
  const response = await client.post<any, ApiResponse<Portfolio>>('/portfolio/add', data);
  return response.data!;
};

// 删除持仓
export const deletePortfolio = async (portfolioId: number): Promise<void> => {
  await client.delete(`/portfolio/${portfolioId}`);
};

// 更新持仓
export const updatePortfolio = async (
  portfolioId: number,
  data: Partial<Portfolio>
): Promise<Portfolio> => {
  const response = await client.put<any, ApiResponse<Portfolio>>(
    `/portfolio/${portfolioId}`,
    data
  );
  return response.data!;
};
