import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { getRawNews } from '@/api/news';
import { News } from '@/types';
import { usePortfolioStore } from '@/store/portfolioStore';
import ReactECharts from 'echarts-for-react';

const DashboardPage: React.FC = () => {
  // Real Portfolio Data
  const { portfolios, totalValue, totalProfitLoss, totalProfitLossRatio, fetchPortfolios, loading: portfolioLoading } = usePortfolioStore();

  useEffect(() => {
    fetchPortfolios();
    // Auto-refresh every 60s
    const timer = setInterval(() => {
      fetchPortfolios();
    }, 60000);
    return () => clearInterval(timer);
  }, []); // Run once on mount

  // Top Movers (Sort by absolute change percent)
  const portfolioMovements = [...(portfolios || [])]
    .sort((a, b) => Math.abs(b.changePct || 0) - Math.abs(a.changePct || 0))
    .slice(0, 3)

    .map(p => ({
      code: p.symbol,
      name: p.name,
      changePercent: p.changePct,
      price: p.currentPrice
    }));

  // Mock Sentiment Data (can be connected to API later)
  const sentimentScore = 0.45;
  const sentimentLabel = '中性';

  // News Data
  const [newsList, setNewsList] = useState<News[]>([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [selectedNews, setSelectedNews] = useState<News | null>(null);

  useEffect(() => {
    const fetchNews = async (isBackground = false) => {
      try {
        if (!isBackground) setNewsLoading(true);
        const data = await getRawNews(undefined, 24, 20);
        setNewsList(data);
      } catch (error) {
        console.error('获取新闻失败:', error);
      } finally {
        if (!isBackground) setNewsLoading(false);
      }
    };

    fetchNews();
    const intervalId = setInterval(() => fetchNews(true), 30000); // 30s refresh for news
    return () => clearInterval(intervalId);
  }, []);

  const formatTimeAgo = (publishTime: string) => {
    const now = new Date();
    const publish = new Date(publishTime);
    const diffMs = now.getTime() - publish.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}分钟前`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}小时前`;
    return `${Math.floor(diffHours / 24)}天前`;
  };

  const riskAlerts = [
    { type: 'warning', message: '新能源行业仓位过重，建议适度减持' },
    { type: 'info', message: '现金比例偏低，建议保留10%应急资金' },
  ];

  const getProfitColor = (percent: number) => {
    // CN Market: Red up, Green down
    return percent >= 0 ? 'text-[#FF3B30]' : 'text-[#34C759]';
  };

  const getProfitBgColor = (percent: number) => {
    // CN Market: Red up, Green down (with opacity)
    return percent >= 0 ? 'bg-[rgba(255,59,48,0.15)]' : 'bg-[rgba(52,199,89,0.15)]';
  };

  // ECharts Option for Sentiment Gauge
  const getGaugeOption = (score: number) => ({
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 1,
        splitNumber: 5,
        itemStyle: {
          color: '#58D9F9',
          shadowColor: 'rgba(0,138,255,0.45)',
          shadowBlur: 10,
          shadowOffsetX: 2,
          shadowOffsetY: 2
        },
        progress: {
          show: true,
          roundCap: true,
          width: 8
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '12%',
          width: 10,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: 'auto'
          }
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 8
          }
        },
        axisTick: {
          splitNumber: 2,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        splitLine: {
          length: 8,
          lineStyle: {
            width: 3,
            color: '#999'
          }
        },
        axisLabel: {
          distance: 10,
          color: '#999',
          fontSize: 10
        },
        title: {
          show: false
        },
        detail: {
          show: false
        },
        data: [{ value: score }]
      }
    ]
  });

  return (
    <div className="p-6 space-y-6 animate-fade-in pb-24 lg:pb-6">
      <div className="flex flex-col space-y-1 mb-2">
        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">概览</h1>
        <p className="text-sm text-[var(--color-text-secondary)]">欢迎回来，今日市场情绪 {sentimentLabel}</p>
      </div>

      {/* 第一行：资产全景 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 总资产卡片 */}
        <div className="glass-card lg:col-span-2 p-6 hover-lift relative overflow-hidden">
          {/* Background Glow */}
          <div className="absolute top-0 right-0 -mr-10 -mt-10 w-48 h-48 bg-purple-500/10 blur-3xl rounded-full pointer-events-none"></div>

          <div className="flex items-center justify-between mb-6 relative z-10">
            <h2 className="text-base font-medium text-[var(--color-text-secondary)]">总资产</h2>
            {/* Market toggle removed */}
          </div>

          <div className="space-y-2 relative z-10">
            <div className="flex items-baseline space-x-4">
              <span className="text-4xl font-bold numbers tracking-tight text-white">
                {portfolioLoading ? '...' : `¥${(totalValue || 0).toLocaleString()}`}
              </span>
            </div>
            <div className="flex items-center space-x-3 mt-2">
              <span className={clsx('text-sm font-semibold px-2 py-0.5 rounded flex items-center', getProfitColor(totalProfitLossRatio || 0), getProfitBgColor(totalProfitLossRatio || 0))}>
                {totalProfitLoss >= 0 ? '+' : ''}{(totalProfitLoss || 0).toLocaleString()} ({totalProfitLossRatio >= 0 ? '+' : ''}{((totalProfitLossRatio || 0) * 100).toFixed(2)}%)
              </span>

              <span className="text-xs text-[var(--color-text-muted)]">今日盈亏</span>
            </div>
          </div>
        </div>

        {/* Ruo情绪指数 */}
        <div className="glass-card p-6 flex flex-col justify-between hover-lift">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-base font-medium text-[var(--color-text-secondary)]">Ruo 情绪指数</h3>
            <span className="text-xs px-2 py-1 rounded bg-purple-500/20 text-purple-400 border border-purple-500/20">{sentimentLabel}</span>
          </div>

          <div className="h-28 w-full flex items-center justify-center -mt-4">
            <ReactECharts
              option={getGaugeOption(sentimentScore)}
              style={{ height: '100%', width: '100%' }}
              notMerge={true}
            />
          </div>

          <div className="text-center mt-[-10px]">
            <p className="text-2xl font-bold text-white numbers">{sentimentScore * 100}</p>
            <p className="text-xs text-[var(--color-text-secondary)] mt-1">分歧较大，建议观望</p>
          </div>
        </div>
      </div>

      {/* 第二行：核心动态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 持仓异动卡片 */}
        <div className="glass-card p-6 hover-lift">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-base font-medium text-white flex items-center">
              <span className="mr-2 text-lg">📊</span> 持仓异动
            </h3>
            <span className="text-xs text-[var(--color-text-muted)]">Top 3 Movers</span>
          </div>

          <div className="space-y-3">
            {portfolioLoading ? (
              <div className="text-center py-8 text-[var(--color-text-muted)]">加载中...</div>
            ) : portfolioMovements.length === 0 ? (
              <div className="text-center py-8 text-[var(--color-text-muted)]">暂无持仓数据</div>
            ) : (
              portfolioMovements.map((stock, index) => (
                <div
                  key={index}
                  className="group bg-[var(--color-surface-1)]/40 hover:bg-[var(--color-surface-3)] p-3 rounded-xl transition-all border border-white/5 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={clsx("w-1 h-8 rounded-full", stock.changePercent >= 0 ? "bg-[#FF3B30]" : "bg-[#34C759]")}></div>
                      <div>
                        <div className="font-bold text-sm text-white group-hover:text-purple-400 transition-colors">{stock.name}</div>
                        <div className="text-xs text-[var(--color-text-secondary)] font-mono">{stock.code}</div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className={clsx('text-sm font-bold numbers', getProfitColor(stock.changePercent))}>
                        {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent}%
                      </div>
                      <div className="text-xs text-[var(--color-text-secondary)] numbers">¥{stock.price}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 快讯 */}
        <div className="glass-card p-6 hover-lift flex flex-col h-[400px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-base font-medium text-white flex items-center">
              <span className="mr-2 text-lg">⚡</span> 7x24 快讯
            </h3>
            <div className="flex items-center space-x-2">
              {newsLoading && <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>}
            </div>
          </div>

          <div className="space-y-4 overflow-y-auto flex-1 pr-2 custom-scrollbar">
            {newsLoading && newsList.length === 0 ? (
              <div className="text-center text-[var(--color-text-secondary)] py-10">
                加载中...
              </div>
            ) : newsList.length === 0 ? (
              <div className="text-center text-[var(--color-text-secondary)] py-10">
                暂无快讯
              </div>
            ) : (
              newsList.map((news) => (
                <div
                  key={news.id}
                  className="relative pl-4 border-l border-[var(--color-surface-4)] hover:border-purple-500/50 transition-colors py-1 group cursor-pointer"
                  onClick={() => setSelectedNews(news)}
                >
                  <div className="absolute left-[-5px] top-2 w-2.5 h-2.5 rounded-full bg-[var(--color-surface-4)] group-hover:bg-purple-500 transition-colors border-2 border-[var(--color-surface-2)]"></div>
                  <div className="mb-1 flex items-center space-x-2">
                    <span className="text-xs text-[var(--color-text-secondary)] font-mono opacity-80">
                      {formatTimeAgo(news.publishTime)}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface-3)] text-[var(--color-text-secondary)] border border-white/5">
                      {news.source === 'cls' ? '财联社' : news.source === 'xueqiu' ? '雪球' : news.source}
                    </span>
                  </div>
                  <h4 className="text-sm text-gray-300 group-hover:text-white transition-colors leading-relaxed line-clamp-2">
                    {news.title || news.content.slice(0, 100)}
                  </h4>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 第三行：风险雷达 */}
      <div className="glass-card p-6 hover-lift mb-6">
        <h3 className="text-base font-medium text-white flex items-center mb-4">
          <span className="mr-2 text-lg">📡</span> 风险雷达
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {riskAlerts.map((alert, index) => (
            <div
              key={index}
              className={clsx(
                'p-4 rounded-xl border border-dashed transition-all duration-300',
                alert.type === 'warning'
                  ? 'bg-orange-500/5 border-orange-500/30 hover:bg-orange-500/10'
                  : 'bg-blue-500/5 border-blue-500/30 hover:bg-blue-500/10'
              )}
            >
              <div className="flex items-start space-x-3">
                <span className={clsx(
                  'text-lg mt-0.5',
                  alert.type === 'warning' ? 'text-orange-500' : 'text-blue-500'
                )}>
                  {alert.type === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <div>
                  <h5 className={clsx('text-sm font-bold mb-1', alert.type === 'warning' ? 'text-orange-400' : 'text-blue-400')}>
                    {alert.type === 'warning' ? '风险提示' : '建议'}
                  </h5>
                  <p className="text-sm text-gray-400">{alert.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>


      {/* 新闻详情弹窗 */}
      {
        selectedNews && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in" onClick={() => setSelectedNews(null)}>
            <div className="glass-card w-full max-w-2xl overflow-hidden shadow-2xl transform transition-all scale-100" onClick={e => e.stopPropagation()}>
              <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                <div className="flex items-center space-x-3">
                  <span className="text-xs px-2 py-1 rounded bg-purple-500/20 text-purple-300 border border-purple-500/20">
                    {selectedNews.source === 'cls' ? '财联社' : selectedNews.source === 'xueqiu' ? '雪球' : selectedNews.source}
                  </span>
                  <span className="text-sm text-[var(--color-text-secondary)] font-mono">
                    {formatTimeAgo(selectedNews.publishTime)}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedNews(null)}
                  className="p-1 rounded-full hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                {selectedNews.title && <h3 className="text-xl font-bold mb-6 text-white leading-tight">{selectedNews.title}</h3>}
                <div className="whitespace-pre-wrap text-gray-300 leading-7 text-base font-light">
                  {selectedNews.content}
                </div>
                {selectedNews.aiAnalysis && (
                  <div className="mt-8 p-5 bg-purple-500/5 rounded-xl border border-purple-500/10">
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-purple-400 text-lg">🤖</span>
                      <h4 className="text-sm font-bold text-purple-400">AI 智能解读</h4>
                    </div>
                    <p className="text-sm text-gray-400 leading-relaxed italic">{selectedNews.aiAnalysis}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      }
    </div>
  );
};

export default DashboardPage;