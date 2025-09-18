import { Page, expect } from '@playwright/test';

/**
 * Utility functions for E2E tests
 */
export class TestUtils {
  /**
   * Wait for element to be visible with custom timeout
   */
  static async waitForVisible(page: Page, selector: string, timeout: number = 10000): Promise<void> {
    await page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * Wait for element to be hidden
   */
  static async waitForHidden(page: Page, selector: string, timeout: number = 10000): Promise<void> {
    await page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * Wait for page to be fully loaded
   */
  static async waitForPageLoad(page: Page): Promise<void> {
    await page.waitForLoadState('networkidle');
  }

  /**
   * Take screenshot with timestamp
   */
  static async takeTimestampedScreenshot(page: Page, name: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({
      path: `test-results/screenshots/${name}-${timestamp}.png`,
      fullPage: true
    });
  }

  /**
   * Simulate typing with realistic delays
   */
  static async typeWithDelay(page: Page, selector: string, text: string, delay: number = 100): Promise<void> {
    const element = page.locator(selector);
    await element.click();
    await element.fill(''); // Clear existing text

    for (const char of text) {
      await element.type(char, { delay });
    }
  }

  /**
   * Scroll element into view and click
   */
  static async scrollAndClick(page: Page, selector: string): Promise<void> {
    const element = page.locator(selector);
    await element.scrollIntoViewIfNeeded();
    await element.click();
  }

  /**
   * Wait for API response with specific status
   */
  static async waitForApiResponse(
    page: Page,
    urlPattern: string | RegExp,
    status: number = 200,
    timeout: number = 30000
  ): Promise<void> {
    await page.waitForResponse(
      response => {
        const matchesUrl = typeof urlPattern === 'string'
          ? response.url().includes(urlPattern)
          : urlPattern.test(response.url());
        return matchesUrl && response.status() === status;
      },
      { timeout }
    );
  }

  /**
   * Monitor console for errors during test execution
   */
  static async monitorConsoleErrors(page: Page): Promise<string[]> {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(`Console Error: ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    return errors;
  }

  /**
   * Monitor network failures during test execution
   */
  static async monitorNetworkFailures(page: Page): Promise<string[]> {
    const failures: string[] = [];

    page.on('response', response => {
      if (!response.ok() && response.status() !== 304) { // Ignore cache hits
        failures.push(`Network Error: ${response.status()} - ${response.url()}`);
      }
    });

    page.on('requestfailed', request => {
      failures.push(`Request Failed: ${request.url()} - ${request.failure()?.errorText}`);
    });

    return failures;
  }

  /**
   * Set up authentication for test session
   */
  static async setupAuth(page: Page, userType: 'user' | 'admin' = 'user'): Promise<void> {
    const token = userType === 'admin' ? 'mock_admin_token' : 'mock_user_token';

    await page.context().addCookies([
      {
        name: 'auth_token',
        value: token,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false
      }
    ]);
  }

  /**
   * Clear authentication
   */
  static async clearAuth(page: Page): Promise<void> {
    await page.context().clearCookies();
  }

  /**
   * Mock API responses for testing
   */
  static async mockApiResponse(
    page: Page,
    urlPattern: string | RegExp,
    responseData: any,
    status: number = 200
  ): Promise<void> {
    await page.route(urlPattern, async route => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(responseData)
      });
    });
  }

  /**
   * Mock API failure for testing error handling
   */
  static async mockApiFailure(
    page: Page,
    urlPattern: string | RegExp,
    errorType: 'abort' | 'timeout' | 'status' = 'abort',
    status?: number
  ): Promise<void> {
    await page.route(urlPattern, async route => {
      if (errorType === 'abort') {
        await route.abort('failed');
      } else if (errorType === 'timeout') {
        await page.waitForTimeout(30000); // Simulate timeout
        await route.continue();
      } else if (errorType === 'status' && status) {
        await route.fulfill({
          status,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Mocked error response' })
        });
      }
    });
  }

  /**
   * Verify element accessibility
   */
  static async verifyAccessibility(page: Page, selector: string): Promise<void> {
    const element = page.locator(selector);

    // Check if element has proper ARIA attributes
    const ariaLabel = await element.getAttribute('aria-label');
    const ariaLabelledBy = await element.getAttribute('aria-labelledby');
    const ariaDescribedBy = await element.getAttribute('aria-describedby');

    if (!ariaLabel && !ariaLabelledBy && !ariaDescribedBy) {
      const textContent = await element.textContent();
      if (!textContent) {
        throw new Error(`Element ${selector} lacks accessible name`);
      }
    }

    // Check if focusable element is keyboard accessible
    const tagName = await element.evaluate(el => el.tagName.toLowerCase());
    const tabIndex = await element.getAttribute('tabindex');

    if (['button', 'input', 'select', 'textarea', 'a'].includes(tagName) || tabIndex !== null) {
      // Element should be focusable
      await element.focus();
      const isFocused = await element.evaluate(el => document.activeElement === el);
      expect(isFocused).toBe(true);
    }
  }

  /**
   * Measure performance metrics
   */
  static async measurePerformance(page: Page): Promise<{
    loadTime: number;
    domContentLoaded: number;
    firstContentfulPaint: number;
  }> {
    return await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');

      const fcp = paint.find(entry => entry.name === 'first-contentful-paint');

      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstContentfulPaint: fcp ? fcp.startTime : 0
      };
    });
  }

  /**
   * Generate unique test ID
   */
  static generateTestId(prefix: string = 'test'): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Wait for condition with polling
   */
  static async waitForCondition(
    condition: () => Promise<boolean>,
    timeout: number = 10000,
    interval: number = 100
  ): Promise<void> {
    const start = Date.now();

    while (Date.now() - start < timeout) {
      if (await condition()) {
        return;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error(`Condition not met within ${timeout}ms`);
  }

  /**
   * Simulate slow network conditions
   */
  static async simulateSlowNetwork(page: Page): Promise<void> {
    await page.route('**/*', async route => {
      await page.waitForTimeout(Math.random() * 2000 + 1000); // 1-3 second delay
      await route.continue();
    });
  }

  /**
   * Simulate network interruption
   */
  static async simulateNetworkInterruption(page: Page, duration: number = 5000): Promise<void> {
    await page.context().setOffline(true);
    await page.waitForTimeout(duration);
    await page.context().setOffline(false);
  }

  /**
   * Verify responsive design at different viewport sizes
   */
  static async testResponsiveDesign(
    page: Page,
    testCallback: () => Promise<void>,
    viewports: Array<{ width: number; height: number; name: string }>
  ): Promise<void> {
    for (const viewport of viewports) {
      console.log(`Testing ${viewport.name} (${viewport.width}x${viewport.height})`);

      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height
      });

      await page.waitForTimeout(500); // Allow layout to settle

      await testCallback();

      await TestUtils.takeTimestampedScreenshot(page, `responsive-${viewport.name}`);
    }
  }

  /**
   * Fill form with validation handling
   */
  static async fillFormWithValidation(
    page: Page,
    fields: Record<string, string>,
    submitSelector: string
  ): Promise<{ success: boolean; errors: string[] }> {
    const errors: string[] = [];

    // Fill all fields
    for (const [selector, value] of Object.entries(fields)) {
      await page.locator(selector).fill(value);

      // Check for immediate validation errors
      const errorSelector = `${selector}-error`;
      const errorElement = page.locator(`[data-testid="${errorSelector}"]`);

      if (await errorElement.isVisible()) {
        const errorText = await errorElement.textContent();
        if (errorText) {
          errors.push(`${selector}: ${errorText}`);
        }
      }
    }

    // Submit form
    await page.locator(submitSelector).click();

    // Wait for submission to complete
    await page.waitForTimeout(1000);

    // Check for any validation errors after submission
    const validationErrors = page.locator('[data-testid*="validation-error"]');
    const count = await validationErrors.count();

    for (let i = 0; i < count; i++) {
      const errorText = await validationErrors.nth(i).textContent();
      if (errorText) {
        errors.push(errorText);
      }
    }

    return {
      success: errors.length === 0,
      errors
    };
  }

  /**
   * Wait for download and verify file
   */
  static async waitForDownload(
    page: Page,
    triggerCallback: () => Promise<void>,
    expectedFilename?: string | RegExp
  ): Promise<{ path: string; filename: string }> {
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      triggerCallback()
    ]);

    const filename = download.suggestedFilename();

    if (expectedFilename) {
      if (typeof expectedFilename === 'string') {
        expect(filename).toContain(expectedFilename);
      } else {
        expect(filename).toMatch(expectedFilename);
      }
    }

    const path = await download.path();
    expect(path).toBeTruthy();

    return { path: path!, filename };
  }

  /**
   * Verify table data structure and content
   */
  static async verifyTableData(
    page: Page,
    tableSelector: string,
    expectedColumns: string[],
    minRows: number = 1
  ): Promise<void> {
    const table = page.locator(tableSelector);
    await expect(table).toBeVisible();

    // Verify headers
    const headerCells = table.locator('thead th');
    const headerCount = await headerCells.count();
    expect(headerCount).toBeGreaterThanOrEqual(expectedColumns.length);

    for (let i = 0; i < expectedColumns.length; i++) {
      const headerText = await headerCells.nth(i).textContent();
      expect(headerText).toContain(expectedColumns[i]);
    }

    // Verify minimum row count
    const bodyRows = table.locator('tbody tr');
    const rowCount = await bodyRows.count();
    expect(rowCount).toBeGreaterThanOrEqual(minRows);
  }

  /**
   * Simulate user keyboard navigation
   */
  static async navigateWithKeyboard(
    page: Page,
    startSelector: string,
    keys: string[],
    expectedFinalSelector?: string
  ): Promise<void> {
    await page.locator(startSelector).focus();

    for (const key of keys) {
      await page.keyboard.press(key);
      await page.waitForTimeout(100); // Small delay between key presses
    }

    if (expectedFinalSelector) {
      const finalElement = page.locator(expectedFinalSelector);
      const isFocused = await finalElement.evaluate(el => document.activeElement === el);
      expect(isFocused).toBe(true);
    }
  }
}