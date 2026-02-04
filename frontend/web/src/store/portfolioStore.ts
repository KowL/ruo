import { create } from 'zustand';
import { Portfolio, PortfolioListResponse } from '@/types';
import { getPortfolioList, addPortfolio, deletePortfolio } from '@/api/portfolio';

interface PortfolioState {
  portfolios: Portfolio[];
  totalValue: number;
  totalCost: number;
  totalProfitLoss: number;
  totalProfitLossRatio: number;
  loading: boolean;
  error: string | null;

  // Actions
  fetchPortfolios: () => Promise<void>;
  addNewPortfolio: (data: any) => Promise<void>;
  removePortfolio: (id: number) => Promise<void>;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  portfolios: [],
  totalValue: 0,
  totalCost: 0,
  totalProfitLoss: 0,
  totalProfitLossRatio: 0,
  loading: false,
  error: null,

  fetchPortfolios: async () => {
    set({ loading: true, error: null });
    try {
      console.log('正在获取持仓列表...');
      const data: PortfolioListResponse = await getPortfolioList();
      console.log('获取成功:', data);
      set({
        portfolios: data.items,
        totalValue: data.totalValue,
        totalCost: data.totalCost,
        totalProfitLoss: data.totalProfitLoss,
        totalProfitLossRatio: data.totalProfitLossRatio,
        loading: false,
      });
    } catch (error: any) {
      console.error('获取持仓列表失败:', error);
      set({ error: error.message, loading: false });
    }
  },

  addNewPortfolio: async (data) => {
    set({ loading: true, error: null });
    try {
      console.log('正在添加持仓...', data);
      await addPortfolio({
        symbol: data.symbol,
        costPrice: data.costPrice,
        quantity: data.quantity,
        strategyTag: data.strategyTag,
      });
      console.log('添加成功，正在刷新列表...');
      // 重新获取列表
      const portfolioData = await getPortfolioList();
      set({
        portfolios: portfolioData.items,
        totalValue: portfolioData.totalValue,
        totalCost: portfolioData.totalCost,
        totalProfitLoss: portfolioData.totalProfitLoss,
        totalProfitLossRatio: portfolioData.totalProfitLossRatio,
        loading: false,
      });
      console.log('列表刷新成功');
    } catch (error: any) {
      console.error('添加持仓失败:', error);
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  removePortfolio: async (id) => {
    set({ loading: true, error: null });
    try {
      await deletePortfolio(id);
      // 重新获取列表
      const data = await getPortfolioList();
      set({
        portfolios: data.items,
        totalValue: data.totalValue,
        totalCost: data.totalCost,
        totalProfitLoss: data.totalProfitLoss,
        totalProfitLossRatio: data.totalProfitLossRatio,
        loading: false,
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));
