import React, { useState } from 'react';
import { createGroup } from '@/api/favorites';
import Toast from '@/components/common/Toast';
import { X, FolderPlus } from 'lucide-react';

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
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md flex items-center justify-center z-[60] p-4 animate-in fade-in duration-300">
            <div className="bg-card w-full max-w-md relative overflow-hidden border border-border rounded-3xl shadow-[0_32px_64px_-12px_rgba(0,0,0,0.2)]">
                {/* Header Section */}
                <div className="p-6 border-b border-border flex items-center justify-between bg-muted/30 relative">
                    <div className="flex items-center">
                        <div className="w-1.5 h-6 bg-gradient-to-b from-orange-400 to-orange-600 rounded-full mr-4 shadow-[0_0_12px_rgba(249,115,22,0.4)]"></div>
                        <div>
                            <h3 className="text-xl font-black text-foreground tracking-tight">新建自选分组</h3>
                            <p className="text-xs text-muted-foreground mt-0.5 font-medium">按行业或题材管理您的股票</p>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        type="button"
                        className="p-2 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition-all active:scale-95"
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-orange-500/5 rounded-full blur-3xl pointer-events-none"></div>
                </div>

                {/* Content Section */}
                <div className="p-8 space-y-6 relative z-10">
                    <div className="space-y-2">
                        <label className="text-[13px] font-bold text-muted-foreground flex items-center gap-1.5 ml-1">
                            <FolderPlus className="w-3.5 h-3.5" />
                            <span>分组名称</span>
                        </label>
                        <input
                            type="text"
                            placeholder="例如：科技龙头、我的持仓"
                            value={groupName}
                            onChange={(e) => setGroupName(e.target.value)}
                            className="w-full px-5 py-4 bg-muted/50 border border-slate-200/50 rounded-2xl text-foreground placeholder-muted-foreground/30 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500/30 transition-all font-bold"
                            autoFocus
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-[13px] font-bold text-muted-foreground flex items-center gap-1.5 ml-1">
                            <span>备注说明</span>
                            <span className="text-[10px] font-normal opacity-50">(可选)</span>
                        </label>
                        <input
                            type="text"
                            placeholder="关于该分组的简单描述..."
                            value={groupDescription}
                            onChange={(e) => setGroupDescription(e.target.value)}
                            className="w-full px-5 py-4 bg-muted/50 border border-slate-200/50 rounded-2xl text-foreground placeholder-muted-foreground/30 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500/30 transition-all font-bold"
                        />
                    </div>
                </div>

                {/* Footer Section */}
                <div className="p-8 pt-0 flex space-x-4 relative z-10">
                    <button
                        onClick={onClose}
                        type="button"
                        className="flex-1 px-6 py-4 rounded-2xl border border-slate-200 text-slate-500 hover:bg-muted hover:text-foreground transition-all font-black text-sm active:scale-95"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleCreateGroup}
                        type="button"
                        disabled={loading}
                        className={`
                            flex-1 px-6 py-4 rounded-2xl bg-gradient-to-br from-orange-400 to-orange-600 text-white font-black text-sm shadow-lg shadow-orange-500/20 hover:shadow-orange-500/30 hover:-translate-y-0.5 active:scale-95 transition-all
                            ${loading ? 'opacity-70 cursor-not-allowed saturate-0' : ''}
                        `}
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
