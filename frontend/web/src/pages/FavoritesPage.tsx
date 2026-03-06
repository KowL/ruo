import React, { useEffect, useState } from 'react';
import { getGroups, createGroup, updateGroup, deleteGroup, getStocks, addStock, deleteStock, StockGroup, StockFavorite, SearchStock } from '@/api/favorites';
import { searchStock } from '@/api/stock';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';

const FavoritesPage: React.FC = () => {
  const [groups, setGroups] = useState<StockGroup[]>([]);
  const [stocks, setStocks] = useState<StockFavorite[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // 新建分组弹窗状态
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [groupName, setGroupName] = useState('');
  const [groupDescription, setGroupDescription] = useState('');

  // 添加股票弹窗状态
  const [showAddStockModal, setShowAddStockModal] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<SearchStock[]>([]);
  const [searching, setSearching] = useState(false);

  // 加载分组列表
  const loadGroups = async () => {
    try {
      const res = await getGroups();
      setGroups(res.data);
      if (res.data.length > 0 && !selectedGroupId) {
        setSelectedGroupId(res.data[0].id);
      }
    } catch (error) {
      console.error('加载分组失败:', error);
      showToast('加载分组失败', 'error');
    }
  };

  // 加载自选股票
  const loadStocks = async (groupId: number) => {
    try {
      const res = await getStocks(groupId);
      setStocks(res.data);
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

  // 创建分组
  const handleCreateGroup = async () => {
    if (!groupName.trim()) {
      showToast('请输入分组名称', 'error');
      return;
    }
    try {
      await createGroup({ name: groupName, description: groupDescription });
      showToast('分组创建成功', 'success');
      setShowGroupModal(false);
      setGroupName('');
      setGroupDescription('');
      loadGroups();
    } catch (error) {
      showToast('创建分组失败', 'error');
    }
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

  // 搜索股票
  const handleSearch = async () => {
    if (!searchKeyword.trim() || searchKeyword.trim().length < 2) return;
    setSearching(true);
    try {
      const results = await searchStock(searchKeyword.trim());

      // 检查哪些股票已经在当前自选组中
      const currentStockSymbols = new Set(stocks.map(s => s.symbol));

      const formattedResults = results.map(stock => ({
        ...stock,
        isFavorited: currentStockSymbols.has(stock.symbol)
      }));

      setSearchResults(formattedResults as SearchStock[]);
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setSearching(false);
    }
  };

  // 添加自选股票
  const handleAddStock = async (stock: SearchStock) => {
    if (!selectedGroupId) {
      showToast('请先选择一个分组', 'error');
      return;
    }
    try {
      await addStock({ groupId: selectedGroupId, symbol: stock.symbol, name: stock.name });
      showToast(`已添加 ${stock.name}`, 'success');
      loadStocks(selectedGroupId);
      setShowAddStockModal(false);
      setSearchKeyword('');
      setSearchResults([]);
    } catch (error: any) {
      showToast(error.response?.data?.detail || '添加失败', 'error');
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

  const currentGroup = groups.find(g => g.id === selectedGroupId);

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">自选管理</h1>
          <p className="text-slate-400 mt-1">管理您的自选分组与关注标的</p>
        </div>
        <button
          onClick={() => setShowGroupModal(true)}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all"
        >
          + 新建分组
        </button>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* 左侧分组列表 */}
        <div className="w-64 flex-shrink-0">
          <div className="glass-card p-4 h-full overflow-auto border border-white/5 bg-slate-900/50">
            <h3 className="text-sm font-medium mb-4 text-slate-400 px-2">
              我的分组
            </h3>
            <div className="space-y-2">
              {groups.map((group) => (
                <div
                  key={group.id}
                  onClick={() => setSelectedGroupId(group.id)}
                  className={`p-3 rounded-xl cursor-pointer transition-all ${selectedGroupId === group.id
                    ? 'bg-blue-500/20 border border-blue-500/30 text-blue-400'
                    : 'border border-transparent hover:bg-white/5 text-slate-300'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{group.name}</span>
                    <span className="text-xs bg-slate-800 px-2 py-0.5 rounded-full text-slate-400">
                      {group.stockCount}
                    </span>
                  </div>
                  {group.isDefault && (
                    <span className="text-xs text-blue-500 mt-1 inline-block">默认分组</span>
                  )}
                </div>
              ))}
              {groups.length === 0 && (
                <div className="text-center py-8 text-slate-500 text-sm">
                  暂无分组
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧股票列表 */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedGroupId ? (
            <>
              <div className="flex items-center justify-between mb-4 px-1">
                <h2 className="text-lg font-medium text-white flex items-center">
                  <span className="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full mr-3"></span>
                  {currentGroup?.name || '自选股票'}
                </h2>
                <div className="flex gap-3">
                  {currentGroup && !currentGroup.isDefault && (
                    <button
                      onClick={() => handleDeleteGroup(currentGroup.id)}
                      className="px-4 py-2 rounded-xl border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-all text-sm font-medium"
                    >
                      删除分组
                    </button>
                  )}
                  <button
                    onClick={() => setShowAddStockModal(true)}
                    className="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5 transition-all text-sm font-medium text-white"
                  >
                    + 添加股票
                  </button>
                </div>
              </div>

              <div className="flex-1 glass-card overflow-auto border border-white/5 bg-slate-900/50">
                {stocks.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-slate-900/90 backdrop-blur border-b border-white/5 z-10">
                      <tr className="text-left text-slate-400">
                        <th className="p-4 font-medium">代码</th>
                        <th className="p-4 font-medium">名称</th>
                        <th className="p-4 font-medium">添加时间</th>
                        <th className="p-4 font-medium text-right">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {stocks.map((stock) => (
                        <tr
                          key={stock.id}
                          className="hover:bg-white/5 transition-colors group"
                        >
                          <td className="p-4 font-mono text-slate-300 group-hover:text-blue-400 transition-colors">{stock.symbol}</td>
                          <td className="p-4 font-medium text-white">{stock.name}</td>
                          <td className="p-4 text-slate-500">
                            {new Date(stock.addedAt).toLocaleDateString()}
                          </td>
                          <td className="p-4 text-right">
                            <button
                              onClick={() => handleDeleteStock(stock.id)}
                              className="text-slate-500 hover:text-red-400 transition-colors px-2 py-1"
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      ))}
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
            <div className="flex-1 glass-card flex items-center justify-center border border-white/5 bg-slate-900/50 text-slate-500">
              请选择或创建一个分组
            </div>
          )}
        </div>
      </div>

      {/* 新建分组弹窗 */}
      {showGroupModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 relative overflow-hidden border border-white/10 bg-[#1a1a1a]">
            {/* Glow Effects */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

            <h3 className="text-xl font-bold mb-6 text-white flex items-center">
              <span className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full mr-3"></span>
              新建分组
            </h3>

            <div className="space-y-4 relative z-10">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">分组名称</label>
                <input
                  type="text"
                  placeholder="例如：科技股、高息股"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">分组描述 (可选)</label>
                <input
                  type="text"
                  placeholder="简要描述该分组的策略或特点"
                  value={groupDescription}
                  onChange={(e) => setGroupDescription(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div className="flex space-x-4 pt-8 relative z-10">
              <button
                onClick={() => setShowGroupModal(false)}
                className="flex-1 px-4 py-3 rounded-xl border border-white/10 text-gray-300 hover:bg-white/5 hover:text-white transition-all font-medium"
              >
                取消
              </button>
              <button
                onClick={handleCreateGroup}
                className="flex-1 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all"
              >
                确认创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 添加股票弹窗 */}
      {showAddStockModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="glass-card w-full max-w-lg p-6 relative overflow-hidden border border-white/10 bg-[#1a1a1a]">
            {/* Glow Effects */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

            <h3 className="text-xl font-bold mb-6 text-white flex items-center">
              <span className="w-1 h-6 bg-gradient-to-b from-purple-500 to-blue-500 rounded-full mr-3"></span>
              添加自选股票
            </h3>

            <div className="relative z-10">
              <div className="flex gap-3 mb-4">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="输入股票代码或名称，如 000001"
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    className="w-full pl-4 pr-10 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                    autoFocus
                  />
                  {searchKeyword && (
                    <button
                      onClick={() => {
                        setSearchKeyword('');
                        setSearchResults([]);
                      }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
                <button
                  onClick={handleSearch}
                  disabled={searching || !searchKeyword.trim()}
                  className={`px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-medium transition-all ${searching || !searchKeyword.trim() ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/10 hover:border-white/20'
                    }`}
                >
                  {searching ? '搜索中...' : '搜索'}
                </button>
              </div>

              <div className="h-[280px] overflow-auto bg-black/20 rounded-xl border border-white/5 mb-6">
                {searchResults.length > 0 ? (
                  <div className="divide-y divide-white/5">
                    {searchResults.map((stock) => (
                      <div
                        key={stock.symbol}
                        className="flex items-center justify-between p-4 hover:bg-white/5 transition-colors group"
                      >
                        <div>
                          <div className="font-medium text-white group-hover:text-blue-400 transition-colors">{stock.name}</div>
                          <div className="text-sm font-mono text-gray-500">{stock.symbol}</div>
                        </div>
                        <button
                          onClick={() => handleAddStock(stock)}
                          disabled={stock.isFavorited}
                          className={`px-4 py-1.5 text-sm rounded-lg border font-medium transition-all ${stock.isFavorited
                            ? 'border-transparent bg-white/5 text-gray-500 cursor-not-allowed'
                            : 'border-blue-500/30 text-blue-400 hover:bg-blue-500/10'
                            }`}
                        >
                          {stock.isFavorited ? '已添加' : '添加到本组'}
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500 space-y-2">
                    {searching ? (
                      <svg className="animate-spin h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <>
                        <svg className="w-8 h-8 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <p className="text-sm">{searchKeyword ? '未找到相关股票' : '输入代码或名称进行搜索'}</p>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => {
                    setShowAddStockModal(false);
                    setSearchKeyword('');
                    setSearchResults([]);
                  }}
                  className="px-6 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-sm font-medium text-white"
                >
                  完成
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
};

export default FavoritesPage;
