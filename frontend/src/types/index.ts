// Core Types for Job Matching System

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserProfile {
  id: string;
  userId: string;
  title?: string;
  bio?: string;
  location?: string;
  skills: string[];
  experience: ExperienceLevel;
  salaryExpectation?: SalaryRange;
  preferences: UserPreferences;
  resume?: string;
  portfolioUrl?: string;
  linkedinUrl?: string;
  githubUrl?: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  requirements: string[];
  location: string;
  locationType: 'remote' | 'hybrid' | 'onsite';
  salary: SalaryRange;
  experienceLevel: ExperienceLevel;
  jobType: JobType;
  skills: string[];
  benefits: string[];
  postedAt: Date;
  expiresAt?: Date;
  status: JobStatus;
  applicantCount: number;
  views: number;
  companyLogo?: string;
  companySize?: CompanySize;
  industry?: string;
}

export interface JobMatch {
  id: string;
  userId: string;
  jobId: string;
  score: number;
  factors: MatchFactor[];
  createdAt: Date;
  status: MatchStatus;
  feedback?: MatchFeedback;
}

export interface MatchFactor {
  type: 'skills' | 'experience' | 'salary' | 'location' | 'preferences';
  weight: number;
  score: number;
  description: string;
}

export interface Application {
  id: string;
  userId: string;
  jobId: string;
  status: ApplicationStatus;
  appliedAt: Date;
  coverLetter?: string;
  customResume?: string;
  notes?: string;
  timeline: ApplicationEvent[];
}

export interface ApplicationEvent {
  id: string;
  type: ApplicationEventType;
  description: string;
  date: Date;
  metadata?: Record<string, any>;
}

// Enums and Union Types
export type ExperienceLevel = 'entry' | 'junior' | 'mid' | 'senior' | 'lead' | 'executive';
export type JobType = 'full-time' | 'part-time' | 'contract' | 'freelance' | 'internship';
export type JobStatus = 'active' | 'paused' | 'filled' | 'expired' | 'draft';
export type MatchStatus = 'new' | 'viewed' | 'interested' | 'not-interested' | 'applied';
export type ApplicationStatus = 'pending' | 'reviewing' | 'interview' | 'offered' | 'rejected' | 'withdrawn';
export type ApplicationEventType = 'applied' | 'viewed' | 'interview_scheduled' | 'interview_completed' | 'offer_extended' | 'offer_accepted' | 'offer_declined' | 'rejected' | 'withdrawn';
export type CompanySize = 'startup' | 'small' | 'medium' | 'large' | 'enterprise';

// Complex Types
export interface SalaryRange {
  min: number;
  max: number;
  currency: string;
  period: 'hour' | 'month' | 'year';
}

export interface UserPreferences {
  jobTypes: JobType[];
  locationTypes: Array<'remote' | 'hybrid' | 'onsite'>;
  industries: string[];
  companySizes: CompanySize[];
  minSalary?: number;
  maxCommute?: number; // in minutes
  benefits: string[];
  workCulture: string[];
}

export interface MatchFeedback {
  rating: number; // 1-5
  helpful: boolean;
  reason?: string;
  suggestions?: string[];
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  'data-testid'?: string;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

export interface InputProps extends BaseComponentProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url';
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  label?: string;
  helperText?: string;
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  description?: string;
}

