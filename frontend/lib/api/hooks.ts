/**
 * React Hooks for API Integration
 *
 * Custom React hooks that integrate with React Query for efficient
 * data fetching, caching, and state management with the API client.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { apiClient, realtimeManager } from './supabase';
import {
  Job,
  User,
  Score,
  BatchExecution,
  BatchType,
  JobSearchParams,
  UserSearchParams,
  ScoringParams,
  ImportJobsParams,
  ApiResponse,
  SystemLog,
  SystemMetrics,
  EmailPreview,
  LogFilters,
  PaginationParams,
} from './types';
import { API_CONFIG, apiUtils } from './index';

// =====================================================================================
// QUERY KEYS
// =====================================================================================

export const queryKeys = {
  // Jobs
  jobs: ['jobs'] as const,
  jobSearch: (params: JobSearchParams) => ['jobs', 'search', params] as const,
  job: (id: number) => ['jobs', id] as const,
  recommendedJobs: (userId: number, limit?: number, minScore?: number) =>
    ['jobs', 'recommended', userId, limit, minScore] as const,

  // Users
  users: ['users'] as const,
  userSearch: (params: UserSearchParams) => ['users', 'search', params] as const,
  user: (id: number) => ['users', id] as const,

  // Scores
  scores: ['scores'] as const,
  userScores: (userId: number, params?: PaginationParams) =>
    ['scores', 'user', userId, params] as const,

  // Batches
  batches: ['batches'] as const,
  batch: (id: string) => ['batches', id] as const,
  batchList: (params?: PaginationParams) => ['batches', 'list', params] as const,

  // Monitoring
  systemMetrics: ['monitoring', 'metrics'] as const,
  systemLogs: (filters?: LogFilters) => ['monitoring', 'logs', filters] as const,
  healthStatus: ['monitoring', 'health'] as const,

  // Email
  emailPreview: (userId: number) => ['email', 'preview', userId] as const,
  emailJob: (emailId: string) => ['email', 'job', emailId] as const,
} as const;

// =====================================================================================
// JOB HOOKS
// =====================================================================================

/**
 * Hook for searching jobs with pagination and filters
 */
export function useJobSearch(
  params: JobSearchParams = {},
  options?: UseQueryOptions<ApiResponse<Job[]>>
) {
  return useQuery({
    queryKey: queryKeys.jobSearch(params),
    queryFn: () => apiClient.searchJobs(params),
    staleTime: API_CONFIG.CACHE.MEDIUM,
    ...options,
  });
}

/**
 * Hook for getting a single job by ID
 */
export function useJob(
  jobId: number,
  options?: UseQueryOptions<Job>
) {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => apiClient.getJobById(jobId),
    staleTime: API_CONFIG.CACHE.LONG,
    enabled: !!jobId,
    ...options,
  });
}

/**
 * Hook for getting recommended jobs for a user
 */
export function useRecommendedJobs(
  userId: number,
  limit: number = 10,
  minScore: number = 0.5,
  options?: UseQueryOptions<Job[]>
) {
  return useQuery({
    queryKey: queryKeys.recommendedJobs(userId, limit, minScore),
    queryFn: () => apiClient.getRecommendedJobs(userId, limit, minScore),
    staleTime: API_CONFIG.CACHE.MEDIUM,
    enabled: !!userId,
    ...options,
  });
}

/**
 * Hook for importing jobs
 */
export function useImportJobs(
  options?: UseMutationOptions<any, Error, ImportJobsParams>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: ImportJobsParams) => apiClient.importJobs(params),
    onSuccess: () => {
      // Invalidate job-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
    ...options,
  });
}

/**
 * Hook for updating a job
 */
export function useUpdateJob(
  options?: UseMutationOptions<Job, Error, { jobId: number; updates: Partial<Job> }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, updates }) => apiClient.updateJob(jobId, updates),
    onSuccess: (updatedJob) => {
      // Update the specific job cache
      queryClient.setQueryData(queryKeys.job(updatedJob.job_id), updatedJob);
      // Invalidate search results
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
    },
    ...options,
  });
}

// =====================================================================================
// USER HOOKS
// =====================================================================================

/**
 * Hook for searching users with pagination and filters
 */
export function useUserSearch(
  params: UserSearchParams = {},
  options?: UseQueryOptions<ApiResponse<User[]>>
) {
  return useQuery({
    queryKey: queryKeys.userSearch(params),
    queryFn: () => apiClient.searchUsers(params),
    staleTime: API_CONFIG.CACHE.MEDIUM,
    ...options,
  });
}

