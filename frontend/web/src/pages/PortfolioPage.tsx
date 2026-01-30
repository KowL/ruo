import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import AddPortfolioModal from '@/components/portfolio/AddPortfolioModal';
import PortfolioDetailDrawer from '@/components/portfolio/PortfolioDetailDrawer';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';
import { formatMoney, formatPercent } from '@/utils/format';
import clsx from 'clsx';

// 策略类型
type StrategyType = 'grid' | 'long' | 'short' | 'momentum' | 'value';

interface PortfolioWithStrategy {
  id: number;
  symbol: string;
  name: string;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  cost: number;
  value: number;
  profitLoss: number;
  profitLossPercent: number;
  // 新增字段
  strategy?: StrategyType;
  aiStatus?: 'healthy' | 'warning' | 'danger';
  aiMessage?: string;
}

// 模拟AI分析数据
const mockAIData: Record<number, { strategy: StrategyType; status: 'healthy' | 'warning' | 'danger'; message: string }> = {
  1: { strategy: 'long', status: 'healthy', message: '符合策略预期' },
  2: { strategy: 'grid', status: 'warning', message: '偏离均线 5%，注意回调风险' },
  3: { strategy: 'short', status: 'danger', message: '触及止损线，建议卖出' },
  4: { strategy: 'momentum', status: 'healthy', message: '趋势保持良好' },
  5: { strategy: 'value', status: 'warning', message: '估值偏高，谨慎持有' },
};

// 获取策略标签样式
const getStrategyTag = (strategy?: StrategyType) => {
  const strategyMap: Record<StrategyType, { label: string; className: string }> = {
    grid: { label: '网格交易', className: 'tag-grid' },
    long: { label: '长线持有', className: 'tag-long' },
    short: { label: '短线博弈', className: 'tag-short' },
    momentum: { label: '趋势跟踪', className: 'tag-grid' },
    value: { label: '价值投资', className: 'tag-long' },
  };

  const config = strategyMap[strategy || 'long'];
  return (
    <span className={`tag ${config.className}`}>
      {config.label}
    </span>
  );
};

// 获取AI状态图标
const getAIStatus = (status?: 'healthy' | 'warning' | 'danger') => {
  const statusMap = {
    healthy: { emoji: '🟢', className: 'ai-status healthy' },
    warning: { emoji: '🟡', className: 'ai-status warning' },
    danger: { emoji: '🔴', className: 'ai-status danger' },
  };

  const config = statusMap[status || 'healthy'];
  return (
    <span
      className={config.className}
      data-tooltip={mockAIData[1].message}
    >
      {config.emoji}
    </span>
  );
};

