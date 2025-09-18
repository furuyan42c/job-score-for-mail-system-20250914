import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  CancelTokenSource,
} from 'axios';
import { z } from 'zod';
import {
  Job,
  JobMatch,
  User,
  UserProfile,
  JobSearchParams,
  PaginatedResponse,
  ApiResponse,
} from '../types';

// ====================
// ZOD VALIDATION SCHEMAS
// ====================

// Core response schemas
const ApiResponseSchema = z.object({
  data: z.any(),
  message: z.string().optional(),
  success: z.boolean(),
  timestamp: z.string(),
});

const PaginatedResponseSchema = z.object({
  data: z.array(z.any()),
  pagination: z.object({
    page: z.number(),
    limit: z.number(),
    total: z.number(),
    pages: z.number(),
  }),
  success: z.boolean(),
  timestamp: z.string(),
});

// Batch operation schemas
const BatchJobSchema = z.object({
  id: z.string(),
  type: z.enum(['scoring', 'matching', 'email_generation', 'import']),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  progress: z.number().min(0).max(100),
  totalItems: z.number(),
  processedItems: z.number(),
  createdAt: z.string(),
  startedAt: z.string().optional(),
  completedAt: z.string().optional(),
  errorMessage: z.string().optional(),
  result: z.any().optional(),
});

const BatchStatusSchema = z.object({
  id: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  progress: z.number(),
  totalItems: z.number(),
  processedItems: z.number(),
  errorMessage: z.string().optional(),
  result: z.any().optional(),
  updatedAt: z.string(),
});

// Import/Export schemas
const ImportResultSchema = z.object({
  jobId: z.string(),
  totalRecords: z.number(),
  importedRecords: z.number(),
  failedRecords: z.number(),
  errors: z.array(z.object({
    row: z.number(),
    error: z.string(),
  })),
  warnings: z.array(z.string()),
});

// Score calculation schemas
const ScoreSchema = z.object({
  userId: z.string(),
  jobId: z.string(),
  overallScore: z.number().min(0).max(100),
  factors: z.array(z.object({
    type: z.enum(['skills', 'experience', 'salary', 'location', 'preferences']),
    weight: z.number(),
    score: z.number(),
    description: z.string(),
  })),
  calculatedAt: z.string(),
  version: z.string(),
});

const BatchScoreResultSchema = z.object({
  batchId: z.string(),
  totalUsers: z.number(),
  processedUsers: z.number(),
  scores: z.array(ScoreSchema),
  errors: z.array(z.object({
    userId: z.string(),
    error: z.string(),
  })),
});

// Matching schemas
const MatchingResultSchema = z.object({
  userId: z.string(),
  totalJobs: z.number(),
  matchedJobs: z.number(),
  matches: z.array(z.object({
    jobId: z.string(),
    score: z.number(),
    rank: z.number(),
    factors: z.array(z.object({
      type: z.string(),
      weight: z.number(),
      score: z.number(),
      description: z.string(),
    })),
  })),
  generatedAt: z.string(),
});

const UserMatchesSchema = z.object({
  userId: z.string(),
  matches: z.array(z.object({
    id: z.string(),
    jobId: z.string(),
    score: z.number(),
    rank: z.number(),
    status: z.enum(['new', 'viewed', 'interested', 'not-interested', 'applied']),
    createdAt: z.string(),
    updatedAt: z.string(),
  })),
  totalMatches: z.number(),
  lastUpdated: z.string(),
});

// Email schemas
const EmailPreviewSchema = z.object({
  userId: z.string(),
  subject: z.string(),
  htmlContent: z.string(),
  textContent: z.string(),
  matches: z.array(z.object({
    jobId: z.string(),
    jobTitle: z.string(),
    company: z.string(),
    score: z.number(),
  })),
  generatedAt: z.string(),
});

// SQL execution schemas
const QueryResultSchema = z.object({
  columns: z.array(z.string()),
  rows: z.array(z.array(z.any())),
  rowCount: z.number(),
  executionTime: z.number(),
  query: z.string(),
  executedAt: z.string(),
});

const QueryHistorySchema = z.object({
  id: z.string(),
  query: z.string(),
  executionTime: z.number(),
  rowCount: z.number(),
  status: z.enum(['success', 'error']),
  errorMessage: z.string().optional(),
  executedAt: z.string(),
  userId: z.string(),
});

