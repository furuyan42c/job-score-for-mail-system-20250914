/**
 * API Client Implementation
 *
 * Comprehensive API client for the job matching system with methods for
 * batch operations, job management, scoring, monitoring, and email operations.
 * Includes error handling, retry logic, caching, and real-time updates.
 */

import { supabase, createServerSupabaseClient, realtimeManager } from './supabase';
import {
  ApiResponse,
  Job,
  User,
  Score,
  BatchExecution,
  BatchType,
  BatchStatus,
  ScoringParams,
  ScoringCalculationResult,
  ImportJobsParams,
  ImportResult,
  JobSearchParams,
  UserSearchParams,
  QueryResult,
  SystemMetrics,
  SystemLog,
  LogFilters,
  EmailPreview,
  EmailJob,
  APIError,
  ValidationError,
  AuthenticationError,
  NotFoundError,
  RateLimitError,
  PaginationParams,
} from './types';

/**
 * Cache configuration and management
 */
interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class CacheManager {
  private cache = new Map<string, CacheItem<any>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  set<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  get<T>(key: string): T | null {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  invalidate(pattern?: string): void {
    if (pattern) {
      const regex = new RegExp(pattern);
      for (const key of this.cache.keys()) {
        if (regex.test(key)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }

  clear(): void {
    this.cache.clear();
  }
}

/**
 * Retry configuration
 */
interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
};

/**
 * Main API Client Class
 */
export class ApiClient {
  private cache = new CacheManager();
  private isServer: boolean;

  constructor(isServer = false) {
    this.isServer = isServer;
  }

  /**
   * Get the appropriate Supabase client
   */
  private getSupabaseClient() {
    return this.isServer ? createServerSupabaseClient() : supabase;
  }

  /**
   * Utility method for retry logic with exponential backoff
   */
  private async withRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {}
  ): Promise<T> {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
    let lastError: Error;

    for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        // Don't retry certain errors
        if (error instanceof AuthenticationError ||
            error instanceof ValidationError ||
            error instanceof NotFoundError) {
          throw error;
        }

        if (attempt === retryConfig.maxAttempts) {
          break;
        }

        const delay = Math.min(
          retryConfig.baseDelay * Math.pow(retryConfig.backoffMultiplier, attempt - 1),
          retryConfig.maxDelay
        );

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }

  /**
   * Standardized error handling
   */
  private handleError(error: any): never {
    if (error instanceof APIError) {
      throw error;
    }

    // Supabase error handling
    if (error?.code) {
      switch (error.code) {
        case 'PGRST301':
          throw new AuthenticationError('Invalid credentials');
        case 'PGRST116':
          throw new NotFoundError('Resource');
        case '23505':
          throw new ValidationError('Duplicate entry', error.details);
        case '23503':
          throw new ValidationError('Foreign key constraint violation', error.details);
        case '23514':
          throw new ValidationError('Check constraint violation', error.details);
        default:
          throw new APIError(error.code, error.message || 'Database error', 500, error);
      }
    }

    // Network errors
    if (error?.name === 'AbortError') {
      throw new APIError('REQUEST_TIMEOUT', 'Request timeout', 408);
    }

    if (error?.name === 'NetworkError') {
      throw new APIError('NETWORK_ERROR', 'Network error', 503);
    }

    // Generic error
    throw new APIError(
      'UNKNOWN_ERROR',
      error?.message || 'An unexpected error occurred',
      500,
      error
    );
  }

  // =====================================================================================
  // BATCH OPERATIONS
  // =====================================================================================

  /**
   * Trigger a new batch execution
   */
  async triggerBatch(
    type: BatchType,
    config?: Record<string, any>
  ): Promise<BatchExecution> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('batch_executions')
        .insert({
          batch_type: type,
          status: 'pending' as BatchStatus,
          phase: 'import',
          progress_percentage: 0,
          config: config || {},
        })
        .select()
        .single();

      if (error) {
        this.handleError(error);
      }

      // Subscribe to batch updates
      realtimeManager.subscribeToBatchStatus(data.batch_id, (payload) => {
        this.cache.invalidate(`batch-${data.batch_id}`);
      });

      return data;
    });
  }

  /**
   * Get batch execution status
   */
  async getBatchStatus(batchId: string): Promise<BatchExecution> {
    const cacheKey = `batch-${batchId}`;
    const cached = this.cache.get<BatchExecution>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('batch_executions')
        .select('*')
        .eq('batch_id', batchId)
        .single();

      if (error) {
        this.handleError(error);
      }

      // Cache for 30 seconds for completed/failed batches, 5 seconds for running
      const ttl = ['completed', 'failed', 'cancelled'].includes(data.status)
        ? 30000
        : 5000;

      this.cache.set(cacheKey, data, ttl);
      return data;
    });
  }

  /**
   * Cancel a running batch
   */
  async cancelBatch(batchId: string): Promise<void> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { error } = await client
        .from('batch_executions')
        .update({
          status: 'cancelled' as BatchStatus,
          completed_at: new Date().toISOString(),
        })
        .eq('batch_id', batchId)
        .in('status', ['pending', 'running']);

      if (error) {
        this.handleError(error);
      }

      this.cache.invalidate(`batch-${batchId}`);
    });
  }

  /**
   * Get all batch executions with pagination
   */
  async getBatchExecutions(params: PaginationParams = {}): Promise<ApiResponse<BatchExecution[]>> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();
      const { page = 1, per_page = 20, sort_by = 'created_at', sort_order = 'desc' } = params;

      let query = client
        .from('batch_executions')
        .select('*', { count: 'exact' })
        .order(sort_by, { ascending: sort_order === 'asc' })
        .range((page - 1) * per_page, page * per_page - 1);

      const { data, error, count } = await query;

      if (error) {
        this.handleError(error);
      }

      return {
        success: true,
        data: data || [],
        meta: {
          page,
          per_page,
          total: count || 0,
          total_pages: Math.ceil((count || 0) / per_page),
        },
      };
    });
  }

  // =====================================================================================
  // JOB OPERATIONS
  // =====================================================================================

  /**
   * Import jobs from CSV file
   */
  async importJobs(params: ImportJobsParams): Promise<ImportResult> {
    return this.withRetry(async () => {
      const formData = new FormData();
      formData.append('file', params.file);
      formData.append('batch_size', (params.batch_size || 1000).toString());
      formData.append('validate_only', (params.validate_only || false).toString());
      formData.append('update_existing', (params.update_existing || false).toString());

      const response = await fetch('/api/jobs/import', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.code || 'IMPORT_ERROR',
          errorData.message || `Import failed: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    });
  }

  /**
   * Search jobs with filters and pagination
   */
  async searchJobs(params: JobSearchParams): Promise<ApiResponse<Job[]>> {
    const cacheKey = `jobs-search-${JSON.stringify(params)}`;
    const cached = this.cache.get<ApiResponse<Job[]>>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();
      const { page = 1, per_page = 20, sort_by = 'created_at', sort_order = 'desc' } = params;

      let query = client
        .from('jobs')
        .select('*', { count: 'exact' })
        .order(sort_by, { ascending: sort_order === 'asc' });

      // Apply filters
      if (params.title) {
        query = query.ilike('title', `%${params.title}%`);
      }
      if (params.company) {
        query = query.ilike('company_name', `%${params.company}%`);
      }
      if (params.location?.pref_cd) {
        query = query.eq('location->>pref_cd', params.location.pref_cd);
      }
      if (params.location?.city_cd) {
        query = query.eq('location->>city_cd', params.location.city_cd);
      }
      if (params.salary?.min_amount) {
        query = query.gte('salary->>min_amount', params.salary.min_amount);
      }
      if (params.salary?.max_amount) {
        query = query.lte('salary->>max_amount', params.salary.max_amount);
      }
      if (params.employment_types?.length) {
        query = query.in('employment_type', params.employment_types);
      }
      if (params.occupation_codes?.length) {
        query = query.in('occupation_cd', params.occupation_codes);
      }
      if (params.industry_codes?.length) {
        query = query.in('industry_cd', params.industry_codes);
      }
      if (params.remote_work !== undefined) {
        query = query.eq('features->>remote_work_available', params.remote_work);
      }
      if (params.posted_after) {
        query = query.gte('posted_date', params.posted_after);
      }
      if (params.is_active !== undefined) {
        query = query.eq('is_active', params.is_active);
      }

      query = query.range((page - 1) * per_page, page * per_page - 1);

      const { data, error, count } = await query;

      if (error) {
        this.handleError(error);
      }

      const result = {
        success: true,
        data: data || [],
        meta: {
          page,
          per_page,
          total: count || 0,
          total_pages: Math.ceil((count || 0) / per_page),
        },
      };

      this.cache.set(cacheKey, result, 60000); // Cache for 1 minute
      return result;
    });
  }

  /**
   * Get job by ID
   */
  async getJobById(jobId: number): Promise<Job> {
    const cacheKey = `job-${jobId}`;
    const cached = this.cache.get<Job>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('jobs')
        .select('*')
        .eq('job_id', jobId)
        .single();

      if (error) {
        this.handleError(error);
      }

      this.cache.set(cacheKey, data, 300000); // Cache for 5 minutes
      return data;
    });
  }

  /**
   * Update job
   */
  async updateJob(jobId: number, updates: Partial<Job>): Promise<Job> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('jobs')
        .update({
          ...updates,
          updated_at: new Date().toISOString(),
        })
        .eq('job_id', jobId)
        .select()
        .single();

      if (error) {
        this.handleError(error);
      }

      this.cache.invalidate(`job-${jobId}`);
      this.cache.invalidate('jobs-search');
      return data;
    });
  }

  /**
   * Delete job (soft delete)
   */
  async deleteJob(jobId: number): Promise<void> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { error } = await client
        .from('jobs')
        .update({
          is_active: false,
          updated_at: new Date().toISOString(),
        })
        .eq('job_id', jobId);

      if (error) {
        this.handleError(error);
      }

      this.cache.invalidate(`job-${jobId}`);
      this.cache.invalidate('jobs-search');
    });
  }

  // =====================================================================================
  // USER OPERATIONS
  // =====================================================================================

  /**
   * Search users with filters and pagination
   */
  async searchUsers(params: UserSearchParams): Promise<ApiResponse<User[]>> {
    const cacheKey = `users-search-${JSON.stringify(params)}`;
    const cached = this.cache.get<ApiResponse<User[]>>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();
      const { page = 1, per_page = 20, sort_by = 'created_at', sort_order = 'desc' } = params;

      let query = client
        .from('users')
        .select('*', { count: 'exact' })
        .order(sort_by, { ascending: sort_order === 'asc' });

      // Apply filters
      if (params.email) {
        query = query.ilike('email', `%${params.email}%`);
      }
      if (params.name) {
        query = query.or(`first_name.ilike.%${params.name}%,last_name.ilike.%${params.name}%`);
      }
      if (params.age_range?.min) {
        query = query.gte('age', params.age_range.min);
      }
      if (params.age_range?.max) {
        query = query.lte('age', params.age_range.max);
      }
      if (params.location?.pref_cd) {
        query = query.eq('current_location->>pref_cd', params.location.pref_cd);
      }
      if (params.skills?.length) {
        query = query.contains('skills', params.skills);
      }
      if (params.experience_years?.min) {
        query = query.gte('experience_years', params.experience_years.min);
      }
      if (params.experience_years?.max) {
        query = query.lte('experience_years', params.experience_years.max);
      }
      if (params.is_active !== undefined) {
        query = query.eq('is_active', params.is_active);
      }

      query = query.range((page - 1) * per_page, page * per_page - 1);

      const { data, error, count } = await query;

      if (error) {
        this.handleError(error);
      }

      const result = {
        success: true,
        data: data || [],
        meta: {
          page,
          per_page,
          total: count || 0,
          total_pages: Math.ceil((count || 0) / per_page),
        },
      };

      this.cache.set(cacheKey, result, 60000); // Cache for 1 minute
      return result;
    });
  }

  /**
   * Get user by ID
   */
  async getUserById(userId: number): Promise<User> {
    const cacheKey = `user-${userId}`;
    const cached = this.cache.get<User>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('users')
        .select('*')
        .eq('user_id', userId)
        .single();

      if (error) {
        this.handleError(error);
      }

      this.cache.set(cacheKey, data, 300000); // Cache for 5 minutes
      return data;
    });
  }

  // =====================================================================================
  // SCORING OPERATIONS
  // =====================================================================================

  /**
   * Calculate scores for users and jobs
   */
  async calculateScores(params: ScoringParams = {}): Promise<ScoringCalculationResult> {
    return this.withRetry(async () => {
      const response = await fetch('/api/scoring/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.code || 'SCORING_ERROR',
          errorData.message || `Scoring failed: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      const result = await response.json();
      this.cache.invalidate('scores');
      return result;
    });
  }

  /**
   * Get scores for a user
   */
  async getUserScores(
    userId: number,
    params: PaginationParams = {}
  ): Promise<ApiResponse<Score[]>> {
    const cacheKey = `user-scores-${userId}-${JSON.stringify(params)}`;
    const cached = this.cache.get<ApiResponse<Score[]>>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();
      const { page = 1, per_page = 20, sort_by = 'total_score', sort_order = 'desc' } = params;

      const { data, error, count } = await client
        .from('scores')
        .select('*', { count: 'exact' })
        .eq('user_id', userId)
        .order(sort_by, { ascending: sort_order === 'asc' })
        .range((page - 1) * per_page, page * per_page - 1);

      if (error) {
        this.handleError(error);
      }

      const result = {
        success: true,
        data: data || [],
        meta: {
          page,
          per_page,
          total: count || 0,
          total_pages: Math.ceil((count || 0) / per_page),
        },
      };

      this.cache.set(cacheKey, result, 120000); // Cache for 2 minutes
      return result;
    });
  }

  /**
   * Get recommended jobs for a user
   */
  async getRecommendedJobs(
    userId: number,
    limit: number = 10,
    minScore: number = 0.5
  ): Promise<Job[]> {
    const cacheKey = `recommended-jobs-${userId}-${limit}-${minScore}`;
    const cached = this.cache.get<Job[]>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('scores')
        .select(`
          *,
          jobs (*)
        `)
        .eq('user_id', userId)
        .eq('is_recommended', true)
        .gte('total_score', minScore)
        .order('total_score', { ascending: false })
        .limit(limit);

      if (error) {
        this.handleError(error);
      }

      const jobs = data?.map(score => score.jobs).filter(Boolean) || [];
      this.cache.set(cacheKey, jobs, 300000); // Cache for 5 minutes
      return jobs;
    });
  }

  // =====================================================================================
  // MONITORING OPERATIONS
  // =====================================================================================

  /**
   * Execute raw SQL query (admin only)
   */
  async executeSQL(query: string): Promise<QueryResult> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();
      const startTime = Date.now();

      const { data, error } = await client.rpc('execute_sql', {
        query_text: query,
      });

      if (error) {
        this.handleError(error);
      }

      const executionTime = Date.now() - startTime;

      // Transform data to match QueryResult interface
      const result: QueryResult = {
        columns: data?.columns || [],
        rows: data?.rows || [],
        rowCount: data?.rows?.length || 0,
        executionTime,
      };

      return result;
    });
  }

  /**
   * Get system metrics
   */
  async getSystemMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<SystemMetrics[]> {
    const cacheKey = `system-metrics-${startDate || 'all'}-${endDate || 'all'}`;
    const cached = this.cache.get<SystemMetrics[]>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      let query = client
        .from('system_metrics')
        .select('*')
        .order('recorded_at', { ascending: false });

      if (startDate) {
        query = query.gte('recorded_at', startDate);
      }
      if (endDate) {
        query = query.lte('recorded_at', endDate);
      }

      const { data, error } = await query;

      if (error) {
        this.handleError(error);
      }

      this.cache.set(cacheKey, data || [], 60000); // Cache for 1 minute
      return data || [];
    });
  }

  /**
   * Get system logs with filters
   */
  async getLogs(filters: LogFilters = {}): Promise<SystemLog[]> {
    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      let query = client
        .from('system_logs')
        .select('*')
        .order('created_at', { ascending: false });

      if (filters.level?.length) {
        query = query.in('level', filters.level);
      }
      if (filters.component?.length) {
        query = query.in('component', filters.component);
      }
      if (filters.start_date) {
        query = query.gte('created_at', filters.start_date);
      }
      if (filters.end_date) {
        query = query.lte('created_at', filters.end_date);
      }
      if (filters.user_id) {
        query = query.eq('user_id', filters.user_id);
      }
      if (filters.operation) {
        query = query.ilike('operation', `%${filters.operation}%`);
      }
      if (filters.limit) {
        query = query.limit(filters.limit);
      }

      const { data, error } = await query;

      if (error) {
        this.handleError(error);
      }

      return data || [];
    });
  }

  /**
   * Stream logs in real-time
   */
  subscribeToLogs(callback: (log: SystemLog) => void) {
    return realtimeManager.subscribeToLogs((payload) => {
      if (payload.eventType === 'INSERT' && payload.new) {
        callback(payload.new as SystemLog);
      }
    });
  }

  // =====================================================================================
  // EMAIL OPERATIONS
  // =====================================================================================

  /**
   * Preview email for a user
   */
  async previewEmail(userId: number): Promise<EmailPreview> {
    return this.withRetry(async () => {
      const response = await fetch(`/api/email/preview/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.code || 'EMAIL_PREVIEW_ERROR',
          errorData.message || `Email preview failed: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    });
  }

  /**
   * Send email to user
   */
  async sendEmail(userId: number, scheduleTime?: string): Promise<EmailJob> {
    return this.withRetry(async () => {
      const response = await fetch('/api/email/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          scheduled_send_at: scheduleTime,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.code || 'EMAIL_SEND_ERROR',
          errorData.message || `Email send failed: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    });
  }

  /**
   * Get email job status
   */
  async getEmailJob(emailId: string): Promise<EmailJob> {
    const cacheKey = `email-job-${emailId}`;
    const cached = this.cache.get<EmailJob>(cacheKey);
    if (cached) return cached;

    return this.withRetry(async () => {
      const client = this.getSupabaseClient();

      const { data, error } = await client
        .from('email_jobs')
        .select('*')
        .eq('email_id', emailId)
        .single();

      if (error) {
        this.handleError(error);
      }

      // Cache completed/failed emails longer
      const ttl = ['sent', 'failed'].includes(data.send_status) ? 300000 : 30000;
      this.cache.set(cacheKey, data, ttl);
      return data;
    });
  }

  // =====================================================================================
  // UTILITY METHODS
  // =====================================================================================

  /**
   * Get health check status
   */
  async getHealthStatus(): Promise<{ status: 'healthy' | 'unhealthy'; details: any }> {
    try {
      const client = this.getSupabaseClient();
      const { data, error } = await client.rpc('get_database_health');

      if (error) {
        return {
          status: 'unhealthy',
          details: { error: error.message },
        };
      }

      return {
        status: 'healthy',
        details: data,
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: { error: (error as Error).message },
      };
    }
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Invalidate specific cache patterns
   */
  invalidateCache(pattern: string): void {
    this.cache.invalidate(pattern);
  }
}

// Singleton instances
export const apiClient = new ApiClient(false); // Browser client
export const serverApiClient = new ApiClient(true); // Server client

// Export the class for custom instances
export default ApiClient;