import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { Stock } from '@/types';

interface StockCardProps {
  stock: Stock;
  isSelected?: boolean;
  onClick?: () => void;
}

export function StockCard({ stock, isSelected = false, onClick }: StockCardProps) {
  const isPositive = stock.change >= 0;

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className={`p-4 rounded-xl bg-[#1E293B] border cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'border-[#2563EB] shadow-[0_0_20px_rgba(37,99,235,0.2)]'
          : 'border-[#334155] hover:border-[#475569]'
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[#F8FAFC] font-semibold">{stock.name}</h3>
          <p className="text-[#94A3B8] text-sm">{stock.code}</p>
        </div>
        <div className="text-right">
          <p className="text-[#F8FAFC] font-mono font-semibold text-lg">
            ¥{stock.price.toFixed(2)}
          </p>
          <div className={`flex items-center gap-1 justify-end ${
            isPositive ? 'text-[#10B981]' : 'text-[#EF4444]'
          }`}>
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span className="text-sm font-mono">
              {isPositive ? '+' : ''}{stock.change.toFixed(2)} ({isPositive ? '+' : ''}{stock.changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

interface CompactStockCardProps {
  stock: Stock;
}

export function CompactStockCard({ stock }: CompactStockCardProps) {
  const isPositive = stock.change >= 0;

  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-[#334155]/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${isPositive ? 'bg-[#10B981]' : 'bg-[#EF4444]'}`} />
        <div>
          <p className="text-[#F8FAFC] text-sm font-medium">{stock.name}</p>
          <p className="text-[#94A3B8] text-xs">{stock.code}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-[#F8FAFC] text-sm font-mono">{stock.price.toFixed(2)}</p>
        <p className={`text-xs font-mono ${isPositive ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
          {isPositive ? '+' : ''}{stock.changePercent.toFixed(2)}%
        </p>
      </div>
    </div>
  );
}
