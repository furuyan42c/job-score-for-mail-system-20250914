import React from 'react';
import { cn } from '@/lib/utils';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse';
  className?: string;
  'data-testid'?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8'
};

const SpinnerLoader: React.FC<LoaderProps> = ({ size = 'md', className }) => (
  <svg
    className={cn(
      'animate-spin text-current',
      sizeClasses[size],
      className
    )}
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

const DotsLoader: React.FC<LoaderProps> = ({ size = 'md', className }) => {
  const dotSize = size === 'sm' ? 'w-1 h-1' : size === 'md' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  return (
    <div className={cn('flex items-center space-x-1', className)}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn(
            'bg-current rounded-full animate-pulse',
            dotSize
          )}
          style={{
            animationDelay: `${i * 0.2}s`,
            animationDuration: '1.4s'
          }}
        />
      ))}
    </div>
  );
};

const PulseLoader: React.FC<LoaderProps> = ({ size = 'md', className }) => (
  <div
    className={cn(
      'bg-current rounded-full animate-pulse-slow',
      sizeClasses[size],
      className
    )}
  />
);

export const Loader: React.FC<LoaderProps> = ({
  size = 'md',
  variant = 'spinner',
  className,
  'data-testid': testId
}) => {
  const LoaderComponent = {
    spinner: SpinnerLoader,
    dots: DotsLoader,
    pulse: PulseLoader
  }[variant];

  return (
    <div
      className="inline-flex items-center justify-center"
      data-testid={testId}
    >
      <LoaderComponent size={size} className={className} />
    </div>
  );
};