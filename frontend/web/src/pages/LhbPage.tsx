import React, { useEffect, useState } from 'react';
import { getLhbDashboard } from '@/api/lhb';
import type { LhbDashboard, LhbStock, HotSeat, FamousTrader } from '@/types/lhb';
import Loading from '@/components/common/Loading';

const LhbPage: React.FC = () => {
  const [data, setData] = useState<LhbDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'daily' | 'institutional' | 'traders' | 'seats'>('daily');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await getLhbDashboard();
      setData(res.data || null);
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'very_positive':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'positive':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'negative':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const renderDailyData = () => {
    if (!data?.dailyData || data.dailyData.length === 0) {
      return <div className="text-center py-12 text-gray-500">暂无数据</div>;
    }

    return (
      <div className="space-y-3">
        {data.dailyData.map((stock: LhbStock) => (
          <div key={stock.symbol} className="p-4 bg-white rounded-lg border hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <div className="font-semibold text-lg">{stock.name}</div>
                  <div className="text-gray-500 text-sm">{stock.symbol}</div>
                </div>
                <div className="text-sm text-gray-600 max-w-md truncate">{stock.reason}</div>
              </div>

              <div className="flex items-center gap-6 text-right">
                <div>
                  <div className="text-sm text-gray-500">收盘价</div>
                  <div className="font-semibold">¥{stock.closePrice.toFixed(2)}</div>
                </div>

                <div>
                  <div className="text-sm text-gray-500">涨跌幅</div>
                  <div className={`font-semibold ${stock.changePct >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {stock.changePct >= 0 ? '+' : ''}{stock.changePct.toFixed(2)}%
                  </div>
                </div>

                <div>
                  <div className="text-sm text-gray-500">龙虎榜净买</div>
                  <div className={`font-semibold ${stock.netBuyAmount >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {stock.netBuyAmount >= 0 ? '+' : ''}{(stock.netBuyAmount / 10000).toFixed(0)}万
                  </div>
                </div>

                <div>
                  <div className="text-sm text-gray-500">成交额</div>
                  <div className="font-semibold">{(stock.totalAmount / 10000).toFixed(0)}万</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderInstitutionalData = () => {
    if (!data?.institutionalData || data.institutionalData.length === 0) {
      return <div className="text-center py-12 text-gray-500">暂无数据</div>;
    }

    return (
      <div className="space-y-3">
        {data.institutionalData.map((stock) => (
          <div key={stock.symbol} className="p-4 bg-white rounded-lg border">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">{stock.name}</div>
                <div className="text-gray-500 text-sm">{stock.symbol}</div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-xs text-gray-500">机构净买</div>
                  <div className={`font-semibold ${stock.netBuyAmount >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(stock.netBuyAmount / 10000).toFixed(0)}万
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500">买入次数</div>
                  <div className="font-semibold text-red-600">{stock.buyCount}</div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500">卖出次数</div>
                  <div className="font-semibold text-green-600">{stock.sellCount}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderFamousTraders = () => {
    const traders = data?.famousTraders?.famousTraders || [];
    
    if (traders.length === 0) {
      return <div className="text-center py-12 text-gray-500">暂无数据</div>;
    }

    return (
      <div className="space-y-3">
        {traders.map((trader: FamousTrader) => (
          <div key={trader.traderName} className="p-4 bg-white rounded-lg border">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-lg">{trader.traderName}</div>
                <div className="text-xs text-gray-500 mt-1">
                  席位: {trader.seats.slice(0, 2).join(', ')}{trader.seats.length > 2 && `等${trader.seats.length}个`}
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-xs text-gray-500">净买入</div>
                  <div className={`font-semibold ${trader.netAmount >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(trader.netAmount / 10000).toFixed(0)}万
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500">买入</div>
                  <div className="font-semibold text-red-600">{trader.buyCount}次</div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500">卖出</div>
                  <div className="font-semibold text-green-600">{trader.sellCount}次</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderHotSeats = () => {
    if (!data?.hotSeats || data.hotSeats.length === 0) {
      return <div className="text-center py-12 text-gray-500">暂无数据</div>;
    }

    return (
      <div className="space-y-3">
        {data.hotSeats.map((seat: HotSeat, index: number) => (
          <div key={seat.seatName} className="p-4 bg-white rounded-lg border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-lg font-bold text-gray-400 w-8">#{index + 1}</div>
                <div>
                  <div className="font-semibold">{seat.seatName}</div>
                  {seat.isFamous && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                      {seat.traderName}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-xs text-gray-500">净买入</div>
                  <div className={`font-semibold ${seat.netAmount >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(seat.netAmount / 10000).toFixed(0)}万
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-gray-500">买入次数</div>
                  <div className="font-semibold">{seat.buyCount}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <Loading text="加载龙虎榜数据..." />;
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">龙虎榜分析</h1>
          <p className="text-gray-500 mt-1">追踪主力资金动向，识别游资行为</p>
        </div>
        <div className="text-sm text-gray-500">
          更新于: {data?.updateTime ? new Date(data.updateTime).toLocaleTimeString() : '-'}
        </div>
      </div>

      {/* 市场情绪 */}
      {data?.marketSentiment && (
        <div className={`p-4 rounded-lg border ${getSentimentColor(data.marketSentiment.sentiment)}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-80">市场情绪</div>
              <div className="text-xl font-bold">{data.marketSentiment.sentimentName}</div>
            </div>
            <div className="text-right">
              <div className="text-sm opacity-80">龙虎榜净买入</div>
              <div className="text-xl font-bold">
                {(data.marketSentiment.totalNetBuy / 100000000).toFixed(2)}亿
              </div>
            </div>
          </div>
          <div className="mt-2 text-sm opacity-80">{data.marketSentiment.analysis}</div>
        </div>
      )}

      {/* Tab 导航 */}
      <div className="flex gap-2 border-b">
        {[
          { key: 'daily', label: '每日龙虎榜' },
          { key: 'institutional', label: '机构交易' },
          { key: 'traders', label: '游资动向' },
          { key: 'seats', label: '热门席位' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容区域 */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {activeTab === 'daily' && '今日龙虎榜'}
            {activeTab === 'institutional' && '机构交易统计'}
            {activeTab === 'traders' && '知名游资动向'}
            {activeTab === 'seats' && '热门营业部排行'}
          </h2>
          <button
            onClick={fetchData}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            刷新数据
          </button>
        </div>

        {activeTab === 'daily' && renderDailyData()}
        {activeTab === 'institutional' && renderInstitutionalData()}
        {activeTab === 'traders' && renderFamousTraders()}
        {activeTab === 'seats' && renderHotSeats()}
      </div>
    </div>
  );
};

export default LhbPage;
