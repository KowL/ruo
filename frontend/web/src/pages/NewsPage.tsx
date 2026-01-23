import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getStockNews } from '@/api/news';
import NewsCard from '@/components/news/NewsCard';
import Loading from '@/components/common/Loading';
import { StockNews } from '@/types';

const NewsPage: React.FC = () => {
  const { portfolios } = usePortfolioStore();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [news, setNews] = useState<StockNews[]>([]);
  const [loading, setLoading] = useState(false);

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
        <h2 className="text-xl font-bold mb-4">新闻情报</h2>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {portfolios.map((portfolio) => (
            <button
              key={portfolio.symbol}
              onClick={() => setSelectedSymbol(portfolio.symbol)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                selectedSymbol === portfolio.symbol
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {portfolio.name}
              {portfolio.has_new_news && (
                <span className="ml-1 inline-flex h-2 w-2 rounded-full bg-red-500"></span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 新闻列表 */}
      {loading ? (
        <Loading text="加载新闻中..." />
      ) : news.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">暂无新闻</p>
        </div>
      ) : (
        <div className="space-y-4">
          {news.map((item) => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export default NewsPage;
