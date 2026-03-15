import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { getDashboardData, DashboardData } from '@/api/dashboard';
import { getOpeningReport, DailyReport } from '@/api/sentiment';
import { usePortfolioStore } from '@/store/portfolioStore';
import ReactECharts from 'echarts-for-react';
import IndexCards from '@/components/stock/IndexCards';

const DashboardPage: React.FC = () => {
  // Real Portfolio Data
  const { fetchPortfolios } = usePortfolioStore();

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

  // News Data (暂未使用)
  // const [newsList, setNewsList] = useState<News[]>([]);
  // const [newsLoading, setNewsLoading] = useState(true);
  // const [selectedNews, setSelectedNews] = useState<News | null>(null);

  // Daily Report Data
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [reportLoading, setReportLoading] = useState(true);

  useEffect(() => {
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

    fetchDailyReport();
  }, []);


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
      {/* 市场指数卡片 */}
      <IndexCards />

      {/* 第一行：Ruo情绪指数 & 每日简报 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ruo情绪指数 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 flex flex-col justify-between hover-lift lg:col-span-1 min-h-[300px]">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Ruo 情绪指数</h3>
            {!dashboardData ? (
              <div className="w-12 h-5 bg-muted animate-pulse rounded"></div>
            ) : (
              <span className="text-xs px-2 py-1 rounded bg-primary/20 text-primary border border-primary/20">{sentimentLabel}</span>
            )}
          </div>

          <div className="h-28 w-full flex items-center justify-center -mt-2">
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

        {/* 每日简报 */}
        <div className="bg-card text-card-foreground border rounded-xl shadow-sm p-6 hover-lift lg:col-span-2 flex flex-col justify-between min-h-[300px]">
          <div>
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
                <div className="text-sm text-muted-foreground leading-relaxed line-clamp-4 overflow-y-auto custom-scrollbar pr-1 max-h-[140px] whitespace-pre-line">
                  {dailyReport.report}
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">暂无简报数据</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;