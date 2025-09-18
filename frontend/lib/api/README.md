# API Client Infrastructure

A comprehensive API client infrastructure for the Job Matching System, built with Supabase, TypeScript, and React Query.

## 📁 File Structure

```
frontend/lib/api/
├── README.md           # This documentation
├── index.ts           # Main exports and utilities
├── supabase.ts        # Supabase client configuration
├── types.ts           # TypeScript type definitions
├── client.ts          # API client implementation
├── hooks.ts           # React Query hooks
└── config.ts          # Configuration and environment management
```

## 🚀 Quick Start

### Basic Setup

```typescript
import { apiClient } from '@/lib/api';

// Search for jobs
const jobs = await apiClient.searchJobs({
  title: 'Software Engineer',
  location: { pref_cd: '13' }, // Tokyo
  salary: { min_amount: 5000000 },
});

// Get user recommendations
const recommendations = await apiClient.getRecommendedJobs(userId, 10, 0.7);
```

### Using React Hooks

```typescript
import { useJobSearch, useBatchStatus, useRecommendedJobs } from '@/lib/api';

function JobSearchComponent() {
  const { data: jobs, isLoading, error } = useJobSearch({
    title: 'Engineer',
    employment_types: ['full_time'],
  });

  const { data: recommendations } = useRecommendedJobs(userId);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {jobs?.data?.map(job => (
        <JobCard key={job.job_id} job={job} />
      ))}
    </div>
  );
}
```

## 🏗️ Architecture Overview

### Core Components

1. **Supabase Client** (`supabase.ts`)
   - Browser and server-side clients
   - Authentication management
   - Real-time subscriptions
   - Service role client for admin operations

2. **API Client** (`client.ts`)
   - Comprehensive API methods
   - Error handling and retry logic
   - Response caching
   - Rate limiting consideration

3. **Type System** (`types.ts`)
   - Full TypeScript coverage
   - Database schema types
   - API request/response types
   - Error type definitions

4. **React Hooks** (`hooks.ts`)
   - React Query integration
   - Real-time updates
   - Optimistic updates
   - Pagination support

5. **Configuration** (`config.ts`)
   - Environment validation
   - Feature flags
   - Security settings
   - Performance tuning

## 📊 API Client Features

### Batch Operations

```typescript
// Trigger a new batch execution
const batch = await apiClient.triggerBatch('scoring_calculation', {
  user_ids: [1, 2, 3],
  recalculate: true
});

// Monitor batch progress with real-time updates
const { data: batchStatus } = useBatchStatus(batch.batch_id);

// Cancel a running batch
await apiClient.cancelBatch(batch.batch_id);
```

### Job Management

```typescript
// Import jobs from CSV
const importResult = await apiClient.importJobs({
  file: csvFile,
  batch_size: 1000,
  validate_only: false
});

// Advanced job search
const jobs = await apiClient.searchJobs({
  title: 'Developer',
  company: 'Tech Corp',
  location: {
    pref_cd: '13',
    radius_km: 50
  },
  salary: {
    min_amount: 4000000,
    max_amount: 8000000
  },
  employment_types: ['full_time', 'contract'],
  remote_work: true,
  posted_after: '2024-01-01'
});

// Update job information
const updatedJob = await apiClient.updateJob(jobId, {
  title: 'Senior Software Engineer',
  salary: {
    min_amount: 6000000,
    max_amount: 10000000,
    currency: 'JPY',
    period: 'yearly'
  }
});
```

### Scoring System

```typescript
// Calculate scores for specific users
const scoringResult = await apiClient.calculateScores({
  user_ids: [1, 2, 3],
  weights: {
    location_weight: 0.2,
    salary_weight: 0.3,
    skills_weight: 0.5
  },
  min_score_threshold: 0.6
});

// Get user scores with pagination
const { data: scores } = useUserScores(userId, {
  page: 1,
  per_page: 20,
  sort_by: 'total_score',
  sort_order: 'desc'
});

// Get personalized job recommendations
const recommendations = await apiClient.getRecommendedJobs(
  userId,
  10,    // limit
  0.7    // minimum score
);
```

### Monitoring and Analytics

```typescript
// Execute custom SQL queries (admin only)
const queryResult = await apiClient.executeSQL(`
  SELECT
    AVG(total_score) as avg_score,
    COUNT(*) as total_scores
  FROM scores
  WHERE calculated_at > NOW() - INTERVAL '24 hours'
