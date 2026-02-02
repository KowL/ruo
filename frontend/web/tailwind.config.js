/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 极简黑色主题色彩体系
      colors: {
        // 背景色 (Backgrounds)
        'surface-1': '#000000', // 全局背景 - 纯黑
        'surface-2': '#0A0A0A', // 卡片/面板
        'surface-3': '#1A1A1A', // 悬停/激活
        'surface-4': '#2A2A2A', // 边框/分隔

        // 品牌色 (Brand) - 极简白色
        'brand': '#FFFFFF', // 品牌白

        // 功能色 (Functional)
        'profit-up': '#FF3B30', // A股红 (涨)
        'profit-down': '#34C759', // 美股绿 (涨)
        'loss-up': '#34C759', // A股绿 (跌)
        'loss-down': '#FF3B30', // 美股红 (跌)
        'warning': '#FF9500', // 预警

        // 文本色 (Typography)
        'text-primary': '#FFFFFF', // 主文本
        'text-secondary': '#8E8E93', // 次要文本
        'text-muted': '#3A3A3C', // 弱化文本
      },

      // 字体配置
      fontFamily: {
        sans: ['PingFang SC', 'Microsoft YaHei', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'IBM Plex Mono', 'Roboto Mono', 'monospace'],
      },

      // 间距配置
      spacing: {
        'sidebar-collapsed': '64px',
        'sidebar-expanded': '240px',
        'copilot-width': '320px',
      },

      // 动画配置
      animation: {
        'pulse-wave': 'pulse-wave 1.5s ease-in-out infinite',
        'data-flash': 'data-flash 0.3s ease-in-out',
      },

      keyframes: {
        'pulse-wave': {
          '0%, 100%': {
            transform: 'scale(0.95)',
            opacity: '0.8',
          },
          '50%': {
            transform: 'scale(1.05)',
            opacity: '1',
          },
        },
        'data-flash': {
          '0%': {
            backgroundColor: 'rgba(246, 53, 56, 0.2)',
          },
          '100%': {
            backgroundColor: 'transparent',
          },
        },
      },
    },
  },
  plugins: [],
}
