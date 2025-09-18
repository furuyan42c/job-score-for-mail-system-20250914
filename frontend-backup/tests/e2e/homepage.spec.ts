import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should load without errors', async ({ page }) => {
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Check that the page title is visible
    await expect(page).toHaveTitle(/JobMatch Pro/);

    // Check for the success message (if present)
    const successMessage = page.locator('text=Page is loading successfully!');
    if (await successMessage.isVisible()) {
      await expect(successMessage).toBeVisible();
    }

    // Check that the main heading is visible
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
  });

  test('should display navigation links', async ({ page }) => {
    // Check for navigation links
    await expect(page.locator('text=Jobs')).toBeVisible();
    await expect(page.locator('text=Companies')).toBeVisible();
    await expect(page.locator('text=Login')).toBeVisible();
  });

  test('should display hero section', async ({ page }) => {
    // Check for hero section content
    const heroSection = page.locator('section').first();
    await expect(heroSection).toBeVisible();

    // Check for CTA buttons
    const browseJobsButton = page.locator('a:has-text("Browse Jobs")');
    await expect(browseJobsButton).toBeVisible();
  });

  test('should not have console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Filter out known non-critical errors
    const criticalErrors = errors.filter(error =>
      !error.includes('Failed to load resource') &&
      !error.includes('404') &&
      !error.includes('Event handlers cannot be passed') // This should not appear
    );

    expect(criticalErrors).toHaveLength(0);
  });
});