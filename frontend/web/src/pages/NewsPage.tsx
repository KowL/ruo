import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getStockNews } from '@/api/news';
import NewsCard from '@/components/news/NewsCard';
import Loading from '@/components/common/Loading';
import { News } from '@/types';
import clsx from 'clsx';

type NewsFilter = 'all' | 'favorites' | 'positive' | 'negative';

const NewsPage: React.FC = () => {
  const { portfolios } = usePortfolioStore();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<NewsFilter>('all');
  const [usMarket, setUsMarket] = useState(false);

  useEffect(() => {
    // 默认选择第一个持仓
    if (portfolios.length > 0 && !selectedSymbol) {
      setSelectedSymbol(portfolios[0].symbol);
    }
  }, [portfolios, selectedSymbol]);

  useEffect(() => {
    if (selectedSymbol) {
      fetchNews(selectedSymbol);
    }
  }, [selectedSymbol]);

  const fetchNews = async (symbol: string) => {
    setLoading(true);
    try {
      const data = await getStockNews(symbol, 20, 24);
      setNews(data);
    } catch (error) {
      console.error('获取新闻失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 过滤新闻
  const filteredNews = news.filter(item => {
    switch (filter) {
      case 'positive':
        return (item.sentimentScore ?? 0) > 0.6;
      case 'negative':
        return (item.sentimentScore ?? 0) < 0.4;
      case 'favorites':
        return item.isFavorite || portfolios.some(p => p.symbol === item.symbol);
      default:
        return true;
    }
  });

  if (portfolios.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-[var(--color-text-secondary)]">请先添加持仓股票</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 过滤栏 */}
      <div className="card mb-6">
        <div className="flex flex-col space-y-4">
          {/* 股票选择器 */}
          <div>
            <h2 className="text-xl font-bold mb-4">AI 情报分析</h2>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {portfolios.map((portfolio) => (
                <button
                  key={portfolio.symbol}
                  onClick={() => setSelectedSymbol(portfolio.symbol)}
                  className={clsx(
                    'px-4 py-2 rounded-lg whitespace-nowrap transition-colors',
                    selectedSymbol === portfolio.symbol
                      ? 'bg-[var(--color-ruo-purple)]/20 text-[var(--color-ruo-purple)] border border-[var(--color-ruo-purple)]/30'
                      : 'bg-[var(--color-surface-3)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-3)]/80'
                  )}
                >
                  {portfolio.name}
                  {portfolio.hasNewNews && (
                    <span className="ml-1 inline-flex h-2 w-2 rounded-full bg-[var(--color-ruo-purple)]"></span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Tab 过滤器 */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-[var(--color-text-secondary)]">筛选:</span>
            <div className="flex space-x-1">
              {[
                { key: 'all', label: '全部' },
                { key: 'favorites', label: '只看自选' },
                { key: 'positive', label: '只看利好' },
                { key: 'negative', label: '只看利空' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key as NewsFilter)}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    filter === tab.key
                      ? 'bg-[var(--color-ruo-purple)] text-white'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-3)]'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="flex items-center space-x-2 ml-auto">
              <span className="text-sm text-[var(--color-text-secondary)]">市场模式:</span>
              <button
                onClick={() => setUsMarket(!usMarket)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${usMarket ? 'bg-[var(--color-profit-down)]/20 text-[var(--color-profit-down)]' : 'bg-[var(--color-profit-up)]/20 text-[var(--color-profit-up)]'}`}
              >
                {usMarket ? '美股' : 'A股'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 瀑布流新闻列表 */}
      <div className="flex-1 overflow-y-auto p-1">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <Loading text="加载新闻中..." />
          </div>
        ) : filteredNews.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-[var(--color-text-secondary)]">暂无符合条件的新闻</p>
          </div>
        ) : (
          <div className="columns-1 md:columns-2 lg:columns-3 gap-4">
            {filteredNews.map((item) => (
              <div key={item.id} className="mb-4 break-inside-avoid">
                <NewsCard news={item} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsPage;