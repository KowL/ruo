import { create } from 'zustand';
import { Portfolio, PortfolioListResponse } from '@/types';
import { getPortfolioList, addPortfolio, deletePortfolio } from '@/api/portfolio';

interface PortfolioState {
  portfolios: Portfolio[];
  totalValue: number;
  totalCost: number;
  totalProfitLoss: number;
  loading: boolean;
  error: string | null;

  // Actions
  fetchPortfolios: () => Promise<void>;
  addNewPortfolio: (data: {
    symbol: string;
    cost_price: number;
    quantity: number;
    strategy_tag?: string;
  }) => Promise<void>;
  removePortfolio: (id: number) => Promise<void>;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  portfolios: [],
  totalValue: 0,
  totalCost: 0,
  totalProfitLoss: 0,
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
        totalValue: data.total_value,
        totalCost: data.total_cost,
        totalProfitLoss: data.total_profit_loss,
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
      await addPortfolio(data);
      console.log('添加成功，正在刷新列表...');
      // 重新获取列表
      const portfolioData = await getPortfolioList();
      set({
        portfolios: portfolioData.items,
        totalValue: portfolioData.total_value,
        totalCost: portfolioData.total_cost,
        totalProfitLoss: portfolioData.total_profit_loss,
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
        totalValue: data.total_value,
        totalCost: data.total_cost,
        totalProfitLoss: data.total_profit_loss,
        loading: false,
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },
}));
