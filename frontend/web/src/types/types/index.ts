// 智能体类型
export interface Agent {
  id: string;
  name: string;
  avatar: string;
  description: string;
  status: 'online' | 'busy' | 'idle' | 'offline';
}

// 股票类型
export interface Stock {
  id: string;
  name: string;
  code: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

// 任务类型
export interface Task {
  id: string;
  title: string;
  completed: boolean;
  category: string;
}

// 天气类型
export interface Weather {
  current: {
    temp: number;
    condition: string;
    icon: string;
  };
  forecast: Array<{
    day: string;
    temp: number;
    condition: string;
  }>;
}

// 健康数据类型
export interface HealthData {
  steps: number;
  stepsGoal: number;
  sleep: number;
  heartRate: number;
}

// 记账数据类型
export interface FinanceData {
  monthlyExpense: number;
  monthlyBudget: number;
  categories: Array<{
    name: string;
    amount: number;
    color: string;
  }>;
}

// 习惯类型
export interface Habit {
  id: string;
  name: string;
  streak: number;
  completed: boolean;
  icon: string;
}

// 消息类型
export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  agentId?: string;
}

// 导航项类型
export interface NavItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}
