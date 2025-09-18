# API Client Service

A comprehensive API client for the Job Matching System frontend, built with TypeScript, Axios, Zod validation, and React Query integration.

## Features

- ✅ **Type-safe API calls** with full TypeScript support
- ✅ **Request/Response validation** using Zod schemas
- ✅ **Authentication handling** with automatic token injection
- ✅ **Error handling and retry logic** with exponential backoff
- ✅ **Request caching** with configurable TTL
- ✅ **Request debouncing** for search operations
- ✅ **File upload support** with progress tracking
- ✅ **Request cancellation** for better UX
- ✅ **React Query hooks** for easy integration
- ✅ **Optimistic updates** for better responsiveness
- ✅ **Polling capabilities** for real-time data
- ✅ **Comprehensive testing** with mocked responses

## Quick Start

### Basic Usage

```typescript
import { apiClient } from '@/services';

// Direct API calls
const jobs = await apiClient.searchJobs({
  title: 'developer',
  location: 'New York'
});

const score = await apiClient.calculateScore('user-123', 'job-456');
const health = await apiClient.getHealthCheck();
```

### React Query Hooks

```typescript
import { useSearchJobs, useCalculateScore, useHealthCheck } from '@/services';

function JobSearch() {
  const { data: jobs, isLoading, error } = useSearchJobs({
    title: 'developer',
    skills: ['JavaScript', 'React'],
    page: 1,
    limit: 10
  });

  const calculateScore = useCalculateScore();
  const { data: health } = useHealthCheck();

  const handleCalculateScore = async (userId: string, jobId: string) => {
    try {
      const result = await calculateScore.mutateAsync({ userId, jobId });
      console.log('Score calculated:', result);
    } catch (error) {
      console.error('Failed to calculate score:', error);
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <div>System Status: {health?.status}</div>
      {jobs?.jobs.map(job => (
        <div key={job.id}>
          <h3>{job.title}</h3>
          <p>{job.company}</p>
          <button onClick={() => handleCalculateScore('user-123', job.id)}>
            Calculate Score
          </button>
        </div>
      ))}
    </div>
  );
}
```

## API Operations

### Batch Operations

```typescript
// Trigger batch job
const batch = await apiClient.triggerBatch('scoring');

// Monitor batch status with polling
const { data: status } = usePollingBatchStatus(batch.id);

// Cancel batch job
await apiClient.cancelBatch(batch.id);
```

### Job Operations

```typescript
// Import jobs from file
const file = new File(['csv data'], 'jobs.csv');
const result = await apiClient.importJobs(file, {
  onProgress: (progress) => console.log(`Upload progress: ${progress}%`)
});

// Search jobs with filters
const jobs = await apiClient.searchJobs({
  title: 'developer',
  skills: ['JavaScript', 'React'],
  salary: { min: 80000, max: 120000 },
  locationType: ['remote', 'hybrid']
});

// Export jobs
const blob = await apiClient.exportJobs({ title: 'developer' });
```

### Scoring Operations

```typescript
// Calculate individual score
const score = await apiClient.calculateScore('user-123', 'job-456');

// Batch calculate scores
const batchResult = await apiClient.batchCalculateScores(['user-1', 'user-2']);

// Get score history
const history = await apiClient.getScoreHistory('user-123', { page: 1, limit: 10 });
```

### Matching Operations

```typescript
// Generate matching for user
const matching = await apiClient.generateMatching('user-123', {
  forceRefresh: true
});

// Get user matches
const matches = await apiClient.getUserMatches('user-123');

// Update match status with optimistic updates
const updateStatus = useOptimisticMatchStatus();
await updateStatus.mutateAsync({ matchId: 'match-123', status: 'viewed' });
```

### Email Operations

```typescript
// Generate email preview
const preview = await apiClient.generateEmail('user-123', {
  includeMatches: 5
});

// Send test email
await apiClient.sendTestEmail('user-123');

// Schedule email campaign
const campaign = await apiClient.scheduleEmailCampaign(['user-1', 'user-2']);
```

### SQL Operations

```typescript
// Execute SQL query
const result = await apiClient.executeQuery(
  'SELECT * FROM jobs WHERE salary > ?',
  [80000]
);

// Save query for reuse
await apiClient.saveQuery('High Salary Jobs', 'SELECT * FROM jobs WHERE salary > 80000');

// Get saved queries
const savedQueries = await apiClient.getSavedQueries();
```

### Monitoring Operations

