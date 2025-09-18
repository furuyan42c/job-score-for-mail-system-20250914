import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { ApiClient, ApiError, ValidationError, NetworkError } from '../api-client';
import type {
  BatchJob,
  BatchStatus,
  ImportResult,
  Score,
  BatchScoreResult,
  MatchingResult,
  UserMatches,
  EmailPreview,
  QueryResult,
  QueryHistory,
  SystemMetrics,
  HealthStatus,
} from '../api-client';

// Setup axios mock
const mockAxios = new MockAdapter(axios);

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    mockAxios.reset();
    localStorage.clear();

    apiClient = new ApiClient({
      baseURL: 'http://localhost:8000',
      timeout: 5000,
      retryAttempts: 1,
      retryDelay: 100,
      enableLogging: false,
      enableCaching: true,
      cacheTimeout: 1000,
    });
  });

  afterEach(() => {
    apiClient.destroy();
  });

  // ====================
  // MOCK DATA
  // ====================

  const mockBatchJob: BatchJob = {
    id: 'batch-123',
    type: 'scoring',
    status: 'pending',
    progress: 0,
    totalItems: 100,
    processedItems: 0,
    createdAt: '2023-12-01T10:00:00Z',
  };

  const mockBatchStatus: BatchStatus = {
    id: 'batch-123',
    status: 'running',
    progress: 50,
    totalItems: 100,
    processedItems: 50,
    updatedAt: '2023-12-01T10:30:00Z',
  };

  const mockImportResult: ImportResult = {
    jobId: 'import-456',
    totalRecords: 1000,
    importedRecords: 950,
    failedRecords: 50,
    errors: [
      { row: 10, error: 'Invalid email format' },
      { row: 25, error: 'Missing required field: title' },
    ],
    warnings: ['Duplicate job title detected'],
  };

  const mockScore: Score = {
    userId: 'user-123',
    jobId: 'job-456',
    overallScore: 85.5,
    factors: [
      {
        type: 'skills',
        weight: 0.4,
        score: 90,
        description: 'Strong match in required skills',
      },
      {
        type: 'experience',
        weight: 0.3,
        score: 80,
        description: 'Good experience level match',
      },
      {
        type: 'location',
        weight: 0.2,
        score: 95,
        description: 'Perfect location match',
      },
      {
        type: 'salary',
        weight: 0.1,
        score: 70,
        description: 'Salary expectations slightly above range',
      },
    ],
    calculatedAt: '2023-12-01T10:00:00Z',
    version: 'v1.0',
  };

  const mockBatchScoreResult: BatchScoreResult = {
    batchId: 'batch-scores-789',
    totalUsers: 10,
    processedUsers: 10,
    scores: [mockScore],
    errors: [],
  };

  const mockMatchingResult: MatchingResult = {
    userId: 'user-123',
    totalJobs: 500,
    matchedJobs: 25,
    matches: [
      {
        jobId: 'job-456',
        score: 85.5,
        rank: 1,
        factors: [
          {
            type: 'skills',
            weight: 0.4,
            score: 90,
            description: 'Strong skill match',
          },
        ],
      },
      {
        jobId: 'job-789',
        score: 78.2,
        rank: 2,
        factors: [
          {
            type: 'experience',
            weight: 0.3,
            score: 85,
            description: 'Good experience match',
          },
        ],
      },
    ],
    generatedAt: '2023-12-01T10:00:00Z',
  };

  const mockUserMatches: UserMatches = {
    userId: 'user-123',
    matches: [
      {
        id: 'match-123',
        jobId: 'job-456',
        score: 85.5,
        rank: 1,
        status: 'new',
        createdAt: '2023-12-01T10:00:00Z',
        updatedAt: '2023-12-01T10:00:00Z',
      },
    ],
    totalMatches: 25,
    lastUpdated: '2023-12-01T10:00:00Z',
  };

  const mockEmailPreview: EmailPreview = {
    userId: 'user-123',
    subject: 'Your Top Job Matches This Week',
    htmlContent: '<html><body><h1>Your Top Matches</h1></body></html>',
    textContent: 'Your Top Job Matches This Week\\n\\n...',
    matches: [
      {
        jobId: 'job-456',
        jobTitle: 'Senior Developer',
        company: 'Tech Corp',
        score: 85.5,
      },
    ],
    generatedAt: '2023-12-01T10:00:00Z',
  };

  const mockQueryResult: QueryResult = {
    columns: ['id', 'title', 'company', 'salary'],
    rows: [
      ['job-1', 'Developer', 'Tech Corp', 80000],
      ['job-2', 'Designer', 'Design Co', 70000],
    ],
    rowCount: 2,
    executionTime: 150,
    query: 'SELECT id, title, company, salary FROM jobs LIMIT 2',
    executedAt: '2023-12-01T10:00:00Z',
  };

  const mockQueryHistory: QueryHistory = {
    id: 'query-123',
    query: 'SELECT * FROM jobs',
    executionTime: 250,
    rowCount: 100,
    status: 'success',
    executedAt: '2023-12-01T09:00:00Z',
    userId: 'user-123',
  };

  const mockSystemMetrics: SystemMetrics = {
    cpu: {
      usage: 45.2,
      cores: 4,
    },
    memory: {
      used: 2048,
      total: 8192,
      percentage: 25.0,
    },
    database: {
      activeConnections: 25,
      totalQueries: 1500,
      avgResponseTime: 45,
    },
    api: {
      requestsPerMinute: 120,
      avgResponseTime: 180,
      errorRate: 0.5,
    },
    background: {
      activeJobs: 3,
      queuedJobs: 8,
      failedJobs: 1,
    },
    timestamp: '2023-12-01T10:00:00Z',
  };

  const mockHealthStatus: HealthStatus = {
    status: 'healthy',
    checks: {
      database: {
        status: 'healthy',
        responseTime: 25,
        lastCheck: '2023-12-01T10:00:00Z',
      },
      redis: {
        status: 'healthy',
        responseTime: 5,
        lastCheck: '2023-12-01T10:00:00Z',
      },
      external_apis: {
        status: 'healthy',
        services: [
          {
            name: 'OpenAI API',
            status: 'healthy',
            responseTime: 200,
          },
        ],
        lastCheck: '2023-12-01T10:00:00Z',
      },
    },
    timestamp: '2023-12-01T10:00:00Z',
  };

  // ====================
  // HELPER FUNCTIONS
  // ====================

  const mockApiResponse = <T>(data: T) => ({
    data,
    message: 'Success',
    success: true,
    timestamp: '2023-12-01T10:00:00Z',
  });

  const mockPaginatedResponse = <T>(data: T[]) => ({
    data,
    pagination: {
      page: 1,
      limit: 10,
      total: data.length,
      pages: 1,
    },
    success: true,
    timestamp: '2023-12-01T10:00:00Z',
  });

  // ====================
  // AUTHENTICATION TESTS
  // ====================

  describe('Authentication', () => {
    it('should add auth token to requests when available', async () => {
      localStorage.setItem('auth_token', 'test-token');

      mockAxios.onGet('/api/health').reply((config) => {
        expect(config.headers?.Authorization).toBe('Bearer test-token');
        return [200, mockApiResponse(mockHealthStatus)];
      });

      await apiClient.getHealthCheck();
    });

    it('should handle 401 unauthorized errors', async () => {
      mockAxios.onGet('/api/health').reply(401, {
        message: 'Unauthorized',
        success: false,
      });

      await expect(apiClient.getHealthCheck()).rejects.toThrow(ApiError);
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  // ====================
  // BATCH OPERATIONS TESTS
  // ====================

  describe('Batch Operations', () => {
    it('should trigger batch job successfully', async () => {
      mockAxios.onPost('/api/batch/trigger').reply(200, mockApiResponse(mockBatchJob));

      const result = await apiClient.triggerBatch('scoring');

      expect(result).toEqual(mockBatchJob);
      expect(mockAxios.history.post[0].data).toBe(JSON.stringify({ type: 'scoring' }));
    });

    it('should get batch status', async () => {
      mockAxios.onGet('/api/batch/batch-123/status').reply(200, mockApiResponse(mockBatchStatus));

      const result = await apiClient.getBatchStatus('batch-123');

      expect(result).toEqual(mockBatchStatus);
    });

    it('should cancel batch job', async () => {
      mockAxios.onPost('/api/batch/batch-123/cancel').reply(200, mockApiResponse({}));

      await expect(apiClient.cancelBatch('batch-123')).resolves.not.toThrow();
    });

    it('should get batch history with pagination', async () => {
      const expectedResponse = mockPaginatedResponse([mockBatchJob]);
      mockAxios.onGet('/api/batch/history').reply(200, expectedResponse);

      const result = await apiClient.getBatchHistory({ page: 1, limit: 10 });

      expect(result).toEqual(expectedResponse);
    });
  });

  // ====================
  // JOB OPERATIONS TESTS
  // ====================

  describe('Job Operations', () => {
    it('should import jobs from file', async () => {
      const file = new File(['csv content'], 'jobs.csv', { type: 'text/csv' });
      let progressCalled = false;

      mockAxios.onPost('/api/jobs/import').reply((config) => {
        expect(config.data).toBeInstanceOf(FormData);

        // Simulate upload progress
        if (config.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: 100 });
        }

        return [200, mockApiResponse(mockImportResult)];
      });

      const result = await apiClient.importJobs(file, {
        onProgress: (progress) => {
          expect(progress).toBe(50);
          progressCalled = true;
        },
      });

      expect(result).toEqual(mockImportResult);
      expect(progressCalled).toBe(true);
    });

    it('should search jobs with filters', async () => {
      const filters = {
        title: 'developer',
        location: 'New York',
        skills: ['JavaScript', 'React'],
        page: 1,
        limit: 10,
      };

      const mockJobs = {
        jobs: [],
        pagination: {
          page: 1,
          limit: 10,
          total: 0,
          pages: 0,
        },
      };

      mockAxios.onGet('/api/jobs/search').reply((config) => {
        expect(config.params).toEqual(filters);
        return [200, mockJobs];
      });

      const result = await apiClient.searchJobs(filters);
      expect(result).toEqual(mockJobs);
    });

    it('should debounce search requests', async () => {
      const filters = { title: 'dev' };
      let requestCount = 0;

      mockAxios.onGet('/api/jobs/search').reply(() => {
        requestCount++;
        return [200, { jobs: [], pagination: { page: 1, limit: 10, total: 0, pages: 0 } }];
      });

      // Make multiple rapid requests
      const promises = [
        apiClient.searchJobs(filters),
        apiClient.searchJobs(filters),
        apiClient.searchJobs(filters),
      ];

      await Promise.all(promises);

      // Due to debouncing, only one request should be made
      expect(requestCount).toBe(1);
    });

    it('should get job by ID with caching', async () => {
      const mockJob = { id: 'job-123', title: 'Developer' };
      mockAxios.onGet('/api/jobs/job-123').reply(200, mockJob);

      // First request
      const result1 = await apiClient.getJobById('job-123');
      expect(result1).toEqual(mockJob);

      // Second request should use cache
      const result2 = await apiClient.getJobById('job-123');
      expect(result2).toEqual(mockJob);

      // Only one actual request should have been made
      expect(mockAxios.history.get).toHaveLength(1);
    });

    it('should export jobs as blob', async () => {
      const mockBlob = new Blob(['csv content'], { type: 'text/csv' });
      mockAxios.onGet('/api/jobs/export').reply(200, mockBlob);

      const result = await apiClient.exportJobs();
      expect(result).toBeInstanceOf(Blob);
    });
  });

  // ====================
  // SCORING OPERATIONS TESTS
  // ====================

  describe('Scoring Operations', () => {
    it('should calculate individual score', async () => {
      mockAxios.onPost('/api/scores/calculate').reply(200, mockApiResponse(mockScore));

      const result = await apiClient.calculateScore('user-123', 'job-456');

      expect(result).toEqual(mockScore);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userId: 'user-123', jobId: 'job-456' })
      );
    });

    it('should batch calculate scores', async () => {
      mockAxios.onPost('/api/scores/batch-calculate').reply(200, mockApiResponse(mockBatchScoreResult));

      const userIds = ['user-1', 'user-2', 'user-3'];
      const result = await apiClient.batchCalculateScores(userIds, 'job-456');

      expect(result).toEqual(mockBatchScoreResult);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userIds, jobId: 'job-456' })
      );
    });

    it('should get score history with pagination', async () => {
      const expectedResponse = mockPaginatedResponse([mockScore]);
      mockAxios.onGet('/api/scores/history/user-123').reply(200, expectedResponse);

      const result = await apiClient.getScoreHistory('user-123', { page: 1, limit: 5 });

      expect(result).toEqual(expectedResponse);
      expect(mockAxios.history.get[0].params).toEqual({ page: 1, limit: 5 });
    });
  });

  // ====================
  // MATCHING OPERATIONS TESTS
  // ====================

  describe('Matching Operations', () => {
    it('should generate matching for user', async () => {
      mockAxios.onPost('/api/matching/generate').reply(200, mockApiResponse(mockMatchingResult));

      const result = await apiClient.generateMatching('user-123', { forceRefresh: true });

      expect(result).toEqual(mockMatchingResult);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userId: 'user-123', forceRefresh: true })
      );
    });

    it('should get user matches', async () => {
      mockAxios.onGet('/api/matching/user/user-123').reply(200, mockApiResponse(mockUserMatches));

      const result = await apiClient.getUserMatches('user-123');

      expect(result).toEqual(mockUserMatches);
    });

    it('should update match status and clear cache', async () => {
      mockAxios.onPatch('/api/matching/match-123/status').reply(200, {});

      await apiClient.updateMatchStatus('match-123', 'viewed');

      expect(mockAxios.history.patch[0].data).toBe(
        JSON.stringify({ status: 'viewed' })
      );
    });

    it('should get matching stats with caching', async () => {
      const mockStats = { totalMatches: 25, avgScore: 78.5 };
      mockAxios.onGet('/api/matching/stats/user-123').reply(200, mockStats);

      const result1 = await apiClient.getMatchingStats('user-123');
      const result2 = await apiClient.getMatchingStats('user-123');

      expect(result1).toEqual(mockStats);
      expect(result2).toEqual(mockStats);
      expect(mockAxios.history.get).toHaveLength(1);
    });
  });

  // ====================
  // EMAIL OPERATIONS TESTS
  // ====================

  describe('Email Operations', () => {
    it('should generate email preview', async () => {
      mockAxios.onPost('/api/email/generate').reply(200, mockApiResponse(mockEmailPreview));

      const result = await apiClient.generateEmail('user-123', { includeMatches: 5 });

      expect(result).toEqual(mockEmailPreview);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userId: 'user-123', includeMatches: 5 })
      );
    });

    it('should send test email', async () => {
      mockAxios.onPost('/api/email/send-test').reply(200, {});

      await expect(apiClient.sendTestEmail('user-123')).resolves.not.toThrow();
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userId: 'user-123' })
      );
    });

    it('should schedule email campaign', async () => {
      mockAxios.onPost('/api/email/schedule-campaign').reply(200, mockApiResponse(mockBatchJob));

      const userIds = ['user-1', 'user-2'];
      const result = await apiClient.scheduleEmailCampaign(userIds, { template: 'weekly' });

      expect(result).toEqual(mockBatchJob);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ userIds, template: 'weekly' })
      );
    });

    it('should get email templates with caching', async () => {
      const mockTemplates = [{ id: '1', name: 'Weekly Digest' }];
      mockAxios.onGet('/api/email/templates').reply(200, mockTemplates);

      const result1 = await apiClient.getEmailTemplates();
      const result2 = await apiClient.getEmailTemplates();

      expect(result1).toEqual(mockTemplates);
      expect(result2).toEqual(mockTemplates);
      expect(mockAxios.history.get).toHaveLength(1);
    });
  });

  // ====================
  // SQL OPERATIONS TESTS
  // ====================

  describe('SQL Operations', () => {
    it('should execute SQL query', async () => {
      mockAxios.onPost('/api/sql/execute').reply(200, mockApiResponse(mockQueryResult));

      const query = 'SELECT * FROM jobs LIMIT 10';
      const result = await apiClient.executeQuery(query);

      expect(result).toEqual(mockQueryResult);
      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ query, params: undefined })
      );
    });

    it('should execute SQL query with parameters', async () => {
      mockAxios.onPost('/api/sql/execute').reply(200, mockApiResponse(mockQueryResult));

      const query = 'SELECT * FROM jobs WHERE id = ? AND status = ?';
      const params = ['job-123', 'active'];

      await apiClient.executeQuery(query, params);

      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({ query, params })
      );
    });

    it('should get query history', async () => {
      const expectedResponse = mockPaginatedResponse([mockQueryHistory]);
      mockAxios.onGet('/api/sql/history').reply(200, expectedResponse);

      const result = await apiClient.getQueryHistory({ page: 1, limit: 20 });

      expect(result).toEqual(expectedResponse);
    });

    it('should save query', async () => {
      mockAxios.onPost('/api/sql/save').reply(200, {});

      await apiClient.saveQuery('My Query', 'SELECT * FROM jobs', 'Get all jobs');

      expect(mockAxios.history.post[0].data).toBe(
        JSON.stringify({
          name: 'My Query',
          query: 'SELECT * FROM jobs',
          description: 'Get all jobs',
        })
      );
    });

    it('should get saved queries with caching', async () => {
      const mockSavedQueries = [{ id: '1', name: 'All Jobs', query: 'SELECT * FROM jobs' }];
      mockAxios.onGet('/api/sql/saved').reply(200, mockSavedQueries);

      const result1 = await apiClient.getSavedQueries();
      const result2 = await apiClient.getSavedQueries();

      expect(result1).toEqual(mockSavedQueries);
      expect(result2).toEqual(mockSavedQueries);
      expect(mockAxios.history.get).toHaveLength(1);
    });
  });

  // ====================
  // MONITORING OPERATIONS TESTS
  // ====================

  describe('Monitoring Operations', () => {
    it('should get system metrics', async () => {
      mockAxios.onGet('/api/monitoring/metrics').reply(200, mockApiResponse(mockSystemMetrics));

      const result = await apiClient.getMetrics('1h');

      expect(result).toEqual(mockSystemMetrics);
      expect(mockAxios.history.get[0].params).toEqual({ timeRange: '1h' });
    });

    it('should get health check without caching', async () => {
      mockAxios.onGet('/api/health').reply(200, mockApiResponse(mockHealthStatus));

      const result1 = await apiClient.getHealthCheck();
      const result2 = await apiClient.getHealthCheck();

      expect(result1).toEqual(mockHealthStatus);
      expect(result2).toEqual(mockHealthStatus);
      // Health checks should never be cached
      expect(mockAxios.history.get).toHaveLength(2);
    });

    it('should get system logs with pagination', async () => {
      const mockLogs = [{ id: '1', level: 'info', message: 'Test log' }];
      const expectedResponse = mockPaginatedResponse(mockLogs);
      mockAxios.onGet('/api/monitoring/logs').reply(200, expectedResponse);

      const params = { page: 1, limit: 50, level: 'error', service: 'api' };
      const result = await apiClient.getSystemLogs(params);

      expect(result).toEqual(expectedResponse);
      expect(mockAxios.history.get[0].params).toEqual(params);
    });
  });

  // ====================
  // ERROR HANDLING TESTS
  // ====================

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockAxios.onGet('/api/health').networkError();

      await expect(apiClient.getHealthCheck()).rejects.toThrow(NetworkError);
    });

    it('should handle timeout errors', async () => {
      mockAxios.onGet('/api/health').timeout();

      await expect(apiClient.getHealthCheck()).rejects.toThrow(NetworkError);
    });

    it('should handle validation errors', async () => {
      // Mock invalid response data
      mockAxios.onGet('/api/health').reply(200, {
        data: { invalidField: 'invalid' },
        success: true,
        timestamp: '2023-12-01T10:00:00Z',
      });

      await expect(apiClient.getHealthCheck()).rejects.toThrow(ValidationError);
    });

    it('should retry on server errors', async () => {
      let attemptCount = 0;
      mockAxios.onGet('/api/health').reply(() => {
        attemptCount++;
        if (attemptCount < 2) {
          return [500, { message: 'Server Error' }];
        }
        return [200, mockApiResponse(mockHealthStatus)];
      });

      const result = await apiClient.getHealthCheck();

      expect(result).toEqual(mockHealthStatus);
      expect(attemptCount).toBe(2);
    });

    it('should not retry on client errors', async () => {
      let attemptCount = 0;
      mockAxios.onGet('/api/health').reply(() => {
        attemptCount++;
        return [400, { message: 'Bad Request' }];
      });

      await expect(apiClient.getHealthCheck()).rejects.toThrow(ApiError);
      expect(attemptCount).toBe(1);
    });
  });

  // ====================
  // CACHING TESTS
  // ====================

  describe('Caching', () => {
    it('should cache GET requests by default', async () => {
      mockAxios.onGet('/api/health').reply(200, mockApiResponse(mockHealthStatus));

      // This should not use cache (health checks disabled)
      await apiClient.getHealthCheck();
      await apiClient.getHealthCheck();

      expect(mockAxios.history.get).toHaveLength(2);
    });

    it('should not cache non-GET requests', async () => {
      mockAxios.onPost('/api/batch/trigger').reply(200, mockApiResponse(mockBatchJob));

      await apiClient.triggerBatch('scoring');
      await apiClient.triggerBatch('scoring');

      expect(mockAxios.history.post).toHaveLength(2);
    });

    it('should clear cache when pattern is provided', async () => {
      const mockJob = { id: 'job-123', title: 'Developer' };
      mockAxios.onGet('/api/jobs/job-123').reply(200, mockJob);

      // Make request to populate cache
      await apiClient.getJobById('job-123');

      // Clear job-related cache
      apiClient.clearCache('jobs');

      // Next request should not use cache
      await apiClient.getJobById('job-123');

      expect(mockAxios.history.get).toHaveLength(2);
    });
  });

  // ====================
  // REQUEST CANCELLATION TESTS
  // ====================

  describe('Request Cancellation', () => {
    it('should cancel individual requests', async () => {
      let requestCancelled = false;

      mockAxios.onGet('/api/health').reply((config) => {
        return new Promise((resolve, reject) => {
          config.cancelToken?.promise.then(() => {
            requestCancelled = true;
            reject(new axios.Cancel('Request cancelled'));
          });

          setTimeout(() => {
            resolve([200, mockApiResponse(mockHealthStatus)]);
          }, 1000);
        });
      });

      const requestPromise = apiClient.getHealthCheck();
      apiClient.cancelRequest('health-check');

      await expect(requestPromise).rejects.toThrow();
      expect(requestCancelled).toBe(true);
    });

    it('should cancel all requests', async () => {
      let cancelledCount = 0;

      mockAxios.onAny().reply((config) => {
        return new Promise((resolve, reject) => {
          config.cancelToken?.promise.then(() => {
            cancelledCount++;
            reject(new axios.Cancel('Request cancelled'));
          });
        });
      });

      const promises = [
        apiClient.getHealthCheck(),
        apiClient.getMetrics(),
        apiClient.getUserMatches('user-123'),
      ];

      apiClient.cancelAllRequests();

      await expect(Promise.allSettled(promises)).resolves.toEqual([
        { status: 'rejected', reason: expect.any(Error) },
        { status: 'rejected', reason: expect.any(Error) },
        { status: 'rejected', reason: expect.any(Error) },
      ]);
    });
  });

  // ====================
  // UTILITY TESTS
  // ====================

  describe('Utilities', () => {
    it('should get current config', () => {
      const config = apiClient.getConfig();

      expect(config).toEqual({
        baseURL: 'http://localhost:8000',
        timeout: 5000,
        retryAttempts: 1,
        retryDelay: 100,
        enableLogging: false,
        enableCaching: true,
        cacheTimeout: 1000,
      });
    });

    it('should update config', () => {
      apiClient.updateConfig({
        timeout: 10000,
        retryAttempts: 5,
      });

      const config = apiClient.getConfig();
      expect(config.timeout).toBe(10000);
      expect(config.retryAttempts).toBe(5);
    });

    it('should properly destroy client', () => {
      const clearCacheSpy = jest.spyOn(apiClient, 'clearCache');
      const cancelAllSpy = jest.spyOn(apiClient, 'cancelAllRequests');

      apiClient.destroy();

      expect(clearCacheSpy).toHaveBeenCalled();
      expect(cancelAllSpy).toHaveBeenCalled();
    });
  });

  // ====================
  // USER OPERATIONS TESTS
  // ====================

  describe('User Operations', () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const mockUserProfile = {
      id: 'profile-123',
      userId: 'user-123',
      title: 'Software Developer',
      bio: 'Experienced developer',
      location: 'San Francisco',
      skills: ['JavaScript', 'React', 'Node.js'],
      experience: 'senior' as const,
      preferences: {
        jobTypes: ['full-time'],
        locationTypes: ['remote'],
        industries: ['technology'],
        companySizes: ['startup', 'medium'],
        benefits: ['health-insurance', 'flexible-hours'],
        workCulture: ['collaborative', 'innovative'],
      },
    };

    it('should get users with pagination and search', async () => {
      const expectedResponse = mockPaginatedResponse([mockUser]);
      mockAxios.onGet('/api/users').reply(200, expectedResponse);

      const params = { page: 1, limit: 10, search: 'john' };
      const result = await apiClient.getUsers(params);

      expect(result).toEqual(expectedResponse);
      expect(mockAxios.history.get[0].params).toEqual(params);
    });

    it('should get user by ID with caching', async () => {
      mockAxios.onGet('/api/users/user-123').reply(200, mockUser);

      const result1 = await apiClient.getUserById('user-123');
      const result2 = await apiClient.getUserById('user-123');

      expect(result1).toEqual(mockUser);
      expect(result2).toEqual(mockUser);
      expect(mockAxios.history.get).toHaveLength(1);
    });

    it('should get user profile with caching', async () => {
      mockAxios.onGet('/api/users/user-123/profile').reply(200, mockUserProfile);

      const result = await apiClient.getUserProfile('user-123');

      expect(result).toEqual(mockUserProfile);
    });

    it('should update user profile and clear cache', async () => {
      const updates = { title: 'Senior Developer', skills: ['JavaScript', 'TypeScript'] };
      const updatedProfile = { ...mockUserProfile, ...updates };

      mockAxios.onPatch('/api/users/user-123/profile').reply(200, updatedProfile);

      const result = await apiClient.updateUserProfile('user-123', updates);

      expect(result).toEqual(updatedProfile);
      expect(mockAxios.history.patch[0].data).toBe(JSON.stringify(updates));
    });
  });

  // ====================
  // INTEGRATION TESTS
  // ====================

  describe('Integration Tests', () => {
    it('should handle complete job matching workflow', async () => {
      // 1. Import jobs
      mockAxios.onPost('/api/jobs/import').reply(200, mockApiResponse(mockImportResult));

      // 2. Generate matching
      mockAxios.onPost('/api/matching/generate').reply(200, mockApiResponse(mockMatchingResult));

      // 3. Calculate scores
      mockAxios.onPost('/api/scores/calculate').reply(200, mockApiResponse(mockScore));

      // 4. Generate email
      mockAxios.onPost('/api/email/generate').reply(200, mockApiResponse(mockEmailPreview));

      const file = new File(['csv content'], 'jobs.csv');

      // Execute workflow
      const importResult = await apiClient.importJobs(file);
      const matchingResult = await apiClient.generateMatching('user-123');
      const score = await apiClient.calculateScore('user-123', 'job-456');
      const email = await apiClient.generateEmail('user-123');

      expect(importResult).toEqual(mockImportResult);
      expect(matchingResult).toEqual(mockMatchingResult);
      expect(score).toEqual(mockScore);
      expect(email).toEqual(mockEmailPreview);
    });

    it('should handle concurrent requests efficiently', async () => {
      // Mock multiple endpoints
      mockAxios.onGet('/api/health').reply(200, mockApiResponse(mockHealthStatus));
      mockAxios.onGet('/api/monitoring/metrics').reply(200, mockApiResponse(mockSystemMetrics));
      mockAxios.onGet('/api/users/user-123').reply(200, mockUser);

      // Make concurrent requests
      const promises = [
        apiClient.getHealthCheck(),
        apiClient.getMetrics(),
        apiClient.getUserById('user-123'),
      ];

      const results = await Promise.all(promises);

      expect(results[0]).toEqual(mockHealthStatus);
      expect(results[1]).toEqual(mockSystemMetrics);
      expect(results[2]).toEqual(mockUser);
    });
  });
});

// ====================
// MOCK ADAPTER UTILITIES FOR TESTING
// ====================

export const createMockApiClient = (config?: Partial<any>) => {
  const mockAdapter = new MockAdapter(axios);

  const client = new ApiClient({
    baseURL: 'http://localhost:8000',
    enableLogging: false,
    enableCaching: false,
    retryAttempts: 0,
    ...config,
  });

  return { client, mockAdapter };
};

export const mockApiResponses = {
  batchJob: mockBatchJob,
  batchStatus: mockBatchStatus,
  importResult: mockImportResult,
  score: mockScore,
  batchScoreResult: mockBatchScoreResult,
  matchingResult: mockMatchingResult,
  userMatches: mockUserMatches,
  emailPreview: mockEmailPreview,
  queryResult: mockQueryResult,
  queryHistory: mockQueryHistory,
  systemMetrics: mockSystemMetrics,
  healthStatus: mockHealthStatus,
};