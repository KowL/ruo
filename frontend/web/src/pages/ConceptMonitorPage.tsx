import { useState, useEffect } from 'react';
import { TrendingUp, Activity, Zap, Flame, BarChart3, ArrowUpRight } from 'lucide-react';
import { getMonitorDashboard, getLeadingStocks } from '../api/conceptMonitor';
import { MonitorDashboard, ConceptMovement, ConceptFundFlow, LeadingStock } from '../types/conceptMonitor';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import Modal from '../components/common/Modal';

export default function ConceptMonitorPage() {
  const [data, setData] = useState<MonitorDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [leadingStocks, setLeadingStocks] = useState<LeadingStock[]>([]);
  const [loadingStocks, setLoadingStocks] = useState(false);

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 60000); // 60秒刷新
    return () => clearInterval(timer);
  }, []);

  const loadData = async () => {
    try {
      const dashboard = await getMonitorDashboard();
      setData(dashboard);
    } catch (error) {
      console.error('加载监控数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewLeadingStocks = async (conceptName: string) => {
    setSelectedConcept(conceptName);
    setLoadingStocks(true);
    try {
      const stocks = await getLeadingStocks(conceptName, 5);
      setLeadingStocks(stocks);
    } catch (error) {
      console.error('获取龙头股失败:', error);
    } finally {
      setLoadingStocks(false);
    }
  };


  const marketOverview = data?.market_overview;

  return (
    <div className="space-y-6 p-6 pt-0">
      <div className="flex justify-end gap-2 mb-2">
        <Activity className="w-4 h-4 text-cyan-400" />
        <span className="text-sm text-muted-foreground">自动刷新</span>
      </div>

      {/* 市场概览 */}
      {loading && !marketOverview ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 bg-card rounded-xl border border-border"></div>
          ))}
        </div>
      ) : marketOverview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="text-center">
            <div className="text-sm text-muted-foreground mb-1">上涨家数</div>
            <div className="text-2xl font-bold text-profit-up">{marketOverview.up_count}</div>
          </Card>
          <Card className="text-center">
            <div className="text-sm text-muted-foreground mb-1">下跌家数</div>
            <div className="text-2xl font-bold text-profit-down">{marketOverview.down_count}</div>
          </Card>
          <Card className="text-center">
            <div className="text-sm text-muted-foreground mb-1">涨停家数</div>
            <div className="text-2xl font-bold text-orange-500">{marketOverview.limit_up_count}</div>
          </Card>
          <Card className="text-center">
            <div className="text-sm text-muted-foreground mb-1">跌停家数</div>
            <div className="text-2xl font-bold text-cyan-500">{marketOverview.limit_down_count}</div>
          </Card>
        </div>
      )}

      {/* 涨停统计 */}
      {loading && !data?.limit_up_statistics ? (
        <div className="h-48 bg-card rounded-xl border border-border animate-pulse"></div>
      ) : data?.limit_up_statistics && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Flame className="w-5 h-5 text-orange-500" />
            <h2 className="text-lg font-semibold">涨停分布</h2>
            <span className="text-sm text-muted-foreground ml-auto">
              共 {data.limit_up_statistics.total_limit_up} 家涨停
            </span>
          </div>

          <div className="space-y-2">
            {data.limit_up_statistics.concept_ranking.map((concept) => (
              <div
                key={concept.name}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors cursor-pointer"
                onClick={() => handleViewLeadingStocks(concept.name)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center">
                    <Zap className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">{concept.name}</div>
                    <div className="text-xs text-muted-foreground">{concept.limit_up_count} 家涨停</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-2">
                    {concept.stocks.slice(0, 3).map((stock, idx) => (
                      <div
                        key={idx}
                        className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-xs border-2 border-background"
                        title={stock.name}
                      >
                        {stock.name.slice(0, 1)}
                      </div>
                    ))}
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 涨幅排行 */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-profit-up" />
            <h2 className="text-lg font-semibold">概念涨幅排行</h2>
          </div>

          <div className="space-y-2">
            {data?.movement_ranking?.map((concept, index) => (
              <MovementRankingItem
                key={concept.name}
                concept={concept}
                rank={index + 1}
                onClick={() => handleViewLeadingStocks(concept.name)}
              />
            ))}
          </div>
        </Card>

        {/* 资金流入排行 */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">资金流入排行</h2>
          </div>

          <div className="space-y-2">
            {data?.fund_flow_ranking?.map((concept, index) => (
              <FundFlowItem
                key={concept.name}
                concept={concept}
                rank={index + 1}
              />
            ))}
          </div>
        </Card>
      </div>

      {/* 龙头股弹窗 */}
      <Modal
        isOpen={!!selectedConcept}
        onClose={() => {
          setSelectedConcept(null);
          setLeadingStocks([]);
        }}
        title={`${selectedConcept} - 龙头股`}
      >
        {loadingStocks ? (
          <div className="flex items-center justify-center py-8">
            <Loading />
          </div>
        ) : leadingStocks.length > 0 ? (
          <div className="space-y-2">
            {leadingStocks.map((stock) => (
              <div
                key={stock.symbol}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div>
                  <div className="font-medium">{stock.name}</div>
                  <div className="text-sm text-muted-foreground">{stock.symbol}</div>
                </div>
                <div className="text-right">
                  <div className={`font-bold ${stock.change_pct >= 0 ? 'text-profit-up' : 'text-profit-down'}`}>
                    {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct}%
                  </div>
                  <div className="text-sm text-muted-foreground">¥{stock.price}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">暂无数据</div>
        )}
      </Modal>
    </div>
  );
}

// 涨幅排行项
interface MovementRankingItemProps {
  concept: ConceptMovement;
  rank: number;
  onClick: () => void;
}

function MovementRankingItem({ concept, rank, onClick }: MovementRankingItemProps) {
  const isUp = concept.change_pct >= 0;

  return (
    <div
      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <div className={`w-6 h-6 rounded flex items-center justify-center text-sm font-bold ${rank <= 3 ? 'bg-destructive/20 text-destructive' : 'bg-muted text-muted-foreground'
          }`}>
          {rank}
        </div>
        <div>
          <div className="font-medium">{concept.name}</div>
          <div className="text-xs text-muted-foreground">
            ↑{concept.up_count} ↓{concept.down_count}
          </div>
        </div>
      </div>

      <div className="text-right">
        <div className={`font-bold ${isUp ? 'text-profit-up' : 'text-profit-down'}`}>
          {isUp ? '+' : ''}{concept.change_pct}%
        </div>
        <div className="text-xs text-muted-foreground">{concept.limit_up_count} 涨停</div>
      </div>
    </div>
  );
}

// 资金流入项
interface FundFlowItemProps {
  concept: ConceptFundFlow;
  rank: number;
}

function FundFlowItem({ concept, rank }: FundFlowItemProps) {
  const isInflow = concept.main_net_inflow >= 0;

  return (
    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-3">
        <div className={`w-6 h-6 rounded flex items-center justify-center text-sm font-bold ${rank <= 3 ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
          }`}>
          {rank}
        </div>
        <div>
          <div className="font-medium">{concept.name}</div>
          <div className="text-xs text-muted-foreground">成交额 {concept.total_amount}亿</div>
        </div>
      </div>

      <div className="text-right">
        <div className={`font-bold ${isInflow ? 'text-profit-up' : 'text-profit-down'}`}>
          {isInflow ? '+' : ''}{concept.main_net_inflow.toFixed(0)}万
        </div>
        <div className="text-xs text-muted-foreground">占比 {concept.main_net_inflow_pct}%</div>
      </div>
    </div>
  );
}
