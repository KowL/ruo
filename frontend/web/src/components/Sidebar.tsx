import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Home, 
  Bot, 
  TrendingUp, 
  Heart, 
  Settings 
} from 'lucide-react';

const navItems = [
  { id: 'home', label: 'AI助手', icon: Home, path: '/' },
  { id: 'ai-console', label: 'AI控制台', icon: Bot, path: '/ai-console' },
  { id: 'stock', label: '股票', icon: TrendingUp, path: '/stock' },
  { id: 'life', label: '生活', icon: Heart, path: '/life' },
  { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
];

export function Sidebar() {
  return (
    <motion.aside
      initial={{ x: -200 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="fixed left-0 top-0 h-full w-[200px] bg-[#1E293B] border-r border-[#334155] z-50 hidden lg:flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-[#334155]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#2563EB] to-[#06B6D4] flex items-center justify-center">
            <span className="text-white font-bold text-sm">R</span>
          </div>
          <span className="text-[#F8FAFC] font-semibold text-sm">Ruo AI</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.id}>
              <NavLink
                to={item.path}
                className={({ isActive }: { isActive: boolean }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-[#2563EB]/20 text-[#2563EB]'
                      : 'text-[#94A3B8] hover:bg-[#334155] hover:text-[#F8FAFC]'
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
      <div className="p-4 border-t border-[#334155]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#2563EB] flex items-center justify-center">
            <span className="text-white text-xs font-medium">R</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[#F8FAFC] text-sm font-medium truncate">Ruo</p>
            <p className="text-[#94A3B8] text-xs truncate">在线</p>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
