// Main library exports for the job matching system

// Types
export * from './types';

// API Client and Endpoints
export * from './api/client';
export * from './api/endpoints';

// React Query Integration
export * from './query';

// Stores
export * from '../stores';

// Hooks
export * from '../hooks';

// Utilities
export * from './utils';

// Providers
export * from './providers';

// Constants
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
} as const;

export const CACHE_CONFIG = {
  STALE_TIME: 5 * 60 * 1000, // 5 minutes
  GC_TIME: 10 * 60 * 1000, // 10 minutes
  SCORE_TTL: 15 * 60 * 1000, // 15 minutes
  JOB_TTL: 10 * 60 * 1000, // 10 minutes
} as const;

export const UI_CONFIG = {
  TOAST_DURATION: 5000,
  MODAL_ANIMATION_DURATION: 300,
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 100,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024,
} as const;

export const SCORE_CONFIG = {
  MIN_SCORE: 0,
  MAX_SCORE: 100,
  DEFAULT_WEIGHTS: {
    skills: 0.3,
    experience: 0.25,
    location: 0.15,
    salary: 0.2,
    culture: 0.1,
  },
  SCORE_GRADES: {
    A: 90,
    B: 80,
    C: 70,
    D: 60,
    F: 0,
  },
} as const;

export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  INFINITE_SCROLL_THRESHOLD: 200,
} as const;

// Version information
export const VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0';

// Feature flags
export const FEATURES = {
  WEBSOCKET_ENABLED: process.env.NEXT_PUBLIC_WEBSOCKET_ENABLED === 'true',
  ANALYTICS_ENABLED: process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true',
  NOTIFICATIONS_ENABLED: process.env.NEXT_PUBLIC_NOTIFICATIONS_ENABLED === 'true',
  DEVTOOLS_ENABLED: process.env.NODE_ENV === 'development',
} as const;