import React, { useState } from 'react';
import Button from '../common/Button';
import { searchStock } from '@/api/stock';
import { StrategyTag } from '@/types';

interface AddPortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    symbol: string;
    costPrice: number;
    quantity: number;
    strategyTag?: string;
  }) => Promise<void>;
}

const AddPortfolioModal: React.FC<AddPortfolioModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    costPrice: '',
    quantity: '',
    strategyTag: '' as StrategyTag | '',
  });
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
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

  const handleSelectStock = (stock: any) => {
    setFormData({
      ...formData,
      symbol: stock.symbol,
      name: stock.name,
    });
    setSearchResults([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        symbol: formData.symbol,
        costPrice: parseFloat(formData.costPrice),
        quantity: parseFloat(formData.quantity),
        strategyTag: formData.strategyTag || undefined,
      });
      // 重置表单
      setFormData({
        symbol: '',
        name: '',
        costPrice: '',
        quantity: '',
        strategyTag: '',
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-xl font-bold mb-4">添加持仓</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 股票搜索 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              股票代码/名称
            </label>
            <input
              type="text"
              value={formData.symbol || formData.name}
              onChange={(e) => {
                setFormData({ ...formData, symbol: e.target.value });
                handleSearch(e.target.value);
              }}
              placeholder="输入代码或名称，如 000001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
            {searching && <p className="text-xs text-gray-500 mt-1">搜索中...</p>}
            {searchResults.length > 0 && (
              <div className="mt-2 border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                {searchResults.map((stock) => (
                  <div
                    key={stock.symbol}
                    onClick={() => handleSelectStock(stock)}
                    className="px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <span className="font-medium">{stock.name}</span>
                    <span className="text-gray-500 ml-2 text-sm">{stock.symbol}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 成本价 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">成本价</label>
            <input
              type="number"
              step="0.01"
              value={formData.costPrice}
              onChange={(e) => setFormData({ ...formData, costPrice: e.target.value })}
              placeholder="10.50"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          {/* 持仓数量 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">持仓数量</label>
            <input
              type="number"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
              placeholder="1000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          {/* 策略标签 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">策略标签</label>
            <select
              value={formData.strategyTag}
              onChange={(e) =>
                setFormData({ ...formData, strategyTag: e.target.value as StrategyTag })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">请选择</option>
              <option value="打板">打板</option>
              <option value="低吸">低吸</option>
              <option value="趋势">趋势</option>
              <option value="其他">其他</option>
            </select>
          </div>

          {/* 按钮 */}
          <div className="flex space-x-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
              取消
            </Button>
            <Button type="submit" loading={loading} className="flex-1">
              添加
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPortfolioModal;
