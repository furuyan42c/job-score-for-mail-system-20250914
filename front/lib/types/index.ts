// Base Types
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// User Types
export interface User extends BaseEntity {
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  role: 'candidate' | 'recruiter' | 'admin';
  isEmailVerified: boolean;
  lastLoginAt?: string;
}

export interface UserProfile extends BaseEntity {
  userId: string;
  bio?: string;
  location?: string;
  website?: string;
  linkedinUrl?: string;
  githubUrl?: string;
  experience: ExperienceLevel;
  skills: string[];
  preferences: UserPreferences;
}

export interface UserPreferences {
  jobTypes: JobType[];
  salaryRange: {
    min: number;
    max: number;
    currency: string;
  };
  locations: string[];
  remoteWork: boolean;
  emailNotifications: boolean;
  pushNotifications: boolean;
  theme: 'light' | 'dark' | 'system';
}

export interface AuthState {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  sessionExpiresAt: string | null;
}

// Job Types
export type JobType = 'full-time' | 'part-time' | 'contract' | 'freelance' | 'internship';
export type ExperienceLevel = 'entry' | 'junior' | 'mid' | 'senior' | 'lead' | 'principal';
export type JobStatus = 'active' | 'paused' | 'closed' | 'draft';

export interface Job extends BaseEntity {
  title: string;
  company: string;
  description: string;
  requirements: string[];
  responsibilities: string[];
  location: string;
  isRemote: boolean;
  jobType: JobType;
  experienceLevel: ExperienceLevel;
  salaryRange?: {
    min: number;
    max: number;
    currency: string;
  };
  skills: string[];
  benefits: string[];
  status: JobStatus;
  applicationDeadline?: string;
  applicantCount: number;
  viewCount: number;
  postedBy: string; // User ID
  companyLogo?: string;
  companySize?: string;
  industry?: string;
}

export interface JobSearchParams {
  query?: string;
  location?: string;
  jobType?: JobType[];
  experienceLevel?: ExperienceLevel[];
  salaryMin?: number;
  salaryMax?: number;
  isRemote?: boolean;
  skills?: string[];
  company?: string;
  postedWithin?: 'day' | 'week' | 'month' | 'any';
}

export interface JobFilters extends JobSearchParams {
  sortBy: 'relevance' | 'date' | 'salary' | 'distance';
  sortOrder: 'asc' | 'desc';
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
}

// Score Types
export interface JobScore extends BaseEntity {
  userId: string;
  jobId: string;
  overallScore: number;
  skillsScore: number;
  experienceScore: number;
  locationScore: number;
  salaryScore: number;
  cultureScore: number;
  reasons: string[];
  recommendations: string[];
  calculatedAt: string;
}

export interface ScoreBreakdown {
  category: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface UserJobScore {
  job: Job;
  score: JobScore;
  breakdown: ScoreBreakdown[];
  ranking: number;
}

// Application Types
export interface JobApplication extends BaseEntity {
  userId: string;
  jobId: string;
  status: 'pending' | 'reviewing' | 'interview' | 'offer' | 'rejected' | 'withdrawn';
  appliedAt: string;
  coverLetter?: string;
  resumeUrl?: string;
  customResponses?: Record<string, string>;
  lastStatusUpdate: string;
  notes?: string;
}

// UI State Types
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface Modal {
  id: string;
  isOpen: boolean;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeable?: boolean;
}

export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string | null;
}

// Search and Filter Types
export interface SavedSearch extends BaseEntity {
  userId: string;
  name: string;
  filters: JobFilters;
  alertsEnabled: boolean;
  lastRunAt?: string;
}

export interface SearchHistory {
  query: string;
  timestamp: string;
  resultsCount: number;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface RealTimeUpdate {
  entityType: 'job' | 'application' | 'score' | 'user';
  action: 'create' | 'update' | 'delete';
  entityId: string;
  data: any;
}

// Cache Types
export interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number;
  strategy: 'lru' | 'fifo' | 'manual';
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

// Store Types
export interface StoreState {
  isHydrated: boolean;
  lastSync: string | null;
  version: string;
}

export interface AsyncAction<T = any> {
  isLoading: boolean;
  error: string | null;
  data: T | null;
  lastFetch: string | null;
}

// Action Types for optimistic updates
export interface OptimisticAction<T> {
  id: string;
  type: string;
  optimisticData: T;
  rollbackData?: T;
  timestamp: number;
  status: 'pending' | 'confirmed' | 'failed';
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'multiselect' | 'textarea' | 'checkbox' | 'radio';
  required: boolean;
  placeholder?: string;
  options?: { label: string; value: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => string | true;
  };
}

export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}