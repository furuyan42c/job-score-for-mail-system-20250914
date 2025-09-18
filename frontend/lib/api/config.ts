/**
 * API Configuration and Environment Management
 *
 * Centralized configuration management for API clients, Supabase,
 * and environment-specific settings with validation.
 */

import { z } from 'zod';

// =====================================================================================
// ENVIRONMENT SCHEMA VALIDATION
// =====================================================================================

const environmentSchema = z.object({
  // Required Supabase configuration
  NEXT_PUBLIC_SUPABASE_URL: z.string().url('Invalid Supabase URL'),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1, 'Supabase anon key is required'),

  // Optional Supabase service role (server-side only)
  SUPABASE_SERVICE_ROLE_KEY: z.string().optional(),

  // Application configuration
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  NEXT_PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),
  NEXT_PUBLIC_APP_NAME: z.string().default('Job Matching System'),
  NEXT_PUBLIC_APP_VERSION: z.string().default('1.0.0'),

  // API configuration
  NEXT_PUBLIC_API_URL: z.string().url().optional(),
  API_TIMEOUT: z.string().transform(Number).optional(),
  API_RETRY_ATTEMPTS: z.string().transform(Number).default('3'),

  // Feature flags
  NEXT_PUBLIC_ENABLE_REALTIME: z.string().transform(val => val === 'true').default('true'),
  NEXT_PUBLIC_ENABLE_CACHING: z.string().transform(val => val === 'true').default('true'),
  NEXT_PUBLIC_ENABLE_ANALYTICS: z.string().transform(val => val === 'true').default('false'),
  NEXT_PUBLIC_ENABLE_DEBUG_MODE: z.string().transform(val => val === 'true').default('false'),

  // Rate limiting
  RATE_LIMIT_BATCH_OPERATIONS: z.string().transform(Number).default('5'),
  RATE_LIMIT_SCORING_REQUESTS: z.string().transform(Number).default('10'),
  RATE_LIMIT_EMAIL_SENDS: z.string().transform(Number).default('100'),

  // Cache configuration
  CACHE_TTL_SHORT: z.string().transform(Number).default('30'),
  CACHE_TTL_MEDIUM: z.string().transform(Number).default('300'),
  CACHE_TTL_LONG: z.string().transform(Number).default('1800'),

  // Monitoring and logging
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  ENABLE_PERFORMANCE_MONITORING: z.string().transform(val => val === 'true').default('false'),

  // Security
  ENABLE_CSRF_PROTECTION: z.string().transform(val => val === 'true').default('true'),
  CORS_ALLOWED_ORIGINS: z.string().optional(),

  // Email configuration
  SMTP_HOST: z.string().optional(),
  SMTP_PORT: z.string().transform(Number).optional(),
  SMTP_USER: z.string().optional(),
  SMTP_PASSWORD: z.string().optional(),
  EMAIL_FROM: z.string().email().optional(),

  // External services
  OPENAI_API_KEY: z.string().optional(),
  ANTHROPIC_API_KEY: z.string().optional(),
});

// =====================================================================================
// ENVIRONMENT VALIDATION AND PARSING
// =====================================================================================

function validateEnvironment() {
  try {
    const env = environmentSchema.parse(process.env);
    return env;
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(
        (err) => `${err.path.join('.')}: ${err.message}`
      );
      throw new Error(
        `Environment validation failed:\n${errorMessages.join('\n')}`
      );
    }
    throw error;
  }
}

// Validate environment on module load
const env = validateEnvironment();

// =====================================================================================
// CONFIGURATION OBJECTS
// =====================================================================================

/**
 * Supabase configuration
 */
export const supabaseConfig = {
  url: env.NEXT_PUBLIC_SUPABASE_URL,
  anonKey: env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  serviceRoleKey: env.SUPABASE_SERVICE_ROLE_KEY,

  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce' as const,
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
  },

  realtime: {
    enabled: env.NEXT_PUBLIC_ENABLE_REALTIME,
    params: {
      eventsPerSecond: 10,
    },
  },

  db: {
    schema: 'public',
  },

  global: {
    headers: {
      'X-Client-Info': `${env.NEXT_PUBLIC_APP_NAME}/${env.NEXT_PUBLIC_APP_VERSION}`,
    },
  },
} as const;