// Monitoring schemas
const SystemMetricsSchema = z.object({
  cpu: z.object({
    usage: z.number(),
    cores: z.number(),
  }),
  memory: z.object({
    used: z.number(),
    total: z.number(),
    percentage: z.number(),
  }),
  database: z.object({
    activeConnections: z.number(),
    totalQueries: z.number(),
    avgResponseTime: z.number(),
  }),
  api: z.object({
    requestsPerMinute: z.number(),
    avgResponseTime: z.number(),
    errorRate: z.number(),
  }),
  background: z.object({
    activeJobs: z.number(),
    queuedJobs: z.number(),
    failedJobs: z.number(),
  }),
  timestamp: z.string(),
});

const HealthStatusSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  checks: z.object({
    database: z.object({
      status: z.enum(['healthy', 'unhealthy']),
      responseTime: z.number(),
      lastCheck: z.string(),
    }),
    redis: z.object({
      status: z.enum(['healthy', 'unhealthy']),
      responseTime: z.number(),
      lastCheck: z.string(),
    }),
    external_apis: z.object({
      status: z.enum(['healthy', 'unhealthy']),
      services: z.array(z.object({
        name: z.string(),
        status: z.enum(['healthy', 'unhealthy']),
        responseTime: z.number(),
      })),
      lastCheck: z.string(),
    }),
  }),
  timestamp: z.string(),
});

// ====================
// TYPE DEFINITIONS
// ====================

export type BatchType = z.infer<typeof BatchJobSchema>['type'];
export type BatchJob = z.infer<typeof BatchJobSchema>;
export type BatchStatus = z.infer<typeof BatchStatusSchema>;
export type ImportResult = z.infer<typeof ImportResultSchema>;
export type Score = z.infer<typeof ScoreSchema>;
export type BatchScoreResult = z.infer<typeof BatchScoreResultSchema>;
export type MatchingResult = z.infer<typeof MatchingResultSchema>;
export type UserMatches = z.infer<typeof UserMatchesSchema>;
export type EmailPreview = z.infer<typeof EmailPreviewSchema>;
export type QueryResult = z.infer<typeof QueryResultSchema>;
export type QueryHistory = z.infer<typeof QueryHistorySchema>;
export type SystemMetrics = z.infer<typeof SystemMetricsSchema>;
export type HealthStatus = z.infer<typeof HealthStatusSchema>;

export interface JobFilters {
  title?: string;
  company?: string;
  location?: string;
  skills?: string[];
  experienceLevel?: string[];
  salary?: { min?: number; max?: number };
  jobType?: string[];
  locationType?: string[];
  postedWithin?: number; // days
}

export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface PaginatedJobs {
  jobs: Job[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// ====================
// API CLIENT CONFIGURATION
// ====================

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableLogging?: boolean;
  enableCaching?: boolean;
  cacheTimeout?: number; // milliseconds
}

export interface RequestCache {
  [key: string]: {
    data: any;
    timestamp: number;
    expiresAt: number;
  };
}

export interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  timeout?: number;
  maxSize?: number; // bytes
  allowedTypes?: string[];
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// ====================
// ERROR HANDLING
// ====================

export class ApiError extends Error {
  public status: number;
  public data: any;
  public timestamp: string;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.timestamp = new Date().toISOString();
  }
}

export class ValidationError extends Error {
  public errors: z.ZodError;

  constructor(message: string, errors: z.ZodError) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

export class NetworkError extends Error {
  public code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = 'NetworkError';
    this.code = code;
  }
}

// ====================
// UTILITY FUNCTIONS
// ====================

class RequestDebouncer {
  private timeouts: Map<string, NodeJS.Timeout> = new Map();

  public debounce<T extends (...args: any[]) => Promise<any>>(
    key: string,
    fn: T,
    delay: number = 300
  ): T {
    return ((...args: any[]) => {
      return new Promise((resolve, reject) => {
        // Clear existing timeout
        const existingTimeout = this.timeouts.get(key);
        if (existingTimeout) {
          clearTimeout(existingTimeout);
        }

        // Set new timeout
        const timeout = setTimeout(async () => {
          try {
            const result = await fn(...args);
            resolve(result);
          } catch (error) {
            reject(error);
          } finally {
            this.timeouts.delete(key);
          }
        }, delay);

        this.timeouts.set(key, timeout);
      });
    }) as T;
  }

  public clear(key?: string): void {
    if (key) {
      const timeout = this.timeouts.get(key);
      if (timeout) {
        clearTimeout(timeout);
        this.timeouts.delete(key);
      }
    } else {
      this.timeouts.forEach(timeout => clearTimeout(timeout));
      this.timeouts.clear();
    }
  }
}

