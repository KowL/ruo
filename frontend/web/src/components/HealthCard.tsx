import { motion } from 'framer-motion';
import { Footprints, Moon, Heart, Flame } from 'lucide-react';
import type { HealthData } from '@/types';

interface HealthCardProps {
  health: HealthData;
}

export function HealthCard({ health }: HealthCardProps) {
  const stepsPercent = Math.min((health.steps / health.stepsGoal) * 100, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="p-5 rounded-xl bg-[#1E293B] border border-[#334155]"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#F8FAFC] font-semibold">健康数据</h3>
        <Flame className="w-5 h-5 text-[#F59E0B]" />
      </div>

      {/* Steps */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Footprints className="w-4 h-4 text-[#10B981]" />
            <span className="text-[#94A3B8] text-sm">今日步数</span>
          </div>
          <span className="text-[#F8FAFC] font-mono font-semibold">
            {health.steps.toLocaleString()}
          </span>
        </div>
        <div className="h-2 bg-[#334155] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${stepsPercent}%` }}
            transition={{ duration: 1, delay: 0.3 }}
            className="h-full bg-gradient-to-r from-[#10B981] to-[#06B6D4] rounded-full"
          />
        </div>
        <p className="text-[#94A3B8] text-xs mt-1">目标: {health.stepsGoal.toLocaleString()}步</p>
      </div>

      {/* Sleep & Heart Rate */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 rounded-lg bg-[#334155]/30">
          <div className="flex items-center gap-2 mb-1">
            <Moon className="w-4 h-4 text-[#8B5CF6]" />
            <span className="text-[#94A3B8] text-xs">睡眠</span>
          </div>
          <p className="text-[#F8FAFC] font-mono font-semibold">{health.sleep}h</p>
        </div>
        <div className="p-3 rounded-lg bg-[#334155]/30">
          <div className="flex items-center gap-2 mb-1">
            <Heart className="w-4 h-4 text-[#EF4444]" />
            <span className="text-[#94A3B8] text-xs">心率</span>
          </div>
          <p className="text-[#F8FAFC] font-mono font-semibold">{health.heartRate} <span className="text-xs text-[#94A3B8]">bpm</span></p>
        </div>
      </div>
    </motion.div>
  );
}
