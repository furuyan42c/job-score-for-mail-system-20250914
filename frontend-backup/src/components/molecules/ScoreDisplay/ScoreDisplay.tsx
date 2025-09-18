import React from 'react';
import { cn, calculateMatchPercentage, getMatchScoreColor } from '@/lib/utils';
import { Typography, Badge } from '@/components/atoms';
import { MatchFactor } from '@/types';

interface ScoreDisplayProps {
  score: number;
  maxScore?: number;
  variant?: 'default' | 'compact' | 'detailed';
  factors?: MatchFactor[];
  showPercentage?: boolean;
  showLabel?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({
  score,
  maxScore = 100,
  variant = 'default',
  factors = [],
  showPercentage = true,
  showLabel = true,
  className,
  'data-testid': testId
}) => {
  const percentage = calculateMatchPercentage(score, maxScore);
  const colorClass = getMatchScoreColor(percentage);
  const isCompact = variant === 'compact';
  const isDetailed = variant === 'detailed';

  const getScoreLabel = (score: number): string => {
    if (score >= 90) return 'Excellent Match';
    if (score >= 75) return 'Good Match';
    if (score >= 60) return 'Fair Match';
    if (score >= 40) return 'Poor Match';
    return 'No Match';
  };

  const getScoreVariant = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    if (score >= 40) return 'warning';
    return 'danger';
  };

  return (
    <div className={cn('flex flex-col', className)} data-testid={testId}>
      {/* Main Score Display */}
      <div className="flex items-center gap-3">
        {/* Circular Progress */}
        <div className="relative">
          <svg
            className={cn(
              'transform -rotate-90',
              isCompact ? 'w-12 h-12' : 'w-16 h-16'
            )}
            viewBox="0 0 36 36"
          >
            {/* Background Circle */}
            <path
              className="text-secondary-200"
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
            />
            {/* Progress Circle */}
            <path
              className={colorClass}
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray={`${percentage}, 100`}
            />
          </svg>

          {/* Score Text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Typography
              variant={isCompact ? 'caption' : 'body'}
              weight="bold"
              className={colorClass}
            >
              {showPercentage ? `${percentage}%` : score}
            </Typography>
          </div>
        </div>

        {/* Score Info */}
        <div className="flex-1">
          {showLabel && (
            <Typography
              variant={isCompact ? 'caption' : 'body'}
              weight="semibold"
              className="mb-1"
            >
              {getScoreLabel(percentage)}
            </Typography>
          )}

          <div className="flex items-center gap-2">
            <Badge
              variant={getScoreVariant(percentage) as any}
              size={isCompact ? 'sm' : 'md'}
            >
              {percentage}% Match
            </Badge>

            {!isCompact && (
              <Typography variant="caption" className="text-secondary-500">
                {score} / {maxScore} points
              </Typography>
            )}
          </div>
        </div>
      </div>

      {/* Detailed Factor Breakdown */}
      {isDetailed && factors.length > 0 && (
        <div className="mt-4 space-y-3">
          <Typography variant="body" weight="semibold">
            Match Factors
          </Typography>

          {factors.map((factor, index) => (
            <div key={index} className="space-y-1">
              <div className="flex items-center justify-between">
                <Typography variant="caption" weight="medium">
                  {factor.description}
                </Typography>
                <Typography variant="caption" className={getMatchScoreColor(factor.score)}>
                  {factor.score}%
                </Typography>
              </div>

              {/* Factor Progress Bar */}
              <div className="w-full bg-secondary-200 rounded-full h-1.5">
                <div
                  className={cn(
                    'h-1.5 rounded-full transition-all duration-300',
                    getMatchScoreColor(factor.score).replace('text-', 'bg-')
                  )}
                  style={{ width: `${factor.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};