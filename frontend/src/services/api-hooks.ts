import { useQuery, useMutation, useQueryClient, QueryKey } from '@tanstack/react-query';
import { useCallback } from 'react';
import { apiClient } from './api-client';
import type {
  BatchJob,
  BatchStatus,
  ImportResult,
  Score,
  BatchScoreResult,
  MatchingResult,
  UserMatches,
  EmailPreview,
  QueryResult,
  QueryHistory,
  SystemMetrics,
  HealthStatus,
  JobFilters,
  PaginationParams,
  PaginatedJobs,
} from './api-client';
import { Job, User, UserProfile, PaginatedResponse } from '../types';

// ====================
// QUERY KEYS
// ====================

export const queryKeys = {
  // Batch operations
  batchJobs: ['batch', 'jobs'] as const,
  batchJob: (id: string) => ['batch', 'job', id] as const,
  batchStatus: (id: string) => ['batch', 'status', id] as const,
  batchHistory: (params?: PaginationParams) => ['batch', 'history', params] as const,

  // Jobs
  jobs: ['jobs'] as const,
  job: (id: string) => ['jobs', id] as const,
  jobSearch: (filters: JobFilters & PaginationParams) => ['jobs', 'search', filters] as const,

  // Scores
  scores: ['scores'] as const,
  score: (userId: string, jobId: string) => ['scores', userId, jobId] as const,
  scoreHistory: (userId: string, params?: PaginationParams) => ['scores', 'history', userId, params] as const,

  // Matching
  matching: ['matching'] as const,
  userMatches: (userId: string, params?: PaginationParams) => ['matching', 'user', userId, params] as const,
  matchingStats: (userId: string) => ['matching', 'stats', userId] as const,

  // Email
  email: ['email'] as const,
  emailTemplates: ['email', 'templates'] as const,
  emailPreview: (userId: string, options?: any) => ['email', 'preview', userId, options] as const,

  // SQL
  sql: ['sql'] as const,
  queryHistory: (params?: PaginationParams) => ['sql', 'history', params] as const,
  savedQueries: ['sql', 'saved'] as const,

  // Monitoring
  monitoring: ['monitoring'] as const,
  metrics: (timeRange?: string) => ['monitoring', 'metrics', timeRange] as const,
  health: ['monitoring', 'health'] as const,
  logs: (params?: any) => ['monitoring', 'logs', params] as const,

  // Users
  users: ['users'] as const,
  user: (id: string) => ['users', id] as const,
  userProfile: (id: string) => ['users', id, 'profile'] as const,
  usersList: (params?: PaginationParams & { search?: string }) => ['users', 'list', params] as const,
} as const;

// ====================
// BATCH OPERATIONS HOOKS
// ====================

export const useTriggerBatch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiClient.triggerBatch.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batchJobs });
    },
  });
};

export const useBatchStatus = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.batchStatus(id),
    queryFn: () => apiClient.getBatchStatus(id),
    enabled,
    refetchInterval: (data) => {
      // Auto-refresh if batch is still running
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000; // 2 seconds
      }
      return false;
    },
  });
};

export const useCancelBatch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiClient.cancelBatch.bind(apiClient),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batchStatus(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.batchJobs });
    },
  });
};

export const useBatchHistory = (params?: PaginationParams) => {
  return useQuery({
    queryKey: queryKeys.batchHistory(params),
    queryFn: () => apiClient.getBatchHistory(params),
  });
};

// ====================
// JOB OPERATIONS HOOKS
// ====================

export const useImportJobs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: any }) =>
      apiClient.importJobs(file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.invalidateQueries({ queryKey: queryKeys.batchJobs });
    },
  });
};

export const useSearchJobs = (filters: JobFilters & PaginationParams) => {
  return useQuery({
    queryKey: queryKeys.jobSearch(filters),
    queryFn: () => apiClient.searchJobs(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useJob = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.job(id),
    queryFn: () => apiClient.getJobById(id),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useExportJobs = () => {
  return useMutation({
    mutationFn: apiClient.exportJobs.bind(apiClient),
  });
};

// ====================
// SCORING OPERATIONS HOOKS
// ====================

export const useCalculateScore = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, jobId }: { userId: string; jobId: string }) =>
      apiClient.calculateScore(userId, jobId),
    onSuccess: (_, { userId, jobId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.score(userId, jobId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.scoreHistory(userId) });
    },
  });
};

export const useBatchCalculateScores = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userIds, jobId }: { userIds: string[]; jobId?: string }) =>
      apiClient.batchCalculateScores(userIds, jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.scores });
      queryClient.invalidateQueries({ queryKey: queryKeys.batchJobs });
    },
  });
};

export const useScoreHistory = (userId: string, params?: PaginationParams) => {
  return useQuery({
    queryKey: queryKeys.scoreHistory(userId, params),
    queryFn: () => apiClient.getScoreHistory(userId, params),
  });
};

