import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, MessageSquare, Zap } from 'lucide-react';
import { AgentCard } from '@/components/AgentCard';
import { ChatInterface } from '@/components/ChatInterface';
import type { Agent, Message } from '@/types';
import { agents, messages as initialMessages } from '@/data/mockData';

export function AIConsolePage() {
  const [selectedAgent, setSelectedAgent] = useState<Agent>(agents[0]);
  const [messages, setMessages] = useState<Message[]>(initialMessages);

  const handleSendMessage = (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);

    // Simulate agent response
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        content: `我是${selectedAgent.name}，收到你的消息："${content}"。我正在处理中...`,
        sender: 'agent',
        timestamp: new Date(),
        agentId: selectedAgent.id,
      };
      setMessages(prev => [...prev, response]);
    }, 1000);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#06B6D4] flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#F8FAFC]">AI控制台</h1>
            <p className="text-[#94A3B8] text-sm">多智能体协同工作中心</p>
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-3 gap-4 mb-6"
      >
        <div className="p-4 rounded-xl bg-[#1E293B] border border-[#334155]">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="w-4 h-4 text-[#2563EB]" />
            <span className="text-[#94A3B8] text-sm">在线智能体</span>
          </div>
          <p className="text-2xl font-bold text-[#F8FAFC]">5</p>
        </div>
        <div className="p-4 rounded-xl bg-[#1E293B] border border-[#334155]">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-[#10B981]" />
            <span className="text-[#94A3B8] text-sm">今日对话</span>
          </div>
          <p className="text-2xl font-bold text-[#F8FAFC]">24</p>
        </div>
        <div className="p-4 rounded-xl bg-[#1E293B] border border-[#334155]">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-[#F59E0B]" />
            <span className="text-[#94A3B8] text-sm">处理任务</span>
          </div>
          <p className="text-2xl font-bold text-[#F8FAFC]">12</p>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
        {/* Agents Grid */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col"
        >
          <h2 className="text-[#F8FAFC] font-semibold mb-4">智能体列表</h2>
          <div className="grid grid-cols-1 gap-3 overflow-auto">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.05 }}
              >
                <AgentCard
                  agent={agent}
                  isActive={selectedAgent.id === agent.id}
                  onClick={() => setSelectedAgent(agent)}
                />
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Chat Interface */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="min-h-[400px] lg:min-h-0"
        >
          <h2 className="text-[#F8FAFC] font-semibold mb-4">对话窗口</h2>
          <div className="h-[calc(100%-2rem)]">
            <ChatInterface
              messages={messages.filter(m => 
                m.sender === 'user' || 
                !m.agentId || 
                m.agentId === selectedAgent.id
              )}
              currentAgent={selectedAgent}
              onSendMessage={handleSendMessage}
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}
