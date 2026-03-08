import { motion } from 'framer-motion';
import type { Agent } from '@/types';

interface AgentCardProps {
  agent: Agent;
  isActive?: boolean;
  onClick?: () => void;
}

export function AgentCard({ agent, isActive = false, onClick }: AgentCardProps) {
  const statusColors = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    idle: 'bg-slate-400',
    offline: 'bg-slate-500',
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
      className={`p-4 rounded-xl glass-card cursor-pointer transition-all duration-200 ${isActive
          ? 'ring-2 ring-primary border-transparent bg-white shadow-md'
          : 'hover:bg-white/80'
        }`}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="relative">
          <div className="w-14 h-14 rounded-full bg-orange-100 flex items-center justify-center text-2xl shadow-sm">
            {agent.avatar}
          </div>
          {/* Status Indicator */}
          <motion.div
            className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-white ${statusColors[agent.status]}`}
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
            <h3 className="text-foreground font-semibold text-base">{agent.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${agent.status === 'online' ? 'bg-emerald-100 text-emerald-700' :
                agent.status === 'busy' ? 'bg-amber-100 text-amber-700' :
                  'bg-slate-100 text-slate-500'
              }`}>
              {statusLabels[agent.status]}
            </span>
          </div>
          <p className="text-muted-foreground text-sm line-clamp-2">{agent.description}</p>
        </div>
      </div>
    </motion.div>
  );
}
