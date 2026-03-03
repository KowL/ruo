import React, { useEffect, useState } from 'react';
import { getStrategies, deleteStrategy, getStrategyTemplates, createStrategy } from '@/api/strategy';
import type { Strategy, StrategyTemplate } from '@/types/strategy';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';

const StrategyPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // 创建表单
  const [newStrategy, setNewStrategy] = useState({
    name: '',
    strategyType: 'trend_following',
    description: ''
  });

  useEffect(() => {
    fetchData();
    fetchTemplates();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await getStrategies();
      setStrategies(res.data || []);
    } catch (error) {
      setToast({ message: '获取策略失败', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await getStrategyTemplates();
      setTemplates(res.data || []);
    } catch (error) {
      console.error('获取模板失败:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('确定要删除这个策略吗？')) return;
    
    try {
      await deleteStrategy(id);
      setToast({ message: '删除成功', type: 'success' });
      fetchData();
    } catch (error) {
      setToast({ message: '删除失败', type: 'error' });
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newStrategy.name.trim()) {
      setToast({ message: '请输入策略名称', type: 'error' });
      return;
    }

    try {
      await createStrategy(newStrategy);
      setToast({ message: '创建成功', type: 'success' });
      setShowCreateModal(false);
      setNewStrategy({ name: '', strategyType: 'trend_following', description: '' });
      fetchData();
    } catch (error) {
      setToast({ message: '创建失败', type: 'error' });
    }
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

  if (loading) {
    return <Loading text="加载策略..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">策略管理</h1>
          <p className="text-gray-500 mt-1">创建和管理交易策略，支持回测验证</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>+ 创建策略</Button>
      </div>

      {/* 策略列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map((strategy) => (
          <div key={strategy.id} className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-lg">{strategy.name}</h3>
                <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                  {getTypeLabel(strategy.strategyType)}
                </span>
              </div>
              <button
                onClick={() => handleDelete(strategy.id)}
                className="text-gray-400 hover:text-red-500"
              >
                删除
              </button>
            </div>
            
            <p className="text-gray-600 text-sm mb-4 line-clamp-2">{strategy.description || '暂无描述'}</p>
            
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500">总收益</div>
                <div className={`font-semibold ${strategy.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {strategy.totalReturn >= 0 ? '+' : ''}{strategy.totalReturn.toFixed(2)}%
                </div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500">最大回撤</div>
                <div className="font-semibold text-green-600">{strategy.maxDrawdown.toFixed(2)}%</div>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500">夏普比率</div>
                <div className="font-semibold">{strategy.sharpeRatio.toFixed(2)}</div>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <a
                href={`/#/backtest?strategyId=${strategy.id}`}
                className="flex-1 text-center py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 text-sm"
              >
                回测
              </a>
              <a
                href={`/#/signals?strategyId=${strategy.id}`}
                className="flex-1 text-center py-2 bg-green-50 text-green-600 rounded hover:bg-green-100 text-sm"
              >
                信号
              </a>
            </div>
          </div>
        ))}
      </div>

      {strategies.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">还没有创建策略</p>
          <Button onClick={() => setShowCreateModal(true)}>创建第一个策略</Button>
        </div>
      )}

      {/* 创建策略弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">创建策略</h2>
            
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm mb-1">策略名称 *</label>
                <input
                  type="text"
                  value={newStrategy.name}
                  onChange={(e) => setNewStrategy({ ...newStrategy, name: e.target.value })}
                  className="w-full p-2 border rounded"
                  placeholder="输入策略名称"
                  required
                />
              </div>

              <div>
                <label className="block text-sm mb-1">策略类型</label>
                <select
                  value={newStrategy.strategyType}
                  onChange={(e) => setNewStrategy({ ...newStrategy, strategyType: e.target.value })}
                  className="w-full p-2 border rounded"
                >
                  {templates.map((t) => (
                    <option key={t.type} value={t.type}>{t.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm mb-1">描述</label>
                <textarea
                  value={newStrategy.description}
                  onChange={(e) => setNewStrategy({ ...newStrategy, description: e.target.value })}
                  className="w-full p-2 border rounded h-20"
                  placeholder="策略描述（可选）"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreateModal(false)}>
                  取消
                </Button>
                <Button type="submit">创建</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toast */}
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

export default StrategyPage;
