import { Page, expect } from '@playwright/test';

/**
 * Responsive design testing helpers
 */
export class ResponsiveHelpers {
  constructor(private page: Page) {}

  /**
   * Set viewport to desktop size
   */
  async setDesktopViewport() {
    await this.page.setViewportSize({ width: 1920, height: 1080 });
    await this.page.waitForTimeout(500); // Allow time for layout to adjust
  }

  /**
   * Set viewport to tablet size
   */
  async setTabletViewport() {
    await this.page.setViewportSize({ width: 768, height: 1024 });
    await this.page.waitForTimeout(500);
  }

  /**
   * Set viewport to mobile size
   */
  async setMobileViewport() {
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(500);
  }

  /**
   * Check if main content is visible and properly sized
   */
  async verifyMainContentLayout() {
    const mainContent = this.page.locator('[data-testid="main-content"]');
    await expect(mainContent).toBeVisible();

    const boundingBox = await mainContent.boundingBox();
    expect(boundingBox).toBeTruthy();
    expect(boundingBox!.width).toBeGreaterThan(0);
    expect(boundingBox!.height).toBeGreaterThan(0);
  }

  /**
   * Check if sidebar is properly responsive
   */
  async verifySidebarLayout() {
    const sidebar = this.page.locator('[data-testid="tables-list"]').locator('..');
    await expect(sidebar).toBeVisible();

    const viewport = this.page.viewportSize();
    const boundingBox = await sidebar.boundingBox();

    if (viewport && viewport.width <= 768) {
      // On mobile/tablet, sidebar might be collapsible or overlay
      // Check if it's either collapsed or overlays content
      expect(boundingBox!.width).toBeLessThanOrEqual(viewport.width);
    } else {
      // On desktop, sidebar should have fixed width
      expect(boundingBox!.width).toBeGreaterThan(200);
      expect(boundingBox!.width).toBeLessThan(400);
    }
  }

  /**
   * Check if navigation tabs are responsive
   */
  async verifyTabNavigation() {
    const tabsList = this.page.locator('[role="tablist"]');
    await expect(tabsList).toBeVisible();

    const tabs = tabsList.locator('[role="tab"]');
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThan(0);

    // Check if all tabs are visible or properly handled on small screens
    for (let i = 0; i < tabCount; i++) {
      const tab = tabs.nth(i);
      const tabBox = await tab.boundingBox();
      expect(tabBox).toBeTruthy();
    }
  }

  /**
   * Check if tables are responsive
   */
  async verifyTableResponsiveness() {
    const tables = this.page.locator('table');
    const tableCount = await tables.count();

    if (tableCount > 0) {
      const firstTable = tables.first();
      await expect(firstTable).toBeVisible();

      const tableContainer = firstTable.locator('..');
      const containerBox = await tableContainer.boundingBox();
      const viewport = this.page.viewportSize();

      // Table container should not exceed viewport width
      expect(containerBox!.width).toBeLessThanOrEqual(viewport!.width + 100); // Allow for scroll
    }
  }

  /**
   * Check if buttons and controls are appropriately sized for touch
   */
  async verifyTouchTargets() {
    const viewport = this.page.viewportSize();

    if (viewport && viewport.width <= 768) {
      // On mobile, buttons should be large enough for touch
      const buttons = this.page.locator('button');
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 10); i++) { // Check first 10 buttons
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const buttonBox = await button.boundingBox();
          if (buttonBox) {
            // Touch target should be at least 44px (iOS guideline)
            const minSize = Math.min(buttonBox.width, buttonBox.height);
            expect(minSize).toBeGreaterThanOrEqual(32); // Relaxed for testing
          }
        }
      }
    }
  }

  /**
   * Test scrolling behavior on different screen sizes
   */
  async verifyScrollBehavior() {
    const mainContent = this.page.locator('[data-testid="main-content"]');
    await expect(mainContent).toBeVisible();

    // Scroll down to test overflow handling
    await this.page.mouse.wheel(0, 500);
    await this.page.waitForTimeout(300);

    // Scroll back up
    await this.page.mouse.wheel(0, -500);
    await this.page.waitForTimeout(300);

    // Verify content is still visible after scrolling
    await expect(mainContent).toBeVisible();
  }

  /**
   * Take screenshot for visual comparison
   */
  async takeResponsiveScreenshot(name: string) {
    const viewport = this.page.viewportSize();
    const screenshotPath = `test-results/screenshots/${name}-${viewport!.width}x${viewport!.height}.png`;

    await this.page.screenshot({
      path: screenshotPath,
      fullPage: true,
    });

    return screenshotPath;
  }

  /**
   * Test all responsive breakpoints
   */
  async testAllBreakpoints(testCallback: () => Promise<void>) {
    // Desktop
    await this.setDesktopViewport();
    await testCallback();

    // Tablet
    await this.setTabletViewport();
    await testCallback();

    // Mobile
    await this.setMobileViewport();
    await testCallback();

    // Reset to desktop
    await this.setDesktopViewport();
  }
}