export interface SelectProps extends BaseComponentProps {
  options: SelectOption[];
  value?: string | string[];
  defaultValue?: string | string[];
  onChange?: (value: string | string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  label?: string;
  helperText?: string;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export interface BadgeProps extends BaseComponentProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  removable?: boolean;
  onRemove?: () => void;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
  success: boolean;
  timestamp: string;
}

export interface JobSearchParams {
  query?: string;
  skills?: string[];
  location?: string;
  salary?: SalaryRange;
  experienceLevel?: ExperienceLevel[];
  jobType?: JobType[];
  locationType?: Array<'remote' | 'hybrid' | 'onsite'>;
  companySize?: CompanySize[];
  industry?: string[];
  postedWithin?: number; // days
  sortBy?: 'relevance' | 'date' | 'salary' | 'match_score';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface JobFilters {
  skills: string[];
  locations: string[];
  salaryRange: SalaryRange;
  experienceLevels: ExperienceLevel[];
  jobTypes: JobType[];
  locationTypes: Array<'remote' | 'hybrid' | 'onsite'>;
  companySizes: CompanySize[];
  industries: string[];
  postedWithin: number;
}

// State Management Types
export interface JobState {
  jobs: Job[];
  selectedJob: Job | null;
  loading: boolean;
  error: string | null;
  filters: JobFilters;
  searchParams: JobSearchParams;
  totalJobs: number;
  currentPage: number;
}

export interface UserState {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface MatchState {
  matches: JobMatch[];
  selectedMatch: JobMatch | null;
  loading: boolean;
  error: string | null;
  totalMatches: number;
  currentPage: number;
}

// Event Types
export interface ComponentEvent<T = any> {
  type: string;
  payload: T;
  timestamp: Date;
}

export interface FormValidation {
  isValid: boolean;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

// Utility Types
export type WithLoading<T> = T & { loading?: boolean };
export type WithError<T> = T & { error?: string };
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// SqlEditor Types
export interface SqlQuery {
  id: string;
  query: string;
  timestamp: Date;
  executionTime?: number;
  rowCount?: number;
  error?: string;
}

export interface SqlQueryResult {
  columns: SqlColumn[];
  rows: Record<string, any>[];
  rowCount: number;
  executionTime: number;
  query: string;
}

export interface SqlColumn {
  name: string;
  type: string;
  nullable?: boolean;
}

export interface SqlEditorProps extends BaseComponentProps {
  initialQuery?: string;
  onQueryExecute?: (query: string) => Promise<SqlQueryResult>;
  readOnly?: boolean;
  height?: string;
  showHistory?: boolean;
  autoComplete?: boolean;
  templates?: SqlTemplate[];
}

export interface SqlTemplate {
  id: string;
  name: string;
  description: string;
  query: string;
  category: 'jobs' | 'users' | 'matches' | 'general';
}

export interface QueryHistoryProps extends BaseComponentProps {
  queries: SqlQuery[];
  onQuerySelect?: (query: SqlQuery) => void;
  onQueryDelete?: (queryId: string) => void;
  maxItems?: number;
}

export interface ResultsTableProps extends BaseComponentProps {
  result: SqlQueryResult | null;
  loading?: boolean;
  error?: string;
  onExportCsv?: () => void;
  maxRows?: number;
}

// Dashboard Types
export interface DashboardMetric {
  id: string;
  label: string;
  value: number | string;
  previousValue?: number | string;
  trend?: 'up' | 'down' | 'stable';
  change?: number;
  format?: 'number' | 'percentage' | 'currency' | 'duration';
  icon?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  services: ServiceStatus[];
  lastCheck: Date;
  uptime: number;
}

export interface ServiceStatus {
  name: string;
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  lastCheck: Date;
  error?: string;
}

export interface BatchJobStatus {
  id: string;
  name: string;
  type: 'matching' | 'email' | 'sync' | 'cleanup';
  status: 'running' | 'completed' | 'failed' | 'pending' | 'cancelled';
  progress?: number;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  processedItems?: number;
  totalItems?: number;
  error?: string;
}

export interface DashboardData {
  metrics: DashboardMetric[];
  systemHealth: SystemHealth;
  batchJobs: BatchJobStatus[];
  recentActivity: ActivityItem[];
  chartData: ChartDataPoint[];
}

export interface ActivityItem {
  id: string;
  type: 'user_registered' | 'job_posted' | 'match_created' | 'application_submitted';
  description: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  category?: string;
}

export interface DashboardProps extends BaseComponentProps {
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
  showBatchJobs?: boolean;
  showSystemHealth?: boolean;
  showCharts?: boolean;
  onRefresh?: () => void;
}

export interface MetricCardProps extends BaseComponentProps {
  metric: DashboardMetric;
  size?: 'sm' | 'md' | 'lg';
  showTrend?: boolean;
  onClick?: () => void;
}

export interface StatusIndicatorProps extends BaseComponentProps {
  status: 'up' | 'down' | 'degraded' | 'running' | 'completed' | 'failed' | 'pending';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}