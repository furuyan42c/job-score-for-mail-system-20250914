/**
 * Routing Types for Job Matching System
 * Next.js 14 App Router with TypeScript
 */

import { Metadata } from 'next';

// Route Parameters
export interface RouteParams {
  id: string;
  slug?: string;
  locale?: string;
}

export interface SearchParams {
  [key: string]: string | string[] | undefined;
}

// Page Props Interface
export interface PageProps {
  params: RouteParams;
  searchParams: SearchParams;
}

// Layout Props Interface
export interface LayoutProps {
  children: React.ReactNode;
  params: RouteParams;
}

// Route Configuration
export interface RouteConfig {
  path: string;
  component: string;
  layout?: string;
  middleware?: string[];
  auth?: boolean;
  roles?: string[];
  metadata?: Metadata;
  revalidate?: number | false;
  dynamic?: 'auto' | 'force-dynamic' | 'error' | 'force-static';
}

// Navigation Item
export interface NavItem {
  title: string;
  href: string;
  description?: string;
  icon?: string;
  disabled?: boolean;
  external?: boolean;
  label?: string;
}

// Breadcrumb
export interface BreadcrumbItem {
  title: string;
  href?: string;
  current?: boolean;
}

// Route Groups
export type RouteGroup = 'public' | 'protected' | 'admin' | 'api';

// Authentication State
export interface AuthState {
  isAuthenticated: boolean;
  user?: {
    id: string;
    email: string;
    role: string;
    profile?: {
      firstName: string;
      lastName: string;
      avatar?: string;
    };
  };
  loading: boolean;
}

// Locale Configuration
export interface LocaleConfig {
  locale: string;
  label: string;
  default?: boolean;
}

// SEO Metadata
export interface SEOData {
  title: string;
  description: string;
  keywords?: string[];
  ogImage?: string;
  canonical?: string;
  alternates?: {
    canonical?: string;
    languages?: Record<string, string>;
  };
}

// Error Types
export interface RouteError {
  status: number;
  message: string;
  digest?: string;
}

// Loading State
export interface LoadingState {
  page?: boolean;
  component?: string;
  skeleton?: boolean;
}