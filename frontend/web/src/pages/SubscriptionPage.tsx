import React, { useEffect, useState } from 'react';
import { getStrategies } from '@/api/strategy';
import { getSubscriptions, createSubscription, deleteSubscription, Subscription } from '@/api/subscriptions';
import { getGroups } from '@/api/favorites';
import Toast from '@/components/common/Toast';

interface Strategy {
  id: number;
  name: string;
  strategyType: string;
  description?: string;
}

interface StockGroup {
  id: number;
  name: string;
  stockCount: number;
}

const SubscriptionPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [groups, setGroups] = useState<StockGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // 新建订阅弹窗状态
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null);
  const [stockPoolType, setStockPoolType] = useState<'all' | 'group' | 'custom'>('all');
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [customSymbols, setCustomSymbols] = useState('');
  const [notifyEnabled, setNotifyEnabled] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [strategyRes, subscriptionRes, groupRes] = await Promise.all([
        getStrategies(),
        getSubscriptions(),
        getGroups(),
      ]);
      setStrategies((strategyRes as any)?.data || []);
      setSubscriptions((subscriptionRes as any)?.data || []);
      setGroups((groupRes as any)?.data || []);
    } catch (error) {
      console.error('加载数据失败:', error);
      showToast('加载数据失败', 'error');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // 订阅策略
  const handleSubscribe = async () => {
    if (!selectedStrategyId) {
      showToast('请选择策略', 'error');
      return;
    }
    try {
      await createSubscription({
        strategyId: selectedStrategyId,
        stockPoolType,
        stockGroupId: stockPoolType === 'group' ? selectedGroupId || undefined : undefined,
        customSymbols: stockPoolType === 'custom'
          ? customSymbols.split(',').map(s => s.trim()).filter(Boolean)
          : undefined,
        notifyEnabled,
      });
      showToast('订阅成功', 'success');
      setShowSubscribeModal(false);
      resetModal();
      loadData();
    } catch (error: any) {
      showToast(error.response?.data?.detail || '订阅失败', 'error');
    }
  };

  // 取消订阅
  const handleUnsubscribe = async (subscriptionId: number) => {
    if (!confirm('确定要取消订阅吗？')) return;
    try {
      await deleteSubscription(subscriptionId);
      showToast('取消订阅成功', 'success');
      loadData();
    } catch (error) {
      showToast('取消订阅失败', 'error');
    }
  };

  const resetModal = () => {
    setSelectedStrategyId(null);
    setStockPoolType('all');
    setSelectedGroupId(null);
    setCustomSymbols('');
    setNotifyEnabled(true);
  };

  const getPoolTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      all: '全部自选股',
      group: '指定分组',
      custom: '自定义',
    };
    return map[type] || type;
  };

  const getStrategyType = (strategyId: number) => {
    const strategy = strategies.find(s => s.id === strategyId);
    return strategy?.strategyType || '';
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'trend_following': '趋势跟踪',
      'mean_reversion': '均值回归',
      'breakout': '突破策略',
      'multi_factor': '多因子'
    };
    return labels[type] || type;
  };

  return (
    <div className="p-6 space-y-6 text-white min-h-screen">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
            策略订阅
          </h1>
          <p className="text-gray-400 mt-1 flex items-center">
            <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mr-2 shadow-[0_0_8px_rgba(168,85,247,0.6)]"></span>
            订阅策略后自动接收买卖信号通知
          </p>
        </div>
        <button
          onClick={() => setShowSubscribeModal(true)}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white font-medium hover:shadow-lg hover:shadow-purple-500/20 hover:-translate-y-0.5 transition-all flex items-center"
        >
          <span className="mr-2 text-lg">+</span> 订阅策略
        </button>
      </div>

      {/* 订阅列表 */}
      {loading && subscriptions.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card h-40 border border-white/5 bg-white/5"></div>
          ))}
        </div>
      ) : subscriptions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subscriptions.map((sub) => (
            <div key={sub.id} className="glass-card p-5 group hover:border-purple-500/30 transition-all duration-300 relative overflow-hidden">
              {/* Hover Glow */}
              <div className="absolute -top-10 -right-10 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all"></div>

              <div className="flex items-start justify-between mb-4 relative z-10">
                <div>
                  <h3 className="font-bold text-lg text-white group-hover:text-purple-400 transition-colors">
                    {sub.strategyName}
                  </h3>
                  <span className="inline-block mt-2 px-2.5 py-0.5 bg-purple-500/10 text-purple-400 text-[10px] font-bold rounded-full border border-purple-500/20 uppercase tracking-tighter">
                    {getTypeLabel(getStrategyType(sub.strategyId))}
                  </span>
                </div>
                <button
                  onClick={() => handleUnsubscribe(sub.id)}
                  className="text-gray-500 hover:text-red-400 p-1.5 hover:bg-red-400/10 rounded-lg transition-all"
                  title="取消订阅"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-3 text-sm mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">股票池</span>
                  <span className="px-2 py-0.5 bg-white/5 rounded text-gray-300 text-xs">
                    {getPoolTypeLabel(sub.stockPoolType)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">股票数量</span>
                  <span className="text-gray-300 font-mono">{sub.stockPoolCount} 只</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">通知</span>
                  <span className={sub.notifyEnabled ? 'text-green-400' : 'text-gray-500'}>
                    {sub.notifyEnabled ? '已开启' : '已关闭'}
                  </span>
                </div>
              </div>

              <div className="text-xs text-gray-500 pt-3 border-t border-white/5">
                订阅于 {new Date(sub.createdAt).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card p-16 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <h3 className="text-xl font-medium text-gray-300 mb-2">暂无订阅</h3>
          <p className="text-gray-500 mb-6">订阅策略后可接收买卖信号通知</p>
          <button
            onClick={() => setShowSubscribeModal(true)}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white font-medium hover:shadow-lg hover:shadow-purple-500/20 transition-all inline-flex items-center"
          >
            <span className="mr-2 text-lg">+</span> 立即订阅
          </button>
        </div>
      )}

      {/* 订阅弹窗 */}
      {showSubscribeModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="glass-card w-[500px] p-6 relative z-10">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold">订阅策略</h3>
              <button
                onClick={() => {
                  setShowSubscribeModal(false);
                  resetModal();
                }}
                className="text-gray-500 hover:text-white p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 选择策略 */}
            <div className="mb-5">
              <label className="block text-sm text-gray-400 mb-2">选择策略</label>
              <select
                value={selectedStrategyId || ''}
                onChange={(e) => setSelectedStrategyId(Number(e.target.value))}
                className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-purple-500/50 focus:outline-none transition-colors"
              >
                <option value="" className="bg-gray-800">请选择策略</option>
                {strategies.map((strategy) => (
                  <option key={strategy.id} value={strategy.id} className="bg-gray-800">
                    {strategy.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 股票池类型 */}
            <div className="mb-5">
              <label className="block text-sm text-gray-400 mb-2">股票池</label>
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[
                  { value: 'all', label: '全部自选' },
                  { value: 'group', label: '指定分组' },
                  { value: 'custom', label: '自定义' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setStockPoolType(option.value as any)}
                    className={`py-2.5 rounded-xl border transition-all text-sm ${
                      stockPoolType === option.value
                        ? 'bg-purple-500/20 border-purple-500/50 text-purple-400'
                        : 'border-white/10 text-gray-400 hover:border-white/20'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              {/* 分组选择 */}
              {stockPoolType === 'group' && (
                <select
                  value={selectedGroupId || ''}
                  onChange={(e) => setSelectedGroupId(Number(e.target.value))}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-purple-500/50 focus:outline-none transition-colors"
                >
                  <option value="" className="bg-gray-800">请选择分组</option>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id} className="bg-gray-800">
                      {group.name} ({group.stockCount}只)
                    </option>
                  ))}
                </select>
              )}

              {/* 自定义股票 */}
              {stockPoolType === 'custom' && (
                <input
                  type="text"
                  placeholder="输入股票代码，用逗号分隔，如: 000001, 000002"
                  value={customSymbols}
                  onChange={(e) => setCustomSymbols(e.target.value)}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none transition-colors"
                />
              )}
            </div>

            {/* 通知设置 */}
            <div className="mb-6">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className={`w-10 h-6 rounded-full transition-colors flex items-center px-0.5 ${notifyEnabled ? 'bg-purple-500' : 'bg-white/10'}`}>
                  <div className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${notifyEnabled ? 'translate-x-4' : ''}`}></div>
                </div>
                <input
                  type="checkbox"
                  checked={notifyEnabled}
                  onChange={(e) => setNotifyEnabled(e.target.checked)}
                  className="hidden"
                />
                <span className="text-gray-300 group-hover:text-white transition-colors">开启信号通知</span>
              </label>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowSubscribeModal(false);
                  resetModal();
                }}
                className="flex-1 py-3 rounded-xl border border-white/10 text-gray-400 hover:bg-white/5 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSubscribe}
                className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white font-medium hover:shadow-lg hover:shadow-purple-500/20 transition-all"
              >
                确认订阅
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default SubscriptionPage;
