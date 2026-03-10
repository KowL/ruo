import React, { useState } from 'react';
import { createGroup } from '@/api/favorites';
import Toast from '@/components/common/Toast';

interface AddGroupModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const AddGroupModal: React.FC<AddGroupModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [groupName, setGroupName] = useState('');
    const [groupDescription, setGroupDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    if (!isOpen) return null;

    const showToast = (message: string, type: 'success' | 'error') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleCreateGroup = async () => {
        if (!groupName.trim()) {
            showToast('请输入分组名称', 'error');
            return;
        }
        setLoading(true);
        try {
            await createGroup({ name: groupName, description: groupDescription });
            showToast('分组创建成功', 'success');
            setGroupName('');
            setGroupDescription('');
            setTimeout(() => {
                onSuccess();
                onClose();
            }, 1000);
        } catch (error) {
            showToast('创建分组失败', 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-card w-full max-w-md p-6 relative overflow-hidden border border-border rounded-2xl shadow-2xl">
                {/* Glow Effects */}
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

                <h3 className="text-xl font-bold mb-6 text-foreground flex items-center">
                    <span className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full mr-3"></span>
                    新建分组
                </h3>

                <div className="space-y-4 relative z-10">
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">分组名称</label>
                        <input
                            type="text"
                            placeholder="例如：科技股、高息股"
                            value={groupName}
                            onChange={(e) => setGroupName(e.target.value)}
                            className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">分组描述 (可选)</label>
                        <input
                            type="text"
                            placeholder="简要描述该分组的策略或特点"
                            value={groupDescription}
                            onChange={(e) => setGroupDescription(e.target.value)}
                            className="w-full px-4 py-3 bg-muted/50 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                        />
                    </div>
                </div>

                <div className="flex space-x-4 pt-8 relative z-10">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-3 rounded-xl border border-border text-muted-foreground hover:bg-muted hover:text-foreground transition-all font-medium"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleCreateGroup}
                        disabled={loading}
                        className={`flex-1 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-blue-500/20 hover:-translate-y-0.5 transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''
                            }`}
                    >
                        {loading ? '处理中...' : '确认创建'}
                    </button>
                </div>

                {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            </div>
        </div>
    );
};

export default AddGroupModal;
