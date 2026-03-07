import React, { useState, useEffect } from 'react';
import { createAlertRule, getAlertRules } from '@/api/alert';
import type { AlertRule, CreateAlertRuleRequest } from '@/types/alert';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Toast from '@/components/common/Toast';

interface AlertSettingModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: number;
  symbol: string;
  name: string;
  currentPrice: number;
  costPrice: number;
}

const AlertSettingModal: React.FC<AlertSettingModalProps> = ({
  isOpen,
  onClose,
  portfolioId,
  symbol,
  name,
  currentPrice,
  costPrice,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [existingRules, setExistingRules] = useState<AlertRule[]>([]);

  // 表单状态
  const [alertType, setAlertType] = useState<'profit_loss' | 'price_change' | 'target_price'>('profit_loss');
  const [thresholdValue, setThresholdValue] = useState<string>('');
  const [compareOperator, setCompareOperator] = useState<'>=' | '<=' | '>' | '<'>('>=');
  const [cooldownMinutes, setCooldownMinutes] = useState<number>(60);
  const [notes, setNotes] = useState<string>('');

  // 加载现有预警规则
  useEffect(() => {
    if (isOpen && portfolioId) {
      loadExistingRules();
    }
  }, [isOpen, portfolioId]);

  const loadExistingRules = async () => {
    try {
      setLoading(true);
      const res = await getAlertRules(portfolioId);
      setExistingRules(res.data || []);
    } catch (error) {
      console.error('加载预警规则失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!thresholdValue || isNaN(Number(thresholdValue))) {
      setToast({ message: '请输入有效的阈值', type: 'error' });
      return;
    }

    try {
      setSaving(true);
      const data: CreateAlertRuleRequest = {
        portfolioId,
        alertType,
        thresholdValue: Number(thresholdValue),
        compareOperator,
        cooldownMinutes,
        notes: notes || undefined,
      };

      await createAlertRule(data);
      setToast({ message: '预警设置成功！', type: 'success' });

      // 重置表单并刷新列表
      setThresholdValue('');
      setNotes('');
      loadExistingRules();
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || '设置失败', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (ruleId: number) => {
    if (!window.confirm('确定要删除这条预警规则吗？')) return;

    try {
      const { deleteAlertRule } = await import('@/api/alert');
      await deleteAlertRule(ruleId);
      setToast({ message: '删除成功', type: 'success' });
      loadExistingRules();
    } catch (error) {
      setToast({ message: '删除失败', type: 'error' });
    }
  };

  const getAlertTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      profit_loss: '盈亏比例',
      price_change: '涨跌幅',
      target_price: '目标价',
    };
    return labels[type] || type;
  };

  const getOperatorLabel = (op: string) => {
    const labels: Record<string, string> = {
      '>=': '大于等于',
      '<=': '小于等于',
      '>': '大于',
      '<': '小于',
    };
    return labels[op] || op;
  };

  // 快速设置按钮
  const quickSettings = [
    { label: '止盈 +15%', type: 'profit_loss' as const, op: '>=' as const, value: 15 },
    { label: '止损 -7%', type: 'profit_loss' as const, op: '<=' as const, value: -7 },
    { label: '涨停监控', type: 'price_change' as const, op: '>=' as const, value: 9.5 },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-card text-card-foreground border border-border rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="text-lg font-semibold">
            预警设置 - {name} ({symbol})
          </h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-xl"
          >
            ×
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* 当前价格信息 */}
          <div className="flex justify-between text-sm bg-muted/50 p-3 rounded-xl border border-border">
            <span>当前价: ¥{currentPrice.toFixed(2)}</span>
            <span>成本价: ¥{costPrice.toFixed(2)}</span>
            <span className={currentPrice >= costPrice ? 'text-profit-up' : 'text-profit-down'}>
              盈亏: {((currentPrice - costPrice) / costPrice * 100).toFixed(2)}%
            </span>
          </div>

          {/* 快速设置 */}
          <div className="flex gap-2 flex-wrap">
            <span className="text-sm text-muted-foreground py-1">快速设置:</span>
            {quickSettings.map((setting) => (
              <button
                key={setting.label}
                type="button"
                onClick={() => {
                  setAlertType(setting.type);
                  setCompareOperator(setting.op);
                  setThresholdValue(String(setting.value));
                }}
                className="px-3 py-1 text-xs bg-muted hover:bg-primary hover:text-primary-foreground rounded transition-colors border border-border"
              >
                {setting.label}
              </button>
            ))}
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-1">预警类型</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value as any)}
                  className="w-full p-2 rounded bg-card border border-border"
                >
                  <option value="profit_loss">盈亏比例</option>
                  <option value="price_change">涨跌幅</option>
                  <option value="target_price">目标价</option>
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">比较方式</label>
                <select
                  value={compareOperator}
                  onChange={(e) => setCompareOperator(e.target.value as any)}
                  className="w-full p-2 rounded bg-card border border-border"
                >
                  <option value=">=">大于等于</option>
                  <option value="<=">小于等于</option>
                  <option value=">">大于</option>
                  <option value="<">小于</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm mb-1">阈值</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  step="0.01"
                  value={thresholdValue}
                  onChange={(e) => setThresholdValue(e.target.value)}
                  placeholder={alertType === 'target_price' ? '目标价格' : '百分比数值'}
                  className="flex-1 p-2 rounded bg-card border border-border"
                />
                <span className="text-sm text-muted-foreground w-12">
                  {alertType === 'target_price' ? '元' : '%'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {alertType === 'profit_loss' && '相对于成本价的盈亏比例，如15表示盈利15%触发'}
                {alertType === 'price_change' && '当日涨跌幅，如9.5表示涨幅9.5%触发'}
                {alertType === 'target_price' && '股价达到指定价格时触发'}
              </p>
            </div>

            <div>
              <label className="block text-sm mb-1">冷却时间（分钟）</label>
              <select
                value={cooldownMinutes}
                onChange={(e) => setCooldownMinutes(Number(e.target.value))}
                className="w-full p-2 rounded bg-card border border-border"
              >
                <option value={15}>15分钟</option>
                <option value={30}>30分钟</option>
                <option value={60}>1小时</option>
                <option value={180}>3小时</option>
                <option value={360}>6小时</option>
                <option value={1440}>24小时</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                触发后在此时间内不会重复提醒
              </p>
            </div>

            <div>
              <label className="block text-sm mb-1">备注（可选）</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="如：止盈位、止损位等"
                className="w-full p-2 rounded bg-card border border-border"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={onClose}>
                取消
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? '保存中...' : '保存预警'}
              </Button>
            </div>
          </form>

          {/* 现有规则列表 */}
          {loading ? (
            <Loading text="加载中..." />
          ) : existingRules.length > 0 ? (
            <div className="mt-6 pt-4 border-t border-border">
              <h4 className="text-sm font-medium mb-3">已设置的预警</h4>
              <div className="space-y-2">
                {existingRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-xl border border-border text-sm"
                  >
                    <div>
                      <span className="font-medium">{getAlertTypeLabel(rule.alertType)}</span>
                      <span className="mx-2 text-muted-foreground">
                        {getOperatorLabel(rule.compareOperator)}
                      </span>
                      <span className="font-medium">
                        {rule.alertType === 'target_price' ? '¥' : ''}
                        {rule.thresholdValue}
                        {rule.alertType !== 'target_price' ? '%' : ''}
                      </span>
                      {rule.triggerCount > 0 && (
                        <span className="ml-2 text-xs text-muted-foreground">
                          已触发{rule.triggerCount}次
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-[hsl(var(--destructive))] hover:opacity-80 text-xs"
                    >
                      删除
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default AlertSettingModal;