const PortfolioPage: React.FC = () => {
  const {
    portfolios,
    totalValue,
    totalCost,
    totalProfitLoss,
    loading,
    fetchPortfolios,
    addNewPortfolio,
    removePortfolio,
  } = usePortfolioStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [selectedPortfolio, setSelectedPortfolio] = useState<PortfolioWithStrategy | null>(null);
  const [usMarket, setUsMarket] = useState(false);

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

  // 为持仓添加策略和AI数据
  const portfoliosWithStrategy = portfolios.map(portfolio => {
    const aiData = mockAIData[portfolio.id] || {
      strategy: 'long' as StrategyType,
      status: 'healthy' as const,
      message: '符合策略预期'
    };
    return {
      ...portfolio,
      strategy: aiData.strategy,
      aiStatus: aiData.status,
      aiMessage: aiData.message,
    };
  });

  const handleDelete = async (id: number) => {
    if (window.confirm('确定要删除这个持仓吗？')) {
      try {
        await removePortfolio(id);
        setToast({ message: '删除成功', type: 'success' });
      } catch (error) {
        setToast({ message: '删除失败，请重试', type: 'error' });
      }
    }
  };

  const handleAddPortfolio = async (data: any) => {
    try {
      await addNewPortfolio(data);
      setToast({ message: '添加成功！', type: 'success' });
    } catch (error) {
      throw error; // 重新抛出让 Modal 处理
    }
  };

  const handleRowClick = (portfolio: PortfolioWithStrategy) => {
    setSelectedPortfolio(portfolio);
  };

  const getProfitColor = (percent: number) => {
    return usMarket
      ? (percent >= 0 ? 'text-[var(--color-profit-down)]' : 'text-[var(--color-loss-down)]')
      : (percent >= 0 ? 'text-[var(--color-profit-up)]' : 'text-[var(--color-loss-up)]');
  };

  const getProfitBgColor = (percent: number) => {
    return usMarket
      ? (percent >= 0 ? 'bg-[var(--color-profit-down)]/20' : 'bg-[var(--color-loss-down)]/20')
      : (percent >= 0 ? 'bg-[var(--color-profit-up)]/20' : 'bg-[var(--color-loss-up)]/20');
  };

  if (loading && portfolios.length === 0) {
    return <Loading text="加载持仓中..." />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* 总览卡片 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">持仓总览</h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-[var(--color-text-secondary)]">市场模式:</span>
            <button
              onClick={() => setUsMarket(!usMarket)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${usMarket ? 'bg-[var(--color-profit-down)]/20 text-[var(--color-profit-down)]' : 'bg-[var(--color-profit-up)]/20 text-[var(--color-profit-up)]'}`}
            >
              {usMarket ? '美股' : 'A股'}
            </button>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-[var(--color-text-secondary)]">总市值</p>
            <p className="text-2xl font-bold numbers mt-1">¥{formatMoney(totalValue)}</p>
          </div>
          <div>
            <p className="text-sm text--[color-text-secondary)]">总成本</p>
            <p className="text-2xl font-bold numbers mt-1">¥{formatMoney(totalCost)}</p>
          </div>
          <div>
            <p className="text-sm text-[var(--color-text-secondary)]">总盈亏</p>
            <p className={clsx('text-2xl font-bold mt-1', getProfitColor(totalProfitLoss / totalCost * 100))}>
              ¥{formatMoney(totalProfitLoss)}
            </p>
            <p className="text-sm mt-1">
              {formatPercent(totalCost > 0 ? totalProfitLoss / totalCost : 0)}
            </p>
          </div>
        </div>
      </div>

      {/* 操作栏 */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">智能持仓</h2>
        <Button onClick={() => setIsModalOpen(true)} disabled={loading}>
          + 添加持仓
        </Button>
      </div>

      {/* 增强型表格 */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--color-surface-3)] text-left text-[var(--color-text-secondary)] text-sm">
                <th className="py-3 px-4">代码</th>
                <th className="py-3 px-4">名称</th>
                <th className="py-3 px-4 text-right">现价</th>
                <th className="py-3 px-4 text-right">盈亏</th>
                <th className="py-3 px-4">策略标签</th>
                <th className="py-3 px-4">AI建议</th>
                <th className="py-3 px-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {portfoliosWithStrategy.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center">
                    <p className="text-[var(--color-text-secondary)] mb-4">还没有添加持仓</p>
                    <Button onClick={() => setIsModalOpen(true)}>添加第一个持仓</Button>
                  </td>
                </tr>
              ) : (
                portfoliosWithStrategy.map((portfolio) => (
                  <tr
                    key={portfolio.id}
                    className={clsx(
                      'border-b border-[var(--color-surface-3)] hover:bg-[var(--color-surface-3)] cursor-pointer transition-colors',
                      getProfitBgColor(portfolio.profitLossPercent)
                    )}
                    onClick={() => handleRowClick(portfolio)}
                  >
                    <td className="py-3 px-4 font-medium numbers">{portfolio.symbol}</td>
                    <td className="py-3 px-4">{portfolio.name}</td>
                    <td className="py-3 px-4 text-right numbers">¥{portfolio.currentPrice.toFixed(2)}</td>
                    <td className={clsx('py-3 px-4 text-right', getProfitColor(portfolio.profitLossPercent))}>
                      <div className="numbers">
                        ¥{formatMoney(portfolio.profitLoss)}
                        <div className="text-sm font-normal">
                          {formatPercent(portfolio.profitLossPercent)}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {getStrategyTag(portfolio.strategy)}
                    </td>
                    <td className="py-3 px-4">
                      {getAIStatus(portfolio.aiStatus)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(portfolio.id);
                        }}
                        className="text-[var(--color-text-secondary)] hover:text-[var(--color-danger)] transition-colors p-2"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 添加持仓弹窗 */}
      <AddPortfolioModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleAddPortfolio}
      />

      {/* Toast 提示 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* 持仓详情抽屉 */}
      {selectedPortfolio && (
        <PortfolioDetailDrawer
          isOpen={!!selectedPortfolio}
          onClose={() => setSelectedPortfolio(null)}
          portfolio={selectedPortfolio}
        />
      )}
    </div>
  );
};

export default PortfolioPage;