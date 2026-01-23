import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import PortfolioCard from '@/components/portfolio/PortfolioCard';
import AddPortfolioModal from '@/components/portfolio/AddPortfolioModal';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';
import { formatMoney, formatPercent, getRiseOrFallClass } from '@/utils/format';
import clsx from 'clsx';

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

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

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

  if (loading && portfolios.length === 0) {
    return <Loading text="加载持仓中..." />;
  }

  return (
    <div className="space-y-6">
      {/* 总览卡片 */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg p-6 text-white">
        <h2 className="text-lg font-medium mb-4">持仓总览</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm opacity-90">总市值</p>
            <p className="text-2xl font-bold mt-1">{formatMoney(totalValue)}</p>
          </div>
          <div>
            <p className="text-sm opacity-90">总成本</p>
            <p className="text-2xl font-bold mt-1">{formatMoney(totalCost)}</p>
          </div>
          <div>
            <p className="text-sm opacity-90">总盈亏</p>
            <p
              className={clsx(
                'text-2xl font-bold mt-1',
                totalProfitLoss > 0 ? 'text-yellow-300' : totalProfitLoss < 0 ? 'text-red-300' : ''
              )}
            >
              {formatMoney(totalProfitLoss)}
            </p>
            <p className="text-sm mt-1">
              {formatPercent(totalCost > 0 ? totalProfitLoss / totalCost : 0)}
            </p>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">我的持仓</h2>
        <Button onClick={() => setIsModalOpen(true)} disabled={loading}>
          + 添加持仓
        </Button>
      </div>

      {/* 持仓列表 */}
      {portfolios.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">还没有添加持仓</p>
          <Button onClick={() => setIsModalOpen(true)}>添加第一个持仓</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {portfolios.map((portfolio) => (
            <PortfolioCard
              key={portfolio.id}
              portfolio={portfolio}
              onClick={() => {
                // 跳转到详情页（可以后续实现）
                console.log('查看详情:', portfolio.symbol);
              }}
              onDelete={() => handleDelete(portfolio.id)}
            />
          ))}
        </div>
      )}

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
    </div>
  );
};

export default PortfolioPage;
