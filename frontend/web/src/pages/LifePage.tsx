import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Calendar, CheckCircle2, Circle } from 'lucide-react';
import { WeatherCard } from '@/components/WeatherCard';
import { HealthCard } from '@/components/HealthCard';
import { FinanceCard } from '@/components/FinanceCard';
import { HabitList } from '@/components/HabitCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { weather, healthData, financeData, habits as initialHabits } from '@/data/mockData';
import type { Habit } from '@/types';

const scheduleData = [
  { id: '1', title: '团队周会', time: '09:00', type: 'work', completed: true },
  { id: '2', title: '项目评审', time: '14:00', type: 'work', completed: false },
  { id: '3', title: '健身运动', time: '18:00', type: 'health', completed: false },
  { id: '4', title: '阅读学习', time: '20:00', type: 'study', completed: false },
];

export function LifePage() {
  const [habits, setHabits] = useState<Habit[]>(initialHabits);

  const handleToggleHabit = (id: string) => {
    setHabits(prev => prev.map(h => h.id === id ? { ...h, completed: !h.completed } : h));
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'work': return 'bg-[#2563EB]/20 text-[#2563EB]';
      case 'health': return 'bg-[#10B981]/20 text-[#10B981]';
      case 'study': return 'bg-[#8B5CF6]/20 text-[#8B5CF6]';
      default: return 'bg-[#94A3B8]/20 text-[#94A3B8]';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'work': return '工作';
      case 'health': return '健康';
      case 'study': return '学习';
      default: return '其他';
    }
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-[#F8FAFC]">生活中心</h1>
          <p className="text-[#94A3B8]">一站式生活管理平台</p>
        </div>
        <Button className="bg-[#2563EB] hover:bg-[#1D4ED8]">
          <Plus className="w-4 h-4 mr-2" />
          快速记录
        </Button>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <WeatherCard weather={weather} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <HealthCard health={healthData} />
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <FinanceCard finance={financeData} />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
          <div className="p-5 rounded-xl bg-[#1E293B] border border-[#334155]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#F8FAFC] font-semibold">习惯追踪</h3>
              <Badge className="bg-[#10B981]/20 text-[#10B981]">
                {habits.filter(h => h.completed).length}/{habits.length}
              </Badge>
            </div>
            <HabitList habits={habits} onToggle={handleToggleHabit} />
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}>
          <div className="p-5 rounded-xl bg-[#1E293B] border border-[#334155]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-[#2563EB]" />
                <h3 className="text-[#F8FAFC] font-semibold">今日日程</h3>
              </div>
              <Badge className="bg-[#2563EB]/20 text-[#2563EB]">
                {scheduleData.filter(s => s.completed).length}/{scheduleData.length}
              </Badge>
            </div>
            <ScrollArea className="h-[280px]">
              <div className="space-y-3">
                {scheduleData.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.05 }}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-[#334155]/50 transition-colors"
                  >
                    <div className="text-[#94A3B8] text-sm font-mono w-12">{item.time}</div>
                    <div className="flex-1">
                      <p className={`text-sm ${item.completed ? 'text-[#94A3B8] line-through' : 'text-[#F8FAFC]'}`}>
                        {item.title}
                      </p>
                    </div>
                    <Badge className={getTypeColor(item.type)}>{getTypeLabel(item.type)}</Badge>
                    {item.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                    ) : (
                      <Circle className="w-5 h-5 text-[#475569]" />
                    )}
                  </motion.div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