/**
 * Hook for getting a single user by ID
 */
export function useUser(
  userId: number,
  options?: UseQueryOptions<User>
) {
  return useQuery({
    queryKey: queryKeys.user(userId),
    queryFn: () => apiClient.getUserById(userId),
    staleTime: API_CONFIG.CACHE.LONG,
    enabled: !!userId,
    ...options,
  });
}

/**
 * Hook for getting user scores
 */
export function useUserScores(
  userId: number,
  params: PaginationParams = {},
  options?: UseQueryOptions<ApiResponse<Score[]>>
) {
  return useQuery({
    queryKey: queryKeys.userScores(userId, params),
    queryFn: () => apiClient.getUserScores(userId, params),
    staleTime: API_CONFIG.CACHE.SHORT,
    enabled: !!userId,
    ...options,
  });
}

// =====================================================================================
// SCORING HOOKS
// =====================================================================================

/**
 * Hook for calculating scores
 */
export function useCalculateScores(
  options?: UseMutationOptions<any, Error, ScoringParams>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: ScoringParams) => apiClient.calculateScores(params),
    onSuccess: () => {
      // Invalidate score-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.scores });
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
    ...options,
  });
}

// =====================================================================================
// BATCH HOOKS
// =====================================================================================

/**
 * Hook for getting batch executions list
 */
export function useBatchExecutions(
  params: PaginationParams = {},
  options?: UseQueryOptions<ApiResponse<BatchExecution[]>>
) {
  return useQuery({
    queryKey: queryKeys.batchList(params),
    queryFn: () => apiClient.getBatchExecutions(params),
    staleTime: API_CONFIG.CACHE.SHORT,
    refetchInterval: 5000, // Refresh every 5 seconds for active batches
    ...options,
  });
}

/**
 * Hook for getting batch status with real-time updates
 */
export function useBatchStatus(
  batchId: string,
  options?: UseQueryOptions<BatchExecution>
) {
  const queryClient = useQueryClient();

  // Subscribe to real-time updates
  useEffect(() => {
    if (!batchId) return;

    const subscription = realtimeManager.subscribeToBatchStatus(
      batchId,
      (payload) => {
        if (payload.new) {
          queryClient.setQueryData(queryKeys.batch(batchId), payload.new);
        }
      }
    );

    return () => {
      realtimeManager.unsubscribe(`batch-${batchId}`);
    };
  }, [batchId, queryClient]);

  return useQuery({
    queryKey: queryKeys.batch(batchId),
    queryFn: () => apiClient.getBatchStatus(batchId),
    enabled: !!batchId,
    refetchInterval: (data) => {
      // Stop polling if batch is completed
      return data?.status === 'completed' || data?.status === 'failed'
        ? false
        : 2000;
    },
    ...options,
  });
}

/**
 * Hook for triggering batch operations
 */
export function useTriggerBatch(
  options?: UseMutationOptions<BatchExecution, Error, { type: BatchType; config?: Record<string, any> }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ type, config }) => apiClient.triggerBatch(type, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
    ...options,
  });
}

/**
 * Hook for canceling batch operations
 */
export function useCancelBatch(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (batchId: string) => apiClient.cancelBatch(batchId),
    onSuccess: (_, batchId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batch(batchId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
    ...options,
  });
}

// =====================================================================================
// MONITORING HOOKS
// =====================================================================================

/**
 * Hook for system health status
 */
export function useHealthStatus(
  options?: UseQueryOptions<{ status: 'healthy' | 'unhealthy'; details: any }>
) {
  return useQuery({
    queryKey: queryKeys.healthStatus,
    queryFn: () => apiClient.getHealthStatus(),
    staleTime: API_CONFIG.CACHE.SHORT,
    refetchInterval: 30000, // Check every 30 seconds
    ...options,
  });
}

/**
 * Hook for system metrics
 */
export function useSystemMetrics(
  startDate?: string,
  endDate?: string,
  options?: UseQueryOptions<SystemMetrics[]>
) {
  return useQuery({
    queryKey: [...queryKeys.systemMetrics, startDate, endDate],
    queryFn: () => apiClient.getSystemMetrics(startDate, endDate),
    staleTime: API_CONFIG.CACHE.SHORT,
    ...options,
  });
}

