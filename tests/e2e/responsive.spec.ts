/**
 * T052: UIレスポンシブE2Eテスト
 * Responsive Design E2E Tests
 *
 * Tests the application's responsive behavior across different viewport sizes:
 * 1. Desktop (1920x1080) - Full desktop experience
 * 2. Tablet (768x1024) - Tablet portrait mode
 * 3. Mobile (375x667) - Mobile phone experience
 *
 * Dependencies: T045 (Tailwind CSS styling and responsive design)
 * Testing Framework: Playwright
 */

import { test, expect, Page } from '@playwright/test';

// Viewport configurations for responsive testing
const VIEWPORTS = {
  desktop: { width: 1920, height: 1080, name: 'Desktop' },
  tablet: { width: 768, height: 1024, name: 'Tablet' },
  mobile: { width: 375, height: 667, name: 'Mobile' }
} as const;

// Key UI elements to test for responsive behavior
const UI_ELEMENTS = {
  header: '[data-testid="header"], header, .header',
  navigation: '[data-testid="navigation"], nav, .nav',
  sidebar: '[data-testid="sidebar"], .sidebar, aside',
  mainContent: '[data-testid="main-content"], main, .main-content',
  sqlEditor: '[data-testid="sql-editor"], .sql-editor, textarea',
  resultsTable: '[data-testid="results-table"], .results-table, table',
  mobileMenu: '[data-testid="mobile-menu"], .mobile-menu',
  tabletMenu: '[data-testid="tablet-menu"], .tablet-menu'
} as const;

