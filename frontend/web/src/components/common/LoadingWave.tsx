import React from 'react';
import clsx from 'clsx';

interface LoadingWaveProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
  text?: string;
}

const LoadingWave: React.FC<LoadingWaveProps> = ({
  size = 'medium',
  className,
  text = '加载中...'
}) => {
  const sizeClasses = {
    small: 'w-1 h-4',
    medium: 'w-2 h-6',
    large: 'w-3 h-8',
  };

  return (
    <div className={clsx('flex flex-col items-center justify-center', className)}>
      <div className="flex items-center space-x-1 mb-2">
        {[0, 150, 300].map((delay) => (
          <div
            key={delay}
            className={clsx(
              'bg-[var(--color-ruo-purple)] rounded-full pulse-wave',
              sizeClasses[size]
            )}
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
      {text && (
        <p className="text-sm text-[var(--color-text-secondary)]">
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingWave;