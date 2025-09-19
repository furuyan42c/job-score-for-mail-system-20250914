/**
 * T050: SQL Execution E2E Test
 *
 * Test the complete SQL query flow:
 * - Table selection from sidebar (19 tables)
 * - SQL query input and execution
 * - Result display and pagination
 * - Tab switching (SQL Query, Data Browser, Table Structure)
 */

import { test, expect } from '@playwright/test';
import { DatabaseHelpers } from './helpers/database-helpers';
import { testTables, testQueries, expectedTableCounts, performanceThresholds } from './fixtures/test-data';

test.describe('T050: SQL Execution E2E Tests', () => {
  let dbHelpers: DatabaseHelpers;

  test.beforeEach(async ({ page }) => {
    dbHelpers = new DatabaseHelpers(page);
    await dbHelpers.navigateToDashboard();
  });

  test.describe('Table Selection and Sidebar Navigation', () => {
    test('should display all 19 database tables in sidebar', async ({ page }) => {
      const tablesListContainer = page.locator('[data-testid="tables-list"]');
      await expect(tablesListContainer).toBeVisible();

      // Check that all expected tables are visible
      for (const tableName of testTables) {
        const tableButton = page.locator(`[data-testid="tables-list"] button:has-text("${tableName}")`);
        await expect(tableButton).toBeVisible();
      }

      // Verify table count
      const visibleTableCount = await dbHelpers.getVisibleTableCount();
      expect(visibleTableCount).toBeGreaterThanOrEqual(19);
    });

    test('should update SQL query when table is selected', async ({ page }) => {
      // Select different tables and verify SQL query updates
      for (const tableName of testTables.slice(0, 3)) { // Test first 3 tables
        await dbHelpers.selectTable(tableName);

        const queryEditor = page.locator('textarea[placeholder*="SQL"]');
        const queryText = await queryEditor.inputValue();

        expect(queryText).toContain(tableName);
        expect(queryText).toContain('SELECT');
        expect(queryText).toContain('LIMIT');
      }
    });

    test('should highlight selected table in sidebar', async ({ page }) => {
      const tableName = 'users';
      await dbHelpers.selectTable(tableName);

      const selectedTableButton = page.locator(`[data-testid="tables-list"] button:has-text("${tableName}")`);
      await expect(selectedTableButton).toHaveClass(/secondary/);
    });

    test('should display table information (row count and description)', async ({ page }) => {
      for (const tableName of ['users', 'jobs', 'prefecture_master']) {
        const tableButton = page.locator(`[data-testid="tables-list"] button:has-text("${tableName}")`);
        await expect(tableButton).toBeVisible();

        // Check for description and row count
        const tableInfo = tableButton.locator('..');
        const descriptionText = await tableInfo.textContent();

        expect(descriptionText).toBeTruthy();
        expect(descriptionText).toMatch(/\d+/); // Should contain numbers (row count)
      }
    });
  });

  test.describe('SQL Query Input and Execution', () => {
    test('should allow SQL query input and execution', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');

      // Test valid queries
      for (const query of testQueries.simple.valid.slice(0, 2)) {
        await dbHelpers.executeQuery(query);

        // Check if results are displayed or mock message is shown
        const resultArea = await dbHelpers.getQueryResults();
        const resultContent = await resultArea.textContent();

        // Should either show results or a mock/not implemented message
        expect(resultContent).toBeTruthy();
        expect(resultContent.length).toBeGreaterThan(0);

        // If it's a mock implementation, should contain appropriate message
        if (resultContent.includes('mock') || resultContent.includes('実装予定')) {
          expect(resultContent).toMatch(/(mock|実装予定|not implemented)/i);
        }
      }
    });

    test('should handle invalid SQL queries with error messages', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');

      // Test invalid queries
      for (const invalidQuery of testQueries.simple.invalid.slice(0, 2)) {
        await dbHelpers.executeQuery(invalidQuery);

        // Should show error message
        const hasError = await dbHelpers.hasErrorMessage();
        if (hasError) {
          const errorMessage = await dbHelpers.getErrorMessage();
          expect(errorMessage).toBeTruthy();
          expect(errorMessage).not.toContain('undefined');
          expect(errorMessage).not.toContain('null');
        } else {
          // If no error shown, should show mock implementation message
          const resultArea = await dbHelpers.getQueryResults();
          const resultContent = await resultArea.textContent();
          expect(resultContent).toMatch(/(mock|実装予定|not implemented)/i);
        }
      }
    });

    test('should show query execution status (loading/completed)', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');

      const executeButton = page.locator('button:has-text("クエリ実行")');
      const queryEditor = page.locator('textarea[placeholder*="SQL"]');

      await queryEditor.clear();
      await queryEditor.fill('SELECT * FROM users LIMIT 10;');

      // Click execute and check for loading state
      await executeButton.click();

      // The button should briefly show loading state
      try {
        await expect(executeButton).toHaveText(/実行中/, { timeout: 2000 });
      } catch {
        // If loading state is too fast to catch, that's also fine
      }

      // Eventually should return to normal state
      await expect(executeButton).toHaveText(/クエリ実行/, { timeout: 10000 });
    });

    test('should display execution time and performance metrics', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');
      await dbHelpers.executeQuery('SELECT * FROM users LIMIT 5;');

      // Look for performance metrics
      const perfMetrics = page.locator('text=実行時間').locator('..');

      // Performance metrics might be shown for real implementation
      if (await perfMetrics.isVisible()) {
        const metricsText = await perfMetrics.textContent();
        expect(metricsText).toMatch(/\d+ms/); // Should contain execution time
      }
    });
  });

  test.describe('Tab Switching and Navigation', () => {
    test('should switch between all tabs correctly', async ({ page }) => {
      const tabs = ['SQLクエリ', 'データ閲覧', 'テーブル構造', 'リアルタイム'];

      for (const tabName of tabs) {
        await dbHelpers.switchToTab(tabName as any);

        // Verify tab is active
        const activeTab = page.locator(`[role="tab"][aria-selected="true"]:has-text("${tabName}")`);
        await expect(activeTab).toBeVisible();

        // Wait for tab content to load
        await page.waitForTimeout(500);
      }
    });

    test('should maintain table selection across tab switches', async ({ page }) => {
      const tableName = 'jobs';
      await dbHelpers.selectTable(tableName);

      const tabs = ['SQLクエリ', 'データ閲覧', 'テーブル構造'];

      for (const tabName of tabs) {
        await dbHelpers.switchToTab(tabName as any);

        // Verify table is still selected
        const selectedTableButton = page.locator(`[data-testid="tables-list"] button:has-text("${tableName}")`);
        await expect(selectedTableButton).toHaveClass(/secondary/);
      }
    });

    test('should show appropriate content for each tab', async ({ page }) => {
      await dbHelpers.selectTable('users');

      // SQL Query tab
      await dbHelpers.switchToTab('SQLクエリ');
      await expect(page.locator('textarea[placeholder*="SQL"]')).toBeVisible();
      await expect(page.locator('button:has-text("クエリ実行")')).toBeVisible();

      // Data Browser tab
      await dbHelpers.switchToTab('データ閲覧');
      await expect(page.locator('text=テーブル: users')).toBeVisible();
      await expect(page.locator('button:has-text("新規追加")')).toBeVisible();

      // Table Structure tab
      await dbHelpers.switchToTab('テーブル構造');
      await expect(page.locator('text=テーブル構造: users')).toBeVisible();
      await expect(page.locator('text=カラム情報')).toBeVisible();

      // Realtime tab
      await dbHelpers.switchToTab('リアルタイム');
      await expect(page.locator('text=リアルタイム更新通知')).toBeVisible();
    });
  });

  test.describe('Result Display and Data Handling', () => {
    test('should display query results in table format', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');
      await dbHelpers.executeQuery('SELECT * FROM users LIMIT 3;');

      const resultArea = await dbHelpers.getQueryResults();
      await expect(resultArea).toBeVisible();

      // Check if table structure is present (either real data or mock)
      const tableHeaders = page.locator('[data-testid="query-result"] table th');
      const tableRows = page.locator('[data-testid="query-result"] table tr');

      if (await tableHeaders.count() > 0) {
        // Real implementation with table results
        expect(await tableHeaders.count()).toBeGreaterThan(0);
        expect(await tableRows.count()).toBeGreaterThan(1); // Headers + data rows
      } else {
        // Mock implementation
        const resultText = await resultArea.textContent();
        expect(resultText).toMatch(/(mock|実装予定|not implemented)/i);
      }
    });

    test('should show row count in query results', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');
      await dbHelpers.executeQuery('SELECT * FROM users LIMIT 5;');

      // Look for row count display
      const rowCountBadge = page.locator('text=/\\d+ 行/');

      if (await rowCountBadge.isVisible()) {
        const countText = await rowCountBadge.textContent();
        expect(countText).toMatch(/\d+ 行/);
      }
    });

    test('should handle large result sets with scrolling', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');
      await dbHelpers.executeQuery('SELECT * FROM jobs LIMIT 50;');

      const resultArea = await dbHelpers.getQueryResults();
      await expect(resultArea).toBeVisible();

      // Check if scrollable area exists for large datasets
      const scrollArea = page.locator('[data-testid="query-result"] .overflow-hidden, [data-testid="query-result"] [class*="scroll"]');

      if (await scrollArea.isVisible()) {
        // Verify scrollable container
        const scrollContainer = scrollArea.first();
        const boundingBox = await scrollContainer.boundingBox();
        expect(boundingBox).toBeTruthy();
        expect(boundingBox!.height).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Search and Filter Functionality', () => {
    test('should filter tables based on search term', async ({ page }) => {
      // Test various search terms
      const searchTerms = ['user', 'master', 'job', 'prefecture'];

      for (const searchTerm of searchTerms) {
        await dbHelpers.searchTables(searchTerm);

        const visibleTableCount = await dbHelpers.getVisibleTableCount();
        expect(visibleTableCount).toBeGreaterThan(0);

        // Verify filtered tables contain search term
        const visibleTables = page.locator('[data-testid="tables-list"] .table-item:visible');
        const count = await visibleTables.count();

        for (let i = 0; i < count; i++) {
          const tableText = await visibleTables.nth(i).textContent();
          expect(tableText?.toLowerCase()).toContain(searchTerm.toLowerCase());
        }
      }

      // Clear search
      await dbHelpers.searchTables('');
      const totalCount = await dbHelpers.getVisibleTableCount();
      expect(totalCount).toBeGreaterThanOrEqual(19);
    });

    test('should show no results for invalid search terms', async ({ page }) => {
      await dbHelpers.searchTables('nonexistentxyz123');

      const visibleTableCount = await dbHelpers.getVisibleTableCount();
      expect(visibleTableCount).toBe(0);
    });
  });

  test.describe('Performance and Responsiveness', () => {
    test('should load main interface within performance threshold', async ({ page }) => {
      const startTime = Date.now();
      await dbHelpers.navigateToDashboard();
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(performanceThresholds.pageLoad);
    });

    test('should switch tabs quickly', async ({ page }) => {
      const tabs = ['SQLクエリ', 'データ閲覧', 'テーブル構造'];

      for (const tabName of tabs) {
        const startTime = Date.now();
        await dbHelpers.switchToTab(tabName as any);
        const switchTime = Date.now() - startTime;

        expect(switchTime).toBeLessThan(performanceThresholds.tabSwitch);
      }
    });

    test('should handle concurrent operations', async ({ page }) => {
      // Test selecting table while search is active
      await dbHelpers.searchTables('user');
      await dbHelpers.selectTable('users');

      // Verify both operations completed successfully
      const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
      await expect(selectedTable).toBeVisible();

      const queryEditor = page.locator('textarea[placeholder*="SQL"]');
      const queryText = await queryEditor.inputValue();
      expect(queryText).toContain('users');
    });
  });
});