/**
 * API client configuration
 */
export const apiConfig = {
  baseURL: env.NEXT_PUBLIC_API_URL || env.NEXT_PUBLIC_APP_URL,
  timeout: env.API_TIMEOUT || 30000,
  retryAttempts: env.API_RETRY_ATTEMPTS,

  // Cache settings
  cache: {
    enabled: env.NEXT_PUBLIC_ENABLE_CACHING,
    ttl: {
      short: env.CACHE_TTL_SHORT * 1000,
      medium: env.CACHE_TTL_MEDIUM * 1000,
      long: env.CACHE_TTL_LONG * 1000,
    },
  },

  // Rate limiting
  rateLimit: {
    batchOperations: env.RATE_LIMIT_BATCH_OPERATIONS,
    scoringRequests: env.RATE_LIMIT_SCORING_REQUESTS,
    emailSends: env.RATE_LIMIT_EMAIL_SENDS,
  },

  // Retry configuration
  retry: {
    maxAttempts: env.API_RETRY_ATTEMPTS,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
  },

  // Headers
  defaultHeaders: {
    'Content-Type': 'application/json',
    'X-Client-Version': env.NEXT_PUBLIC_APP_VERSION,
  },
} as const;

/**
 * Application configuration
 */
export const appConfig = {
  name: env.NEXT_PUBLIC_APP_NAME,
  version: env.NEXT_PUBLIC_APP_VERSION,
  url: env.NEXT_PUBLIC_APP_URL,
  environment: env.NODE_ENV,

  // Feature flags
  features: {
    realtime: env.NEXT_PUBLIC_ENABLE_REALTIME,
    caching: env.NEXT_PUBLIC_ENABLE_CACHING,
    analytics: env.NEXT_PUBLIC_ENABLE_ANALYTICS,
    debugMode: env.NEXT_PUBLIC_ENABLE_DEBUG_MODE,
    performanceMonitoring: env.ENABLE_PERFORMANCE_MONITORING,
  },

  // Pagination defaults
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
    minPageSize: 5,
  },

  // File upload limits
  upload: {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedMimeTypes: [
      'text/csv',
      'application/csv',
      'text/plain',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
  },

  // UI configuration
  ui: {
    theme: 'system' as 'light' | 'dark' | 'system',
    animations: true,
    compactMode: false,
  },
} as const;

/**
 * Logging configuration
 */
export const loggingConfig = {
  level: env.LOG_LEVEL,
  enableConsole: env.NODE_ENV === 'development',
  enableRemote: env.NODE_ENV === 'production',

  // Log retention
  retention: {
    debug: 1, // 1 day
    info: 7,  // 7 days
    warn: 30, // 30 days
    error: 90, // 90 days
  },

  // Performance logging
  performance: {
    enabled: env.ENABLE_PERFORMANCE_MONITORING,
    thresholds: {
      slow: 1000,    // 1 second
      verySlow: 5000, // 5 seconds
    },
  },
} as const;

/**
 * Security configuration
 */
export const securityConfig = {
  csrf: {
    enabled: env.ENABLE_CSRF_PROTECTION,
  },

  cors: {
    allowedOrigins: env.CORS_ALLOWED_ORIGINS?.split(',') || [env.NEXT_PUBLIC_APP_URL],
    allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  },

  // Content Security Policy
  csp: {
    enabled: env.NODE_ENV === 'production',
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-eval'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", env.NEXT_PUBLIC_SUPABASE_URL],
    },
  },
} as const;

/**
 * Email configuration
 */
