import { NavLink, Outlet } from 'react-router-dom';

const stockNavItems = [
    { id: 'dashboard', label: '概览', path: '/stock' },
    { id: 'portfolio', label: '持仓', path: '/stock/portfolio' },
    { id: 'favorites', label: '自选', path: '/stock/favorites' },
    { id: 'strategies', label: '策略', path: '/stock/strategies' },
    { id: 'radar', label: '雷达', path: '/stock/radar' },
    { id: 'news', label: '情报', path: '/stock/news' },
    { id: 'analysis', label: '复盘', path: '/stock/analysis' },
    { id: 'opening-analysis', label: '开盘', path: '/stock/opening-analysis' },
    { id: 'concepts', label: '概念', path: '/stock/concepts' },
    { id: 'concept-monitor', label: '监控', path: '/stock/concept-monitor' },
    { id: 'subscriptions', label: '订阅', path: '/stock/subscriptions' },
];

export function StockLayout() {
    return (
        <div className="flex flex-col min-h-full">
            {/* Sub Navigation */}
            <div className="sticky top-0 z-30 mb-6 mt-2 px-2 py-1 overflow-x-auto scrollbar-hide">
                <nav className="flex space-x-1 min-w-max">
                    {stockNavItems.map((item) => (
                        <NavLink
                            key={item.id}
                            to={item.path}
                            end={item.path === '/stock'}
                            className={({ isActive }) =>
                                `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                    ? 'bg-primary text-primary-foreground'
                                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                                }`
                            }
                        >
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
            </div>

            {/* Page Content */}
            <div className="flex-1">
                <Outlet />
            </div>
        </div>
    );
}
