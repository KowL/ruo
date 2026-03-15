import React, { useState, useEffect } from 'react';
import { searchStock } from '@/api/stock';
import { addStock, StockGroup, SearchStock } from '@/api/favorites';
import Toast from '@/components/common/Toast';
import { X, Search, Plus, Loader2 } from 'lucide-react';

interface AddStockModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (groupId: number) => void;
    groups: StockGroup[];
    activeGroupId: number | null;
}

const AddStockModal: React.FC<AddStockModalProps> = ({ isOpen, onClose, onSuccess, groups, activeGroupId }) => {
    const [searchKeyword, setSearchKeyword] = useState('');
    const [searchResults, setSearchResults] = useState<SearchStock[]>([]);
    const [searching, setSearching] = useState(false);
    const [selectedGroupId, setSelectedGroupId] = useState<number | null>(activeGroupId);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    useEffect(() => {
        setSelectedGroupId(activeGroupId);
    }, [activeGroupId, isOpen]);

    if (!isOpen) return null;

    const showToast = (message: string, type: 'success' | 'error') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleSearch = async () => {
        if (!searchKeyword.trim() || searchKeyword.trim().length < 2) {
            setSearchResults([]);
            return;
        }
        setSearching(true);
        try {
            const results = await searchStock(searchKeyword.trim());
            const formattedResults = results.map(stock => ({
                ...stock,
                isFavorited: false 
            }));
            setSearchResults(formattedResults);
        } catch (error) {
            console.error('搜索失败:', error);
            showToast('搜索失败', 'error');
        } finally {
            setSearching(false);
        }
    };

    const handleAddStock = async (stock: SearchStock) => {
        const groupId = selectedGroupId || (groups.length > 0 ? groups[0].id : null);
        if (!groupId) {
            showToast('请先选择一个分组', 'error');
            return;
        }
        try {
            await addStock({ groupId, symbol: stock.symbol, name: stock.name });
            showToast(`已添加 ${stock.name}`, 'success');
            setTimeout(() => {
                onSuccess(groupId);
                onClose();
                setSearchKeyword('');
                setSearchResults([]);
            }, 1000);
        } catch (error: any) {
            showToast(error.response?.data?.detail || '添加失败', 'error');
        }
    };

    return (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-300">
            <div className="bg-card w-full max-w-lg relative overflow-hidden border border-border rounded-3xl shadow-[0_32px_64px_-12px_rgba(0,0,0,0.2)] flex flex-col max-h-[85vh]">
                {/* Modal Header */}
                <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30 relative shrink-0 sticky top-0 z-10">
                    <div className="flex items-center">
                        <div className="w-1.5 h-6 bg-gradient-to-b from-orange-400 to-orange-600 rounded-full mr-4 shadow-[0_0_12px_rgba(249,115,22,0.4)]"></div>
                        <div>
                            <h3 className="text-xl font-black text-foreground tracking-tight">添加自选股票</h3>
                            <p className="text-xs text-muted-foreground mt-0.5 font-medium">收藏您感兴趣的股票以便追踪</p>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        type="button"
                        className="p-2 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition-all active:scale-95"
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-orange-500/5 rounded-full blur-3xl pointer-events-none"></div>
                </div>

                {/* Modal Content */}
                <div className="p-6 space-y-6 flex-1 flex flex-col min-h-0 overflow-y-auto custom-scrollbar">
                    {/* Group Selection */}
                    <div className="space-y-2">
                        <label className="text-[13px] font-bold text-muted-foreground flex items-center gap-1.5 ml-1">
                            <span>选择存放分组</span>
                        </label>
                        <select
                            value={selectedGroupId || ''}
                            onChange={(e) => setSelectedGroupId(Number(e.target.value))}
                            className="w-full px-4 py-3 bg-muted/50 border border-slate-200/50 rounded-2xl text-foreground focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500/30 transition-all font-bold cursor-pointer"
                        >
                            {groups.map(group => (
                                <option key={group.id} value={group.id}>{group.name}</option>
                            ))}
                            {groups.length === 0 && <option value="">暂无分组</option>}
                        </select>
                    </div>

                    {/* Search Input */}
                    <div className="space-y-3">
                        <div className="flex gap-3">
                            <div className="relative flex-1 group">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground transition-colors group-focus-within:text-orange-500" />
                                <input
                                    type="text"
                                    placeholder="代码 / 名称 / 拼音"
                                    value={searchKeyword}
                                    onChange={(e) => setSearchKeyword(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                    className="w-full pl-11 pr-10 py-3.5 bg-muted border border-slate-200/50 rounded-2xl text-foreground placeholder-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500/30 transition-all font-bold text-sm"
                                    autoFocus
                                />
                                {searchKeyword && (
                                    <button
                                        onClick={() => {
                                            setSearchKeyword('');
                                            setSearchResults([]);
                                        }}
                                        type="button"
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-all"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                            <button
                                onClick={handleSearch}
                                type="button"
                                disabled={searching || !searchKeyword.trim()}
                                className={`
                                    px-8 rounded-2xl bg-gradient-to-br from-orange-400 to-orange-600 text-white font-black text-sm shadow-lg shadow-orange-500/20 hover:shadow-orange-500/30 hover:-translate-y-0.5 active:scale-95 transition-all
                                    ${searching || !searchKeyword.trim() ? 'opacity-50 cursor-not-allowed saturate-0' : ''}
                                `}
                            >
                                {searching ? <Loader2 className="w-5 h-5 animate-spin" /> : '搜索'}
                            </button>
                        </div>
                    </div>

                    {/* Search Results Area */}
                    <div className="flex-1 min-h-[320px] bg-muted/30 rounded-2xl border border-slate-100/50 overflow-hidden flex flex-col">
                        {searchResults.length > 0 ? (
                            <div className="divide-y divide-slate-100 overflow-y-auto flex-1 custom-scrollbar px-2">
                                {searchResults.map((stock) => (
                                    <div
                                        key={stock.symbol}
                                        className="flex items-center justify-between p-4 hover:bg-white rounded-xl my-1 transition-all group border border-transparent hover:border-orange-100 hover:shadow-sm"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center font-black text-xs text-slate-400 group-hover:bg-orange-50 group-hover:text-orange-500 transition-colors">
                                                {stock.symbol.slice(0, 2)}
                                            </div>
                                            <div>
                                                <div className="font-black text-foreground group-hover:text-orange-500 transition-colors">{stock.name}</div>
                                                <div className="text-xs font-mono font-bold text-slate-400 mt-0.5">{stock.symbol}</div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleAddStock(stock)}
                                            type="button"
                                            className="px-4 py-2 text-xs rounded-xl bg-orange-50 text-orange-600 hover:bg-orange-500 hover:text-white font-black transition-all border border-orange-100"
                                        >
                                            <Plus className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-10 text-center space-y-4">
                                {searching ? (
                                    <Loader2 className="w-8 h-8 text-orange-500 animate-spin opacity-40" />
                                ) : (
                                    <>
                                        <div className="w-16 h-16 rounded-3xl bg-slate-50 flex items-center justify-center">
                                            <Search className="w-8 h-8 opacity-10 text-foreground" />
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-sm font-black text-slate-600">{searchKeyword ? '未找到相关股票' : '开始搜索'}</p>
                                            <p className="text-[11px] font-medium text-slate-400 leading-relaxed">
                                                {searchKeyword ? `抱歉，没能找到关键词为 "${searchKeyword}" 的结果` : '您可以输入代码、完整名称或拼音简写'}
                                            </p>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Modal Footer */}
                <div className="p-4 px-6 border-t border-border flex justify-end bg-muted/10 shrink-0 sticky bottom-0 z-10">
                    <button
                        onClick={onClose}
                        type="button"
                        className="px-10 py-3 rounded-2xl bg-white border border-slate-200 hover:bg-muted font-black text-sm text-slate-700 transition-all hover:shadow-sm active:scale-95"
                    >
                        完成
                    </button>
                </div>
                
                {/* Toast Overlay */}
                {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            </div>
        </div>
    );
};

export default AddStockModal;
