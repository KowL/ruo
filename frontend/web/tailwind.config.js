/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 深空暗黑主题色彩体系
      colors: {
        // 背景色 (Backgrounds)
        'surface-1': '#0F1115', // Global BG
        'surface-2': '#181B21', // Cards/Panels
        'surface-3': '#2A2E35', // Hover/Active

        // 品牌与 AI 色 (Brand & AI)
        'ruo-purple': '#7C3AED', // AI 核心色
        'electric-cyan': '#06B6D4', // 高亮/强调

        // 功能色 (Functional)
        'profit-up': '#F63538', // A股红 (涨/利好)
        'profit-down': '#10B981', // 美股绿 (涨/利好)
        'loss-up': '#10B981', // A股绿 (跌/利空)
        'loss-down': '#F63538', // 美股红 (跌/利空)
        'warning': '#F59E0B', // 预警

        // 文本色 (Typography)
        'text-primary': '#F9FAFB', // 高亮白
        'text-secondary': '#9CA3AF', // 冷灰

        // 保留原有的颜色体系作为备用
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
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
