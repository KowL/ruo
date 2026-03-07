import { motion } from 'framer-motion';
import { Sun, Dumbbell, BookOpen, Brain, Check } from 'lucide-react';
import type { Habit } from '@/types';

interface HabitCardProps {
  habit: Habit;
  onToggle?: () => void;
}

const habitIcons: Record<string, React.ElementType> = {
  'sun': Sun,
  'dumbbell': Dumbbell,
  'book': BookOpen,
  'brain': Brain,
};

export function HabitCard({ habit, onToggle }: HabitCardProps) {
  const Icon = habitIcons[habit.icon] || Sun;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onToggle}
      className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
        habit.completed
          ? 'bg-[#10B981]/10 border-[#10B981]/30'
          : 'bg-[#1E293B] border-[#334155] hover:border-[#475569]'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          habit.completed ? 'bg-[#10B981]/20' : 'bg-[#334155]'
        }`}>
          <Icon className={`w-5 h-5 ${habit.completed ? 'text-[#10B981]' : 'text-[#94A3B8]'}`} />
        </div>
        <div className="flex-1">
          <p className={`font-medium ${habit.completed ? 'text-[#10B981]' : 'text-[#F8FAFC]'}`}>
            {habit.name}
          </p>
          <p className="text-[#94A3B8] text-xs">
            连续 {habit.streak} 天
          </p>
        </div>
        <motion.div
          initial={false}
          animate={{
            scale: habit.completed ? 1 : 0.8,
            opacity: habit.completed ? 1 : 0.3,
          }}
          className={`w-6 h-6 rounded-full flex items-center justify-center ${
            habit.completed ? 'bg-[#10B981]' : 'bg-[#334155]'
          }`}
        >
          <Check className="w-4 h-4 text-white" />
        </motion.div>
      </div>
    </motion.div>
  );
}

interface HabitListProps {
  habits: Habit[];
  onToggle?: (id: string) => void;
}

export function HabitList({ habits, onToggle }: HabitListProps) {
  return (
    <div className="space-y-2">
      {habits.map((habit) => (
        <HabitCard
          key={habit.id}
          habit={habit}
          onToggle={() => onToggle?.(habit.id)}
        />
      ))}
    </div>
  );
}
