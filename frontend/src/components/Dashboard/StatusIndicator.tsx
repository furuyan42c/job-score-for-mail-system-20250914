'use client';

import React from 'react';
import { StatusIndicatorProps } from '@/types';
import { clsx } from 'clsx';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Loader2,
} from 'lucide-react';

export default function StatusIndicator({
  status,
  label,
  size = 'md',
  showLabel = true,
  className,
  'data-testid': testId,
}: StatusIndicatorProps) {
  const getStatusConfig = () => {
    const configs = {
      up: {
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        label: 'Online',
        dotColor: 'bg-green-500',
      },
      down: {
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        label: 'Offline',
        dotColor: 'bg-red-500',
      },
      degraded: {
        icon: AlertTriangle,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        label: 'Degraded',
        dotColor: 'bg-yellow-500',
      },
      running: {
        icon: Loader2,
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        label: 'Running',
        dotColor: 'bg-blue-500',
        animate: true,
      },
      completed: {
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        label: 'Completed',
        dotColor: 'bg-green-500',
      },
      failed: {
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        label: 'Failed',
        dotColor: 'bg-red-500',
      },
      pending: {
        icon: Clock,
        color: 'text-gray-600',
        bgColor: 'bg-gray-100',
        label: 'Pending',
        dotColor: 'bg-gray-500',
      },
    };

    return configs[status] || configs.pending;
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const sizeClasses = {
    sm: {
      icon: 'w-3 h-3',
      container: 'text-xs',
      dot: 'w-2 h-2',
      spacing: 'space-x-1',
    },
    md: {
      icon: 'w-4 h-4',
      container: 'text-sm',
      dot: 'w-3 h-3',
      spacing: 'space-x-2',
    },
    lg: {
      icon: 'w-5 h-5',
      container: 'text-base',
      dot: 'w-4 h-4',
      spacing: 'space-x-2',
    },
  };

  const currentSize = sizeClasses[size];
  const displayLabel = label || config.label;

  // Icon variant
  if (!showLabel) {
    return (
      <div
        className={clsx(
          'inline-flex items-center justify-center rounded-full',
          config.bgColor,
          {
            'p-1': size === 'sm',
            'p-1.5': size === 'md',
            'p-2': size === 'lg',
          },
          className
        )}
        title={displayLabel}
        data-testid={testId}
      >
        <Icon
          className={clsx(
            currentSize.icon,
            config.color,
            {
              'animate-spin': config.animate,
            }
          )}
        />
      </div>
    );
  }

  // Badge variant with label
  return (
    <div
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-1',
        config.bgColor,
        currentSize.container,
        currentSize.spacing,
        className
      )}
      data-testid={testId}
    >
      {/* Status dot */}
      <div
        className={clsx(
          'rounded-full flex-shrink-0',
          config.dotColor,
          currentSize.dot,
          {
            'animate-pulse': config.animate,
          }
        )}
      />

      {/* Label */}
      <span className={clsx('font-medium', config.color)}>
        {displayLabel}
      </span>
    </div>
  );
}