// ====================
// MATCHING OPERATIONS HOOKS
// ====================

export const useGenerateMatching = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, options }: { userId: string; options?: { forceRefresh?: boolean } }) =>
      apiClient.generateMatching(userId, options),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userMatches(userId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.matchingStats(userId) });
    },
  });
};

export const useUserMatches = (userId: string, params?: PaginationParams) => {
  return useQuery({
    queryKey: queryKeys.userMatches(userId, params),
    queryFn: () => apiClient.getUserMatches(userId, params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateMatchStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ matchId, status }: { matchId: string; status: 'viewed' | 'interested' | 'not-interested' | 'applied' }) =>
      apiClient.updateMatchStatus(matchId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.matching });
    },
  });
};

export const useMatchingStats = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.matchingStats(userId),
    queryFn: () => apiClient.getMatchingStats(userId),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// ====================
// EMAIL OPERATIONS HOOKS
// ====================

export const useGenerateEmail = () => {
  return useMutation({
    mutationFn: ({ userId, options }: { userId: string; options?: { includeMatches?: number } }) =>
      apiClient.generateEmail(userId, options),
  });
};

export const useSendTestEmail = () => {
  return useMutation({
    mutationFn: ({ userId, emailData }: { userId: string; emailData?: any }) =>
      apiClient.sendTestEmail(userId, emailData),
  });
};

export const useScheduleEmailCampaign = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userIds, options }: { userIds: string[]; options?: any }) =>
      apiClient.scheduleEmailCampaign(userIds, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batchJobs });
    },
  });
};

export const useEmailTemplates = () => {
  return useQuery({
    queryKey: queryKeys.emailTemplates,
    queryFn: apiClient.getEmailTemplates.bind(apiClient),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// ====================
// SQL OPERATIONS HOOKS
// ====================

export const useExecuteQuery = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ query, params }: { query: string; params?: any[] }) =>
      apiClient.executeQuery(query, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.queryHistory() });
    },
  });
};

export const useQueryHistory = (params?: PaginationParams) => {
  return useQuery({
    queryKey: queryKeys.queryHistory(params),
    queryFn: () => apiClient.getQueryHistory(params),
  });
};

export const useSaveQuery = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, query, description }: { name: string; query: string; description?: string }) =>
      apiClient.saveQuery(name, query, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.savedQueries });
    },
  });
};

export const useSavedQueries = () => {
  return useQuery({
    queryKey: queryKeys.savedQueries,
    queryFn: apiClient.getSavedQueries.bind(apiClient),
  });
};

// ====================
// MONITORING OPERATIONS HOOKS
// ====================

export const useMetrics = (timeRange?: '1h' | '24h' | '7d' | '30d') => {
  return useQuery({
    queryKey: queryKeys.metrics(timeRange),
    queryFn: () => apiClient.getMetrics(timeRange),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // 1 minute
  });
};

export const useHealthCheck = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: apiClient.getHealthCheck.bind(apiClient),
    staleTime: 0, // Never stale
    refetchInterval: 30 * 1000, // 30 seconds
  });
};

export const useSystemLogs = (params?: PaginationParams & { level?: string; service?: string }) => {
  return useQuery({
    queryKey: queryKeys.logs(params),
    queryFn: () => apiClient.getSystemLogs(params),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

// ====================
// USER OPERATIONS HOOKS
// ====================

export const useUsers = (params?: PaginationParams & { search?: string }) => {
  return useQuery({
    queryKey: queryKeys.usersList(params),
    queryFn: () => apiClient.getUsers(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUser = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.user(id),
    queryFn: () => apiClient.getUserById(id),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUserProfile = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.userProfile(id),
    queryFn: () => apiClient.getUserProfile(id),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateUserProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, profile }: { id: string; profile: Partial<UserProfile> }) =>
      apiClient.updateUserProfile(id, profile),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.user(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.userProfile(id) });
    },
  });
};

// ====================
// UTILITY HOOKS
// ====================

export const useApiClient = () => {
  const queryClient = useQueryClient();

  const clearCache = useCallback((pattern?: string) => {
    if (pattern) {
      // Clear specific cache pattern
      queryClient.getQueryCache().findAll().forEach((query) => {
        if (query.queryKey.some(key => typeof key === 'string' && key.includes(pattern))) {
          queryClient.removeQueries({ queryKey: query.queryKey });
        }
      });
    } else {
      queryClient.clear();
    }
    apiClient.clearCache(pattern);
  }, [queryClient]);

  const cancelRequests = useCallback((key?: string) => {
    if (key) {
      apiClient.cancelRequest(key);
    } else {
      apiClient.cancelAllRequests();
    }
  }, []);

  const updateConfig = useCallback((config: any) => {
    apiClient.updateConfig(config);
  }, []);

  return {
    client: apiClient,
    clearCache,
    cancelRequests,
    updateConfig,
    config: apiClient.getConfig(),
  };
};

// ====================
// POLLING HOOKS
// ====================

