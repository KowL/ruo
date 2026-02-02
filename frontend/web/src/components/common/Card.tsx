import React from 'react';
import clsx from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ children, className, onClick }) => {
  return (
    <div
      className={clsx(
        'rounded-lg p-4',
        onClick && 'cursor-pointer hover:opacity-80 transition-opacity',
        className
      )}
      style={{
        backgroundColor: 'var(--color-surface-2)',
        border: '1px solid var(--color-surface-4)'
      }}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
