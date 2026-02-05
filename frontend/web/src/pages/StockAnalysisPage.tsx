import React, { useState } from 'react';
import { runLimitUpAnalysis, getAnalysisReport } from '@/api/analysis';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';

const StockAnalysisPage: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');
    const [reportContent, setReportContent] = useState('');
    const [selectedDate, setSelectedDate] = useState(() => {
        // 默认获取今天日期字符串 YYYY-MM-DD
        return new Date().toISOString().split('T')[0];
    });
    const [isPolling, setIsPolling] = useState(false);

    // 当日期改变时，优先尝试获取已有的报告
    React.useEffect(() => {
        const fetchInitialReport = async () => {
            setLoading(true);
            setError('');
            try {
                // 1. 优先尝试从数据库直接 GET 报告
                const res = await getAnalysisReport('limit-up', selectedDate);
                if (res && res.success && res.result) {
                    setResult(res.result.data || res.result);
                    setReportContent(res.result.markdown || '');
                } else {
                    // 2. 如果没找到，则显示提示或让用户手动触发
                    setResult(null);
                    setReportContent('');
                    setError(res?.message || '该日期暂无复盘报告，请点击分析开始');
                }
            } catch (err: any) {
                setResult(null);
                setReportContent('');
                const errMsg = err.response?.data?.detail || err.message || '未知错误';
                setError('查询失败: ' + errMsg);
            } finally {
                setLoading(false);
            }
        };

        fetchInitialReport();
        // 清理轮询
        setIsPolling(false);
    }, [selectedDate]);

    // 实现轮询逻辑
    React.useEffect(() => {
        let timer: NodeJS.Timeout;
        if (isPolling) {
            timer = setInterval(async () => {
                try {
                    const res = await getAnalysisReport('limit-up', selectedDate);
                    if (res && res.success && res.result) {
                        setResult(res.result.data || res.result);
                        setReportContent(res.result.markdown || '');
                        setIsPolling(false);
                    }
                } catch (e) {
                    console.error('轮询出错:', e);
                }
            }, 5000); // 每5秒检查一次
        }
        return () => clearInterval(timer);
    }, [isPolling, selectedDate]);

    const handleAnalysis = async (forceRerun: boolean = false) => {
        setLoading(true);
        setError('');
        try {
            // 调用运行分析的 POST 接口
            const res = await runLimitUpAnalysis(selectedDate, forceRerun);
            if (res && res.success) {
                if (res.message && res.message.includes('分析中')) {
                    setIsPolling(true);
                } else if (res.result) {
                    setResult(res.result.data || res.result);
                    setReportContent(res.result.markdown || '');
                }
            } else {
                setError('分析失败: ' + (res?.message || '未知错误'));
            }
        } catch (err: any) {
            setError('请求失败: ' + (err.response?.data?.detail || err.message || '网络异常'));
        } finally {
            setLoading(false);
        }
    };

    // 获取最近一周的日期列表
    const recentDays = React.useMemo(() => {
        const days = [];
        let checkDate = new Date();
        while (days.length < 7) {
            const dayOfWeek = checkDate.getDay();
            // 跳过周六(6)和周日(0)
            if (dayOfWeek !== 0 && dayOfWeek !== 6) {
                days.push(checkDate.toISOString().split('T')[0]);
            }
            checkDate.setDate(checkDate.getDate() - 1);
        }
        return days.reverse();
    }, []);

    const [showCalendar, setShowCalendar] = useState(false);
    const [viewDate, setViewDate] = useState(new Date());

    const calendarRef = React.useRef<HTMLDivElement>(null);

    // 处理外部点击关闭
    React.useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (calendarRef.current && !calendarRef.current.contains(event.target as Node)) {
                setShowCalendar(false);
            }
        };
        if (showCalendar) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showCalendar]);

    // 生成日历网格
    const calendarDays = React.useMemo(() => {
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const days = [];
        // 填充前导空格 (周日居首)
        for (let i = 0; i < firstDay; i++) {
            days.push(null);
        }
        // 填充实际日期
        for (let i = 1; i <= daysInMonth; i++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            days.push({ day: i, dateStr });
        }
        return days;
    }, [viewDate]);

    const changeMonth = (offset: number) => {
        const newDate = new Date(viewDate);
        newDate.setMonth(newDate.getMonth() + offset);
        setViewDate(newDate);
    };

    return (
        <div className="p-6 space-y-6 animate-fade-in pb-24 lg:pb-6">
            <div className="flex flex-col space-y-1 mb-2">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">涨停股分析</h1>
                <p className="text-sm text-[var(--color-text-secondary)]">AI 驱动的深度复盘与机会挖掘</p>
            </div>

            {/* 控制面板 */}
            <div className="glass-card p-4 sm:p-6 relative z-20">
                <div className="flex flex-col space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex flex-col">
                            <h2 className="text-lg font-bold text-white">分析报告</h2>
                            <p className="text-sm text-[var(--color-text-secondary)]">
                                {result ? (result.cached ? '已加载存档报告' : '最新生成的分析报告') : '选择日期或开始新分析'}
                            </p>
                        </div>
                        <button
                            onClick={() => handleAnalysis(true)}
                            disabled={loading}
                            className={clsx(
                                "px-6 py-2 rounded-lg font-bold text-white transition-all shadow-lg active:scale-95",
                                loading ? "bg-gray-600 cursor-not-allowed" : "bg-purple-600 hover:bg-purple-700 hover:shadow-purple-500/30"
                            )}
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    分析中...
                                </span>
                            ) : '重新生成该日分析'}
                        </button>
                    </div>

                    <div className="flex items-center gap-2 pb-2 scrollbar-none relative">
                        {/* 日历图标按钮 */}
                        <div className="shrink-0">
                            <button
                                onClick={() => setShowCalendar(!showCalendar)}
                                className={clsx(
                                    "w-10 h-10 flex items-center justify-center rounded-xl bg-surface-3 border transition-all active:scale-90",
                                    showCalendar ? "border-purple-500 bg-purple-600/10 text-purple-400" : "border-surface-4 text-gray-400 hover:border-purple-500/50 hover:bg-surface-4 hover:text-purple-400"
                                )}
                                title="选择指定日期"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2" /><line x1="16" x2="16" y1="2" y2="6" /><line x1="8" x2="8" y1="2" y2="6" /><line x1="3" x2="21" y1="10" y2="10" /></svg>
                            </button>

                            {/* 自定义日历弹窗 */}
                            {showCalendar && (
                                <div
                                    ref={calendarRef}
                                    className="absolute top-12 left-0 z-[100] w-72 bg-[#121212] border border-surface-4 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.8)] backdrop-blur-2xl animate-fade-in p-4"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <button onClick={() => changeMonth(-1)} className="p-1 hover:bg-surface-3 rounded-lg text-gray-400 transition-colors">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
                                        </button>
                                        <div className="text-sm font-bold text-white">
                                            {viewDate.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })}
                                        </div>
                                        <button onClick={() => changeMonth(1)} className="p-1 hover:bg-surface-3 rounded-lg text-gray-400 transition-colors">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-7 gap-1 mb-2">
                                        {['日', '一', '二', '三', '四', '五', '六'].map(d => (
                                            <div key={d} className="text-[10px] text-gray-500 text-center font-bold py-1 uppercase">{d}</div>
                                        ))}
                                    </div>
                                    <div className="grid grid-cols-7 gap-1 text-sm">
                                        {calendarDays.map((d, i) => {
                                            if (!d) return <div key={`empty-${i}`} className="h-8" />;
                                            const isSelected = selectedDate === d.dateStr;
                                            const isToday = new Date().toISOString().split('T')[0] === d.dateStr;

                                            return (
                                                <button
                                                    key={d.dateStr}
                                                    onClick={() => {
                                                        setSelectedDate(d.dateStr);
                                                        setShowCalendar(false);
                                                    }}
                                                    className={clsx(
                                                        "h-8 flex items-center justify-center rounded-lg transition-all active:scale-90 relative",
                                                        isSelected
                                                            ? "bg-purple-600 text-white font-bold"
                                                            : "text-gray-300 hover:bg-surface-4",
                                                        isToday && !isSelected && "text-purple-400 font-bold"
                                                    )}
                                                >
                                                    {d.day}
                                                    {isToday && !isSelected && (
                                                        <div className="absolute bottom-1 w-1 h-1 bg-purple-500 rounded-full" />
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none flex-1">
                            {/* 最近一周快捷选择 */}
                            <div className="flex items-center gap-2">
                                {recentDays.map(date => {
                                    const isSelected = selectedDate === date;
                                    const isToday = new Date().toISOString().split('T')[0] === date;
                                    const dateObj = new Date(date);
                                    const dayName = isToday ? '今天' : dateObj.toLocaleDateString('zh-CN', { weekday: 'short' });
                                    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                                    const day = String(dateObj.getDate()).padStart(2, '0');
                                    const displayDate = `${month}-${day}`;

                                    return (
                                        <button
                                            key={date}
                                            onClick={() => setSelectedDate(date)}
                                            className={clsx(
                                                "flex flex-col items-center justify-center min-w-[56px] h-14 rounded-xl border transition-all active:scale-95 shrink-0",
                                                isSelected
                                                    ? "bg-purple-600/20 border-purple-500 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
                                                    : "bg-surface-2 border-surface-3 text-gray-400 hover:border-gray-600 hover:bg-surface-3"
                                            )}
                                        >
                                            <span className="text-[10px] uppercase font-medium opacity-70">{dayName}</span>
                                            <span className="text-sm font-bold">{displayDate}</span>
                                        </button>
                                    );
                                })}
                            </div>

                            {/* 如果选中的日期不在最近一周内，显示一个特殊的选中项 */}
                            {!recentDays.includes(selectedDate) && (
                                <div className="flex items-center gap-2">
                                    <div className="h-4 w-px bg-surface-4 mx-1"></div>
                                    <button
                                        onClick={() => setSelectedDate(selectedDate)}
                                        className="flex flex-col items-center justify-center min-w-[70px] h-14 rounded-xl border bg-purple-600/20 border-purple-500 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.2)] shrink-0"
                                    >
                                        <span className="text-[10px] uppercase font-medium opacity-70">选定日期</span>
                                        <span className="text-xs font-bold">{selectedDate.split('-').slice(1).join('/')}</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
                {error && (
                    <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                        {error}
                    </div>
                )}
            </div>

            {/* 报告内容 */}
            {loading ? (
                <div className="glass-card p-12 flex flex-col items-center justify-center space-y-4">
                    <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-600 rounded-full animate-spin"></div>
                    <p className="text-gray-400">正在分析数据，请稍候...</p>
                </div>
            ) : reportContent ? (
                <div className="glass-card p-8 min-h-[500px]">
                    <article className="prose prose-invert max-w-none prose-p:text-gray-300 prose-headings:text-white prose-strong:text-purple-300">
                        <ReactMarkdown>{reportContent}</ReactMarkdown>
                    </article>
                </div>
            ) : (
                <div className="text-center py-20 text-[var(--color-text-muted)]">
                    {error ? '未发现当日报告' : '选择日期并点击分析开始'}
                </div>
            )}
        </div>
    );
};

export default StockAnalysisPage;
