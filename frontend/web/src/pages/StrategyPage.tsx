import React, { useEffect, useState } from 'react';
import { getStrategies, deleteStrategy, getStrategyTemplates, createStrategy } from '@/api/strategy';
import type { Strategy, StrategyTemplate } from '@/types/strategy';
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


  return (
    <div className="p-6 space-y-6 text-white min-h-screen pt-0">
      <div className="flex items-center justify-end mb-4">
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all flex items-center"
        >
          <span className="mr-2 text-lg">+</span> 创建策略
        </button>
      </div>

      {/* 策略列表 */}
      {loading && strategies.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-card h-48 border border-border bg-muted/20 animate-pulse rounded-xl"></div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="bg-card text-card-foreground p-5 group hover:border-primary/30 transition-all duration-300 relative overflow-hidden border border-border rounded-xl">
                {/* Hover Glow */}
                <div className="absolute -top-10 -right-10 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all"></div>

                <div className="flex items-start justify-between mb-4 relative z-10">
                  <div>
                    <h3 className="font-bold text-lg text-white group-hover:text-blue-400 transition-colors uppercase tracking-wider">{strategy.name}</h3>
                    <span className="inline-block mt-2 px-2.5 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded-full border border-blue-500/20 uppercase tracking-tighter">
                      {getTypeLabel(strategy.strategyType)}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(strategy.id)}
                    className="text-gray-500 hover:text-red-400 p-1.5 hover:bg-red-400/10 rounded-lg transition-all"
                    title="删除策略"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>

                <p className="text-gray-400 text-sm mb-6 line-clamp-2 min-h-[40px] leading-relaxed">
                  {strategy.description || '暂无详细描述...'}
                </p>

                <div className="grid grid-cols-3 gap-3 text-center mb-6">
                  <div className="bg-muted/50 rounded-xl p-2.5 border border-border">
                    <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1">总收益</div>
                    <div className={`text-sm font-mono font-bold ${strategy.totalReturn >= 0 ? 'text-[#FF3B30]' : 'text-[#34C759]'}`}>
                      {strategy.totalReturn >= 0 ? '+' : ''}{strategy.totalReturn.toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-muted/50 rounded-xl p-2.5 border border-border">
                    <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1">最大回撤</div>
                    <div className="text-sm font-mono font-bold text-[#34C759]">{strategy.maxDrawdown.toFixed(2)}%</div>
                  </div>
                  <div className="bg-muted/50 rounded-xl p-2.5 border border-border">
                    <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1">夏普</div>
                    <div className="text-sm font-mono font-bold text-blue-400">{strategy.sharpeRatio.toFixed(2)}</div>
                  </div>
                </div>

                <div className="flex gap-3 relative z-10 font-bold uppercase tracking-widest text-[#34C759]">
                  <a
                    href={`/#/signals?strategyId=${strategy.id}`}
                    className="flex-1 flex items-center justify-center py-2.5 bg-muted/50 text-card-foreground rounded-xl border border-border hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all text-xs font-bold uppercase tracking-widest group/btn"
                  >
                    查看实时信号
                  </a>
                </div>
              </div>
            ))}
          </div>

          {!loading && strategies.length === 0 && (
            <div className="text-center py-20 bg-card text-card-foreground mx-auto max-w-lg border-dashed border-border rounded-xl">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4 border border-border">
                <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-gray-400 mb-6">目前还没有任何交易策略，请开始创建您的第一个量化方案</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-3 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600 hover:text-white transition-all font-bold"
              >
                立即创建
              </button>
            </div>
          )}
        </>
      )}
      {/* 创建策略弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-card text-card-foreground w-full max-w-md p-8 relative overflow-hidden border border-border rounded-xl">
            {/* Decorative Glows */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

            <h2 className="text-2xl font-bold mb-8 text-white flex items-center">
              <span className="w-1 h-7 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full mr-4"></span>
              创建交易策略
            </h2>

            <form onSubmit={handleCreate} className="space-y-6 relative z-10">
              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">策略名称 <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={newStrategy.name}
                  onChange={(e) => setNewStrategy({ ...newStrategy, name: e.target.value })}
                  className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-card-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                  placeholder="如：均线交叉超短线策略"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">业务类型</label>
                <div className="relative">
                  <select
                    value={newStrategy.strategyType}
                    onChange={(e) => setNewStrategy({ ...newStrategy, strategyType: e.target.value })}
                    className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 appearance-none transition-all"
                  >
                    {templates.map((t) => (
                      <option key={t.type} value={t.type} className="bg-card">{t.name}</option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">逻辑描述</label>
                <textarea
                  value={newStrategy.description}
                  onChange={(e) => setNewStrategy({ ...newStrategy, description: e.target.value })}
                  className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-card-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 h-28 transition-all resize-none"
                  placeholder="简述策略的核心交易逻辑（可选）"
                />
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-3 rounded-xl border border-white/10 text-gray-300 hover:bg-white/5 hover:text-white transition-all font-bold uppercase tracking-widest text-xs"
                >
                  放弃返回
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-400 text-white font-bold hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all uppercase tracking-widest text-xs"
                >
                  立即创建
                </button>
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
