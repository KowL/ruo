import { motion } from 'framer-motion';
import { Wallet } from 'lucide-react';
import type { FinanceData } from '@/types';

interface FinanceCardProps {
  finance: FinanceData;
}

export function FinanceCard({ finance }: FinanceCardProps) {
  const percentUsed = (finance.monthlyExpense / finance.monthlyBudget) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="p-5 rounded-xl bg-[#1E293B] border border-[#334155]"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#F8FAFC] font-semibold">本月支出</h3>
        <Wallet className="w-5 h-5 text-[#2563EB]" />
      </div>

      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-[#F8FAFC] text-2xl font-bold font-mono">
          ¥{finance.monthlyExpense.toLocaleString()}
        </span>
        <span className="text-[#94A3B8] text-sm">
          / ¥{finance.monthlyBudget.toLocaleString()}
        </span>
      </div>

      <div className="h-2 bg-[#334155] rounded-full overflow-hidden mb-4">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentUsed}%` }}
          transition={{ duration: 1, delay: 0.3 }}
          className={`h-full rounded-full ${
            percentUsed > 80 ? 'bg-[#EF4444]' : percentUsed > 60 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'
          }`}
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        {finance.categories.slice(0, 4).map((cat, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: cat.color }}
            />
            <span className="text-[#94A3B8] text-xs truncate">{cat.name}</span>
            <span className="text-[#F8FAFC] text-xs font-mono ml-auto">¥{cat.amount}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
