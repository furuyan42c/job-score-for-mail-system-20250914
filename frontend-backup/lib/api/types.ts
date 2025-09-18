/**
 * TypeScript Type Definitions for Job Matching System
 *
 * Comprehensive type definitions for database tables, API requests/responses,
 * and business logic entities based on the PostgreSQL schema.
 */

// =====================================================================================
// DATABASE TYPES - Master Data
// =====================================================================================

export interface PrefectureMaster {
  code: string; // CHAR(2)
  name: string;
  region: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CityMaster {
  code: string; // VARCHAR(5)
  pref_cd: string;
  name: string;
  latitude?: number;
  longitude?: number;
  nearby_city_codes?: string[];
  created_at: string;
  updated_at: string;
}

export interface OccupationMaster {
  code: string; // CHAR(3)
  name: string;
  category: string;
  subcategory?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface IndustryMaster {
  code: string; // CHAR(3)
  name: string;
  category: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// =====================================================================================
// CORE ENTITY TYPES
// =====================================================================================

export interface Location {
  pref_cd: string;
  city_cd?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  station_access?: string;
  remote_work_rate?: number;
}

export interface Salary {
  min_amount?: number;
  max_amount?: number;
  avg_amount?: number;
  currency: string;
  period: 'hourly' | 'daily' | 'monthly' | 'yearly';
  bonus_info?: string;
  benefits?: string[];
}

export interface JobFeatures {
  remote_work_available?: boolean;
  flexible_hours?: boolean;
  overtime_avg_hours?: number;
  vacation_days?: number;
  training_provided?: boolean;
  career_advancement?: boolean;
  certification_support?: boolean;
  equipment_provided?: boolean;
}

export interface Job {
  job_id: number;
  endcl_cd: string;
  title: string;
  description: string;
  company_name: string;
  company_type?: string;
  company_size?: string;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'temporary' | 'internship';
  occupation_cd: string;
  industry_cd: string;
  location: Location;
  salary: Salary;
  features: JobFeatures;
  requirements?: string[];
  skills_required?: string[];
  experience_required?: string;
  education_required?: string;
  application_deadline?: string;
  external_url?: string;
  is_active: boolean;
  posted_date: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  preferred_occupations?: string[];
  preferred_industries?: string[];
  preferred_locations?: string[];
  salary_expectations?: {
    min_amount?: number;
    max_amount?: number;
    currency: string;
    period: string;
  };
  employment_types?: string[];
  remote_work_preference?: number; // 0-10 scale
  overtime_tolerance?: number; // max hours
  commute_time_max?: number; // minutes
  career_stage?: 'entry' | 'mid' | 'senior' | 'executive';
  skills?: string[];
  certifications?: string[];
}

export interface User {
  user_id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  age?: number;
  gender?: string;
  current_location?: Location;
  preferences: UserPreferences;
  resume_text?: string;
  skills?: string[];
  experience_years?: number;
  education_level?: string;
  certifications?: string[];
  language_skills?: Record<string, string>;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface ScoringWeights {
  location_weight: number;
  salary_weight: number;
  occupation_weight: number;
  industry_weight: number;
  skills_weight: number;
  experience_weight: number;
  company_culture_weight: number;
  growth_potential_weight: number;
}

export interface Score {
  user_id: number;
  job_id: number;
  total_score: number;
  location_score: number;
  salary_score: number;
  occupation_score: number;
  industry_score: number;
  skills_score: number;
  experience_score: number;
  company_culture_score: number;
  growth_potential_score: number;
  reasoning?: Record<string, any>;
  is_recommended: boolean;
  calculated_at: string;
}

export interface ScoringCalculationResult {
  calculation_id: string;
  user_id?: number;
  total_jobs_processed: number;
  total_scores_calculated: number;
  avg_score: number;
  max_score: number;
  min_score: number;
  processing_time_ms: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

// =====================================================================================
// BATCH PROCESSING TYPES
// =====================================================================================

export type BatchType = 'jobs_import' | 'scoring_calculation' | 'email_generation' | 'full_pipeline';

export type BatchStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type BatchPhase = 'import' | 'validation' | 'matching' | 'email' | 'complete';

export interface BatchExecution {
  batch_id: string;
  batch_type: BatchType;
  status: BatchStatus;
  phase: BatchPhase;
  progress_percentage: number;
  items_total?: number;
  items_processed?: number;
  items_successful?: number;
  items_failed?: number;
  config?: Record<string, any>;
  error_summary?: string;
  performance_metrics?: Record<string, any>;
  estimated_completion?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface BatchOperationLog {
  log_id: string;
  batch_id: string;
  phase: BatchPhase;
  operation_type: string;
  target_entity?: string;
  target_id?: string;
  status: 'success' | 'warning' | 'error';
  message: string;
  details?: Record<string, any>;
  execution_time_ms?: number;
  created_at: string;
}

// =====================================================================================
// EMAIL TYPES
// =====================================================================================

export interface EmailTemplate {
  template_id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text?: string;
  variables?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailJob {
  email_id: string;
  user_id: number;
  template_id: string;
  subject: string;
  body_html: string;
  body_text?: string;
  personalized_content?: Record<string, any>;
  recommended_jobs?: number[];
  send_status: 'pending' | 'sent' | 'failed' | 'scheduled';
  scheduled_send_at?: string;
  sent_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// =====================================================================================
// MONITORING TYPES
// =====================================================================================

export interface SystemLog {
  log_id: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  component: string;
  operation: string;
  message: string;
  details?: Record<string, any>;
  user_id?: number;
  session_id?: string;
  ip_address?: string;
  user_agent?: string;
  execution_time_ms?: number;
  memory_usage_mb?: number;
  created_at: string;
}

export interface SystemMetrics {
  metric_id: string;
  metric_name: string;
  metric_value: number;
  metric_unit: string;
  tags?: Record<string, string>;
  recorded_at: string;
}

export interface Performance {
  operation_id: string;
  operation_name: string;
  component: string;
  execution_time_ms: number;
  memory_used_mb?: number;
  cpu_usage_percent?: number;
  database_queries?: number;
  cache_hits?: number;
  cache_misses?: number;
  status: 'success' | 'error';
  error_details?: string;
  recorded_at: string;
}

// =====================================================================================
// API REQUEST/RESPONSE TYPES
// =====================================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    page?: number;
    per_page?: number;
    total?: number;
    total_pages?: number;
    execution_time?: number;
  };
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface JobSearchParams extends PaginationParams {
  title?: string;
  company?: string;
  location?: {
    pref_cd?: string;
    city_cd?: string;
    radius_km?: number;
  };
  salary?: {
    min_amount?: number;
    max_amount?: number;
  };
  employment_types?: string[];
  occupation_codes?: string[];
  industry_codes?: string[];
  remote_work?: boolean;
  posted_after?: string;
  is_active?: boolean;
}

export interface UserSearchParams extends PaginationParams {
  email?: string;
  name?: string;
  age_range?: {
    min?: number;
    max?: number;
  };
  location?: {
    pref_cd?: string;
    city_cd?: string;
  };
  skills?: string[];
  experience_years?: {
    min?: number;
    max?: number;
  };
  is_active?: boolean;
}

export interface ScoringParams {
  user_ids?: number[];
  job_ids?: number[];
  recalculate?: boolean;
  weights?: Partial<ScoringWeights>;
  min_score_threshold?: number;
}

export interface ImportJobsParams {
  file: File;
  batch_size?: number;
  validate_only?: boolean;
  update_existing?: boolean;
}

export interface ImportResult {
  batch_id: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  validation_errors?: Array<{
    row: number;
    field: string;
    error: string;
  }>;
}

export interface EmailPreview {
  subject: string;
  body_html: string;
  body_text?: string;
  recommended_jobs: Job[];
  personalization_data: Record<string, any>;
}

export interface QueryResult {
  columns: string[];
  rows: any[][];
  rowCount: number;
  executionTime: number;
}

export interface LogFilters {
  level?: string[];
  component?: string[];
  start_date?: string;
  end_date?: string;
  user_id?: number;
  operation?: string;
  limit?: number;
}

// =====================================================================================
// ERROR TYPES
// =====================================================================================

export class APIError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(code: string, message: string, status: number = 500, details?: any) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export class ValidationError extends APIError {
  constructor(message: string, details?: any) {
    super('VALIDATION_ERROR', message, 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required') {
    super('AUTHENTICATION_ERROR', message, 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends APIError {
  constructor(message: string = 'Insufficient permissions') {
    super('AUTHORIZATION_ERROR', message, 403);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends APIError {
  constructor(resource: string) {
    super('NOT_FOUND', `${resource} not found`, 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends APIError {
  constructor(message: string = 'Rate limit exceeded') {
    super('RATE_LIMIT_ERROR', message, 429);
    this.name = 'RateLimitError';
  }
}

// =====================================================================================
// SUPABASE DATABASE TYPE (Generated)
// =====================================================================================

export interface Database {
  public: {
    Tables: {
      prefecture_master: {
        Row: PrefectureMaster;
        Insert: Omit<PrefectureMaster, 'created_at' | 'updated_at'>;
        Update: Partial<Omit<PrefectureMaster, 'code' | 'created_at'>>;
      };
      city_master: {
        Row: CityMaster;
        Insert: Omit<CityMaster, 'created_at' | 'updated_at'>;
        Update: Partial<Omit<CityMaster, 'code' | 'created_at'>>;
      };
      occupation_master: {
        Row: OccupationMaster;
        Insert: Omit<OccupationMaster, 'created_at' | 'updated_at'>;
        Update: Partial<Omit<OccupationMaster, 'code' | 'created_at'>>;
      };
      industry_master: {
        Row: IndustryMaster;
        Insert: Omit<IndustryMaster, 'created_at' | 'updated_at'>;
        Update: Partial<Omit<IndustryMaster, 'code' | 'created_at'>>;
      };
      jobs: {
        Row: Job;
        Insert: Omit<Job, 'job_id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<Job, 'job_id' | 'created_at'>>;
      };
      users: {
        Row: User;
        Insert: Omit<User, 'user_id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<User, 'user_id' | 'created_at'>>;
      };
      scores: {
        Row: Score;
        Insert: Omit<Score, 'calculated_at'>;
        Update: Partial<Omit<Score, 'user_id' | 'job_id'>>;
      };
      scoring_calculation_results: {
        Row: ScoringCalculationResult;
        Insert: Omit<ScoringCalculationResult, 'calculation_id' | 'created_at'>;
        Update: Partial<Omit<ScoringCalculationResult, 'calculation_id' | 'created_at'>>;
      };
      batch_executions: {
        Row: BatchExecution;
        Insert: Omit<BatchExecution, 'batch_id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<BatchExecution, 'batch_id' | 'created_at'>>;
      };
      batch_operation_logs: {
        Row: BatchOperationLog;
        Insert: Omit<BatchOperationLog, 'log_id' | 'created_at'>;
        Update: Partial<Omit<BatchOperationLog, 'log_id' | 'created_at'>>;
      };
      email_templates: {
        Row: EmailTemplate;
        Insert: Omit<EmailTemplate, 'template_id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<EmailTemplate, 'template_id' | 'created_at'>>;
      };
      email_jobs: {
        Row: EmailJob;
        Insert: Omit<EmailJob, 'email_id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<EmailJob, 'email_id' | 'created_at'>>;
      };
      system_logs: {
        Row: SystemLog;
        Insert: Omit<SystemLog, 'log_id' | 'created_at'>;
        Update: Partial<Omit<SystemLog, 'log_id' | 'created_at'>>;
      };
      system_metrics: {
        Row: SystemMetrics;
        Insert: Omit<SystemMetrics, 'metric_id'>;
        Update: Partial<Omit<SystemMetrics, 'metric_id'>>;
      };
      performance: {
        Row: Performance;
        Insert: Omit<Performance, 'operation_id'>;
        Update: Partial<Omit<Performance, 'operation_id'>>;
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      execute_sql: {
        Args: { query_text: string };
        Returns: any;
      };
      get_database_health: {
        Args: {};
        Returns: any;
      };
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// =====================================================================================
// UTILITY TYPES
// =====================================================================================

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;