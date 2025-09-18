import React from 'react';
import { cn, formatCurrency, formatRelativeTime, getJobTypeDisplay, getLocationTypeDisplay } from '@/lib/utils';
import { Avatar, Badge, Typography } from '@/components/atoms';
import { Job } from '@/types';
import { MapPin, Clock, Building2, Users } from 'lucide-react';

interface JobCardProps {
  job: Job;
  variant?: 'default' | 'compact' | 'featured';
  onClick?: (job: Job) => void;
  onSave?: (job: Job) => void;
  onApply?: (job: Job) => void;
  showActions?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const JobCard: React.FC<JobCardProps> = ({
  job,
  variant = 'default',
  onClick,
  onSave,
  onApply,
  showActions = true,
  className,
  'data-testid': testId
}) => {
  const isCompact = variant === 'compact';
  const isFeatured = variant === 'featured';

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger card click if clicking on action buttons
    if ((e.target as HTMLElement).closest('[data-action-button]')) {
      return;
    }
    onClick?.(job);
  };

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSave?.(job);
  };

  const handleApply = (e: React.MouseEvent) => {
    e.stopPropagation();
    onApply?.(job);
  };

  return (
    <div
      className={cn(
        'bg-white border border-secondary-200 rounded-lg transition-all duration-200',
        'hover:shadow-medium hover:border-secondary-300',
        isFeatured && 'ring-2 ring-primary-200 border-primary-300',
        onClick && 'cursor-pointer',
        isCompact ? 'p-4' : 'p-6',
        className
      )}
      onClick={handleCardClick}
      data-testid={testId}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Company Logo */}
          <Avatar
            src={job.companyLogo}
            name={job.company}
            size={isCompact ? 'sm' : 'md'}
            shape="square"
          />

          {/* Job Info */}
          <div className="flex-1 min-w-0">
            <Typography
              variant={isCompact ? 'body' : 'h6'}
              weight="semibold"
              className="text-secondary-900 mb-1"
              truncate
            >
              {job.title}
            </Typography>

            <div className="flex items-center gap-2 mb-2">
              <Typography variant="body" weight="medium" color="secondary">
                {job.company}
              </Typography>
              {job.companySize && (
                <>
                  <span className="text-secondary-300">•</span>
                  <div className="flex items-center gap-1 text-secondary-500">
                    <Users className="w-3 h-3" />
                    <Typography variant="caption">
                      {job.companySize}
                    </Typography>
                  </div>
                </>
              )}
            </div>

            {/* Meta Information */}
            <div className="flex items-center gap-4 text-secondary-500">
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                <Typography variant="caption">
                  {job.location} • {getLocationTypeDisplay(job.locationType)}
                </Typography>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <Typography variant="caption">
                  {formatRelativeTime(job.postedAt)}
                </Typography>
              </div>
            </div>
          </div>
        </div>

        {/* Featured Badge */}
        {isFeatured && (
          <Badge variant="info" size="sm">
            Featured
          </Badge>
        )}
      </div>

      {/* Job Details */}
      {!isCompact && (
        <div className="mb-4">
          <Typography
            variant="body"
            className="text-secondary-600 line-clamp-2"
          >
            {job.description}
          </Typography>
        </div>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        <Badge variant="default" size="sm">
          {getJobTypeDisplay(job.jobType)}
        </Badge>
        <Badge variant="default" size="sm">
          {job.experienceLevel}
        </Badge>
        {job.skills.slice(0, isCompact ? 2 : 3).map((skill) => (
          <Badge key={skill} variant="default" size="sm">
            {skill}
          </Badge>
        ))}
        {job.skills.length > (isCompact ? 2 : 3) && (
          <Badge variant="default" size="sm">
            +{job.skills.length - (isCompact ? 2 : 3)} more
          </Badge>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        {/* Salary */}
        <div>
          <Typography variant="body" weight="semibold" color="primary">
            {formatCurrency(job.salary.min)} - {formatCurrency(job.salary.max)}
          </Typography>
          <Typography variant="caption" className="text-secondary-500">
            per {job.salary.period}
          </Typography>
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              data-action-button
              className="px-3 py-1.5 text-sm text-secondary-600 hover:text-secondary-800 hover:bg-secondary-50 rounded transition-colors"
            >
              Save
            </button>
            <button
              onClick={handleApply}
              data-action-button
              className="px-4 py-1.5 text-sm bg-primary-600 text-white hover:bg-primary-700 rounded transition-colors"
            >
              Apply
            </button>
          </div>
        )}
      </div>

      {/* Additional Info for Featured Jobs */}
      {isFeatured && !isCompact && (
        <div className="mt-4 pt-4 border-t border-secondary-100">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="text-secondary-600">
                {job.applicantCount} applicants
              </span>
              <span className="text-secondary-600">
                {job.views} views
              </span>
            </div>
            {job.industry && (
              <Badge variant="info" size="sm">
                {job.industry}
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
};