test.describe('Responsive Design E2E Tests', () => {

  // Test each viewport size
  Object.entries(VIEWPORTS).forEach(([device, viewport]) => {
    test.describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {

      test.beforeEach(async ({ page }) => {
        // Set viewport size
        await page.setViewportSize(viewport);

        // Navigate to the main application
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');
      });

      test(`should display properly on ${viewport.name}`, async ({ page }) => {
        await test.step('Verify page loads without layout issues', async () => {
          // Check that the page doesn't have horizontal scrollbars
          const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
          const windowInnerWidth = await page.evaluate(() => window.innerWidth);

          expect(bodyScrollWidth).toBeLessThanOrEqual(windowInnerWidth + 5); // Allow 5px tolerance
        });

        await test.step('Verify header responsiveness', async () => {
          const header = page.locator(UI_ELEMENTS.header).first();
          await expect(header).toBeVisible();

          const headerBox = await header.boundingBox();
          expect(headerBox?.width).toBeGreaterThan(0);
          expect(headerBox?.width).toBeLessThanOrEqual(viewport.width);
        });

        await test.step('Verify main content area', async () => {
          const mainContent = page.locator(UI_ELEMENTS.mainContent).first();

          if (await mainContent.count() > 0) {
            await expect(mainContent).toBeVisible();

            const contentBox = await mainContent.boundingBox();
            expect(contentBox?.width).toBeGreaterThan(0);
            expect(contentBox?.width).toBeLessThanOrEqual(viewport.width);
          }
        });
      });

      test(`should handle navigation on ${viewport.name}`, async ({ page }) => {
        if (device === 'mobile') {
          await test.step('Verify mobile navigation behavior', async () => {
            // Look for mobile menu trigger
            const mobileMenuTrigger = page.locator('button[aria-label*="menu"], .menu-toggle, [data-testid="mobile-menu-toggle"]').first();

            if (await mobileMenuTrigger.count() > 0) {
              await expect(mobileMenuTrigger).toBeVisible();

              // Test mobile menu toggle
              await mobileMenuTrigger.click();

              // Check if mobile menu appears
              const mobileMenu = page.locator(UI_ELEMENTS.mobileMenu).first();
              if (await mobileMenu.count() > 0) {
                await expect(mobileMenu).toBeVisible();
              }
            }
          });
        } else if (device === 'tablet') {
          await test.step('Verify tablet navigation behavior', async () => {
            // Tablet should show either full navigation or condensed version
            const navigation = page.locator(UI_ELEMENTS.navigation).first();

            if (await navigation.count() > 0) {
              await expect(navigation).toBeVisible();

              const navBox = await navigation.boundingBox();
              expect(navBox?.width).toBeLessThanOrEqual(viewport.width);
            }
          });
        } else {
          await test.step('Verify desktop navigation behavior', async () => {
            // Desktop should show full navigation
            const navigation = page.locator(UI_ELEMENTS.navigation).first();

            if (await navigation.count() > 0) {
              await expect(navigation).toBeVisible();
            }
          });
        }
      });

      test(`should handle SQL editor responsively on ${viewport.name}`, async ({ page }) => {
        await test.step('Navigate to SQL editor if needed', async () => {
          // Look for SQL tab or SQL editor section
          const sqlTab = page.locator('text="SQL" >> visible=true, [data-testid="sql-tab"], .sql-tab').first();

          if (await sqlTab.count() > 0) {
            await sqlTab.click();
            await page.waitForTimeout(500); // Wait for tab transition
          }
        });

        await test.step('Verify SQL editor responsiveness', async () => {
          const sqlEditor = page.locator(UI_ELEMENTS.sqlEditor).first();

          if (await sqlEditor.count() > 0) {
            await expect(sqlEditor).toBeVisible();

            const editorBox = await sqlEditor.boundingBox();
            expect(editorBox?.width).toBeGreaterThan(0);
            expect(editorBox?.width).toBeLessThanOrEqual(viewport.width - 40); // Account for padding

            // Test that editor is usable
            await sqlEditor.click();
            await sqlEditor.fill('SELECT 1;');

            const editorValue = await sqlEditor.inputValue();
            expect(editorValue).toBe('SELECT 1;');
          }
        });

        await test.step('Verify execute button accessibility', async () => {
          const executeButton = page.locator('button:has-text("Execute"), button:has-text("実行"), [data-testid="execute-button"]').first();

          if (await executeButton.count() > 0) {
            await expect(executeButton).toBeVisible();

            const buttonBox = await executeButton.boundingBox();

            // Button should be appropriately sized for the viewport
            if (device === 'mobile') {
              expect(buttonBox?.height).toBeGreaterThanOrEqual(44); // Minimum touch target
            }
          }
        });
      });

      test(`should handle results table responsively on ${viewport.name}`, async ({ page }) => {
        await test.step('Execute a query to generate results', async () => {
          const sqlEditor = page.locator(UI_ELEMENTS.sqlEditor).first();

          if (await sqlEditor.count() > 0) {
            await sqlEditor.fill('SELECT 1 as id, "test" as name, "example@test.com" as email;');

            const executeButton = page.locator('button:has-text("Execute"), button:has-text("実行"), [data-testid="execute-button"]').first();

            if (await executeButton.count() > 0) {
              await executeButton.click();
              await page.waitForTimeout(1000); // Wait for query execution
            }
          }
        });

        await test.step('Verify results table responsiveness', async () => {
          const resultsTable = page.locator(UI_ELEMENTS.resultsTable).first();

          if (await resultsTable.count() > 0) {
            await expect(resultsTable).toBeVisible();

            const tableBox = await resultsTable.boundingBox();
            expect(tableBox?.width).toBeLessThanOrEqual(viewport.width);

            // Check for horizontal scrolling on mobile/tablet if table is wide
            if (device !== 'desktop') {
              const tableContainer = page.locator('.table-container, .overflow-x-auto').first();

              if (await tableContainer.count() > 0) {
                const containerBox = await tableContainer.boundingBox();
                expect(containerBox?.width).toBeLessThanOrEqual(viewport.width);
              }
            }
          }
        });

        await test.step('Verify table interactions work on touch devices', async () => {
          if (device !== 'desktop') {
            const tableRows = page.locator('tr').nth(1); // First data row

            if (await tableRows.count() > 0) {
              // Test touch/click interaction
              await tableRows.click();

              // Verify no layout issues after interaction
              const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
              const windowInnerWidth = await page.evaluate(() => window.innerWidth);

              expect(bodyScrollWidth).toBeLessThanOrEqual(windowInnerWidth + 5);
            }
          }
        });
      });

      test(`should handle sidebar responsively on ${viewport.name}`, async ({ page }) => {
        await test.step('Check sidebar behavior', async () => {
          const sidebar = page.locator(UI_ELEMENTS.sidebar).first();

          if (await sidebar.count() > 0) {
            if (device === 'mobile') {
              // Mobile sidebar should be hidden by default or collapsible
              const sidebarBox = await sidebar.boundingBox();

              if (sidebarBox) {
                // Either sidebar is hidden (width 0) or takes full width when open
                expect(sidebarBox.width === 0 || sidebarBox.width >= viewport.width * 0.8).toBeTruthy();
              }
            } else if (device === 'tablet') {
              // Tablet sidebar might be condensed or overlay
              await expect(sidebar).toBeVisible();

              const sidebarBox = await sidebar.boundingBox();
              if (sidebarBox) {
                expect(sidebarBox.width).toBeLessThanOrEqual(viewport.width * 0.5);
              }
            } else {
              // Desktop sidebar should be fully visible
              await expect(sidebar).toBeVisible();
            }
          }
        });

        await test.step('Test sidebar table list on different devices', async () => {
          // Look for table list items
          const tableItems = page.locator('[data-testid="table-item"], .table-item, li:has-text("users"), li:has-text("jobs")');

          if (await tableItems.count() > 0) {
            const firstTable = tableItems.first();
            await expect(firstTable).toBeVisible();

            // Test interaction
            await firstTable.click();
            await page.waitForTimeout(500);

            // Verify no layout issues after interaction
            const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
            const windowInnerWidth = await page.evaluate(() => window.innerWidth);

            expect(bodyScrollWidth).toBeLessThanOrEqual(windowInnerWidth + 5);
          }
        });
      });

      test(`should maintain text readability on ${viewport.name}`, async ({ page }) => {
        await test.step('Check font sizes and text readability', async () => {
          // Test various text elements
          const textElements = await page.locator('h1, h2, h3, p, span, td, th').all();

          for (const element of textElements.slice(0, 10)) { // Test first 10 elements
            if (await element.isVisible()) {
              const fontSize = await element.evaluate(el => getComputedStyle(el).fontSize);
              const fontSizeNum = parseInt(fontSize.replace('px', ''));

              // Minimum font sizes for readability
              const minFontSize = device === 'mobile' ? 14 : device === 'tablet' ? 13 : 12;

              expect(fontSizeNum).toBeGreaterThanOrEqual(minFontSize);
            }
          }
        });

        await test.step('Check line height and spacing', async () => {
          const textElements = page.locator('p, div, span').first();

          if (await textElements.count() > 0) {
            const lineHeight = await textElements.evaluate(el => getComputedStyle(el).lineHeight);

            // Line height should be reasonable (not 'normal' and not too tight)
            if (lineHeight !== 'normal') {
              const lineHeightNum = parseFloat(lineHeight);
              expect(lineHeightNum).toBeGreaterThan(1.2);
            }
          }
        });
      });

      test(`should handle form inputs properly on ${viewport.name}`, async ({ page }) => {
        await test.step('Test input field accessibility', async () => {
          const inputs = page.locator('input, textarea, select');

          if (await inputs.count() > 0) {
            const firstInput = inputs.first();
            await expect(firstInput).toBeVisible();

            const inputBox = await firstInput.boundingBox();

            if (inputBox) {
              // Input should be appropriately sized for touch on mobile
              if (device === 'mobile') {
                expect(inputBox.height).toBeGreaterThanOrEqual(44); // Minimum touch target
              }

              // Input should not overflow viewport
              expect(inputBox.width).toBeLessThanOrEqual(viewport.width - 20);
            }

            // Test input functionality
            await firstInput.click();
            await firstInput.fill('test input');

            const inputValue = await firstInput.inputValue();
            expect(inputValue).toBe('test input');
          }
        });
      });

      test(`should handle scrolling properly on ${viewport.name}`, async ({ page }) => {
        await test.step('Test vertical scrolling behavior', async () => {
          const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
          const windowHeight = await page.evaluate(() => window.innerHeight);

          if (bodyHeight > windowHeight) {
            // Test scrolling to bottom
            await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

            const scrollY = await page.evaluate(() => window.scrollY);
            expect(scrollY).toBeGreaterThan(0);

            // Scroll back to top
            await page.evaluate(() => window.scrollTo(0, 0));

            const topScrollY = await page.evaluate(() => window.scrollY);
            expect(topScrollY).toBe(0);
          }
        });

        await test.step('Test horizontal scrolling prevention', async () => {
          const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
          const windowInnerWidth = await page.evaluate(() => window.innerWidth);

          // Body should not be wider than viewport (within small tolerance)
          expect(bodyScrollWidth).toBeLessThanOrEqual(windowInnerWidth + 5);
        });
      });
    });
  });

  // Cross-viewport comparison tests
  test.describe('Cross-Viewport Consistency', () => {
    test('should maintain consistent functionality across all viewports', async ({ browser }) => {
      const contexts = await Promise.all(
        Object.entries(VIEWPORTS).map(async ([device, viewport]) => {
          const context = await browser.newContext({ viewport });
          const page = await context.newPage();
          await page.goto('/');
          await page.waitForLoadState('networkidle');
          return { device, page, context };
        })
      );

      try {
        await test.step('Test SQL execution works on all viewports', async () => {
          const testQuery = 'SELECT 1 as test_column;';

          for (const { device, page } of contexts) {
            const sqlEditor = page.locator(UI_ELEMENTS.sqlEditor).first();

            if (await sqlEditor.count() > 0) {
              await sqlEditor.fill(testQuery);

              const executeButton = page.locator('button:has-text("Execute"), button:has-text("実行")').first();

              if (await executeButton.count() > 0) {
                await executeButton.click();
                await page.waitForTimeout(1000);

                // Verify results appear
                const results = page.locator('table, .results');
                if (await results.count() > 0) {
                  await expect(results.first()).toBeVisible();
                }
              }
            }
          }
        });

        await test.step('Test navigation consistency', async () => {
          for (const { device, page } of contexts) {
            // Each viewport should have some form of navigation
            const hasNavigation = await page.locator('nav, .nav, [role="navigation"]').count() > 0 ||
                                await page.locator('button[aria-label*="menu"]').count() > 0;

            expect(hasNavigation).toBeTruthy();
          }
        });

      } finally {
        // Clean up contexts
        for (const { context } of contexts) {
          await context.close();
        }
      }
    });
  });

  // Performance tests across viewports
  test.describe('Responsive Performance', () => {
    test('should load quickly on all viewport sizes', async ({ page }) => {
      for (const [device, viewport] of Object.entries(VIEWPORTS)) {
        await test.step(`Test ${device} loading performance`, async () => {
          await page.setViewportSize(viewport);

          const startTime = Date.now();
          await page.goto('/', { waitUntil: 'networkidle' });
          const loadTime = Date.now() - startTime;

          // All viewports should load within reasonable time (5 seconds)
          expect(loadTime).toBeLessThan(5000);

          // Check for layout shift
          const layoutShift = await page.evaluate(() => {
            return new Promise((resolve) => {
              let cumulativeLayoutShift = 0;
              new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                  if (entry.entryType === 'layout-shift') {
                    cumulativeLayoutShift += (entry as any).value;
                  }
                }
                setTimeout(() => resolve(cumulativeLayoutShift), 2000);
              }).observe({ entryTypes: ['layout-shift'] });
            });
          });

          // Layout shift should be minimal (< 0.1 is good)
          expect(layoutShift).toBeLessThan(0.2);
        });
      }
    });
  });
});

/**
 * Helper function to take screenshots for visual regression testing
 */
async function takeResponsiveScreenshots(page: Page, testName: string) {
  for (const [device, viewport] of Object.entries(VIEWPORTS)) {
    await page.setViewportSize(viewport);
    await page.screenshot({
      path: `screenshots/${testName}-${device}-${viewport.width}x${viewport.height}.png`,
      fullPage: true
    });
  }
}

// Export utility for other tests to use
export { VIEWPORTS, UI_ELEMENTS, takeResponsiveScreenshots };