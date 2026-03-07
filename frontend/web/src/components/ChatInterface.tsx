import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, MoreVertical } from 'lucide-react';
import type { Message, Agent } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface ChatInterfaceProps {
  messages: Message[];
  currentAgent: Agent;
  onSendMessage?: (content: string) => void;
}

export function ChatInterface({ messages, currentAgent, onSendMessage }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage?.(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#1E293B] rounded-xl border border-[#334155] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#334155]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#2563EB]/20 to-[#06B6D4]/20 flex items-center justify-center text-xl">
            {currentAgent.avatar}
          </div>
          <div>
            <p className="text-[#F8FAFC] font-medium">{currentAgent.name}</p>
            <p className="text-[#94A3B8] text-xs">{currentAgent.description}</p>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="text-[#94A3B8]">
          <MoreVertical className="w-5 h-5" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2.5 rounded-2xl ${
                    message.sender === 'user'
                      ? 'bg-[#2563EB] text-white rounded-br-md'
                      : 'bg-[#334155] text-[#F8FAFC] rounded-bl-md'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={`text-[10px] mt-1 ${
                    message.sender === 'user' ? 'text-blue-200' : 'text-[#94A3B8]'
                  }`}>
                    {message.timestamp.toLocaleTimeString('zh-CN', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-[#334155]">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="text-[#94A3B8] hover:text-[#F8FAFC]"
          >
            <Mic className="w-5 h-5" />
          </Button>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`给 ${currentAgent.name} 发送消息...`}
            className="flex-1 bg-[#334155] border-[#475569] text-[#F8FAFC] placeholder:text-[#94A3B8]"
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="bg-[#2563EB] hover:bg-[#1D4ED8] text-white"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
