import { create } from 'zustand';
import { createStoreWithMiddleware, type StoreCreator, handleAsyncError, OptimisticCache } from '../lib/utils/store-middleware';
import {
  Job,
  JobSearchParams,
  JobFilters,
  PaginationState,
  AsyncAction,
  ApiResponse,
  PaginatedResponse,
  JobApplication,
  CacheEntry
} from '../lib/types';

// Mock API functions
const jobApi = {
  getJobs: async (params?: JobSearchParams & { page?: number; limit?: number }): Promise<PaginatedResponse<Job>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockJobs: Job[] = Array.from({ length: 20 }, (_, i) => ({
          id: `job-${i + 1}`,
          title: `Software Engineer ${i + 1}`,
          company: `Company ${i + 1}`,
          description: `Job description for position ${i + 1}`,
          requirements: ['JavaScript', 'React', 'TypeScript'],
          responsibilities: ['Develop features', 'Code reviews', 'Testing'],
          location: i % 2 === 0 ? 'San Francisco, CA' : 'Remote',
          isRemote: i % 2 === 0,
          jobType: 'full-time',
          experienceLevel: 'mid',
          salaryRange: {
            min: 80000 + (i * 5000),
            max: 120000 + (i * 5000),
            currency: 'USD'
          },
          skills: ['JavaScript', 'React', 'TypeScript', 'Node.js'],
          benefits: ['Health insurance', '401k', 'Remote work'],
          status: 'active',
          applicantCount: Math.floor(Math.random() * 100),
          viewCount: Math.floor(Math.random() * 1000),
          postedBy: 'recruiter-1',
          industry: 'Technology',
          createdAt: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
          updatedAt: new Date().toISOString(),
        }));

        resolve({
          status: 'success',
          data: mockJobs,
          pagination: {
            page: params?.page || 1,
            limit: params?.limit || 20,
            total: 100,
            totalPages: 5,
            hasNext: (params?.page || 1) < 5,
            hasPrev: (params?.page || 1) > 1,
          }
        });
      }, 1000);
    });
  },

  getJobById: async (id: string): Promise<ApiResponse<Job>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            id,
            title: 'Senior Software Engineer',
            company: 'Tech Corp',
            description: 'Detailed job description...',
            requirements: ['JavaScript', 'React', 'TypeScript', '5+ years experience'],
            responsibilities: ['Lead development', 'Mentor junior developers', 'Architecture decisions'],
            location: 'San Francisco, CA',
            isRemote: true,
            jobType: 'full-time',
            experienceLevel: 'senior',
            salaryRange: {
              min: 120000,
              max: 160000,
              currency: 'USD'
            },
            skills: ['JavaScript', 'React', 'TypeScript', 'Node.js', 'AWS'],
            benefits: ['Health insurance', '401k', 'Stock options', 'Remote work'],
            status: 'active',
            applicantCount: 45,
            viewCount: 234,
            postedBy: 'recruiter-1',
            companyLogo: '/company-logo.png',
            companySize: '100-500',
            industry: 'Technology',
            createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
            updatedAt: new Date().toISOString(),
          }
        });
      }, 800);
    });
  },

  applyToJob: async (jobId: string, applicationData: Partial<JobApplication>): Promise<ApiResponse<JobApplication>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            id: `app-${Date.now()}`,
            userId: 'user-1',
            jobId,
            status: 'pending',
            appliedAt: new Date().toISOString(),
            coverLetter: applicationData.coverLetter,
            resumeUrl: applicationData.resumeUrl,
            customResponses: applicationData.customResponses,
            lastStatusUpdate: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        });
      }, 1500);
    });
  },

  getMyApplications: async (): Promise<ApiResponse<JobApplication[]>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: []
        });
      }, 800);
    });
  },

  saveJob: async (jobId: string): Promise<ApiResponse<void>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ status: 'success', data: undefined });
      }, 500);
    });
  },

  unsaveJob: async (jobId: string): Promise<ApiResponse<void>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ status: 'success', data: undefined });
      }, 500);
    });
  }
};

interface JobState {
  // Job listings and cache
  jobs: Job[];
  jobsCache: Map<string, CacheEntry<Job>>;
  jobDetails: Record<string, Job>;

