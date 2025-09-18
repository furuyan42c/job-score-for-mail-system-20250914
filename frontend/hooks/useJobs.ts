import { useCallback, useEffect, useMemo } from 'react';
import { useJobStore, jobSelectors } from '../stores/jobStore';
import { useFilterStore, filterSelectors } from '../stores/filterStore';
import { Job, JobSearchParams, JobApplication, PaginationState } from '../lib/types';

export const useJobs = () => {
  const store = useJobStore();

  // Selectors
  const jobs = useJobStore(jobSelectors.jobs);
  const jobDetails = useJobStore(jobSelectors.jobDetails);
  const selectedJob = useJobStore(jobSelectors.selectedJob);
  const pagination = useJobStore(jobSelectors.pagination);
  const searchHistory = useJobStore(jobSelectors.searchHistory);
  const applications = useJobStore(jobSelectors.applications);

  // Filter state
  const searchParams = useFilterStore(filterSelectors.searchQuery);
  const activeFilters = useFilterStore(filterSelectors.activeFilters);

  // Actions
  const {
    searchJobs,
    loadMoreJobs,
    getJobDetails,
    applyToJob,
    saveJob,
    unsaveJob,
    setSelectedJob,
    loadApplications,
    invalidateCache,
    resetStore,
  } = store;

  // Async action states
  const searchJobsAction = useJobStore(jobSelectors.searchJobsAction);
  const getJobDetailsAction = useJobStore(jobSelectors.getJobDetailsAction);
  const applyToJobAction = useJobStore(jobSelectors.applyToJobAction);
  const saveJobAction = useJobStore(jobSelectors.saveJobAction);
  const loadApplicationsAction = useJobStore(jobSelectors.loadApplicationsAction);

  // Check if job is saved or applied
  const isJobSaved = useJobStore(jobSelectors.isJobSaved);
  const isJobApplied = useJobStore(jobSelectors.isJobApplied);

  // Search jobs with current filters
  const searchWithFilters = useCallback(async (overrideParams?: JobSearchParams) => {
    const params = {
      ...activeFilters,
      ...overrideParams,
    };
    await searchJobs(params);
  }, [searchJobs, activeFilters]);

  // Load more jobs (pagination)
  const loadMore = useCallback(async () => {
    if (!pagination.hasMore || searchJobsAction.isLoading) {
      return;
    }
    await loadMoreJobs();
  }, [loadMoreJobs, pagination.hasMore, searchJobsAction.isLoading]);

  // Get job by ID with caching
  const getJob = useCallback(async (jobId: string, useCache = true) => {
    await getJobDetails(jobId, useCache);
    return jobDetails[jobId] || null;
  }, [getJobDetails, jobDetails]);

  // Apply to job with optimistic update
  const applyToJobWithFeedback = useCallback(async (
    jobId: string,
    applicationData: Partial<JobApplication>
  ) => {
    try {
      await applyToJob(jobId, applicationData);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Application failed'
      };
    }
  }, [applyToJob]);

  // Save/unsave job toggle
  const toggleSaveJob = useCallback(async (jobId: string) => {
    try {
      if (isJobSaved(jobId)) {
        await unsaveJob(jobId);
        return { saved: false, error: null };
      } else {
        await saveJob(jobId);
        return { saved: true, error: null };
      }
    } catch (error) {
      return {
        saved: isJobSaved(jobId), // Return current state on error
        error: error instanceof Error ? error.message : 'Save operation failed'
      };
    }
  }, [isJobSaved, saveJob, unsaveJob]);

  // Initialize jobs on mount
  useEffect(() => {
    if (jobs.length === 0 && !searchJobsAction.isLoading) {
      searchWithFilters();
    }
  }, [searchWithFilters, jobs.length, searchJobsAction.isLoading]);

  // Load applications on mount
  useEffect(() => {
    if (applications.length === 0 && !loadApplicationsAction.isLoading) {
      loadApplications();
    }
  }, [loadApplications, applications.length, loadApplicationsAction.isLoading]);

  // Computed values
  const hasJobs = jobs.length > 0;
  const hasMoreJobs = pagination.hasMore;
  const isLoadingJobs = searchJobsAction.isLoading;
  const isLoadingMore = searchJobsAction.isLoading && pagination.page > 1;
  const jobsError = searchJobsAction.error;

  // Search state
  const hasActiveSearch = !!(searchParams || Object.keys(activeFilters).length > 2); // More than sortBy and sortOrder

  return {
    // Job data
    jobs,
    jobDetails,
    selectedJob,
    pagination,
    searchHistory,
    applications,

    // State
    isLoadingJobs,
    isLoadingMore,
    hasJobs,
    hasMoreJobs,
    jobsError,
    hasActiveSearch,

    // Actions
    searchJobs: searchWithFilters,
    loadMore,
    getJob,
    applyToJob: applyToJobWithFeedback,
    saveJob,
    unsaveJob,
    toggleSaveJob,
    setSelectedJob,
    loadApplications,
    invalidateCache,
    resetStore,

    // Async action states
    searchJobsAction,
    getJobDetailsAction,
    applyToJobAction,
    saveJobAction,
    loadApplicationsAction,

    // Job status checkers
    isJobSaved,
    isJobApplied,

    // Pagination info
    currentPage: pagination.page,
    totalJobs: pagination.total,
    jobsPerPage: pagination.limit,
  };
};

