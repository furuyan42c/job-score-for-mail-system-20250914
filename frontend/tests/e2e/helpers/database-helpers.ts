import { Page, expect } from '@playwright/test';

/**
 * Database-related helper functions for E2E tests
 */
export class DatabaseHelpers {
  constructor(private page: Page) {}

  /**
   * Navigate to the database admin dashboard
   */
  async navigateToDashboard() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
    await expect(this.page).toHaveTitle(/database/i);
  }

  /**
   * Select a table from the sidebar
   */
  async selectTable(tableName: string) {
    const tableButton = this.page.locator(`[data-testid="tables-list"] button:has-text("${tableName}")`);
    await expect(tableButton).toBeVisible();
    await tableButton.click();

    // Wait for table to be selected
    await expect(tableButton).toHaveAttribute('class', /secondary/);
  }

  /**
   * Switch to a specific tab
   */
  async switchToTab(tabName: 'SQLクエリ' | 'データ閲覧' | 'テーブル構造' | 'リアルタイム') {
    const tabTrigger = this.page.locator(`[role="tab"]:has-text("${tabName}")`);
    await expect(tabTrigger).toBeVisible();
    await tabTrigger.click();

    // Wait for tab content to be visible
    await this.page.waitForTimeout(500);
  }

  /**
   * Execute SQL query in the query editor
   */
  async executeQuery(query: string) {
    await this.switchToTab('SQLクエリ');

    const queryEditor = this.page.locator('textarea[placeholder*="SQL"]');
    await expect(queryEditor).toBeVisible();

    // Clear and enter new query
    await queryEditor.clear();
    await queryEditor.fill(query);

    // Execute query
    const executeButton = this.page.locator('button:has-text("クエリ実行")');
    await expect(executeButton).toBeVisible();
    await executeButton.click();

    // Wait for execution to complete
    await expect(executeButton).not.toHaveText(/実行中/);
  }

  /**
   * Get query results
   */
  async getQueryResults() {
    const resultArea = this.page.locator('[data-testid="query-result"]');
    await expect(resultArea).toBeVisible();
    return resultArea;
  }

  /**
   * Check if error message is displayed
   */
  async hasErrorMessage() {
    const errorMessage = this.page.locator('[data-testid="error-message"]');
    return await errorMessage.isVisible();
  }

  /**
   * Get error message text
   */
  async getErrorMessage() {
    const errorMessage = this.page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
    return await errorMessage.textContent();
  }

  /**
   * Wait for table data to load in browse tab
   */
  async waitForTableData() {
    await this.switchToTab('データ閲覧');
    const tableBody = this.page.locator('table tbody');
    await expect(tableBody).toBeVisible();

    // Wait for at least one row to be visible
    const firstRow = tableBody.locator('tr').first();
    await expect(firstRow).toBeVisible();
  }

  /**
   * Get table statistics from structure tab
   */
  async getTableStatistics() {
    await this.switchToTab('テーブル構造');

    const statsCard = this.page.locator('div:has-text("テーブル統計")').locator('..').locator('div[class*="CardContent"]');
    await expect(statsCard).toBeVisible();

    return {
      rows: await statsCard.locator('div:has-text("総行数")').locator('span[class*="font-mono"]').textContent(),
      columns: await statsCard.locator('div:has-text("カラム数")').locator('span[class*="font-mono"]').textContent(),
      indexes: await statsCard.locator('div:has-text("インデックス")').locator('span[class*="font-mono"]').textContent(),
    };
  }

  /**
   * Search for tables in the sidebar
   */
  async searchTables(searchTerm: string) {
    const searchInput = this.page.locator('input[placeholder*="テーブル検索"]');
    await expect(searchInput).toBeVisible();
    await searchInput.clear();
    await searchInput.fill(searchTerm);

    // Wait for search results
    await this.page.waitForTimeout(500);
  }

  /**
   * Get visible table count in sidebar
   */
  async getVisibleTableCount() {
    const tableItems = this.page.locator('[data-testid="tables-list"] .table-item');
    return await tableItems.count();
  }

  /**
   * Check if realtime notifications are working
   */
  async checkRealtimeStatus() {
    await this.switchToTab('リアルタイム');

    const statusBadge = this.page.locator('text=接続中, text=切断');
    await expect(statusBadge).toBeVisible();

    return await statusBadge.textContent();
  }

  /**
   * Toggle realtime functionality
   */
  async toggleRealtime() {
    const realtimeButton = this.page.locator('button:has-text("リアルタイム")');
    await expect(realtimeButton).toBeVisible();
    await realtimeButton.click();
  }
}