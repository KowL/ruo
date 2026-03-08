import React, { useEffect, useState } from 'react';
import { getBatchStockRealtime } from '@/api/stock';
import { StockRealtime } from '@/types';
import clsx from 'clsx';

// 带前缀的请求symbol与无前缀的返回key映射
const INDICES = [
    { requestSymbol: 'sh000001', key: '000001', name: '上证指数' },
    { requestSymbol: 'sz399001', key: '399001', name: '深证成指' },
    { requestSymbol: 'sz399006', key: '399006', name: '创业板指' },
    { requestSymbol: 'sh000688', key: '000688', name: '科创50' },
];

const IndexCards: React.FC = () => {
    const [data, setData] = useState<Record<string, StockRealtime>>({});
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            // 使用带前缀的请求symbol
            const symbols = INDICES.map(i => i.requestSymbol);
            const res = await getBatchStockRealtime(symbols);
            setData(res);
        } catch (error) {
            console.error('获取指数数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const timer = setInterval(fetchData, 60000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {INDICES.map((index) => {
                // 后端返回的key是无前缀的
                const quote = data[index.key];
                const changePct = quote?.changePct || 0;
                const price = quote?.price || 0;

                return (
                    <div
                        key={index.key}
                        className="bg-card text-card-foreground border rounded-xl p-4 shadow-sm hover-lift transition-all group"
                    >
                        <div className="flex flex-col">
                            <span className="text-xs text-muted-foreground font-medium mb-1 group-hover:text-primary transition-colors">
                                {index.name}
                            </span>
                            <div className="flex items-baseline justify-between mt-1">
                                <span className="text-xl font-bold font-mono tracking-tight text-foreground">
                                    {loading ? '---' : price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </span>
                                <span className={clsx(
                                    "text-sm font-bold numbers ml-2 px-1.5 py-0.5 rounded",
                                    changePct >= 0 ? "text-profit-up bg-profit-up/10" : "text-loss-up bg-loss-up/10"
                                )}>
                                    {loading ? '--%' : `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%`}
                                </span>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default IndexCards;
