import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { ButtonProps } from '@/types';
import { Loader } from '../Loader';

const buttonVariants = {
  primary: 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 text-white',
  secondary: 'bg-secondary-100 hover:bg-secondary-200 focus:ring-secondary-500 text-secondary-900',
  danger: 'bg-danger-600 hover:bg-danger-700 focus:ring-danger-500 text-white',
  ghost: 'hover:bg-secondary-100 focus:ring-secondary-500 text-secondary-700',
  outline: 'border border-secondary-300 hover:bg-secondary-50 focus:ring-secondary-500 text-secondary-700'
};

const buttonSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base'
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      disabled = false,
      loading = false,
      onClick,
      type = 'button',
      icon,
      iconPosition = 'left',
      fullWidth = false,
      className,
      'data-testid': testId,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (!isDisabled && onClick) {
        onClick(event);
      }
    };

    return (
      <button
        ref={ref}
        type={type}
        onClick={handleClick}
        disabled={isDisabled}
        data-testid={testId}
        className={cn(
          // Base styles
          'relative inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',

          // Variant styles
          buttonVariants[variant],

          // Size styles
          buttonSizes[size],

          // Full width
          fullWidth && 'w-full',

          // Custom className
          className
        )}
        {...props}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader size="sm" />
          </div>
        )}

        <div className={cn('flex items-center gap-2', loading && 'invisible')}>
          {icon && iconPosition === 'left' && (
            <span className="flex-shrink-0">{icon}</span>
          )}

          {children && <span>{children}</span>}

          {icon && iconPosition === 'right' && (
            <span className="flex-shrink-0">{icon}</span>
          )}
        </div>
      </button>
    );
  }
);

Button.displayName = 'Button';