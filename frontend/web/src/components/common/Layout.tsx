import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import CopilotPanel from './CopilotPanel';
import SettingsPanel from './SettingsPanel';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const location = useLocation();

  // 键盘快捷键支持
  React.useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K 打开 Copilot
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCopilotOpen(true);
      }
      // ESC 关闭 Copilot
      if (e.key === 'Escape' && copilotOpen) {
        setCopilotOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [copilotOpen]);

  const navItems = [
    { path: '/', label: '首页' },
    { path: '/portfolio', label: '持仓' },
    { path: '/news', label: '情报' },
    { path: '/analysis', label: '复盘' },
    { path: '/opening-analysis', label: '开盘' },
  ];

  const handleLogoClick = () => {
    setCopilotOpen(true);
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-surface-1)' }}>
      {/* 左侧导航栏 */}
      <nav
        className={clsx(
          'transition-all duration-300 flex flex-col border-r',
          sidebarCollapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-expanded)]'
        )}
        style={{ backgroundColor: 'var(--color-surface-2)', borderColor: 'var(--color-surface-4)' }}
      >
        {/* Logo */}
        <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-surface-4)' }}>
          <button
            onClick={handleLogoClick}
            className="flex items-center space-x-2"
          >
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-black font-bold"
              style={{ backgroundColor: 'var(--color-brand)' }}
            >
              R
            </div>
            {!sidebarCollapsed && (
              <span className="text-xl font-bold">Ruo</span>
            )}
          </button>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="text-[var(--color-text-secondary)] hover:text-white"
          >
            {sidebarCollapsed ? '>>' : '<<'}
          </button>
        </div>

        {/* 导航菜单 */}
        <div className="flex-1 py-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center justify-center px-4 py-3 mx-2 mb-1 rounded-lg transition-all',
                location.pathname === item.path
                  ? 'bg-[var(--color-surface-3)] text-[var(--color-brand)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-3)]'
              )}
            >
              {!sidebarCollapsed ? (
                <span className="font-bold text-lg">{item.label}</span>
              ) : (
                <span className="font-bold text-base">{item.label.substring(0, 1)}</span>
              )}
            </Link>
          ))}
        </div>

        {/* 底部设置 */}
        <div className="p-4 border-t" style={{ borderColor: 'var(--color-surface-4)' }}>
          <button
            onClick={() => setSettingsOpen(true)}
            className="flex items-center justify-center w-full text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
          >
            {!sidebarCollapsed ? (
              <span className="font-bold text-lg">设置</span>
            ) : (
              <span className="font-bold text-base">设</span>
            )}
          </button>
        </div>
      </nav>

      {/* 中间主工作区 */}
      <main
        className="flex-1 flex flex-col"
      >

        {/* 页面内容 */}
        <div className="flex-1">
          {children}
        </div>
      </main>

      {/* Ruo Copilot 面板 */}
      <CopilotPanel
        isOpen={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        context={{
          page: location.pathname,
        }}
      />

      {/* 设置面板 */}
      <SettingsPanel
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
};

export default Layout;
