/**
 * 概念库页面 - 极致体验版 (Hermes Orange Theme)
 * Concept Library Page
 */
import React, { useEffect, useState } from 'react';
import {
  getConceptRanking,
  getConceptDistribution,
  getConceptMarketDetail
} from '@/api/concept';
import {
  type ConceptMarketData,
  type ConceptDistributionItem,
  type LimitUpConceptDistribution,
  type ConceptMarketStock,
  type ConceptRankingItem
} from '@/types/concept';
import { 
  RefreshCw, ChevronRight, X, Flame, Trophy, TrendingUp, 
  PieChart, Layers, Zap, Info
} from 'lucide-react';
import Loading from '@/components/common/Loading';

const ConceptLibraryPage: React.FC = () => {
  const [ranking, setRanking] = useState<ConceptRankingItem[]>([]);
  const [distribution, setDistribution] = useState<ConceptDistributionItem[]>([]);
  const [lifecycleStats, setLifecycleStats] = useState<LimitUpConceptDistribution['lifecycle_stats'] | null>(null);
  const [totalLimitUp, setTotalLimitUp] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'hot_score' | 'limit_up_count' | 'continuous_days'>('hot_score');
  const [selectedConcept, setSelectedConcept] = useState<ConceptMarketData | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    fetchAllData();
  }, []);

  useEffect(() => {
    fetchRanking();
  }, [sortBy]);

  const fetchAllData = async () => {
    if (!loading) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      await Promise.all([fetchRanking(), fetchDistribution()]);
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchRanking = async () => {
    const res = await getConceptRanking(sortBy, 20);
    if (res.status === 'success') {
      setRanking(res.data || []);
    }
  };

  const fetchDistribution = async () => {
    const res = await getConceptDistribution();
    if (res.status === 'success' && res.data) {
      setDistribution(res.data.distribution || []);
      setLifecycleStats(res.data.lifecycle_stats || null);
      setTotalLimitUp(res.data.total_limit_up || 0);
    }
  };

  const handleConceptClick = async (conceptName: string) => {
    try {
      const res = await getConceptMarketDetail(conceptName);
      if (res.status === 'success') {
        setSelectedConcept(res.data);
        setShowDetail(true);
      }
    } catch (err: any) {
      console.error('获取概念详情失败:', err);
    }
  };

  // 生命周期样式定义
  const getLifecycleConfig = (lifecycle: string) => {
    switch (lifecycle) {
      case '发酵期':
        return { 
          text: '发酵期', 
          color: 'text-emerald-500', 
          bg: 'bg-emerald-500/10', 
          border: 'border-emerald-500/20',
          dot: 'bg-emerald-500' 
        };
      case '高潮期':
        return { 
          text: '高潮期', 
          color: 'text-orange-500', 
          bg: 'bg-orange-500/10', 
          border: 'border-orange-500/20',
          dot: 'bg-orange-500' 
        };
      case '退潮期':
        return { 
          text: '退潮期', 
          color: 'text-slate-400', 
          bg: 'bg-slate-500/10', 
          border: 'border-slate-500/20',
          dot: 'bg-slate-500' 
        };
      default:
        return { 
          text: lifecycle, 
          color: 'text-blue-500', 
          bg: 'bg-blue-500/10', 
          border: 'border-blue-500/20',
          dot: 'bg-blue-500' 
        };
    }
  };

  const getRankBadge = (index: number) => {
    if (index === 0) return { icon: <Trophy className="w-4 h-4 text-yellow-500" />, bg: 'bg-yellow-500/10 shadow-lg shadow-yellow-500/10 border-yellow-500/20' };
    if (index === 1) return { icon: <Trophy className="w-4 h-4 text-slate-300" />, bg: 'bg-slate-300/10 border-slate-300/20' };
    if (index === 2) return { icon: <Trophy className="w-4 h-4 text-amber-600" />, bg: 'bg-amber-600/10 border-amber-600/20' };
    return { icon: <span className="text-[11px] font-black">{index + 1}</span>, bg: 'bg-muted border-border/50' };
  };

  if (loading) return <Loading />;

  return (
    <div className="min-h-screen pb-20">
      {/* Header Container */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-orange-500 flex items-center justify-center shadow-lg shadow-orange-500/20">
              <Flame className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">概念库</h1>
          </div>
          <p className="text-muted-foreground font-medium pl-1">深度挖掘市场热点，追踪概念生命周期演变</p>
        </div>

        <button 
          onClick={fetchAllData}
          disabled={refreshing}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-card border border-border/50 hover:bg-muted font-bold text-sm transition-all active:scale-95"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? '刷新中...' : '同步数据'}</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-3 text-red-500 font-bold text-sm">
            <Info className="w-5 h-5" />
            <span>{error}</span>
          </div>
          <button onClick={fetchAllData} className="text-xs font-black text-red-500 hover:underline">点击重试</button>
        </div>
      )}

      {/* Stats Quick View */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: '今日涨停', value: totalLimitUp, icon: <Zap className="w-5 h-5 text-orange-500" />, color: 'orange' },
          { label: '发酵期', value: lifecycleStats?.发酵期 || 0, icon: <TrendingUp className="w-5 h-5 text-emerald-500" />, color: 'emerald' },
          { label: '高潮期', value: lifecycleStats?.高潮期 || 0, icon: <Flame className="w-5 h-5 text-orange-600" />, color: 'orange' },
          { label: '退潮期', value: lifecycleStats?.退潮期 || 0, icon: <Layers className="w-5 h-5 text-slate-400" />, color: 'slate' },
        ].map((stat, idx) => (
          <div key={idx} className="bg-card border border-border/50 rounded-2xl p-5 hover:shadow-md transition-all group overflow-hidden relative">
            <div className={`absolute top-0 right-0 w-24 h-24 bg-${stat.color}-500/5 blur-3xl -mr-8 -mt-8 rounded-full`} />
            <div className="flex items-center gap-4 relative z-10">
              <div className={`w-12 h-12 rounded-xl bg-muted flex items-center justify-center`}>
                {stat.icon}
              </div>
              <div>
                <div className="text-2xl font-black text-foreground">{stat.value}</div>
                <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest">{stat.label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Leaderboard Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-orange-500" />
              <h2 className="text-xl font-black text-foreground">概念强度榜</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-muted-foreground uppercase">排序:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-card border border-border/50 rounded-lg px-3 py-1.5 text-xs font-black text-foreground focus:outline-none focus:ring-2 focus:ring-orange-500/50"
              >
                <option value="hot_score">实时热度</option>
                <option value="limit_up_count">涨停数量</option>
                <option value="continuous_days">持续时间</option>
              </select>
            </div>
          </div>

          <div className="space-y-3">
            {ranking.map((concept, index) => {
              const lifecycle = getLifecycleConfig(concept.lifecycle);
              const rank = getRankBadge(index);
              return (
                <div
                  key={concept.theme_name}
                  onClick={() => handleConceptClick(concept.theme_name)}
                  className="group flex items-center gap-4 p-4 bg-card border border-border/50 rounded-2xl hover:border-orange-500/30 hover:shadow-lg transition-all cursor-pointer relative overflow-hidden"
                >
                  <div className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center border font-black transition-all group-hover:scale-110 ${rank.bg}`}>
                    {rank.icon}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-base font-black text-foreground truncate">{concept.theme_name}</span>
                      <span className={`shrink-0 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black border uppercase tracking-wider ${lifecycle.bg} ${lifecycle.color} ${lifecycle.border}`}>
                        <span className={`w-1 h-1 rounded-full ${lifecycle.dot}`} />
                        {lifecycle.text}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-medium text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-3.5 h-3.5" />
                        持续 {concept.continuous_days} 天
                      </span>
                      {concept.leader_stocks?.[0] && (
                        <span className="flex items-center gap-1">
                          <Trophy className="w-3.5 h-3.5 text-orange-500" />
                          <span className="text-foreground font-bold">{concept.leader_stocks[0].name}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-8 shrink-0">
                    <div className="text-right">
                      <div className="text-lg font-black text-foreground">{concept.limit_up_count}</div>
                      <div className="text-[10px] font-bold text-muted-foreground tracking-tighter uppercase">涨停数</div>
                    </div>
                    <div className="text-right min-w-[60px]">
                      <div className={`text-2xl font-black italic tracking-tighter ${
                        concept.hot_score >= 80 ? 'text-orange-500' : 
                        concept.hot_score >= 50 ? 'text-foreground' : 'text-muted-foreground'
                      }`}>
                        {concept.hot_score}
                      </div>
                      <div className="text-[10px] font-bold text-muted-foreground uppercase">HOT SCORE</div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-muted-foreground opacity-30 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Distribution Section */}
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <PieChart className="w-5 h-5 text-orange-500" />
            <h2 className="text-xl font-black text-foreground">涨停概念分布</h2>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {distribution.map((item) => {
              const lifecycle = getLifecycleConfig(item.lifecycle);
              return (
                <div
                  key={item.theme_name}
                  onClick={() => handleConceptClick(item.theme_name)}
                  className="bg-card border border-border/50 rounded-2xl p-4 hover:border-orange-500/30 hover:shadow-md transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-black text-foreground text-sm truncate">{item.theme_name}</span>
                    <span className={`px-2 py-0.5 text-[9px] rounded-md font-black border uppercase ${lifecycle.bg} ${lifecycle.color} ${lifecycle.border}`}>
                      {lifecycle.text}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-bold">
                      <span className="text-muted-foreground">占比 {item.percentage.toFixed(1)}%</span>
                      <span className="text-foreground">{item.limit_up_count} 只涨停</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-orange-500 rounded-full h-1.5 shadow-[0_0_8px_rgba(249,115,22,0.4)] transition-all duration-500 ease-out group-hover:w-full"
                        style={{ width: `${Math.min(item.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Concept Detail Modal */}
      {showDetail && selectedConcept && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={() => setShowDetail(false)} />
          
          <div className="bg-card w-full max-w-2xl max-h-[90vh] rounded-3xl border border-border/50 shadow-2xl flex flex-col overflow-hidden relative z-10">
            {/* Modal Header */}
            <div className="px-8 py-6 border-b border-border/50 flex items-center justify-between bg-muted/30 sticky top-0 z-20">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-orange-500/10 flex items-center justify-center">
                  <Flame className="w-6 h-6 text-orange-500" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-black text-foreground">{selectedConcept.theme_name}</h2>
                    <span className={`px-3 py-1 text-[11px] rounded-full font-black border uppercase ${getLifecycleConfig(selectedConcept.lifecycle).bg} ${getLifecycleConfig(selectedConcept.lifecycle).color}`}>
                      {selectedConcept.lifecycle}
                    </span>
                  </div>
                  <p className="text-xs font-medium text-muted-foreground mt-0.5 italic">详细概念归类及龙头成分股分析</p>
                </div>
              </div>
              <button 
                onClick={() => setShowDetail(false)} 
                className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center text-muted-foreground hover:bg-orange-500 hover:text-white transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
              {/* Quick Stats Grid */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: '热度评分', value: selectedConcept.hot_score, icon: <Flame className="w-4 h-4" />, color: 'orange' },
                  { label: '涨停数量', value: selectedConcept.limit_up_count, icon: <Zap className="w-4 h-4" />, color: 'orange' },
                  { label: '持续天数', value: selectedConcept.continuous_days, icon: <Layers className="w-4 h-4" />, color: 'orange' },
                ].map((stat, i) => (
                  <div key={i} className="bg-background border border-border/50 rounded-2xl p-4 text-center group hover:border-orange-500/30 transition-all">
                    <div className="flex justify-center mb-2">
                       <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center text-orange-500">
                         {stat.icon}
                       </div>
                    </div>
                    <div className="text-xl font-black text-foreground mb-0.5">{stat.value}</div>
                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Leader Stocks Section */}
              {selectedConcept.leader_stocks && selectedConcept.leader_stocks.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-orange-500" />
                    <h3 className="text-sm font-black text-foreground uppercase tracking-wider">核心龙头股</h3>
                  </div>
                  <div className="grid gap-3">
                    {selectedConcept.leader_stocks.map((stock: ConceptMarketStock, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-4 bg-muted/30 border border-border/50 rounded-2xl hover:border-orange-500/30 transition-all">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-orange-500 text-white flex items-center justify-center font-black text-xs shadow-lg shadow-orange-500/20">
                            {idx + 1}
                          </div>
                          <div>
                            <div className="font-black text-foreground flex items-center gap-2">
                              {stock.name}
                              <span className="text-[10px] font-mono text-muted-foreground px-1.5 py-0.5 bg-background rounded border border-border">
                                {stock.symbol}
                              </span>
                            </div>
                            <div className="text-[11px] font-bold text-orange-500 mt-0.5">
                              {stock.positioning} · {stock.limit_up_days}连板
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-black ${stock.change_pct >= 0 ? 'text-profit-up' : 'text-profit-down'}`}>
                            {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct?.toFixed(2)}%
                          </div>
                          <div className="text-[10px] font-bold text-muted-foreground">最新涨跌</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Follower Stocks Area (if exists in API) */}
               {selectedConcept.follower_stocks && selectedConcept.follower_stocks.length > 0 && (
                <div className="space-y-4 pb-4">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-orange-500" />
                    <h3 className="text-sm font-black text-foreground uppercase tracking-wider">板块成分股</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedConcept.follower_stocks.map((stock: ConceptMarketStock, idx: number) => (
                      <div key={idx} className="px-3 py-1.5 rounded-xl bg-background border border-border/50 text-xs font-black text-foreground hover:border-orange-500/50 transition-all cursor-default">
                        {stock.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-8 py-5 border-t border-border/50 bg-muted/30 flex items-center justify-between sticky bottom-0 z-20">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                最后更新: {new Date(selectedConcept.update_time).toLocaleString()}
              </div>
              <button 
                onClick={() => setShowDetail(false)}
                className="px-6 py-2.5 rounded-xl bg-foreground text-background font-black text-sm hover:scale-105 active:scale-95 transition-all"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConceptLibraryPage;
