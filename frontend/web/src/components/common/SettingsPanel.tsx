import React, { useState } from 'react';
import clsx from 'clsx';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SettingsState {
  usMarket: boolean;
  privacyMode: boolean;
  darkMode: boolean;
  notifications: boolean;
}

const SettingsPanel: React.FC<SettingsProps> = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState<SettingsState>({
    usMarket: false,
    privacyMode: false,
    darkMode: true,
    notifications: true,
  });

  const handleSettingChange = (key: keyof SettingsState, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleReset = () => {
    setSettings({
      usMarket: false,
      privacyMode: false,
      darkMode: true,
      notifications: true,
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 遮罩层 */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
      />

      {/* 设置面板 */}
      <div className="fixed bottom-0 right-0 w-[400px] h-full shadow-2xl z-50">
        <div
          className="h-full flex flex-col"
          style={{ backgroundColor: 'var(--color-surface-2)' }}
        >
          {/* 头部 */}
          <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-surface-4)' }}>
            <h2 className="text-lg font-bold">设置</h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleReset}
                className="text-sm hover:opacity-80 px-3 py-1 rounded"
                style={{ color: 'var(--color-text-secondary)', backgroundColor: 'var(--color-surface-3)' }}
              >
                重置
              </button>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:opacity-70"
              >
                ✕
              </button>
            </div>
          </div>

          {/* 设置选项 */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* 市场设置 */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>市场设置</h3>

                {/* 涨跌颜色设置 */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">市场模式</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      {settings.usMarket ? '美股红涨绿跌' : 'A股红涨绿跌'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('usMarket', !settings.usMarket)}
                    className={clsx(
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                      settings.usMarket ? '' : ''
                    )}
                    style={{ backgroundColor: settings.usMarket ? 'var(--color-profit-up)' : 'var(--color-loss-up)' }}
                  >
                    <span
                      className={clsx(
                        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                        settings.usMarket ? 'translate-x-6' : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>
              </div>

              {/* 隐私设置 */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>隐私设置</h3>

                {/* 隐私模式 */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">隐私模式</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      模糊显示所有金额数据
                    </p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('privacyMode', !settings.privacyMode)}
                    className={clsx(
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                      settings.privacyMode ? '' : ''
                    )}
                    style={{ backgroundColor: settings.privacyMode ? 'var(--color-brand)' : 'var(--color-surface-3)' }}
                  >
                    <span
                      className={clsx(
                        'inline-block h-4 w-4 transform rounded-full bg-black transition-transform',
                        settings.privacyMode ? 'translate-x-6' : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>

                {/* 隐私模式预览 */}
                {settings.privacyMode && (
                  <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--color-surface-3)' }}>
                    <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>预览效果:</p>
                    <div className="mt-2 space-y-1">
                      <div className="flex justify-between">
                        <span>总资产</span>
                        <span className="blur-sm">¥125,800.50</span>
                      </div>
                      <div className="flex justify-between">
                        <span>今日盈亏</span>
                        <span className="blur-sm">+¥2,350.80</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 显示设置 */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>显示设置</h3>

                {/* 深色模式 */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">深色模式</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      使用极简黑色主题
                    </p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('darkMode', !settings.darkMode)}
                    className={clsx(
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                      settings.darkMode ? '' : ''
                    )}
                    style={{ backgroundColor: settings.darkMode ? 'var(--color-brand)' : 'var(--color-surface-3)' }}
                  >
                    <span
                      className={clsx(
                        'inline-block h-4 w-4 transform rounded-full bg-black transition-transform',
                        settings.darkMode ? 'translate-x-6' : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>

                {/* 通知设置 */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">推送通知</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      价格提醒和新闻推送
                    </p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('notifications', !settings.notifications)}
                    className={clsx(
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                      settings.notifications ? '' : ''
                    )}
                    style={{ backgroundColor: settings.notifications ? 'var(--color-brand)' : 'var(--color-surface-3)' }}
                  >
                    <span
                      className={clsx(
                        'inline-block h-4 w-4 transform rounded-full bg-black transition-transform',
                        settings.notifications ? 'translate-x-6' : 'translate-x-1'
                      )}
                    />
                  </button>
                </div>
              </div>

              {/* 其他设置 */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>其他</h3>

                <button className="w-full p-3 rounded-lg text-left hover:opacity-70 transition-opacity">
                  <p className="font-medium">关于 Ruo</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>版本 1.0.0</p>
                </button>

                <button className="w-full p-3 rounded-lg text-left hover:opacity-70 transition-opacity">
                  <p className="font-medium">用户反馈</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>帮助我们改进产品</p>
                </button>

                <button className="w-full p-3 rounded-lg text-left hover:opacity-70 transition-opacity" style={{ color: 'var(--color-profit-up)' }}>
                  <p className="font-medium">退出登录</p>
                </button>
              </div>
            </div>
          </div>

          {/* 底部 */}
          <div className="p-4 border-t text-center" style={{ borderColor: 'var(--color-surface-4)' }}>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              © 2024 Ruo AI 智能投顾副驾
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsPanel;
