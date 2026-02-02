import React from 'react';
import { StockNews } from '@/types';
import { formatRelativeTime } from '@/utils/format';

interface NewsCardProps {
  news: StockNews;
}

const NewsCard: React.FC<NewsCardProps> = ({ news }) => {
  const getSentimentColor = (score?: number) => {
    if (!score) return 'text-[var(--color-text-secondary)]';
    if (score > 0.6) return 'text-[var(--color-profit-up)]';
    if (score < 0.4) return 'text-[var(--color-loss-up)]';
    return 'text-[var(--color-warning)]';
  };

  const getSentimentPosition = (score?: number) => {
    if (!score) return 50;
    return score * 100;
  };

  return (
    <div className="card hover:shadow-md transition-all hover:shadow-[var(--color-ruo-purple)]/10">
      <div className="space-y-3">
        {/* Header - 来源和时间 */}
        <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>{news.source}</span>
          <span>{formatRelativeTime(news.publishTime)}</span>
        </div>

        {/* Body - AI 摘要 */}
        <div className="space-y-2">
          <p className="font-medium leading-tight">{news.aiSummary || news.title}</p>

          {/* 情感倾向条 */}
          {news.sentimentScore !== undefined && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-[var(--color-text-secondary)]">利空</span>
              <div className="flex-1 h-1 bg-[var(--color-surface-3)] rounded-full relative">
                <div
                  className="absolute top-1/2 transform -translate-y-1/2 w-3 h-3 bg-[var(--color-ruo-purple)] rounded-full -mt-1.5"
                  style={{ left: `${getSentimentPosition(news.sentimentScore)}%` }}
                ></div>
              </div>
              <span className="text-xs text-[var(--color-text-secondary)]">利好</span>
            </div>
          )}
        </div>

        {/* Footer - 关联股票 */}
        {news.stockSymbols && news.stockSymbols.length > 0 && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-[var(--color-text-secondary)]">关联股票:</span>
              {news.stockSymbols.map((symbol, idx) => (
                <span key={idx} className="text-xs text-[var(--color-ruo-purple)] cursor-pointer hover:underline">
                  {symbol}
                  {idx < news.stockSymbols!.length - 1 && ', '}
                </span>
              ))}
            </div>
            {/* 情感分数 */}
            {news.sentimentScore !== undefined && (
              <span className={`text-xs font-medium ${getSentimentColor(news.sentimentScore)}`}>
                {news.sentimentScore > 0.6 ? '📈' : news.sentimentScore < 0.4 ? '📉' : '➡️'}
                {Math.round(news.sentimentScore * 100)}%
              </span>
            )}
          </div>
        )}

        {/* 查看原文链接 */}
        {news.url && (
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[var(--color-ruo-purple)] hover:text-[var(--color-electric-cyan)] inline-flex items-center transition-colors"
          >
            查看原文 →
          </a>
        )}
      </div>
    </div>
  );
};

export default NewsCard;