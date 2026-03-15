import { motion } from 'framer-motion';
import {
  TrendingUp,
  Calendar,
  Home,
  Bell,
  Sparkles,
  ArrowRight,
  Bot
} from 'lucide-react';
import { TaskList } from '@/components/TaskList';
import { NewsFlashList } from '@/components/news/NewsFlashList';
import { tasks } from '@/data/mockData';
import { Send } from 'lucide-react';

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
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-amber-500 via-orange-400 to-amber-300 p-8 shadow-sm"
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
                <Sparkles className="w-5 h-5 text-yellow-100" />
                <span className="text-orange-50 text-sm font-medium">工作台</span>
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
                className="text-orange-50/90"
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
              className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center overflow-hidden"
            >
              <img src="/favicon.svg" alt="Ruo AI" className="w-10 h-10 object-contain" />
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
              className="p-4 rounded-xl glass-card hover:bg-white transition-all duration-200 group"
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
        {/* Right Column - News Flash */}
        <div className="lg:col-span-2">
          <NewsFlashList />
        </div>
      </div>

      {/* Global AI Input Box (Floating) */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-2xl px-4 z-40"
      >
        <div className="glass-card flex items-center p-2 pl-4 pr-2 rounded-full shadow-lg border border-border/60">
          <Bot className="w-5 h-5 text-primary mr-3" />
          <input
            type="text"
            placeholder="有什么我可以帮你的吗？ (例如: 今天有什么日程, 给飞龙股份写一篇短平)"
            className="flex-1 bg-transparent border-none focus:ring-0 text-foreground placeholder:text-muted-foreground outline-none text-sm"
          />
          <button className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors shadow-sm ml-2">
            <Send className="w-4 h-4 ml-[-2px]" />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