`);

// Get system metrics
const metrics = await apiClient.getSystemMetrics(
  '2024-01-01',  // start date
  '2024-01-31'   // end date
);

// Stream system logs in real-time
const { logs, refresh } = useSystemLogs({
  level: ['ERROR', 'WARNING'],
  component: ['scoring', 'email'],
  limit: 100
}, true); // enable real-time streaming
```

### Email Operations

```typescript
// Preview personalized email for user
const preview = await apiClient.previewEmail(userId);

// Send email to user
const emailJob = await apiClient.sendEmail(userId, '2024-01-15T10:00:00Z');

// Monitor email delivery status
const { data: emailStatus } = useEmailJob(emailJob.email_id);
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file with the following variables:

```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Optional - Server-side only
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Application
NEXT_PUBLIC_APP_NAME="Job Matching System"
NEXT_PUBLIC_APP_VERSION="1.0.0"
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature flags
NEXT_PUBLIC_ENABLE_REALTIME=true
NEXT_PUBLIC_ENABLE_CACHING=true
NEXT_PUBLIC_ENABLE_DEBUG_MODE=false

# Rate limiting
RATE_LIMIT_BATCH_OPERATIONS=5
RATE_LIMIT_SCORING_REQUESTS=10
RATE_LIMIT_EMAIL_SENDS=100

# Cache configuration (in seconds)
CACHE_TTL_SHORT=30
CACHE_TTL_MEDIUM=300
CACHE_TTL_LONG=1800
```

### Feature Flags

```typescript
import { isFeatureEnabled } from '@/lib/api/config';

if (isFeatureEnabled('realtime')) {
  // Enable real-time features
}

if (isFeatureEnabled('analytics')) {
  // Enable analytics tracking
}
```

## 🔄 Real-time Features

### Batch Status Updates

```typescript
import { useBatchStatus } from '@/lib/api';

function BatchMonitor({ batchId }) {
  const { data: batch } = useBatchStatus(batchId);

  return (
    <div>
      <div>Status: {batch?.status}</div>
      <div>Progress: {batch?.progress_percentage}%</div>
      <div>Phase: {batch?.phase}</div>
    </div>
  );
}
```

### Live Log Streaming

```typescript
import { useSystemLogs } from '@/lib/api';

function LogViewer() {
  const { logs, isLoading } = useSystemLogs(
    { level: ['ERROR', 'WARNING'] },
    true // enable real-time
  );

  return (
    <div>
      {logs.map(log => (
        <LogEntry key={log.log_id} log={log} />
      ))}
    </div>
  );
}
```

## 🛡️ Error Handling

### Error Types

```typescript
import {
  APIError,
  ValidationError,
  AuthenticationError,
  NotFoundError
} from '@/lib/api';

try {
  await apiClient.searchJobs(params);
} catch (error) {
  if (error instanceof ValidationError) {
    // Handle validation errors
    console.error('Validation failed:', error.details);
  } else if (error instanceof AuthenticationError) {
    // Handle auth errors
    redirectToLogin();
  } else if (error instanceof NotFoundError) {
    // Handle not found
    showNotFoundMessage();
  } else {
    // Handle generic errors
    showGenericError(error.message);
  }
}
```

### Automatic Retry Logic

The API client automatically retries failed requests with exponential backoff:

```typescript
const retryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2
};

// Non-retryable errors:
// - AuthenticationError
// - ValidationError
// - NotFoundError
// - RateLimitError
```

## 📱 Responsive Caching

### Cache Strategy

```typescript
// Short-term cache (30 seconds)
// - Batch statuses
// - System logs
// - Real-time data

// Medium-term cache (5 minutes)
// - Search results
// - User scores
// - System metrics

// Long-term cache (30 minutes)
// - Individual jobs/users
// - Master data
// - Configuration data
```

### Cache Management

```typescript
import { apiClient } from '@/lib/api';

// Clear all caches
apiClient.clearCache();

// Invalidate specific cache patterns
apiClient.invalidateCache('jobs-search');
apiClient.invalidateCache('user-\\d+');
```

## 🔒 Security Features

### Authentication

```typescript
import { AuthManager } from '@/lib/api';

// Check current user
const { user, error } = await AuthManager.getCurrentUser();

// Sign in
await AuthManager.signIn(email, password);

