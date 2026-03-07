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
        'rounded-xl p-4 bg-card text-card-foreground border border-border transition-all',
        onClick && 'cursor-pointer hover:bg-muted/80',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