/**
 * Hook for system logs with real-time streaming
 */
export function useSystemLogs(
  filters: LogFilters = {},
  enableRealtime: boolean = false
) {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Initial load
  useEffect(() => {
    const loadLogs = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.getLogs(filters);
        setLogs(data);
        setError(null);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    loadLogs();
  }, [JSON.stringify(filters)]);

  // Real-time subscription
  useEffect(() => {
    if (!enableRealtime) return;

    const subscription = apiClient.subscribeToLogs((newLog) => {
      setLogs(prevLogs => [newLog, ...prevLogs.slice(0, 999)]); // Keep last 1000 logs
    });

    return () => {
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, [enableRealtime]);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getLogs(filters);
      setLogs(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [JSON.stringify(filters)]);

  return {
    logs,
    isLoading,
    error,
    refresh,
  };
}

/**
 * Hook for executing SQL queries
 */
export function useExecuteSQL(
  options?: UseMutationOptions<any, Error, string>
) {
  return useMutation({
    mutationFn: (query: string) => apiClient.executeSQL(query),
    ...options,
  });
}

// =====================================================================================
// EMAIL HOOKS
// =====================================================================================

/**
 * Hook for email preview
 */
export function useEmailPreview(
  userId: number,
  options?: UseQueryOptions<EmailPreview>
) {
  return useQuery({
    queryKey: queryKeys.emailPreview(userId),
    queryFn: () => apiClient.previewEmail(userId),
    enabled: !!userId,
    staleTime: API_CONFIG.CACHE.SHORT,
    ...options,
  });
}

/**
 * Hook for sending emails
 */
export function useSendEmail(
  options?: UseMutationOptions<any, Error, { userId: number; scheduleTime?: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, scheduleTime }) => apiClient.sendEmail(userId, scheduleTime),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.batches });
    },
    ...options,
  });
}

/**
 * Hook for getting email job status
 */
export function useEmailJob(
  emailId: string,
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: queryKeys.emailJob(emailId),
    queryFn: () => apiClient.getEmailJob(emailId),
    enabled: !!emailId,
    refetchInterval: (data) => {
      // Stop polling if email is sent or failed
      return data?.send_status === 'sent' || data?.send_status === 'failed'
        ? false
        : 5000;
    },
    ...options,
  });
}

// =====================================================================================
// UTILITY HOOKS
// =====================================================================================

/**
 * Hook for debounced search
 */
export function useDebouncedSearch<T>(
  searchFn: (query: string) => Promise<T>,
  delay: number = 300
) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, delay);

    return () => clearTimeout(timer);
  }, [query, delay]);

  const search = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchFn(debouncedQuery),
    enabled: debouncedQuery.length > 0,
    staleTime: API_CONFIG.CACHE.SHORT,
  });

  return {
    query,
    setQuery,
    debouncedQuery,
    ...search,
  };
}

/**
 * Hook for pagination state management
 */
export function usePagination(initialPage: number = 1, initialPageSize: number = 20) {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const reset = useCallback(() => {
    setPage(1);
  }, []);

  const goToPage = useCallback((newPage: number) => {
    setPage(Math.max(1, newPage));
  }, []);

  const nextPage = useCallback(() => {
    setPage(prev => prev + 1);
  }, []);

  const prevPage = useCallback(() => {
    setPage(prev => Math.max(1, prev - 1));
  }, []);

  const changePageSize = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when changing page size
  }, []);

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    goToPage,
    nextPage,
    prevPage,
    changePageSize,
    reset,
  };
}

/**
 * Hook for optimistic updates
 */
export function useOptimisticUpdate<T>(
  queryKey: any[],
  updateFn: (oldData: T | undefined, variables: any) => T
) {
  const queryClient = useQueryClient();

  const mutate = useCallback(
    async (variables: any, actualUpdateFn: () => Promise<T>) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousData = queryClient.getQueryData<T>(queryKey);

      // Optimistically update
      queryClient.setQueryData<T>(queryKey, (old) => updateFn(old, variables));

      try {
        // Perform the actual update
        const result = await actualUpdateFn();
        // Update with real data
        queryClient.setQueryData(queryKey, result);
        return result;
      } catch (error) {
        // Rollback on error
        queryClient.setQueryData(queryKey, previousData);
        throw error;
      }
    },
    [queryClient, queryKey, updateFn]
  );

  return mutate;
}