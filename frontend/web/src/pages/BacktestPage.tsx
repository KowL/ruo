import React, { useEffect, useState } from 'react';
import { getBacktests, runBacktest, getBacktestDetail, deleteBacktest } from '@/api/strategy';
import { getStrategies } from '@/api/strategy';
import type { Backtest, BacktestDetail, Strategy } from '@/types/strategy';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';

const BacktestPage: React.FC = () => {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRunModal, setShowRunModal] = useState(false);
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestDetail | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // 回测表单
  const [runParams, setRunParams] = useState({
    strategyId: 0,
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialCapital: 1000000
  });

  useEffect(() => {
    fetchData();
    fetchStrategies();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await getBacktests();
      setBacktests(res.data || []);
    } catch (error) {
      setToast({ message: '获取回测失败', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategies = async () => {
    try {
      const res = await getStrategies();
      setStrategies(res.data || []);
      if (res.data && res.data.length > 0) {
        setRunParams(p => ({ ...p, strategyId: res.data![0].id }));
      }
    } catch (error) {
      console.error('获取策略失败:', error);
    }
  };

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!runParams.strategyId) {
      setToast({ message: '请选择策略', type: 'error' });
      return;
    }

    try {
      setLoading(true);
      await runBacktest(runParams);
      setToast({ message: '回测运行成功', type: 'success' });
      setShowRunModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.message || '回测失败', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (id: number) => {
    try {
      setLoading(true);
      const res = await getBacktestDetail(id);
      setSelectedBacktest(res.data || null);
    } catch (error) {
      setToast({ message: '获取详情失败', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('确定要删除这个回测吗？')) return;
    
    try {
      await deleteBacktest(id);
      setToast({ message: '删除成功', type: 'success' });
      fetchData();
    } catch (error) {
      setToast({ message: '删除失败', type: 'error' });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return '完成';
      case 'running':
        return '运行中';
      case 'failed':
        return '失败';
      default:
        return status;
    }
  };

  if (loading && backtests.length === 0) {
    return <Loading text="加载回测数据..." />;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">回测系统</h1>
          <p className="text-gray-500 mt-1">验证策略表现，分析历史收益</p>
        </div>
        <Button onClick={() => setShowRunModal(true)}>+ 运行回测</Button>
      </div>

      {/* 回测列表 */}
      <div className="bg-white rounded-lg border">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">策略</th>
              <th className="px-4 py-3 text-left">时间范围</th>
              <th className="px-4 py-3 text-right">总收益</th>
              <th className="px-4 py-3 text-right">最大回撤</th>
              <th className="px-4 py-3 text-right">夏普比率</th>
              <th className="px-4 py-3 text-center">状态</th>
              <th className="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            {backtests.map((bt) => (
              <tr key={bt.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3">{bt.strategyName}</td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {bt.startDate} ~ {bt.endDate}
                </td>
                <td className={`px-4 py-3 text-right font-semibold ${bt.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {bt.totalReturn >= 0 ? '+' : ''}{bt.totalReturn.toFixed(2)}%
                </td>
                <td className="px-4 py-3 text-right text-green-600">{bt.maxDrawdown.toFixed(2)}%</td>
                <td className="px-4 py-3 text-right">{bt.sharpeRatio.toFixed(2)}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(bt.status)}`}>
                    {getStatusLabel(bt.status)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleViewDetail(bt.id)}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    详情
                  </button>
                  <button
                    onClick={() => handleDelete(bt.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {backtests.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">还没有运行回测</p>
            <Button onClick={() => setShowRunModal(true)}>运行第一个回测</Button>
          </div>
        )}
      </div>

      {/* 运行回测弹窗 */}
      {showRunModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">运行回测</h2>
            
            <form onSubmit={handleRunBacktest} className="space-y-4">
              <div>
                <label className="block text-sm mb-1">选择策略 *</label>
                <select
                  value={runParams.strategyId}
                  onChange={(e) => setRunParams({ ...runParams, strategyId: Number(e.target.value) })}
                  className="w-full p-2 border rounded"
                  required
                >
                  <option value={0}>请选择策略</option>
                  {strategies.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">开始日期</label>
                  <input
                    type="date"
                    value={runParams.startDate}
                    onChange={(e) => setRunParams({ ...runParams, startDate: e.target.value })}
                    className="w-full p-2 border rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">结束日期</label>
                  <input
                    type="date"
                    value={runParams.endDate}
                    onChange={(e) => setRunParams({ ...runParams, endDate: e.target.value })}
                    className="w-full p-2 border rounded"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm mb-1">初始资金</label>
                <input
                  type="number"
                  value={runParams.initialCapital}
                  onChange={(e) => setRunParams({ ...runParams, initialCapital: Number(e.target.value) })}
                  className="w-full p-2 border rounded"
                  min={100000}
                  step={100000}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowRunModal(false)}>
                  取消
                </Button>
                <Button type="submit">开始回测</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 回测详情弹窗 */}
      {selectedBacktest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-auto">
          <div className="bg-white rounded-lg w-full max-w-4xl m-4 p-6 max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">回测详情 - {selectedBacktest.strategyName}</h2>
              <button
                onClick={() => setSelectedBacktest(null)}
                className="text-2xl text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            {/* 绩效指标 */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-500">总收益率</div>
                <div className={`text-2xl font-bold ${selectedBacktest.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {selectedBacktest.totalReturn >= 0 ? '+' : ''}{selectedBacktest.totalReturn.toFixed(2)}%
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-500">年化收益</div>
                <div className="text-2xl font-bold">{selectedBacktest.annualizedReturn.toFixed(2)}%</div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-500">最大回撤</div>
                <div className="text-2xl font-bold text-green-600">{selectedBacktest.maxDrawdown.toFixed(2)}%</div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-500">夏普比率</div>
                <div className="text-2xl font-bold">{selectedBacktest.sharpeRatio.toFixed(2)}</div>
              </div>
            </div>

            {/* 交易统计 */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-sm text-gray-500">总交易次数</div>
                <div className="text-xl font-semibold">{selectedBacktest.totalTrades}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">胜率</div>
                <div className="text-xl font-semibold text-red-600">{selectedBacktest.winRate.toFixed(1)}%</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">盈亏比</div>
                <div className="text-xl font-semibold">{selectedBacktest.profitFactor.toFixed(2)}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">平均盈亏</div>
                <div className="text-xl font-semibold">
                  {selectedBacktest.avgProfit > 0 ? '+' : ''}{selectedBacktest.avgProfit.toFixed(0)}
                </div>
              </div>
            </div>

            {/* 交易记录 */}
            {selectedBacktest.trades && selectedBacktest.trades.length > 0 && (
              <div>
                <h3 className="font-semibold mb-3">交易记录</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2">股票</th>
                        <th className="px-3 py-2">入场日期</th>
                        <th className="px-3 py-2">出场日期</th>
                        <th className="px-3 py-2 text-right">盈亏</th>
                        <th className="px-3 py-2 text-right">收益率</th>
                        <th className="px-3 py-2">原因</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBacktest.trades.map((trade, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{trade.symbol}</td>
                          <td className="px-3 py-2">{trade.entryDate}</td>
                          <td className="px-3 py-2">{trade.exitDate}</td>
                          <td className={`px-3 py-2 text-right ${trade.profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {trade.profit >= 0 ? '+' : ''}{trade.profit.toFixed(0)}
                          </td>
                          <td className={`px-3 py-2 text-right ${trade.returnPct >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {trade.returnPct >= 0 ? '+' : ''}{trade.returnPct.toFixed(2)}%
                          </td>
                          <td className="px-3 py-2">{trade.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
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

export default BacktestPage;
