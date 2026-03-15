import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Home,
  Bot,
  TrendingUp,
  Heart,
  Settings,
  PanelLeft,
  ChevronDown,
  ChevronRight,
  Flame,
  Library,
  Users,
  FileText,
  Newspaper,
  LayoutDashboard,
  Star
} from 'lucide-react';
import { useSidebarStore } from '../store/sidebarStore';

// 主导航项
const navItems = [
  { id: 'home', label: '工作台', icon: Home, path: '/' },
  { id: 'ai-console', label: 'AI控制台', icon: Bot, path: '/ai-console' },
  { id: 'stock', label: '股票', icon: TrendingUp, path: '/stock', hasSubMenu: true },
  { id: 'life', label: '生活', icon: Heart, path: '/life' },
  { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
];

// 股票子菜单
const stockSubItems = [
  { id: 'dashboard', label: '概览', path: '/stock', icon: LayoutDashboard },
  { id: 'favorites', label: '自选', path: '/stock/favorites', icon: Star },
  { id: 'limit-up-ladder', label: '连板天梯', path: '/stock/limit-up-ladder', icon: Flame },
  { id: 'concept-library', label: '概念库', path: '/stock/concept-library', icon: Library },
  { id: 'portfolio', label: '持仓', path: '/stock/portfolio', icon: Users },
  { id: 'strategies', label: '策略', path: '/stock/strategies', icon: FileText },
  { id: 'subscriptions', label: '订阅', path: '/stock/subscriptions', icon: FileText },
  { id: 'news', label: '情报', path: '/stock/news', icon: Newspaper },
  { id: 'ai-analysis', label: 'AI分析', path: '/stock/analysis', icon: Bot },
];

export function Sidebar() {
  const location = useLocation();
  const { isVisible, toggleSidebar } = useSidebarStore();
  const [expandedStock, setExpandedStock] = useState(true);

  if (!isVisible) return null;

  const isStockActive = (pathname: string) => pathname.startsWith('/stock');

  return (
    <motion.aside
      initial={{ x: -200, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -200, opacity: 0 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="fixed left-0 top-0 h-full w-[200px] glass z-50 hidden lg:flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border/50">
        <div className="flex items-center gap-2">
          <img src="/favicon.svg" alt="Ruo AI" className="w-8 h-8 object-contain" />
          <span className="text-foreground font-semibold text-sm tracking-wide">Ruo AI</span>
        </div>
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground active:bg-muted active:border active:border-border transition-all duration-100"
          title="隐藏侧边栏"
        >
          <PanelLeft className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => {
            if (item.id === 'stock') {
              // 股票菜单 - 带展开子菜单
              const isActive = isStockActive(location.pathname);
              return (
                <li key={item.id}>
                  <button
                    onClick={() => setExpandedStock(!expandedStock)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                        ? 'bg-primary/10 text-primary font-medium shadow-sm'
                        : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="w-5 h-5" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </div>
                    {expandedStock ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>

                  {/* 股票子菜单 */}
                  {expandedStock && (
                    <motion.ul
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="ml-4 mt-1 space-y-0.5 overflow-hidden"
                    >
                      {stockSubItems.map((subItem) => {
                        const Icon = subItem.icon;
                        // 判断是否当前选中
                        const isSubActive = location.pathname === subItem.path ||
                          (subItem.path !== '/stock' && location.pathname.startsWith(subItem.path));

                        return (
                          <li key={subItem.id}>
                            <NavLink
                              to={subItem.path}
                              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 ${isSubActive
                                  ? 'bg-primary/10 text-primary'
                                  : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                                }`}
                            >
                              {Icon && <Icon className="w-4 h-4" />}
                              <span>{subItem.label}</span>
                            </NavLink>
                          </li>
                        );
                      })}
                    </motion.ul>
                  )}
                </li>
              );
            }

            // 普通菜单项
            return (
              <li key={item.id}>
                <NavLink
                  to={item.path}
                  className={({ isActive }: { isActive: boolean }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                      ? 'bg-primary/10 text-primary font-medium shadow-sm'
                      : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Info */}
      <div className="p-4 border-t border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-400 shadow-sm flex items-center justify-center">
            <span className="text-white text-xs font-semibold">R</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-foreground text-sm font-medium truncate">Ruo</p>
            <p className="text-muted-foreground text-xs truncate">在线</p>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
