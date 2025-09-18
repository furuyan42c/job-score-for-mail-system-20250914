import { QueryClient, DefaultOptions } from '@tanstack/react-query';
import { ApiError } from '../api/client';

// Default query options
const defaultOptions: DefaultOptions = {
  queries: {
    // Stale time: Data is considered fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
    // Cache time: Data stays in cache for 10 minutes after component unmounts
    gcTime: 10 * 60 * 1000,
    // Retry failed requests 3 times with exponential backoff
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors (client errors)
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        return false;
      }
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Refetch on window focus for important data
    refetchOnWindowFocus: false,
    // Refetch on reconnect
    refetchOnReconnect: 'always',
  },
  mutations: {
    // Retry mutations once
    retry: 1,
    retryDelay: 1000,
  },
};

// Create QueryClient instance
export const queryClient = new QueryClient({
  defaultOptions,
});

// Query key factories for consistent cache management
export const queryKeys = {
  // User queries
  user: ['user'] as const,
  userProfile: ['user', 'profile'] as const,
  userPreferences: ['user', 'preferences'] as const,

  // Job queries
  jobs: ['jobs'] as const,
  jobsSearch: (params: any) => ['jobs', 'search', params] as const,
  jobDetail: (id: string) => ['jobs', 'detail', id] as const,
  jobsByCompany: (companyId: string) => ['jobs', 'company', companyId] as const,
  featuredJobs: ['jobs', 'featured'] as const,
  recentJobs: ['jobs', 'recent'] as const,
  jobSkills: ['jobs', 'skills'] as const,
  jobLocations: ['jobs', 'locations'] as const,
  jobCompanies: ['jobs', 'companies'] as const,

  // Application queries
  applications: ['applications'] as const,
  myApplications: (filters?: any) => ['applications', 'me', filters] as const,
  applicationDetail: (id: string) => ['applications', 'detail', id] as const,
  applicationHistory: (jobId: string) => ['applications', 'history', jobId] as const,

  // Score queries
  scores: ['scores'] as const,
  jobScore: (jobId: string) => ['scores', 'job', jobId] as const,
  batchScores: (jobIds: string[]) => ['scores', 'batch', jobIds] as const,
  rankedJobs: (params?: any) => ['scores', 'ranked', params] as const,
  scoreHistory: (params?: any) => ['scores', 'history', params] as const,
  scoreBreakdown: (jobId: string) => ['scores', 'breakdown', jobId] as const,
  scoreWeights: ['scores', 'weights'] as const,
  scoreStats: ['scores', 'stats'] as const,

  // Saved jobs queries
  savedJobs: ['saved-jobs'] as const,
  savedJobsList: (params?: any) => ['saved-jobs', 'list', params] as const,
  savedJobStatus: (jobId: string) => ['saved-jobs', 'status', jobId] as const,

  // Saved searches queries
  savedSearches: ['saved-searches'] as const,
  savedSearchDetail: (id: string) => ['saved-searches', 'detail', id] as const,

  // Company queries
  companies: ['companies'] as const,
  companyDetail: (id: string) => ['companies', 'detail', id] as const,
  companyJobs: (id: string, params?: any) => ['companies', id, 'jobs', params] as const,
  followedCompanies: ['companies', 'followed'] as const,

  // Analytics queries
  analytics: ['analytics'] as const,
  userAnalytics: ['analytics', 'user'] as const,
  jobAnalytics: (jobId: string) => ['analytics', 'job', jobId] as const,

  // Notifications queries
  notifications: ['notifications'] as const,
  notificationsList: (params?: any) => ['notifications', 'list', params] as const,
  unreadCount: ['notifications', 'unread-count'] as const,
};

// Cache invalidation helpers
export const invalidateQueries = {
  // Invalidate all user-related queries
  user: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.user });
    queryClient.invalidateQueries({ queryKey: queryKeys.userProfile });
    queryClient.invalidateQueries({ queryKey: queryKeys.userPreferences });
  },

  // Invalidate job-related queries
  jobs: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
    queryClient.invalidateQueries({ queryKey: queryKeys.featuredJobs });
    queryClient.invalidateQueries({ queryKey: queryKeys.recentJobs });
  },

  // Invalidate specific job
  job: (jobId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.jobDetail(jobId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.jobScore(jobId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.scoreBreakdown(jobId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.savedJobStatus(jobId) });
  },

  // Invalidate application-related queries
  applications: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.applications });
    queryClient.invalidateQueries({ queryKey: queryKeys.myApplications() });
  },

  // Invalidate score-related queries
  scores: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.scores });
    queryClient.invalidateQueries({ queryKey: queryKeys.rankedJobs() });
    queryClient.invalidateQueries({ queryKey: queryKeys.scoreHistory() });
    queryClient.invalidateQueries({ queryKey: queryKeys.scoreStats });
  },

  // Invalidate saved jobs
  savedJobs: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.savedJobs });
    queryClient.invalidateQueries({ queryKey: queryKeys.savedJobsList() });
  },

  // Invalidate saved searches
  savedSearches: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.savedSearches });
  },

  // Invalidate notifications
  notifications: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.notifications });
    queryClient.invalidateQueries({ queryKey: queryKeys.unreadCount });
  },

  // Invalidate analytics
  analytics: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.analytics });
  },
};

