import React, { useState } from 'react';
import { cn, formatCurrency, formatRelativeTime, getJobTypeDisplay, getLocationTypeDisplay } from '@/lib/utils';
import { Avatar, Badge, Button, Typography } from '@/components/atoms';
import { ScoreDisplay } from '@/components/molecules';
import { Job, JobMatch } from '@/types';
import {
  MapPin,
  Clock,
  Building2,
  Users,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Heart,
  HeartOff,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface JobListItemProps {
  job: Job;
  match?: JobMatch;
  variant?: 'default' | 'compact' | 'detailed';
  showMatchScore?: boolean;
  showActions?: boolean;
  isSaved?: boolean;
  isLiked?: boolean;
  onView?: (job: Job) => void;
  onApply?: (job: Job) => void;
  onSave?: (job: Job) => void;
  onLike?: (job: Job) => void;
  onShare?: (job: Job) => void;
  className?: string;
  'data-testid'?: string;
}

export const JobListItem: React.FC<JobListItemProps> = ({
  job,
  match,
  variant = 'default',
  showMatchScore = true,
  showActions = true,
  isSaved = false,
  isLiked = false,
  onView,
  onApply,
  onSave,
  onLike,
  onShare,
  className,
  'data-testid': testId
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isCompact = variant === 'compact';
  const isDetailed = variant === 'detailed';

  const handleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleView = () => {
    onView?.(job);
  };

  const handleApply = (e: React.MouseEvent) => {
    e.stopPropagation();
    onApply?.(job);
  };

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSave?.(job);
  };

  const handleLike = (e: React.MouseEvent) => {
    e.stopPropagation();
    onLike?.(job);
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    onShare?.(job);
  };

  return (
    <div
      className={cn(
        'bg-white border border-secondary-200 rounded-lg transition-all duration-200',
        'hover:shadow-medium hover:border-secondary-300',
        onView && 'cursor-pointer',
        className
      )}
      onClick={handleView}
      data-testid={testId}
    >
      <div className={cn('p-6', isCompact && 'p-4')}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4 flex-1 min-w-0">
            {/* Company Logo */}
            <Avatar
              src={job.companyLogo}
              name={job.company}
              size={isCompact ? 'md' : 'lg'}
              shape="square"
            />

            {/* Job Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <Typography
                    variant={isCompact ? 'h6' : 'h5'}
                    weight="semibold"
                    className="text-secondary-900 mb-1"
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
                          <Users className="w-4 h-4" />
                          <Typography variant="body">
                            {job.companySize}
                          </Typography>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Match Score */}
                {showMatchScore && match && (
                  <div className="ml-4">
                    <ScoreDisplay
                      score={match.score}
                      variant="compact"
                      showLabel={false}
                    />
                  </div>
                )}
              </div>

              {/* Meta Information */}
              <div className="flex flex-wrap items-center gap-4 text-secondary-500 mb-3">
                <div className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  <Typography variant="body">
                    {job.location} • {getLocationTypeDisplay(job.locationType)}
                  </Typography>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <Typography variant="body">
                    {formatRelativeTime(job.postedAt)}
                  </Typography>
                </div>
                {job.industry && (
                  <div className="flex items-center gap-1">
                    <Building2 className="w-4 h-4" />
                    <Typography variant="body">
                      {job.industry}
                    </Typography>
                  </div>
                )}
              </div>

              {/* Job Description */}
              {!isCompact && (
                <Typography
                  variant="body"
                  className={cn(
                    'text-secondary-600 mb-4',
                    !isExpanded && 'line-clamp-2'
                  )}
                >
                  {job.description}
                </Typography>
              )}

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="default" size="sm">
                  {getJobTypeDisplay(job.jobType)}
                </Badge>
                <Badge variant="default" size="sm">
                  {job.experienceLevel}
                </Badge>
                {job.skills.slice(0, isCompact ? 3 : 5).map((skill) => (
                  <Badge key={skill} variant="default" size="sm">
                    {skill}
                  </Badge>
                ))}
                {job.skills.length > (isCompact ? 3 : 5) && (
                  <Badge variant="default" size="sm">
                    +{job.skills.length - (isCompact ? 3 : 5)} more
                  </Badge>
                )}
              </div>

              {/* Salary */}
              <div className="mb-4">
                <Typography variant="h6" weight="semibold" color="primary">
                  {formatCurrency(job.salary.min)} - {formatCurrency(job.salary.max)}
                </Typography>
                <Typography variant="body" className="text-secondary-500">
                  per {job.salary.period} • {job.applicantCount} applicants
                </Typography>
              </div>
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && !isCompact && (
          <div className="border-t border-secondary-100 pt-4 mb-4">
            {/* Requirements */}
            {job.requirements.length > 0 && (
              <div className="mb-4">
                <Typography variant="h6" weight="semibold" className="mb-2">
                  Requirements
                </Typography>
                <ul className="space-y-1">
                  {job.requirements.map((requirement, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-secondary-400 rounded-full mt-2 flex-shrink-0" />
                      <Typography variant="body" className="text-secondary-600">
                        {requirement}
                      </Typography>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Benefits */}
            {job.benefits.length > 0 && (
              <div className="mb-4">
                <Typography variant="h6" weight="semibold" className="mb-2">
                  Benefits
                </Typography>
                <div className="flex flex-wrap gap-2">
                  {job.benefits.map((benefit) => (
                    <Badge key={benefit} variant="success" size="sm">
                      {benefit}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Match Factors */}
            {match && match.factors && (
              <div className="mb-4">
                <ScoreDisplay
                  score={match.score}
                  factors={match.factors}
                  variant="detailed"
                />
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between">
          {/* Left Actions */}
          <div className="flex items-center gap-2">
            {!isCompact && (
              <Button
                variant="ghost"
                size="sm"
                icon={isExpanded ? <ChevronUp /> : <ChevronDown />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleExpand();
                }}
              >
                {isExpanded ? 'Show Less' : 'Show More'}
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              icon={<ExternalLink />}
              onClick={handleView}
            >
              View Details
            </Button>
          </div>

          {/* Right Actions */}
          {showActions && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                icon={isSaved ? <BookmarkCheck /> : <Bookmark />}
                onClick={handleSave}
                className={cn(
                  isSaved && 'text-primary-600 hover:text-primary-700'
                )}
              />

              <Button
                variant="ghost"
                size="sm"
                icon={isLiked ? <Heart className="fill-current" /> : <HeartOff />}
                onClick={handleLike}
                className={cn(
                  isLiked && 'text-danger-600 hover:text-danger-700'
                )}
              />

              <Button
                variant="primary"
                size="sm"
                onClick={handleApply}
              >
                Apply Now
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};