// Specialized hook for job details
export const useJobDetails = (jobId: string) => {
  const { getJob, jobDetails, getJobDetailsAction, isJobSaved, isJobApplied } = useJobs();

  const job = useMemo(() => jobDetails[jobId] || null, [jobDetails, jobId]);

  useEffect(() => {
    if (jobId && !job && !getJobDetailsAction.isLoading) {
      getJob(jobId);
    }
  }, [jobId, job, getJob, getJobDetailsAction.isLoading]);

  return {
    job,
    isLoading: getJobDetailsAction.isLoading,
    error: getJobDetailsAction.error,
    isSaved: job ? isJobSaved(job.id) : false,
    isApplied: job ? isJobApplied(job.id) : false,
    refreshJob: () => job && getJob(job.id, false),
  };
};

// Hook for job applications
export const useJobApplications = () => {
  const {
    applications,
    loadApplications,
    loadApplicationsAction,
    applyToJob,
    applyToJobAction,
  } = useJobs();

  const getApplicationByJobId = useCallback((jobId: string) => {
    return applications.find(app => app.jobId === jobId);
  }, [applications]);

  const getApplicationsByStatus = useCallback((status: JobApplication['status']) => {
    return applications.filter(app => app.status === status);
  }, [applications]);

  const applicationStats = useMemo(() => {
    const stats = {
      total: applications.length,
      pending: 0,
      reviewing: 0,
      interview: 0,
      offer: 0,
      rejected: 0,
      withdrawn: 0,
    };

    applications.forEach(app => {
      stats[app.status]++;
    });

    return stats;
  }, [applications]);

  return {
    applications,
    applicationStats,
    isLoading: loadApplicationsAction.isLoading,
    error: loadApplicationsAction.error,
    loadApplications,
    applyToJob,
    applyToJobAction,
    getApplicationByJobId,
    getApplicationsByStatus,
  };
};

// Hook for saved jobs
export const useSavedJobs = () => {
  const { jobs, isJobSaved, saveJob, unsaveJob, toggleSaveJob, saveJobAction } = useJobs();

  const savedJobs = useMemo(() => {
    return jobs.filter(job => isJobSaved(job.id));
  }, [jobs, isJobSaved]);

  return {
    savedJobs,
    isLoading: saveJobAction.isLoading,
    error: saveJobAction.error,
    saveJob,
    unsaveJob,
    toggleSaveJob,
    savedJobsCount: savedJobs.length,
    isJobSaved,
  };
};

// Hook for job search with real-time updates
export const useJobSearch = () => {
  const { searchJobs, searchJobsAction, jobs, pagination } = useJobs();
  const {
    searchQuery,
    activeFilters,
    setSearchQuery,
    setFilters,
    clearAllFilters,
    hasActiveFilters,
    getFilterSummary,
  } = useFilterStore();

  const search = useCallback(async (query?: string, filters?: Partial<typeof activeFilters>) => {
    const searchParams = {
      ...activeFilters,
      ...filters,
      query: query ?? searchQuery,
    };

    await searchJobs(searchParams);
  }, [searchJobs, activeFilters, searchQuery]);

  const quickSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    await search(query);
  }, [search, setSearchQuery]);

  const applyFilters = useCallback(async (filters: Partial<typeof activeFilters>) => {
    setFilters(filters);
    await search(undefined, filters);
  }, [search, setFilters]);

  const clearFilters = useCallback(async () => {
    clearAllFilters();
    await searchJobs({});
  }, [clearAllFilters, searchJobs]);

  return {
    // Search state
    searchQuery,
    activeFilters,
    isSearching: searchJobsAction.isLoading,
    searchError: searchJobsAction.error,
    hasFilters: hasActiveFilters(),
    filterSummary: getFilterSummary(),

    // Results
    results: jobs,
    resultCount: pagination.total,
    hasResults: jobs.length > 0,

    // Actions
    search,
    quickSearch,
    applyFilters,
    clearFilters,
    setSearchQuery,
    setFilters,
  };
};