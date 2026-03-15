import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGroups, deleteGroup, getStocks, deleteStock, StockGroup, StockFavorite } from '@/api/favorites';
import { getStockRealtime } from '@/api/stock';
import type { StockRealtime } from '@/types';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';
import AddGroupModal from './AddGroupModal';
import AddStockModal from './AddStockModal';
import { Plus, X, Search, Trash2, Settings2 } from 'lucide-react';

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
    const handleDeleteGroup = async (e: React.MouseEvent, groupId: number) => {
        e.stopPropagation();
        if (!confirm('确定要删除该分组吗？组内股票也会被删除。')) return;
        try {
            await deleteGroup(groupId);
            showToast('分组删除成功', 'success');
            if (selectedGroupId === groupId) {
                const otherGroup = groups.find(g => g.id !== groupId);
                setSelectedGroupId(otherGroup ? otherGroup.id : null);
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
            loadGroups(); // 刷新分组下的股票数量
        } catch (error) {
            showToast('删除失败', 'error');
        }
    };


    if (loading) {
        return <Loading />;
    }

    return (
        <div className="bg-card text-card-foreground border border-border/50 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col h-[600px] overflow-hidden">
            {/* Top Toolbar / Tabs Row */}
            <div className="px-6 py-4 flex items-center justify-between border-b border-border/30 bg-muted/20 shrink-0">
                <div className="flex-1 flex items-center gap-1.5 overflow-x-auto custom-scrollbar no-scrollbar scroll-smooth">
                    {groups.map((group) => (
                        <div
                            key={group.id}
                            onClick={() => setSelectedGroupId(group.id)}
                            className={`
                                shrink-0 group flex items-center gap-2 px-4 py-2.5 rounded-xl cursor-pointer transition-all border font-bold text-[13px]
                                ${selectedGroupId === group.id
                                    ? 'bg-white border-orange-500/30 text-orange-600 shadow-sm'
                                    : 'bg-transparent border-transparent text-muted-foreground hover:bg-white hover:text-foreground'
                                }
                            `}
                        >
                            <span>{group.name}</span>
                            <span className={`text-[11px] px-1.5 py-0.5 rounded-md font-black ${selectedGroupId === group.id ? 'bg-orange-500/10 text-orange-500' : 'bg-muted text-muted-foreground opacity-60'}`}>
                                {group.stockCount}
                            </span>
                            {selectedGroupId === group.id && !group.isDefault && (
                                <button
                                    onClick={(e) => handleDeleteGroup(e, group.id)}
                                    className="ml-1 p-0.5 rounded-md hover:bg-orange-100 text-orange-400 opacity-60 hover:opacity-100 transition-all"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            )}
                        </div>
                    ))}
                    
                    <button
                        onClick={() => setShowGroupModal(true)}
                        className="shrink-0 p-2.5 rounded-xl border border-dashed border-border/50 text-muted-foreground hover:border-orange-500/50 hover:text-orange-500 transition-all active:scale-95 mr-4"
                        title="新建分组"
                    >
                        <Plus className="w-4 h-4" />
                    </button>
                </div>

                <div className="flex items-center gap-3 shrink-0 ml-4">
                    <button
                        onClick={() => setShowAddStockModal(true)}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-500 text-white font-black text-sm shadow-lg shadow-orange-500/20 hover:shadow-orange-500/30 hover:-translate-y-0.5 active:scale-95 transition-all"
                    >
                        <Plus className="w-4 h-4" />
                        <span>添加股票</span>
                    </button>
                </div>
            </div>

            {/* Stocks Table Area */}
            <div className="flex-1 min-h-0 bg-background/20 relative">
                {selectedGroupId ? (
                    <div className="h-full flex flex-col">
                        {stocks.length > 0 ? (
                            <div className="flex-1 overflow-auto custom-scrollbar">
                                <table className="w-full text-sm border-separate border-spacing-0">
                                    <thead className="sticky top-0 bg-muted/80 backdrop-blur-md z-20 border-b border-border/50">
                                        <tr className="text-left">
                                            <th className="px-6 py-4 font-black text-muted-foreground/60 text-[11px] uppercase tracking-wider">代码</th>
                                            <th className="px-6 py-4 font-black text-muted-foreground/60 text-[11px] uppercase tracking-wider">名称</th>
                                            <th className="px-6 py-4 font-black text-muted-foreground/60 text-[11px] uppercase tracking-wider text-right">最新价</th>
                                            <th className="px-6 py-4 font-black text-muted-foreground/60 text-[11px] uppercase tracking-wider text-right">涨跌幅</th>
                                            <th className="px-6 py-4 font-black text-muted-foreground/60 text-[11px] uppercase tracking-wider text-right">操作</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/20">
                                        {stocks.map((stock) => {
                                            const price = stockPrices[stock.symbol];
                                            const changePct = price?.changePct || 0;
                                            const isUp = changePct > 0;
                                            const isDown = changePct < 0;
                                            
                                            return (
                                                <tr
                                                    key={stock.id}
                                                    onClick={() => navigate(`/stock/chart?symbol=${stock.symbol}`)}
                                                    className="group hover:bg-orange-500/[0.02] cursor-pointer transition-colors"
                                                >
                                                    <td className="px-6 py-4">
                                                        <span className="font-mono text-[12px] font-bold text-muted-foreground group-hover:text-orange-500 transition-colors">
                                                            {stock.symbol}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className="font-black text-foreground group-hover:text-orange-600 transition-colors">
                                                            {stock.name}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <span className={`font-black text-[15px] ${isUp ? 'text-profit-up' : isDown ? 'text-profit-down' : 'text-foreground'}`}>
                                                            {price ? price.price.toFixed(2) : '--'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg font-black text-[13px] ${
                                                            isUp ? 'bg-profit-up/10 text-profit-up' : 
                                                            isDown ? 'bg-profit-down/10 text-profit-down' : 
                                                            'bg-muted text-muted-foreground'
                                                        }`}>
                                                            {price ? `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%` : '--'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); handleDeleteStock(stock.id); }}
                                                            className="p-2 rounded-xl text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center p-20 space-y-4">
                                <div className="w-20 h-20 rounded-[2rem] bg-muted/30 flex items-center justify-center">
                                    <Search className="w-10 h-10 text-muted-foreground/30" />
                                </div>
                                <div className="text-center space-y-1">
                                    <p className="font-black text-muted-foreground">该分组暂无股票</p>
                                    <p className="text-[12px] text-muted-foreground/60 font-medium">点击上方“添加股票”按钮开始自选</p>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center p-20 space-y-4">
                        <div className="w-20 h-20 rounded-[2rem] bg-muted/30 flex items-center justify-center">
                            <Settings2 className="w-10 h-10 text-muted-foreground/30" />
                        </div>
                        <div className="text-center space-y-1">
                            <p className="font-black text-muted-foreground">请选择一个自选分组</p>
                            <p className="text-[12px] text-muted-foreground/60 font-medium">或者点击“+”创建一个新分组</p>
                        </div>
                    </div>
                )}

                {/* Bottom Shadow Overlay for better depth */}
                <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-background/5 to-transparent pointer-events-none"></div>
            </div>

            {/* Modals */}
            <AddGroupModal
                isOpen={showGroupModal}
                onClose={() => setShowGroupModal(false)}
                onSuccess={() => loadGroups()}
            />

            <AddStockModal
                isOpen={showAddStockModal}
                onClose={() => setShowAddStockModal(false)}
                onSuccess={(groupId) => {
                    setSelectedGroupId(groupId);
                    loadStocks(groupId);
                    loadGroups();
                }}
                groups={groups}
                activeGroupId={selectedGroupId}
            />

            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
    );
};

export default FavoritesCard;
