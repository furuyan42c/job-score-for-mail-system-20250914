import { useQuery, useMutation, useInfiniteQuery, UseQueryOptions, UseMutationOptions, UseInfiniteQueryOptions } from '@tanstack/react-query';
import { api } from '../api/endpoints';
import { queryKeys, queryClient, invalidateQueries, optimisticUpdates } from './client';
import {
  User,
  UserProfile,
  UserPreferences,
  Job,
  JobSearchParams,
  JobScore,
  JobApplication,
  SavedSearch,
  ApiResponse,
  PaginatedResponse
} from '../types';

// User hooks
export const useUser = (options?: UseQueryOptions<ApiResponse<{ user: User; profile: UserProfile | null }>>) => {
  return useQuery({
    queryKey: queryKeys.user,
    queryFn: api.user.getCurrentUser,
    ...options,
  });
};

export const useUpdateUser = () => {
  return useMutation({
    mutationFn: api.user.updateUser,
    onSuccess: () => {
      invalidateQueries.user();
    },
  });
};

export const useUpdateProfile = () => {
  return useMutation({
    mutationFn: api.profile.updateProfile,
    onSuccess: () => {
      invalidateQueries.user();
    },
  });
};

export const useUpdatePreferences = () => {
  return useMutation({
    mutationFn: api.profile.updatePreferences,
    onSuccess: () => {
      invalidateQueries.user();
    },
  });
};

// Job hooks
export const useJobs = (
  params?: JobSearchParams & { page?: number; limit?: number },
  options?: UseQueryOptions<PaginatedResponse<Job>>
) => {
  return useQuery({
    queryKey: queryKeys.jobsSearch(params),
    queryFn: () => api.jobs.getJobs(params),
    enabled: !!params || Object.keys(params || {}).length === 0,
    ...options,
  });
};

