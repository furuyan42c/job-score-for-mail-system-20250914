import React from 'react';
import { JobCard } from './JobCard';
import { EmailSectionProps } from './types';
import { cn } from '@/lib/utils';
import {
  Sparkles,
  Target,
  Heart,
  Clock,
  TrendingUp,
  Users
} from 'lucide-react';

export const EmailSection: React.FC<EmailSectionProps> = ({
  section,
  previewMode,
  className
}) => {
  const getSectionIcon = (sectionId: string) => {
    switch (sectionId) {
      case 'editorial-picks':
        return <Sparkles className="h-4 w-4" />;
      case 'top-recommendations':
        return <Target className="h-4 w-4" />;
      case 'personalized-picks':
        return <Heart className="h-4 w-4" />;
      case 'new-arrivals':
        return <Clock className="h-4 w-4" />;
      case 'popular-jobs':
        return <TrendingUp className="h-4 w-4" />;
      case 'you-might-like':
        return <Users className="h-4 w-4" />;
      default:
        return <Target className="h-4 w-4" />;
    }
  };

  const getSectionColor = (sectionId: string) => {
    switch (sectionId) {
      case 'editorial-picks':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'top-recommendations':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'personalized-picks':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'new-arrivals':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'popular-jobs':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'you-might-like':
        return 'text-indigo-600 bg-indigo-50 border-indigo-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // Plain text rendering
  if (previewMode === 'plaintext') {
    return (
      <div className="mb-8">
        <div className="border-t border-gray-300 pt-4 mb-4">
          <h2 className="font-bold text-lg mb-2">{section.title}</h2>
          {section.description && (
            <p className="text-gray-600 mb-4">{section.description}</p>
          )}
        </div>
        <div className="space-y-4">
          {section.jobs.map((job, index) => (
            <JobCard
              key={job.id}
              job={job}
              previewMode={previewMode}
              showMatchScore={section.id !== 'editorial-picks'}
            />
          ))}
        </div>
      </div>
    );
  }

  // HTML rendering for mobile and desktop
  return (
    <div className={cn('mb-8', className)}>
      {/* Section Header */}
      <div className={cn(
        'flex items-center gap-3 p-4 rounded-lg border mb-4',
        getSectionColor(section.id)
      )}>
        <div className="flex items-center gap-2">
          {getSectionIcon(section.id)}
          <h2 className={cn(
            'font-bold',
            previewMode === 'mobile' ? 'text-lg' : 'text-xl'
          )}>
            {section.title}
          </h2>
        </div>
        <div className="ml-auto text-sm opacity-75">
          {section.jobs.length}件の求人
        </div>
      </div>

      {/* Section Description */}
      {section.description && (
        <p className="text-gray-600 mb-4 text-sm leading-relaxed px-1">
          {section.description}
        </p>
      )}

      {/* Jobs Grid */}
      <div className={cn(
        'grid gap-4',
        previewMode === 'mobile'
          ? 'grid-cols-1'
          : section.jobs.length > 2
            ? 'grid-cols-1 lg:grid-cols-2'
            : 'grid-cols-1'
      )}>
        {section.jobs.map((job, index) => (
          <JobCard
            key={job.id}
            job={job}
            previewMode={previewMode}
            showMatchScore={section.id !== 'editorial-picks'}
            compact={previewMode === 'mobile' || section.jobs.length > 3}
          />
        ))}
      </div>

      {/* Show more indicator for sections with many jobs */}
      {section.jobs.length >= section.maxJobs && (
        <div className="text-center mt-4">
          <div className="text-sm text-gray-500 bg-gray-50 rounded-lg py-2 px-4 border border-dashed border-gray-300">
            他に{Math.max(0, section.maxJobs - section.jobs.length)}件の求人があります
          </div>
        </div>
      )}
    </div>
  );
};