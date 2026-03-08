import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Bot, MessageSquare, Zap, Loader2 } from 'lucide-react';
import { AgentCard } from '@/components/AgentCard';
import { ChatInterface } from '@/components/ChatInterface';
import * as openclaw from '@/api/openclaw';
import type { Message, OpenClawAgent } from '@/types';

export function AIConsolePage() {
  const [agents, setAgents] = useState<OpenClawAgent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<OpenClawAgent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 加载 Agents 列表
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await openclaw.listAgents();
      if (response.status === 'success' && response.data) {
        setAgents(response.data);
        if (response.data.length > 0) {
          setSelectedAgent(response.data[0]);
        }
      }
    } catch (error) {
      console.error('加载 Agents 失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedAgent || sending) return;

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // 添加空的消息用于流式输出
    const tempAssistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      sender: 'agent',
      timestamp: new Date(),
      agentId: selectedAgent.id,
    };
    setMessages(prev => [...prev, tempAssistantMessage]);

    setSending(true);

    try {
      // 使用流式 API
      const response = await fetch(`/api/v1/openclaw/agents/${selectedAgent.id}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法读取响应');
      }

      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'chunk' && data.content) {
                fullContent += data.content;
                setMessages(prev => 
                  prev.map((msg, idx) => 
                    idx === prev.length - 1 
                      ? { ...msg, content: fullContent }
                      : msg
                  )
                );
              } else if (data.type === 'start' && data.sessionId) {
                setSessionId(data.sessionId);
              } else if (data.type === 'end') {
                // 流结束
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // 请求被取消
        return;
      }
      console.error('发送消息失败:', error);
      // 更新最后一条消息为错误消息
      setMessages(prev => 
        prev.map((msg, idx) => 
          idx === prev.length - 1 
            ? { ...msg, content: '抱歉，发送消息失败: ' + error.message }
            : msg
        )
      );
    } finally {
      setSending(false);
    }
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
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-400 flex items-center justify-center shadow-sm">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">AI控制台</h1>
            <p className="text-muted-foreground text-sm">多智能体协同工作中心</p>
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
        <div className="p-4 glass-card border-none hover:bg-white/90 transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="w-4 h-4 text-blue-500" />
            <span className="text-muted-foreground text-sm">在线智能体</span>
          </div>
          <p className="text-2xl font-bold text-foreground">{agents.length || '-'}</p>
        </div>
        <div className="p-4 glass-card border-none hover:bg-white/90 transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-emerald-500" />
            <span className="text-muted-foreground text-sm">今日对话</span>
          </div>
          <p className="text-2xl font-bold text-foreground">
            {messages.filter(m => m.sender === 'user').length}
          </p>
        </div>
        <div className="p-4 glass-card border-none hover:bg-white/90 transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span className="text-muted-foreground text-sm">处理任务</span>
          </div>
          <p className="text-2xl font-bold text-foreground">-</p>
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
          <h2 className="text-foreground font-semibold mb-4">智能体列表</h2>
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 overflow-auto">
              {agents.map((agent, index) => (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                >
                  <AgentCard
                    agent={{
                      id: agent.id,
                      name: agent.name,
                      avatar: agent.emoji || '🤖',
                      description: agent.description,
                      status: 'online',
                    }}
                    isActive={selectedAgent?.id === agent.id}
                    onClick={() => setSelectedAgent(agent)}
                  />
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Chat Interface */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="min-h-[400px] lg:min-h-0"
        >
          <h2 className="text-foreground font-semibold mb-4">
            对话窗口
            {selectedAgent && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                - {selectedAgent.name}
              </span>
            )}
          </h2>
          <div className="h-[calc(100%-2rem)]">
            <ChatInterface
              messages={messages.filter(m =>
                m.sender === 'user' ||
                !m.agentId ||
                m.agentId === selectedAgent?.id
              )}
              currentAgent={{
                id: selectedAgent?.id || '',
                name: selectedAgent?.name || '',
                avatar: selectedAgent?.emoji || '🤖',
                description: selectedAgent?.description || '',
                status: 'online',
              }}
              onSendMessage={handleSendMessage}
              disabled={sending || !selectedAgent}
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}
