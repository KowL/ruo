import { NavLink } from 'react-router-dom';
import { 
  Home, 
  Bot, 
  TrendingUp, 
  Heart, 
  Settings 
} from 'lucide-react';

const navItems = [
  { id: 'home', label: '工作台', icon: Home, path: '/' },
  { id: 'ai-console', label: 'AI', icon: Bot, path: '/ai-console' },
  { id: 'stock', label: '股票', icon: TrendingUp, path: '/stock' },
  { id: 'life', label: '生活', icon: Heart, path: '/life' },
  { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
];

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 h-16 bg-[#1E293B] border-t border-[#334155] z-50 lg:hidden">
      <ul className="flex items-center justify-around h-full px-2">
        {navItems.map((item) => (
          <li key={item.id}>
            <NavLink
              to={item.path}
              className={({ isActive }: { isActive: boolean }) =>
                `flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'text-[#2563EB]'
                    : 'text-[#94A3B8]'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
