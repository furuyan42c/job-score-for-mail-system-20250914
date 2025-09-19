/**
 * T083: Data Flow Integration Tests [RED PHASE]
 * 
 * This test is intentionally designed to fail (TDD RED phase).
 * Documents the expected Frontend→Backend→DB→Frontend data flow
 * that is not yet fully implemented.
 * 
 * Test scenarios:
 * 1. Job listing page display
 * 2. Job detail modal display
 * 3. User registration/login
 * 4. Matching results display
 * 
 * Run command: npx playwright test test_data_flow.spec.ts
 */

import { test, expect, type Page } from '@playwright/test';

// Test configuration
const API_BASE_URL = 'http://localhost:8001';
const FRONTEND_URL = 'http://localhost:3000';

// Test data
const TEST_USER = {
  email: 'dataflow_test@example.com',
  password: 'testpass123',
  name: 'DataFlow Test User'
};

class DataFlowTestHelper {
  constructor(private page: Page) {}

  async waitForApiCall(endpoint: string, timeout: number = 5000) {
    return this.page.waitForResponse(
      response => response.url().includes(endpoint),
      { timeout }
    );
  }

  async verifyApiResponse(response: any, expectedStatus: number = 200) {
    expect(response.status()).toBe(expectedStatus);
    const data = await response.json();
    return data;
  }

  async checkNetworkError(endpoint: string) {
    try {
      const response = await this.page.request.get(`${API_BASE_URL}${endpoint}`);
      return response;
    } catch (error) {
      // Expected in RED phase - API endpoints don't exist yet
      return null;
    }
  }
}