  // Search and filtering
  searchParams: JobSearchParams;
  filters: JobFilters;
  searchHistory: Array<{ query: string; timestamp: string; resultsCount: number }>;

  // Pagination
  pagination: PaginationState;

  // Selected job
  selectedJobId: string | null;

  // Applications
  applications: JobApplication[];
  appliedJobIds: Set<string>;

  // Saved jobs
  savedJobIds: Set<string>;

  // Async actions
  searchJobsAction: AsyncAction<Job[]>;
  getJobDetailsAction: AsyncAction<Job>;
  applyToJobAction: AsyncAction<JobApplication>;
  saveJobAction: AsyncAction<void>;
  loadApplicationsAction: AsyncAction<JobApplication[]>;

  // Cache management
  optimisticCache: OptimisticCache<Job>;

  // Actions
  searchJobs: (params?: JobSearchParams, page?: number) => Promise<void>;
  loadMoreJobs: () => Promise<void>;
  getJobDetails: (jobId: string, useCache?: boolean) => Promise<void>;
  applyToJob: (jobId: string, applicationData: Partial<JobApplication>) => Promise<void>;
  saveJob: (jobId: string) => Promise<void>;
  unsaveJob: (jobId: string) => Promise<void>;
  setFilters: (filters: Partial<JobFilters>) => void;
  setSearchParams: (params: Partial<JobSearchParams>) => void;
  setSelectedJob: (jobId: string | null) => void;
  addToSearchHistory: (query: string, resultsCount: number) => void;
  clearSearchHistory: () => void;
  loadApplications: () => Promise<void>;
  invalidateCache: (jobId?: string) => void;
  clearJobsCache: () => void;
  resetFilters: () => void;
  resetStore: () => void;
}

const initialFilters: JobFilters = {
  sortBy: 'relevance',
  sortOrder: 'desc',
};

const initialState: Omit<JobState, keyof JobActions> = {
  jobs: [],
  jobsCache: new Map(),
  jobDetails: {},
  searchParams: {},
  filters: initialFilters,
  searchHistory: [],
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    hasMore: true,
  },
  selectedJobId: null,
  applications: [],
  appliedJobIds: new Set(),
  savedJobIds: new Set(),
  searchJobsAction: { isLoading: false, error: null, data: null, lastFetch: null },
  getJobDetailsAction: { isLoading: false, error: null, data: null, lastFetch: null },
  applyToJobAction: { isLoading: false, error: null, data: null, lastFetch: null },
  saveJobAction: { isLoading: false, error: null, data: null, lastFetch: null },
  loadApplicationsAction: { isLoading: false, error: null, data: null, lastFetch: null },
  optimisticCache: new OptimisticCache<Job>(),
};

type JobActions = Pick<JobState,
  | 'searchJobs'
  | 'loadMoreJobs'
  | 'getJobDetails'
  | 'applyToJob'
  | 'saveJob'
  | 'unsaveJob'
  | 'setFilters'
  | 'setSearchParams'
  | 'setSelectedJob'
  | 'addToSearchHistory'
  | 'clearSearchHistory'
  | 'loadApplications'
  | 'invalidateCache'
  | 'clearJobsCache'
  | 'resetFilters'
  | 'resetStore'
>;

