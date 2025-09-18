/**
 * API Module Index
 *
 * Central export point for all API-related functionality.
 * Provides easy access to clients, types, and utilities.
 */

// Main API client exports
export { default as ApiClient, apiClient, serverApiClient } from './client';

// Supabase client exports
export {
  default as supabase,
  createServerSupabaseClient,
  createServiceRoleClient,
  realtimeManager,
  AuthManager,
  DatabaseUtils,
} from './supabase';

// Type exports - Core entities
export type {
  Job,
  User,
  Score,
  BatchExecution,
  BatchOperationLog,
  EmailJob,
  EmailTemplate,
  SystemLog,
  SystemMetrics,
  Performance,
} from './types';

// Type exports - Master data
export type {
  PrefectureMaster,
  CityMaster,
  OccupationMaster,
  IndustryMaster,
} from './types';

// Type exports - Utility types
export type {
  Location,
  Salary,
  JobFeatures,
  UserPreferences,
  ScoringWeights,
} from './types';

// Type exports - API types
export type {
  ApiResponse,
  BatchType,
  BatchStatus,
  BatchPhase,
  JobSearchParams,
  UserSearchParams,
  ScoringParams,
  ImportJobsParams,
  ImportResult,
  EmailPreview,
  QueryResult,
  LogFilters,
  PaginationParams,
} from './types';

// Type exports - Error types
export {
  APIError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  RateLimitError,
} from './types';

// Type exports - Database schema
export type { Database } from './types';

// Re-export common Supabase types that might be useful
export type { SupabaseClient } from '@supabase/supabase-js';

/**
 * API Configuration and Utilities
 */
export const API_CONFIG = {
  // Cache TTL values (in milliseconds)
  CACHE: {
    SHORT: 30 * 1000,      // 30 seconds
    MEDIUM: 5 * 60 * 1000,  // 5 minutes
    LONG: 30 * 60 * 1000,   // 30 minutes
  },

  // Pagination defaults
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    MIN_PAGE_SIZE: 5,
  },

  // Retry configuration
  RETRY: {
    MAX_ATTEMPTS: 3,
    BASE_DELAY: 1000,
    MAX_DELAY: 10000,
  },

  // Real-time subscription settings
  REALTIME: {
    EVENTS_PER_SECOND: 10,
    RECONNECT_ATTEMPTS: 5,
  },

  // Rate limiting
  RATE_LIMITS: {
    BATCH_OPERATIONS: 5,   // per minute
    SCORING_REQUESTS: 10,  // per minute
    EMAIL_SENDS: 100,      // per hour
  },
} as const;

/**
 * Utility functions for API interactions
 */
