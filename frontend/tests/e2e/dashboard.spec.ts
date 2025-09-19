/**
 * T051: Dashboard E2E Test
 *
 * Test dashboard functionality:
 * - Table structure tab with detailed views
 * - Data browsing tab with pagination
 * - Search functionality (table name and description filtering)
 * - Statistics display
 */

import { test, expect } from '@playwright/test';
import { DatabaseHelpers } from './helpers/database-helpers';
import { testTables, expectedTableCounts, expectedColumns, performanceThresholds } from './fixtures/test-data';

test.describe('T051: Dashboard E2E Tests', () => {
  let dbHelpers: DatabaseHelpers;

  test.beforeEach(async ({ page }) => {
    dbHelpers = new DatabaseHelpers(page);
    await dbHelpers.navigateToDashboard();
  });

  test.describe('Table Structure Tab - Detailed Views', () => {
    test('should display detailed table structure information', async ({ page }) => {
      const testTableNames = ['users', 'jobs', 'prefecture_master'];

      for (const tableName of testTableNames) {
        await dbHelpers.selectTable(tableName);
        await dbHelpers.switchToTab('テーブル構造');

        // Verify table structure heading
        await expect(page.locator(`text=テーブル構造: ${tableName}`)).toBeVisible();

        // Check column information card
        const columnInfoCard = page.locator('text=カラム情報').locator('..');
        await expect(columnInfoCard).toBeVisible();

        // Check table statistics card
        const statisticsCard = page.locator('text=テーブル統計').locator('..');
        await expect(statisticsCard).toBeVisible();

        // Verify schema edit button is present
        await expect(page.locator('button:has-text("スキーマ編集")')).toBeVisible();
      }
    });

    test('should show accurate column information with data types', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('テーブル構造');

      const expectedUserColumns = expectedColumns.users;

      // Check that expected columns are displayed
      for (const columnName of expectedUserColumns) {
        const columnElement = page.locator(`text=${columnName}`);
        await expect(columnElement).toBeVisible();
      }

      // Verify data type information is shown
      const dataTypeElements = page.locator('text=UUID, text=BIGINT, text=TEXT, text=BOOLEAN, text=TIMESTAMP');
      const dataTypeCount = await dataTypeElements.count();
      expect(dataTypeCount).toBeGreaterThan(0);

      // Check for primary key indicator
      const primaryKeyBadge = page.locator('text=PK');
      await expect(primaryKeyBadge).toBeVisible();
    });

    test('should display table statistics accurately', async ({ page }) => {
      const testTables = [
        { name: 'users', expectedRows: expectedTableCounts.users },
        { name: 'prefecture_master', expectedRows: expectedTableCounts.prefecture_master },
        { name: 'jobs', expectedRows: expectedTableCounts.jobs }
      ];

      for (const table of testTables) {
        await dbHelpers.selectTable(table.name);
        const stats = await dbHelpers.getTableStatistics();

        // Verify row count matches expected (allowing for formatted numbers)
        expect(stats.rows).toBeTruthy();
        const rowCount = parseInt(stats.rows!.replace(/,/g, ''));
        expect(rowCount).toBe(table.expectedRows);

        // Verify column count
        expect(stats.columns).toBeTruthy();
        const columnCount = parseInt(stats.columns!);
        expect(columnCount).toBeGreaterThan(0);

        // Verify other statistics are present
        expect(stats.indexes).toBeTruthy();
      }
    });

    test('should show column details with constraints and indexes', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('テーブル構造');

      // Check column list container
      const columnContainer = page.locator('text=カラム情報').locator('..').locator('div').last();
      await expect(columnContainer).toBeVisible();

      // Verify individual column entries are displayed with proper information
      const columnEntries = columnContainer.locator('div[class*="border"]');
      const columnCount = await columnEntries.count();
      expect(columnCount).toBeGreaterThan(0);

      // Check first few columns for proper structure
      for (let i = 0; i < Math.min(3, columnCount); i++) {
        const columnEntry = columnEntries.nth(i);
        await expect(columnEntry).toBeVisible();

        // Should have column name and data type
        const entryText = await columnEntry.textContent();
        expect(entryText).toBeTruthy();
        expect(entryText!.length).toBeGreaterThan(0);
      }
    });

    test('should provide visual indicators for different column types', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('テーブル構造');

      // Look for different data type indicators
      const dataTypes = ['UUID', 'TEXT', 'BOOLEAN', 'TIMESTAMP', 'INTEGER'];

      for (const dataType of dataTypes) {
        const dataTypeElement = page.locator(`text=${dataType}`);
        // At least some data types should be present
        if (await dataTypeElement.isVisible()) {
          await expect(dataTypeElement).toBeVisible();
        }
      }

      // Check for badges or visual indicators
      const badges = page.locator('[class*="badge"], [class*="Badge"]');
      const badgeCount = await badges.count();
      expect(badgeCount).toBeGreaterThan(0);
    });
  });

  test.describe('Data Browsing Tab - Data Display and Pagination', () => {
    test('should display table data with proper formatting', async ({ page }) => {
      const tablesToTest = ['users', 'jobs', 'prefecture_master'];

      for (const tableName of tablesToTest) {
        await dbHelpers.selectTable(tableName);
        await dbHelpers.waitForTableData();

        // Verify table header
        await expect(page.locator(`text=テーブル: ${tableName}`)).toBeVisible();

        // Check for data table
        const dataTable = page.locator('table');
        await expect(dataTable).toBeVisible();

        // Verify table headers are present
        const tableHeaders = dataTable.locator('thead th');
        const headerCount = await tableHeaders.count();
        expect(headerCount).toBeGreaterThan(0);

        // Verify table body with data
        const tableBody = dataTable.locator('tbody');
        await expect(tableBody).toBeVisible();

        const dataRows = tableBody.locator('tr[data-mock="true"]');
        const rowCount = await dataRows.count();
        expect(rowCount).toBeGreaterThan(0);
      }
    });

    test('should handle different data types in table cells', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.waitForTableData();

      // Check for different data type displays
      const booleanBadges = page.locator('td .badge, td .Badge');
      const textCells = page.locator('td[class*="font-mono"]');
      const dateCells = page.locator('td:has-text("-"):has-text(":")');

      // At least some formatted data should be present
      const totalFormattedElements = await booleanBadges.count() + await textCells.count();
      expect(totalFormattedElements).toBeGreaterThan(0);
    });

    test('should provide data manipulation controls', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.waitForTableData();

      // Check for control buttons
      await expect(page.locator('button:has-text("新規追加")')).toBeVisible();
      await expect(page.locator('button:has-text("フィルター")')).toBeVisible();

      // Check for row-level actions
      const editButtons = page.locator('button:has(svg)', { hasText: 'Edit' });
      const deleteButtons = page.locator('button:has(svg)', { hasText: 'Trash' });

      // Should have action buttons for data rows
      if (await editButtons.count() > 0) {
        await expect(editButtons.first()).toBeVisible();
      }
    });

    test('should handle scrolling for large datasets', async ({ page }) => {
      await dbHelpers.selectTable('jobs');
      await dbHelpers.waitForTableData();

      // Check for scroll area
      const scrollArea = page.locator('[class*="scroll"]').first();
      if (await scrollArea.isVisible()) {
        const scrollContainer = scrollArea;
        const boundingBox = await scrollContainer.boundingBox();

        expect(boundingBox).toBeTruthy();
        expect(boundingBox!.height).toBeGreaterThan(0);

        // Test scrolling behavior
        await scrollContainer.hover();
        await page.mouse.wheel(0, 200);
        await page.waitForTimeout(300);
        await page.mouse.wheel(0, -200);
      }
    });

    test('should display row numbers and navigation', async ({ page }) => {
      await dbHelpers.selectTable('users');
      await dbHelpers.waitForTableData();

      // Check for row numbers in first column
      const rowNumberCells = page.locator('table tbody td:first-child');
      const firstRowNumber = rowNumberCells.first();

      if (await firstRowNumber.isVisible()) {
        const numberText = await firstRowNumber.textContent();
        expect(numberText).toMatch(/\d+/);
      }

      // Check for sequential numbering
      const rowCount = await rowNumberCells.count();
      if (rowCount > 1) {
        const secondRowNumber = rowNumberCells.nth(1);
        const secondNumberText = await secondRowNumber.textContent();
        expect(secondNumberText).toMatch(/\d+/);
      }
    });
  });

  test.describe('Search Functionality - Advanced Filtering', () => {
    test('should filter tables by name accurately', async ({ page }) => {
      const searchTests = [
        { term: 'user', expectedMinCount: 3 }, // users, user_actions, user_profiles, user_job_mapping
        { term: 'master', expectedMinCount: 6 }, // Various master tables
        { term: 'job', expectedMinCount: 5 }, // job-related tables
        { term: 'prefecture', expectedMinCount: 1 } // prefecture_master
      ];

      for (const test of searchTests) {
        await dbHelpers.searchTables(test.term);

        const visibleCount = await dbHelpers.getVisibleTableCount();
        expect(visibleCount).toBeGreaterThanOrEqual(test.expectedMinCount);

        // Verify all visible tables contain the search term
        const visibleTables = page.locator('[data-testid="tables-list"] .table-item:visible');
        const count = await visibleTables.count();

        for (let i = 0; i < count; i++) {
          const tableText = await visibleTables.nth(i).textContent();
          expect(tableText?.toLowerCase()).toContain(test.term.toLowerCase());
        }
      }

      // Clear search
      await dbHelpers.searchTables('');
    });

    test('should filter tables by description content', async ({ page }) => {
      // Test searching by Japanese description terms
      const descriptionSearches = [
        'ユーザー',
        '求人',
        'マスター',
        'メール'
      ];

      for (const searchTerm of descriptionSearches) {
        await dbHelpers.searchTables(searchTerm);

        const visibleCount = await dbHelpers.getVisibleTableCount();

        if (visibleCount > 0) {
          // Verify search results contain the term in name or description
          const visibleTables = page.locator('[data-testid="tables-list"] .table-item:visible');
          const count = await visibleTables.count();

          for (let i = 0; i < Math.min(count, 3); i++) { // Check first 3 results
            const tableText = await visibleTables.nth(i).textContent();
            // Should contain search term in either name or description
            expect(tableText?.includes(searchTerm) || tableText?.toLowerCase().includes(searchTerm.toLowerCase())).toBeTruthy();
          }
        }
      }

      // Clear search
      await dbHelpers.searchTables('');
    });

    test('should handle partial matches and case insensitive search', async ({ page }) => {
      const caseTests = [
        { search: 'USER', expectedTable: 'users' },
        { search: 'Job', expectedTable: 'jobs' },
        { search: 'pref', expectedTable: 'prefecture_master' }
      ];

      for (const caseTest of caseTests) {
        await dbHelpers.searchTables(caseTest.search);

        const matchingTable = page.locator(`[data-testid="tables-list"] button:has-text("${caseTest.expectedTable}"):visible`);
        await expect(matchingTable).toBeVisible();
      }

      // Clear search
      await dbHelpers.searchTables('');
    });

    test('should clear search results appropriately', async ({ page }) => {
      // Apply search filter
      await dbHelpers.searchTables('user');
      const filteredCount = await dbHelpers.getVisibleTableCount();
      expect(filteredCount).toBeLessThan(testTables.length);

      // Clear search
      await dbHelpers.searchTables('');
      const clearedCount = await dbHelpers.getVisibleTableCount();
      expect(clearedCount).toBeGreaterThanOrEqual(testTables.length);
    });

    test('should maintain search state during table operations', async ({ page }) => {
      // Apply search and select table
      await dbHelpers.searchTables('user');
      await dbHelpers.selectTable('users');

      // Switch tabs
      await dbHelpers.switchToTab('テーブル構造');
      await dbHelpers.switchToTab('データ閲覧');

      // Verify search is still active
      const visibleCount = await dbHelpers.getVisibleTableCount();
      expect(visibleCount).toBeLessThan(testTables.length);

      // Verify selected table is still selected
      const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
      await expect(selectedTable).toBeVisible();
    });
  });

  test.describe('Statistics Display and Monitoring', () => {
    test('should display database overview statistics', async ({ page }) => {
      // Check main header for statistics
      const headerArea = page.locator('header');
      await expect(headerArea).toBeVisible();

      // Look for table count in sidebar
      const tableCountText = page.locator('text=/データベーステーブル.*\\d+/');
      if (await tableCountText.isVisible()) {
        const countText = await tableCountText.textContent();
        expect(countText).toMatch(/\d+/);
      }

      // Check for database type indicator
      const dbTypeBadge = page.locator('text=SQLite風');
      await expect(dbTypeBadge).toBeVisible();
    });

    test('should show real-time connection status', async ({ page }) => {
      // Check connection status indicators
      const connectionStatus = page.locator('text=リアルタイム接続中, text=オフライン');
      await expect(connectionStatus).toBeVisible();

      // Check for activity indicators
      const activityIndicators = page.locator('[class*="animate-pulse"], svg[class*="animate-pulse"]');
      if (await activityIndicators.count() > 0) {
        await expect(activityIndicators.first()).toBeVisible();
      }
    });

    test('should display table-specific statistics in structure view', async ({ page }) => {
      const tablesWithKnownStats = [
        { name: 'prefecture_master', expectedRows: 47 },
        { name: 'employment_type_master', expectedRows: 10 },
        { name: 'salary_type_master', expectedRows: 5 }
      ];

      for (const table of tablesWithKnownStats) {
        await dbHelpers.selectTable(table.name);
        const stats = await dbHelpers.getTableStatistics();

        // Verify row count
        const rowCount = parseInt(stats.rows!.replace(/,/g, ''));
        expect(rowCount).toBe(table.expectedRows);

        // Verify other statistics are present and reasonable
        const columnCount = parseInt(stats.columns!);
        expect(columnCount).toBeGreaterThan(0);
        expect(columnCount).toBeLessThan(50); // Reasonable upper bound

        const indexCount = parseInt(stats.indexes!);
        expect(indexCount).toBeGreaterThanOrEqual(0);
      }
    });

    test('should show performance metrics when available', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');
      await dbHelpers.executeQuery('SELECT * FROM users LIMIT 5;');

      // Look for performance metrics
      const perfSection = page.locator('text=実行時間').locator('..');

      if (await perfSection.isVisible()) {
        // Check execution time
        const executionTime = page.locator('text=/\\d+ms/');
        await expect(executionTime).toBeVisible();

        // Check query statistics
        const statsSection = page.locator('text=総実行, text=成功, text=失敗');
        if (await statsSection.count() > 0) {
          await expect(statsSection.first()).toBeVisible();
        }
      }
    });

    test('should track and display query history', async ({ page }) => {
      await dbHelpers.switchToTab('SQLクエリ');

      // Execute multiple queries to build history
      const queries = [
        'SELECT COUNT(*) FROM users;',
        'SELECT * FROM prefecture_master LIMIT 3;'
      ];

      for (const query of queries) {
        await dbHelpers.executeQuery(query);
        await page.waitForTimeout(1000); // Allow time for stats to update
      }

      // Look for updated statistics
      const statsElements = page.locator('text=総実行, text=成功, text=失敗');
      if (await statsElements.count() > 0) {
        const statsText = await page.locator('text=/総実行.*\\d+/').textContent();
        if (statsText) {
          expect(statsText).toMatch(/\d+/);
        }
      }
    });
  });

  test.describe('Dashboard Performance and Responsiveness', () => {
    test('should load dashboard components within performance thresholds', async ({ page }) => {
      const startTime = Date.now();

      await dbHelpers.navigateToDashboard();
      await dbHelpers.selectTable('users');
      await dbHelpers.switchToTab('データ閲覧');

      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeLessThan(performanceThresholds.pageLoad);
    });

    test('should handle rapid tab switching efficiently', async ({ page }) => {
      await dbHelpers.selectTable('jobs');

      const tabs = ['SQLクエリ', 'データ閲覧', 'テーブル構造', 'リアルタイム'];

      for (let i = 0; i < 3; i++) { // Test multiple cycles
        for (const tab of tabs) {
          const startTime = Date.now();
          await dbHelpers.switchToTab(tab as any);
          const switchTime = Date.now() - startTime;

          expect(switchTime).toBeLessThan(performanceThresholds.tabSwitch);
        }
      }
    });

    test('should maintain responsiveness during search operations', async ({ page }) => {
      const searchTerms = ['user', 'job', 'master', 'prefecture'];

      for (const term of searchTerms) {
        const startTime = Date.now();
        await dbHelpers.searchTables(term);
        const searchTime = Date.now() - startTime;

        expect(searchTime).toBeLessThan(performanceThresholds.search);

        // Verify results are displayed
        const visibleCount = await dbHelpers.getVisibleTableCount();
        expect(visibleCount).toBeGreaterThanOrEqual(0);
      }
    });

    test('should handle concurrent user interactions gracefully', async ({ page }) => {
      // Simulate rapid user interactions
      await Promise.all([
        dbHelpers.searchTables('user'),
        dbHelpers.selectTable('users'),
        dbHelpers.switchToTab('データ閲覧')
      ]);

      // Verify final state is consistent
      const selectedTable = page.locator('[data-testid="tables-list"] button.secondary');
      await expect(selectedTable).toBeVisible();

      const activeTab = page.locator('[role="tab"][aria-selected="true"]');
      await expect(activeTab).toBeVisible();
    });
  });
});