export const useInfiniteJobs = (
  params?: JobSearchParams,
  options?: UseInfiniteQueryOptions<PaginatedResponse<Job>>
) => {
  return useInfiniteQuery({
    queryKey: queryKeys.jobsSearch(params),
    queryFn: ({ pageParam = 1 }) => api.jobs.getJobs({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      return lastPage.pagination.hasNext ? lastPage.pagination.page + 1 : undefined;
    },
    ...options,
  });
};

export const useJob = (
  jobId: string,
  options?: UseQueryOptions<ApiResponse<Job>>
) => {
  return useQuery({
    queryKey: queryKeys.jobDetail(jobId),
    queryFn: () => api.jobs.getJobById(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useFeaturedJobs = (options?: UseQueryOptions<ApiResponse<Job[]>>) => {
  return useQuery({
    queryKey: queryKeys.featuredJobs,
    queryFn: api.jobs.getFeaturedJobs,
    ...options,
  });
};

export const useJobSkills = (options?: UseQueryOptions<ApiResponse<string[]>>) => {
  return useQuery({
    queryKey: queryKeys.jobSkills,
    queryFn: api.jobs.getJobSkills,
    staleTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
};

export const useJobLocations = (options?: UseQueryOptions<ApiResponse<string[]>>) => {
  return useQuery({
    queryKey: queryKeys.jobLocations,
    queryFn: api.jobs.getJobLocations,
    staleTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
};

export const useJobCompanies = (options?: UseQueryOptions<ApiResponse<Array<{ id: string; name: string; logo?: string }>>>) => {
  return useQuery({
    queryKey: queryKeys.jobCompanies,
    queryFn: api.jobs.getJobCompanies,
    staleTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
};

// Application hooks
export const useMyApplications = (
  params?: { status?: JobApplication['status']; page?: number; limit?: number },
  options?: UseQueryOptions<PaginatedResponse<JobApplication>>
) => {
  return useQuery({
    queryKey: queryKeys.myApplications(params),
    queryFn: () => api.applications.getMyApplications(params),
    ...options,
  });
};

export const useApplication = (
  applicationId: string,
  options?: UseQueryOptions<ApiResponse<JobApplication>>
) => {
  return useQuery({
    queryKey: queryKeys.applicationDetail(applicationId),
    queryFn: () => api.applications.getApplicationById(applicationId),
    enabled: !!applicationId,
    ...options,
  });
};

export const useApplyToJob = () => {
  return useMutation({
    mutationFn: ({ jobId, applicationData }: {
      jobId: string;
      applicationData: { coverLetter?: string; resumeUrl?: string; customResponses?: Record<string, string> };
    }) => api.applications.applyToJob(jobId, applicationData),
    onSuccess: () => {
      invalidateQueries.applications();
    },
  });
};

export const useWithdrawApplication = () => {
  return useMutation({
    mutationFn: api.applications.withdrawApplication,
    onSuccess: () => {
      invalidateQueries.applications();
    },
  });
};

// Score hooks
export const useJobScore = (
  jobId: string,
  options?: UseQueryOptions<ApiResponse<JobScore>>
) => {
  return useQuery({
    queryKey: queryKeys.jobScore(jobId),
    queryFn: () => api.scores.getJobScore(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useCalculateJobScore = () => {
  return useMutation({
    mutationFn: api.scores.calculateJobScore,
    onSuccess: (data, jobId) => {
      // Update the job score in cache
      queryClient.setQueryData(queryKeys.jobScore(jobId), data);
      // Invalidate related queries
      invalidateQueries.scores();
    },
  });
};

export const useBatchJobScores = () => {
  return useMutation({
    mutationFn: api.scores.getBatchJobScores,
    onSuccess: (data) => {
      // Update individual job scores in cache
      data.data.forEach(score => {
        queryClient.setQueryData(queryKeys.jobScore(score.jobId), {
          status: 'success',
          data: score
        });
      });
      invalidateQueries.scores();
    },
  });
};

export const useRankedJobs = (
  params?: { limit?: number; minScore?: number; skills?: string[]; locations?: string[] },
  options?: UseQueryOptions<ApiResponse<Array<{
    job: Job;
    score: JobScore;
    breakdown: Array<{ category: string; score: number; weight: number; explanation: string }>;
    ranking: number;
  }>>>
) => {
  return useQuery({
    queryKey: queryKeys.rankedJobs(params),
    queryFn: () => api.scores.getRankedJobs(params),
    ...options,
  });
};

export const useScoreHistory = (
  params?: { page?: number; limit?: number; dateFrom?: string; dateTo?: string },
  options?: UseQueryOptions<PaginatedResponse<JobScore>>
) => {
  return useQuery({
    queryKey: queryKeys.scoreHistory(params),
    queryFn: () => api.scores.getScoreHistory(params),
    ...options,
  });
};

export const useScoreBreakdown = (
  jobId: string,
  options?: UseQueryOptions<ApiResponse<Array<{ category: string; score: number; weight: number; explanation: string }>>>
) => {
  return useQuery({
    queryKey: queryKeys.scoreBreakdown(jobId),
    queryFn: () => api.scores.getScoreBreakdown(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useScoreWeights = (options?: UseQueryOptions<ApiResponse<Record<string, number>>>) => {
  return useQuery({
    queryKey: queryKeys.scoreWeights,
    queryFn: api.scores.getScoreWeights,
    ...options,
  });
};

export const useUpdateScoreWeights = () => {
  return useMutation({
    mutationFn: api.scores.updateScoreWeights,
    onSuccess: () => {
      invalidateQueries.scores();
    },
  });
};

export const useScoreStats = (options?: UseQueryOptions<ApiResponse<{
  totalScores: number;
  averageScore: number;
  topScore: number;
  scoreDistribution: Record<string, number>;
}>>) => {
  return useQuery({
    queryKey: queryKeys.scoreStats,
    queryFn: api.scores.getScoreStats,
    ...options,
  });
};

// Saved Jobs hooks
export const useSavedJobs = (
  params?: { page?: number; limit?: number },
  options?: UseQueryOptions<PaginatedResponse<Job>>
) => {
  return useQuery({
    queryKey: queryKeys.savedJobsList(params),
    queryFn: () => api.savedJobs.getSavedJobs(params),
    ...options,
  });
};

export const useIsSavedJob = (
  jobId: string,
  options?: UseQueryOptions<ApiResponse<{ isSaved: boolean }>>
) => {
  return useQuery({
    queryKey: queryKeys.savedJobStatus(jobId),
    queryFn: () => api.savedJobs.isSaved(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useSaveJob = () => {
  return useMutation({
    mutationFn: api.savedJobs.saveJob,
    onMutate: async (jobId) => {
      // Optimistic update
      optimisticUpdates.toggleJobSave(jobId, true);
    },
    onSuccess: () => {
      invalidateQueries.savedJobs();
    },
    onError: (error, jobId) => {
      // Rollback optimistic update
      optimisticUpdates.toggleJobSave(jobId, false);
    },
  });
};

export const useUnsaveJob = () => {
  return useMutation({
    mutationFn: api.savedJobs.unsaveJob,
    onMutate: async (jobId) => {
      // Optimistic update
      optimisticUpdates.toggleJobSave(jobId, false);
    },
    onSuccess: () => {
      invalidateQueries.savedJobs();
    },
    onError: (error, jobId) => {
      // Rollback optimistic update
      optimisticUpdates.toggleJobSave(jobId, true);
    },
  });
};

// Saved Searches hooks
export const useSavedSearches = (options?: UseQueryOptions<ApiResponse<SavedSearch[]>>) => {
  return useQuery({
    queryKey: queryKeys.savedSearches,
    queryFn: api.savedSearches.getSavedSearches,
    ...options,
  });
};

export const useCreateSavedSearch = () => {
  return useMutation({
    mutationFn: api.savedSearches.createSavedSearch,
    onSuccess: () => {
      invalidateQueries.savedSearches();
    },
  });
};

export const useUpdateSavedSearch = () => {
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<SavedSearch> }) =>
      api.savedSearches.updateSavedSearch(id, updates),
    onSuccess: () => {
      invalidateQueries.savedSearches();
    },
  });
};

export const useDeleteSavedSearch = () => {
  return useMutation({
    mutationFn: api.savedSearches.deleteSavedSearch,
    onSuccess: () => {
      invalidateQueries.savedSearches();
    },
  });
};

export const useRunSavedSearch = () => {
  return useMutation({
    mutationFn: api.savedSearches.runSavedSearch,
  });
};

// Company hooks
export const useCompany = (
  companyId: string,
  options?: UseQueryOptions<ApiResponse<{
    id: string;
    name: string;
    description: string;
    logo?: string;
    website?: string;
    size?: string;
    industry?: string;
    location?: string;
    founded?: number;
    benefits?: string[];
    culture?: string[];
  }>>
) => {
  return useQuery({
    queryKey: queryKeys.companyDetail(companyId),
    queryFn: () => api.companies.getCompany(companyId),
    enabled: !!companyId,
    ...options,
  });
};

export const useCompanyJobs = (
  companyId: string,
  params?: { page?: number; limit?: number },
  options?: UseQueryOptions<PaginatedResponse<Job>>
) => {
  return useQuery({
    queryKey: queryKeys.companyJobs(companyId, params),
    queryFn: () => api.companies.getCompanyJobs(companyId, params),
    enabled: !!companyId,
    ...options,
  });
};

export const useFollowedCompanies = (options?: UseQueryOptions<ApiResponse<Array<{
  id: string;
  name: string;
  logo?: string;
}>>>) => {
  return useQuery({
    queryKey: queryKeys.followedCompanies,
    queryFn: api.companies.getFollowedCompanies,
    ...options,
  });
};

export const useFollowCompany = () => {
  return useMutation({
    mutationFn: api.companies.followCompany,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.followedCompanies });
    },
  });
};

export const useUnfollowCompany = () => {
  return useMutation({
    mutationFn: api.companies.unfollowCompany,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.followedCompanies });
    },
  });
};

// Analytics hooks
export const useUserAnalytics = (options?: UseQueryOptions<ApiResponse<{
  totalApplications: number;
  totalJobViews: number;
  averageScore: number;
  topSkills: string[];
  applicationSuccess: number;
  weeklyActivity: Array<{ date: string; applications: number; views: number }>;
}>>) => {
  return useQuery({
    queryKey: queryKeys.userAnalytics,
    queryFn: api.analytics.getUserAnalytics,
    ...options,
  });
};

export const useJobAnalytics = (
  jobId: string,
  options?: UseQueryOptions<ApiResponse<{
    viewCount: number;
    applicationCount: number;
    averageScore: number;
    topSkills: string[];
    demographics: any;
  }>>
) => {
  return useQuery({
    queryKey: queryKeys.jobAnalytics(jobId),
    queryFn: () => api.analytics.getJobAnalytics(jobId),
    enabled: !!jobId,
    ...options,
  });
};

export const useTrackEvent = () => {
  return useMutation({
    mutationFn: api.analytics.trackEvent,
  });
};

// Notifications hooks
export const useNotifications = (
  params?: { page?: number; limit?: number; unreadOnly?: boolean },
  options?: UseQueryOptions<PaginatedResponse<{
    id: string;
    type: string;
    title: string;
    message: string;
    isRead: boolean;
    createdAt: string;
    data?: any;
  }>>
) => {
  return useQuery({
    queryKey: queryKeys.notificationsList(params),
    queryFn: () => api.notifications.getNotifications(params),
    ...options,
  });
};

export const useUnreadNotificationsCount = (options?: UseQueryOptions<ApiResponse<{ count: number }>>) => {
  return useQuery({
    queryKey: queryKeys.unreadCount,
    queryFn: api.notifications.getUnreadCount,
    refetchInterval: 30000, // Refetch every 30 seconds
    ...options,
  });
};

export const useMarkNotificationAsRead = () => {
  return useMutation({
    mutationFn: api.notifications.markAsRead,
    onMutate: async (notificationId) => {
      // Optimistic update
      optimisticUpdates.markNotificationAsRead(notificationId);
    },
    onSuccess: () => {
      invalidateQueries.notifications();
    },
  });
};

export const useMarkAllNotificationsAsRead = () => {
  return useMutation({
    mutationFn: api.notifications.markAllAsRead,
    onSuccess: () => {
      invalidateQueries.notifications();
    },
  });
};

export const useDeleteNotification = () => {
  return useMutation({
    mutationFn: api.notifications.deleteNotification,
    onSuccess: () => {
      invalidateQueries.notifications();
    },
  });
};

export const useUpdateNotificationSettings = () => {
  return useMutation({
    mutationFn: api.notifications.updateNotificationSettings,
    onSuccess: () => {
      invalidateQueries.user();
    },
  });
};

// Combined hooks for complex operations
export const useJobWithScore = (jobId: string) => {
  const jobQuery = useJob(jobId);
  const scoreQuery = useJobScore(jobId);
  const breakdownQuery = useScoreBreakdown(jobId);

  return {
    job: jobQuery.data?.data,
    score: scoreQuery.data?.data,
    breakdown: breakdownQuery.data?.data,
    isLoading: jobQuery.isLoading || scoreQuery.isLoading || breakdownQuery.isLoading,
    error: jobQuery.error || scoreQuery.error || breakdownQuery.error,
    refetch: () => {
      jobQuery.refetch();
      scoreQuery.refetch();
      breakdownQuery.refetch();
    },
  };
};

export const useJobsWithScores = (params?: JobSearchParams) => {
  const jobsQuery = useJobs(params);
  const calculateBatchScores = useBatchJobScores();

  // Calculate scores for jobs when they're loaded
  const calculateScoresForJobs = (jobIds: string[]) => {
    if (jobIds.length > 0) {
      calculateBatchScores.mutate(jobIds);
    }
  };

  return {
    jobs: jobsQuery.data?.data || [],
    pagination: jobsQuery.data?.pagination,
    isLoading: jobsQuery.isLoading,
    error: jobsQuery.error,
    refetch: jobsQuery.refetch,
    calculateScoresForJobs,
    isCalculatingScores: calculateBatchScores.isPending,
  };
};