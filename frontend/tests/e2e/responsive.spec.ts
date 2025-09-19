/**
 * T052: UI Responsive E2E Test
 *
 * Test responsive design:
 * - Desktop (1920x1080) display
 * - Tablet (768x1024) display
 * - Mobile (375x667) display
 * - Verify all UI elements adapt properly
 */

import { test, expect } from '@playwright/test';
import { DatabaseHelpers } from './helpers/database-helpers';
import { ResponsiveHelpers } from './helpers/responsive-helpers';
import { testViewports, testTables, performanceThresholds } from './fixtures/test-data';

test.describe('T052: Responsive UI E2E Tests', () => {
  let dbHelpers: DatabaseHelpers;
  let responsiveHelpers: ResponsiveHelpers;

  test.beforeEach(async ({ page }) => {
    dbHelpers = new DatabaseHelpers(page);
    responsiveHelpers = new ResponsiveHelpers(page);
    await dbHelpers.navigateToDashboard();
  });

  test.describe('Desktop Layout (1920x1080)', () => {
    test.beforeEach(async () => {
      await responsiveHelpers.setDesktopViewport();
    });

    test('should display full desktop layout correctly', async ({ page }) => {
      await responsiveHelpers.verifyMainContentLayout();
      await responsiveHelpers.verifySidebarLayout();

      // Verify desktop-specific elements
      const sidebar = page.locator('[data-testid="tables-list"]').locator('..');
      const mainContent = page.locator('[data-testid="main-content"]');

      const sidebarBox = await sidebar.boundingBox();
      const mainBox = await mainContent.boundingBox();

      // Sidebar should have reasonable width on desktop
      expect(sidebarBox!.width).toBeGreaterThan(250);
      expect(sidebarBox!.width).toBeLessThan(400);

      // Main content should take remaining space
      expect(mainBox!.width).toBeGreaterThan(1000);
    });

    test('should show all navigation elements clearly', async ({ page }) => {
      await responsiveHelpers.verifyTabNavigation();

      // Check header elements
      const header = page.locator('header');
      await expect(header).toBeVisible();

      const headerButtons = header.locator('button');
      const buttonCount = await headerButtons.count();
      expect(buttonCount).toBeGreaterThan(0);

      // All buttons should be fully visible
      for (let i = 0; i < buttonCount; i++) {
        const button = headerButtons.nth(i);
        await expect(button).toBeVisible();

        const buttonBox = await button.boundingBox();
        expect(buttonBox!.width).toBeGreaterThan(0);
      }
    });

    test('should display tables with full column visibility', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('データ閲覧');

      const table = page.locator('table').first();
      await expect(table).toBeVisible();

      const headers = table.locator('thead th');
      const headerCount = await headers.count();

      // On desktop, all columns should be visible
      expect(headerCount).toBeGreaterThan(5);

      // Check column widths are reasonable
      for (let i = 0; i < Math.min(headerCount, 5); i++) {
        const header = headers.nth(i);
        const headerBox = await header.boundingBox();
        expect(headerBox!.width).toBeGreaterThan(50);
      }
    });

    test('should handle side-by-side content layout', async ({ page }) => {
      await dbHelpers.switchToTab('テーブル構造');

      // Check for grid layout cards
      const gridContainer = page.locator('[class*="grid"]');
      if (await gridContainer.isVisible()) {
        const cards = gridContainer.locator('[class*="Card"], .card');
        const cardCount = await cards.count();

        if (cardCount >= 2) {
          // Cards should be side by side on desktop
          const firstCard = cards.first();
          const secondCard = cards.nth(1);

          const firstBox = await firstCard.boundingBox();
          const secondBox = await secondCard.boundingBox();

          // Cards should be on same row (similar y coordinates)
          expect(Math.abs(firstBox!.y - secondBox!.y)).toBeLessThan(50);
        }
      }
    });
  });

  test.describe('Tablet Layout (768x1024)', () => {
    test.beforeEach(async () => {
      await responsiveHelpers.setTabletViewport();
    });

    test('should adapt layout for tablet viewport', async ({ page }) => {
      await responsiveHelpers.verifyMainContentLayout();
      await responsiveHelpers.verifySidebarLayout();

      // Verify tablet-specific adaptations
      const viewport = page.viewportSize();
      expect(viewport!.width).toBe(768);

      // Content should fit within viewport
      const mainContent = page.locator('[data-testid="main-content"]');
      const mainBox = await mainContent.boundingBox();
      expect(mainBox!.width).toBeLessThanOrEqual(768);
    });

    test('should show responsive navigation elements', async ({ page }) => {
      await responsiveHelpers.verifyTabNavigation();

      // Tab navigation should still be accessible
      const tabsList = page.locator('[role="tablist"]');
      await expect(tabsList).toBeVisible();

      const tabs = tabsList.locator('[role="tab"]');
      const tabCount = await tabs.count();

      // All tabs should fit or be scrollable
      for (let i = 0; i < tabCount; i++) {
        const tab = tabs.nth(i);
        if (await tab.isVisible()) {
          const tabBox = await tab.boundingBox();
          expect(tabBox!.width).toBeGreaterThan(0);
        }
      }
    });

    test('should maintain table readability', async ({ page }) => {
      await responsiveHelpers.verifyTableResponsiveness();

      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('データ閲覧');

      const tableContainer = page.locator('table').locator('..');
      const containerBox = await tableContainer.boundingBox();

      // Table should not exceed viewport width
      expect(containerBox!.width).toBeLessThanOrEqual(768 + 50); // Allow for scroll
    });

    test('should stack cards appropriately', async ({ page }) => {
      await dbHelpers.switchToTab('テーブル構造');

      const gridContainer = page.locator('[class*="grid"]');
      if (await gridContainer.isVisible()) {
        const cards = gridContainer.locator('[class*="Card"], .card');
        const cardCount = await cards.count();

        if (cardCount >= 2) {
          // Cards might stack on tablet
          const firstCard = cards.first();
          const secondCard = cards.nth(1);

          const firstBox = await firstCard.boundingBox();
          const secondBox = await secondCard.boundingBox();

          // Cards should either be side by side or stacked
          const isStacked = Math.abs(firstBox!.y - secondBox!.y) > 100;
          const isSideBySide = Math.abs(firstBox!.y - secondBox!.y) < 50;

          expect(isStacked || isSideBySide).toBeTruthy();
        }
      }
    });
  });

  test.describe('Mobile Layout (375x667)', () => {
    test.beforeEach(async () => {
      await responsiveHelpers.setMobileViewport();
    });

    test('should optimize layout for mobile viewport', async ({ page }) => {
      await responsiveHelpers.verifyMainContentLayout();
      await responsiveHelpers.verifyTouchTargets();

      const viewport = page.viewportSize();
      expect(viewport!.width).toBe(375);

      // All content should fit within mobile viewport
      const body = page.locator('body');
      const bodyBox = await body.boundingBox();
      expect(bodyBox!.width).toBeLessThanOrEqual(375);
    });

    test('should provide mobile-friendly navigation', async ({ page }) => {
      await responsiveHelpers.verifyTabNavigation();

      // Check if navigation is accessible on mobile
      const tabsList = page.locator('[role="tablist"]');
      await expect(tabsList).toBeVisible();

      // Tabs should be readable on mobile
      const tabs = tabsList.locator('[role="tab"]');
      const visibleTabs = await tabs.count();

      for (let i = 0; i < visibleTabs; i++) {
        const tab = tabs.nth(i);
        if (await tab.isVisible()) {
          const tabBox = await tab.boundingBox();
          // Tab should have reasonable touch target size
          expect(Math.min(tabBox!.width, tabBox!.height)).toBeGreaterThan(30);
        }
      }
    });

    test('should handle mobile table display', async ({ page }) => {
      await responsiveHelpers.verifyTableResponsiveness();

      await dbHelpers.selectTable('prefecture_master'); // Smaller table
      await dbHelpers.switchToTab('データ閲覧');

      const table = page.locator('table').first();
      if (await table.isVisible()) {
        const tableBox = await table.boundingBox();

        // Table should fit within mobile viewport or be scrollable
        expect(tableBox!.width).toBeLessThanOrEqual(375 + 100); // Allow for scroll
      }
    });

    test('should stack content vertically', async ({ page }) => {
      await dbHelpers.switchToTab('テーブル構造');

      // Cards should definitely stack on mobile
      const gridContainer = page.locator('[class*="grid"]');
      if (await gridContainer.isVisible()) {
        const cards = gridContainer.locator('[class*="Card"], .card');
        const cardCount = await cards.count();

        if (cardCount >= 2) {
          const firstCard = cards.first();
          const secondCard = cards.nth(1);

          const firstBox = await firstCard.boundingBox();
          const secondBox = await secondCard.boundingBox();

          // Cards should be stacked vertically
          expect(Math.abs(firstBox!.y - secondBox!.y)).toBeGreaterThan(50);
        }
      }
    });

    test('should optimize touch interactions', async ({ page }) => {
      await responsiveHelpers.verifyTouchTargets();

      // Test button interactions on mobile
      const buttons = page.locator('button').filter({ hasText: /実行|クエリ|フィルター/ });
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 3); i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const buttonBox = await button.boundingBox();

          // Touch targets should be at least 32px
          const minDimension = Math.min(buttonBox!.width, buttonBox!.height);
          expect(minDimension).toBeGreaterThan(30);
        }
      }
    });

    test('should handle mobile sidebar appropriately', async ({ page }) => {
      const sidebar = page.locator('[data-testid="tables-list"]').locator('..');

      if (await sidebar.isVisible()) {
        const sidebarBox = await sidebar.boundingBox();

        // Sidebar should not take up entire mobile width or should be collapsible
        expect(sidebarBox!.width).toBeLessThan(300);
      }
    });
  });

  test.describe('Cross-Viewport Functionality', () => {
    test('should maintain functionality across all viewports', async ({ page }) => {
      const viewports = [
        { name: 'Desktop', set: () => responsiveHelpers.setDesktopViewport() },
        { name: 'Tablet', set: () => responsiveHelpers.setTabletViewport() },
        { name: 'Mobile', set: () => responsiveHelpers.setMobileViewport() }
      ];

      for (const viewport of viewports) {
        await viewport.set();

        // Basic functionality should work on all viewports
        await dbHelpers.selectTable('users');

        const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
        await expect(selectedTable).toBeVisible();

        // Tab switching should work
        await dbHelpers.switchToTab('SQLクエリ');
        const activeTab = page.locator('[role="tab"][aria-selected="true"]');
        await expect(activeTab).toBeVisible();
      }
    });

    test('should handle viewport transitions smoothly', async ({ page }) => {
      // Start with desktop
      await responsiveHelpers.setDesktopViewport();
      await dbHelpers.selectTable('jobs');
      await dbHelpers.switchToTab('データ閲覧');

      // Transition to tablet
      await responsiveHelpers.setTabletViewport();
      await page.waitForTimeout(500); // Allow layout to adjust

      // Verify functionality is maintained
      const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
      await expect(selectedTable).toBeVisible();

      // Transition to mobile
      await responsiveHelpers.setMobileViewport();
      await page.waitForTimeout(500);

      // Verify functionality is still maintained
      await expect(selectedTable).toBeVisible();
    });

    test('should maintain search functionality across viewports', async ({ page }) => {
      await responsiveHelpers.testAllBreakpoints(async () => {
        await dbHelpers.searchTables('user');

        const visibleCount = await dbHelpers.getVisibleTableCount();
        expect(visibleCount).toBeGreaterThan(0);
        expect(visibleCount).toBeLessThan(testTables.length);

        // Clear search
        await dbHelpers.searchTables('');
      });
    });

    test('should handle performance consistently across viewports', async ({ page }) => {
      const viewports = [
        responsiveHelpers.setDesktopViewport,
        responsiveHelpers.setTabletViewport,
        responsiveHelpers.setMobileViewport
      ];

      for (const setViewport of viewports) {
        await setViewport();

        const startTime = Date.now();
        await dbHelpers.selectTable('prefecture_master');
        await dbHelpers.switchToTab('テーブル構造');
        const actionTime = Date.now() - startTime;

        expect(actionTime).toBeLessThan(performanceThresholds.tabSwitch * 2); // Allow extra time for mobile
      }
    });
  });

  test.describe('Visual Regression and Layout Consistency', () => {
    test('should maintain visual consistency across breakpoints', async ({ page }) => {
      const testCases = [
        { viewport: 'desktop', set: () => responsiveHelpers.setDesktopViewport() },
        { viewport: 'tablet', set: () => responsiveHelpers.setTabletViewport() },
        { viewport: 'mobile', set: () => responsiveHelpers.setMobileViewport() }
      ];

      for (const testCase of testCases) {
        await testCase.set();
        await dbHelpers.selectTable('users');

        // Take screenshots for visual comparison
        await responsiveHelpers.takeResponsiveScreenshot(`dashboard-${testCase.viewport}`);

        // Verify key elements are present
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        await expect(page.locator('[data-testid="tables-list"]')).toBeVisible();
      }
    });

    test('should handle edge cases in viewport sizes', async ({ page }) => {
      const edgeCases = [
        { width: 320, height: 568 }, // iPhone SE
        { width: 1024, height: 768 }, // iPad landscape
        { width: 1366, height: 768 }, // Common laptop
        { width: 2560, height: 1440 } // 4K display
      ];

      for (const viewport of edgeCases) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        // Basic layout should work
        await responsiveHelpers.verifyMainContentLayout();

        // No horizontal overflow should occur
        const body = page.locator('body');
        const bodyBox = await body.boundingBox();
        expect(bodyBox!.width).toBeLessThanOrEqual(viewport.width + 20); // Small tolerance
      }
    });

    test('should maintain accessibility across viewports', async ({ page }) => {
      await responsiveHelpers.testAllBreakpoints(async () => {
        // Check for essential ARIA labels and roles
        const tabList = page.locator('[role="tablist"]');
        await expect(tabList).toBeVisible();

        const tabs = page.locator('[role="tab"]');
        const tabCount = await tabs.count();
        expect(tabCount).toBeGreaterThan(0);

        // Check for main content landmark
        const mainContent = page.locator('[data-testid="main-content"]');
        await expect(mainContent).toBeVisible();
      });
    });

    test('should handle dynamic content resizing', async ({ page }) => {
      await responsiveHelpers.setMobileViewport();

      // Test with different table selections that might have different content sizes
      const tables = ['prefecture_master', 'users', 'jobs_contents_raw'];

      for (const tableName of tables) {
        await dbHelpers.selectTable(tableName);
        await dbHelpers.switchToTab('データ閲覧');

        // Content should adapt to the available space
        const mainContent = page.locator('[data-testid="main-content"]');
        const contentBox = await mainContent.boundingBox();
        expect(contentBox!.width).toBeLessThanOrEqual(375);

        await page.waitForTimeout(300); // Allow for content adjustment
      }
    });
  });

  test.describe('Responsive Interaction Patterns', () => {
    test('should support appropriate input methods per device', async ({ page }) => {
      // Test scroll behavior on different viewports
      await responsiveHelpers.testAllBreakpoints(async () => {
        await responsiveHelpers.verifyScrollBehavior();

        // Verify scrollable areas are accessible
        const scrollAreas = page.locator('[class*="scroll"]');
        const scrollCount = await scrollAreas.count();

        if (scrollCount > 0) {
          const firstScrollArea = scrollAreas.first();
          if (await firstScrollArea.isVisible()) {
            const scrollBox = await firstScrollArea.boundingBox();
            expect(scrollBox!.height).toBeGreaterThan(0);
          }
        }
      });
    });

    test('should optimize content density per viewport', async ({ page }) => {
      // Desktop should show more information density
      await responsiveHelpers.setDesktopViewport();
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('データ閲覧');

      const desktopRows = page.locator('table tbody tr');
      const desktopRowCount = await desktopRows.count();

      // Mobile should potentially show fewer rows or different layout
      await responsiveHelpers.setMobileViewport();
      await page.waitForTimeout(500);

      const mobileRows = page.locator('table tbody tr');
      const mobileRowCount = await mobileRows.count();

      // Both should show content, but density might differ
      expect(desktopRowCount).toBeGreaterThan(0);
      expect(mobileRowCount).toBeGreaterThan(0);
    });

    test('should handle orientation changes gracefully', async ({ page }) => {
      // Simulate tablet portrait to landscape
      await page.setViewportSize({ width: 768, height: 1024 }); // Portrait
      await dbHelpers.selectTable('jobs');

      await page.setViewportSize({ width: 1024, height: 768 }); // Landscape
      await page.waitForTimeout(500);

      // Content should still be accessible
      await responsiveHelpers.verifyMainContentLayout();

      const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
      await expect(selectedTable).toBeVisible();
    });
  });
});