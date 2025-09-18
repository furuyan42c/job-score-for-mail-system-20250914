import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button, Badge, Typography } from '@/components/atoms';
import { FormField, SearchBar } from '@/components/molecules';
import { JobFilters, SelectOption } from '@/types';
import {
  EXPERIENCE_LEVELS,
  JOB_TYPES,
  LOCATION_TYPES,
  COMPANY_SIZES,
  INDUSTRIES,
  POPULAR_SKILLS,
  SALARY_RANGES
} from '@/lib/constants';
import { Filter, X, ChevronDown, ChevronUp } from 'lucide-react';

interface JobFilterPanelProps {
  filters: JobFilters;
  onFiltersChange: (filters: JobFilters) => void;
  onClearFilters: () => void;
  variant?: 'sidebar' | 'dropdown' | 'modal';
  isOpen?: boolean;
  onToggle?: () => void;
  showActiveCount?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const JobFilterPanel: React.FC<JobFilterPanelProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
  variant = 'sidebar',
  isOpen = true,
  onToggle,
  showActiveCount = true,
  className,
  'data-testid': testId
}) => {
  const [localFilters, setLocalFilters] = useState<JobFilters>(filters);
  const [skillSearch, setSkillSearch] = useState('');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    skills: true,
    location: true,
    salary: true,
    experience: true,
    jobType: true,
    company: true,
    industry: false
  });

  const isDropdown = variant === 'dropdown';
  const isModal = variant === 'modal';
  const isSidebar = variant === 'sidebar';

  // Count active filters
  const getActiveFilterCount = (): number => {
    let count = 0;
    if (localFilters.skills.length > 0) count++;
    if (localFilters.locations.length > 0) count++;
    if (localFilters.experienceLevels.length > 0) count++;
    if (localFilters.jobTypes.length > 0) count++;
    if (localFilters.locationTypes.length > 0) count++;
    if (localFilters.companySizes.length > 0) count++;
    if (localFilters.industries.length > 0) count++;
    if (localFilters.salaryRange.min > 0 || localFilters.salaryRange.max < 1000000) count++;
    if (localFilters.postedWithin < 30) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  // Update local filters when external filters change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Apply filters
  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    if (isDropdown && onToggle) {
      onToggle();
    }
  };

  // Clear all filters
  const handleClearAll = () => {
    const clearedFilters: JobFilters = {
      skills: [],
      locations: [],
      salaryRange: { min: 0, max: 1000000, currency: 'USD', period: 'year' },
      experienceLevels: [],
      jobTypes: [],
      locationTypes: [],
      companySizes: [],
      industries: [],
      postedWithin: 30
    };
    setLocalFilters(clearedFilters);
    onClearFilters();
  };

  // Toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Skill management
  const handleSkillAdd = (skill: string) => {
    if (skill && !localFilters.skills.includes(skill)) {
      setLocalFilters(prev => ({
        ...prev,
        skills: [...prev.skills, skill]
      }));
      setSkillSearch('');
    }
  };

  const handleSkillRemove = (skill: string) => {
    setLocalFilters(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill)
    }));
  };

  // Filter suggested skills based on search
  const filteredSkills = POPULAR_SKILLS.filter(skill =>
    skill.toLowerCase().includes(skillSearch.toLowerCase()) &&
    !localFilters.skills.includes(skill)
  ).slice(0, 10);

  // Section component
  const FilterSection: React.FC<{
    title: string;
    sectionKey: string;
    children: React.ReactNode;
  }> = ({ title, sectionKey, children }) => (
    <div className="border-b border-secondary-200 last:border-b-0">
      <button
        type="button"
        onClick={() => toggleSection(sectionKey)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-secondary-50"
      >
        <Typography variant="h6" weight="semibold">
          {title}
        </Typography>
        {expandedSections[sectionKey] ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {expandedSections[sectionKey] && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  );

  const filterContent = (
    <div className={cn('bg-white', isDropdown && 'border border-secondary-200 rounded-lg shadow-lg')}>
      {/* Header */}
      <div className="p-4 border-b border-secondary-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            <Typography variant="h5" weight="semibold">
              Filters
            </Typography>
            {showActiveCount && activeFilterCount > 0 && (
              <Badge variant="primary" size="sm">
                {activeFilterCount}
              </Badge>
            )}
          </div>

          {(isDropdown || isModal) && onToggle && (
            <Button
              variant="ghost"
              size="sm"
              icon={<X />}
              onClick={onToggle}
            />
          )}
        </div>

        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="mt-2"
          >
            Clear All
          </Button>
        )}
      </div>

      {/* Filter Sections */}
      <div className="max-h-96 overflow-y-auto">
        {/* Skills */}
        <FilterSection title="Skills" sectionKey="skills">
          <div className="space-y-3">
            <SearchBar
              placeholder="Search skills..."
              value={skillSearch}
              onChange={setSkillSearch}
              onSearch={(value) => handleSkillAdd(value)}
              size="sm"
              showSearchButton={false}
              showClearButton={false}
            />

            {/* Selected Skills */}
            {localFilters.skills.length > 0 && (
              <div className="space-y-2">
                <Typography variant="caption" weight="medium">
                  Selected Skills
                </Typography>
                <div className="flex flex-wrap gap-1">
                  {localFilters.skills.map(skill => (
                    <Badge
                      key={skill}
                      variant="primary"
                      size="sm"
                      removable
                      onRemove={() => handleSkillRemove(skill)}
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Skills */}
            {filteredSkills.length > 0 && (
              <div className="space-y-2">
                <Typography variant="caption" weight="medium">
                  Suggested
                </Typography>
                <div className="flex flex-wrap gap-1">
                  {filteredSkills.map(skill => (
                    <Badge
                      key={skill}
                      variant="default"
                      size="sm"
                      className="cursor-pointer hover:bg-primary-50"
                      onClick={() => handleSkillAdd(skill)}
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </FilterSection>

        {/* Experience Level */}
        <FilterSection title="Experience Level" sectionKey="experience">
          <FormField
            type="select"
            selectProps={{
              options: EXPERIENCE_LEVELS.map(level => ({
                value: level.value,
                label: level.label,
                description: level.description
              })),
              value: localFilters.experienceLevels,
              onChange: (value) => setLocalFilters(prev => ({
                ...prev,
                experienceLevels: Array.isArray(value) ? value as any : [value as any]
              })),
              multiple: true,
              placeholder: 'Select experience levels...'
            }}
          />
        </FilterSection>

        {/* Job Type */}
        <FilterSection title="Job Type" sectionKey="jobType">
          <FormField
            type="select"
            selectProps={{
              options: JOB_TYPES.map(type => ({
                value: type.value,
                label: type.label,
                description: type.description
              })),
              value: localFilters.jobTypes,
              onChange: (value) => setLocalFilters(prev => ({
                ...prev,
                jobTypes: Array.isArray(value) ? value as any : [value as any]
              })),
              multiple: true,
              placeholder: 'Select job types...'
            }}
          />
        </FilterSection>

        {/* Location Type */}
        <FilterSection title="Location Type" sectionKey="location">
          <FormField
            type="select"
            selectProps={{
              options: LOCATION_TYPES.map(type => ({
                value: type.value,
                label: type.label,
                description: type.description
              })),
              value: localFilters.locationTypes,
              onChange: (value) => setLocalFilters(prev => ({
                ...prev,
                locationTypes: Array.isArray(value) ? value as any : [value as any]
              })),
              multiple: true,
              placeholder: 'Select location types...'
            }}
          />
        </FilterSection>

        {/* Salary Range */}
        <FilterSection title="Salary Range" sectionKey="salary">
          <FormField
            type="select"
            selectProps={{
              options: SALARY_RANGES.map(range => ({
                value: `${range.min}-${range.max}`,
                label: range.label
              })),
              value: `${localFilters.salaryRange.min}-${localFilters.salaryRange.max}`,
              onChange: (value) => {
                const [min, max] = (value as string).split('-').map(Number);
                setLocalFilters(prev => ({
                  ...prev,
                  salaryRange: { ...prev.salaryRange, min, max }
                }));
              },
              placeholder: 'Select salary range...'
            }}
          />
        </FilterSection>

        {/* Company Size */}
        <FilterSection title="Company Size" sectionKey="company">
          <FormField
            type="select"
            selectProps={{
              options: COMPANY_SIZES.map(size => ({
                value: size.value,
                label: size.label,
                description: size.description
              })),
              value: localFilters.companySizes,
              onChange: (value) => setLocalFilters(prev => ({
                ...prev,
                companySizes: Array.isArray(value) ? value as any : [value as any]
              })),
              multiple: true,
              placeholder: 'Select company sizes...'
            }}
          />
        </FilterSection>

        {/* Industry */}
        <FilterSection title="Industry" sectionKey="industry">
          <FormField
            type="select"
            selectProps={{
              options: INDUSTRIES.map(industry => ({
                value: industry,
                label: industry
              })),
              value: localFilters.industries,
              onChange: (value) => setLocalFilters(prev => ({
                ...prev,
                industries: Array.isArray(value) ? value as string[] : [value as string]
              })),
              multiple: true,
              searchable: true,
              placeholder: 'Select industries...'
            }}
          />
        </FilterSection>
      </div>

      {/* Footer */}
      {(isDropdown || isModal) && (
        <div className="p-4 border-t border-secondary-200">
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={handleApplyFilters}
              fullWidth
            >
              Apply Filters
            </Button>
            <Button
              variant="ghost"
              onClick={handleClearAll}
            >
              Clear
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  if (isDropdown) {
    return isOpen ? (
      <div className={cn('absolute z-50 w-80 mt-2', className)} data-testid={testId}>
        {filterContent}
      </div>
    ) : null;
  }

  if (isModal) {
    return isOpen ? (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
        <div className={cn('w-full max-w-md max-h-full overflow-hidden', className)} data-testid={testId}>
          {filterContent}
        </div>
      </div>
    ) : null;
  }

  return (
    <div className={cn('w-full', className)} data-testid={testId}>
      {filterContent}
    </div>
  );
};