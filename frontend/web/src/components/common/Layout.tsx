import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '持仓', icon: '💼' },
    { path: '/news', label: '情报', icon: '📰' },
    { path: '/chart', label: 'K线', icon: '📈' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部导航栏 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🐉</span>
              <h1 className="text-xl font-bold text-primary-600">Ruo AI 投顾</h1>
            </div>
            <div className="text-sm text-gray-500">MVP v0.1</div>
          </div>
        </div>
      </header>

      {/* 主体内容 */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {children}
      </main>

      {/* 底部导航 */}
      <nav className="bg-white border-t border-gray-200 sticky bottom-0 md:relative">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-around py-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex flex-col items-center py-2 px-4 rounded-lg transition-colors',
                  location.pathname === item.path
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
                )}
              >
                <span className="text-2xl mb-1">{item.icon}</span>
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Layout;