class ResponseCache {
  private cache: RequestCache = {};
  private defaultTimeout: number;

  constructor(defaultTimeout: number = 5 * 60 * 1000) { // 5 minutes
    this.defaultTimeout = defaultTimeout;
  }

  public get(key: string): any | null {
    const cached = this.cache[key];
    if (!cached) return null;

    if (Date.now() > cached.expiresAt) {
      delete this.cache[key];
      return null;
    }

    return cached.data;
  }

  public set(key: string, data: any, timeout?: number): void {
    const expiresAt = Date.now() + (timeout || this.defaultTimeout);
    this.cache[key] = {
      data,
      timestamp: Date.now(),
      expiresAt,
    };
  }

  public delete(key: string): void {
    delete this.cache[key];
  }

  public clear(): void {
    this.cache = {};
  }

  public cleanup(): void {
    const now = Date.now();
    Object.keys(this.cache).forEach(key => {
      if (now > this.cache[key].expiresAt) {
        delete this.cache[key];
      }
    });
  }
}

// ====================
// MAIN API CLIENT CLASS
// ====================

export class ApiClient {
  private instance: AxiosInstance;
  private config: ApiClientConfig;
  private cache: ResponseCache;
  private debouncer: RequestDebouncer;
  private cancelTokens: Map<string, CancelTokenSource> = new Map();

