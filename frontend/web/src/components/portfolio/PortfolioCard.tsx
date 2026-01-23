import React from 'react';
import Card from '../common/Card';
import { Portfolio } from '@/types';
import { formatMoney, formatPercent, getRiseOrFallClass } from '@/utils/format';
import clsx from 'clsx';

interface PortfolioCardProps {
  portfolio: Portfolio;
  onClick?: () => void;
  onDelete?: () => void;
}

const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio, onClick, onDelete }) => {
  const {
    name,
    symbol,
    current_price,
    cost_price,
    quantity,
    profit_loss = 0,
    profit_loss_ratio = 0,
    strategy_tag,
    has_new_news,
  } = portfolio;

  return (
    <Card className="relative" onClick={onClick}>
      {/* 新消息提示 */}
      {has_new_news && (
        <div className="absolute top-2 right-2">
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}

      <div className="space-y-3">
        {/* 股票名称和代码 */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{name}</h3>
            <p className="text-sm text-gray-500">{symbol}</p>
          </div>
          {strategy_tag && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
              {strategy_tag}
            </span>
          )}
        </div>

        {/* 价格信息 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500">现价</p>
            <p className="text-lg font-semibold">{current_price?.toFixed(2) || '--'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">成本</p>
            <p className="text-lg font-semibold">{cost_price.toFixed(2)}</p>
          </div>
        </div>

        {/* 盈亏信息 */}
        <div className="pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500">持仓盈亏</p>
              <p className={clsx('text-xl font-bold', getRiseOrFallClass(profit_loss))}>
                {formatMoney(profit_loss)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">收益率</p>
              <p className={clsx('text-xl font-bold', getRiseOrFallClass(profit_loss_ratio))}>
                {formatPercent(profit_loss_ratio)}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            持仓 {quantity} 股 · 市值 {formatMoney((current_price || cost_price) * quantity)}
          </p>
        </div>
      </div>

      {/* 删除按钮 */}
      {onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="absolute bottom-2 right-2 text-red-500 hover:text-red-700 text-sm"
        >
          删除
        </button>
      )}
    </Card>
  );
};

export default PortfolioCard;