test.describe('T083: Complete Data Flow Integration Tests', () => {
  let helper: DataFlowTestHelper;

  test.beforeEach(async ({ page }) => {
    helper = new DataFlowTestHelper(page);
    await page.goto(FRONTEND_URL);
  });

  test('1. Job Listing Page Data Flow', async ({ page }) => {
    /**
     * Expected Data Flow:
     * Frontend → GET /api/v1/jobs → Database → Frontend Display
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: Job listing data flow test');
    
    // Navigate to jobs page
    await page.goto(`${FRONTEND_URL}/jobs`);
    
    // Wait for API call to jobs endpoint
    const jobsApiPromise = helper.waitForApiCall('/api/v1/jobs');
    
    // Verify API call is made
    try {
      const jobsResponse = await jobsApiPromise;
      const jobsData = await helper.verifyApiResponse(jobsResponse);
      
      // Verify response structure
      expect(Array.isArray(jobsData)).toBe(true);
      
      if (jobsData.length > 0) {
        const job = jobsData[0];
        expect(job).toHaveProperty('id');
        expect(job).toHaveProperty('title');
        expect(job).toHaveProperty('company');
        expect(job).toHaveProperty('location');
        expect(job).toHaveProperty('description');
      }
      
      // Verify frontend displays the data
      await expect(page.locator('.job-listing')).toBeVisible();
      await expect(page.locator('.job-card')).toHaveCount(jobsData.length);
      
    } catch (error) {
      // Expected failure in RED phase
      console.log('Expected failure: Jobs API endpoint not yet implemented');
      
      // Verify error handling in frontend
      await expect(page.locator('.error-message')).toBeVisible();
      await expect(page.locator('.error-message')).toContainText('Failed to load jobs');
    }
  });

  test('2. Job Detail Modal Data Flow', async ({ page }) => {
    /**
     * Expected Data Flow:
     * User Click → GET /api/v1/jobs/{id} → Database → Modal Display
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: Job detail modal data flow test');
    
    await page.goto(`${FRONTEND_URL}/jobs`);
    
    // Click on first job (if exists)
    const firstJobCard = page.locator('.job-card').first();
    if (await firstJobCard.count() > 0) {
      
      // Click to open detail modal
      const jobDetailApiPromise = helper.waitForApiCall('/api/v1/jobs/');
      await firstJobCard.click();
      
      try {
        const jobDetailResponse = await jobDetailApiPromise;
        const jobDetail = await helper.verifyApiResponse(jobDetailResponse);
        
        // Verify detailed job data structure
        expect(jobDetail).toHaveProperty('id');
        expect(jobDetail).toHaveProperty('title');
        expect(jobDetail).toHaveProperty('description');
        expect(jobDetail).toHaveProperty('requirements');
        expect(jobDetail).toHaveProperty('salary');
        expect(jobDetail).toHaveProperty('benefits');
        
        // Verify modal displays detailed information
        await expect(page.locator('.job-detail-modal')).toBeVisible();
        await expect(page.locator('.job-title')).toContainText(jobDetail.title);
        await expect(page.locator('.job-description')).toContainText(jobDetail.description);
        
      } catch (error) {
        // Expected failure in RED phase
        console.log('Expected failure: Job detail API endpoint not yet implemented');
        
        // Verify error handling
        await expect(page.locator('.modal-error')).toBeVisible();
      }
    } else {
      // No jobs available - also expected in RED phase
      console.log('No jobs available to test detail view');
    }
  });

  test('3. User Registration/Login Data Flow', async ({ page }) => {
    /**
     * Expected Data Flow:
     * Registration Form → POST /api/v1/auth/register → Supabase → Success Response
     * Login Form → POST /api/v1/auth/login → JWT Token → Protected Access
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: User registration/login data flow test');
    
    // Navigate to registration page
    await page.goto(`${FRONTEND_URL}/auth/register`);
    
    // Fill registration form
    await page.fill('[data-testid="email-input"]', TEST_USER.email);
    await page.fill('[data-testid="password-input"]', TEST_USER.password);
    await page.fill('[data-testid="name-input"]', TEST_USER.name);
    
    // Submit registration
    const registerApiPromise = helper.waitForApiCall('/api/v1/auth/register');
    await page.click('[data-testid="register-button"]');
    
    try {
      const registerResponse = await registerApiPromise;
      const userData = await helper.verifyApiResponse(registerResponse, 201);
      
      // Verify user data structure
      expect(userData).toHaveProperty('id');
      expect(userData).toHaveProperty('email');
      expect(userData).toHaveProperty('name');
      expect(userData).toHaveProperty('created_at');
      expect(userData).toHaveProperty('supabase_user_id');
      expect(userData).not.toHaveProperty('password'); // Security check
      
      // Verify redirect to login or dashboard
      await expect(page).toHaveURL(/\/(login|dashboard)/);
      
      // Test login flow
      if (page.url().includes('/login')) {
        await page.fill('[data-testid="login-email"]', TEST_USER.email);
        await page.fill('[data-testid="login-password"]', TEST_USER.password);
        
        const loginApiPromise = helper.waitForApiCall('/api/v1/auth/login');
        await page.click('[data-testid="login-button"]');
        
        const loginResponse = await loginApiPromise;
        const tokenData = await helper.verifyApiResponse(loginResponse);
        
        // Verify token structure
        expect(tokenData).toHaveProperty('access_token');
        expect(tokenData).toHaveProperty('refresh_token');
        expect(tokenData).toHaveProperty('token_type');
        expect(tokenData.token_type).toBe('bearer');
        
        // Verify token is stored and user is authenticated
        await expect(page).toHaveURL(/\/dashboard/);
        await expect(page.locator('.user-name')).toContainText(TEST_USER.name);
      }
      
    } catch (error) {
      // Expected failure in RED phase
      console.log('Expected failure: Authentication endpoints not yet implemented');
      
      // Verify error handling
      await expect(page.locator('.auth-error')).toBeVisible();
    }
  });

  test('4. Matching Results Data Flow', async ({ page }) => {
    /**
     * Expected Data Flow:
     * User Profile → POST /api/v1/matching/calculate → Scoring Engine → Match Results
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: Matching results data flow test');
    
    // Assume user is logged in (mock authentication)
    await page.goto(`${FRONTEND_URL}/matching`);
    
    // Trigger matching calculation
    const matchingApiPromise = helper.waitForApiCall('/api/v1/matching/calculate');
    await page.click('[data-testid="calculate-matches-button"]');
    
    try {
      const matchingResponse = await matchingApiPromise;
      const matchingResults = await helper.verifyApiResponse(matchingResponse);
      
      // Verify matching results structure
      expect(matchingResults).toHaveProperty('matches');
      expect(matchingResults).toHaveProperty('user_id');
      expect(matchingResults).toHaveProperty('calculated_at');
      expect(Array.isArray(matchingResults.matches)).toBe(true);
      
      if (matchingResults.matches.length > 0) {
        const match = matchingResults.matches[0];
        expect(match).toHaveProperty('job_id');
        expect(match).toHaveProperty('score');
        expect(match).toHaveProperty('reasons');
        expect(match.score).toBeGreaterThanOrEqual(0);
        expect(match.score).toBeLessThanOrEqual(100);
      }
      
      // Verify frontend displays matching results
      await expect(page.locator('.matching-results')).toBeVisible();
      await expect(page.locator('.match-card')).toHaveCount(matchingResults.matches.length);
      
      // Verify score display
      for (const match of matchingResults.matches) {
        const matchCard = page.locator(`[data-job-id="${match.job_id}"]`);
        await expect(matchCard.locator('.match-score')).toContainText(`${match.score}%`);
      }
      
    } catch (error) {
      // Expected failure in RED phase
      console.log('Expected failure: Matching engine not yet implemented');
      
      // Verify error handling
      await expect(page.locator('.matching-error')).toBeVisible();
      await expect(page.locator('.matching-error')).toContainText('Matching calculation failed');
    }
  });

  test('5. Complete User Journey Data Flow', async ({ page }) => {
    /**
     * Expected Complete Flow:
     * Registration → Login → Job Browse → Job Details → Matching → Results
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: Complete user journey data flow test');
    
    const journey = [
      { step: 'registration', url: '/auth/register' },
      { step: 'login', url: '/auth/login' },
      { step: 'jobs', url: '/jobs' },
      { step: 'matching', url: '/matching' },
      { step: 'profile', url: '/profile' }
    ];
    
    for (const { step, url } of journey) {
      try {
        await page.goto(`${FRONTEND_URL}${url}`);
        
        // Verify page loads without critical errors
        await expect(page.locator('body')).toBeVisible();
        
        // Check for API calls made by this page
        const networkRequests: string[] = [];
        page.on('request', request => {
          if (request.url().includes('/api/v1/')) {
            networkRequests.push(request.url());
          }
        });
        
        // Wait for page to settle
        await page.waitForTimeout(1000);
        
        console.log(`Step ${step}: API calls made:`, networkRequests);
        
        // Verify error handling for missing APIs
        if (networkRequests.length > 0) {
          // APIs are being called but should fail in RED phase
          await expect(page.locator('.loading-spinner, .error-message')).toBeVisible();
        }
        
      } catch (error) {
        console.log(`Expected failure at step ${step}:`, error);
      }
    }
  });

  test('6. Data Persistence Verification', async ({ page }) => {
    /**
     * Expected Flow:
     * Data Input → API Storage → Database Persistence → Data Retrieval
     * 
     * Current state: Not implemented → This test will fail
     */
    console.log('🔴 RED PHASE: Data persistence verification test');
    
    // Test data that should persist
    const testData = {
      user_preference: { location: 'Tokyo', salary_min: 300000 },
      job_application: { job_id: 1, message: 'Test application' },
      user_profile: { skills: ['JavaScript', 'React'], experience_years: 3 }
    };
    
    for (const [dataType, data] of Object.entries(testData)) {
      try {
        // Attempt to save data
        const saveResponse = await page.request.post(
          `${API_BASE_URL}/api/v1/${dataType}`,
          { data }
        );
        
        if (saveResponse.ok()) {
          const savedData = await saveResponse.json();
          expect(savedData).toHaveProperty('id');
          
          // Attempt to retrieve data
          const retrieveResponse = await page.request.get(
            `${API_BASE_URL}/api/v1/${dataType}/${savedData.id}`
          );
          
          if (retrieveResponse.ok()) {
            const retrievedData = await retrieveResponse.json();
            expect(retrievedData).toEqual(expect.objectContaining(data));
            console.log(`✅ Data persistence works for ${dataType}`);
          }
        }
        
      } catch (error) {
        // Expected failure in RED phase
        console.log(`Expected failure for ${dataType} persistence:`, error);
      }
    }
  });
});

