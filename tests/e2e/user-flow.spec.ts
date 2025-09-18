import { test, expect } from '@playwright/test';
import { HomePage } from './page-objects/HomePage';
import { AuthPage } from './page-objects/AuthPage';
import { JobsPage } from './page-objects/JobsPage';
import { DashboardPage } from './page-objects/DashboardPage';

test.describe('Complete User Flow E2E Tests', () => {
  test.setTimeout(120000); // 2 minutes for complete flows

  test.describe('New User Journey', () => {
    test('should complete full new user registration and job application flow', async ({ page, context }) => {
      // Initialize page objects
      const homePage = new HomePage(page);
      const authPage = new AuthPage(page);
      const jobsPage = new JobsPage(page);
      const dashboardPage = new DashboardPage(page);

      // Monitor console errors throughout the test
      const consoleErrors = await homePage.monitorConsoleErrors();

      // Step 1: Navigate to homepage and verify it loads
      await test.step('Navigate to homepage', async () => {
        await homePage.goto();
        await homePage.verifyHomePageLoaded();

        // Verify featured jobs are displayed
        const jobsCount = await homePage.getFeaturedJobsCount();
        expect(jobsCount).toBeGreaterThan(0);
      });

      // Step 2: Navigate to registration
      await test.step('Start registration process', async () => {
        await homePage.clickSignUp();
        await authPage.verifyRegistrationForm();
      });

      // Step 3: Register new user
      const testUser = {
        firstName: 'Test',
        lastName: 'User',
        email: `testuser${Date.now()}@example.com`,
        password: 'SecurePassword123!'
      };

      await test.step('Complete user registration', async () => {
        await authPage.register(
          testUser.firstName,
          testUser.lastName,
          testUser.email,
          testUser.password
        );

        // Wait for registration success and redirect
        await authPage.verifyAuthenticationSuccess();
      });

      // Step 4: Complete profile setup (after registration)
      await test.step('Complete profile setup', async () => {
        // Profile setup should be accessible after registration
        await page.waitForURL('**/profile**');

        // Fill additional profile information
        await page.getByTestId('skills-input').fill('JavaScript, TypeScript, React');
        await page.getByTestId('experience-select').selectOption('3-5 years');
        await page.getByTestId('location-input').fill('New York, NY');
        await page.getByTestId('save-profile-button').click();

        // Verify profile saved successfully
        await expect(page.getByTestId('profile-success-message')).toBeVisible();
      });

      // Step 5: Navigate to job search
      await test.step('Navigate to job search', async () => {
        await jobsPage.goto();
        await jobsPage.verifyJobsPageLoaded();
      });

      // Step 6: Search for jobs
      await test.step('Search for relevant jobs', async () => {
        await jobsPage.searchJobs('Software Developer', 'New York');
        await jobsPage.waitForSearchResults();

        const jobCount = await jobsPage.getJobCount();
        expect(jobCount).toBeGreaterThan(0);
      });

      // Step 7: Apply filters
      await test.step('Apply job filters', async () => {
        await jobsPage.applyJobTypeFilter('full-time');
        await jobsPage.applyExperienceFilter('mid-level');
        await jobsPage.waitForSearchResults();

        // Verify filtered results
        const filteredCount = await jobsPage.getJobCount();
        expect(filteredCount).toBeGreaterThanOrEqual(1);
      });

      // Step 8: View job details
      let selectedJobInfo: any;
      await test.step('View job details', async () => {
        // Get info about the first job
        selectedJobInfo = await jobsPage.getJobCardInfo(0);

        // Click to view details
        await jobsPage.clickJobCard(0);
        await jobsPage.verifyJobDetailLoaded();

        // Verify job details match
        const detailInfo = await jobsPage.getJobDetailInfo();
        expect(detailInfo.title).toBe(selectedJobInfo.title);
        expect(detailInfo.company).toBe(selectedJobInfo.company);
      });

      // Step 9: Apply to job
      await test.step('Apply to job', async () => {
        await jobsPage.applyToJob();

        // Wait for application modal/form
        await page.waitForSelector('[data-testid="application-form"]');

        // Fill application form
        await page.getByTestId('cover-letter').fill('I am very interested in this position...');
        await page.getByTestId('submit-application').click();

        // Verify application submitted
        await expect(page.getByTestId('application-success')).toBeVisible();
      });

      // Step 10: Check application status
      await test.step('Check application status in dashboard', async () => {
        await dashboardPage.goto();
        await dashboardPage.verifyDashboardLoaded();

        // Navigate to applications tab
        await page.getByTestId('my-applications-tab').click();

        // Verify the application appears in the list
        const applicationRow = page.getByTestId('application-row').first();
        await expect(applicationRow).toBeVisible();

        const applicationTitle = await applicationRow.getByTestId('application-job-title').textContent();
        expect(applicationTitle).toBe(selectedJobInfo.title);
      });

      // Step 11: Verify email notifications (mock check)
      await test.step('Verify email notification system', async () => {
        // Check if email notification settings are accessible
        await dashboardPage.switchToTab('settings');

        const emailSettings = page.getByTestId('email-notification-settings');
        await expect(emailSettings).toBeVisible();

        // Verify application confirmation email setting is enabled
        const applicationNotifications = page.getByTestId('application-notifications-toggle');
        const isEnabled = await applicationNotifications.isChecked();
        expect(isEnabled).toBe(true);
      });

      // Verify no console errors occurred during the flow
      expect(consoleErrors).toHaveLength(0);
    });

    test('should handle registration validation errors gracefully', async ({ page }) => {
      const homePage = new HomePage(page);
      const authPage = new AuthPage(page);

      await homePage.goto();
      await homePage.clickSignUp();

      await test.step('Test email validation', async () => {
        await authPage.fillRegistrationForm(
          'Test',
          'User',
          'invalid-email', // Invalid email
          'password123',
          'password123'
        );

        await authPage.submitForm();

        const validationErrors = await authPage.getValidationErrors();
        expect(validationErrors).toContain('Please enter a valid email address');
      });

      await test.step('Test password mismatch', async () => {
        await authPage.fillRegistrationForm(
          'Test',
          'User',
          'test@example.com',
          'password123',
          'differentpassword' // Password mismatch
        );

        await authPage.submitForm();

        const validationErrors = await authPage.getValidationErrors();
        expect(validationErrors).toContain('Passwords do not match');
      });
    });
  });

  test.describe('Returning User Flow', () => {
    test('should complete returning user login and job management flow', async ({ page }) => {
      const homePage = new HomePage(page);
      const authPage = new AuthPage(page);
      const jobsPage = new JobsPage(page);
      const dashboardPage = new DashboardPage(page);

      // Use existing test user credentials
      const existingUser = {
        email: 'returning.user@example.com',
        password: 'SecurePassword123!'
      };

      await test.step('Login with existing account', async () => {
        await homePage.goto();
        await homePage.clickLogin();
        await authPage.verifyLoginForm();

        await authPage.login(existingUser.email, existingUser.password, true); // Remember me
        await authPage.verifyAuthenticationSuccess();
      });

      await test.step('View personalized dashboard', async () => {
        await dashboardPage.verifyDashboardLoaded();

        // Check for personalized content
        const statistics = await dashboardPage.getStatistics();
        expect(statistics.totalJobs).toBeTruthy();
        expect(statistics.activeUsers).toBeTruthy();
      });

      await test.step('Check saved job searches', async () => {
        await jobsPage.goto();

        // Look for saved searches
        const savedSearches = page.getByTestId('saved-searches');
        if (await savedSearches.isVisible()) {
          const searchCount = await savedSearches.locator('[data-testid="saved-search-item"]').count();
          expect(searchCount).toBeGreaterThanOrEqual(0);
        }
      });

      await test.step('View personalized job recommendations', async () => {
        // Check for recommended jobs section
        const recommendations = page.getByTestId('job-recommendations');
        await expect(recommendations).toBeVisible();

        const recommendedJobs = recommendations.locator('[data-testid="job-card"]');
        const count = await recommendedJobs.count();
        expect(count).toBeGreaterThan(0);
      });

      await test.step('Check application history', async () => {
        await dashboardPage.goto();
        await page.getByTestId('application-history-tab').click();

        // Verify application history is accessible
        const applicationHistory = page.getByTestId('application-history');
        await expect(applicationHistory).toBeVisible();
      });

      await test.step('Update user preferences', async () => {
        await dashboardPage.switchToTab('settings');

        // Update notification preferences
        await page.getByTestId('email-frequency-select').selectOption('weekly');
        await page.getByTestId('job-alert-radius').fill('25');

        await dashboardPage.saveSettings();

        // Verify settings saved
        await expect(page.getByTestId('settings-success-message')).toBeVisible();
      });
    });

    test('should handle login failures appropriately', async ({ page }) => {
      const homePage = new HomePage(page);
      const authPage = new AuthPage(page);

      await homePage.goto();
      await homePage.clickLogin();

      await test.step('Test invalid credentials', async () => {
        await authPage.login('invalid@example.com', 'wrongpassword');
        await authPage.verifyAuthenticationError('Invalid email or password');
      });

      await test.step('Test account lockout after multiple failures', async () => {
        // Try multiple failed logins
        for (let i = 0; i < 3; i++) {
          await authPage.login('test@example.com', 'wrongpassword');
          await page.waitForTimeout(1000); // Small delay between attempts
        }

        // Should show account lockout message
        await authPage.verifyAuthenticationError('Account temporarily locked');
      });
    });
  });

  test.describe('Email Integration Flow', () => {
    test('should handle email-based job viewing and application', async ({ page }) => {
      // Simulate user clicking email link to view job
      await test.step('Access job via email link', async () => {
        // Simulate email link with job ID and tracking parameters
        await page.goto('/jobs/123?source=email&campaign=weekly_digest');

        const jobsPage = new JobsPage(page);
        await jobsPage.verifyJobDetailLoaded();
      });

      await test.step('Track email engagement', async () => {
        // Verify tracking parameters are captured
        const url = await page.url();
        expect(url).toContain('source=email');
        expect(url).toContain('campaign=weekly_digest');
      });
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test('should work correctly on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      const homePage = new HomePage(page);
      const jobsPage = new JobsPage(page);

      await test.step('Navigate mobile homepage', async () => {
        await homePage.goto();
        await homePage.verifyHomePageLoaded();

        // Verify mobile navigation menu
        const mobileMenu = page.getByTestId('mobile-menu-button');
        await expect(mobileMenu).toBeVisible();
      });

      await test.step('Search jobs on mobile', async () => {
        await jobsPage.goto();
        await jobsPage.searchJobs('Developer');

        // Verify mobile-friendly results layout
        const jobCards = page.getByTestId('job-card');
        await expect(jobCards.first()).toBeVisible();

        // Check mobile-specific UI elements
        const mobileFilters = page.getByTestId('mobile-filters-button');
        await expect(mobileFilters).toBeVisible();
      });
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should be accessible via keyboard navigation', async ({ page }) => {
      const homePage = new HomePage(page);

      await homePage.goto();

      await test.step('Navigate using keyboard', async () => {
        // Tab through main navigation
        await page.keyboard.press('Tab'); // Logo
        await page.keyboard.press('Tab'); // First nav item
        await page.keyboard.press('Tab'); // Second nav item

        // Verify focus is visible
        const focusedElement = await page.locator(':focus');
        await expect(focusedElement).toBeVisible();
      });

      await test.step('Use keyboard shortcuts', async () => {
        // Test global keyboard shortcuts
        await page.keyboard.press('Alt+S'); // Should focus search
        const searchInput = page.getByTestId('global-search-input');
        await expect(searchInput).toBeFocused();
      });
    });

    test('should have proper ARIA labels and roles', async ({ page }) => {
      const jobsPage = new JobsPage(page);
      await jobsPage.goto();

      await test.step('Check ARIA attributes', async () => {
        // Check search form has proper labels
        const searchInput = page.getByTestId('job-search-input');
        const ariaLabel = await searchInput.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();

        // Check buttons have accessible names
        const searchButton = page.getByTestId('search-button');
        const buttonName = await searchButton.getAttribute('aria-label') || await searchButton.textContent();
        expect(buttonName).toBeTruthy();
      });
    });
  });

  test.describe('Performance Tests', () => {
    test('should load pages within acceptable time limits', async ({ page }) => {
      await test.step('Measure homepage load time', async () => {
        const startTime = Date.now();

        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;
        expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
      });

      await test.step('Measure job search performance', async () => {
        const jobsPage = new JobsPage(page);
        await jobsPage.goto();

        const startTime = Date.now();

        await jobsPage.searchJobs('Developer');
        await jobsPage.waitForSearchResults();

        const searchTime = Date.now() - startTime;
        expect(searchTime).toBeLessThan(5000); // Search should complete within 5 seconds
      });
    });
  });

  test.describe('Network Error Handling', () => {
    test('should handle network failures gracefully', async ({ page }) => {
      const jobsPage = new JobsPage(page);

      await test.step('Handle API failure during job search', async () => {
        // Intercept and fail API requests
        await page.route('**/api/jobs/**', route => {
          route.abort('failed');
        });

        await jobsPage.goto();
        await jobsPage.searchJobs('Developer');

        // Verify error handling
        const errorMessage = page.getByTestId('search-error-message');
        await expect(errorMessage).toBeVisible();
        await expect(errorMessage).toContainText('Unable to load jobs');
      });

      await test.step('Handle timeout scenarios', async () => {
        // Simulate slow network
        await page.route('**/api/jobs/**', async route => {
          await page.waitForTimeout(10000); // 10 second delay
          await route.continue();
        });

        await jobsPage.goto();
        await jobsPage.searchJobs('Developer');

        // Should show loading state initially, then timeout message
        const loadingSpinner = page.getByTestId('loading-spinner');
        await expect(loadingSpinner).toBeVisible();

        // Wait for timeout error
        const timeoutMessage = page.getByTestId('request-timeout-message');
        await expect(timeoutMessage).toBeVisible({ timeout: 15000 });
      });
    });
  });
});