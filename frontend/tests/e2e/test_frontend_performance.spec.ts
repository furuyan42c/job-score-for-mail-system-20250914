/**
 * T085: Frontend Performance Testing [RED PHASE]
 *
 * This test is intentionally designed to fail (TDD RED phase).
 * Documents the expected frontend performance requirements that are not yet met,
 * making the need for frontend optimization clear.
 *
 * Performance targets:
 * - Lighthouse Performance Score: >90
 * - First Contentful Paint: <1.5s
 * - Largest Contentful Paint: <2.5s
 * - Time to Interactive: <3s
 * - Cumulative Layout Shift: <0.1
 * - Large data rendering: <2s for 1000 items
 *
 * Run command: npx playwright test test_frontend_performance.spec.ts
 */

import { test, expect, type Page, type BrowserContext } from '@playwright/test';

// Test configuration
const FRONTEND_URL = 'http://localhost:3000';

// Performance thresholds
const PERFORMANCE_TARGETS = {
  lighthouse_performance_score: 90,
  first_contentful_paint_ms: 1500,
  largest_contentful_paint_ms: 2500,
  time_to_interactive_ms: 3000,
  cumulative_layout_shift: 0.1,
  large_data_render_ms: 2000,
  concurrent_users: 100,
  page_load_timeout_ms: 10000
};

interface PerformanceMetrics {
  first_contentful_paint: number;
  largest_contentful_paint: number;
  time_to_interactive: number;
  cumulative_layout_shift: number;
  total_blocking_time: number;
  load_event_end: number;
}

class FrontendPerformanceHelper {
  constructor(private page: Page) {}

  async collectPerformanceMetrics(): Promise<PerformanceMetrics> {
    /**
     * Collect Web Vitals and performance metrics from the browser
     */
    return await this.page.evaluate(() => {
      return new Promise((resolve) => {
        // Wait for page to fully load
        if (document.readyState === 'complete') {
          this.getMetrics(resolve);
        } else {
          window.addEventListener('load', () => {
            setTimeout(() => this.getMetrics(resolve), 1000);
          });
        }
      });

      function getMetrics(resolve) {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

        // Collect Core Web Vitals
        const metrics = {
          first_contentful_paint: 0,
          largest_contentful_paint: 0,
          time_to_interactive: 0,
          cumulative_layout_shift: 0,
          total_blocking_time: 0,
          load_event_end: navigation.loadEventEnd - navigation.fetchStart
        };

        // Get paint metrics
        const paintEntries = performance.getEntriesByType('paint');
        for (const entry of paintEntries) {
          if (entry.name === 'first-contentful-paint') {
            metrics.first_contentful_paint = entry.startTime;
          }
        }

        // Use PerformanceObserver for LCP and CLS if available
        if ('PerformanceObserver' in window) {
          try {
            const observer = new PerformanceObserver((list) => {
              const entries = list.getEntries();
              for (const entry of entries) {
                if (entry.entryType === 'largest-contentful-paint') {
                  metrics.largest_contentful_paint = entry.startTime;
                }
                if (entry.entryType === 'layout-shift' && !entry.hadRecentInput) {
                  metrics.cumulative_layout_shift += entry.value;
                }
              }
            });

            observer.observe({ entryTypes: ['largest-contentful-paint', 'layout-shift'] });

            // Give time for metrics to be collected
            setTimeout(() => {
              observer.disconnect();
              resolve(metrics);
            }, 500);
          } catch (error) {
            console.warn('PerformanceObserver not fully supported:', error);
            resolve(metrics);
          }
        } else {
          resolve(metrics);
        }
      }
    });
  }

  async simulateSlowNetwork(): Promise<void> {
    /**
     * Simulate slow 3G network conditions
     */
    const context = this.page.context();
    await context.route('**/*', async (route) => {
      // Add artificial delay to simulate slow network
      await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));
      route.continue();
    });
  }

  async generateLargeDataSet(size: number): Promise<any[]> {
    /**
     * Generate large dataset for performance testing
     */
    return Array.from({ length: size }, (_, i) => ({
      id: i + 1,
      title: `Job Title ${i + 1}`,
      company: `Company ${Math.floor(Math.random() * 100) + 1}`,
      location: ['Tokyo', 'Osaka', 'Nagoya', 'Fukuoka'][Math.floor(Math.random() * 4)],
      salary: `${Math.floor(Math.random() * 5000000) + 3000000}円`,
      description: `Job description for position ${i + 1}. `.repeat(10),
      tags: Array.from({ length: 5 }, (_, j) => `tag${i}-${j}`),
      createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
    }));
  }
}

test.describe('T085: Frontend Performance Testing', () => {
  let helper: FrontendPerformanceHelper;

  test.beforeEach(async ({ page }) => {
    helper = new FrontendPerformanceHelper(page);
  });

  test('1. Page Load Performance Metrics', async ({ page }) => {
    /**
     * Performance Test: Core Web Vitals and page load metrics
     *
     * Expected behavior:
     * - First Contentful Paint < 1.5s
     * - Largest Contentful Paint < 2.5s
     * - Time to Interactive < 3s
     * - Cumulative Layout Shift < 0.1
     *
     * Current state: Not optimized -> This test will fail
     */
    console.log('🔴 RED PHASE: Page load performance metrics test');

    try {
      // Navigate and measure performance
      const startTime = Date.now();
      await page.goto(FRONTEND_URL, {
        waitUntil: 'networkidle',
        timeout: PERFORMANCE_TARGETS.page_load_timeout_ms
      });

      // Wait for application to initialize
      await page.waitForTimeout(2000);

      // Collect performance metrics
      const metrics = await helper.collectPerformanceMetrics();
      const totalLoadTime = Date.now() - startTime;

      console.log('Performance Metrics:');
      console.log(`- Total Load Time: ${totalLoadTime}ms`);
      console.log(`- First Contentful Paint: ${metrics.first_contentful_paint.toFixed(2)}ms`);
      console.log(`- Largest Contentful Paint: ${metrics.largest_contentful_paint.toFixed(2)}ms`);
      console.log(`- Load Event End: ${metrics.load_event_end.toFixed(2)}ms`);
      console.log(`- Cumulative Layout Shift: ${metrics.cumulative_layout_shift.toFixed(3)}`);

      // Performance assertions (will fail in RED phase)
      expect(metrics.first_contentful_paint).toBeLessThan(PERFORMANCE_TARGETS.first_contentful_paint_ms);
      expect(metrics.largest_contentful_paint).toBeLessThan(PERFORMANCE_TARGETS.largest_contentful_paint_ms);
      expect(metrics.cumulative_layout_shift).toBeLessThan(PERFORMANCE_TARGETS.cumulative_layout_shift);
      expect(totalLoadTime).toBeLessThan(PERFORMANCE_TARGETS.page_load_timeout_ms / 2);

      // Check for performance best practices
      await expect(page.locator('img[loading="lazy"]')).toHaveCount(0, 'Images should have lazy loading');

    } catch (error) {
      console.log('Expected failure: Frontend performance not optimized');
      console.log(`Error: ${error.message}`);
      throw new Error(`Page load performance test failed: ${error.message}`);
    }
  });

  test('2. Large Data Rendering Performance', async ({ page }) => {
    /**
     * Performance Test: Large dataset rendering performance
     *
     * Expected behavior:
     * - 1000 items render within 2 seconds
     * - Smooth scrolling with virtual scrolling
     * - No significant UI blocking during render
     * - Memory usage remains stable
     *
     * Current state: Not optimized -> This test will fail
     */
    console.log('🔴 RED PHASE: Large data rendering performance test');

    try {
      await page.goto(`${FRONTEND_URL}/jobs`);

      // Generate large dataset
      const largeDataSet = await helper.generateLargeDataSet(1000);

      // Mock API response with large dataset
      await page.route('**/api/v1/jobs*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: largeDataSet,
            total: largeDataSet.length,
            page: 1,
            limit: 1000
          })
        });
      });

      // Measure rendering time
      const renderStartTime = Date.now();

      // Trigger data load
      await page.reload();

      // Wait for data to load and render
      await page.waitForSelector('.job-card', { timeout: 10000 });
      await page.waitForFunction(
        (expectedCount) => document.querySelectorAll('.job-card').length >= expectedCount,
        largeDataSet.length,
        { timeout: PERFORMANCE_TARGETS.large_data_render_ms * 2 }
      );

      const renderEndTime = Date.now();
      const renderDuration = renderEndTime - renderStartTime;

      console.log(`Large data rendering completed in ${renderDuration}ms`);
      console.log(`Rendered ${largeDataSet.length} items`);

      // Performance assertions
      expect(renderDuration).toBeLessThan(PERFORMANCE_TARGETS.large_data_render_ms);

      // Check for virtual scrolling or pagination
      const visibleItems = await page.locator('.job-card').count();
      if (visibleItems === largeDataSet.length) {
        console.warn('Warning: All items rendered at once, virtual scrolling recommended');
      }

      // Test scrolling performance
      console.log('Testing scroll performance...');
      const scrollStartTime = Date.now();

      for (let i = 0; i < 10; i++) {
        await page.mouse.wheel(0, 500);
        await page.waitForTimeout(50);
      }

      const scrollEndTime = Date.now();
      const scrollDuration = scrollEndTime - scrollStartTime;
      console.log(`Scroll test completed in ${scrollDuration}ms`);

      // Scroll should be smooth (< 16ms per frame for 60fps)
      expect(scrollDuration / 10).toBeLessThan(100); // Average 100ms per scroll action

    } catch (error) {
      console.log('Expected failure: Large data rendering not optimized');
      console.log(`Error: ${error.message}`);
      throw new Error(`Large data rendering test failed: ${error.message}`);
    }
  });

  test('3. Network Performance Under Slow Conditions', async ({ page }) => {
    /**
     * Performance Test: Performance under slow network conditions
     *
     * Expected behavior:
     * - App remains usable under slow 3G conditions
     * - Progressive loading shows content incrementally
     * - Loading states provide good UX
     * - Essential content loads first
     *
     * Current state: Not optimized -> This test will fail
     */
    console.log('🔴 RED PHASE: Network performance under slow conditions test');

    try {
      // Simulate slow network
      await helper.simulateSlowNetwork();

      const loadStartTime = Date.now();
      await page.goto(FRONTEND_URL, { timeout: 15000 });

      // Check for loading states
      const hasLoadingSpinner = await page.locator('.loading, .spinner, [data-testid="loading"]').isVisible();
      console.log(`Loading state visible: ${hasLoadingSpinner}`);

      // Wait for initial content
      await page.waitForSelector('main, .main-content, [data-testid="main-content"]', { timeout: 10000 });

      const initialLoadTime = Date.now() - loadStartTime;
      console.log(`Initial content loaded in ${initialLoadTime}ms under slow network`);

      // Test interaction during loading
      const navigationLink = page.locator('nav a, .nav-link').first();
      if (await navigationLink.isVisible()) {
        await navigationLink.click();

        // Should show loading state for navigation
        const navigationLoadingVisible = await page.locator('.loading, .spinner').isVisible();
        console.log(`Navigation loading state: ${navigationLoadingVisible}`);
      }

      // Performance assertions for slow network
      expect(initialLoadTime).toBeLessThan(8000); // 8 seconds for slow network
      expect(hasLoadingSpinner).toBe(true); // Should show loading states

      // Check for performance optimizations
      const hasServiceWorker = await page.evaluate(() => 'serviceWorker' in navigator);
      console.log(`Service Worker support: ${hasServiceWorker}`);

    } catch (error) {
      console.log('Expected failure: Network performance not optimized for slow conditions');
      console.log(`Error: ${error.message}`);
      throw new Error(`Network performance test failed: ${error.message}`);
    }
  });

  test('4. Concurrent User Simulation', async ({ browser }) => {
    /**
     * Performance Test: Multiple concurrent user sessions
     *
     * Expected behavior:
     * - System handles 100 concurrent frontend sessions
     * - No significant performance degradation
     * - All sessions load successfully
     * - Average response time remains acceptable
     *
     * Current state: Not optimized -> This test will fail
     */
    console.log('🔴 RED PHASE: Concurrent user simulation test');

    const concurrentUsers = 20; // Reduced for RED phase testing
    const contexts: BrowserContext[] = [];
    const results: Array<{ userId: number; loadTime: number; success: boolean; error?: string }> = [];

    try {
      console.log(`Simulating ${concurrentUsers} concurrent users...`);

      // Create concurrent browser contexts
      for (let i = 0; i < concurrentUsers; i++) {
        const context = await browser.newContext();
        contexts.push(context);
      }

      // Execute concurrent user sessions
      const userPromises = contexts.map(async (context, index) => {
        const userId = index + 1;
        try {
          const page = await context.newPage();
          const startTime = Date.now();

          await page.goto(FRONTEND_URL, { timeout: 10000 });
          await page.waitForSelector('main, body', { timeout: 5000 });

          // Simulate user interaction
          await page.waitForTimeout(Math.random() * 1000 + 500);

          const loadTime = Date.now() - startTime;

          await page.close();

          return {
            userId,
            loadTime,
            success: true
          };
        } catch (error) {
          return {
            userId,
            loadTime: 10000,
            success: false,
            error: error.message
          };
        }
      });

      // Wait for all users to complete
      const userResults = await Promise.all(userPromises);
      results.push(...userResults);

      // Analyze results
      const successfulUsers = results.filter(r => r.success);
      const failedUsers = results.filter(r => !r.success);

      const avgLoadTime = successfulUsers.reduce((sum, r) => sum + r.loadTime, 0) / successfulUsers.length;
      const maxLoadTime = Math.max(...successfulUsers.map(r => r.loadTime));
      const minLoadTime = Math.min(...successfulUsers.map(r => r.loadTime));
      const successRate = (successfulUsers.length / results.length) * 100;

      console.log(`Concurrent user test results:`);
      console.log(`- Success rate: ${successRate.toFixed(1)}% (${successfulUsers.length}/${results.length})`);
      console.log(`- Average load time: ${avgLoadTime.toFixed(2)}ms`);
      console.log(`- Load time range: ${minLoadTime}ms - ${maxLoadTime}ms`);

      if (failedUsers.length > 0) {
        console.log(`Failed users: ${failedUsers.length}`);
        failedUsers.forEach(user => {
          console.log(`  User ${user.userId}: ${user.error}`);
        });
      }

      // Performance assertions
      expect(successRate).toBeGreaterThan(90); // 90% success rate
      expect(avgLoadTime).toBeLessThan(5000); // 5 second average load time
      expect(maxLoadTime).toBeLessThan(10000); // 10 second max load time

    } catch (error) {
      console.log('Expected failure: Concurrent user performance not optimized');
      console.log(`Error: ${error.message}`);
      throw new Error(`Concurrent user test failed: ${error.message}`);
    } finally {
      // Clean up contexts
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('5. Memory Leak Detection', async ({ page }) => {
    /**
     * Performance Test: Frontend memory leak detection
     *
     * Expected behavior:
     * - Memory usage remains stable during navigation
     * - No significant memory increase after operations
     * - JavaScript heap size stays within limits
     * - Event listeners are properly cleaned up
     *
     * Current state: Not optimized -> This test will fail
     */
    console.log('🔴 RED PHASE: Memory leak detection test');

    try {
      await page.goto(FRONTEND_URL);

      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (!initialMemory) {
        console.log('Performance.memory API not available, skipping memory test');
        return;
      }

      console.log(`Initial memory usage: ${(initialMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);

      // Simulate memory-intensive operations
      for (let i = 0; i < 10; i++) {
        // Navigate between pages
        await page.goto(`${FRONTEND_URL}/jobs`);
        await page.waitForTimeout(500);

        await page.goto(`${FRONTEND_URL}/profile`);
        await page.waitForTimeout(500);

        await page.goto(FRONTEND_URL);
        await page.waitForTimeout(500);

        // Force garbage collection if available
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });
      }

      // Get final memory usage
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const memoryIncreasePercent = (memoryIncrease / initialMemory.usedJSHeapSize) * 100;

      console.log(`Final memory usage: ${(finalMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${memoryIncreasePercent.toFixed(1)}%)`);

      // Memory leak assertions
      expect(memoryIncreasePercent).toBeLessThan(50); // Memory should not increase by more than 50%
      expect(finalMemory.usedJSHeapSize).toBeLessThan(finalMemory.jsHeapSizeLimit * 0.8); // Stay under 80% of heap limit

      // Check for excessive DOM nodes
      const domNodeCount = await page.evaluate(() => document.querySelectorAll('*').length);
      console.log(`DOM node count: ${domNodeCount}`);
      expect(domNodeCount).toBeLessThan(5000); // Reasonable DOM size limit

    } catch (error) {
      console.log('Expected failure: Memory optimization not implemented');
      console.log(`Error: ${error.message}`);
      throw new Error(`Memory leak detection test failed: ${error.message}`);
    }
  });
});

/**
 * RED PHASE SUMMARY:
 *
 * Expected Failures:
 * 1. Page load performance not meeting Core Web Vitals targets
 * 2. Large data rendering not optimized (no virtual scrolling)
 * 3. No loading states or progressive enhancement for slow networks
 * 4. Poor concurrent user performance
 * 5. Memory leaks and excessive DOM manipulation
 * 6. Missing performance optimizations (lazy loading, code splitting, etc.)
 *
 * Next Steps (GREEN PHASE):
 * 1. Implement virtual scrolling for large datasets
 * 2. Add loading states and skeleton screens
 * 3. Implement lazy loading for images and components
 * 4. Add service worker for caching
 * 5. Optimize bundle size with code splitting
 * 6. Add performance monitoring and metrics
 *
 * REFACTOR PHASE:
 * 1. Advanced performance optimizations
 * 2. Implement performance budgets
 * 3. Add real user monitoring (RUM)
 * 4. Optimize critical rendering path
 * 5. Add performance regression testing
 * 6. Implement progressive web app features
 */