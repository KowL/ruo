import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.locale('zh-cn');
dayjs.extend(relativeTime);

// 格式化数字
export const formatNumber = (num: number, decimals: number = 2): string => {
  return num.toFixed(decimals);
};

// 格式化金额
export const formatMoney = (amount: number | undefined | null): string => {
  const value = amount ?? 0;
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

// 格式化百分比
export const formatPercent = (value: number, decimals: number = 2): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(decimals)}%`;
};

// 格式化时间
export const formatTime = (time: string | Date): string => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

// 相对时间
export const formatRelativeTime = (time: string | Date): string => {
  return dayjs(time).fromNow();
};

// 判断涨跌
export const getRiseOrFall = (value: number): 'rise' | 'fall' | 'neutral' => {
  if (value > 0) return 'rise';
  if (value < 0) return 'fall';
  return 'neutral';
};

// 获取涨跌颜色类
export const getRiseOrFallClass = (value: number): string => {
  const type = getRiseOrFall(value);
  if (type === 'rise') return 'text-red-600';
  if (type === 'fall') return 'text-green-600';
  return 'text-gray-600';
};
