import React, { useEffect, useState } from 'react';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getKLineData } from '@/api/stock';
import KLineChart from '@/components/chart/KLineChart';
import Loading from '@/components/common/Loading';
import { KLineData } from '@/types';
import clsx from 'clsx';

type AILayer = 'support' | 'pattern' | 'signal';

const ChartPage: React.FC = () => {
  const { portfolios } = usePortfolioStore();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedName, setSelectedName] = useState<string>('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [aiLayers, setAiLayers] = useState<Record<AILayer, boolean>>({
    support: false,
    pattern: false,
    signal: false,
  });
  const [usMarket, setUsMarket] = useState(false);

  useEffect(() => {
    // 默认选择第一个持仓
    if (portfolios.length > 0 && !selectedSymbol) {
      setSelectedSymbol(portfolios[0].symbol);
      setSelectedName(portfolios[0].name);
    }
  }, [portfolios, selectedSymbol]);

  useEffect(() => {
    if (selectedSymbol) {
      fetchKLineData(selectedSymbol, period);
    }
  }, [selectedSymbol, period]);

  const fetchKLineData = async (symbol: string, period: 'daily' | 'weekly' | 'monthly') => {
    setLoading(true);
    try {
      const data = await getKLineData(symbol, period, 120);
      setKlineData(data);
    } catch (error) {
      console.error('获取K线数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectStock = (symbol: string, name: string) => {
    setSelectedSymbol(symbol);
    setSelectedName(name);
  };

  const toggleAILayer = (layer: AILayer) => {
    setAiLayers(prev => ({
      ...prev,
      [layer]: !prev[layer],
    }));
  };

  if (portfolios.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-[var(--color-text-secondary)]">请先添加持仓股票</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      {/* 顶部控制栏 */}
      <div className="flex flex-col space-y-4">
        {/* 股票选择器 */}
        <div>
          <h2 className="text-xl font-bold mb-4">K 线实验室</h2>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {portfolios.map((portfolio) => (
              <button
                key={portfolio.symbol}
                onClick={() => handleSelectStock(portfolio.symbol, portfolio.name)}
                className={clsx(
                  'px-4 py-2 rounded-lg whitespace-nowrap transition-colors',
                  selectedSymbol === portfolio.symbol
                    ? 'bg-[var(--color-ruo-purple)]/20 text-[var(--color-ruo-purple)] border border-[var(--color-ruo-purple)]/30'
                    : 'bg-[var(--color-surface-3)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-3)]/80'
                )}
              >
                {portfolio.name}
              </button>
            ))}
          </div>
        </div>

        {/* 控制按钮组 */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* 周期选择 */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-[var(--color-text-secondary)]">周期:</span>
            <div className="flex space-x-1">
              {(['daily', 'weekly', 'monthly'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    period === p
                      ? 'bg-[var(--color-ruo-purple)] text-white'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-3)]'
                  )}
                >
                  {p === 'daily' ? '日K' : p === 'weekly' ? '周K' : '月K'}
                </button>
              ))}
            </div>
          </div>

          {/* 市场模式切换 */}
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
      </div>

      {/* K线图表区 */}
      <div className="flex-1 flex flex-col card overflow-hidden">
        {/* AI 图层开关 */}
        <div className="p-4 border-b border-[var(--color-surface-3)]">
          <div className="flex items-center space-x-2 flex-wrap gap-2">
            <span className="text-sm text-[var(--color-text-secondary)]">AI 图层:</span>
            <div className="flex space-x-1">
              {[
                { key: 'support' as AILayer, label: '识别支撑位', icon: '📏' },
                { key: 'pattern' as AILayer, label: '识别形态', icon: '📐' },
                { key: 'signal' as AILayer, label: '买卖点提示', icon: '💡' },
              ].map((layer) => (
                <button
                  key={layer.key}
                  onClick={() => toggleAILayer(layer.key)}
                  className={clsx(
                    'px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center space-x-1',
                    aiLayers[layer.key]
                      ? 'bg-[var(--color-ruo-purple)]/20 text-[var(--color-ruo-purple)] border border-[var(--color-ruo-purple)]/30'
                      : 'bg-[var(--color-surface-3)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-3)]/80'
                  )}
                >
                  <span>{layer.icon}</span>
                  <span>{layer.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 图表内容 */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <Loading text="加载K线数据中..." />
            </div>
          ) : klineData.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-[var(--color-text-secondary)]">暂无K线数据</p>
            </div>
          ) : (
            <div className="h-full p-4">
              <KLineChart data={klineData} symbol={selectedSymbol} name={selectedName} aiLayers={aiLayers} />
            </div>
          )}
        </div>

        {/* AI 图层说明（当有图层开启时显示） */}
        {Object.values(aiLayers).some(Boolean) && (
          <div className="p-4 border-t border-[var(--color-surface-3)] bg-[var(--color-ruo-purple)]/5">
            <div className="text-sm text-[var(--color-text-secondary)] space-y-1">
              <p className="font-medium text-[var(--color-ruo-purple)] mb-2">AI 分析说明:</p>
              {aiLayers.support && (
                <p>• <span className="text-[var(--color-ruo-purple)]">支撑位识别:</span> 紫色虚线标注关键支撑位，价格在此处可能反弹</p>
              )}
              {aiLayers.pattern && (
                <p>• <span className="text-[var(--color-ruo-purple)]">形态识别:</span> 自动识别常见K线形态，预示未来走势</p>
              )}
              {aiLayers.signal && (
                <p>• <span className="text-[var(--color-ruo-purple)]">买卖点提示:</span> 箭头标注技术性买卖信号，仅供参考</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartPage;