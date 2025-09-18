import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * SQL Execution Page Object Model
 */
export class SqlExecutionPage extends BasePage {
  // Query editor elements
  readonly queryEditor: Locator;
  readonly queryInput: Locator;
  readonly executeButton: Locator;
  readonly clearButton: Locator;
  readonly formatButton: Locator;

  // Query history elements
  readonly queryHistory: Locator;
  readonly historyItems: Locator;
  readonly clearHistoryButton: Locator;
  readonly loadHistoryButton: Locator;

  // Sample queries
  readonly sampleQueries: Locator;
  readonly loadSampleButton: Locator;

  // Results elements
  readonly resultsContainer: Locator;
  readonly resultsTable: Locator;
  readonly resultsRows: Locator;
  readonly resultsHeaders: Locator;
  readonly noResultsMessage: Locator;
  readonly executionTime: Locator;
  readonly rowCount: Locator;

  // Export functionality
  readonly exportButton: Locator;
  readonly exportDropdown: Locator;
  readonly exportCsvButton: Locator;
  readonly exportJsonButton: Locator;
  readonly exportExcelButton: Locator;

  // Pagination
  readonly paginationContainer: Locator;
  readonly pageSize: Locator;
  readonly nextPageButton: Locator;
  readonly prevPageButton: Locator;
  readonly pageInfo: Locator;

  // Error handling
  readonly errorMessage: Locator;
  readonly errorDetails: Locator;
  readonly dismissErrorButton: Locator;

  // Performance metrics
  readonly performanceMetrics: Locator;
  readonly queryDuration: Locator;
  readonly memoryUsage: Locator;
  readonly connectionStatus: Locator;

  // Loading states
  readonly queryExecutionSpinner: Locator;
  readonly resultsLoadingSpinner: Locator;

  constructor(page: Page) {
    super(page);

    // Query editor elements
    this.queryEditor = this.getByTestId('query-editor');
    this.queryInput = this.getByTestId('query-input');
    this.executeButton = this.getByTestId('execute-button');
    this.clearButton = this.getByTestId('clear-button');
    this.formatButton = this.getByTestId('format-button');

    // Query history elements
    this.queryHistory = this.getByTestId('query-history');
    this.historyItems = this.getByTestId('history-item');
    this.clearHistoryButton = this.getByTestId('clear-history');
    this.loadHistoryButton = this.getByTestId('load-history');

    // Sample queries
    this.sampleQueries = this.getByTestId('sample-queries');
    this.loadSampleButton = this.getByTestId('load-sample');

    // Results elements
    this.resultsContainer = this.getByTestId('results-container');
    this.resultsTable = this.getByTestId('results-table');
    this.resultsRows = this.resultsTable.locator('tbody tr');
    this.resultsHeaders = this.resultsTable.locator('thead th');
    this.noResultsMessage = this.getByTestId('no-results-message');
    this.executionTime = this.getByTestId('execution-time');
    this.rowCount = this.getByTestId('row-count');

    // Export functionality
    this.exportButton = this.getByTestId('export-button');
    this.exportDropdown = this.getByTestId('export-dropdown');
    this.exportCsvButton = this.getByTestId('export-csv');
    this.exportJsonButton = this.getByTestId('export-json');
    this.exportExcelButton = this.getByTestId('export-excel');

    // Pagination
    this.paginationContainer = this.getByTestId('pagination-container');
    this.pageSize = this.getByTestId('page-size-select');
    this.nextPageButton = this.getByTestId('next-page');
    this.prevPageButton = this.getByTestId('prev-page');
    this.pageInfo = this.getByTestId('page-info');

    // Error handling
    this.errorMessage = this.getByTestId('error-message');
    this.errorDetails = this.getByTestId('error-details');
    this.dismissErrorButton = this.getByTestId('dismiss-error');

    // Performance metrics
    this.performanceMetrics = this.getByTestId('performance-metrics');
    this.queryDuration = this.getByTestId('query-duration');
    this.memoryUsage = this.getByTestId('memory-usage');
    this.connectionStatus = this.getByTestId('connection-status');

    // Loading states
    this.queryExecutionSpinner = this.getByTestId('query-execution-spinner');
    this.resultsLoadingSpinner = this.getByTestId('results-loading-spinner');
  }

