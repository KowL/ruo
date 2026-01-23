import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8300',
        changeOrigin: true,
        configure: (proxy, options) => {
        proxy.on('proxyReq', (proxyReq, req, res) => {
          console.log('发送请求到后端:', req.method, options.target + req.url);
        });
        proxy.on('proxyRes', (proxyRes, req, res) => {
          console.log('接收到后端响应:', proxyRes.statusCode, req.url);
        });
      },
      },
    },
  },
})
