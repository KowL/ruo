import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getKLineData } from '@/api/stock';
import KLineChart from '@/components/chart/KLineChart';
import Loading from '@/components/common/Loading';
import { KLineData } from '@/types';

const ChartPage: React.FC = () => {
  const { portfolios } = usePortfolioStore();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedName, setSelectedName] = useState<string>('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  useEffect(() => {
    // 默认选择第一个持仓
    if (portfolios.length > 0 && !selectedSymbol) {
      setSelectedSymbol(portfolios[0].symbol);
      setSelectedName(portfolios[0].name);
    }
  }, [portfolios, selectedSymbol]);

  useEffect(() => {
    if (selectedSymbol) {
      fetchKLineData(selectedSymbol, period);
    }
  }, [selectedSymbol, period]);

  const fetchKLineData = async (symbol: string, period: 'daily' | 'weekly' | 'monthly') => {
    setLoading(true);
    try {
      const data = await getKLineData(symbol, period, 120);
      setKlineData(data);
    } catch (error) {
      console.error('获取K线数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectStock = (symbol: string, name: string) => {
    setSelectedSymbol(symbol);
    setSelectedName(name);
  };

  if (portfolios.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">请先添加持仓股票</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 股票选择器 */}
      <div>
        <h2 className="text-xl font-bold mb-4">K线图表</h2>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {portfolios.map((portfolio) => (
            <button
              key={portfolio.symbol}
              onClick={() => handleSelectStock(portfolio.symbol, portfolio.name)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                selectedSymbol === portfolio.symbol
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {portfolio.name}
            </button>
          ))}
        </div>
      </div>

      {/* 周期选择 */}
      <div className="flex gap-2">
        {(['daily', 'weekly', 'monthly'] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              period === p
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {p === 'daily' ? '日K' : p === 'weekly' ? '周K' : '月K'}
          </button>
        ))}
      </div>

      {/* K线图 */}
      {loading ? (
        <Loading text="加载K线数据中..." />
      ) : klineData.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">暂无K线数据</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <KLineChart data={klineData} symbol={selectedSymbol} name={selectedName} />
        </div>
      )}
    </div>
  );
};

export default ChartPage;