export const apiUtils = {
  /**
   * Create standardized error response
   */
  createErrorResponse: <T = any>(
    code: string,
    message: string,
    details?: any
  ): ApiResponse<T> => ({
    success: false,
    error: {
      code,
      message,
      details,
    },
  }),

  /**
   * Create standardized success response
   */
  createSuccessResponse: <T>(
    data: T,
    meta?: any
  ): ApiResponse<T> => ({
    success: true,
    data,
    meta,
  }),

  /**
   * Format pagination metadata
   */
  formatPaginationMeta: (
    page: number,
    perPage: number,
    total: number,
    executionTime?: number
  ) => ({
    page,
    per_page: perPage,
    total,
    total_pages: Math.ceil(total / perPage),
    execution_time: executionTime,
  }),

  /**
   * Validate pagination parameters
   */
  validatePaginationParams: (params: PaginationParams) => {
    const { page = 1, per_page = API_CONFIG.PAGINATION.DEFAULT_PAGE_SIZE } = params;

    return {
      page: Math.max(1, page),
      per_page: Math.min(
        Math.max(API_CONFIG.PAGINATION.MIN_PAGE_SIZE, per_page),
        API_CONFIG.PAGINATION.MAX_PAGE_SIZE
      ),
    };
  },

  /**
   * Generate cache key from parameters
   */
  generateCacheKey: (prefix: string, params: Record<string, any>) => {
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((result, key) => {
        result[key] = params[key];
        return result;
      }, {} as Record<string, any>);

    return `${prefix}-${JSON.stringify(sortedParams)}`;
  },

  /**
   * Check if error is retryable
   */
  isRetryableError: (error: any): boolean => {
    if (error instanceof AuthenticationError ||
        error instanceof ValidationError ||
        error instanceof NotFoundError) {
      return false;
    }

    // Network errors are usually retryable
    if (error?.name === 'NetworkError' || error?.name === 'TimeoutError') {
      return true;
    }

    // 5xx server errors are retryable
    if (error?.status >= 500) {
      return true;
    }

    return false;
  },

  /**
   * Calculate exponential backoff delay
   */
  calculateBackoffDelay: (
    attempt: number,
    baseDelay: number = API_CONFIG.RETRY.BASE_DELAY,
    maxDelay: number = API_CONFIG.RETRY.MAX_DELAY
  ): number => {
    const delay = baseDelay * Math.pow(2, attempt - 1);
    return Math.min(delay, maxDelay);
  },

  /**
   * Format bytes to human readable string
   */
  formatBytes: (bytes: number, decimals: number = 2): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  },

  /**
   * Format duration in milliseconds to human readable string
   */
  formatDuration: (milliseconds: number): string => {
    if (milliseconds < 1000) {
      return `${milliseconds}ms`;
    }

    const seconds = milliseconds / 1000;
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }

    const minutes = seconds / 60;
    if (minutes < 60) {
      return `${minutes.toFixed(1)}m`;
    }

    const hours = minutes / 60;
    return `${hours.toFixed(1)}h`;
  },

  /**
   * Debounce function for API calls
   */
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout;

    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  },

  /**
   * Throttle function for API calls
   */
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean;

    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
};

/**
 * Type guards for API responses
 */
export const typeGuards = {
  isApiResponse: <T>(obj: any): obj is ApiResponse<T> => {
    return obj && typeof obj.success === 'boolean';
  },

  isErrorResponse: <T>(obj: any): obj is ApiResponse<T> & { success: false } => {
    return typeGuards.isApiResponse(obj) && !obj.success && !!obj.error;
  },

  isSuccessResponse: <T>(obj: any): obj is ApiResponse<T> & { success: true } => {
    return typeGuards.isApiResponse(obj) && obj.success && obj.data !== undefined;
  },

  isBatchExecution: (obj: any): obj is BatchExecution => {
    return obj &&
           typeof obj.batch_id === 'string' &&
           typeof obj.batch_type === 'string' &&
           typeof obj.status === 'string' &&
           typeof obj.phase === 'string';
  },

  isJob: (obj: any): obj is Job => {
    return obj &&
           typeof obj.job_id === 'number' &&
           typeof obj.title === 'string' &&
           typeof obj.company_name === 'string';
  },

  isUser: (obj: any): obj is User => {
    return obj &&
           typeof obj.user_id === 'number' &&
           typeof obj.email === 'string';
  },
};

/**
 * Environment-specific configurations
 */
export const getApiConfig = () => {
  const isDev = process.env.NODE_ENV === 'development';
  const isProd = process.env.NODE_ENV === 'production';

  return {
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
    enableLogging: isDev,
    enableCaching: true,
    enableRetries: true,
    enableRealtime: true,
    strictMode: isProd,
    rateLimitEnabled: isProd,

    // Development-specific settings
    ...(isDev && {
      cacheTimeout: API_CONFIG.CACHE.SHORT,
      retryAttempts: 1,
      logLevel: 'debug',
    }),

    // Production-specific settings
    ...(isProd && {
      cacheTimeout: API_CONFIG.CACHE.MEDIUM,
      retryAttempts: API_CONFIG.RETRY.MAX_ATTEMPTS,
      logLevel: 'warn',
    }),
  };
};