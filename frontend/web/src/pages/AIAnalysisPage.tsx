import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysisHistory, HistoryItem, runAnalysis } from '@/api/analysis';
import { getPrompts, Prompt } from '@/api/prompt';
import clsx from 'clsx';
import { StockCalendar } from '@/components/StockCalendar';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  BarChart3,
  Play,
  RefreshCw,
  History,
  X,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  Trash2,
  Copy,
  MessageSquare
} from 'lucide-react';

// 分析任务类型
type AnalysisTask = 'limit-up' | 'opening-analysis';

// 任务卡片配置
const taskConfigs = {
  'limit-up': {
    id: 'limit-up',
    title: '市场复盘',
    description: '基于当日股票数据的复盘分析',
    icon: BarChart3,
    color: '#10B981',
    apiType: 'limit-up',
  },
  'opening-analysis': {
    id: 'opening-analysis',
    title: '开盘分析',
    description: '基于昨日涨停与今日竞价数据的早盘策略分析',
    icon: TrendingUp,
    color: '#2563EB',
    apiType: 'opening_analysis',
  },
};

const AIAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedTask, setSelectedTask] = useState<AnalysisTask | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportContent, setReportContent] = useState('');
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    const today = new Date();
    const day = today.getDay();
    let defaultDate = today;

    if (day === 0) {
      defaultDate = new Date(today.setDate(today.getDate() - 2));
    } else if (day === 6) {
      defaultDate = new Date(today.setDate(today.getDate() - 1));
    }

    return defaultDate.toISOString().split('T')[0];
  });
  const [showHistory, setShowHistory] = useState(false);
  const [historyReports, setHistoryReports] = useState<HistoryItem[]>([]);

  // 筛选状态
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStartDate, setFilterStartDate] = useState<string>('');
  const [filterEndDate, setFilterEndDate] = useState<string>('');

  // 分页状态
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPageSize] = useState(10);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 排序状态
  const [sortField, setSortField] = useState<'date' | 'type'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // 提示词广场状态
  const [showPrompts, setShowPrompts] = useState(false);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [promptFilter, setPromptFilter] = useState<'all' | 'official' | 'user'>('all');
  const [copiedPromptId, setCopiedPromptId] = useState<number | null>(null);

  // 日期选择弹窗
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [pendingTask, setPendingTask] = useState<AnalysisTask | null>(null);

  // 分析指令模板
  const promptTemplates: Record<AnalysisTask, string> = {
    'limit-up': '请帮我分析今日市场表现最强的股票，归纳其成为龙头的特征，并整理连板梯队和资金流向。',
    'opening-analysis': '请帮我分析今日竞价情况，基于昨日涨停与今日竞价数据给出早盘策略建议。',
  };

  // 获取提示词列表
  const fetchPrompts = async () => {
    setPromptsLoading(true);
    try {
      const params: any = {};
      if (promptFilter === 'official') {
        params.is_official = true;
      } else if (promptFilter === 'user') {
        params.is_official = false;
      }
      const data = await getPrompts(params);
      setPrompts(data);
    } catch (err) {
      console.error('获取提示词失败:', err);
    } finally {
      setPromptsLoading(false);
    }
  };

  // 加载提示词
  useEffect(() => {
    if (showPrompts) {
      fetchPrompts();
    }
  }, [showPrompts, promptFilter]);

  // 复制提示词到输入框
  const handleCopyPrompt = async (prompt: Prompt) => {
    setCustomPrompt(prompt.content);
    setCopiedPromptId(prompt.id);
    setShowPrompts(false);
    setSelectedTask(null);
    setShowHistory(false);
    setTimeout(() => setCopiedPromptId(null), 2000);
  };


  const handleAnalysis = async (type: AnalysisTask | 'prompt', params: any = {}) => {
    setLoading(true);

    try {
      let res;

      if (type === 'prompt') {
        res = await runAnalysis({
          analysisType: 'prompt',
          analysisName: params.analysisName || '自定义分析',
          prompt: params.prompt
        });
      } else {
        res = await runAnalysis({
          analysisType: type,
          analysisName: taskConfigs[type].title,
          analysisParam: { date: selectedDate }
        });
      }

      if (res && res.success) {
        setReportContent(res.message || '分析任务已成功启动，请在下方历史记录中查看进度。');
        // 自动切换到历史记录并刷新
        setShowHistory(true);
        fetchHistory(1);
      } else {
        setReportContent('分析失败: ' + (res?.message || '未知错误'));
      }
    } catch (err: any) {
      setReportContent('请求失败: ' + (err.response?.data?.detail || err.message || '网络异常'));
    } finally {
      setLoading(false);
    }
  };

  // 显示提示词广场
  const handleShowPrompts = () => {
    setShowPrompts(true);
    setSelectedTask(null);
    setShowHistory(false);
  };

  const handleTaskSelect = (task: AnalysisTask) => {
    // 弹出日期选择弹窗
    setPendingTask(task);
    setShowDatePicker(true);
  };

  // 处理日期确认
  const handleDateConfirm = () => {
    if (pendingTask) {
      setSelectedTask(pendingTask);
      // 将对应的分析指令填入输入框
      setCustomPrompt(promptTemplates[pendingTask]);
    }
    setShowDatePicker(false);
    setPendingTask(null);
  };


  // 获取历史报告
  const fetchHistory = async (page: number = 1) => {
    setHistoryLoading(true);
    try {
      const res = await getAnalysisHistory(
        page, 
        historyPageSize, 
        filterType === 'all' ? undefined : filterType,
        filterStartDate,
        filterEndDate
      );
      if (res?.success && res?.result?.items) {
        setHistoryReports(res.result.items);
        setHistoryTotal(res.total || 0);
        setHistoryPage(page);
      }
    } catch (err) {
      console.error('获取历史报告失败:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleShowHistory = async () => {
    setShowHistory(true);
    setSelectedTask(null);
    setHistoryPage(1);
    await fetchHistory(1);
  };

  // 查看详情
  const handleViewDetail = (report: HistoryItem) => {
    navigate(`/stock/analysis-history/${report.id}`);
  };

  // 删除历史记录
  const handleDeleteHistory = async (report: HistoryItem, e: React.MouseEvent) => {
    e.stopPropagation();
    // TODO: 实现删除功能
    console.log('删除报告:', report.id);
  };

  // 排序处理
  const handleSort = (field: 'date' | 'type') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // 排序后的历史记录
  const sortedHistoryReports = useMemo(() => {
    const sorted = [...historyReports].sort((a, b) => {
      if (sortField === 'date') {
        const dateA = new Date(a.report_date).getTime();
        const dateB = new Date(b.report_date).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
      } else {
        const typeA = a.analysis_name || '';
        const typeB = b.analysis_name || '';
        return sortOrder === 'asc' ? typeA.localeCompare(typeB) : typeB.localeCompare(typeA);
      }
    });
    return sorted;
  }, [historyReports, sortField, sortOrder]);

  // 分页计算
  const totalPages = Math.ceil(historyTotal / historyPageSize);

  return (
    <div className="min-h-screen bg-background">
      {/* 日期选择弹窗 */}
      {showDatePicker && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                {pendingTask === 'limit-up' ? '市场复盘' : '开盘分析'} - {selectedDate}
              </h3>
              <button
                onClick={() => {
                  setShowDatePicker(false);
                  setPendingTask(null);
                }}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="mb-6">
              <StockCalendar
                value={selectedDate}
                onChange={setSelectedDate}
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDatePicker(false);
                  setPendingTask(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleDateConfirm}
                className="flex-1 px-4 py-2 bg-amber-500 text-white rounded-xl hover:bg-amber-600 transition-colors font-medium"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 顶部输入框区域 */}
      <div className="bg-white border-b border-gray-100 px-4 py-4 md:px-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Sparkles className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-amber-500" />
              <input
                type="text"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="输入自定义分析指令... (可选)"
                className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
              />
            </div>
            <button
              onClick={() => {
                if (selectedTask) {
                  handleAnalysis(selectedTask);
                } else if (customPrompt.trim()) {
                  handleAnalysis('prompt', { prompt: customPrompt });
                }
              }}
              disabled={!customPrompt.trim() && !selectedTask}
              className={clsx(
                "px-5 py-3 rounded-xl font-medium text-sm transition-all",
                (customPrompt.trim() || selectedTask) && !loading
                  ? "bg-amber-500 text-white hover:bg-amber-600 shadow-sm"
                  : "bg-gray-100 text-gray-400 cursor-not-allowed"
              )}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  分析中
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  执行分析
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 任务卡片区域 */}
        {!showHistory && !reportContent && !showPrompts && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {(Object.keys(taskConfigs) as AnalysisTask[]).map((taskKey) => {
              const config = taskConfigs[taskKey];
              const isSelected = selectedTask === taskKey;

              return (
                <motion.button
                  key={taskKey}
                  onClick={() => handleTaskSelect(taskKey)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={clsx(
                    "relative p-6 rounded-2xl border-2 text-left transition-all duration-200",
                    isSelected
                      ? "border-gray-300 bg-gray-50 shadow-md"
                      : "border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${config.color}15` }}
                    >
                      <config.icon className="w-6 h-6" style={{ color: config.color }} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{config.title}</h3>
                      <p className="text-sm text-gray-500">{config.description}</p>
                    </div>
                    {isSelected && (
                      <div className="w-6 h-6 rounded-full bg-gray-900 flex items-center justify-center">
                        <ChevronRight className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </div>
                </motion.button>
              );
            })}

            {/* 历史报告卡片 */}
            <motion.button
              onClick={handleShowHistory}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="p-6 rounded-2xl border-2 border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm transition-all duration-200 text-left"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 bg-gray-100">
                  <History className="w-6 h-6 text-gray-500" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">历史报告</h3>
                  <p className="text-sm text-gray-500">查看过往的分析报告</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </motion.button>

            {/* 提示词广场卡片 */}
            <motion.button
              onClick={handleShowPrompts}
              whileHover={{ scale: 1.02, translateY: -4 }}
              whileTap={{ scale: 0.98 }}
              className="p-6 rounded-3xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-transparent hover:border-amber-500/40 hover:shadow-xl hover:shadow-amber-500/10 transition-all duration-300 text-left relative overflow-hidden group"
            >
              <div className="absolute -right-8 -bottom-8 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-all" />
              <div className="flex items-start gap-4 relative z-10">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 bg-amber-500/20 shadow-inner">
                  <MessageSquare className="w-6 h-6 text-amber-500" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 mb-1">提示词广场</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">选择预设提示词进行自定义分析</p>
                </div>
                <ChevronRight className="w-5 h-5 text-amber-500/50 group-hover:text-amber-500 transition-colors" />
              </div>
            </motion.button>
          </div>
        )}

        {/* 返回按钮（当在历史记录或提示词广场时） */}
        {(showHistory || showPrompts) && (
          <div className="mb-6">
            <button
              onClick={() => {
                setShowHistory(false);
                setShowPrompts(false);
                setReportContent('');
              }}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              <span>返回分析主页</span>
            </button>
          </div>
        )}

        {/* 历史报告列表 - 表格布局 */}
        {showHistory && (
          <div className="bg-white/80 backdrop-blur-xl border border-gray-200 rounded-3xl overflow-hidden shadow-xl shadow-gray-200/50">
            <div className="px-8 py-6 border-b border-gray-100 bg-gradient-to-r from-gray-50/50 to-transparent">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <h3 className="font-bold text-gray-900 flex items-center gap-3 text-lg">
                  <div className="p-2 rounded-xl bg-gray-900 text-white">
                    <History className="w-5 h-5" />
                  </div>
                  历史分析报告
                </h3>
                
                <div className="flex flex-wrap items-center gap-3 bg-white p-2 rounded-2xl border border-gray-100 shadow-sm">
                  {/* 类型筛选 */}
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="pl-3 pr-8 py-2 bg-gray-50 border-none rounded-xl text-sm font-medium focus:ring-2 focus:ring-amber-500/20 transition-all cursor-pointer"
                  >
                    <option value="all">全部类型</option>
                    <option value="limit-up">市场复盘</option>
                    <option value="opening-analysis">开盘分析</option>
                    <option value="prompt">自定义分析</option>
                    <option value="kline_analysis">K线分析</option>
                  </select>

                  {/* 日期筛选 */}
                  <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-xl">
                    <input
                      type="date"
                      value={filterStartDate}
                      onChange={(e) => setFilterStartDate(e.target.value)}
                      className="bg-transparent border-none p-0 text-sm focus:ring-0 cursor-pointer"
                      placeholder="开始日期"
                    />
                    <span className="text-gray-300 text-xs">至</span>
                    <input
                      type="date"
                      value={filterEndDate}
                      onChange={(e) => setFilterEndDate(e.target.value)}
                      className="bg-transparent border-none p-0 text-sm focus:ring-0 cursor-pointer"
                      placeholder="结束日期"
                    />
                  </div>

                  {/* 搜索按钮 */}
                  <button
                    onClick={() => fetchHistory(1)}
                    className="px-4 py-2 bg-gray-900 text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-all flex items-center gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    查询
                  </button>
                  
                  {/* 重置按钮 */}
                  <button
                    onClick={() => {
                      setFilterType('all');
                      setFilterStartDate('');
                      setFilterEndDate('');
                      setTimeout(() => fetchHistory(1), 0);
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all"
                    title="重置筛选"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {historyLoading ? (
              <div className="p-12 flex flex-col items-center justify-center">
                <div className="w-10 h-10 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
                <p className="text-gray-500 mt-3">加载中...</p>
              </div>
            ) : sortedHistoryReports.length > 0 ? (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-100">
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('date')}
                        >
                          <div className="flex items-center gap-1">
                            分析时间
                            {sortField === 'date' ? (
                              sortOrder === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                            ) : <ArrowUpDown className="w-3 h-3 opacity-30" />}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('type')}
                        >
                          <div className="flex items-center gap-1">
                            分析类型
                            {sortField === 'type' ? (
                              sortOrder === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                            ) : <ArrowUpDown className="w-3 h-3 opacity-30" />}
                          </div>
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          股票代码
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          分析摘要
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          状态
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {sortedHistoryReports.map((report) => (
                        <tr
                          key={report.id}
                          className="hover:bg-gray-50 transition-colors cursor-pointer"
                          onClick={() => handleViewDetail(report)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {report.report_date}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={clsx(
                              "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                              report.analysis_type === 'limit-up'
                                ? "bg-emerald-100 text-emerald-800"
                                : report.analysis_type === 'opening_analysis'
                                  ? "bg-blue-100 text-blue-800"
                                  : "bg-gray-100 text-gray-800"
                            )}>
                              {report.analysis_name}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {report.symbol || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                            {report.summary || '暂无摘要'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={clsx(
                              "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                              report.status === 'completed'
                                ? "bg-green-100 text-green-800"
                                : report.status === 'processing'
                                  ? "bg-amber-100 text-amber-800 animate-pulse"
                                  : "bg-red-100 text-red-800"
                            )}>
                              {report.status === 'completed' ? '已完成' : report.status === 'processing' ? '正在分析' : '分析失败'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                            <div className="flex items-center justify-end gap-2" onClick={e => e.stopPropagation()}>
                              <button
                                onClick={() => handleViewDetail(report)}
                                disabled={report.status === 'processing'}
                                className={clsx(
                                  "p-1.5 rounded-lg transition-colors",
                                  report.status === 'processing'
                                    ? "text-gray-300 cursor-not-allowed"
                                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                                )}
                                title={report.status === 'processing' ? "正在分析中" : "查看"}
                              >
                                {report.status === 'processing' ? (
                                  <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                                ) : (
                                  <Eye className="w-4 h-4" />
                                )}
                              </button>
                              <button
                                onClick={(e) => handleDeleteHistory(report, e)}
                                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="删除"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="px-8 py-6 border-t border-gray-100 flex flex-col md:flex-row items-center justify-between gap-4 bg-gray-50/30">
                    <div className="text-sm text-gray-500 font-medium">
                      显示第 <span className="text-gray-900">{(historyPage - 1) * historyPageSize + 1}</span> 到 <span className="text-gray-900">{Math.min(historyPage * historyPageSize, historyTotal)}</span> 条，共 <span className="text-gray-900">{historyTotal}</span> 条记录
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => fetchHistory(historyPage - 1)}
                        disabled={historyPage === 1}
                        className={clsx(
                          "px-3 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-1",
                          historyPage === 1
                            ? "bg-gray-100 text-gray-300 cursor-not-allowed"
                            : "bg-white border border-gray-200 text-gray-700 hover:border-gray-900 hover:shadow-sm"
                        )}
                      >
                        <ChevronLeft className="w-4 h-4" />
                        上一页
                      </button>
                      
                      <div className="flex items-center gap-1.5 px-1">
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                          .filter(p => p === 1 || p === totalPages || Math.abs(p - historyPage) <= 1)
                          .map((pageNum, idx, arr) => (
                            <React.Fragment key={pageNum}>
                              {idx > 0 && arr[idx - 1] !== pageNum - 1 && (
                                <span className="text-gray-300 px-1">...</span>
                              )}
                              <button
                                onClick={() => fetchHistory(pageNum)}
                                className={clsx(
                                  "w-10 h-10 rounded-xl text-sm font-bold transition-all",
                                  historyPage === pageNum
                                    ? "bg-gray-900 text-white shadow-lg shadow-gray-900/20"
                                    : "bg-white border border-gray-200 text-gray-600 hover:border-gray-900 hover:text-gray-900"
                                )}
                              >
                                {pageNum}
                              </button>
                            </React.Fragment>
                          ))}
                      </div>

                      <button
                        onClick={() => fetchHistory(historyPage + 1)}
                        disabled={historyPage === totalPages}
                        className={clsx(
                          "px-3 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-1",
                          historyPage === totalPages
                            ? "bg-gray-100 text-gray-300 cursor-not-allowed"
                            : "bg-white border border-gray-200 text-gray-700 hover:border-gray-900 hover:shadow-sm"
                        )}
                      >
                        下一页
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="p-12 text-center text-gray-500">
                暂无历史报告
              </div>
            )}
          </div>
        )}

        {/* 提示词广场 */}
        {showPrompts && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-amber-600" />
                提示词广场
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPromptFilter('all')}
                  className={clsx(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                    promptFilter === 'all'
                      ? "bg-gray-900 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  )}
                >
                  全部
                </button>
                <button
                  onClick={() => setPromptFilter('official')}
                  className={clsx(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                    promptFilter === 'official'
                      ? "bg-amber-500 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  )}
                >
                  官方示例
                </button>
                <button
                  onClick={() => setPromptFilter('user')}
                  className={clsx(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                    promptFilter === 'user'
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  )}
                >
                  用户分享
                </button>
              </div>
            </div>

            {promptsLoading ? (
              <div className="p-12 flex flex-col items-center justify-center">
                <div className="w-10 h-10 border-4 border-gray-200 border-t-amber-500 rounded-full animate-spin"></div>
                <p className="text-gray-500 mt-3">加载中...</p>
              </div>
            ) : prompts.length > 0 ? (
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {prompts.map((prompt) => (
                    <motion.div
                      key={prompt.id}
                      whileHover={{ scale: 1.02 }}
                      className="p-4 rounded-xl border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all cursor-pointer bg-white"
                      onClick={() => handleCopyPrompt(prompt)}
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h4 className="font-medium text-gray-900 flex items-center gap-2">
                          {prompt.is_official && (
                            <span className="px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-700 rounded">
                              官方
                            </span>
                          )}
                          {prompt.name}
                        </h4>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyPrompt(prompt);
                          }}
                          className={clsx(
                            "p-1.5 rounded-lg transition-colors shrink-0",
                            copiedPromptId === prompt.id
                              ? "bg-green-100 text-green-600"
                              : "text-gray-400 hover:text-amber-600 hover:bg-amber-50"
                          )}
                          title="使用此提示词"
                        >
                          {copiedPromptId === prompt.id ? (
                            <Sparkles className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                      <p className="text-sm text-gray-500 line-clamp-2">
                        {prompt.description}
                      </p>
                      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                        <span className="text-xs text-gray-400">
                          {prompt.category}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-gray-500">
                暂无提示词
              </div>
            )}
          </div>
        )}

        {/* 状态消息 */}
        {reportContent && !showHistory && !showPrompts && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative overflow-hidden rounded-3xl border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-orange-500/5 p-12 text-center"
          >
            <div className="absolute -right-20 -top-20 w-64 h-64 blur-[100px] opacity-10 bg-amber-500 rounded-full" />
            <div className="absolute -left-20 -bottom-20 w-64 h-64 blur-[100px] opacity-10 bg-orange-500 rounded-full" />

            <div className="relative z-10">
              <div className="w-20 h-20 rounded-3xl bg-amber-500/20 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-amber-500/10">
                <Sparkles className="w-10 h-10 text-amber-500" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 mb-3 tracking-tight">分析任务已提交</h3>
              <p className="text-gray-600 font-medium mb-8 max-w-md mx-auto leading-relaxed">{reportContent}</p>
              <button
                onClick={handleShowHistory}
                className="px-8 py-3 bg-amber-500 text-white rounded-2xl hover:bg-amber-600 hover:shadow-lg hover:shadow-amber-500/30 transition-all font-bold inline-flex items-center gap-2 active:scale-95"
              >
                <History className="w-5 h-5" />
                前往历史报告列表
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default AIAnalysisPage;
