import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash2, Edit2, TrendingUp, Building2, Zap, Crown } from 'lucide-react';
import {
  getConcept,
  addStockToConcept,
  updateStockPositioning,
  removeStockFromConcept,
} from '../../api/concept';
import { searchStock } from '../../api/stock';
import { ConceptDetail, ConceptStock, StockPositioning, POSITIONING_OPTIONS } from '../../types/concept';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import Loading from '../../components/common/Loading';
import Modal from '../../components/common/Modal';
import ConceptForm from './ConceptForm';

// 定位图标映射
const positioningIcons: Record<StockPositioning, React.ReactNode> = {
  '龙头': <Crown className="w-4 h-4" />,
  '中军': <Building2 className="w-4 h-4" />,
  '补涨': <TrendingUp className="w-4 h-4" />,
  '妖股': <Zap className="w-4 h-4" />,
  '先锋': <Zap className="w-4 h-4" />, // Using Zap for '先锋' as well, or another appropriate icon
};

export default function ConceptDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [concept, setConcept] = useState<ConceptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddStockModal, setShowAddStockModal] = useState(false);

  useEffect(() => {
    if (id) {
      loadConcept(parseInt(id));
    }
  }, [id]);

  const loadConcept = async (conceptId: number) => {
    try {
      setLoading(true);
      const data = await getConcept(conceptId);
      setConcept(data);
    } catch (error) {
      console.error('加载概念详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveStock = async (stockSymbol: string) => {
    if (!concept) return;
    if (!confirm(`确定要从概念中移除 ${stockSymbol} 吗？`)) return;

    try {
      await removeStockFromConcept(concept.id, stockSymbol);
      loadConcept(concept.id);
    } catch (error) {
      console.error('移除股票失败:', error);
    }
  };

  const handleUpdatePositioning = async (stockSymbol: string, positioning: StockPositioning) => {
    if (!concept) return;

    try {
      await updateStockPositioning(concept.id, stockSymbol, { positioning });
      loadConcept(concept.id);
    } catch (error) {
      console.error('更新定位失败:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading />
      </div>
    );
  }

  if (!concept) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">概念不存在</p>
        <Button onClick={() => navigate('/concept')} className="mt-4">
          返回列表
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/concept')}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{concept.name}</h1>
            <button
              onClick={() => setShowEditModal(true)}
              className="p-2 text-slate-500 hover:text-cyan-400 hover:bg-cyan-500/10 rounded-lg transition-colors"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          </div>
          {concept.description && (
            <p className="text-slate-400 mt-1">{concept.description}</p>
          )}
        </div>
        <Button onClick={() => setShowAddStockModal(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          添加股票
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {POSITIONING_OPTIONS.map((pos) => {
          const count = concept.stocks.filter((s) => s.positioning === pos.value).length;
          return (
            <Card key={pos.value} className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <span style={{ color: pos.color }}>{positioningIcons[pos.value]}</span>
                <span className="text-sm text-slate-400">{pos.label}</span>
              </div>
              <div className="text-2xl font-bold text-white">{count}</div>
            </Card>
          );
        })}
      </div>

      {/* Stocks List */}
      <Card>
        <h2 className="text-lg font-semibold text-white mb-4">
          股票列表 ({concept.stocks.length})
        </h2>

        {concept.stocks.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            暂无股票，点击右上角添加
          </div>
        ) : (
          <div className="space-y-2">
            {concept.stocks.map((stock) => (
              <StockItem
                key={stock.id}
                stock={stock}
                onRemove={() => handleRemoveStock(stock.stock_symbol)}
                onUpdatePositioning={(pos) => handleUpdatePositioning(stock.stock_symbol, pos)}
              />
            ))}
          </div>
        )}
      </Card>

      {/* Edit Modal */}
      <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title="编辑概念">
        <ConceptForm
          concept={concept}
          onSuccess={() => {
            setShowEditModal(false);
            loadConcept(concept.id);
          }}
          onCancel={() => setShowEditModal(false)}
        />
      </Modal>

      {/* Add Stock Modal */}
      <Modal isOpen={showAddStockModal} onClose={() => setShowAddStockModal(false)} title="添加股票">
        <AddStockForm
          conceptId={concept.id}
          onSuccess={() => {
            setShowAddStockModal(false);
            loadConcept(concept.id);
          }}
          onCancel={() => setShowAddStockModal(false)}
        />
      </Modal>
    </div>
  );
}

// 股票项组件
interface StockItemProps {
  stock: ConceptStock;
  onRemove: () => void;
  onUpdatePositioning: (positioning: StockPositioning) => void;
}

function StockItem({ stock, onRemove, onUpdatePositioning }: StockItemProps) {
  const positioningOption = POSITIONING_OPTIONS.find((p) => p.value === stock.positioning);

  return (
    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors">
      <div className="flex items-center gap-4">
        <div>
          <div className="font-medium text-white">{stock.stock_symbol}</div>
          {stock.stock_name && (
            <div className="text-sm text-slate-400">{stock.stock_name}</div>
          )}
        </div>

        <select
          value={stock.positioning}
          onChange={(e) => onUpdatePositioning(e.target.value as StockPositioning)}
          className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
          style={{
            borderColor: positioningOption?.color,
            color: positioningOption?.color,
          }}
        >
          {POSITIONING_OPTIONS.map((pos) => (
            <option key={pos.value} value={pos.value}>
              {pos.label}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={onRemove}
        className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

// 添加股票表单
interface AddStockFormProps {
  conceptId: number;
  onSuccess: () => void;
  onCancel: () => void;
}

function AddStockForm({ conceptId, onSuccess, onCancel }: AddStockFormProps) {
  const [symbol, setSymbol] = useState('');
  const [stockName, setStockName] = useState('');
  const [positioning, setPositioning] = useState<StockPositioning>('补涨');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ symbol: string; name: string }>>([]);

  // 搜索股票
  useEffect(() => {
    const search = async () => {
      if (symbol.length < 2) {
        setSearchResults([]);
        return;
      }
      try {
        const response: any[] = await searchStock(symbol);
        if (Array.isArray(response)) {
          setSearchResults(response.slice(0, 5));
        }
      } catch (error) {
        console.error('搜索失败:', error);
      }
    };

    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [symbol]);

  const handleSelectStock = (selected: { symbol: string; name: string }) => {
    setSymbol(selected.symbol);
    setStockName(selected.name);
    setSearchResults([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!symbol.trim()) {
      setError('请输入股票代码');
      return;
    }

    try {
      setLoading(true);
      await addStockToConcept(conceptId, {
        stock_symbol: symbol,
        stock_name: stockName,
        positioning,
        notes,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || '添加失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="relative">
        <label className="block text-sm font-medium text-slate-300 mb-1">
          股票代码 *
        </label>
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="输入代码或名称搜索"
          className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
        {searchResults.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-lg">
            {searchResults.map((result) => (
              <button
                key={result.symbol}
                type="button"
                onClick={() => handleSelectStock(result)}
                className="w-full px-3 py-2 text-left hover:bg-slate-700 transition-colors"
              >
                <span className="text-white">{result.symbol}</span>
                <span className="text-slate-400 ml-2">{result.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">定位</label>
        <select
          value={positioning}
          onChange={(e) => setPositioning(e.target.value as StockPositioning)}
          className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        >
          {POSITIONING_OPTIONS.map((pos) => (
            <option key={pos.value} value={pos.value}>
              {pos.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">备注</label>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="可选"
          className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? '添加中...' : '添加'}
        </Button>
      </div>
    </form>
  );
}
