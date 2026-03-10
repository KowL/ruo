/**
 * 设置 Store
 * 使用 localStorage 存储用户配置
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface OpenClawConfig {
  gatewayWsUrl: string;
  token: string;
  enabled: boolean;
}

interface SettingsState {
  // OpenClaw 配置
  openclaw: OpenClawConfig;

  // Actions
  setOpenClawConfig: (config: Partial<OpenClawConfig>) => void;
  resetOpenClawConfig: () => void;
}

const defaultOpenClawConfig: OpenClawConfig = {
  gatewayWsUrl: 'ws://localhost:18789',
  token: '',
  enabled: true,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      openclaw: defaultOpenClawConfig,

      setOpenClawConfig: (config) =>
        set((state) => ({
          openclaw: { ...state.openclaw, ...config },
        })),

      resetOpenClawConfig: () =>
        set(() => ({
          openclaw: defaultOpenClawConfig,
        })),
    }),
    {
      name: 'ruo-settings',
    }
  )
);
