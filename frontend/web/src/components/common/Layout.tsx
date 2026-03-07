import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import CopilotPanel from './CopilotPanel';
import SettingsPanel from './SettingsPanel';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
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

  return (
    <>
      <div className="w-full">
        {children}
      </div>

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
    </>
  );
};

export default Layout;
