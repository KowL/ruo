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
    { path: '/portfolio', label: '持仓', icon: '📊' },
    { path: '/news', label: '情报', icon: '📰' },
    { path: '/chart', label: 'K线', icon: '📈' },
  ];

  const handleLogoClick = () => {
    setCopilotOpen(true);
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-surface-1)' }}>
      {/* 左侧导航栏 */}
      <nav
        className={clsx(
          'transition-all duration-300 flex flex-col',
          sidebarCollapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-expanded)]',
          'border-r border-[var(--color-surface-3)]'
        )}
        style={{ backgroundColor: 'var(--color-surface-2)' }}
      >
        {/* Logo */}
        <div className="p-4 border-b border-[var(--color-surface-3)]">
          <button
            onClick={handleLogoClick}
            className="flex items-center space-x-2 w-full"
          >
            <div
              className="w-8 h-8 rounded-lg gradient-aurora flex items-center justify-center text-white font-bold"
            >
              R
            </div>
            {!sidebarCollapsed && (
              <span className="text-xl font-bold">Ruo</span>
            )}
          </button>
        </div>

        {/* 导航菜单 */}
        <div className="flex-1 py-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center space-x-3 px-4 py-3 mx-2 mb-1 rounded-lg transition-all',
                location.pathname === item.path
                  ? 'bg-[var(--color-ruo-purple)]/20 border-l-4 border-[var(--color-ruo-purple)] text-[var(--color-ruo-purple)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-3)]'
              )}
            >
              <span className="text-xl">{item.icon}</span>
              {!sidebarCollapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </Link>
          ))}
        </div>

        {/* 底部设置 */}
        <div className="p-4 border-t border-[var(--color-surface-3)]">
          <button
            onClick={() => setSettingsOpen(true)}
            className="flex items-center space-x-3 w-full text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
          >
            <span className="text-xl">⚙️</span>
            {!sidebarCollapsed && (
              <span className="font-medium">设置</span>
            )}
          </button>
        </div>
      </nav>

      {/* 中间主工作区 */}
      <main
        className="flex-1 flex flex-col"
        style={{ marginLeft: sidebarCollapsed ? '64px' : '240px' }}
      >
        {/* 顶部栏 */}
        <header
          className="sticky top-0 z-40 border-b border-[var(--color-surface-3)]"
          style={{ backgroundColor: 'var(--color-surface-2)' }}
        >
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-3)]"
              >
                <span className="text-xl">
                  {sidebarCollapsed ? '☰' : '✕'}
                </span>
              </button>
              <h1 className="text-xl font-bold">Ruo AI 智能投顾副驾</h1>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCopilotOpen(true)}
                className="px-4 py-2 rounded-lg hover:bg-[var(--color-surface-3)]"
              >
                快捷键: <kbd className="px-2 py-1 text-xs rounded bg-[var(--color-surface-3)]">Cmd</kbd>+<kbd className="px-2 py-1 text-xs rounded bg-[var(--color-surface-3)]">K</kbd>
              </button>
            </div>
          </div>
        </header>

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