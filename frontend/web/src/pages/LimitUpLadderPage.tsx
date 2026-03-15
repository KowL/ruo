/**
 * 连板天梯页面 - 参考 quicktiny.cn 样式优化
 * Limit Up Ladder Page
 */
import React, { useEffect, useState, useMemo } from 'react';
import { getLimitUpLadder } from '@/api/limitUpLadder';
import { ChevronDown, ChevronUp, Flame } from 'lucide-react';
import { StockCalendar } from '@/components/StockCalendar';

const LimitUpLadderPage: React.FC = () => {
  const [levels, setLevels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [firstBoardExpanded, setFirstBoardExpanded] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // 计算最近一个交易日（跳过周末）
    const today = new Date();
    const day = today.getDay();
    let defaultDate = today;

    // 周日(0) -> 上周五, 周六(6) -> 上周五, 周一到周五 -> 今天
    if (day === 0) { // 周日
      defaultDate = new Date(today.setDate(today.getDate() - 2)); // 上周五
    } else if (day === 6) { // 周六
      defaultDate = new Date(today.setDate(today.getDate() - 1)); // 上周五
    }

    return defaultDate.toISOString().split('T')[0];
  });

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await getLimitUpLadder(1, 200, selectedDate);

      if (res.success && res.data && res.data.levels) {
        setLevels(res.data.levels);
      } else {
        setError('获取数据失败');
      }
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 提取所有题材并统计
  const themeStats = useMemo(() => {
    const stats: Record<string, number> = {};
    levels.forEach((level) => {
      level.stocks?.forEach((stock: any) => {
        const theme = stock.industry || stock.reason || '其他';
        stats[theme] = (stats[theme] || 0) + 1;
      });
    });
    return Object.entries(stats)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20);
  }, [levels]);

  // 分离首板和其他连板
  const { firstBoard, otherLevels } = useMemo(() => {
    const first = levels.find((l) => l.level === 1);
    const others = levels.filter((l) => l.level >= 2).sort((a, b) => b.level - a.level);
    return { firstBoard: first, otherLevels: others };
  }, [levels]);

  // 根据选中题材过滤股票
  const filterByTheme = (stocks: any[]) => {
    if (!selectedTheme) return stocks;
    return stocks.filter(
      (s) => s.industry === selectedTheme || s.reason === selectedTheme
    );;
  };

  const formatTime = (time: string) => {
    if (!time) return '--';
    if (time.length === 6) {
      return `${time.slice(0, 2)}:${time.slice(2, 4)}`;
    }
    return time;
  };

  // 获取涨停类型标签
  const getLimitType = (stock: any) => {
    // 优先判断一字板
    if (stock.open_count === 0 && stock.first_time?.startsWith('09:25')) {
      return { text: '一字', bg: 'bg-[#5B3921]' }; // 深褐色
    }
    // 判断 T 字板
    if (stock.open_count === 0) {
      return { text: 'T字', bg: 'bg-[#F97316]' }; // 橙色
    }
    // 判断 融 (成交量或特定标记)
    if (stock.seal_amount > 100000000 || stock.is_margin) {
      return { text: '融', bg: 'bg-[#EF4444]' }; // 红色
    }
    return null;
  };

  // 获取层级标识颜色
  const getLevelColor = (level: number) => {
    const colors: Record<number, string> = {
      5: 'bg-[#EF4444]',
      4: 'bg-[#EF4444]',
      3: 'bg-[#EF4444]',
      2: 'bg-[#EF4444]',
      1: 'bg-[#94A3B8]',
    };
    return colors[level] || 'bg-[#EF4444]';
  };

  // 渲染股票卡片
  const renderStockCard = (stock: any) => {
    const limitType = getLimitType(stock);

    // 根据行业或题材获取颜色（模拟多色条）
    const borderColors = ['border-b-[#A855F7]', 'border-b-[#3B82F6]', 'border-b-[#EF4444]', 'border-b-[#F97316]', 'border-b-[#10B981]'];
    const borderColor = borderColors[Math.abs(stock.name.length + (stock.industry?.length || 0)) % borderColors.length];

    return (
      <div
        key={stock.code}
        className={`group relative flex flex-col p-2.5
                   bg-white hover:bg-slate-50
                   rounded-xl border border-slate-100 shadow-md
                   transition-all duration-200 cursor-pointer
                   w-[154px] h-[104px] ${borderColor} border-b-[3px]`}
      >
        {/* 第一行：状态标签 + 时间 */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1">
            {limitType && (
              <span className={`px-1 py-0.5 text-[10px] font-bold text-white rounded-sm ${limitType.bg}`}>
                {limitType.text}
              </span>
            )}
            {/* 始终显示一个占位或者额外标签，如参考图所示 */}
            {stock.is_margin && !limitType?.text.includes('融') && (
               <span className="px-1 py-0.5 text-[10px] font-bold text-white rounded-sm bg-[#EF4444]">
                融
               </span>
            )}
          </div>
          <span className="text-[10px] text-slate-400 font-medium">
            {formatTime(stock.first_time || stock.limit_time)}
          </span>
        </div>

        {/* 股票名称 - 居中且加粗 */}
        <div className="flex-1 flex items-center justify-center">
          <div className="font-bold text-slate-800 text-[16px] tracking-tight text-center truncate w-full">
            {stock.name}
          </div>
        </div>

        {/* 题材标签 - 底部居中，背景淡色 */}
        <div className="flex justify-center mt-1">
          <span className="px-2 py-0.5 text-[10px] font-semibold text-blue-500 bg-blue-50 rounded-md">
            {stock.industry || stock.reason || '其他'}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-500
                            flex items-center justify-center shadow-lg shadow-orange-200">
              <Flame className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">连板天梯</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <StockCalendar
          value={selectedDate}
          onChange={setSelectedDate}
          className="shadow-sm"
          align="right"
        />  </div>
        </div>

        {/* 题材标签横向滚动 */}
        {themeStats.length > 0 && (
          <div className="px-6 pb-4">
            <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide py-1">
              <button
                onClick={() => setSelectedTheme(null)}
                className={`shrink-0 px-5 py-2 rounded-full text-sm font-bold transition-all
                  ${!selectedTheme
                    ? 'bg-orange-500 text-white shadow-lg shadow-orange-200'
                    : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
              >
                全部
              </button>
              {themeStats.map(([theme, count]) => (
                <button
                  key={theme}
                  onClick={() => setSelectedTheme(theme === selectedTheme ? null : theme)}
                  className={`shrink-0 px-5 py-2 rounded-full text-sm font-bold transition-all
                    ${selectedTheme === theme
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-200'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                >
                  {theme} <span className="ml-1 opacity-60 text-xs font-medium">{count}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 主内容区 */}
      <div className="p-6 max-w-[1400px] mx-auto">
        {/* 加载状态 */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="w-12 h-12 border-4 border-slate-100 border-t-orange-500 rounded-full animate-spin mb-4" />
            <p className="text-sm font-medium text-slate-400">正在分析连板数据...</p>
          </div>
        )}

        {/* 连板天梯 */}
        {!loading && !error && (
          <div className="relative">
            {/* 时间轴背景虚线 */}
            <div className="absolute left-6 top-8 bottom-0 w-[1.5px] border-l border-dashed border-slate-200 z-0" />

            <div className="space-y-12 relative z-10">
              {/* 2连板及以上 */}
              {otherLevels.map((level) => {
                const filteredStocks = filterByTheme(level.stocks || []);
                if (filteredStocks.length === 0) return null;

                return (
                  <div key={level.level} className="flex gap-8 group">
                    {/* 左侧层级标识 */}
                    <div className="shrink-0 relative">
                      <div className={`w-12 h-12 rounded-lg ${getLevelColor(level.level)}
                                      flex items-center justify-center text-white
                                      font-black text-2xl shadow-lg ring-4 ring-white`}>
                        {level.level}
                      </div>
                    </div>

                    {/* 股票卡片网格 */}
                    <div className="flex-1 pb-4">
                      <div className="flex flex-wrap gap-4">
                        {filteredStocks.map((stock: any) =>
                          renderStockCard(stock)
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* 首板展示 */}
              {firstBoard && (
                <div className="flex gap-8 group">
                  <div className="shrink-0 relative">
                    <div className={`w-12 h-12 rounded-lg ${getLevelColor(1)}
                                    flex items-center justify-center text-white
                                    font-black text-2xl shadow-md ring-4 ring-white`}>
                      1
                    </div>
                  </div>
                  <div className="flex-1">
                    <button
                      onClick={() => setFirstBoardExpanded(!firstBoardExpanded)}
                      className="mb-4 flex items-center gap-2 px-4 py-2 bg-white rounded-full
                                 shadow-sm border border-slate-100 hover:border-orange-200
                                 transition-all text-slate-600 font-bold text-sm"
                    >
                      {firstBoardExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      首板涨停 ({firstBoard.count})
                    </button>

                    {firstBoardExpanded && (
                      <div className="flex flex-wrap gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
                        {(filterByTheme(firstBoard.stocks || []) || []).map((stock: any) =>
                          renderStockCard(stock)
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {!loading && otherLevels.length === 0 && (!firstBoard || (firstBoard && firstBoard.stocks?.length === 0)) && (
          <div className="text-center py-32 bg-white rounded-3xl border border-dashed border-slate-200">
            <div className="text-4xl mb-4">🌙</div>
            <div className="text-lg font-bold text-slate-800 mb-1">暂无强势连板</div>
            <div className="text-sm text-slate-400">当前市场可能处于低迷期或尚未开盘</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LimitUpLadderPage;
