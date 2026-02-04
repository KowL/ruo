import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  loading = false,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseClass = 'px-4 py-2 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-white text-black hover:bg-white/90 active:scale-95',
    secondary: 'hover:opacity-80 active:scale-95',
    danger: 'hover:opacity-80 active:scale-95',
  };

  const variantStyles = {
    primary: { backgroundColor: 'var(--color-brand)', color: 'black' },
    secondary: { backgroundColor: 'var(--color-surface-3)', color: 'var(--color-text-primary)' },
    danger: { backgroundColor: 'var(--color-profit-up)', color: 'white' },
  };



  return (
    <button
      className={clsx(baseClass, variantClasses[variant], className)}
      style={variantStyles[variant]}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center justify-center">
          <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          处理中...
        </span>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;
