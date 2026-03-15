import { Outlet, useLocation } from 'react-router-dom';
import { Flame } from 'lucide-react';

// 获取当前页面标题
const getPageTitle = (pathname: string): string => {
    if (pathname === '/stock' || pathname === '/stock/') return '概览';
    if (pathname.includes('limit-up-ladder')) return '连板天梯';
    if (pathname.includes('theme-library')) return '题材库';
    if (pathname.includes('concept') && !pathname.includes('monitor')) return '概念板块';
    if (pathname.includes('concept-monitor')) return '概念监控';
    if (pathname.includes('analysis') && !pathname.includes('opening')) return '复盘';
    if (pathname.includes('opening-analysis')) return '开盘分析';
    if (pathname.includes('portfolio')) return '持仓';
    if (pathname.includes('strategies')) return '策略';
    if (pathname.includes('subscriptions')) return '订阅';
    if (pathname.includes('news')) return '情报';
    if (pathname.includes('chart')) return '走势';
    return '股票';
};

export function StockLayout() {
    const location = useLocation();
    const pageTitle = getPageTitle(location.pathname);

    return (
        <div className="flex flex-col min-h-full">
            {/* 页面标题 - 移动端显示 */}
            <div className="lg:hidden sticky top-0 z-30 flex items-center px-4 py-3 bg-[#0F172A]/95 backdrop-blur-sm border-b border-[#1E293B]">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                        <Flame className="w-5 h-5 text-primary" />
                    </div>
                    <h1 className="text-lg font-bold text-white">{pageTitle}</h1>
                </div>
            </div>

            {/* 页面内容区域 */}
            <div className="flex-1">
                <Outlet />
            </div>
        </div>
    );
}
