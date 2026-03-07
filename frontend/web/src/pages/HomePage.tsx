import { motion } from 'framer-motion';
import {
  TrendingUp,
  Calendar,
  Home,
  Bell,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { TaskList } from '@/components/TaskList';
import { WeatherCard } from '@/components/WeatherCard';
import { HealthCard } from '@/components/HealthCard';
import { FinanceCard } from '@/components/FinanceCard';
import { tasks, weather, healthData, financeData } from '@/data/mockData';

const quickActions = [
  { id: 'stock', label: '股票分析', icon: TrendingUp, color: '#10B981', path: '/stock' },
  { id: 'schedule', label: '日程安排', icon: Calendar, color: '#2563EB', path: '/ai-console' },
  { id: 'life', label: '生活建议', icon: Home, color: '#8B5CF6', path: '/life' },
  { id: 'reminder', label: '智能提醒', icon: Bell, color: '#F59E0B', path: '/settings' },
];

export function HomePage() {
  const today = new Date();
  const hour = today.getHours();
  const greeting = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好';

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#2563EB] via-[#1D4ED8] to-[#06B6D4] p-6"
      >
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white rounded-full blur-3xl transform -translate-x-1/3 translate-y-1/3" />
        </div>

        <div className="relative z-10">
          <div className="flex items-start justify-between">
            <div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="flex items-center gap-2 mb-2"
              >
                <Sparkles className="w-5 h-5 text-yellow-300" />
                <span className="text-blue-100 text-sm">AI助手</span>
              </motion.div>
              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-3xl font-bold text-white mb-2"
              >
                {greeting}，Ruo！
              </motion.h1>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="text-blue-100"
              >
                今天是 {today.toLocaleDateString('zh-CN', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  weekday: 'long'
                })}
              </motion.p>
            </div>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2, type: 'spring' }}
              className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-3xl"
            >
              🤖
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-foreground font-semibold mb-4">快捷操作</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <motion.a
              key={action.id}
              href={action.path}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="p-4 rounded-xl bg-card text-card-foreground border border-border hover:bg-muted transition-all duration-200 group"
            >
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                style={{ backgroundColor: `${action.color}20` }}
              >
                <action.icon className="w-5 h-5" style={{ color: action.color }} />
              </div>
              <p className="text-foreground font-medium text-sm">{action.label}</p>
              <div className="flex items-center gap-1 mt-2 text-muted-foreground text-xs group-hover:text-primary transition-colors">
                <span>进入</span>
                <ArrowRight className="w-3 h-3 transform group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.a>
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Tasks */}
        <div className="lg:col-span-1">
          <TaskList tasks={tasks} />
        </div>

        {/* Right Column - Life Dashboard */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-foreground font-semibold">生活信息看板</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <WeatherCard weather={weather} />
            <HealthCard health={healthData} />
          </div>
          <FinanceCard finance={financeData} />
        </div>
      </div>
    </div>
  );
}
