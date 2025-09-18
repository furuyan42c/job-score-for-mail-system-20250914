// Export the main API client
export { ApiClient, apiClient } from './api-client';

// Export all types
export type {
  BatchType,
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
  ApiClientConfig,
  RequestCache,
  FileUploadOptions,
  UploadProgress,
} from './api-client';

// Export error classes
export { ApiError, ValidationError, NetworkError } from './api-client';

// Export all hooks
export {
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

  // Query keys for external usage
  queryKeys,
} from './api-hooks';

// Default export for convenience
export { default as apiHooks } from './api-hooks';