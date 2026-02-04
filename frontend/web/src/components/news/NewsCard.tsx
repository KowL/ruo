import React from 'react';
import { News } from '@/types';
import { formatRelativeTime } from '@/utils/format';

interface NewsCardProps {
  news: News;
}

const NewsCard: React.FC<NewsCardProps> = ({ news }) => {
  const getSourceName = (source: string) => {
    switch (source) {
      case 'cls': return '财联社';
      case 'xueqiu': return '雪球';
      default: return source;
    }
  };

  return (
    <div className="card hover:shadow-md transition-all hover:shadow-[var(--color-ruo-purple)]/10">
      <div className="space-y-3">
        {/* Header - 来源和时间 */}
        <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>{getSourceName(news.source)}</span>
          <span>{formatRelativeTime(news.publishTime)}</span>
        </div>

        {/* Body - 内容 */}
        <div className="space-y-2">
          {news.title && <p className="font-medium leading-tight">{news.title}</p>}
          <p className="text-sm text-[var(--color-text-secondary)]">{news.content}</p>

          {/* AI 分析 */}
          {news.aiAnalysis && (
            <p className="text-sm text-[var(--color-ruo-purple)] bg-[var(--color-ruo-purple)]/5 p-2 rounded">
              {news.aiAnalysis}
            </p>
          )}
        </div>

        {/* Footer - 关联股票 */}
        {news.relationStocks && news.relationStocks.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-[var(--color-text-secondary)]">关联股票:</span>
            {news.relationStocks.map((symbol, idx) => (
              <span key={idx} className="text-xs text-[var(--color-ruo-purple)] cursor-pointer hover:underline">
                {symbol}
                {news.relationStocks && idx < news.relationStocks.length - 1 && ', '}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsCard;