```typescript
// Get system metrics
const metrics = await apiClient.getMetrics('24h');

// Health check with polling
const { data: health } = usePollingHealth();

// Get system logs
const logs = await apiClient.getSystemLogs({
  level: 'error',
  service: 'api'
});
```

## Advanced Features

### File Upload with Progress

```typescript
const uploadJobs = useImportJobs();

const handleFileUpload = async (file: File) => {
  try {
    const result = await uploadJobs.mutateAsync({
      file,
      options: {
        onProgress: (progress) => {
          console.log(`Upload progress: ${progress}%`);
        },
        maxSize: 10 * 1024 * 1024, // 10MB
        allowedTypes: ['text/csv', 'application/json']
      }
    });
    console.log('Upload completed:', result);
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

### Request Debouncing

```typescript
// Search requests are automatically debounced
const { data: jobs } = useSearchJobs({
  title: searchTerm, // This will be debounced automatically
  page: 1,
  limit: 10
});
```

### Caching and Cache Management

```typescript
const { clearCache } = useApiClient();

// Clear specific cache pattern
clearCache('jobs');

// Clear all cache
clearCache();

// Configure cache timeout
const client = new ApiClient({
  baseURL: 'http://localhost:8000',
  enableCaching: true,
  cacheTimeout: 10 * 60 * 1000, // 10 minutes
});
```

### Request Cancellation

```typescript
const { cancelRequests } = useApiClient();

// Cancel specific request
cancelRequests('search-jobs');

// Cancel all requests
cancelRequests();
```

### Error Handling

```typescript
import { ApiError, ValidationError, NetworkError } from '@/services';

try {
  const result = await apiClient.searchJobs(filters);
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.status, error.message);
  } else if (error instanceof ValidationError) {
    console.error('Validation Error:', error.errors);
  } else if (error instanceof NetworkError) {
    console.error('Network Error:', error.code);
  }
}
```

### Optimistic Updates

```typescript
const updateMatchStatus = useOptimisticMatchStatus();

const handleStatusChange = async (matchId: string, status: string) => {
  // UI updates immediately, reverts on error
  await updateMatchStatus.mutateAsync({ matchId, status });
};
```

### Infinite Queries

```typescript
const {
  data: jobPages,
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage
} = useInfiniteJobSearch({ title: 'developer' });

const allJobs = jobPages?.pages.flatMap(page => page.jobs) ?? [];
```

### Prefetching

```typescript
const prefetchJob = usePrefetchJob();
const prefetchProfile = usePrefetchUserProfile();

// Prefetch data on hover
const handleJobHover = (jobId: string) => {
  prefetchJob(jobId);
};

const handleUserHover = (userId: string) => {
  prefetchProfile(userId);
};
```

## Configuration

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Client Configuration

```typescript
const client = new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableLogging: process.env.NODE_ENV === 'development',
  enableCaching: true,
  cacheTimeout: 5 * 60 * 1000, // 5 minutes
});
```

## Testing

The API client comes with comprehensive test coverage:

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Mock Usage in Tests

```typescript
import { createMockApiClient, mockApiResponses } from '@/services/__tests__/api-client.test';

const { client, mockAdapter } = createMockApiClient();

mockAdapter.onGet('/api/jobs/search').reply(200, {
  jobs: mockApiResponses.jobs,
  pagination: { page: 1, limit: 10, total: 1, pages: 1 }
});
```

## Type Safety

All API methods are fully typed with TypeScript and validated with Zod schemas:

```typescript
// TypeScript will enforce correct types
const score: Score = await apiClient.calculateScore('user-123', 'job-456');

// Zod validation ensures runtime type safety
const batchJob: BatchJob = await apiClient.triggerBatch('scoring');
```

## Error Recovery

The client includes automatic retry logic and graceful error recovery:

- **Network errors**: Automatic retry with exponential backoff
- **Server errors (5xx)**: Automatic retry up to configured limit
- **Client errors (4xx)**: No retry, immediate error response
- **Validation errors**: No retry, detailed error information
- **Timeout errors**: Configurable timeout with retry

## Performance Optimizations

- **Request deduplication**: Identical requests are automatically deduplicated
- **Intelligent caching**: GET requests cached with configurable TTL
- **Request debouncing**: Search operations debounced to reduce server load
- **Connection pooling**: HTTP connection reuse for better performance
- **Compression**: Automatic gzip compression support

## Security Features

- **Authentication**: Automatic token injection from localStorage
- **Token refresh**: Automatic handling of expired tokens
- **CSRF protection**: Built-in CSRF token handling
- **Input validation**: All inputs validated before sending
- **Output validation**: All responses validated before returning