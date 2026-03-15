import React, { useEffect, useState } from 'react';
import { getRawNews } from '@/api/news';
import { News } from '@/types';
import { formatRelativeTime } from '@/utils/format';
import { Newspaper, RefreshCw, ChevronRight, X, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';

export const NewsFlashList: React.FC = () => {
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedNews, setSelectedNews] = useState<News | null>(null);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const data = await getRawNews(undefined, 24, 15);
      setNews(data);
    } catch (error) {
      console.error('获取快讯失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
    const timer = setInterval(fetchNews, 60000); // 每分钟自动刷新
    return () => clearInterval(timer);
  }, []);

  return (
    <>
      <div className="card h-[500px] flex flex-col p-5 group overflow-hidden">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Newspaper className="w-5 h-5" />
            </div>
            <h2 className="text-foreground font-bold text-lg tracking-tight">7X24 快讯</h2>
          </div>
          <button 
            onClick={(e) => { e.stopPropagation(); fetchNews(); }}
            disabled={loading}
            className={clsx(
              "p-2 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/5 transition-all duration-300",
              loading && "animate-spin"
            )}
            title="刷新内容"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-hide custom-scrollbar">
          {loading && news.length === 0 ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="space-y-2">
                  <div className="h-3 bg-muted rounded w-1/4" />
                  <div className="h-4 bg-muted rounded w-full" />
                  <div className="h-4 bg-muted rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : news.length > 0 ? (
            news.map((item) => (
              <div 
                key={item.id} 
                onClick={() => setSelectedNews(item)}
                className="relative pl-4 pb-1 border-l border-border/60 hover:border-primary/40 transition-colors group/item cursor-pointer"
              >
                <div className="absolute left-[-5px] top-[6px] w-2 h-2 rounded-full bg-border group-hover/item:bg-primary transition-colors" />
                <div className="text-[10px] font-bold text-muted-foreground mb-1 flex items-center gap-2">
                  <span className="bg-muted px-1.5 py-0.5 rounded uppercase tracking-tighter">
                    {item.source === 'cls' ? '财联社' : '雪球'}
                  </span>
                  <span className="font-mono">{formatRelativeTime(item.publishTime)}</span>
                </div>
                <p className="text-sm text-foreground/90 leading-relaxed font-medium line-clamp-3 group-hover/item:text-primary transition-colors">
                  {item.title || item.content}
                </p>
              </div>
            ))
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground py-10">
              <Newspaper className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm">暂无最新快讯</p>
            </div>
          )}
        </div>

        <a 
          href="#/stock/news" 
          className="mt-4 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-muted/30 text-muted-foreground text-xs font-bold hover:bg-primary/10 hover:text-primary transition-all group/btn"
        >
          查看全部情报
          <ChevronRight className="w-3.5 h-3.5 transform group-hover/btn:translate-x-0.5 transition-transform" />
        </a>
      </div>

      {/* 详情弹窗 */}
      <AnimatePresence>
        {selectedNews && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedNews(null)}
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-3">
                  <span className="bg-primary/10 text-primary px-2 py-1 rounded text-xs font-bold uppercase tracking-wider">
                    {selectedNews.source === 'cls' ? '财联社' : '雪球'}
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {formatRelativeTime(selectedNews.publishTime)}
                  </span>
                </div>
                <button 
                  onClick={() => setSelectedNews(null)}
                  className="p-2 rounded-full hover:bg-muted text-muted-foreground transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                {selectedNews.title && (
                  <h3 className="text-xl font-bold text-foreground mb-6 leading-tight">
                    {selectedNews.title}
                  </h3>
                )}
                <div className="text-foreground/80 leading-8 text-[15px] whitespace-pre-wrap font-medium">
                  {selectedNews.content}
                </div>

                {/* AI Analysis */}
                {selectedNews.aiAnalysis && (
                  <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="w-5 h-5 text-primary" />
                      <h4 className="text-sm font-bold text-primary">AI 智能解读</h4>
                    </div>
                    <p className="text-[14px] text-foreground/70 leading-relaxed italic">
                      {selectedNews.aiAnalysis}
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t border-border bg-muted/5 flex justify-end">
                <button 
                  onClick={() => setSelectedNews(null)}
                  className="px-6 py-2 rounded-xl bg-primary text-white text-sm font-bold hover:bg-primary/90 transition-all shadow-sm"
                >
                  确 定
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
