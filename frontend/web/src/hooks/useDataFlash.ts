import { useEffect, useRef, useState } from 'react';

/**
 * 自定义Hook：当数据变化时添加闪烁效果
 * @param value 要监听的数据值
 * @param deps 依赖项数组
 */
export const useDataFlash = (value: any, deps: React.DependencyList = []) => {
  const prevValueRef = useRef(value);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 检测数值变化
    if (prevValueRef.current !== value && elementRef.current) {
      // 添加闪烁动画类
      elementRef.current.classList.add('data-flash');

      // 动画结束后移除类
      const animationEnd = () => {
        if (elementRef.current) {
          elementRef.current.classList.remove('data-flash');
        }
      };

      elementRef.current.addEventListener('animationend', animationEnd);

      return () => {
        if (elementRef.current) {
          elementRef.current.removeEventListener('animationend', animationEnd);
        }
      };
    }

    prevValueRef.current = value;
  }, [value, ...deps]);

  return elementRef;
};

/**
 * 数据跳动组件
 */
interface DataFlashProps {
  value: any;
  children: React.ReactNode;
  className?: string;
  isPositive?: boolean;
}

export const DataFlash: React.FC<DataFlashProps> = ({ value, children, className, isPositive }) => {
  const prevValue = useRef(value);
  const [flashClass, setFlashClass] = useState<string>('');

  useEffect(() => {
    if (prevValue.current !== value) {
      // 根据涨跌决定闪烁颜色
      const flashColor = isPositive
        ? 'rgba(246, 53, 56, 0.2)' // 涨 - 红色
        : 'rgba(16, 185, 129, 0.2)'; // 跌 - 绿色

      setFlashClass(`data-flash`);
      prevValue.current = value;

      // 300ms后移除闪烁效果
      const timer = setTimeout(() => {
        setFlashClass('');
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [value, isPositive]);

  return (
    <div className={`${flashClass} ${className || ''}`}>
      {children}
    </div>
  );
};

export default useDataFlash;