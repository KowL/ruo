import { motion } from 'framer-motion';
import { Check, ChevronRight } from 'lucide-react';
import type { Task } from '@/types';

interface TaskListProps {
  tasks: Task[];
  onToggle?: (id: string) => void;
}

export function TaskList({ tasks, onToggle }: TaskListProps) {
  const completedCount = tasks.filter(t => t.completed).length;
  const progress = (completedCount / tasks.length) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="p-5 rounded-xl bg-[#1E293B] border border-[#334155]"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#F8FAFC] font-semibold">今日任务</h3>
        <span className="text-[#94A3B8] text-sm">
          {completedCount}/{tasks.length}
        </span>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="h-2 bg-[#334155] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="h-full bg-gradient-to-r from-[#2563EB] to-[#06B6D4] rounded-full"
          />
        </div>
        <p className="text-[#94A3B8] text-xs mt-2">
          已完成 {Math.round(progress)}%，继续保持！
        </p>
      </div>

      {/* Task List */}
      <div className="space-y-2">
        {tasks.slice(0, 5).map((task, index) => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            onClick={() => onToggle?.(task.id)}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-[#334155]/50 cursor-pointer transition-colors"
          >
            <motion.div
              whileTap={{ scale: 0.9 }}
              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                task.completed
                  ? 'bg-[#10B981] border-[#10B981]'
                  : 'border-[#475569]'
              }`}
            >
              {task.completed && <Check className="w-3 h-3 text-white" />}
            </motion.div>
            <span className={`flex-1 text-sm ${
              task.completed ? 'text-[#94A3B8] line-through' : 'text-[#F8FAFC]'
            }`}>
              {task.title}
            </span>
            <span className="text-[#94A3B8] text-xs px-2 py-0.5 rounded-full bg-[#334155]">
              {task.category}
            </span>
          </motion.div>
        ))}
      </div>

      {/* View All */}
      <button className="w-full mt-4 flex items-center justify-center gap-1 text-[#2563EB] text-sm hover:underline">
        查看全部
        <ChevronRight className="w-4 h-4" />
      </button>
    </motion.div>
  );
}
