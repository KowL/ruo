import React, { useEffect, useState } from 'react';
import { getRadarDashboard } from '@/api/radar';
import type { RadarSignal, RadarDashboard } from '@/types/radar';
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
        return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'strong_up':
      case 'auction_burst':
        return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
      case 'limit_down':
        return 'text-green-400 bg-green-400/10 border-green-400/20';
      case 'strong_down':
        return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const renderSignalList = (signals: RadarSignal[]) => {
    if (loading && (!signals || signals.length === 0)) {
      return (
        <div className="flex-1 bg-card flex items-center justify-center border border-border text-muted-foreground rounded-xl">
          <div className="w-12 h-12 border-4 border-white/5 border-t-primary-light animate-spin rounded-full"></div>
          <div className="text-gray-500 font-medium">正在同步雷达信号...</div>
        </div>
      );
    }

    if (!signals || signals.length === 0) {
      return (
        <div className="text-center py-20 text-gray-500">
          <div className="text-4xl mb-4 text-gray-700">📡</div>
          暂无信号
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {signals.map((signal, index) => (
          <div
            key={`${signal.symbol}-${index}`}
            className="flex items-center justify-between p-4 rounded-xl border border-border bg-card hover:bg-muted transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="text-center w-10">
                <div className="text-xl font-black text-white/10 group-hover:text-white/20 transition-colors">
                  {String(index + 1).padStart(2, '0')}
                </div>
              </div>
              <div>
                <div className="font-bold text-lg text-white group-hover:text-primary-light transition-colors">{signal.name}</div>
                <div className="text-gray-400 text-sm font-mono">{signal.symbol}</div>
              </div>
            </div>

            <div className="flex items-center gap-8">
              <div className="text-right">
                <div className={`inline-block px-3 py-0.5 rounded-full text-xs font-bold border ${getSignalColor(signal.signalType)}`}>
                  {signal.signalName}
                </div>
                <div className="text-xs text-gray-400 mt-1">{signal.reason}</div>
              </div>

              <div className="text-right w-28">
                {signal.price && (
                  <div className="text-lg font-bold text-white">¥{signal.price.toFixed(2)}</div>
                )}
                {signal.changePct !== undefined && (
                  <div className={`text-sm font-bold ${signal.changePct >= 0 ? 'text-profit-up' : 'text-loss-up'}`}>
                    {signal.changePct >= 0 ? '+' : ''}{signal.changePct.toFixed(2)}%
                  </div>
                )}
                {signal.openPct !== undefined && (
                  <div className="text-xs text-gray-500">
                    高开 {signal.openPct.toFixed(2)}%
                  </div>
                )}
              </div>

              <div className="text-right w-32 border-l border-border pl-6">
                <div className="text-sm font-medium text-gray-300">{formatMoney(signal.amount)}</div>
                <div className="text-xs text-gray-500 mt-0.5">强度: <span className="text-primary-light font-bold">{signal.signalStrength.toFixed(1)}</span></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };


  if (error) {
    return (
      <div className="p-6">
        <div className="bg-card border-destructive/20 p-8 text-center bg-destructive/5 rounded-2xl border">
          <p className="text-red-400 mb-6 flex items-center justify-center gap-2">
            <span className="text-2xl">⚠️</span> {error}
          </p>
          <button
            onClick={fetchData}
            className="px-6 py-2.5 bg-red-500/20 text-red-100 rounded-xl hover:bg-red-500/30 border border-red-500/30 transition-all font-medium"
          >
            尝试重新加载
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
    <div className="p-6 space-y-6 max-w-7xl mx-auto pt-0">
      <div className="flex items-center justify-end mb-4">
        <div className="text-sm font-mono text-muted-foreground bg-muted px-3 py-1 rounded-full border border-border">
          TIMESTAMP: {data?.updateTime ? new Date(data.updateTime).toLocaleTimeString() : '-'}
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          className={`bg-card text-card-foreground border border-border p-6 cursor-pointer transition-all duration-300 relative overflow-hidden rounded-xl group ${activeTab === 'auction'
            ? 'ring-2 ring-orange-500/50 bg-orange-500/10 shadow-[0_0_20px_rgba(249,115,22,0.15)]'
            : 'hover:bg-muted'
            }`}
          onClick={() => setActiveTab('auction')}
        >
          <div className="text-sm font-bold text-muted-foreground group-hover:text-foreground transition-colors">竞价爆点</div>
          <div className="text-4xl font-black text-orange-500 mt-2 tracking-tighter">{data?.auctionSignals?.length || 0}</div>
          <div className="text-xs text-muted-foreground mt-2 border-t border-border pt-2 font-medium">高开3-7% + 竞价额&gt;1000万</div>
          {activeTab === 'auction' && <div className="absolute top-0 right-0 w-2 h-full bg-orange-500/50" />}
        </div>

        <div
          className={`bg-card text-card-foreground border border-border p-6 cursor-pointer transition-all duration-300 relative overflow-hidden rounded-xl group ${activeTab === 'movers'
            ? 'ring-2 ring-red-500/50 bg-red-500/10 shadow-[0_0_20px_rgba(239,68,68,0.15)]'
            : 'hover:bg-muted'
            }`}
          onClick={() => setActiveTab('movers')}
        >
          <div className="text-sm font-bold text-muted-foreground group-hover:text-foreground transition-colors">实时异动</div>
          <div className="text-4xl font-black text-red-500 mt-2 tracking-tighter">{data?.intradayMovers?.length || 0}</div>
          <div className="text-xs text-muted-foreground mt-2 border-t border-border pt-2 font-medium">涨跌幅&gt;5%的异动股票</div>
          {activeTab === 'movers' && <div className="absolute top-0 right-0 w-2 h-full bg-red-500/50" />}
        </div>

        <div
          className={`bg-card text-card-foreground border border-border p-6 cursor-pointer transition-all duration-300 relative overflow-hidden rounded-xl group ${activeTab === 'candidates'
            ? 'ring-2 ring-purple-500/50 bg-purple-500/10 shadow-[0_0_20px_rgba(168,85,247,0.15)]'
            : 'hover:bg-muted'
            }`}
          onClick={() => setActiveTab('candidates')}
        >
          <div className="text-sm font-bold text-muted-foreground group-hover:text-foreground transition-colors">涨停候选</div>
          <div className="text-4xl font-black text-purple-500 mt-2 tracking-tighter">{data?.limitUpCandidates?.length || 0}</div>
          <div className="text-xs text-muted-foreground mt-2 border-t border-border pt-2 font-medium">涨停池 + 即将涨停</div>
          {activeTab === 'candidates' && <div className="absolute top-0 right-0 w-2 h-full bg-purple-500/50" />}
        </div>
      </div>

      {/* 信号列表 */}
      <div className="bg-card text-card-foreground border border-border p-6 space-y-6 rounded-xl shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-6 rounded-full ${activeTab === 'auction' ? 'bg-orange-500' :
              activeTab === 'movers' ? 'bg-red-500' : 'bg-purple-500'
              }`} />
            <h2 className="text-xl font-bold text-white tracking-tight">
              {activeTab === 'auction' && '竞价爆点信号'}
              {activeTab === 'movers' && '实时异动监控'}
              {activeTab === 'candidates' && '涨停候选池'}
            </h2>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-xl border border-border transition-all text-sm font-bold shadow-sm"
          >
            <span>🔄</span> 刷新数据
          </button>
        </div>

        <div className="min-h-[400px]">
          {renderSignalList(currentSignals || [])}
        </div>
      </div>
    </div>
  );
};

export default RadarPage;
