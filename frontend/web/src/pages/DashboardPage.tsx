import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { getRawNews } from '@/api/news';
import { getDashboardData, DashboardData } from '@/api/dashboard';
import { getOpeningReport, DailyReport } from '@/api/sentiment';
import { News } from '@/types';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getProfitColor, getProfitBgColor } from '@/utils/format';
import ReactECharts from 'echarts-for-react';

const DashboardPage: React.FC = () => {
  // Real Portfolio Data
  const { portfolios, totalValue, totalProfitLoss, totalProfitLossRatio, fetchPortfolios, loading: portfolioLoading } = usePortfolioStore();

  // Dashboard Data
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetchPortfolios();
    fetchDashboardData();

    // Auto-refresh every 60s
    const timer = setInterval(() => {
      fetchPortfolios();
      fetchDashboardData();
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await getDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
    }
  };

  // Sentiment Data
  const sentiment = dashboardData?.sentiment;
  const sentimentScore = sentiment ? sentiment.score / 100 : 0.5;
  const sentimentLabel = sentiment?.label || '中性';
  const sentimentDescription = sentiment?.description || '分歧较大，建议观望';

  // Market Breadth Data (保留给未来使用)
  // const marketBreadth = dashboardData?.market_breadth;

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

  // News Data
  const [newsList, setNewsList] = useState<News[]>([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [selectedNews, setSelectedNews] = useState<News | null>(null);

  // Daily Report Data
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [reportLoading, setReportLoading] = useState(true);

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

    const fetchDailyReport = async () => {
      try {
        setReportLoading(true);
        const data = await getOpeningReport();
        setDailyReport(data);
      } catch (error) {
        console.error('获取每日简报失败:', error);
      } finally {
        setReportLoading(false);
      }
    };

    fetchNews();
    fetchDailyReport();

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
      {/* 第一行：资产全景 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 总资产卡片 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm lg:col-span-2 p-6 hover-lift relative overflow-hidden">
          {/* Background Glow */}
          <div className="absolute top-0 right-0 -mr-10 -mt-10 w-48 h-48 bg-primary/10 blur-3xl rounded-full pointer-events-none"></div>

          <div className="flex items-center justify-between mb-6 relative z-10">
            <h2 className="text-sm font-medium text-muted-foreground">总资产</h2>
            {/* Market toggle removed */}
          </div>

          <div className="space-y-2 relative z-10">
            <div className="flex items-baseline space-x-4">
              <span className="text-4xl font-bold numbers tracking-tight text-foreground">
                {portfolioLoading ? <span className="animate-pulse text-muted-foreground text-2xl">加载中...</span> : `¥${(totalValue || 0).toLocaleString()}`}
              </span>
            </div>
            <div className="flex items-center space-x-3 mt-2">
              {!portfolioLoading && (
                <>
                  <span className={clsx('text-sm font-semibold px-2 py-0.5 rounded flex items-center', getProfitColor(totalProfitLossRatio || 0), getProfitBgColor(totalProfitLossRatio || 0))}>
                    {totalProfitLoss >= 0 ? '+' : ''}{(totalProfitLoss || 0).toLocaleString()} ({totalProfitLossRatio >= 0 ? '+' : ''}{((totalProfitLossRatio || 0) * 100).toFixed(2)}%)
                  </span>
                  <span className="text-xs text-muted-foreground">今日盈亏</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Ruo情绪指数 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 flex flex-col justify-between hover-lift">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Ruo 情绪指数</h3>
            {!dashboardData ? (
              <div className="w-12 h-5 bg-muted animate-pulse rounded"></div>
            ) : (
              <span className="text-xs px-2 py-1 rounded bg-primary/20 text-primary border border-primary/20">{sentimentLabel}</span>
            )}
          </div>

          <div className="h-28 w-full flex items-center justify-center -mt-4">
            {!dashboardData ? (
              <div className="w-24 h-24 rounded-full border-4 border-white/5 border-t-purple-500/30 animate-spin"></div>
            ) : (
              <ReactECharts
                option={getGaugeOption(sentimentScore)}
                style={{ height: '100%', width: '100%' }}
                notMerge={true}
              />
            )}
          </div>

          <div className="text-center mt-[-10px]">
            <p className="text-2xl font-bold text-foreground numbers">{dashboardData ? (sentiment ? sentiment.score : '--') : '...'}</p>
            <p className="text-xs text-muted-foreground mt-1">{dashboardData ? sentimentDescription : '正在分析市场情绪...'}</p>
          </div>
        </div>
      </div>

      {/* 第二行：每日简报 */}
      <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 hover-lift mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-medium text-foreground flex items-center">
            <span className="mr-2 text-lg">📰</span> 每日简报
          </h3>
          <div className="flex items-center space-x-2">
            {reportLoading && <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>}
            <span className="text-xs text-muted-foreground">{dailyReport?.date || ''}</span>
          </div>
        </div>

        {reportLoading && !dailyReport ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-8 bg-muted rounded w-1/4"></div>
            <div className="h-20 bg-muted rounded w-full"></div>
          </div>
        ) : dailyReport ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-4 mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-foreground">{dailyReport.sentiment_index}</span>
                <span className="text-sm text-muted-foreground">/ 100</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={clsx(
                  "px-2 py-0.5 rounded text-xs font-medium",
                  dailyReport.sentiment_index >= 60 ? "bg-green-500/20 text-green-400" :
                    dailyReport.sentiment_index >= 45 ? "bg-yellow-500/20 text-yellow-400" :
                      "bg-red-500/20 text-red-400"
                )}>
                  {dailyReport.sentiment_label}
                </span>
                {dailyReport.key_factors?.length > 0 && (
                  <div className="flex space-x-1">
                    {dailyReport.key_factors.slice(0, 3).map((factor, idx) => (
                      <span key={idx} className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">
                        {factor}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
              {dailyReport.report}
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">暂无简报数据</div>
        )}
      </div>

      {/* 第三行：核心动态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 持仓异动卡片 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 hover-lift">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-base font-medium text-foreground flex items-center">
              <span className="mr-2 text-lg">📊</span> 持仓异动
            </h3>
            <span className="text-xs text-muted-foreground">Top 3 Movers</span>
          </div>

          <div className="space-y-3">
            {portfolioLoading ? (
              <div className="text-center py-8 text-muted-foreground">加载中...</div>
            ) : portfolioMovements.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">暂无持仓数据</div>
            ) : (
              portfolioMovements.map((stock, index) => (
                <div
                  key={index}
                  className="group bg-muted/40 hover:bg-muted p-3 rounded-xl transition-all border border-border cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={clsx("w-1 h-8 rounded-full", stock.changePercent >= 0 ? "bg-profit-up" : "bg-profit-down")}></div>
                      <div>
                        <div className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">{stock.name}</div>
                        <div className="text-xs text-muted-foreground font-mono">{stock.code}</div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className={clsx('text-sm font-bold numbers', getProfitColor(stock.changePercent))}>
                        {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent}%
                      </div>
                      <div className="text-xs text-muted-foreground numbers">¥{stock.price}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 快讯 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 hover-lift flex flex-col h-[400px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-base font-medium text-foreground flex items-center">
              <span className="mr-2 text-lg">⚡</span> 7x24 快讯
            </h3>
            <div className="flex items-center space-x-2">
              {newsLoading && <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>}
            </div>
          </div>

          <div className="space-y-4 overflow-y-auto flex-1 pr-2 custom-scrollbar">
            {newsLoading && newsList.length === 0 ? (
              <div className="text-center text-muted-foreground py-10">
                加载中...
              </div>
            ) : newsList.length === 0 ? (
              <div className="text-center text-muted-foreground py-10">
                暂无快讯
              </div>
            ) : (
              newsList.map((news) => (
                <div
                  key={news.id}
                  className="relative pl-4 border-l border-border hover:border-primary/50 transition-colors py-1 group cursor-pointer"
                  onClick={() => setSelectedNews(news)}
                >
                  <div className="absolute left-[-5px] top-2 w-2.5 h-2.5 rounded-full bg-muted group-hover:bg-primary transition-colors border-2 border-background"></div>
                  <div className="mb-1 flex items-center space-x-2">
                    <span className="text-xs text-muted-foreground font-mono opacity-80">
                      {formatTimeAgo(news.publishTime)}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">
                      {news.source === 'cls' ? '财联社' : news.source === 'xueqiu' ? '雪球' : news.source}
                    </span>
                  </div>
                  <h4 className="text-sm text-foreground/80 group-hover:text-foreground transition-colors leading-relaxed line-clamp-2">
                    {news.title || news.content.slice(0, 100)}
                  </h4>
                </div>
              ))
            )}
          </div>
        </div>
      </div>


      {/* 新闻详情弹窗 */}
      {
        selectedNews && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-fade-in" onClick={() => setSelectedNews(null)}>
            <div className="bg-card text-card-foreground border rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl transform transition-all scale-100" onClick={e => e.stopPropagation()}>
              <div className="p-4 border-b border-border flex justify-between items-center bg-muted/50">
                <div className="flex items-center space-x-3">
                  <span className="text-xs px-2 py-1 rounded bg-primary/20 text-primary border border-primary/20">
                    {selectedNews.source === 'cls' ? '财联社' : selectedNews.source === 'xueqiu' ? '雪球' : selectedNews.source}
                  </span>
                  <span className="text-sm text-muted-foreground font-mono">
                    {formatTimeAgo(selectedNews.publishTime)}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedNews(null)}
                  className="p-1 rounded-full hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                {selectedNews.title && <h3 className="text-xl font-bold mb-6 text-foreground leading-tight">{selectedNews.title}</h3>}
                <div className="whitespace-pre-wrap text-muted-foreground leading-7 text-base font-light">
                  {selectedNews.content}
                </div>
                {selectedNews.aiAnalysis && (
                  <div className="mt-8 p-5 bg-primary/5 rounded-xl border border-primary/10">
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-primary text-lg">🤖</span>
                      <h4 className="text-sm font-bold text-primary">AI 智能解读</h4>
                    </div>
                    <p className="text-sm text-foreground/70 leading-relaxed italic">{selectedNews.aiAnalysis}</p>
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