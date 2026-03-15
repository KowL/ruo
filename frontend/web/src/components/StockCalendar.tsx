/**
 * 股票交易日期选择器组件
 * Stock Trading Calendar Component
 * 
 * 特性：
 * - 只允许选择交易日（周一到周五）
 * - 周末日期灰掉不可点击
 * - 默认显示最近交易日
 * - 支持自定义日期范围
 * - 支持左右对齐 (align: 'left' | 'right')
 */
import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';

interface StockCalendarProps {
  value: string;
  onChange: (date: string) => void;
  minDate?: string;  // 最小日期 YYYY-MM-DD
  maxDate?: string;  // 最大日期 YYYY-MM-DD
  placeholder?: string;
  className?: string;
  align?: 'left' | 'right';
  iconOnly?: boolean;
}

export const StockCalendar: React.FC<StockCalendarProps> = ({
  value,
  onChange,
  minDate,
  maxDate,
  placeholder = '选择日期',
  className = '',
  align = 'left',
  iconOnly = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewDate, setViewDate] = useState(new Date(value || new Date()));
  
  // 默认范围：过去1年到今天
  const today = new Date();
  const defaultMinDate = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
  
  const min = minDate ? new Date(minDate) : defaultMinDate;
  const max = maxDate ? new Date(maxDate) : today;

  // 点击外部关闭逻辑
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);
  
  // 判断是否为交易日
  const isTradingDay = (date: Date) => {
    const day = date.getDay();
    return day !== 0 && day !== 6;
  };
  
  // 获取月份天数
  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };
  
  // 获取月初是周几
  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };
  
  // 渲染日历
  const renderCalendar = () => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const daysInMonth = getDaysInMonth(viewDate);
    const firstDay = getFirstDayOfMonth(viewDate);
    const selected = value ? new Date(value) : null;
    
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    const cells = [];
    
    // 1. 周标题
    weekDays.forEach((d, i) => {
      cells.push(
        <div key={`weekday-${i}`} className={`text-center text-[11px] font-semibold py-2 ${i === 0 || i === 6 ? 'text-red-400' : 'text-slate-400'}`}>
          {d}
        </div>
      );
    });
    
    // 2. 填充前导空格
    for (let i = 0; i < firstDay; i++) {
      cells.push(<div key={`empty-${i}`} className="h-8" />);
    }
    
    // 3. 日期格子
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDate = new Date(year, month, day);
      const isWeekend = currentDate.getDay() === 0 || currentDate.getDay() === 6;
      const isDisabled = currentDate > max || currentDate < min || isWeekend;
      const isSelected = selected && selected.getFullYear() === year && 
                        selected.getMonth() === month && 
                        selected.getDate() === day;
      const isToday = today.getFullYear() === year && 
                      today.getMonth() === month && 
                      today.getDate() === day;
      
      cells.push(
        <button
          key={`day-${day}`}
          type="button"
          disabled={isDisabled}
          onClick={() => {
            if (!isDisabled) {
              onChange(currentDate.toISOString().split('T')[0]);
              setIsOpen(false);
            }
          }}
          className={`h-9 w-9 rounded-xl text-sm font-bold transition-all flex items-center justify-center mx-auto
            ${isDisabled 
              ? 'text-slate-200 cursor-not-allowed' 
              : isSelected 
                ? 'bg-orange-500 text-white shadow-lg shadow-orange-200' 
                : isToday 
                  ? 'border-2 border-orange-500 text-orange-500 bg-orange-50'
                  : 'text-slate-700 hover:bg-slate-100 hover:text-orange-500'
            }
            ${isWeekend && !isDisabled ? 'text-red-400' : ''}
          `}
        >
          {day}
        </button>
      );
    }
    
    return cells;
  };

  const changeMonth = (offset: number) => {
    const newDate = new Date(viewDate);
    newDate.setMonth(newDate.getMonth() + offset);
    if (newDate >= min && newDate <= max) {
      setViewDate(newDate);
    }
  };
  
  // 格式化显示日期
  const formatDisplay = () => {
    if (!value) return placeholder;
    const date = new Date(value);
    return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
  };
  
  // 跳转到最近交易日
  const goToLatestTradingDay = () => {
    let targetDate = new Date(today);
    while (!isTradingDay(targetDate) && targetDate >= min) {
      targetDate.setDate(targetDate.getDate() - 1);
    }
    if (targetDate >= min) {
      onChange(targetDate.toISOString().split('T')[0]);
    }
    setIsOpen(false);
  };
  
  return (
    <div className={`relative inline-block ${className}`} ref={containerRef}>
      <button
        type="button"
        title={formatDisplay()}
        onClick={() => setIsOpen(!isOpen)}
        className={`
          bg-slate-50 border border-slate-200/50 rounded-xl outline-none 
          flex items-center gap-2 hover:bg-slate-100 transition-all active:scale-95
          ${iconOnly ? 'p-2.5 aspect-square' : 'px-4 py-2 text-sm'}
          ${isOpen ? 'ring-2 ring-orange-500/20 border-orange-200' : ''}
        `}
      >
        <Calendar className={`${iconOnly ? 'w-5 h-5' : 'w-4 h-4'} text-slate-400`} />
        {!iconOnly && (
          <>
            <span className="font-bold text-slate-700">{formatDisplay()}</span>
            <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
          </>
        )}
      </button>
      
      {isOpen && (
        <div 
          className={`absolute top-full mt-3 bg-white rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-slate-100 p-5 z-[100] w-[310px] animate-in fade-in zoom-in duration-300
            ${align === 'right' ? 'right-0 origin-top-right' : 'left-0 origin-top-left'}
          `}
        >
          {/* 月份导航 */}
          <div className="flex items-center justify-between mb-5">
            <button
              type="button"
              onClick={() => changeMonth(-1)}
              className="p-2 hover:bg-slate-100 rounded-xl transition-all active:scale-90"
            >
              <ChevronLeft className="w-5 h-5 text-slate-600" />
            </button>
            <span className="font-black text-slate-800 text-lg tracking-tight">
              {viewDate.getFullYear()}年{String(viewDate.getMonth() + 1).padStart(2, '0')}月
            </span>
            <button
              type="button"
              onClick={() => changeMonth(1)}
              className="p-2 hover:bg-slate-100 rounded-xl transition-all active:scale-90"
            >
              <ChevronRight className="w-5 h-5 text-slate-600" />
            </button>
          </div>
          
          {/* 日历网格 - 包含表头 */}
          <div className="grid grid-cols-7 gap-y-1 gap-x-1">
            {renderCalendar()}
          </div>
          
          {/* 快捷按钮 */}
          <div className="flex justify-between mt-6 pt-4 border-t border-slate-50">
            <button
              type="button"
              onClick={goToLatestTradingDay}
              className="text-xs text-orange-600 hover:text-orange-700 font-bold transition-all px-2 py-1 hover:bg-orange-50 rounded-lg"
            >
              最近交易日
            </button>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-xs text-slate-400 hover:text-slate-600 font-bold transition-all px-2 py-1 hover:bg-slate-50 rounded-lg"
            >
              收起
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// 工具函数：获取最近交易日
export const getLatestTradingDay = (date: Date = new Date()): Date => {
  const day = date.getDay();
  let targetDate = new Date(date);
  
  if (day === 0) { // 周日
    targetDate.setDate(targetDate.getDate() - 2); // 上周五
  } else if (day === 6) { // 周六
    targetDate.setDate(targetDate.getDate() - 1); // 上周五
  }
  
  return targetDate;
};

// 工具函数：格式化日期为 YYYY-MM-DD
export const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

export default StockCalendar;
