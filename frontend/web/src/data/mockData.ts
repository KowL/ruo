import type { Agent, Stock, Task, Weather, HealthData, FinanceData, Habit, Message } from '@/types';

// 智能体数据
export const agents: Agent[] = [
  {
    id: 'ruo',
    name: 'Ruo',
    avatar: '🤖',
    description: '主助手，统筹协调各智能体',
    status: 'online',
  },
  {
    id: 'stock',
    name: '股票助手',
    avatar: '📈',
    description: '股票分析、投资建议、行情解读',
    status: 'online',
  },
  {
    id: 'schedule',
    name: '日程助手',
    avatar: '📅',
    description: '日程管理、任务提醒、时间规划',
    status: 'idle',
  },
  {
    id: 'life',
    name: '生活助手',
    avatar: '🏠',
    description: '生活建议、健康提醒、记账分析',
    status: 'idle',
  },
  {
    id: 'data',
    name: '数据分析师',
    avatar: '📊',
    description: '数据分析、报表生成、趋势预测',
    status: 'busy',
  },
];

// 股票数据
export const stocks: Stock[] = [
  {
    id: '1',
    name: '平安银行',
    code: '000001',
    price: 12.58,
    change: 0.23,
    changePercent: 1.86,
    volume: 125800,
  },
  {
    id: '2',
    name: '万科A',
    code: '000002',
    price: 15.32,
    change: -0.15,
    changePercent: -0.97,
    volume: 89300,
  },
  {
    id: '3',
    name: '国农科技',
    code: '000004',
    price: 28.65,
    change: 0.89,
    changePercent: 3.21,
    volume: 56200,
  },
  {
    id: '4',
    name: '深科技',
    code: '000021',
    price: 18.92,
    change: 0.45,
    changePercent: 2.44,
    volume: 102400,
  },
  {
    id: '5',
    name: '神州数码',
    code: '000034',
    price: 32.15,
    change: -0.28,
    changePercent: -0.86,
    volume: 67800,
  },
];

// 任务数据
export const tasks: Task[] = [
  { id: '1', title: '完成股票分析报告', completed: true, category: '工作' },
  { id: '2', title: '预约体检', completed: true, category: '健康' },
  { id: '3', title: '购买生活用品', completed: false, category: '生活' },
  { id: '4', title: '学习AI新技术', completed: false, category: '学习' },
  { id: '5', title: '整理财务报表', completed: false, category: '财务' },
];

// 天气数据
export const weather: Weather = {
  current: {
    temp: 22,
    condition: '多云',
    icon: 'cloud',
  },
  forecast: [
    { day: '周一', temp: 23, condition: '晴' },
    { day: '周二', temp: 21, condition: '多云' },
    { day: '周三', temp: 19, condition: '小雨' },
    { day: '周四', temp: 20, condition: '多云' },
    { day: '周五', temp: 24, condition: '晴' },
  ],
};

// 健康数据
export const healthData: HealthData = {
  steps: 8432,
  stepsGoal: 10000,
  sleep: 7.2,
  heartRate: 72,
};

// 财务数据
export const financeData: FinanceData = {
  monthlyExpense: 3250,
  monthlyBudget: 5000,
  categories: [
    { name: '餐饮', amount: 1200, color: '#EF4444' },
    { name: '交通', amount: 450, color: '#F59E0B' },
    { name: '购物', amount: 800, color: '#3B82F6' },
    { name: '娱乐', amount: 500, color: '#8B5CF6' },
    { name: '其他', amount: 300, color: '#6B7280' },
  ],
};

// 习惯数据
export const habits: Habit[] = [
  { id: '1', name: '早起', streak: 15, completed: true, icon: 'sun' },
  { id: '2', name: '运动', streak: 8, completed: false, icon: 'dumbbell' },
  { id: '3', name: '阅读', streak: 23, completed: true, icon: 'book' },
  { id: '4', name: '冥想', streak: 5, completed: false, icon: 'brain' },
];

// 消息数据
export const messages: Message[] = [
  {
    id: '1',
    content: '你好！我是Ruo，你的AI助手。有什么可以帮助你的吗？',
    sender: 'agent',
    timestamp: new Date('2026-03-07T09:00:00'),
    agentId: 'ruo',
  },
  {
    id: '2',
    content: '帮我看看今天的股票行情',
    sender: 'user',
    timestamp: new Date('2026-03-07T09:01:00'),
  },
  {
    id: '3',
    content: '今天市场整体表现平稳，你的持仓中有3只股票上涨，2只下跌。需要我详细分析一下吗？',
    sender: 'agent',
    timestamp: new Date('2026-03-07T09:01:30'),
    agentId: 'stock',
  },
];

// 市场指数数据
export const marketIndices = [
  { name: '上证指数', value: 3047.36, change: 0.42 },
  { name: '深证成指', value: 9412.56, change: 0.58 },
  { name: '创业板指', value: 1823.24, change: -0.21 },
  { name: '科创50', value: 815.63, change: 1.23 },
];

// 资产数据
export const portfolioData = {
  totalAssets: 10500,
  todayProfit: 0,
  todayProfitPercent: 0,
  holdings: 1,
};

// 图表数据
export const chartData = Array.from({ length: 24 }, (_, i) => ({
  time: `${9 + Math.floor(i / 2)}:${i % 2 === 0 ? '00' : '30'}`,
  price: 12.3 + Math.random() * 0.5,
  volume: Math.floor(Math.random() * 10000),
}));
