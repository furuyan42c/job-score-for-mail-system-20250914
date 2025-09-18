# Job Matching System - Routing Architecture

## Overview

This document describes the comprehensive routing architecture for the Job Matching System built with Next.js 14 App Router and TypeScript. The architecture focuses on performance, SEO, internationalization, and user experience.

## Route Structure

### Public Routes (Unauthenticated)

```
/                      → Landing page (SSG + ISR)
/jobs                  → Job listing (SSG + ISR)
/jobs/[id]            → Job detail (SSR)
/jobs/search          → Advanced search (CSR)
/companies            → Company listing (SSG + ISR)
/companies/[id]       → Company profile (SSR)
/about                → About page (SSG)
/contact             → Contact form (SSG)
/privacy             → Privacy policy (SSG)
/terms               → Terms of service (SSG)
```

### Protected Routes (Authentication Required)

```
/dashboard            → User dashboard (SSR)
/profile              → User profile (SSR)
/profile/edit         → Edit profile (SSR)
/preferences          → User preferences (SSR)
/recommendations      → Personalized jobs (SSR)
/applied              → Applied jobs (SSR)
/saved                → Saved jobs (SSR)
/history              → Action history (SSR)
/settings             → Account settings (SSR)
```

### API Routes

```
/api/auth/[...nextauth]  → NextAuth.js authentication
/api/jobs                → Job CRUD operations
/api/jobs/[id]          → Individual job operations
/api/users              → User management
/api/scores             → Score calculation
/api/actions            → Action tracking
/api/upload             → File upload handling
/api/analytics          → Performance analytics
```

## Directory Structure

```
frontend/
├── app/
│   ├── (public)/               # Public route group
│   │   ├── layout.tsx         # Public layout
│   │   ├── page.tsx          # Landing page
│   │   ├── jobs/
│   │   │   ├── page.tsx      # Job listing
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx  # Job detail
│   │   │   └── search/
│   │   │       └── page.tsx  # Advanced search
│   │   ├── companies/
│   │   │   ├── page.tsx      # Company listing
│   │   │   └── [id]/
│   │   │       └── page.tsx  # Company profile
│   │   ├── about/
│   │   │   └── page.tsx      # About page
│   │   ├── contact/
│   │   │   └── page.tsx      # Contact form
│   │   ├── privacy/
│   │   │   └── page.tsx      # Privacy policy
│   │   └── terms/
│   │       └── page.tsx      # Terms of service
│   ├── (protected)/           # Protected route group
│   │   ├── layout.tsx        # Protected layout
│   │   ├── dashboard/
│   │   │   └── page.tsx      # User dashboard
│   │   ├── profile/
│   │   │   ├── page.tsx      # User profile
│   │   │   └── edit/
│   │   │       └── page.tsx  # Edit profile
│   │   ├── preferences/
│   │   │   └── page.tsx      # User preferences
│   │   ├── recommendations/
│   │   │   └── page.tsx      # Personalized jobs
│   │   ├── applied/
│   │   │   └── page.tsx      # Applied jobs
│   │   ├── saved/
│   │   │   └── page.tsx      # Saved jobs
│   │   ├── history/
│   │   │   └── page.tsx      # Action history
│   │   └── settings/
│   │       └── page.tsx      # Account settings
│   ├── api/
│   │   ├── auth/
│   │   │   └── [...nextauth]/
│   │   │       └── route.ts  # NextAuth handler
│   │   ├── jobs/
│   │   │   ├── route.ts      # Jobs CRUD
│   │   │   └── [id]/
│   │   │       └── route.ts  # Individual job
│   │   ├── users/
│   │   │   └── route.ts      # User management
│   │   ├── scores/
│   │   │   └── route.ts      # Score calculation
│   │   ├── actions/
│   │   │   └── route.ts      # Action tracking
│   │   └── upload/
│   │       └── route.ts      # File upload
│   ├── layout.tsx            # Root layout
│   ├── error.tsx             # Global error boundary
│   ├── not-found.tsx         # 404 page
│   ├── loading.tsx           # Global loading
│   ├── sitemap.ts            # Dynamic sitemap
│   └── robots.ts             # Robots.txt
├── middleware.ts             # Request middleware
├── types/
│   └── routing.ts           # Routing TypeScript types
└── lib/
    ├── i18n/               # Internationalization
    │   ├── config.ts      # Locale configuration
    │   └── utils.ts       # i18n utilities
    └── utils/
        └── performance.ts  # Performance utilities
```

## Key Features

### 1. Middleware (`middleware.ts`)

The middleware handles:
- **Authentication checks** for protected routes
- **Rate limiting** for API routes
- **Locale detection** and redirects
- **Security headers** injection
- **Request logging** for monitoring

```typescript
// Protected routes check
const isProtectedRoute = protectedRoutes.some(route =>
  pathWithoutLocale.startsWith(route)
);

// Rate limiting
if (!rateLimit(identifier)) {
  return new NextResponse('Too many requests', { status: 429 });
}
```

### 2. Route Groups

**Public Routes `(public)/`:**
- No authentication required
- Optimized for SEO with SSG/ISR
- Public header/footer layout
- Search engine friendly