// Listen to auth changes
AuthManager.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    // User signed in
  } else if (event === 'SIGNED_OUT') {
    // User signed out
  }
});
```

### Row Level Security (RLS)

Supabase RLS policies are automatically enforced:

- Users can only access their own data
- Admin users have elevated permissions
- Public data is read-only for anonymous users

### Rate Limiting

Built-in rate limiting protection:

```typescript
// Automatic rate limiting based on configuration
const rateLimits = {
  batchOperations: 5,   // per minute
  scoringRequests: 10,  // per minute
  emailSends: 100,      // per hour
};
```

## 📊 Performance Optimization

### Parallel Operations

```typescript
// Execute multiple independent operations in parallel
const [jobs, users, metrics] = await Promise.all([
  apiClient.searchJobs(jobParams),
  apiClient.searchUsers(userParams),
  apiClient.getSystemMetrics()
]);
```

### Optimistic Updates

```typescript
import { useOptimisticUpdate } from '@/lib/api';

const updateJob = useOptimisticUpdate(
  ['jobs', jobId],
  (oldJob, updates) => ({ ...oldJob, ...updates })
);

await updateJob(updates, () => apiClient.updateJob(jobId, updates));
```

### Pagination

```typescript
import { usePagination } from '@/lib/api';

function JobList() {
  const { page, pageSize, goToPage, nextPage, prevPage } = usePagination();

  const { data: jobs } = useJobSearch({
    page,
    per_page: pageSize
  });

  return (
    <div>
      <JobGrid jobs={jobs?.data} />
      <Pagination
        page={page}
        totalPages={jobs?.meta?.total_pages}
        onPageChange={goToPage}
        onNext={nextPage}
        onPrev={prevPage}
      />
    </div>
  );
}
```

## 🧪 Testing

### Mock Data

```typescript
import { apiClient } from '@/lib/api';

// In test environment, use mock client
if (process.env.NODE_ENV === 'test') {
  // Mock API responses
  jest.mock('@/lib/api', () => ({
    apiClient: {
      searchJobs: jest.fn().mockResolvedValue(mockJobs),
      getUser: jest.fn().mockResolvedValue(mockUser),
    }
  }));
}
```

### Error Testing

```typescript
import { APIError, ValidationError } from '@/lib/api';

// Test error handling
const mockError = new ValidationError('Invalid data', {
  field: 'email',
  code: 'INVALID_FORMAT'
});

expect(() => {
  throw mockError;
}).toThrow(ValidationError);
```

## 📈 Monitoring and Debugging

### Development Tools

```typescript
import { getConfigSummary } from '@/lib/api/config';

// Debug configuration
console.log('API Config:', getConfigSummary());

// Monitor API calls in development
if (process.env.NODE_ENV === 'development') {
  apiClient.enableDebugMode();
}
```

### Performance Monitoring

```typescript
// Track API call performance
const startTime = performance.now();
const result = await apiClient.searchJobs(params);
const duration = performance.now() - startTime;

console.log(`Search completed in ${duration}ms`);
```

## 🔧 Troubleshooting

### Common Issues

1. **Environment Variables Missing**
   ```
   Error: Environment validation failed: NEXT_PUBLIC_SUPABASE_URL is required
   ```
   Solution: Check `.env.local` file and ensure all required variables are set.

2. **Authentication Errors**
   ```
   AuthenticationError: Invalid credentials
   ```
   Solution: Verify Supabase keys and user permissions.

3. **Rate Limiting**
   ```
   RateLimitError: Rate limit exceeded
   ```
   Solution: Implement proper debouncing and respect rate limits.

4. **Cache Issues**
   ```
   Stale data being displayed
   ```
   Solution: Clear cache or adjust TTL values.

### Debug Mode

Enable debug mode in development:

```typescript
NEXT_PUBLIC_ENABLE_DEBUG_MODE=true
```

This enables:
- Detailed error logging
- API call timing
- Cache hit/miss tracking
- Real-time subscription monitoring

## 📚 API Reference

For detailed API method documentation, see the TypeScript definitions in `types.ts` and method implementations in `client.ts`.

### Key Interfaces

- `Job` - Job entity with all fields
- `User` - User entity with preferences
- `Score` - Scoring result with breakdown
- `BatchExecution` - Batch process status
- `ApiResponse<T>` - Standardized API response

### Hook Reference

- `useJobSearch()` - Search jobs with filters
- `useUser()` - Get user by ID
- `useBatchStatus()` - Monitor batch execution
- `useSystemLogs()` - Stream system logs
- `useEmailPreview()` - Preview email content

---

For more examples and advanced usage, see the component implementations in the `app/` directory.