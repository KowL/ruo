import { motion } from 'framer-motion';
import type { Agent } from '@/types';

interface AgentCardProps {
  agent: Agent;
  isActive?: boolean;
  onClick?: () => void;
}

export function AgentCard({ agent, isActive = false, onClick }: AgentCardProps) {
  const statusColors = {
    online: 'bg-[#10B981]',
    busy: 'bg-[#F59E0B]',
    idle: 'bg-[#94A3B8]',
    offline: 'bg-[#475569]',
  };

  const statusLabels = {
    online: '在线',
    busy: '忙碌',
    idle: '待命中',
    offline: '离线',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`p-4 rounded-xl bg-[#1E293B] border cursor-pointer transition-all duration-200 ${
        isActive
          ? 'border-[#2563EB] shadow-[0_0_20px_rgba(37,99,235,0.3)]'
          : 'border-[#334155] hover:border-[#475569]'
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="relative">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#2563EB]/20 to-[#06B6D4]/20 flex items-center justify-center text-2xl">
            {agent.avatar}
          </div>
          {/* Status Indicator */}
          <motion.div
            className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-[#1E293B] ${statusColors[agent.status]}`}
            animate={
              agent.status === 'online'
                ? {
                    scale: [1, 1.2, 1],
                    opacity: [1, 0.7, 1],
                  }
                : agent.status === 'busy'
                ? {
                    opacity: [1, 0.5, 1],
                  }
                : {}
            }
            transition={
              agent.status === 'online'
                ? {
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }
                : agent.status === 'busy'
                ? {
                    duration: 1,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }
                : {}
            }
          />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-[#F8FAFC] font-semibold text-base">{agent.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              agent.status === 'online' ? 'bg-[#10B981]/20 text-[#10B981]' :
              agent.status === 'busy' ? 'bg-[#F59E0B]/20 text-[#F59E0B]' :
              'bg-[#94A3B8]/20 text-[#94A3B8]'
            }`}>
              {statusLabels[agent.status]}
            </span>
          </div>
          <p className="text-[#94A3B8] text-sm line-clamp-2">{agent.description}</p>
        </div>
      </div>
    </motion.div>
  );
}
