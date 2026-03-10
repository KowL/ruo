import React, { useState, useEffect } from 'react';
import { searchStock } from '@/api/stock';
import { addStock, StockGroup, SearchStock } from '@/api/favorites';
import Toast from '@/components/common/Toast';

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
        if (!searchKeyword.trim() || searchKeyword.trim().length < 2) return;
        setSearching(true);
        try {
            const results = await searchStock(searchKeyword.trim());
            // 这里的结果格式需要转换，api/favorites.ts 中的 SearchStock 定义了 isFavorited
            // 但 api/stock.ts 返回的可能没有这个字段
            const formattedResults = results.map(stock => ({
                ...stock,
                isFavorited: false // 初始设为 false，实际应根据当前组检查
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
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-card w-full max-w-lg p-6 relative overflow-hidden border border-border rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">
                {/* Glow Effects */}
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

                <h3 className="text-xl font-bold mb-6 text-foreground flex items-center flex-shrink-0">
                    <span className="w-1 h-6 bg-gradient-to-b from-purple-500 to-blue-500 rounded-full mr-3"></span>
                    添加自选股票
                </h3>

                <div className="relative z-10 space-y-4 flex-1 flex flex-col min-h-0">
                    {/* 分组选择 */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">选择分组</label>
                        <select
                            value={selectedGroupId || ''}
                            onChange={(e) => setSelectedGroupId(Number(e.target.value))}
                            className="w-full px-4 py-2.5 bg-muted/50 border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                        >
                            {groups.map(group => (
                                <option key={group.id} value={group.id}>{group.name}</option>
                            ))}
                            {groups.length === 0 && <option value="">暂无分组</option>}
                        </select>
                    </div>

                    <div className="flex gap-3 mt-4">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                placeholder="输入股票代码或名称，如 000001"
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                className="w-full pl-4 pr-10 py-3 bg-muted/50 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                                autoFocus
                            />
                            {searchKeyword && (
                                <button
                                    onClick={() => {
                                        setSearchKeyword('');
                                        setSearchResults([]);
                                    }}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                            className={`px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium transition-all ${searching || !searchKeyword.trim() ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-90'
                                }`}
                        >
                            {searching ? '搜索中...' : '搜索'}
                        </button>
                    </div>

                    <div className="flex-1 min-h-[250px] overflow-auto bg-muted/30 rounded-xl border border-border mb-6">
                        {searchResults.length > 0 ? (
                            <div className="divide-y divide-border">
                                {searchResults.map((stock) => (
                                    <div
                                        key={stock.symbol}
                                        className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors group"
                                    >
                                        <div>
                                            <div className="font-medium text-foreground group-hover:text-primary transition-colors">{stock.name}</div>
                                            <div className="text-sm font-mono text-muted-foreground">{stock.symbol}</div>
                                        </div>
                                        <button
                                            onClick={() => handleAddStock(stock)}
                                            className="px-4 py-1.5 text-sm rounded-lg border border-primary/30 text-primary hover:bg-primary/10 font-medium transition-all"
                                        >
                                            添加
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-2">
                                {searching ? (
                                    <svg className="animate-spin h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24">
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

                    <div className="flex justify-end pt-2 flex-shrink-0">
                        <button
                            onClick={onClose}
                            className="px-6 py-2.5 rounded-xl border border-border hover:bg-muted transition-all text-sm font-medium text-foreground"
                        >
                            完成
                        </button>
                    </div>
                </div>

                {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            </div>
        </div>
    );
};

export default AddStockModal;