**Protected Routes `(protected)/`:**
- Authentication required via middleware
- Dashboard-style layout with sidebar
- User-specific content
- Dynamic rendering (SSR)

### 3. Data Fetching Strategies

**Static Generation (SSG):**
- Landing page
- About, Privacy, Terms pages
- Job/Company listings (with ISR)

**Server-Side Rendering (SSR):**
- Job detail pages
- Company profiles
- User dashboard and protected pages

**Incremental Static Regeneration (ISR):**
- Job listings (revalidate every 5 minutes)
- Company listings (revalidate every hour)
- Landing page (revalidate every hour)

**Client-Side Rendering (CSR):**
- Search interfaces
- Interactive components
- Real-time features

### 4. SEO Optimization

**Metadata Configuration:**
```typescript
export const metadata: Metadata = {
  title: {
    default: 'JobMatch Pro - AI-Powered Job Matching Platform',
    template: '%s | JobMatch Pro',
  },
  description: 'Find your perfect job match...',
  keywords: ['job matching', 'AI recruitment', ...],
  openGraph: { /* OpenGraph config */ },
  twitter: { /* Twitter card config */ },
  alternates: { /* Language alternates */ },
};
```

**Dynamic Sitemap:**
- Automatically generated from database
- Multi-language support
- Includes all public pages
- Updates every 24 hours

**Structured Data:**
- Organization schema
- JobPosting schema
- BreadcrumbList schema
- WebSite schema with search action

### 5. Internationalization

**Supported Locales:**
- English (en) - Default
- Japanese (ja)
- Spanish (es)
- French (fr)
- German (de)

**Implementation:**
```typescript
// Locale detection in middleware
const locale = acceptLanguage
  .split(',')[0]
  ?.split('-')[0]
  ?.toLowerCase();

// URL structure: /[locale]/[...path]
// Example: /ja/jobs, /es/empresas
```

### 6. Performance Optimizations

**Bundle Optimization:**
- Route-based code splitting
- Dynamic imports for non-critical components
- Webpack optimization for chunks

**Caching Strategy:**
```typescript
// Static assets: 1 year cache
'Cache-Control': 'public, max-age=31536000, immutable'

// API responses: 5 minutes cache with stale-while-revalidate
'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600'

// Dynamic pages: ISR with appropriate revalidation
export const revalidate = 300; // 5 minutes
```

**Image Optimization:**
- Next.js Image component
- WebP/AVIF formats
- Responsive images with srcSet
- Lazy loading by default

### 7. Error Handling

**Global Error Boundary:**
- Production-friendly error messages
- Development error details
- Error reporting to monitoring services
- Fallback UI with recovery options

**404 Page:**
- Helpful navigation suggestions
- Search functionality
- Popular page links

**API Error Handling:**
- Structured error responses
- Rate limiting errors
- Authentication errors
- Validation errors

### 8. TypeScript Integration

**Route Type Safety:**
```typescript
interface PageProps {
  params: RouteParams;
  searchParams: SearchParams;
}

interface RouteParams {
  id: string;
  slug?: string;
  locale?: string;
}
```

**API Route Types:**
```typescript
// Validation schemas with Zod
const getJobsSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  // ...
});
```

## Security Features

### 1. Content Security Policy
- Strict CSP headers in middleware
- Protection against XSS attacks
- Safe external resource loading

### 2. Rate Limiting
- API route protection
- IP-based limiting
- Different limits for different endpoints

### 3. Authentication
- NextAuth.js integration
- JWT token validation
- Role-based access control

### 4. Data Validation
- Zod schema validation
- Input sanitization
- Type-safe API contracts

## Monitoring and Analytics

### 1. Performance Monitoring
- Core Web Vitals tracking
- Navigation timing
- Resource loading metrics
- Custom performance markers

### 2. Error Tracking
- Global error boundary
- API error logging
- Client-side error reporting

### 3. User Analytics
- Page view tracking
- User journey analysis
- Conversion funnel monitoring

## Deployment Considerations

### 1. Environment Configuration
- Environment-specific settings
- Feature flags
- API endpoint configuration

### 2. CDN Integration
- Static asset caching
- Image optimization
- Global distribution

### 3. Database Optimization
- Connection pooling
- Query optimization
- Caching strategies

## Future Enhancements

### 1. Advanced Features
- Real-time notifications
- WebSocket integration
- Progressive Web App (PWA)

### 2. Performance Improvements
- Edge computing
- Micro-frontends
- Service workers

### 3. Accessibility
- WCAG 2.1 AA compliance
- Screen reader optimization
- Keyboard navigation

## Development Guidelines

### 1. Code Organization
- Feature-based folder structure
- Shared component library
- Utility function organization

### 2. Testing Strategy
- Unit tests for utilities
- Integration tests for API routes
- E2E tests for critical flows

### 3. Code Quality
- ESLint configuration
- Prettier formatting
- TypeScript strict mode

This routing architecture provides a solid foundation for a scalable, performant, and SEO-friendly job matching platform while maintaining excellent developer experience and code quality.