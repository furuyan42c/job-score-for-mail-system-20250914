'use client';

import React from 'react';
import { MetricCardProps } from '@/types';
import { clsx } from 'clsx';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  Briefcase,
  Target,
  Mail,
  Activity,
  DollarSign,
  Clock,
} from 'lucide-react';

export default function MetricCard({
  metric,
  size = 'md',
  showTrend = true,
  onClick,
  className,
  'data-testid': testId,
}: MetricCardProps) {
  const getIcon = (iconName?: string) => {
    const iconClasses = clsx('flex-shrink-0', {
      'w-4 h-4': size === 'sm',
      'w-6 h-6': size === 'md',
      'w-8 h-8': size === 'lg',
    });

    const iconMap: Record<string, React.ReactNode> = {
      users: <Users className={iconClasses} />,
      briefcase: <Briefcase className={iconClasses} />,
      target: <Target className={iconClasses} />,
      mail: <Mail className={iconClasses} />,
      activity: <Activity className={iconClasses} />,
      dollar: <DollarSign className={iconClasses} />,
      clock: <Clock className={iconClasses} />,
    };

    return iconMap[iconName || 'activity'] || <Activity className={iconClasses} />;
  };

  const getTrendIcon = () => {
    const iconClasses = 'w-4 h-4';

    if (metric.trend === 'up') {
      return <TrendingUp className={`${iconClasses} text-green-600`} />;
    } else if (metric.trend === 'down') {
      return <TrendingDown className={`${iconClasses} text-red-600`} />;
    }
    return <Minus className={`${iconClasses} text-gray-400`} />;
  };

  const getColorClasses = (color?: string) => {
    const colorMap = {
      blue: 'text-blue-600 bg-blue-50',
      green: 'text-green-600 bg-green-50',
      yellow: 'text-yellow-600 bg-yellow-50',
      red: 'text-red-600 bg-red-50',
      purple: 'text-purple-600 bg-purple-50',
    };

    return colorMap[color as keyof typeof colorMap] || 'text-gray-600 bg-gray-50';
  };

  const formatValue = (value: number | string) => {
    if (metric.format === 'currency' && typeof value === 'number') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value);
    }

    if (metric.format === 'percentage' && typeof value === 'number') {
      return `${value}%`;
    }

    if (metric.format === 'duration' && typeof value === 'number') {
      const hours = Math.floor(value / 3600);
      const minutes = Math.floor((value % 3600) / 60);
      if (hours > 0) return `${hours}h ${minutes}m`;
      if (minutes > 0) return `${minutes}m`;
      return `${value}s`;
    }

    return value;
  };

  const formatChange = (change?: number) => {
    if (change === undefined) return '';
    const prefix = change >= 0 ? '+' : '';
    return `${prefix}${change.toFixed(1)}%`;
  };

  const getChangeColor = (change?: number) => {
    if (change === undefined) return 'text-gray-500';
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  return (
    <div
      className={clsx(
        'bg-white rounded-lg border shadow-sm transition-all duration-200',
        {
          'p-4': size === 'sm',
          'p-6': size === 'md',
          'p-8': size === 'lg',
          'cursor-pointer hover:shadow-md hover:border-gray-300': onClick,
          'hover:shadow-sm': !onClick,
        },
        className
      )}
      onClick={onClick}
      data-testid={testId}
    >
      <div className="flex items-center justify-between">
        {/* Icon and Label */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-3 mb-2">
            <div
              className={clsx(
                'p-2 rounded-md',
                getColorClasses(metric.color)
              )}
            >
              {getIcon(metric.icon)}
            </div>
            {size !== 'sm' && (
              <div className="flex-1 min-w-0">
                <h3
                  className={clsx(
                    'font-medium text-gray-900 truncate',
                    {
                      'text-sm': size === 'sm',
                      'text-base': size === 'md',
                      'text-lg': size === 'lg',
                    }
                  )}
                >
                  {metric.label}
                </h3>
              </div>
            )}
          </div>

          {size === 'sm' && (
            <h3 className="text-sm font-medium text-gray-900 truncate mb-1">
              {metric.label}
            </h3>
          )}

          {/* Value */}
          <div
            className={clsx(
              'font-bold text-gray-900',
              {
                'text-lg': size === 'sm',
                'text-2xl': size === 'md',
                'text-3xl': size === 'lg',
              }
            )}
          >
            {formatValue(metric.value)}
          </div>

          {/* Previous value (subtle) */}
          {metric.previousValue && (
            <div className="text-xs text-gray-400 mt-1">
              Previous: {formatValue(metric.previousValue)}
            </div>
          )}
        </div>

        {/* Trend indicator */}
        {showTrend && metric.trend && (
          <div className="flex flex-col items-end space-y-1">
            {getTrendIcon()}
            {metric.change !== undefined && (
              <span
                className={clsx(
                  'text-sm font-medium',
                  getChangeColor(metric.change)
                )}
              >
                {formatChange(metric.change)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Description or additional info */}
      {size === 'lg' && metric.change !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>
              {metric.trend === 'up' && 'Increased'}
              {metric.trend === 'down' && 'Decreased'}
              {metric.trend === 'stable' && 'No change'}
            </span>
            <span>from previous period</span>
          </div>
        </div>
      )}
    </div>
  );
}