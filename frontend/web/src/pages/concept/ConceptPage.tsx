import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Trash2, ChevronRight } from 'lucide-react';
import { getConceptList, deleteConcept } from '../../api/concept';
import { ConceptListItem } from '../../types/concept';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import Loading from '../../components/common/Loading';
import Modal from '../../components/common/Modal';
import ConceptForm from './ConceptForm';

export default function ConceptPage() {
  const navigate = useNavigate();
  const [concept, setConcept] = useState<ConceptListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  useEffect(() => {
    loadConcept();
  }, []);

  const loadConcept = async () => {
    try {
      setLoading(true);
      const data = await getConceptList();
      setConcept(data);
    } catch (error) {
      console.error('加载概念列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteConcept(deleteId);
      setConcept(concept.filter(c => c.id !== deleteId));
      setDeleteId(null);
    } catch (error) {
      console.error('删除概念失败:', error);
    }
  };

  const filteredConcept = concept.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">概念管理</h1>
          <p className="text-slate-400 mt-1">管理股票板块概念和龙头定位</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          新建概念
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
        <input
          type="text"
          placeholder="搜索概念..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
      </div>

      {/* Concept Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredConcept.map((concept) => (
          <Card
            key={concept.id}
            className="group cursor-pointer hover:border-cyan-500/30 transition-colors"
            onClick={() => navigate(`/concept/${concept.id}`)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                  {concept.name}
                </h3>
                {concept.description && (
                  <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                    {concept.description}
                  </p>
                )}
                <div className="flex items-center gap-4 mt-3">
                  <span className="text-sm text-slate-500">
                    {concept.stock_count} 只股票
                  </span>
                  <span className="text-xs text-slate-600">
                    {new Date(concept.created_at || '').toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteId(concept.id);
                  }}
                  className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredConcept.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-slate-500">
            {searchTerm ? '没有找到匹配的概念' : '暂无概念，点击上方按钮创建'}
          </p>
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="新建概念">
        <ConceptForm
          onSuccess={() => {
            setShowCreateModal(false);
            loadConcept();
          }}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteId} onClose={() => setDeleteId(null)} title="确认删除">
        <div className="space-y-4">
          <p className="text-slate-300">确定要删除这个概念吗？此操作不可恢复。</p>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDeleteId(null)}>
              取消
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              删除
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
