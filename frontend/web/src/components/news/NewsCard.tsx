import React from 'react';
import Card from '../common/Card';
import { StockNews } from '@/types';
import { formatRelativeTime } from '@/utils/format';
import clsx from 'clsx';

interface NewsCardProps {
  news: StockNews;
}

const NewsCard: React.FC<NewsCardProps> = ({ news }) => {
  const getSentimentColor = (label?: string) => {
    switch (label) {
      case '利好':
        return 'text-red-600 bg-red-50';
      case '利空':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getSentimentStars = (score?: number) => {
    if (!score) return '';
    return '★'.repeat(Math.round(score));
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* 标题和情感标签 */}
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base font-semibold text-gray-900 flex-1">{news.title}</h3>
          {news.sentiment_label && (
            <span
              className={clsx(
                'px-2 py-1 text-xs font-medium rounded whitespace-nowrap',
                getSentimentColor(news.sentiment_label)
              )}
            >
              {news.sentiment_label} {getSentimentStars(news.sentiment_score)}
            </span>
          )}
        </div>

        {/* AI 摘要 */}
        {news.ai_summary && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
            <p className="text-xs text-blue-800 font-medium mb-1">🤖 AI 分析</p>
            <p className="text-sm text-gray-700">{news.ai_summary}</p>
          </div>
        )}

        {/* 来源和时间 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{news.source}</span>
          <span>{formatRelativeTime(news.publish_time)}</span>
        </div>

        {/* 查看原文链接 */}
        {news.url && (
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center"
          >
            查看原文 →
          </a>
        )}
      </div>
    </Card>
  );
};

export default NewsCard;