export const emailConfig = {
  smtp: {
    host: env.SMTP_HOST,
    port: env.SMTP_PORT || 587,
    secure: false,
    auth: env.SMTP_USER && env.SMTP_PASSWORD ? {
      user: env.SMTP_USER,
      pass: env.SMTP_PASSWORD,
    } : undefined,
  },

  from: env.EMAIL_FROM || `noreply@${env.NEXT_PUBLIC_APP_URL.replace(/https?:\/\//, '')}`,

  templates: {
    jobRecommendations: 'job-recommendations',
    batchComplete: 'batch-complete',
    systemAlert: 'system-alert',
  },

  limits: {
    dailySendLimit: 1000,
    hourlyBatchLimit: 10,
    recipientsPerBatch: 100,
  },
} as const;

/**
 * External services configuration
 */
export const externalConfig = {
  openai: {
    apiKey: env.OPENAI_API_KEY,
    model: 'gpt-4',
    maxTokens: 2048,
    temperature: 0.7,
  },

  anthropic: {
    apiKey: env.ANTHROPIC_API_KEY,
    model: 'claude-3-sonnet-20240229',
    maxTokens: 4096,
  },
} as const;

// =====================================================================================
// UTILITY FUNCTIONS
// =====================================================================================

/**
 * Check if feature is enabled
 */
export function isFeatureEnabled(feature: keyof typeof appConfig.features): boolean {
  return appConfig.features[feature];
}

/**
 * Get environment-specific configuration
 */
export function getEnvironmentConfig() {
  const isDevelopment = env.NODE_ENV === 'development';
  const isProduction = env.NODE_ENV === 'production';
  const isTest = env.NODE_ENV === 'test';

  return {
    isDevelopment,
    isProduction,
    isTest,

    // Development-specific settings
    ...(isDevelopment && {
      enableDebugLogs: true,
      enableHotReload: true,
      skipRateLimit: true,
      showPerformanceMetrics: true,
    }),

    // Production-specific settings
    ...(isProduction && {
      enableDebugLogs: false,
      enableHotReload: false,
      skipRateLimit: false,
      showPerformanceMetrics: false,
      enableSecurityHeaders: true,
      enableErrorReporting: true,
    }),

    // Test-specific settings
    ...(isTest && {
      enableDebugLogs: false,
      skipAuthentication: true,
      useMockData: true,
      disableRealtime: true,
    }),
  };
}

/**
 * Validate configuration at runtime
 */
export function validateConfig() {
  const errors: string[] = [];

  // Check required environment variables
  if (!supabaseConfig.url) {
    errors.push('NEXT_PUBLIC_SUPABASE_URL is required');
  }

  if (!supabaseConfig.anonKey) {
    errors.push('NEXT_PUBLIC_SUPABASE_ANON_KEY is required');
  }

  // Check Supabase URL format
  if (supabaseConfig.url && !supabaseConfig.url.includes('supabase.co')) {
    console.warn('Supabase URL does not appear to be a valid Supabase URL');
  }

  // Check rate limit values
  if (apiConfig.rateLimit.batchOperations < 1) {
    errors.push('RATE_LIMIT_BATCH_OPERATIONS must be at least 1');
  }

  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }

  return true;
}

/**
 * Get configuration summary for debugging
 */
export function getConfigSummary() {
  return {
    environment: env.NODE_ENV,
    appName: appConfig.name,
    appVersion: appConfig.version,
    supabaseUrl: supabaseConfig.url,
    featuresEnabled: Object.entries(appConfig.features)
      .filter(([, enabled]) => enabled)
      .map(([feature]) => feature),
    cacheEnabled: apiConfig.cache.enabled,
    realtimeEnabled: supabaseConfig.realtime.enabled,
  };
}

// Validate configuration on module load
validateConfig();

// Export the validated environment for type safety
export { env };

// Export all configurations
export default {
  supabase: supabaseConfig,
  api: apiConfig,
  app: appConfig,
  logging: loggingConfig,
  security: securityConfig,
  email: emailConfig,
  external: externalConfig,
  env,
};