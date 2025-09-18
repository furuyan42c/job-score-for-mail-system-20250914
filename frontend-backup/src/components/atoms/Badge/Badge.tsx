import React from 'react';
import { cn } from '@/lib/utils';
import { BadgeProps } from '@/types';
import { X } from 'lucide-react';

const badgeVariants = {
  default: 'bg-secondary-100 text-secondary-800 border-secondary-200',
  success: 'bg-success-100 text-success-800 border-success-200',
  warning: 'bg-warning-100 text-warning-800 border-warning-200',
  danger: 'bg-danger-100 text-danger-800 border-danger-200',
  info: 'bg-primary-100 text-primary-800 border-primary-200'
};

const badgeSizes = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-sm'
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  removable = false,
  onRemove,
  className,
  'data-testid': testId
}) => {
  return (
    <span
      className={cn(
        // Base styles
        'inline-flex items-center font-medium rounded-full border',

        // Variant styles
        badgeVariants[variant],

        // Size styles
        badgeSizes[size],

        // Removable padding adjustment
        removable && 'pr-1',

        className
      )}
      data-testid={testId}
    >
      <span>{children}</span>

      {removable && onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className={cn(
            'ml-1 inline-flex items-center justify-center rounded-full',
            'hover:bg-black hover:bg-opacity-10 focus:outline-none focus:bg-black focus:bg-opacity-10',
            'transition-colors duration-150',
            size === 'sm' && 'w-3 h-3',
            size === 'md' && 'w-4 h-4',
            size === 'lg' && 'w-5 h-5'
          )}
          data-testid={`${testId}-remove`}
        >
          <X
            className={cn(
              size === 'sm' && 'w-2 h-2',
              size === 'md' && 'w-3 h-3',
              size === 'lg' && 'w-3.5 h-3.5'
            )}
          />
        </button>
      )}
    </span>
  );
};