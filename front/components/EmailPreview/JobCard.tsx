import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { JobCardProps } from './types';
import {
  MapPin,
  Building2,
  Star,
  TrendingUp,
  Clock,
  ExternalLink
} from 'lucide-react';

export const JobCard: React.FC<JobCardProps> = ({
  job,
  previewMode,
  showMatchScore = true,
  compact = false,
  className
}) => {
  const formatSalary = (min?: number, max?: number, type?: string) => {
    if (!min && !max) return null;

    const formatNumber = (num: number) => {
      if (type === 'hourly') return `¥${num.toLocaleString()}`;
      if (type === 'monthly') return `¥${(num * 10000).toLocaleString()}万`;
      if (type === 'yearly') return `¥${(num * 10000).toLocaleString()}万`;
      return `¥${num.toLocaleString()}`;
    };

    if (min && max && min !== max) {
      return `${formatNumber(min)} - ${formatNumber(max)}`;
    }
    return formatNumber(min || max || 0);
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 80) return 'text-blue-600 bg-blue-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getMatchScoreIcon = (score: number) => {
    if (score >= 90) return <Star className="h-3 w-3 fill-current" />;
    if (score >= 80) return <TrendingUp className="h-3 w-3" />;
    return null;
  };

  // Plain text rendering
  if (previewMode === 'plaintext') {
    const salary = formatSalary(job.salaryMin, job.salaryMax, job.salaryType);
    return (
      <div className="border-b border-gray-200 pb-4 mb-4">
        <div className="font-semibold text-sm">{job.title}</div>
        <div className="text-sm text-gray-600">{job.companyName}</div>
        <div className="text-sm text-gray-600">{job.location}</div>
        {salary && <div className="text-sm">{salary}</div>}
        {showMatchScore && (
          <div className="text-sm">マッチ度: {job.matchScore}%</div>
        )}
        <div className="text-sm text-blue-600 mt-1">応募する: {job.applyUrl}</div>
      </div>
    );
  }

  // HTML rendering for mobile and desktop
  const cardClasses = cn(
    'transition-all duration-200 hover:shadow-md border border-gray-200',
    compact ? 'p-3' : 'p-4',
    previewMode === 'mobile' ? 'rounded-lg' : 'rounded-lg',
    className
  );

  const salary = formatSalary(job.salaryMin, job.salaryMax, job.salaryType);

  return (
    <Card className={cardClasses}>
      <CardContent className={cn('p-0')}>
        <div className="flex gap-3">
          {/* Company Logo */}
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              {job.companyLogo ? (
                <img
                  src={job.companyLogo}
                  alt={job.companyName}
                  className="w-8 h-8 object-contain"
                />
              ) : (
                <Building2 className="h-6 w-6 text-gray-400" />
              )}
            </div>
          </div>

          {/* Job Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className={cn(
                'font-semibold text-gray-900 line-clamp-2',
                compact ? 'text-sm' : 'text-base'
              )}>
                {job.title}
              </h3>

              {/* Match Score */}
              {showMatchScore && (
                <div className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium flex-shrink-0',
                  getMatchScoreColor(job.matchScore)
                )}>
                  {getMatchScoreIcon(job.matchScore)}
                  {job.matchScore}%
                </div>
              )}
            </div>

            {/* Company Name */}
            <div className={cn(
              'text-gray-600 mb-2',
              compact ? 'text-sm' : 'text-sm'
            )}>
              {job.companyName}
            </div>

            {/* Location and Salary */}
            <div className="flex flex-wrap items-center gap-4 mb-3 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                <span>{job.location}</span>
              </div>
              {salary && (
                <div className="font-semibold text-gray-900">
                  {salary}
                  {job.salaryType === 'hourly' && '/時間'}
                  {job.salaryType === 'monthly' && '/月'}
                  {job.salaryType === 'yearly' && '/年'}
                </div>
              )}
            </div>

            {/* Tags */}
            {job.tags && job.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {job.tags.slice(0, 3).map((tag, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="text-xs"
                  >
                    {tag}
                  </Badge>
                ))}
                {job.isNew && (
                  <Badge className="text-xs bg-red-100 text-red-800 border-red-200">
                    <Clock className="h-3 w-3 mr-1" />
                    新着
                  </Badge>
                )}
                {job.isPopular && (
                  <Badge className="text-xs bg-orange-100 text-orange-800 border-orange-200">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    人気
                  </Badge>
                )}
              </div>
            )}

            {/* Apply Button */}
            <div className="pt-2">
              <Button
                size={compact ? "sm" : "default"}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => window.open(job.applyUrl, '_blank')}
              >
                応募する
                <ExternalLink className="h-3 w-3 ml-1" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};