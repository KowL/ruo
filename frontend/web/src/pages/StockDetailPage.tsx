import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const StockDetailPage: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();

  // 根据纯数字代码识别板块
  const getMarketPrefix = (code: string): string => {
    const firstDigit = code.charAt(0);
    switch (firstDigit) {
      case '6':
        return 'sh'; // 上海证券交易所
      case '0':
      case '3':
        return 'sz'; // 深圳证券交易所
      case '8':
      case '4':
        return 'bj'; // 北交所
      default:
        return 'sz'; // 默认深圳
    }
  };

  // 构建东方财富 URL
  const eastmoneyUrl = useMemo(() => {
    if (!symbol) return '';

    let code = symbol;

    const market = getMarketPrefix(code);

    return `https://quote.eastmoney.com/basic/h5chart-iframe.html?code=${code}&market=${market}`;
  }, [symbol]);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* 顶部工具栏 */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-[var(--color-surface-3)]">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-[var(--color-surface-3)] rounded-lg transition-colors"
          aria-label="返回"
        >
          <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex-1">
          <span className="text-sm font-medium text-[var(--color-text-primary)]">{symbol}</span>
        </div>

        <a
          href={eastmoneyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-[var(--color-ruo-purple)] hover:text-[var(--color-ruo-purple)]/80 transition-colors flex items-center gap-1"
        >
          在新标签页打开
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>

      {/* iframe 内容区域 */}
      <div className="flex-1 overflow-hidden">
        <iframe
          src={eastmoneyUrl}
          className="w-full h-full border-0"
          title="东方财富股票详情"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
        />
      </div>
    </div>
  );
};

export default StockDetailPage;