// Optimistic update helpers
export const optimisticUpdates = {
  // Update job save status optimistically
  toggleJobSave: (jobId: string, isSaved: boolean) => {
    queryClient.setQueryData(queryKeys.savedJobStatus(jobId), { isSaved });

    // Update saved jobs list
    const savedJobsKey = queryKeys.savedJobsList();
    queryClient.setQueryData(savedJobsKey, (oldData: any) => {
      if (!oldData) return oldData;

      if (isSaved) {
        // Add job to saved list (would need job data)
        return oldData;
      } else {
        // Remove job from saved list
        return {
          ...oldData,
          data: oldData.data?.filter((job: any) => job.id !== jobId) || [],
        };
      }
    });
  },

  // Update application status optimistically
  updateApplicationStatus: (applicationId: string, status: string) => {
    queryClient.setQueryData(queryKeys.applicationDetail(applicationId), (oldData: any) => {
      if (!oldData) return oldData;
      return {
        ...oldData,
        data: {
          ...oldData.data,
          status,
          lastStatusUpdate: new Date().toISOString(),
        },
      };
    });

    // Update applications list
    queryClient.setQueryData(queryKeys.myApplications(), (oldData: any) => {
      if (!oldData) return oldData;
      return {
        ...oldData,
        data: oldData.data?.map((app: any) =>
          app.id === applicationId
            ? { ...app, status, lastStatusUpdate: new Date().toISOString() }
            : app
        ) || [],
      };
    });
  },

  // Update notification read status
  markNotificationAsRead: (notificationId: string) => {
    queryClient.setQueryData(queryKeys.notificationsList(), (oldData: any) => {
      if (!oldData) return oldData;
      return {
        ...oldData,
        data: oldData.data?.map((notification: any) =>
          notification.id === notificationId
            ? { ...notification, isRead: true }
            : notification
        ) || [],
      };
    });

    // Update unread count
    queryClient.setQueryData(queryKeys.unreadCount, (oldData: any) => {
      if (!oldData) return oldData;
      return {
        ...oldData,
        count: Math.max(0, oldData.count - 1),
      };
    });
  },
};

// Prefetch helpers for better UX
export const prefetchQueries = {
  // Prefetch job details when hovering over job card
  jobDetails: (jobId: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.jobDetail(jobId),
      staleTime: 10 * 60 * 1000, // 10 minutes
    });
  },

  // Prefetch related data when user logs in
  userRelatedData: () => {
    queryClient.prefetchQuery({ queryKey: queryKeys.userProfile });
    queryClient.prefetchQuery({ queryKey: queryKeys.myApplications() });
    queryClient.prefetchQuery({ queryKey: queryKeys.savedJobs });
    queryClient.prefetchQuery({ queryKey: queryKeys.savedSearches });
    queryClient.prefetchQuery({ queryKey: queryKeys.unreadCount });
  },

  // Prefetch job scores when viewing job list
  jobScores: (jobIds: string[]) => {
    jobIds.forEach(jobId => {
      queryClient.prefetchQuery({
        queryKey: queryKeys.jobScore(jobId),
        staleTime: 15 * 60 * 1000, // 15 minutes
      });
    });
  },
};

// Background sync for real-time updates
export const backgroundSync = {
  // Sync notifications periodically
  startNotificationSync: () => {
    const syncInterval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: queryKeys.unreadCount });
    }, 30000); // Every 30 seconds

    return () => clearInterval(syncInterval);
  },

  // Sync application status periodically
  startApplicationSync: () => {
    const syncInterval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: queryKeys.myApplications() });
    }, 60000); // Every minute

    return () => clearInterval(syncInterval);
  },
};

// Error handling helpers
export const handleQueryError = (error: unknown) => {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        // Handle authentication error
        queryClient.clear(); // Clear all cache
        window.location.href = '/login';
        break;
      case 403:
        // Handle authorization error
        console.error('Access denied:', error.message);
        break;
      case 404:
        // Handle not found error
        console.error('Resource not found:', error.message);
        break;
      case 500:
        // Handle server error
        console.error('Server error:', error.message);
        break;
      default:
        console.error('API error:', error.message);
    }
  } else {
    console.error('Unexpected error:', error);
  }
};

// Cache management utilities
export const cacheUtils = {
  // Get cached data without triggering a fetch
  getCachedData: <T>(queryKey: readonly unknown[]): T | undefined => {
    return queryClient.getQueryData<T>(queryKey);
  },

  // Set data in cache manually
  setCachedData: <T>(queryKey: readonly unknown[], data: T) => {
    queryClient.setQueryData(queryKey, data);
  },

  // Remove specific query from cache
  removeQuery: (queryKey: readonly unknown[]) => {
    queryClient.removeQueries({ queryKey });
  },

  // Clear all cache
  clearAll: () => {
    queryClient.clear();
  },

  // Get cache size (for debugging)
  getCacheSize: () => {
    const cache = queryClient.getQueryCache();
    return cache.getAll().length;
  },
};

// Development helpers
if (process.env.NODE_ENV === 'development') {
  // Log cache changes in development
  queryClient.getQueryCache().subscribe((event) => {
    console.log('Query cache event:', event);
  });

  // Add cache to window for debugging
  (window as any).queryClient = queryClient;
  (window as any).queryKeys = queryKeys;
  (window as any).cacheUtils = cacheUtils;
}