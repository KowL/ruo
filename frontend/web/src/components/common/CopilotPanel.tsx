import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface QuickCommand {
  label: string;
  prompt: string;
  icon: string;
}

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  context?: {
    page?: string;
    symbol?: string;
    symbolName?: string;
  };
}

const CopilotPanel: React.FC<CopilotPanelProps> = ({
  isOpen,
  onClose,
  context,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: getWelcomeMessage(context),
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickCommands: QuickCommand[] = [
    { label: '分析主力资金', prompt: '帮我分析当前持仓的主力资金流向', icon: '💰' },
    { label: '生成今日复盘', prompt: '帮我生成今日市场复盘', icon: '📊' },
    { label: '解释这个指标', prompt: '解释K线图中的当前指标含义', icon: '📈' },
    { label: '风险评估', prompt: '帮我评估当前持仓的风险状况', icon: '⚠️' },
  ];

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // 当上下文变化时更新欢迎消息
  useEffect(() => {
    if (context) {
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: getWelcomeMessage(context),
          timestamp: new Date(),
        },
      ]);
    }
  }, [context]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // 模拟AI回复
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAIResponse(input),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleQuickCommand = (command: QuickCommand) => {
    setInput(command.prompt);
    // 自动发送快捷指令
    setTimeout(() => {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: command.prompt,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      setInput('');
      setIsTyping(true);

      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: getAIResponse(command.prompt),
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
        setIsTyping(false);
      }, 1500);
    }, 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 遮罩层 */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Copilot 面板 */}
      <div className="fixed right-0 top-0 h-full w-[var(--copilot-width)] z-50">
        <div
          className="h-full flex flex-col shadow-2xl"
          style={{ backgroundColor: 'var(--color-surface-2)' }}
        >
          {/* 头部 */}
          <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-surface-4)' }}>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-black font-bold text-sm" style={{ backgroundColor: 'var(--color-brand)' }}>
                R
              </div>
              <h2 className="text-lg font-bold">Ruo Copilot</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:opacity-70"
            >
              ✕
            </button>
          </div>

          {/* 快捷指令 */}
          <div className="p-4 border-b" style={{ borderColor: 'var(--color-surface-4)' }}>
            <div className="text-xs mb-2" style={{ color: 'var(--color-text-secondary)' }}>快捷指令</div>
            <div className="grid grid-cols-2 gap-2">
              {quickCommands.map((command, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickCommand(command)}
                  className="p-2 rounded-lg text-xs font-medium transition-opacity flex items-center space-x-1"
                  style={{ backgroundColor: 'var(--color-surface-3)', color: 'var(--color-text-primary)' }}
                >
                  <span>{command.icon}</span>
                  <span>{command.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  'flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-[85%] rounded-lg p-3',
                    message.role === 'user'
                      ? ''
                      : 'border'
                  )}
                  style={
                    message.role === 'user'
                      ? { backgroundColor: 'var(--color-surface-3)', color: 'var(--color-text-primary)' }
                      : { backgroundColor: 'var(--color-surface-2)', borderColor: 'var(--color-surface-4)', color: 'var(--color-text-primary)' }
                  }
                >
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                    {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}

            {/* AI 正在输入 */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="rounded-lg p-3 border" style={{ backgroundColor: 'var(--color-surface-2)', borderColor: 'var(--color-surface-4)' }}>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 rounded-full pulse-wave" style={{ backgroundColor: 'var(--color-brand)', animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 rounded-full pulse-wave" style={{ backgroundColor: 'var(--color-brand)', animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 rounded-full pulse-wave" style={{ backgroundColor: 'var(--color-brand)', animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* 输入区 */}
          <div className="p-4 border-t" style={{ borderColor: 'var(--color-surface-4)' }}>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的问题..."
                className="flex-1"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: 'var(--color-brand)',
                  color: 'black'
                }}
              >
                发送
              </button>
            </div>
            <div className="text-xs mt-2 text-center" style={{ color: 'var(--color-text-secondary)' }}>
              按 <kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--color-surface-3)' }}>Enter</kbd> 发送，<kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--color-surface-3)' }}>Shift</kbd>+<kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--color-surface-3)' }}>Enter</kbd> 换行
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// 根据上下文生成欢迎消息
function getWelcomeMessage(context?: any): string {
  if (context?.symbol) {
    return `你好！我注意到你正在查看 ${context.symbolName || context.symbol} 的相关数据。\n\n我可以帮你：\n• 分析该股票的技术面和基本面\n• 解读相关新闻和市场情绪\n• 提供买卖点建议\n• 评估持仓风险\n\n有什么我可以帮你的吗？`;
  }
  return `你好！我是 Ruo Copilot，你的智能投顾副驾。\n\n我可以帮你：\n• 分析市场走势和个股情况\n• 解读新闻和研报\n• 提供投资建议和风险提示\n• 进行回测和策略分析\n\n有什么我可以帮你的吗？`;
}

// 模拟AI回复
function getAIResponse(input: string): string {
  const lowerInput = input.toLowerCase();

  if (lowerInput.includes('主力资金') || lowerInput.includes('资金流向')) {
    return `根据最新数据分析：\n\n• 北向资金净流入：+12.5亿\n• 主力净流入：+8.3亿\n• 散户净流入：+4.2亿\n\n整体来看，主力资金呈现净流入态势，市场情绪偏乐观。建议关注持续性。`;
  }

  if (lowerInput.includes('复盘') || lowerInput.includes('今日市场')) {
    return `今日市场复盘（2024-01-28）：\n\n📈 市场表现\n• 上证指数：+1.23%\n• 深证成指：+0.87%\n• 创业板指：+0.45%\n\n📊 热点板块\n• 半导体 +3.2%\n• 新能源 +2.8%\n• AI概念 +2.5%\n\n💡 明日策略\n• 控制仓位，适度谨慎\n• 关注政策消息面\n• 短线可关注科技股机会`;
  }

  if (lowerInput.includes('指标') || lowerInput.includes('解释')) {
    return `当前K线指标解读：\n\n📈 MACD：\n• 快线上穿慢线，金叉形态\n• 动能增强，延续上涨趋势\n\n📊 KDJ：\n• J值进入超买区（>100）\n• 短期可能回调\n\n💡 建议：\n• 趋势向上但短期有回调风险\n• 可考虑减仓或设置止盈\n• 关注成交量变化`;
  }

  if (lowerInput.includes('风险') || lowerInput.includes('评估')) {
    return `当前持仓风险评估：\n\n🔴 风险等级：中等\n\n📊 风险分布：\n• 行业集中度：偏高（新能源占比65%）\n• 个股集中度：适中\n• 杠杆比例：无\n\n💡 建议：\n• 建议适当分散行业配置\n• 设置止损位防范下行风险\n• 保持合理现金仓位`;
  }

  return `感谢你的提问！\n\n关于"${input}"的分析，我正在深入研究... \n\n目前我可以提供以下类型的服务：\n• 个股技术分析和基本面解读\n• 市场热点和情绪分析\n• 投资策略和风险建议\n• 新闻研报解读\n\n请问你具体想了解哪个方面？`;
}

export default CopilotPanel;
