import React, { useState } from 'react';

import { searchStock } from '@/api/stock';
import { StrategyTag, StockSearchResult } from '@/types';

interface AddPortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    symbol: string;
    name: string;
    costPrice: number;
    quantity: number;
    strategyTag?: string;
    market?: string;
  }) => Promise<void>;
}

const AddPortfolioModal: React.FC<AddPortfolioModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    costPrice: '',
    quantity: '',
    strategyTag: '' as StrategyTag | '',
    market: '',
  });
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  if (!isOpen) return null;

  const handleSearch = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const results = await searchStock(keyword);
      setSearchResults(results);
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectStock = (stock: StockSearchResult) => {
    setFormData({
      ...formData,
      symbol: stock.symbol,
      name: stock.name,
      market: stock.market,
    });
    setSearchResults([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        symbol: formData.symbol,
        name: formData.name,
        costPrice: parseFloat(formData.costPrice),
        quantity: parseFloat(formData.quantity),
        strategyTag: formData.strategyTag || undefined,
        market: formData.market,
      });
      // 重置表单
      setFormData({
        symbol: '',
        name: '',
        costPrice: '',
        quantity: '',
        strategyTag: '',
        market: '',
      });
      // 成功后关闭模态框
      onClose();
    } catch (error: any) {
      console.error('添加失败:', error);
      // 显示错误提示
      alert(error?.response?.data?.message || error?.message || '添加失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      {/* Glassmorphism Card */}
      <div className="glass-card w-full max-w-md p-6 relative overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

        <h2 className="text-xl font-bold mb-6 text-white flex items-center">
          <span className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full mr-3"></span>
          添加持仓
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
          {/* 股票搜索 */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              股票代码/名称
            </label>
            <div className="relative">
              <input
                type="text"
                value={formData.symbol && formData.name ? `${formData.name} (${formData.symbol})` : (formData.symbol || formData.name)}
                onChange={(e) => {
                  const val = e.target.value;
                  // 如果包含名称 (代码) 的格式，且用户在修改，则清空重新搜索
                  if (formData.name && val.includes(formData.name)) {
                    setFormData({ ...formData, symbol: '', name: '' });
                    handleSearch('');
                  } else {
                    setFormData({ ...formData, symbol: val, name: '' });
                    handleSearch(val);
                  }
                }}
                placeholder="输入代码或名称，如 000001"
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                required
              />
              {/* Search Dropdown */}
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-20 max-h-48 overflow-y-auto">
                  {searchResults.map((stock) => (
                    <div
                      key={stock.symbol}
                      onClick={() => handleSelectStock(stock)}
                      className="px-4 py-3 hover:bg-white/5 cursor-pointer flex justify-between items-center group transition-colors"
                    >
                      <div className="flex flex-col">
                        <span className="text-white font-medium group-hover:text-blue-400 transition-colors">{stock.name}</span>
                        <span className="text-gray-500 text-sm">{stock.symbol}</span>
                      </div>
                      {stock.price ? (
                        <div className="text-right">
                          <div className="text-white font-mono">{stock.price}</div>
                          <div className={`text-xs ${stock.changePct && stock.changePct >= 0 ? 'text-[#FF3B30]' : 'text-[#34C759]'}`}>
                            {stock.changePct && stock.changePct > 0 ? '+' : ''}{stock.changePct}%
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {searching && <p className="text-xs text-blue-400 mt-2 ml-1 animate-pulse">正在搜索...</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* 成本价 */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">成本价</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">¥</span>
                <input
                  type="number"
                  step="0.01"
                  value={formData.costPrice}
                  onChange={(e) => setFormData({ ...formData, costPrice: e.target.value })}
                  placeholder="0.00"
                  className="w-full pl-8 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all numbers"
                  required
                />
              </div>
            </div>

            {/* 持仓数量 */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">持仓数量</label>
              <input
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                placeholder="1000"
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all numbers"
                required
              />
            </div>
          </div>

          {/* 策略标签 */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">策略标签</label>
            <div className="relative">
              <select
                value={formData.strategyTag}
                onChange={(e) =>
                  setFormData({ ...formData, strategyTag: e.target.value as StrategyTag })
                }
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
              >
                <option value="" className="bg-[#1a1a1a] text-gray-500">请选择策略类型</option>
                <option value="打板" className="bg-[#1a1a1a]">🚀 打板 (超短线)</option>
                <option value="低吸" className="bg-[#1a1a1a]">📉 低吸 (反弹)</option>
                <option value="趋势" className="bg-[#1a1a1a]">📈 趋势 (波段)</option>
                <option value="其他" className="bg-[#1a1a1a]">📝 其他</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex space-x-4 pt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 rounded-xl border border-white/10 text-gray-300 hover:bg-white/5 hover:text-white transition-all font-medium"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all
                ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  处理中...
                </div>
              ) : '确认添加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPortfolioModal;