const jobStoreCreator: StoreCreator<JobState> = (set, get) => ({
  ...initialState,

  searchJobs: async (params?: JobSearchParams, page = 1) => {
    set((state) => {
      state.searchJobsAction.isLoading = true;
      state.searchJobsAction.error = null;
      if (page === 1) {
        state.jobs = []; // Clear jobs for new search
      }
    });

    try {
      const searchParams = { ...get().searchParams, ...params };
      const filters = get().filters;

      const apiParams = {
        ...searchParams,
        ...filters,
        page,
        limit: get().pagination.limit,
      };

      const response = await jobApi.getJobs(apiParams);

      if (response.status === 'success') {
        set((state) => {
          if (page === 1) {
            state.jobs = response.data;
          } else {
            state.jobs.push(...response.data);
          }

          state.pagination = {
            page: response.pagination.page,
            limit: response.pagination.limit,
            total: response.pagination.total,
            hasMore: response.pagination.hasNext,
          };

          state.searchParams = searchParams;
          state.searchJobsAction.isLoading = false;
          state.searchJobsAction.data = response.data;
          state.searchJobsAction.lastFetch = new Date().toISOString();

          // Cache the jobs
          response.data.forEach(job => {
            state.jobsCache.set(job.id, {
              data: job,
              timestamp: Date.now(),
              ttl: 5 * 60 * 1000, // 5 minutes
              key: job.id,
            });
          });
        });

        // Add to search history if there's a query
        if (searchParams.query) {
          get().addToSearchHistory(searchParams.query, response.data.length);
        }
      }
    } catch (error) {
      set((state) => {
        state.searchJobsAction.isLoading = false;
        state.searchJobsAction.error = handleAsyncError(error);
      });
    }
  },

  loadMoreJobs: async () => {
    const { pagination } = get();
    if (!pagination.hasMore || get().searchJobsAction.isLoading) {
      return;
    }

    await get().searchJobs(get().searchParams, pagination.page + 1);
  },

  getJobDetails: async (jobId: string, useCache = true) => {
    // Check cache first
    if (useCache) {
      const cached = get().jobsCache.get(jobId);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        set((state) => {
          state.jobDetails[jobId] = cached.data;
          state.getJobDetailsAction.data = cached.data;
          state.getJobDetailsAction.lastFetch = new Date(cached.timestamp).toISOString();
        });
        return;
      }
    }

    set((state) => {
      state.getJobDetailsAction.isLoading = true;
      state.getJobDetailsAction.error = null;
    });

    try {
      const response = await jobApi.getJobById(jobId);

      if (response.status === 'success') {
        set((state) => {
          state.jobDetails[jobId] = response.data;
          state.getJobDetailsAction.isLoading = false;
          state.getJobDetailsAction.data = response.data;
          state.getJobDetailsAction.lastFetch = new Date().toISOString();

          // Update cache
          state.jobsCache.set(jobId, {
            data: response.data,
            timestamp: Date.now(),
            ttl: 10 * 60 * 1000, // 10 minutes for detailed view
            key: jobId,
          });
        });
      }
    } catch (error) {
      set((state) => {
        state.getJobDetailsAction.isLoading = false;
        state.getJobDetailsAction.error = handleAsyncError(error);
      });
    }
  },

  applyToJob: async (jobId: string, applicationData: Partial<JobApplication>) => {
    // Optimistic update
    set((state) => {
      state.appliedJobIds.add(jobId);
      state.applyToJobAction.isLoading = true;
      state.applyToJobAction.error = null;
    });

    try {
      const response = await jobApi.applyToJob(jobId, applicationData);

      if (response.status === 'success') {
        set((state) => {
          state.applications.push(response.data);
          state.applyToJobAction.isLoading = false;
          state.applyToJobAction.data = response.data;
          state.applyToJobAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      // Rollback optimistic update
      set((state) => {
        state.appliedJobIds.delete(jobId);
        state.applyToJobAction.isLoading = false;
        state.applyToJobAction.error = handleAsyncError(error);
      });
    }
  },

  saveJob: async (jobId: string) => {
    // Optimistic update
    const wasSaved = get().savedJobIds.has(jobId);
    set((state) => {
      state.savedJobIds.add(jobId);
      state.saveJobAction.isLoading = true;
      state.saveJobAction.error = null;
    });

    try {
      const response = await jobApi.saveJob(jobId);

      if (response.status === 'success') {
        set((state) => {
          state.saveJobAction.isLoading = false;
          state.saveJobAction.data = response.data;
          state.saveJobAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      // Rollback optimistic update
      set((state) => {
        if (!wasSaved) {
          state.savedJobIds.delete(jobId);
        }
        state.saveJobAction.isLoading = false;
        state.saveJobAction.error = handleAsyncError(error);
      });
    }
  },

  unsaveJob: async (jobId: string) => {
    // Optimistic update
    const wasSaved = get().savedJobIds.has(jobId);
    set((state) => {
      state.savedJobIds.delete(jobId);
      state.saveJobAction.isLoading = true;
      state.saveJobAction.error = null;
    });

    try {
      const response = await jobApi.unsaveJob(jobId);

      if (response.status === 'success') {
        set((state) => {
          state.saveJobAction.isLoading = false;
          state.saveJobAction.data = response.data;
          state.saveJobAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      // Rollback optimistic update
      set((state) => {
        if (wasSaved) {
          state.savedJobIds.add(jobId);
        }
        state.saveJobAction.isLoading = false;
        state.saveJobAction.error = handleAsyncError(error);
      });
    }
  },

  setFilters: (filters: Partial<JobFilters>) => {
    set((state) => {
      state.filters = { ...state.filters, ...filters };
    });
  },

  setSearchParams: (params: Partial<JobSearchParams>) => {
    set((state) => {
      state.searchParams = { ...state.searchParams, ...params };
    });
  },

  setSelectedJob: (jobId: string | null) => {
    set((state) => {
      state.selectedJobId = jobId;
    });
  },

  addToSearchHistory: (query: string, resultsCount: number) => {
    set((state) => {
      // Remove existing entry if present
      state.searchHistory = state.searchHistory.filter(item => item.query !== query);

      // Add new entry at the beginning
      state.searchHistory.unshift({
        query,
        timestamp: new Date().toISOString(),
        resultsCount,
      });

      // Keep only last 20 searches
      if (state.searchHistory.length > 20) {
        state.searchHistory = state.searchHistory.slice(0, 20);
      }
    });
  },

  clearSearchHistory: () => {
    set((state) => {
      state.searchHistory = [];
    });
  },

  loadApplications: async () => {
    set((state) => {
      state.loadApplicationsAction.isLoading = true;
      state.loadApplicationsAction.error = null;
    });

    try {
      const response = await jobApi.getMyApplications();

      if (response.status === 'success') {
        set((state) => {
          state.applications = response.data;
          state.appliedJobIds = new Set(response.data.map(app => app.jobId));
          state.loadApplicationsAction.isLoading = false;
          state.loadApplicationsAction.data = response.data;
          state.loadApplicationsAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.loadApplicationsAction.isLoading = false;
        state.loadApplicationsAction.error = handleAsyncError(error);
      });
    }
  },

  invalidateCache: (jobId?: string) => {
    set((state) => {
      if (jobId) {
        state.jobsCache.delete(jobId);
        delete state.jobDetails[jobId];
      } else {
        state.jobsCache.clear();
        state.jobDetails = {};
      }
    });
  },

  clearJobsCache: () => {
    set((state) => {
      state.jobsCache.clear();
      state.optimisticCache.clear();
    });
  },

  resetFilters: () => {
    set((state) => {
      state.filters = initialFilters;
      state.searchParams = {};
    });
  },

  resetStore: () => {
    set((state) => {
      Object.assign(state, {
        ...initialState,
        jobsCache: new Map(),
        optimisticCache: new OptimisticCache<Job>(),
      });
    });
  },
});

export const useJobStore = create(
  createStoreWithMiddleware(jobStoreCreator, {
    name: 'job-store',
    persist: {
      partialize: (state) => ({
        searchHistory: state.searchHistory,
        savedJobIds: Array.from(state.savedJobIds),
        appliedJobIds: Array.from(state.appliedJobIds),
        filters: state.filters,
        searchParams: state.searchParams,
      }),
      version: 1,
    },
  })
);

// Selectors
export const jobSelectors = {
  jobs: (state: JobState) => state.jobs,
  jobDetails: (state: JobState) => state.jobDetails,
  selectedJob: (state: JobState) =>
    state.selectedJobId ? state.jobDetails[state.selectedJobId] || null : null,
  isJobSaved: (state: JobState) => (jobId: string) => state.savedJobIds.has(jobId),
  isJobApplied: (state: JobState) => (jobId: string) => state.appliedJobIds.has(jobId),
  searchParams: (state: JobState) => state.searchParams,
  filters: (state: JobState) => state.filters,
  pagination: (state: JobState) => state.pagination,
  searchHistory: (state: JobState) => state.searchHistory,
  applications: (state: JobState) => state.applications,
  searchJobsAction: (state: JobState) => state.searchJobsAction,
  getJobDetailsAction: (state: JobState) => state.getJobDetailsAction,
  applyToJobAction: (state: JobState) => state.applyToJobAction,
  saveJobAction: (state: JobState) => state.saveJobAction,
  loadApplicationsAction: (state: JobState) => state.loadApplicationsAction,
};