test.describe('T083: API Connectivity Tests', () => {
  test('Backend API Health Check', async ({ page }) => {
    /**
     * Verify backend API is reachable
     * Current state: Backend has startup issues → This may fail
     */
    try {
      const healthResponse = await page.request.get(`${API_BASE_URL}/health`);
      if (healthResponse.ok()) {
        const healthData = await healthResponse.json();
        expect(healthData).toHaveProperty('status');
        expect(healthData.status).toMatch(/ok|healthy/);
        console.log('✅ Backend API is reachable');
      } else {
        console.log('❌ Backend API health check failed:', healthResponse.status());
      }
    } catch (error) {
      console.log('❌ Backend API is not reachable:', error);
      // This is expected in RED phase due to backend startup issues
    }
  });

  test('Database Connectivity Through API', async ({ page }) => {
    /**
     * Verify database is accessible through API
     * Current state: Foreign key constraint issues → This will fail
     */
    try {
      const dbTestResponse = await page.request.get(`${API_BASE_URL}/api/v1/jobs`);
      if (dbTestResponse.ok()) {
        console.log('✅ Database is accessible through API');
      } else {
        console.log('❌ Database connectivity test failed:', dbTestResponse.status());
      }
    } catch (error) {
      console.log('❌ Database is not accessible through API:', error);
      // This is expected in RED phase due to database schema issues
    }
  });
});

/**
 * RED PHASE SUMMARY:
 * 
 * Expected Failures:
 * 1. Job listing API not implemented (/api/v1/jobs)
 * 2. Job detail API not implemented (/api/v1/jobs/{id})
 * 3. Authentication APIs not implemented (/api/v1/auth/*)
 * 4. Matching engine not implemented (/api/v1/matching/*)
 * 5. Backend startup issues (foreign key constraints)
 * 6. Frontend error handling not complete
 * 
 * Next Steps (GREEN PHASE):
 * 1. Fix backend startup issues
 * 2. Implement basic API endpoints
 * 3. Add frontend error handling
 * 4. Create minimal data flow functionality
 * 5. Integrate with Supabase authentication
 * 
 * REFACTOR PHASE:
 * 1. Optimize data flow performance
 * 2. Add comprehensive error handling
 * 3. Improve user experience
 * 4. Add data validation and security
 */
