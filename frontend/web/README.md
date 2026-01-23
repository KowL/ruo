# Ruo Web 前端

这是 Ruo AI 智能投顾副驾的 Web 前端应用。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 框架**: Tailwind CSS
- **状态管理**: Zustand
- **图表库**: ECharts
- **HTTP 客户端**: Axios
- **路由**: React Router v6

## 功能特性

### ✅ 已实现

1. **持仓管理** (F-02, F-03, F-04)
   - 添加/删除持仓
   - 股票搜索自动补全
   - 实时盈亏计算
   - 策略标签管理

2. **新闻情报** (F-05, F-06)
   - 按股票查看新闻
   - AI 情感分析展示
   - 新闻消息提醒

3. **K线图表** (F-07)
   - 日K/周K/月K 切换
   - 交互式图表
   - 成交量展示

### 🎨 UI/UX 特点

- 现代化设计，简洁美观
- 响应式布局，支持移动端
- 中国股市涨跌颜色（红涨绿跌）
- 流畅的交互动画
- 清晰的数据可视化

## 快速开始

### 安装依赖

```bash
cd /Users/lijun/Project/lijun/ruo/frontend/web
npm install
```

### 开发模式

```bash
npm run dev
```

应用将运行在 `http://localhost:3000`

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
src/
├── api/              # API 服务层
│   ├── client.ts     # Axios 配置
│   ├── portfolio.ts  # 持仓 API
│   ├── stock.ts      # 股票 API
│   └── news.ts       # 新闻 API
├── components/       # 组件
│   ├── common/       # 通用组件
│   ├── portfolio/    # 持仓组件
│   ├── news/         # 新闻组件
│   └── chart/        # 图表组件
├── pages/            # 页面
│   ├── PortfolioPage.tsx
│   ├── NewsPage.tsx
│   └── ChartPage.tsx
├── store/            # 状态管理
│   └── portfolioStore.ts
├── types/            # TypeScript 类型
│   └── index.ts
├── utils/            # 工具函数
│   └── format.ts
├── styles/           # 样式
│   └── index.css
├── App.tsx           # 根组件
└── main.tsx          # 入口文件
```

## API 配置

开发环境下，API 请求会被代理到 `http://localhost:8000`。

如需修改后端地址，请编辑 `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:8000',
      changeOrigin: true,
    },
  },
}
```

## 环境要求

- Node.js >= 16
- npm >= 8

## 开发规范

- 使用 TypeScript 进行类型检查
- 遵循 ESLint 代码规范
- 使用 Prettier 格式化代码
- 组件采用函数式 + Hooks
- 优先使用 Tailwind CSS 工具类

## 待优化

- [ ] 添加单元测试
- [ ] 添加 E2E 测试
- [ ] 优化性能（虚拟列表、懒加载等）
- [ ] 添加错误边界
- [ ] 完善错误提示
- [ ] 添加离线缓存

## License

MIT
