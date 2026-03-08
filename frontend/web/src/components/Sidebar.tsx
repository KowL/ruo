import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Home,
  Bot,
  TrendingUp,
  Heart,
  Settings,
  PanelLeft
} from 'lucide-react';
import { useSidebarStore } from '../store/sidebarStore';

const navItems = [
  { id: 'home', label: 'AI助手', icon: Home, path: '/' },
  { id: 'ai-console', label: 'AI控制台', icon: Bot, path: '/ai-console' },
  { id: 'stock', label: '股票', icon: TrendingUp, path: '/stock' },
  { id: 'life', label: '生活', icon: Heart, path: '/life' },
  { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
];

export function Sidebar() {
  const { isVisible, toggleSidebar } = useSidebarStore();

  if (!isVisible) return null;

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
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-400 shadow-sm flex items-center justify-center">
            <span className="text-white font-bold text-sm">R</span>
          </div>
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
      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
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
          ))}
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
