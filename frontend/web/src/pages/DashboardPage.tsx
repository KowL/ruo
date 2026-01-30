import React, { useState } from 'react';
import clsx from 'clsx';
import PortfolioCard from '../components/portfolio/PortfolioCard';
import NewsCard from '../components/news/NewsCard';

const DashboardPage: React.FC = () => {
  const [usMarket, setUsMarket] = useState(false);

  // 模拟数据
  const assetData = {
    totalAssets: 125800.50,
    todayPnL: 2350.80,
    todayPnLPercent: 1.90,
    sentiment: '恐惧',
    sentimentScore: 0.3,
  };

  const portfolioMovements = [
    { code: 'AAPL', name: '苹果', changePercent: 3.5, price: 182.52 },
    { code: 'TSLA', name: '特斯拉', changePercent: -2.8, price: 245.18 },
    { code: 'NVDA', name: '英伟达', changePercent: 4.2, price: 485.30 },
  ];

  const aiNews = [
    {
      id: 1,
      source: '财经头条',
      time: '10分钟前',
      summary: '央行降准释放流动性，市场预期宽松',
      sentiment: 0.8,
      relatedStocks: ['000001', '600036'],
    },
    {
      id: 2,
      source: '华尔街日报',
      time: '25分钟前',
      summary: '美联储暗示维持利率不变',
      sentiment: 0.2,
      relatedStocks: ['AAPL', 'MSFT'],
    },
    {
      id: 3,
      source: '证券时报',
      time: '1小时前',
      summary: '科技巨头财报超预期',
      sentiment: 0.9,
      relatedStocks: ['AAPL', 'GOOGL', 'AMZN'],
    },
  ];

  const riskAlerts = [
    { type: 'warning', message: '新能源行业仓位过重，建议适度减持' },
    { type: 'info', message: '现金比例偏低，建议保留10%应急资金' },
  ];

  const getProfitColor = (percent: number) => {
    return usMarket
      ? (percent >= 0 ? 'text-[var(--color-profit-down)]' : 'text-[var(--color-loss-down)]')
      : (percent >= 0 ? 'text-[var(--color-profit-up)]' : 'text-[var(--color-loss-up)]');
  };

  const getProfitBgColor = (percent: number) => {
    return usMarket
      ? (percent >= 0 ? 'bg-[var(--color-profit-down)]/20' : 'bg-[var(--color-loss-down)]/20')
      : (percent >= 0 ? 'bg-[var(--color-profit-up)]/20' : 'bg-[var(--color-loss-up)]/20');
  };

  return (
    <div className="p-6 space-y-6">
      {/* 第一行：资产全景 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 总资产卡片 */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">资产全景</h2>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-[var(--color-text-secondary)]">市场模式:</span>
              <button
                onClick={() => setUsMarket(!usMarket)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${usMarket ? 'bg-[var(--color-profit-down)]/20 text-[var(--color-profit-down)]' : 'bg-[var(--color-profit-up)]/20 text-[var(--color-profit-up)]'}`}
              >
                {usMarket ? '美股' : 'A股'}
              </button>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-baseline space-x-4">
              <span className="text-3xl font-bold numbers">¥{assetData.totalAssets.toLocaleString()}</span>
              <span className={clsx('text-lg font-semibold flex items-center space-x-1', getProfitColor(assetData.todayPnLPercent))}>
                {assetData.todayPnLPercent >= 0 && <span>↑</span>}
                {assetData.todayPnLPercent < 0 && <span>↓</span>}
                <span>+¥{assetData.todayPnL.toLocaleString()} ({assetData.todayPnLPercent}%)</span>
              </span>
            </div>
            <div className="text-[var(--color-text-secondary)] text-sm">
              更新时间: 14:30:25
            </div>
          </div>
        </div>

        {/* Ruo情绪指数 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Ruo 情绪指数</h3>
          <div className="relative h-32 flex flex-col items-center justify-center">
            {/* 半圆仪表盘 */}
            <div className="absolute inset-0 flex items-end justify-center">
              <div className="w-48 h-24 rounded-t-full border-b-4 border-[var(--color-surface-3)]"></div>
            </div>
            {/* 指针 */}
            <div
              className="absolute w-1 h-32 bg-[var(--color-ruo-purple)] rounded-full transform origin-bottom transition-transform duration-500"
              style={{ transform: `rotate(${assetData.sentimentScore * 180 - 90}deg)` }}
            ></div>
            <div className="relative z-10 text-center">
              <div className="text-2xl font-bold text-[var(--color-ruo-purple)]">{assetData.sentiment}</div>
              <div className="text-sm text-[var(--color-text-secondary)] mt-1">
                今日市场情绪分歧较大，建议观望
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 第二行：核心动态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 持仓异动卡片 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">持仓异动</h3>
          <div className="space-y-3">
            {portfolioMovements.map((stock, index) => (
              <div
                key={index}
                className={clsx(
                  'p-3 rounded-lg transition-all hover:bg-[var(--color-surface-3)]',
                  getProfitBgColor(stock.changePercent)
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{stock.code}</div>
                    <div className="text-sm text-[var(--color-text-secondary)]">{stock.name}</div>
                  </div>
                  <div className={clsx('text-right', getProfitColor(stock.changePercent))}>
                    <div className="text-lg font-semibold numbers">{stock.changePercent}%</div>
                    <div className="text-sm">{stock.price}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI必读 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">AI 必读</h3>
          <div className="space-y-4">
            {aiNews.map((news) => (
              <div key={news.id} className="p-3 rounded-lg hover:bg-[var(--color-surface-3)] transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div className="text-sm text-[var(--color-text-secondary)]">
                    {news.source} · {news.time}
                  </div>
                </div>
                <div className="font-medium mb-2">{news.summary}</div>
                {/* 情感倾向条 */}
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-[var(--color-text-secondary)]">利空</span>
                  <div className="flex-1 h-1 bg-[var(--color-surface-3)] rounded-full relative">
                    <div
                      className="absolute top-1/2 transform -translate-y-1/2 w-3 h-3 bg-[var(--color-ruo-purple)] rounded-full -mt-1.5"
                      style={{ left: `${news.sentiment * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-[var(--color-text-secondary)]">利好</span>
                </div>
                <div className="flex items-center space-x-2 mt-2">
                  <span className="text-xs text-[var(--color-text-secondary)]">关联股票:</span>
                  {news.relatedStocks.map((stock, idx) => (
                    <span key={idx} className="text-xs text-[var(--color-ruo-purple)] cursor-pointer hover:underline">
                      {stock}
                      {idx < news.relatedStocks.length - 1 && ', '}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 第三行：风险雷达 */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">风险雷达</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {riskAlerts.map((alert, index) => (
            <div
              key={index}
              className={clsx(
                'p-4 rounded-lg border-l-4',
                alert.type === 'warning'
                  ? 'bg-[var(--color-warning)]/10 border-[var(--color-warning)]'
                  : 'bg-[var(--color-surface-3)] border-[var(--color-ruo-purple)]'
              )}
            >
              <div className="flex items-start space-x-3">
                <span className={clsx(
                  'text-xl',
                  alert.type === 'warning' ? 'text-[var(--color-warning)]' : 'text-[var(--color-ruo-purple)]'
                )}>
                  {alert.type === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <p className="text-sm">{alert.message}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;