  constructor(config: ApiClientConfig) {
    this.config = {
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000,
      enableLogging: process.env.NODE_ENV === 'development',
      enableCaching: true,
      cacheTimeout: 5 * 60 * 1000,
      ...config,
    };

    this.cache = new ResponseCache(this.config.cacheTimeout);
    this.debouncer = new RequestDebouncer();

    this.instance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.startCacheCleanup();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add authentication header if token exists
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracking
        config.metadata = {
          requestId: Math.random().toString(36).substring(7),
          startTime: Date.now(),
        };

        if (this.config.enableLogging) {
          console.log(`🚀 API Request [${config.metadata.requestId}]:`, {
            method: config.method?.toUpperCase(),
            url: config.url,
            params: config.params,
            data: config.data,
          });
        }

        return config;
      },
      (error) => {
        if (this.config.enableLogging) {
          console.error('❌ Request Error:', error);
        }
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => {
        const duration = Date.now() - response.config.metadata?.startTime;

        if (this.config.enableLogging) {
          console.log(`✅ API Response [${response.config.metadata?.requestId}]:`, {
            status: response.status,
            duration: `${duration}ms`,
            url: response.config.url,
            data: response.data,
          });
        }

        return response;
      },
      async (error: AxiosError) => {
        const duration = Date.now() - (error.config?.metadata?.startTime || Date.now());

        if (this.config.enableLogging) {
          console.error(`❌ API Error [${error.config?.metadata?.requestId}]:`, {
            status: error.response?.status,
            duration: `${duration}ms`,
            url: error.config?.url,
            message: error.message,
            data: error.response?.data,
          });
        }

        // Handle specific error cases
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          return Promise.reject(new ApiError('Unauthorized', 401, error.response.data));
        }

        if (error.response?.status === 403) {
          return Promise.reject(new ApiError('Forbidden', 403, error.response.data));
        }

        if (error.response?.status >= 500) {
          return Promise.reject(new ApiError('Server Error', error.response.status, error.response.data));
        }

        if (error.code === 'ECONNABORTED') {
          return Promise.reject(new NetworkError('Request timeout', 'TIMEOUT'));
        }

        if (error.code === 'NETWORK_ERROR') {
          return Promise.reject(new NetworkError('Network error', 'NETWORK'));
        }

        return Promise.reject(new ApiError(
          error.response?.data?.message || error.message,
          error.response?.status || 500,
          error.response?.data
        ));
      }
    );
  }

  private startCacheCleanup(): void {
    // Cleanup expired cache entries every 10 minutes
    setInterval(() => {
      this.cache.cleanup();
    }, 10 * 60 * 1000);
  }

  private getCacheKey(method: string, url: string, params?: any): string {
    return `${method}:${url}:${JSON.stringify(params || {})}`;
  }

  private async request<T>(
    config: AxiosRequestConfig,
    options: {
      validate?: z.ZodSchema<T>;
      cache?: boolean;
      cacheTimeout?: number;
      retryAttempts?: number;
    } = {}
  ): Promise<T> {
    const {
      validate,
      cache = this.config.enableCaching,
      cacheTimeout = this.config.cacheTimeout,
      retryAttempts = this.config.retryAttempts,
    } = options;

    // Check cache first
    const cacheKey = this.getCacheKey(config.method || 'GET', config.url || '', config.params);
    if (cache && config.method === 'GET') {
      const cached = this.cache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }

    let lastError: Error;
    for (let attempt = 0; attempt <= retryAttempts!; attempt++) {
      try {
        const response: AxiosResponse<T> = await this.instance.request(config);

        // Validate response if schema provided
        if (validate) {
          try {
            const validatedData = validate.parse(response.data);

            // Cache successful GET requests
            if (cache && config.method === 'GET') {
              this.cache.set(cacheKey, validatedData, cacheTimeout);
            }

            return validatedData;
          } catch (validationError) {
            throw new ValidationError('Response validation failed', validationError as z.ZodError);
          }
        }

        // Cache successful GET requests
        if (cache && config.method === 'GET') {
          this.cache.set(cacheKey, response.data, cacheTimeout);
        }

        return response.data;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx) or validation errors
        if (error instanceof ApiError && error.status < 500) {
          throw error;
        }
        if (error instanceof ValidationError) {
          throw error;
        }

        // Wait before retry
        if (attempt < retryAttempts!) {
          await new Promise(resolve => setTimeout(resolve, this.config.retryDelay! * (attempt + 1)));
        }
      }
    }

    throw lastError!;
  }

  // ====================
  // CANCEL REQUESTS
  // ====================

  public cancelRequest(key: string): void {
    const source = this.cancelTokens.get(key);
    if (source) {
      source.cancel('Request cancelled by user');
      this.cancelTokens.delete(key);
    }
  }

  public cancelAllRequests(): void {
    this.cancelTokens.forEach((source, key) => {
      source.cancel('All requests cancelled');
    });
    this.cancelTokens.clear();
  }

  // ====================
  // BATCH OPERATIONS
  // ====================

  public async triggerBatch(type: BatchType): Promise<BatchJob> {
    return this.request<BatchJob>({
      method: 'POST',
      url: '/api/batch/trigger',
      data: { type },
    }, {
      validate: ApiResponseSchema.transform(res => BatchJobSchema.parse(res.data)),
    });
  }

  public async getBatchStatus(id: string): Promise<BatchStatus> {
    return this.request<BatchStatus>({
      method: 'GET',
      url: `/api/batch/${id}/status`,
    }, {
      validate: ApiResponseSchema.transform(res => BatchStatusSchema.parse(res.data)),
    });
  }

  public async cancelBatch(id: string): Promise<void> {
    await this.request({
      method: 'POST',
      url: `/api/batch/${id}/cancel`,
    });
  }

  public async getBatchHistory(params?: PaginationParams): Promise<PaginatedResponse<BatchJob>> {
    return this.request<PaginatedResponse<BatchJob>>({
      method: 'GET',
      url: '/api/batch/history',
      params,
    }, {
      validate: PaginatedResponseSchema,
    });
  }

  // ====================
  // JOB OPERATIONS
  // ====================

  public async importJobs(file: File, options?: FileUploadOptions): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    const source = axios.CancelToken.source();
    const requestKey = `import-jobs-${Date.now()}`;
    this.cancelTokens.set(requestKey, source);

    try {
      const response = await this.instance.post<ApiResponse<ImportResult>>('/api/jobs/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: options?.timeout || 60000, // 1 minute for file uploads
        cancelToken: source.token,
        onUploadProgress: (progressEvent) => {
          if (options?.onProgress && progressEvent.total) {
            const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            options.onProgress(percentage);
          }
        },
      });

      const validatedData = ImportResultSchema.parse(response.data.data);
      return validatedData;
    } finally {
      this.cancelTokens.delete(requestKey);
    }
  }

  public async searchJobs(filters: JobFilters & PaginationParams): Promise<PaginatedJobs> {
    // Debounce search requests
    const debouncedSearch = this.debouncer.debounce(
      'search-jobs',
      (searchFilters: JobFilters & PaginationParams) =>
        this.request<PaginatedJobs>({
          method: 'GET',
          url: '/api/jobs/search',
          params: searchFilters,
        }, {
          cache: true,
          cacheTimeout: 2 * 60 * 1000, // 2 minutes for search results
        }),
      300
    );

    return debouncedSearch(filters);
  }

  public async getJobById(id: string): Promise<Job> {
    return this.request<Job>({
      method: 'GET',
      url: `/api/jobs/${id}`,
    }, {
      cache: true,
    });
  }

  public async exportJobs(filters?: JobFilters): Promise<Blob> {
    const response = await this.instance.get('/api/jobs/export', {
      params: filters,
      responseType: 'blob',
    });

    return response.data;
  }

  // ====================
  // SCORING OPERATIONS
  // ====================

  public async calculateScore(userId: string, jobId: string): Promise<Score> {
    return this.request<Score>({
      method: 'POST',
      url: '/api/scores/calculate',
      data: { userId, jobId },
    }, {
      validate: ApiResponseSchema.transform(res => ScoreSchema.parse(res.data)),
    });
  }

  public async batchCalculateScores(userIds: string[], jobId?: string): Promise<BatchScoreResult> {
    return this.request<BatchScoreResult>({
      method: 'POST',
      url: '/api/scores/batch-calculate',
      data: { userIds, jobId },
    }, {
      validate: ApiResponseSchema.transform(res => BatchScoreResultSchema.parse(res.data)),
    });
  }

  public async getScoreHistory(userId: string, params?: PaginationParams): Promise<PaginatedResponse<Score>> {
    return this.request<PaginatedResponse<Score>>({
      method: 'GET',
      url: `/api/scores/history/${userId}`,
      params,
    }, {
      validate: PaginatedResponseSchema,
      cache: true,
    });
  }

  // ====================
  // MATCHING OPERATIONS
  // ====================

  public async generateMatching(userId: string, options?: { forceRefresh?: boolean }): Promise<MatchingResult> {
    return this.request<MatchingResult>({
      method: 'POST',
      url: '/api/matching/generate',
      data: { userId, ...options },
    }, {
      validate: ApiResponseSchema.transform(res => MatchingResultSchema.parse(res.data)),
    });
  }

  public async getUserMatches(userId: string, params?: PaginationParams): Promise<UserMatches> {
    return this.request<UserMatches>({
      method: 'GET',
      url: `/api/matching/user/${userId}`,
      params,
    }, {
      validate: ApiResponseSchema.transform(res => UserMatchesSchema.parse(res.data)),
      cache: true,
    });
  }

  public async updateMatchStatus(matchId: string, status: 'viewed' | 'interested' | 'not-interested' | 'applied'): Promise<void> {
    await this.request({
      method: 'PATCH',
      url: `/api/matching/${matchId}/status`,
      data: { status },
    });

    // Clear related cache entries
    this.cache.clear();
  }

  public async getMatchingStats(userId: string): Promise<any> {
    return this.request({
      method: 'GET',
      url: `/api/matching/stats/${userId}`,
    }, {
      cache: true,
      cacheTimeout: 10 * 60 * 1000, // 10 minutes
    });
  }

  // ====================
  // EMAIL OPERATIONS
  // ====================

  public async generateEmail(userId: string, options?: { includeMatches?: number }): Promise<EmailPreview> {
    return this.request<EmailPreview>({
      method: 'POST',
      url: '/api/email/generate',
      data: { userId, ...options },
    }, {
      validate: ApiResponseSchema.transform(res => EmailPreviewSchema.parse(res.data)),
    });
  }

  public async sendTestEmail(userId: string, emailData?: Partial<EmailPreview>): Promise<void> {
    await this.request({
      method: 'POST',
      url: '/api/email/send-test',
      data: { userId, ...emailData },
    });
  }

  public async scheduleEmailCampaign(userIds: string[], options?: any): Promise<BatchJob> {
    return this.request<BatchJob>({
      method: 'POST',
      url: '/api/email/schedule-campaign',
      data: { userIds, ...options },
    }, {
      validate: ApiResponseSchema.transform(res => BatchJobSchema.parse(res.data)),
    });
  }

  public async getEmailTemplates(): Promise<any[]> {
    return this.request({
      method: 'GET',
      url: '/api/email/templates',
    }, {
      cache: true,
      cacheTimeout: 30 * 60 * 1000, // 30 minutes
    });
  }

  // ====================
  // SQL OPERATIONS
  // ====================

  public async executeQuery(query: string, params?: any[]): Promise<QueryResult> {
    return this.request<QueryResult>({
      method: 'POST',
      url: '/api/sql/execute',
      data: { query, params },
    }, {
      validate: ApiResponseSchema.transform(res => QueryResultSchema.parse(res.data)),
    });
  }

  public async getQueryHistory(params?: PaginationParams): Promise<PaginatedResponse<QueryHistory>> {
    return this.request<PaginatedResponse<QueryHistory>>({
      method: 'GET',
      url: '/api/sql/history',
      params,
    }, {
      validate: PaginatedResponseSchema,
      cache: true,
    });
  }

  public async saveQuery(name: string, query: string, description?: string): Promise<void> {
    await this.request({
      method: 'POST',
      url: '/api/sql/save',
      data: { name, query, description },
    });
  }

  public async getSavedQueries(): Promise<any[]> {
    return this.request({
      method: 'GET',
      url: '/api/sql/saved',
    }, {
      cache: true,
    });
  }

  // ====================
  // MONITORING OPERATIONS
  // ====================

  public async getMetrics(timeRange?: '1h' | '24h' | '7d' | '30d'): Promise<SystemMetrics> {
    return this.request<SystemMetrics>({
      method: 'GET',
      url: '/api/monitoring/metrics',
      params: { timeRange },
    }, {
      validate: ApiResponseSchema.transform(res => SystemMetricsSchema.parse(res.data)),
      cache: true,
      cacheTimeout: 30 * 1000, // 30 seconds for metrics
    });
  }

  public async getHealthCheck(): Promise<HealthStatus> {
    return this.request<HealthStatus>({
      method: 'GET',
      url: '/api/health',
    }, {
      validate: ApiResponseSchema.transform(res => HealthStatusSchema.parse(res.data)),
      cache: false, // Never cache health checks
    });
  }

  public async getSystemLogs(params?: PaginationParams & { level?: string; service?: string }): Promise<PaginatedResponse<any>> {
    return this.request<PaginatedResponse<any>>({
      method: 'GET',
      url: '/api/monitoring/logs',
      params,
    }, {
      validate: PaginatedResponseSchema,
      cache: true,
      cacheTimeout: 1 * 60 * 1000, // 1 minute
    });
  }

  // ====================
  // USER OPERATIONS
  // ====================

  public async getUsers(params?: PaginationParams & { search?: string }): Promise<PaginatedResponse<User>> {
    return this.request<PaginatedResponse<User>>({
      method: 'GET',
      url: '/api/users',
      params,
    }, {
      validate: PaginatedResponseSchema,
      cache: true,
    });
  }

  public async getUserById(id: string): Promise<User> {
    return this.request<User>({
      method: 'GET',
      url: `/api/users/${id}`,
    }, {
      cache: true,
    });
  }

  public async getUserProfile(id: string): Promise<UserProfile> {
    return this.request<UserProfile>({
      method: 'GET',
      url: `/api/users/${id}/profile`,
    }, {
      cache: true,
    });
  }

  public async updateUserProfile(id: string, profile: Partial<UserProfile>): Promise<UserProfile> {
    const result = await this.request<UserProfile>({
      method: 'PATCH',
      url: `/api/users/${id}/profile`,
      data: profile,
    });

    // Clear user-related cache
    this.cache.delete(`GET:/api/users/${id}:{}}`);
    this.cache.delete(`GET:/api/users/${id}/profile:{}}`);

    return result;
  }

  // ====================
  // UTILITY METHODS
  // ====================

  public clearCache(pattern?: string): void {
    if (pattern) {
      // Clear cache entries matching pattern
      Object.keys(this.cache).forEach(key => {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      });
    } else {
      this.cache.clear();
    }
  }

  public getConfig(): ApiClientConfig {
    return { ...this.config };
  }

  public updateConfig(updates: Partial<ApiClientConfig>): void {
    this.config = { ...this.config, ...updates };

    // Update axios instance if needed
    if (updates.baseURL) {
      this.instance.defaults.baseURL = updates.baseURL;
    }
    if (updates.timeout) {
      this.instance.defaults.timeout = updates.timeout;
    }
  }

  public destroy(): void {
    this.cancelAllRequests();
    this.debouncer.clear();
    this.cache.clear();
  }
}

// ====================
// DEFAULT CLIENT INSTANCE
// ====================

const defaultConfig: ApiClientConfig = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableLogging: process.env.NODE_ENV === 'development',
  enableCaching: true,
  cacheTimeout: 5 * 60 * 1000,
};

export const apiClient = new ApiClient(defaultConfig);

// Export for easier testing
export default apiClient;