export const usePollingBatchStatus = (id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.batchStatus(id),
    queryFn: () => apiClient.getBatchStatus(id),
    enabled,
    refetchInterval: (data) => {
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling when completed/failed
    },
    refetchIntervalInBackground: false,
  });
};

export const usePollingMetrics = (timeRange?: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.metrics(timeRange),
    queryFn: () => apiClient.getMetrics(timeRange as any),
    enabled,
    refetchInterval: 60 * 1000, // Poll every minute
    refetchIntervalInBackground: false,
  });
};

export const usePollingHealth = (enabled = true) => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: apiClient.getHealthCheck.bind(apiClient),
    enabled,
    refetchInterval: 30 * 1000, // Poll every 30 seconds
    refetchIntervalInBackground: false,
  });
};

// ====================
// OPTIMISTIC UPDATES HOOKS
// ====================

export const useOptimisticMatchStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ matchId, status }: { matchId: string; status: 'viewed' | 'interested' | 'not-interested' | 'applied' }) =>
      apiClient.updateMatchStatus(matchId, status),
    onMutate: async ({ matchId, status }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.matching });

      // Snapshot the previous value
      const previousMatches = queryClient.getQueriesData({ queryKey: queryKeys.matching });

      // Optimistically update the cache
      queryClient.setQueriesData({ queryKey: queryKeys.matching }, (old: any) => {
        if (!old) return old;

        if (old.matches) {
          return {
            ...old,
            matches: old.matches.map((match: any) =>
              match.id === matchId ? { ...match, status } : match
            ),
          };
        }

        return old;
      });

      return { previousMatches };
    },
    onError: (err, variables, context) => {
      // Revert the optimistic update
      if (context?.previousMatches) {
        context.previousMatches.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.matching });
    },
  });
};

// ====================
// INFINITE QUERY HOOKS
// ====================

export const useInfiniteJobSearch = (filters: JobFilters) => {
  return useQuery({
    queryKey: ['jobs', 'infinite', filters],
    queryFn: ({ pageParam = 1 }) =>
      apiClient.searchJobs({ ...filters, page: pageParam, limit: 20 }),
    // getNextPageParam: (lastPage) => {
    //   const { page, pages } = lastPage.pagination;
    //   return page < pages ? page + 1 : undefined;
    // },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useInfiniteQueryHistory = () => {
  return useQuery({
    queryKey: ['sql', 'history', 'infinite'],
    queryFn: ({ pageParam = 1 }) =>
      apiClient.getQueryHistory({ page: pageParam, limit: 50 }),
    // getNextPageParam: (lastPage) => {
    //   const { page, pages } = lastPage.pagination;
    //   return page < pages ? page + 1 : undefined;
    // },
  });
};

// ====================
// PREFETCH HOOKS
// ====================

export const usePrefetchJob = () => {
  const queryClient = useQueryClient();

  return useCallback((id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.job(id),
      queryFn: () => apiClient.getJobById(id),
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);
};

export const usePrefetchUserProfile = () => {
  const queryClient = useQueryClient();

  return useCallback((id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.userProfile(id),
      queryFn: () => apiClient.getUserProfile(id),
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);
};

// ====================
// ERROR BOUNDARY HELPERS
// ====================

export const useApiErrorHandler = () => {
  const queryClient = useQueryClient();

  return useCallback((error: any) => {
    if (error?.status === 401) {
      // Clear all cached data on authentication error
      queryClient.clear();
      apiClient.clearCache();
    }

    // Log error for debugging
    console.error('API Error:', error);

    // You can add custom error handling logic here
    // e.g., show toast notifications, redirect to error page, etc.
  }, [queryClient]);
};

export default {
  // Batch operations
  useTriggerBatch,
  useBatchStatus,
  useCancelBatch,
  useBatchHistory,

  // Job operations
  useImportJobs,
  useSearchJobs,
  useJob,
  useExportJobs,

  // Scoring operations
  useCalculateScore,
  useBatchCalculateScores,
  useScoreHistory,

  // Matching operations
  useGenerateMatching,
  useUserMatches,
  useUpdateMatchStatus,
  useMatchingStats,

  // Email operations
  useGenerateEmail,
  useSendTestEmail,
  useScheduleEmailCampaign,
  useEmailTemplates,

  // SQL operations
  useExecuteQuery,
  useQueryHistory,
  useSaveQuery,
  useSavedQueries,

  // Monitoring operations
  useMetrics,
  useHealthCheck,
  useSystemLogs,

  // User operations
  useUsers,
  useUser,
  useUserProfile,
  useUpdateUserProfile,

  // Utility hooks
  useApiClient,
  usePollingBatchStatus,
  usePollingMetrics,
  usePollingHealth,
  useOptimisticMatchStatus,
  useInfiniteJobSearch,
  useInfiniteQueryHistory,
  usePrefetchJob,
  usePrefetchUserProfile,
  useApiErrorHandler,
};