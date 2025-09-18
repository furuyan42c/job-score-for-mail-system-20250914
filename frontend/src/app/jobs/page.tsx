'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/templates';
import { SearchBar, Pagination } from '@/components/molecules';
import { JobListItem, JobFilterPanel } from '@/components/organisms';
import { Button, Typography, Loader } from '@/components/atoms';
import { Job, JobFilters, JobMatch, JobSearchParams } from '@/types';
import { Filter, Grid, List } from 'lucide-react';
import { cn } from '@/lib/utils';

// Mock data - replace with actual API calls
const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Frontend Developer',
    company: 'TechCorp Inc.',
    description: 'We are looking for a skilled Frontend Developer to join our dynamic team...',
    requirements: ['React', 'TypeScript', 'Next.js', '5+ years experience'],
    location: 'San Francisco, CA',
    locationType: 'hybrid',
    salary: { min: 120000, max: 160000, currency: 'USD', period: 'year' },
    experienceLevel: 'senior',
    jobType: 'full-time',
    skills: ['React', 'TypeScript', 'Next.js', 'GraphQL'],
    benefits: ['Health Insurance', 'Remote Work', 'Stock Options'],
    postedAt: new Date('2024-01-15'),
    status: 'active',
    applicantCount: 45,
    views: 230,
    companySize: 'medium',
    industry: 'Technology'
  },
  // Add more mock jobs...
];

const mockMatches: JobMatch[] = [
  {
    id: '1',
    userId: 'user1',
    jobId: '1',
    score: 85,
    factors: [
      { type: 'skills', weight: 0.4, score: 90, description: 'Skills Match' },
      { type: 'experience', weight: 0.3, score: 85, description: 'Experience Level' },
      { type: 'location', weight: 0.2, score: 75, description: 'Location Preference' },
      { type: 'salary', weight: 0.1, score: 95, description: 'Salary Range' }
    ],
    createdAt: new Date(),
    status: 'new'
  }
];

const initialFilters: JobFilters = {
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

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [filters, setFilters] = useState<JobFilters>(initialFilters);
  const [searchParams, setSearchParams] = useState<JobSearchParams>({
    query: '',
    page: 1,
    limit: 20,
    sortBy: 'relevance',
    sortOrder: 'desc'
  });
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);

  // Mock API call
  useEffect(() => {
    const loadJobs = async () => {
      setLoading(true);
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      setJobs(mockJobs);
      setMatches(mockMatches);
      setLoading(false);
    };

    loadJobs();
  }, [searchParams, filters]);

  const handleSearch = (query: string) => {
    setSearchParams(prev => ({ ...prev, query, page: 1 }));
  };

  const handleFiltersChange = (newFilters: JobFilters) => {
    setFilters(newFilters);
    setSearchParams(prev => ({ ...prev, page: 1 }));
  };

  const handleClearFilters = () => {
    setFilters(initialFilters);
    setSearchParams(prev => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setSearchParams(prev => ({ ...prev, page }));
  };

  const handleJobView = (job: Job) => {
    // Navigate to job detail page
    window.location.href = `/jobs/${job.id}`;
  };

  const handleJobApply = (job: Job) => {
    // Handle job application
    console.log('Apply to job:', job.id);
  };

  const handleJobSave = (job: Job) => {
    // Handle job save
    console.log('Save job:', job.id);
  };

  const toggleFilterPanel = () => {
    setIsFilterPanelOpen(!isFilterPanelOpen);
  };

  const getJobMatch = (jobId: string): JobMatch | undefined => {
    return matches.find(match => match.jobId === jobId);
  };

  return (
    <MainLayout title="Browse Jobs" description="Find your perfect job match">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Typography variant="h3" weight="bold" className="mb-2">
            Find Your Perfect Job
          </Typography>
          <Typography variant="body" className="text-secondary-600">
            Discover opportunities tailored to your skills and preferences
          </Typography>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <SearchBar
            placeholder="Search jobs, companies, or skills..."
            value={searchParams.query}
            onChange={handleSearch}
            onSearch={handleSearch}
            size="lg"
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {/* Filter Toggle */}
            <Button
              variant="outline"
              icon={<Filter />}
              onClick={toggleFilterPanel}
              className="lg:hidden"
            >
              Filters
            </Button>

            {/* Results Count */}
            <Typography variant="body" className="text-secondary-600">
              {loading ? 'Loading...' : `${jobs.length} jobs found`}
            </Typography>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === 'list' ? 'primary' : 'ghost'}
              size="sm"
              icon={<List />}
              onClick={() => setViewMode('list')}
            />
            <Button
              variant={viewMode === 'grid' ? 'primary' : 'ghost'}
              size="sm"
              icon={<Grid />}
              onClick={() => setViewMode('grid')}
            />
          </div>
        </div>

        <div className="flex gap-8">
          {/* Filter Panel - Desktop */}
          <div className="hidden lg:block w-80 flex-shrink-0">
            <div className="sticky top-8">
              <JobFilterPanel
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onClearFilters={handleClearFilters}
                variant="sidebar"
              />
            </div>
          </div>

          {/* Filter Panel - Mobile */}
          <JobFilterPanel
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onClearFilters={handleClearFilters}
            variant="modal"
            isOpen={isFilterPanelOpen}
            onToggle={toggleFilterPanel}
          />

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader size="lg" />
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-12">
                <Typography variant="h5" weight="semibold" className="mb-2">
                  No jobs found
                </Typography>
                <Typography variant="body" className="text-secondary-600 mb-4">
                  Try adjusting your search criteria or filters
                </Typography>
                <Button variant="primary" onClick={handleClearFilters}>
                  Clear Filters
                </Button>
              </div>
            ) : (
              <>
                {/* Job List */}
                <div className={cn(
                  'space-y-4',
                  viewMode === 'grid' && 'grid grid-cols-1 md:grid-cols-2 gap-6 space-y-0'
                )}>
                  {jobs.map((job) => (
                    <JobListItem
                      key={job.id}
                      job={job}
                      match={getJobMatch(job.id)}
                      variant={viewMode === 'grid' ? 'compact' : 'default'}
                      onView={handleJobView}
                      onApply={handleJobApply}
                      onSave={handleJobSave}
                    />
                  ))}
                </div>

                {/* Pagination */}
                <div className="mt-8">
                  <Pagination
                    currentPage={searchParams.page || 1}
                    totalPages={Math.ceil(jobs.length / (searchParams.limit || 20))}
                    onPageChange={handlePageChange}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}