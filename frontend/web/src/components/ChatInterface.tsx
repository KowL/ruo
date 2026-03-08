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
  disabled?: boolean;
}

export function ChatInterface({ messages, currentAgent, onSendMessage, disabled = false }: ChatInterfaceProps) {
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
    <div className="flex flex-col h-full glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 bg-white/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-xl shadow-sm">
            {currentAgent.avatar}
          </div>
          <div>
            <p className="text-foreground font-medium">{currentAgent.name}</p>
            <p className="text-muted-foreground text-xs">{currentAgent.description}</p>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="text-muted-foreground">
          <MoreVertical className="w-5 h-5" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4 bg-transparent">
        <div className="space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'
                  }`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2.5 rounded-2xl shadow-sm ${message.sender === 'user'
                      ? 'bg-primary text-primary-foreground rounded-br-md'
                      : 'bg-white text-foreground border border-border/50 rounded-bl-md'
                    }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={`text-[10px] mt-1 ${message.sender === 'user' ? 'text-primary-foreground/80' : 'text-muted-foreground'
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
      <div className="p-4 border-t border-border/60 bg-white/50 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground"
          >
            <Mic className="w-5 h-5" />
          </Button>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`给 ${currentAgent.name} 发送消息...`}
            disabled={disabled}
            className="flex-1 bg-white border-border/60 text-foreground placeholder:text-muted-foreground focus-visible:ring-primary shadow-sm"
          />
          <Button
            onClick={handleSend}
            disabled={disabled || !inputValue.trim()}
            className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
          >
            <Send className="w-4 h-4 ml-[-2px]" />
          </Button>
        </div>
      </div>
    </div>
  );
}
