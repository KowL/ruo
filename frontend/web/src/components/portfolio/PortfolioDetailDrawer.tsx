import React, { useState, useEffect } from 'react';
import { formatMoney, formatPercent } from '@/utils/format';
import clsx from 'clsx';

interface PortfolioDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  portfolio: any;
}

interface PortfolioAnalysis {
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
  // 成本推演数据
  simulationPrice: number;
  simulationProfitLoss: number;
  simulationProfitLossPercent: number;
  totalAssets: number;
  simulationTotalAssets: number;
  simulationTotalReturn: number;
  simulationTotalReturnPercent: number;
}

const PortfolioDetailDrawer: React.FC<PortfolioDetailDrawerProps> = ({
  isOpen,
  onClose,
  portfolio,
}) => {
  const [analysis, setAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [simulationPrice, setSimulationPrice] = useState(0);
  const [totalAssets, setTotalAssets] = useState(0);

  useEffect(() => {
    if (portfolio) {
      setSimulationPrice(portfolio.currentPrice);
      // 获取账户总资产（这里使用模拟数据）
      setTotalAssets(125800.50); // 从Dashboard获取
    }
  }, [portfolio]);

  useEffect(() => {
    if (portfolio && simulationPrice > 0) {
      const priceChange = simulationPrice - portfolio.avgPrice;
      const simulationProfitLoss = portfolio.shares * priceChange;
      const simulationProfitLossPercent = priceChange / portfolio.avgPrice * 100;
      const simulationTotalReturn = (totalAssets + simulationProfitLoss) - totalAssets;
      const simulationTotalReturnPercent = simulationTotalReturn / totalAssets * 100;

      setAnalysis({
        ...portfolio,
        simulationPrice,
        simulationProfitLoss,
        simulationProfitLossPercent,
        totalAssets,
        simulationTotalAssets: totalAssets + simulationProfitLoss,
        simulationTotalReturn,
        simulationTotalReturnPercent,
      });
    }
  }, [portfolio, simulationPrice, totalAssets]);

  const getProfitColor = (percent: number) => {
    return percent >= 0 ? 'text-[var(--color-profit-up)]' : 'text-[var(--color-loss-up)]';
  };

  const getProfitBgColor = (percent: number) => {
    return percent >= 0 ? 'bg-[var(--color-profit-up)]/20' : 'bg-[var(--color-loss-up)]/20';
  };

  if (!isOpen || !portfolio) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex">
      <div className="ml-auto w-[400px] h-full bg-[var(--color-surface-2)] shadow-xl">
        {/* 头部 */}
        <div className="p-4 border-b border-[var(--color-surface-3)] flex items-center justify-between">
          <h3 className="text-lg font-bold">持仓详情</h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[var(--color-surface-3)]"
          >
            ✕
          </button>
        </div>

        <div className="p-4 space-y-6 overflow-y-auto" style={{ height: 'calc(100% - 60px)' }}>
          {/* 基本信息 */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xl font-bold">{portfolio.symbol}</h4>
                <p className="text-sm text-[var(--color-text-secondary)]">{portfolio.name}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold numbers">{portfolio.shares}股</div>
                <div className="text-sm text-[var(--color-text-secondary)]">持仓数量</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm text-[var(--color-text-secondary)]">平均成本</div>
                <div className="font-bold numbers">¥{portfolio.avgPrice.toFixed(2)}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-[var(--color-text-secondary)]">当前价格</div>
                <div className="font-bold numbers">¥{portfolio.currentPrice.toFixed(2)}</div>
              </div>
            </div>
          </div>

          {/* 成本推演器 */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">成本推演器</h4>

            {/* 价格滑块 */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--color-text-secondary)]">调整股价</span>
                <span className="font-bold numbers">¥{simulationPrice.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max={portfolio.currentPrice * 3}
                step="0.01"
                value={simulationPrice}
                onChange={(e) => setSimulationPrice(parseFloat(e.target.value))}
                className="w-full h-2 bg-[var(--color-surface-3)] rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right,
                    var(--color-profit-up) 0%,
                    var(--color-profit-up) ${((simulationPrice - portfolio.avgPrice) / (portfolio.currentPrice * 3 - portfolio.avgPrice + 1)) * 100}%,
                    var(--color-surface-3) ${((simulationPrice - portfolio.avgPrice) / (portfolio.currentPrice * 3 - portfolio.avgPrice + 1)) * 100}%,
                    var(--color-surface-3) 100%)`
                }}
              />
              <div className="flex justify-between text-xs text-[var(--color-text-secondary)]">
                <span>¥0</span>
                <span>¥{(portfolio.currentPrice * 3).toFixed(0)}</span>
              </div>
            </div>

            {/* 推演结果 */}
            <div className={clsx('p-4 rounded-lg', getProfitBgColor(analysis?.simulationProfitLossPercent || 0))}>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--color-text-secondary)]">推演盈亏</span>
                  <span className={clsx('font-semibold', getProfitColor(analysis?.simulationProfitLossPercent || 0))}>
                    ¥{formatMoney(analysis?.simulationProfitLoss || 0)}
                    <span className="ml-1 text-sm">
                      ({formatPercent(analysis?.simulationProfitLossPercent || 0)})
                    </span>
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--color-text-secondary)]">账户总资产</span>
                  <span className="font-semibold">
                    ¥{formatMoney(analysis?.simulationTotalAssets || 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--color-text-secondary)]">总回撤/收益</span>
                  <span className={clsx('font-semibold', getProfitColor(analysis?.simulationTotalReturnPercent || 0))}>
                    {formatPercent(analysis?.simulationTotalReturnPercent || 0)}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-xs text-[var(--color-text-secondary)] italic">
              提示：拖动滑块模拟股价变动，实时查看对账户总资产的影响
            </div>
          </div>

          {/* AI 建议 */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold">AI 建议</h4>
            <div className="p-4 rounded-lg bg-[var(--color-ruo-purple)]/10 border border-[var(--color-ruo-purple)]/30">
              <div className="flex items-start space-x-3">
                <span className="text-xl text-[var(--color-ruo-purple)]">🤖</span>
                <div>
                  <p className="text-sm mb-2">基于当前持仓和市场分析：</p>
                  <ul className="text-xs space-y-1 text-[var(--color-text-secondary)]">
                    <li>• 当前股价偏离均线 {Math.abs(portfolio.currentPrice - portfolio.avgPrice).toFixed(2)} 元</li>
                    <li>• 建议关注支撑位 ¥{(portfolio.avgPrice * 0.95).toFixed(2)}</li>
                    <li>• 止损位设置在 ¥{(portfolio.avgPrice * 0.85).toFixed(2)}</li>
                    <li>• 止盈位建议设在 ¥{(portfolio.avgPrice * 1.3).toFixed(2)}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="space-y-2 pt-4 border-t border-[var(--color-surface-3)]">
            <button className="w-full py-2 px-4 bg-[var(--color-ruo-purple)] hover:bg-[var(--color-ruo-purple)]/80 text-white rounded-lg transition-colors">
              调整持仓策略
            </button>
            <button className="w-full py-2 px-4 border border-[var(--color-surface-3)] hover:bg-[var(--color-surface-3)] rounded-lg transition-colors">
              设置价格提醒
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioDetailDrawer;