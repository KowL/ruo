import { useState } from 'react';
import { createConcept, updateConcept } from '../../api/concept';
import { Concept } from '../../types/concept';
import Button from '../../components/common/Button';

interface ConceptFormProps {
  concept?: Concept;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function ConceptForm({ concept, onSuccess, onCancel }: ConceptFormProps) {
  const [name, setName] = useState(concept?.name || '');
  const [description, setDescription] = useState(concept?.description || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isEditing = !!concept;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('请输入概念名称');
      return;
    }

    try {
      setLoading(true);
      if (isEditing) {
        await updateConcept(concept.id, { name, description });
      } else {
        await createConcept({ name, description });
      }
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || '保存失败');
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

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          概念名称 *
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="如：人工智能、新能源"
          className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          概念描述
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="简要描述这个概念..."
          rows={3}
          className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? '保存中...' : isEditing ? '保存' : '创建'}
        </Button>
      </div>
    </form>
  );
}
