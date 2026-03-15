import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Calendar, FileText, BarChart3, TrendingUp, History, Copy, Check, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { getHistoryDetail } from '@/api/analysis';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { toast } from 'sonner';

const AnalysisHistoryDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [report, setReport] = useState<any>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const fetchDetail = async () => {
            if (!id) return;
            setLoading(true);
            try {
                const res = await getHistoryDetail(parseInt(id));
                if (res && res.success && res.result) {
                    setReport(res.result);
                } else {
                    toast.error(res?.message || '获取报告详情失败');
                }
            } catch (err: any) {
                console.error('获取报告详情失败:', err);
                toast.error('请求失败: ' + (err.response?.data?.detail || err.message || '网络异常'));
            } finally {
                setLoading(false);
            }
        };

        fetchDetail();
    }, [id]);

    const handleCopy = () => {
        const content = report?.markdown || report?.content;
        if (!content) return;
        navigator.clipboard.writeText(content);
        setCopied(true);
        toast.success('已复制到剪贴板');
        setTimeout(() => setCopied(false), 2000);
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loading />
                <p className="mt-4 text-muted-foreground">正在加载分析报告...</p>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <History className="w-16 h-16 text-muted mb-4 opacity-20" />
                <p className="text-muted-foreground text-lg">未找到该报告或已被删除</p>
                <Button 
                    variant="secondary" 
                    className="mt-6"
                    onClick={() => navigate('/stock/analysis')}
                >
                    返回 AI 分析
                </Button>
            </div>
        );
    }

    const getReportIcon = (type: string) => {
        if (type === 'limit-up') return <BarChart3 className="w-5 h-5 text-amber-500" />;
        if (type === 'opening_analysis') return <TrendingUp className="w-5 h-5 text-orange-500" />;
        return <FileText className="w-5 h-5 text-slate-400" />;
    };

    return (
        <div className="max-w-4xl mx-auto space-y-4 pb-12 animate-fade-in">
            {/* Header Navigation */}
            <div className="flex items-center justify-between px-2">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors py-2 group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                    <span className="text-sm font-medium">返回列表</span>
                </button>

                <Button
                    variant="secondary"
                    onClick={handleCopy}
                    className="flex items-center gap-2 bg-white hover:bg-muted text-foreground text-xs shadow-sm border border-border"
                >
                    {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? '已复制' : '复制全文'}
                </Button>
            </div>

            {/* Simple Header */}
            <div className="px-6 py-5 bg-card border border-border rounded-2xl flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-4">
                    <div className="p-3 rounded-xl bg-muted/50 border border-border">
                        {getReportIcon(report.analysis_type)}
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-foreground">
                            {report.analysis_name}
                        </h1>
                        <div className="flex items-center gap-4 text-xs mt-1">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                                <Calendar className="w-3.5 h-3.5 opacity-70" />
                                {report.report_date}
                            </span>
                            {report.symbol && (
                                <span className="flex items-center gap-1 text-primary/80 font-mono font-bold">
                                    <Zap className="w-3 h-3" />
                                    {report.symbol}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black tracking-wider uppercase border
                        ${report.analysis_type === 'limit-up' 
                            ? 'border-amber-500/20 bg-amber-500/10 text-amber-600' 
                            : 'border-orange-500/20 bg-orange-500/10 text-orange-600'}`}>
                        {report.analysis_type === 'limit-up' ? 'MARKET REVIEW' : 'OPENING SCAN'}
                    </span>
                </div>
            </div>

            {/* Main Content */}
            <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
                <div className="p-8 md:p-12 leading-relaxed">
                    <article className="prose prose-slate prose-stone max-w-none 
                        prose-p:text-foreground/80 prose-p:leading-8 
                        prose-headings:text-foreground prose-headings:font-bold
                        prose-li:text-foreground/80
                        prose-strong:text-primary prose-strong:font-bold
                        ">
                        <ReactMarkdown>{report.markdown || report.content || '# 暂无内容'}</ReactMarkdown>
                    </article>
                </div>
                <div className="px-8 py-5 bg-muted/30 border-t border-border flex justify-between items-center text-[10px] text-muted-foreground font-mono tracking-widest uppercase">
                    <span>GENERATED BY RUO AI</span>
                    <span>REPORT ID: {report.id}</span>
                </div>
            </div>
        </div>
    );
};

export default AnalysisHistoryDetailPage;