  /**
   * Navigate to SQL execution page
   */
  async goto(): Promise<void> {
    await super.goto('/sql-execution');
    await this.waitForPageLoad();
  }

  /**
   * Enter SQL query in the editor
   */
  async enterQuery(query: string): Promise<void> {
    await this.fillInput(this.queryInput, query);
  }

  /**
   * Execute the current query
   */
  async executeQuery(): Promise<void> {
    await this.clickElement(this.executeButton);
    await this.waitForQueryExecution();
  }

  /**
   * Execute query using keyboard shortcut (Ctrl+Enter)
   */
  async executeQueryWithKeyboard(): Promise<void> {
    await this.queryInput.focus();
    await this.pressKeyboard('Control+Enter');
    await this.waitForQueryExecution();
  }

  /**
   * Clear the query editor
   */
  async clearQuery(): Promise<void> {
    await this.clickElement(this.clearButton);
  }

  /**
   * Format the query
   */
  async formatQuery(): Promise<void> {
    await this.clickElement(this.formatButton);
  }

  /**
   * Load a sample query
   */
  async loadSampleQuery(queryName: string): Promise<void> {
    await this.clickElement(this.sampleQueries);
    const sampleQuery = this.sampleQueries.locator(`[data-query-name="${queryName}"]`);
    await this.clickElement(sampleQuery);
  }

  /**
   * Load query from history
   */
  async loadQueryFromHistory(index: number): Promise<void> {
    const historyItem = this.historyItems.nth(index);
    await this.clickElement(historyItem);
  }

  /**
   * Clear query history
   */
  async clearQueryHistory(): Promise<void> {
    await this.clickElement(this.clearHistoryButton);
  }

  /**
   * Get query results data
   */
  async getQueryResults(): Promise<Record<string, string>[]> {
    await this.waitForVisible(this.resultsTable);

    const headerCount = await this.resultsHeaders.count();
    const headers: string[] = [];

    // Get column headers
    for (let i = 0; i < headerCount; i++) {
      const headerText = await this.resultsHeaders.nth(i).textContent();
      headers.push(headerText || '');
    }

    // Get row data
    const rowCount = await this.resultsRows.count();
    const results: Record<string, string>[] = [];

    for (let i = 0; i < rowCount; i++) {
      const row = this.resultsRows.nth(i);
      const cells = row.locator('td');
      const cellCount = await cells.count();

      const rowData: Record<string, string> = {};
      for (let j = 0; j < cellCount && j < headers.length; j++) {
        const cellText = await cells.nth(j).textContent();
        rowData[headers[j]] = cellText || '';
      }
      results.push(rowData);
    }

    return results;
  }

  /**
   * Get result row count
   */
  async getResultRowCount(): Promise<number> {
    await this.waitForVisible(this.resultsTable);
    return await this.resultsRows.count();
  }

  /**
   * Get execution time
   */
  async getExecutionTime(): Promise<string> {
    await this.waitForVisible(this.executionTime);
    return await this.executionTime.textContent() || '';
  }

  /**
   * Get total row count
   */
  async getTotalRowCount(): Promise<string> {
    await this.waitForVisible(this.rowCount);
    return await this.rowCount.textContent() || '';
  }

  /**
   * Export results as CSV
   */
  async exportAsCsv(): Promise<void> {
    await this.clickElement(this.exportButton);
    await this.clickElement(this.exportCsvButton);

    // Wait for download to start
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;

    // Verify download
    return download.path();
  }

  /**
   * Export results as JSON
   */
  async exportAsJson(): Promise<void> {
    await this.clickElement(this.exportButton);
    await this.clickElement(this.exportJsonButton);

    // Wait for download
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;

    return download.path();
  }

