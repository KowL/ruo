import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGroups, deleteGroup, getStocks, deleteStock, StockGroup, StockFavorite } from '@/api/favorites';
import { getStockRealtime } from '@/api/stock';
import type { StockRealtime } from '@/types';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';
import AddGroupModal from './AddGroupModal';
import AddStockModal from './AddStockModal';

const FavoritesCard: React.FC = () => {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<StockGroup[]>([]);
  const [stocks, setStocks] = useState<StockFavorite[]>([]);
  const [stockPrices, setStockPrices] = useState<Record<string, StockRealtime>>({});
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // 弹窗状态
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showAddStockModal, setShowAddStockModal] = useState(false);

  // 加载分组列表
  const loadGroups = async () => {
    try {
      const res = await getGroups();
      const groupsData = res?.data || [];
      setGroups(groupsData as unknown as StockGroup[]);
      if ((groupsData as unknown as StockGroup[]).length > 0 && !selectedGroupId) {
        setSelectedGroupId((groupsData as unknown as StockGroup[])[0].id);
      }
    } catch (error) {
      console.error('加载分组失败:', error);
      showToast('加载分组失败', 'error');
    }
  };

  // 加载自选股票及其价格
  const loadStocks = async (groupId: number) => {
    try {
      const res = await getStocks(groupId);
      const stocksData = res?.data || [];
      setStocks(stocksData as unknown as StockFavorite[]);

      // 获取每只股票的价格
      const pricePromises = (stocksData as unknown as StockFavorite[]).map(async (stock: StockFavorite) => {
        try {
          const priceRes = await getStockRealtime(stock.symbol);
          return { symbol: stock.symbol, data: priceRes };
        } catch {
          return { symbol: stock.symbol, data: null };
        }
      });

      const priceResults = await Promise.all(pricePromises);
      const priceMap: Record<string, StockRealtime> = {};
      priceResults.forEach((item: any) => {
        if (item.data) {
          priceMap[item.symbol] = item.data;
        }
      });
      setStockPrices(priceMap);
    } catch (error) {
      console.error('加载自选股票失败:', error);
      showToast('加载自选股票失败', 'error');
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedGroupId) {
      loadStocks(selectedGroupId);
    }
  }, [selectedGroupId]);

  const loadData = async () => {
    setLoading(true);
    await loadGroups();
    setLoading(false);
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // 删除分组
  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('确定要删除该分组吗？组内股票也会被删除。')) return;
    try {
      await deleteGroup(groupId);
      showToast('分组删除成功', 'success');
      if (selectedGroupId === groupId) {
        setSelectedGroupId(null);
      }
      loadGroups();
    } catch (error) {
      showToast('删除分组失败', 'error');
    }
  };

  // 删除自选股票
  const handleDeleteStock = async (stockId: number) => {
    try {
      await deleteStock(stockId);
      showToast('删除成功', 'success');
      if (selectedGroupId) {
        loadStocks(selectedGroupId);
      }
    } catch (error) {
      showToast('删除失败', 'error');
    }
  };

  const currentGroup = groups?.find(g => g.id === selectedGroupId);

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="bg-card text-card-foreground border rounded-xl shadow-sm hover-lift flex flex-col h-[500px] relative">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h3 className="text-base font-medium text-foreground flex items-center">
          <span className="mr-2 text-lg">⭐</span> 我的自选
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddStockModal(true)}
            className="text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-muted transition-colors font-medium flex items-center gap-1 text-foreground"
          >
            <span>+&nbsp;</span>添加股票
          </button>
          <button
            onClick={() => setShowGroupModal(true)}
            className="text-xs px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors font-medium flex items-center gap-1"
          >
            <span>+&nbsp;</span>新建分组
          </button>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* 左侧分组列表 */}
        <div className="w-48 flex-shrink-0 border-r border-border">
          <div className="p-3 h-full overflow-y-auto custom-scrollbar">
            <div className="space-y-2">
              {(groups || []).map((group) => (
                <div
                  key={group.id}
                  onClick={() => setSelectedGroupId(group.id)}
                  className={`p-3 rounded-xl cursor-pointer transition-all ${selectedGroupId === group.id
                    ? 'bg-blue-500/20 border border-blue-500/30 text-blue-400'
                    : 'border-transparent hover:bg-accent hover:text-accent-foreground text-muted-foreground'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{group.name}</span>
                    <span className="text-xs bg-muted px-2 py-0.5 rounded-full text-muted-foreground">
                      {group.stockCount}
                    </span>
                  </div>
                  {group.isDefault && (
                    <span className="text-xs text-blue-500 mt-1 inline-block">默认分组</span>
                  )}
                </div>
              ))}
              {(groups || []).length === 0 && (
                <div className="text-center py-8 text-slate-500 text-sm">
                  暂无分组
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧股票列表 */}
        <div className="flex-1 flex flex-col min-w-0 bg-background/30 bg-muted/10">
          {selectedGroupId ? (
            <>
              <div className="flex items-center justify-between p-3 border-b border-border/50">
                <h4 className="text-sm font-medium text-foreground flex items-center">
                  <span className="w-1 h-3 bg-primary rounded-full mr-2"></span>
                  {currentGroup?.name || '自选股票'}
                </h4>
                <div className="flex gap-2">
                  {currentGroup && !currentGroup.isDefault && (
                    <button
                      onClick={() => handleDeleteGroup(currentGroup.id)}
                      className="px-2.5 py-1 rounded text-xs border border-destructive/20 text-destructive hover:bg-destructive/10 transition-colors"
                    >
                      删除分组
                    </button>
                  )}
                  <button
                    onClick={() => setShowAddStockModal(true)}
                    className="px-2.5 py-1 rounded text-xs border border-border hover:bg-muted transition-colors text-foreground"
                  >
                    + 添加股票
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-auto custom-scrollbar">
                {(stocks || []).length > 0 ? (
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-muted/50 backdrop-blur border-b border-border z-10">
                      <tr className="text-left text-muted-foreground">
                        <th className="px-4 py-2 font-medium">代码</th>
                        <th className="px-4 py-2 font-medium">名称</th>
                        <th className="px-4 py-2 font-medium text-right">现价</th>
                        <th className="px-4 py-2 font-medium text-right">涨幅</th>
                        <th className="px-4 py-2 font-medium">日期</th>
                        <th className="px-4 py-2 font-medium text-right">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                      {(stocks || []).map((stock) => {
                        const price = stockPrices[stock.symbol];
                        const changePct = price?.changePct || 0;
                        const isUp = changePct > 0;
                        const isDown = changePct < 0;
                        return (
                          <tr
                            key={stock.id}
                            onClick={() => navigate(`/stock/chart?symbol=${stock.symbol}`)}
                            className="hover:bg-muted/50 transition-colors group cursor-pointer"
                          >
                            <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground group-hover:text-primary transition-colors">{stock.symbol}</td>
                            <td className="px-4 py-2.5 font-medium text-sm text-foreground">{stock.name}</td>
                            <td className="px-4 py-2.5 text-right font-medium text-sm numbers">
                              {price ? price.price.toFixed(2) : '-'}
                            </td>
                            <td className={`px-4 py-2.5 text-right text-sm numbers font-medium ${isUp ? 'text-profit-up' : isDown ? 'text-profit-down' : 'text-muted-foreground'}`}>
                              {price ? `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%` : '-'}
                            </td>
                            <td className="px-4 py-2.5 text-xs text-muted-foreground">
                              {new Date(stock.addedAt).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-2.5 text-right">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDeleteStock(stock.id); }}
                                className="text-muted-foreground hover:text-destructive transition-colors text-xs"
                              >
                                删除
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-3">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center">
                      <svg className="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 12H4M12 20V4" />
                      </svg>
                    </div>
                    <span>该分组暂无股票，点击右上角添加</span>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 bg-card flex items-center justify-center border border-border text-muted-foreground rounded-xl">
              请选择或创建一个分组
            </div>
          )}
        </div>
      </div>

      {/* 新建分组弹窗 */}
      <AddGroupModal
        isOpen={showGroupModal}
        onClose={() => setShowGroupModal(false)}
        onSuccess={() => loadGroups()}
      />

      {/* 添加股票弹窗 */}
      <AddStockModal
        isOpen={showAddStockModal}
        onClose={() => setShowAddStockModal(false)}
        onSuccess={(groupId) => {
          setSelectedGroupId(groupId);
          loadStocks(groupId);
          loadGroups(); // 更新股票计数
        }}
        groups={groups}
        activeGroupId={selectedGroupId}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default FavoritesCard;
