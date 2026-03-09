import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePortfolioStore } from '@/store/portfolioStore';
import { getKLineData, getStockRealtime } from '@/api/stock';
import KLineChart from '@/components/chart/KLineChart';
import Loading from '@/components/common/Loading';
import Modal from '@/components/common/Modal'; // Import Modal
import { KLineData } from '@/types';
import clsx from 'clsx';

// type AILayer = 'support';

const ChartPage: React.FC = () => {
  const { portfolios } = usePortfolioStore();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedName, setSelectedName] = useState<string>('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'min'>('min');
  const [aiLayers, setAiLayers] = useState<{ support: boolean }>({
    support: false,
  });


  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [preClose, setPreClose] = useState<number>(0);
  const [isReportOpen, setIsReportOpen] = useState(true);

  const [searchParams] = useSearchParams();
  const urlSymbol = searchParams.get('symbol');

  // 获取股票名称
  const fetchStockName = async (symbol: string) => {
    try {
      const res = await getStockRealtime(symbol);
      setSelectedName(res.name);
    } catch (error) {
      console.error('获取股票名称失败:', error);
      setSelectedName(symbol);
    }
  };

  useEffect(() => {
    // Priority: URL Param > Current Selection > Default to First Portfolio
    if (urlSymbol && urlSymbol !== selectedSymbol) {
      const p = portfolios.find(p => p.symbol === urlSymbol);
      if (p) {
        setSelectedSymbol(p.symbol);
        setSelectedName(p.name);
      } else {
        // Even if not in portfolio (e.g. from external link), allow it if needed, or just set symbol
        setSelectedSymbol(urlSymbol);
        // Name might be missing, maybe fetch or default
        fetchStockName(urlSymbol);
      }
    } else if (portfolios.length > 0 && !selectedSymbol && !urlSymbol) {
      setSelectedSymbol(portfolios[0].symbol);
      setSelectedName(portfolios[0].name);
    }
  }, [portfolios, selectedSymbol, urlSymbol]);

  useEffect(() => {
    if (selectedSymbol) {
      if (period === 'min') {
        fetchTimeShareData(selectedSymbol);
      } else {
        fetchKLineData(selectedSymbol, period);
      }
    }

    // Auto-refresh for time-sharing (min) data every 30 seconds
    let intervalId: NodeJS.Timeout;
    if (selectedSymbol && period === 'min') {
      intervalId = setInterval(() => {
        const now = new Date();
        const hour = now.getHours();
        const minute = now.getMinutes();
        const timeVal = hour * 100 + minute;

        // Trading hours: 09:30 - 11:30, 13:00 - 15:00
        // Relaxed slightly to ensure we capture open/close ticks (e.g. 9:29 - 15:05)
        const isTrading = (timeVal >= 929 && timeVal <= 1135) || (timeVal >= 1259 && timeVal <= 1505);

        if (isTrading) {
          fetchTimeShareData(selectedSymbol, true); // Silent update
        }
      }, 5000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [selectedSymbol, period]);

  // Separate effect for AI Analysis - fetch only when symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      // Initial load: check for existing, but don't prompt re-analyze if found
      // Actually fetchAIAnalysis implementation logic:
      // if checkExisting=true, it shows modal if found.
      // We probably want to just load it if it exists, without showing modal initially.
      // But fetchAIAnalysis logic I wrote shows modal if found.
      // I should tweak fetchAIAnalysis to separate "Check and Load" vs "Check and Prompt".

      // Let's modify fetchAIAnalysis slightly in next step or use a separate loader?
      // Or just load it differently. 
      // For now, let's just calling it.
      // Wait, if I call fetchAIAnalysis(symbol), it defaults checkExisting=true -> prompts modal.
      // Users don't want a modal popped up just by switching stock if a report exists.
      // So I need a way to 'just load' without prompting.

      // I'll update fetchAIAnalysis to accept a 'silent' param for modal?
      // Let's do that in a separate edit or assume the previous tool call already defined it.
      // In the previous tool call, I defined: fetchAIAnalysis(symbol, checkExisting=true)
      // If checkExisting is true, it shows modal.

      // I should update useEffect to call a function that just loads.
      loadExistingAnalysis(selectedSymbol);
    }
  }, [selectedSymbol]);

  const loadExistingAnalysis = async (symbol: string) => {
    try {
      const { getAnalysisReport } = await import('@/api/analysis');
      const today = new Date().toISOString().split('T')[0];
      const res = await getAnalysisReport('kline_analysis', today, symbol);
      if (res && res.success && res.result) {
        const data = res.result.data || res.result;
        if (res.result.date) data.reportDate = res.result.date;
        setAiAnalysis(data);
      } else {
        setAiAnalysis(null);
      }
    } catch (e) { setAiAnalysis(null); }
  };

  const fetchTimeShareData = async (symbol: string, silent: boolean = false) => {
    if (!silent) setLoading(true);
    try {
      const { fetchIntradayData } = await import('@/api/stock');
      const { preClose, trends, name } = await fetchIntradayData(symbol);
      setKlineData(trends as any);
      setPreClose(preClose);
      if (name && name !== selectedName && name !== symbol) {
        setSelectedName(name);
      }
    } catch (error) {
      console.error('Fetch time share failed:', error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

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

  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showReanalyzeModal, setShowReanalyzeModal] = useState(false);

  const runAnalysis = async (symbol: string, forceRerun: boolean) => {
    setAnalysisLoading(true);
    setShowReanalyzeModal(false);
    setAiAnalysis(null);
    try {
      const { getAnalysisReport, runKlineAnalysis } = await import('@/api/analysis');
      const today = new Date().toISOString().split('T')[0];

      const runRes = await runKlineAnalysis(symbol, forceRerun);

      if (runRes && runRes.success) {
        let attempts = 0;
        const maxAttempts = 20;
        const pollInterval = setInterval(async () => {
          attempts++;
          try {
            const res = await getAnalysisReport('kline_analysis', today, symbol);
            if (res && res.success && res.result) {
              const data = res.result.data || res.result;
              if (res.result.date) {
                data.reportDate = res.result.date;
              }
              setAiAnalysis(data);
              clearInterval(pollInterval);
              setAnalysisLoading(false);
            }
          } catch (e) { }

          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            setAnalysisLoading(false);
          }
        }, 3000);
      } else {
        setAnalysisLoading(false);
      }
    } catch (e) {
      console.error(e);
      setAnalysisLoading(false);
    }
  };

  const fetchAIAnalysis = async (symbol: string, checkExisting: boolean = true) => {
    if (!symbol) return;

    if (checkExisting) {
      setAnalysisLoading(true);
      try {
        const { getAnalysisReport } = await import('@/api/analysis');
        const today = new Date().toISOString().split('T')[0];
        const res = await getAnalysisReport('kline_analysis', today, symbol);

        if (res && res.success && res.result) {
          const data = res.result.data || res.result;
          if (res.result.date) data.reportDate = res.result.date;
          setAiAnalysis(data);
          setAnalysisLoading(false);
          // Show modal to confirm re-analysis
          setShowReanalyzeModal(true);
          return;
        }
      } catch (e) {
        // Not found, continue to run
      }
    }

    // If not checking existing (or not found), run analysis
    runAnalysis(symbol, false);
  };



  const toggleSupport = () => {
    setAiLayers(prev => ({ ...prev, support: !prev.support }));
  };

  if (portfolios.length === 0 && !selectedSymbol) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted-foreground">请先添加持仓股票，或通过链接访问</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6 space-y-6 bg-background animate-fade-in">
      {/* 顶部控制栏 */}
      <div className="flex flex-col space-y-6">
        {/* 顶部标题栏：股票信息 + 价格信息 */}
        <div className="flex items-center justify-between">
          <div className="flex items-start gap-4">
            <div>
              <h1 className="text-3xl font-bold text-foreground tracking-tight">
                {selectedName}
              </h1>
              <div className="text-sm text-muted-foreground font-mono mt-1">
                {selectedSymbol}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-8">
            {/* 价格信息 */}
            <div className="text-right">
              {klineData.length > 0 && klineData[klineData.length - 1]?.close ? (
                <>
                  <div className="text-3xl font-bold text-foreground font-mono">
                    ¥{klineData[klineData.length - 1].close.toFixed(2)}
                  </div>
                  <div className={`text-sm font-medium mt-1 ${(klineData[klineData.length - 1].change ?? 0) >= 0 ? 'text-profit-up' : 'text-profit-down'}`}>
                    {(klineData[klineData.length - 1].change ?? 0) >= 0 ? '+' : ''}{(klineData[klineData.length - 1].change ?? 0).toFixed(2)} ({(klineData[klineData.length - 1].changePct ?? 0).toFixed(2)}%)
                  </div>
                </>
              ) : (
                <div className="text-3xl font-bold text-foreground font-mono">--</div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => fetchAIAnalysis(selectedSymbol)}
                disabled={analysisLoading}
                className={clsx(
                  "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-md",
                  analysisLoading
                    ? "bg-muted cursor-not-allowed text-muted-foreground"
                    : "bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-105 active:scale-95 shadow-primary/20"
                )}
              >
                {analysisLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    分析中...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    AI 深度分析
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 控制按钮组：周期选择 + 极值显示 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center bg-muted p-1 rounded-xl border border-border">
            {(['min', 'daily', 'weekly', 'monthly'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={clsx(
                  'px-6 py-2 rounded-lg text-sm font-bold transition-all duration-200',
                  period === p
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-card/50'
                )}
              >
                {p === 'min' ? '分时' : p === 'daily' ? '日K' : p === 'weekly' ? '周K' : '月K'}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground font-medium">最高:</span>
              <span className="text-foreground font-bold font-mono text-base">12.79</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground font-medium">最低:</span>
              <span className="text-foreground font-bold font-mono text-base">12.33</span>
            </div>
          </div>
        </div>
      </div>


      {/* K线图表区 */}
      <div className="flex-1 flex flex-col bg-card rounded-xl border border-border shadow-sm overflow-hidden hover-lift transition-all duration-300">
        {/* AI 图层开关 - 仅在非分时模式显示 */}
        {period !== 'min' && (
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-muted-foreground">AI 辅助:</span>
                  <label className="relative inline-flex items-center cursor-pointer group">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={aiLayers.support}
                      onChange={toggleSupport}
                    />
                    <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    <span className="ml-2 text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                      支撑/压力位
                    </span>
                  </label>
                </div>
              </div>

              {!aiAnalysis && selectedSymbol && (
                <span className="text-xs text-gray-500">(暂无AI分析数据, 仅显示模拟演示)</span>
              )}
            </div>
          </div>
        )}

        {/* 图表内容 */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <Loading text="加载K线数据中..." />
            </div>
          ) : klineData.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-muted-foreground">暂无K线数据</p>
            </div>
          ) : (
            <div className="h-full p-4">
              <div className="h-full p-4">
                <KLineChart
                  data={klineData}
                  symbol={selectedSymbol}
                  name={selectedName}
                  period={period}
                  preClose={preClose}
                  aiLayers={aiLayers}
                  aiAnalysis={aiAnalysis}
                />
              </div>
            </div>
          )}
        </div>

        {/* AI 图层说明（当有图层开启时显示） */}
        {period !== 'min' && Object.values(aiLayers).some(Boolean) && (
          <div className="p-4 border-t border-border bg-primary/5">
            <div className="text-sm text-muted-foreground space-y-2">
              <p className="font-medium text-primary mb-2 flex items-center gap-2">
                <span>🤖 AI 核心观点:</span>
                {aiAnalysis && <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">置信度: {aiAnalysis.confidence}</span>}
              </p>

              {aiLayers.support && (
                <div className="mb-2">
                  <p className="font-bold text-gray-300">📐 支撑/压力:</p>
                  {aiAnalysis?.support_resistance ? (
                    <p className="pl-4 text-gray-400">
                      {aiAnalysis.support_resistance.analysis} (支撑: <span className="text-purple-400">{aiAnalysis.support_resistance.support}</span>, 压力: <span className="text-orange-400">{aiAnalysis.support_resistance.resistance}</span>)
                    </p>
                  ) : (
                    <p className="pl-4 text-gray-500 italic">正在使用模拟算法计算近期高低点...</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* AI 分析报告模块 */}
      <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden transition-all duration-300 hover-lift mt-6">
        <button
          onClick={() => setIsReportOpen(!isReportOpen)}
          className="w-full flex items-center justify-between p-4 bg-card hover:bg-muted transition-colors border-b border-border"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold flex items-center gap-2">
              🧠 AI 深度分析报告
              {aiAnalysis && (
                <span className="flex items-center gap-2">
                  <span className={clsx(
                    "text-xs px-2 py-0.5 rounded",
                    aiAnalysis.recommendation === '买入' ? "bg-red-500/20 text-red-400" :
                      aiAnalysis.recommendation === '卖出' ? "bg-green-500/20 text-green-400" :
                        "bg-gray-500/20 text-gray-400"
                  )}>
                    {aiAnalysis.recommendation} (置信度: {aiAnalysis.confidence})
                  </span>
                  {aiAnalysis.reportDate && (
                    <span className="text-xs text-muted-foreground font-normal ml-2">
                      {aiAnalysis.reportDate}
                    </span>
                  )}
                </span>
              )}
            </span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="text-sm">{isReportOpen ? '收起' : '展开'}</span>
            <svg
              className={clsx("w-5 h-5 transition-transform duration-200", isReportOpen ? "rotate-180" : "")}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {/* 报告内容 */}
        {isReportOpen && (
          <div className="p-4 bg-background">
            {aiAnalysis ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 左侧：核心结论 */}
                <div className="space-y-4">
                  <div className="p-3 rounded-lg bg-card border border-border">
                    <h3 className="text-sm text-muted-foreground mb-1">行情摘要</h3>
                    <p className="text-foreground font-medium">{aiAnalysis.summary}</p>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-muted-foreground mb-2 uppercase tracking-wider">趋势分析</h3>
                    <p className="text-foreground mb-2">
                      <span className="text-purple-400 font-bold">{aiAnalysis.trend}</span>
                    </p>
                    <p className="text-sm text-gray-400">{aiAnalysis.technical_pattern}</p>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-muted-foreground mb-2 uppercase tracking-wider">关键点位</h3>
                    <div className="flex gap-4 mb-2">
                      <div className="flex-1 p-2 bg-red-500/10 border border-red-500/20 rounded text-center">
                        <div className="text-xs text-red-400">压力位</div>
                        <div className="text-lg font-bold text-red-500">{aiAnalysis.support_resistance?.resistance || '--'}</div>
                      </div>
                      <div className="flex-1 p-2 bg-green-500/10 border border-green-500/20 rounded text-center">
                        <div className="text-xs text-green-400">支撑位</div>
                        <div className="text-lg font-bold text-green-500">{aiAnalysis.support_resistance?.support || '--'}</div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 bg-card p-2 rounded">{aiAnalysis.support_resistance?.analysis}</p>
                  </div>
                </div>

                {/* 右侧：信号与建议 */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-muted-foreground mb-2 uppercase tracking-wider">关键信号</h3>
                    {aiAnalysis.signals && aiAnalysis.signals.length > 0 ? (
                      <ul className="space-y-2">
                        {aiAnalysis.signals.map((signal: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                            <span className="text-purple-500 mt-0.5">•</span>
                            <span>{signal}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500 italic">无明显信号</p>
                    )}
                  </div>

                  <div className="p-4 rounded-lg bg-gradient-to-br from-[var(--color-surface-2)] to-[var(--color-surface-3)] border border-border">
                    <h3 className="text-sm font-bold text-muted-foreground mb-2">💡 操作建议</h3>
                    <p className="text-foreground leading-relaxed">
                      {aiAnalysis.suggestion}
                    </p>
                  </div>

                  <div className="text-xs text-gray-600 text-right mt-4">
                    * AI分析基于历史数据，仅供参考，不构成投资建议
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <svg className="w-12 h-12 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                <p>点击上方 "AI 深度分析" 按钮生成报告</p>
              </div>
            )}
          </div>
        )}
      </div>
      {/* Re-analyze Confirmation Modal */}
      <Modal
        isOpen={showReanalyzeModal}
        onClose={() => setShowReanalyzeModal(false)}
        title="确认重新分析?"
        footer={
          <>
            <button
              onClick={() => setShowReanalyzeModal(false)}
              className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              取消
            </button>
            <button
              onClick={() => runAnalysis(selectedSymbol, true)}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-white hover:bg-purple-700 transition-colors shadow-lg shadow-purple-900/20"
            >
              确认重新分析
            </button>
          </>
        }
      >
        <p>检测到今日已有 AI 分析报告，是否强制重新生成？</p>
        <p className="text-sm text-gray-500 mt-2">重新分析大约需要 1-2 分钟。</p>
      </Modal>
    </div>
  );
};

export default ChartPage;