import React, { useEffect, useState } from 'react';
import { getRadarDashboard } from '@/api/radar';
import type { RadarSignal, RadarDashboard } from '@/types/radar';
import Loading from '@/components/common/Loading';
import { formatMoney } from '@/utils/format';

const RadarPage: React.FC = () => {
  const [data, setData] = useState<RadarDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'auction' | 'movers' | 'candidates'>('auction');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await getRadarDashboard();
      setData(res.data || null);
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signalType: string) => {
    switch (signalType) {
      case 'limit_up':
      case 'limit_up_pool':
        return 'text-red-600 bg-red-50';
      case 'strong_up':
      case 'auction_burst':
        return 'text-orange-600 bg-orange-50';
      case 'limit_down':
        return 'text-green-600 bg-green-50';
      case 'strong_down':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const renderSignalList = (signals: RadarSignal[]) => {
    if (!signals || signals.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          暂无信号
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {signals.map((signal, index) => (
          <div
            key={`${signal.symbol}-${index}`}
            className="flex items-center justify-between p-4 bg-white rounded-lg border hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className="text-center w-12">
                <div className="text-lg font-bold text-gray-400">#{index + 1}</div>
              </div>
              <div>
                <div className="font-semibold text-lg">{signal.name}</div>
                <div className="text-gray-500 text-sm">{signal.symbol}</div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getSignalColor(signal.signalType)}`}>
                  {signal.signalName}
                </div>
                <div className="text-sm text-gray-500 mt-1">{signal.reason}</div>
              </div>

              <div className="text-right w-32">
                {signal.price && (
                  <>
                    <div className="text-lg font-semibold">¥{signal.price.toFixed(2)}</div>
                  </>
                )}
                {signal.changePct !== undefined && (
                  <div className={`text-lg font-semibold ${signal.changePct >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {signal.changePct >= 0 ? '+' : ''}{signal.changePct.toFixed(2)}%
                  </div>
                )}
                {signal.openPct !== undefined && (
                  <div className="text-sm text-gray-500">
                    高开 {signal.openPct.toFixed(2)}%
                  </div>
                )}
              </div>

              <div className="text-right w-32">
                <div className="text-sm text-gray-600">{formatMoney(signal.amount)}</div>
                <div className="text-xs text-gray-400">强度: {signal.signalStrength.toFixed(1)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <Loading text="加载短线雷达数据..." />;
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

  const currentSignals = activeTab === 'auction' 
    ? data?.auctionSignals 
    : activeTab === 'movers' 
    ? data?.intradayMovers 
    : data?.limitUpCandidates;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">短线雷达</h1>
          <p className="text-gray-500 mt-1">实时监控市场异动，捕捉短线机会</p>
        </div>
        <div className="text-sm text-gray-500">
          更新于: {data?.updateTime ? new Date(data.updateTime).toLocaleTimeString() : '-'}
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <div 
          className={`p-4 rounded-lg cursor-pointer transition-colors ${activeTab === 'auction' ? 'bg-orange-100 border-2 border-orange-500' : 'bg-white border'}`}
          onClick={() => setActiveTab('auction')}
        >
          <div className="text-sm text-gray-500">竞价爆点</div>
          <div className="text-2xl font-bold text-orange-600">{data?.auctionSignals?.length || 0}</div>
          <div className="text-xs text-gray-400 mt-1">高开3-7% + 竞价额&gt;1000万</div>
        </div>

        <div 
          className={`p-4 rounded-lg cursor-pointer transition-colors ${activeTab === 'movers' ? 'bg-red-100 border-2 border-red-500' : 'bg-white border'}`}
          onClick={() => setActiveTab('movers')}
        >
          <div className="text-sm text-gray-500">实时异动</div>
          <div className="text-2xl font-bold text-red-600">{data?.intradayMovers?.length || 0}</div>
          <div className="text-xs text-gray-400 mt-1">涨跌幅&gt;5%的异动股票</div>
        </div>

        <div 
          className={`p-4 rounded-lg cursor-pointer transition-colors ${activeTab === 'candidates' ? 'bg-purple-100 border-2 border-purple-500' : 'bg-white border'}`}
          onClick={() => setActiveTab('candidates')}
        >
          <div className="text-sm text-gray-500">涨停候选</div>
          <div className="text-2xl font-bold text-purple-600">{data?.limitUpCandidates?.length || 0}</div>
          <div className="text-xs text-gray-400 mt-1">涨停池 + 即将涨停</div>
        </div>
      </div>

      {/* 信号列表 */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {activeTab === 'auction' && '竞价爆点信号'}
            {activeTab === 'movers' && '实时异动监控'}
            {activeTab === 'candidates' && '涨停候选池'}
          </h2>
          <button
            onClick={fetchData}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            刷新数据
          </button>
        </div>

        {renderSignalList(currentSignals || [])}
      </div>
    </div>
  );
};

export default RadarPage;