  /**
   * Change page size
   */
  async changePageSize(size: string): Promise<void> {
    await this.clickElement(this.pageSize);
    const sizeOption = this.pageSize.locator(`option[value="${size}"]`);
    await this.clickElement(sizeOption);
    await this.waitForLoadingToComplete();
  }

  /**
   * Go to next page of results
   */
  async goToNextPage(): Promise<void> {
    await this.clickElement(this.nextPageButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Go to previous page of results
   */
  async goToPreviousPage(): Promise<void> {
    await this.clickElement(this.prevPageButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Get current page information
   */
  async getPageInfo(): Promise<string> {
    await this.waitForVisible(this.pageInfo);
    return await this.pageInfo.textContent() || '';
  }

  /**
   * Get error message
   */
  async getErrorMessage(): Promise<string> {
    await this.waitForVisible(this.errorMessage);
    return await this.errorMessage.textContent() || '';
  }

  /**
   * Get error details
   */
  async getErrorDetails(): Promise<string> {
    await this.waitForVisible(this.errorDetails);
    return await this.errorDetails.textContent() || '';
  }

  /**
   * Dismiss error message
   */
  async dismissError(): Promise<void> {
    await this.clickElement(this.dismissErrorButton);
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(): Promise<{
    duration: string;
    memoryUsage: string;
    connectionStatus: string;
  }> {
    await this.waitForVisible(this.performanceMetrics);

    const duration = await this.queryDuration.textContent() || '';
    const memoryUsage = await this.memoryUsage.textContent() || '';
    const connectionStatus = await this.connectionStatus.textContent() || '';

    return { duration, memoryUsage, connectionStatus };
  }

  /**
   * Verify SQL execution page is loaded
   */
  async verifySqlExecutionPageLoaded(): Promise<void> {
    await this.waitForVisible(this.queryEditor);
    await this.waitForVisible(this.queryInput);
    await this.waitForVisible(this.executeButton);
  }

  /**
   * Verify query results are displayed
   */
  async verifyQueryResultsDisplayed(): Promise<void> {
    await this.waitForVisible(this.resultsContainer);
    await this.waitForVisible(this.resultsTable);
  }

  /**
   * Verify error is displayed
   */
  async verifyErrorDisplayed(): Promise<void> {
    await this.waitForVisible(this.errorMessage);
  }

  /**
   * Wait for query execution to complete
   */
  async waitForQueryExecution(): Promise<void> {
    // Wait for spinner to appear (query started)
    await this.page.waitForSelector('[data-testid="query-execution-spinner"]', {
      state: 'visible',
      timeout: 5000
    }).catch(() => {
      // If spinner doesn't appear, query might execute too fast
    });

    // Wait for spinner to disappear (query completed)
    await this.page.waitForSelector('[data-testid="query-execution-spinner"]', {
      state: 'hidden',
      timeout: 30000
    }).catch(() => {
      // Continue if spinner is not found
    });

    // Wait for either results or error to appear
    await this.page.waitForFunction(() => {
      const results = document.querySelector('[data-testid="results-table"]');
      const error = document.querySelector('[data-testid="error-message"]');
      const noResults = document.querySelector('[data-testid="no-results-message"]');
      return results || error || noResults;
    }, { timeout: 30000 });
  }

  /**
   * Check if query is currently executing
   */
  async isQueryExecuting(): Promise<boolean> {
    return await this.queryExecutionSpinner.isVisible();
  }

  /**
   * Get query history count
   */
  async getQueryHistoryCount(): Promise<number> {
    return await this.historyItems.count();
  }

  /**
   * Verify connection status
   */
  async verifyConnectionStatus(expectedStatus: string): Promise<void> {
    await this.waitForVisible(this.connectionStatus);
    await this.verifyText(this.connectionStatus, expectedStatus);
  }
}