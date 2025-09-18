import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Dashboard Page Object Model
 */
export class DashboardPage extends BasePage {
  // Main dashboard elements
  readonly dashboardContainer: Locator;
  readonly headerTitle: Locator;
  readonly userProfile: Locator;
  readonly logoutButton: Locator;

  // Batch monitoring elements
  readonly batchStatusContainer: Locator;
  readonly currentBatchStatus: Locator;
  readonly batchProgressBar: Locator;
  readonly batchPhaseIndicator: Locator;
  readonly batchStartTime: Locator;
  readonly batchEstimatedCompletion: Locator;
  readonly pauseBatchButton: Locator;
  readonly stopBatchButton: Locator;
  readonly restartBatchButton: Locator;

  // Error log elements
  readonly errorLogContainer: Locator;
  readonly errorLogTabs: Locator;
  readonly errorTab: Locator;
  readonly warningTab: Locator;
  readonly infoTab: Locator;
  readonly logEntries: Locator;
  readonly logSearchInput: Locator;
  readonly logFilterDropdown: Locator;
  readonly clearLogsButton: Locator;
  readonly exportLogsButton: Locator;
  readonly refreshLogsButton: Locator;

  // Performance metrics elements
  readonly performanceContainer: Locator;
  readonly cpuUsageChart: Locator;
  readonly memoryUsageChart: Locator;
  readonly databaseConnectionsChart: Locator;
  readonly processingSpeedIndicator: Locator;
  readonly systemHealthIndicator: Locator;
  readonly autoRefreshToggle: Locator;
  readonly refreshInterval: Locator;
  readonly metricsTimeRange: Locator;

  // Statistics cards
  readonly totalJobsProcessed: Locator;
  readonly activeUsers: Locator;
  readonly systemUptime: Locator;
  readonly errorRate: Locator;

  // Navigation tabs
  readonly overviewTab: Locator;
  readonly monitoringTab: Locator;
  readonly logsTab: Locator;
  readonly settingsTab: Locator;

  // Settings elements
  readonly settingsContainer: Locator;
  readonly notificationSettings: Locator;
  readonly systemSettings: Locator;
  readonly saveSettingsButton: Locator;

  // Export and report elements
  readonly generateReportButton: Locator;
  readonly reportTypeSelect: Locator;
  readonly dateRangePicker: Locator;
  readonly downloadReportButton: Locator;

  constructor(page: Page) {
    super(page);

    // Main dashboard elements
    this.dashboardContainer = this.getByTestId('dashboard-container');
    this.headerTitle = this.getByTestId('dashboard-title');
    this.userProfile = this.getByTestId('user-profile');
    this.logoutButton = this.getByTestId('logout-button');

    // Batch monitoring elements
    this.batchStatusContainer = this.getByTestId('batch-status-container');
    this.currentBatchStatus = this.getByTestId('current-batch-status');
    this.batchProgressBar = this.getByTestId('batch-progress-bar');
    this.batchPhaseIndicator = this.getByTestId('batch-phase-indicator');
    this.batchStartTime = this.getByTestId('batch-start-time');
    this.batchEstimatedCompletion = this.getByTestId('batch-estimated-completion');
    this.pauseBatchButton = this.getByTestId('pause-batch-button');
    this.stopBatchButton = this.getByTestId('stop-batch-button');
    this.restartBatchButton = this.getByTestId('restart-batch-button');

    // Error log elements
    this.errorLogContainer = this.getByTestId('error-log-container');
    this.errorLogTabs = this.getByTestId('error-log-tabs');
    this.errorTab = this.getByTestId('error-tab');
    this.warningTab = this.getByTestId('warning-tab');
    this.infoTab = this.getByTestId('info-tab');
    this.logEntries = this.getByTestId('log-entry');
    this.logSearchInput = this.getByTestId('log-search-input');
    this.logFilterDropdown = this.getByTestId('log-filter-dropdown');
    this.clearLogsButton = this.getByTestId('clear-logs-button');
    this.exportLogsButton = this.getByTestId('export-logs-button');
    this.refreshLogsButton = this.getByTestId('refresh-logs-button');

    // Performance metrics elements
    this.performanceContainer = this.getByTestId('performance-container');
    this.cpuUsageChart = this.getByTestId('cpu-usage-chart');
    this.memoryUsageChart = this.getByTestId('memory-usage-chart');
    this.databaseConnectionsChart = this.getByTestId('database-connections-chart');
    this.processingSpeedIndicator = this.getByTestId('processing-speed-indicator');
    this.systemHealthIndicator = this.getByTestId('system-health-indicator');
    this.autoRefreshToggle = this.getByTestId('auto-refresh-toggle');
    this.refreshInterval = this.getByTestId('refresh-interval');
    this.metricsTimeRange = this.getByTestId('metrics-time-range');

    // Statistics cards
    this.totalJobsProcessed = this.getByTestId('total-jobs-processed');
    this.activeUsers = this.getByTestId('active-users');
    this.systemUptime = this.getByTestId('system-uptime');
    this.errorRate = this.getByTestId('error-rate');

    // Navigation tabs
    this.overviewTab = this.getByTestId('overview-tab');
    this.monitoringTab = this.getByTestId('monitoring-tab');
    this.logsTab = this.getByTestId('logs-tab');
    this.settingsTab = this.getByTestId('settings-tab');

    // Settings elements
    this.settingsContainer = this.getByTestId('settings-container');
    this.notificationSettings = this.getByTestId('notification-settings');
    this.systemSettings = this.getByTestId('system-settings');
    this.saveSettingsButton = this.getByTestId('save-settings-button');

    // Export and report elements
    this.generateReportButton = this.getByTestId('generate-report-button');
    this.reportTypeSelect = this.getByTestId('report-type-select');
    this.dateRangePicker = this.getByTestId('date-range-picker');
    this.downloadReportButton = this.getByTestId('download-report-button');
  }

  /**
   * Navigate to dashboard
   */
  async goto(): Promise<void> {
    await super.goto('/dashboard');
    await this.waitForPageLoad();
  }

  /**
   * Switch to specific dashboard tab
   */
  async switchToTab(tab: 'overview' | 'monitoring' | 'logs' | 'settings'): Promise<void> {
    let tabElement: Locator;

    switch (tab) {
      case 'overview':
        tabElement = this.overviewTab;
        break;
      case 'monitoring':
        tabElement = this.monitoringTab;
        break;
      case 'logs':
        tabElement = this.logsTab;
        break;
      case 'settings':
        tabElement = this.settingsTab;
        break;
    }

    await this.clickElement(tabElement);
    await this.waitForLoadingToComplete();
  }

  /**
   * Get current batch status
   */
  async getBatchStatus(): Promise<string> {
    await this.waitForVisible(this.currentBatchStatus);
    return await this.currentBatchStatus.textContent() || '';
  }

  /**
   * Get batch progress percentage
   */
  async getBatchProgress(): Promise<number> {
    await this.waitForVisible(this.batchProgressBar);
    const progressText = await this.batchProgressBar.getAttribute('aria-valuenow');
    return parseInt(progressText || '0', 10);
  }

  /**
   * Get current batch phase
   */
  async getBatchPhase(): Promise<string> {
    await this.waitForVisible(this.batchPhaseIndicator);
    return await this.batchPhaseIndicator.textContent() || '';
  }

  /**
   * Pause current batch
   */
  async pauseBatch(): Promise<void> {
    await this.clickElement(this.pauseBatchButton);
  }

  /**
   * Stop current batch
   */
  async stopBatch(): Promise<void> {
    await this.clickElement(this.stopBatchButton);

    // Confirm in dialog if appears
    this.page.on('dialog', async dialog => {
      await dialog.accept();
    });
  }

  /**
   * Restart batch
   */
  async restartBatch(): Promise<void> {
    await this.clickElement(this.restartBatchButton);

    // Confirm in dialog if appears
    this.page.on('dialog', async dialog => {
      await dialog.accept();
    });
  }

  /**
   * Filter logs by severity
   */
  async filterLogsBySeverity(severity: 'error' | 'warning' | 'info'): Promise<void> {
    let tabElement: Locator;

    switch (severity) {
      case 'error':
        tabElement = this.errorTab;
        break;
      case 'warning':
        tabElement = this.warningTab;
        break;
      case 'info':
        tabElement = this.infoTab;
        break;
    }

    await this.clickElement(tabElement);
    await this.waitForLoadingToComplete();
  }

  /**
   * Search logs
   */
  async searchLogs(searchTerm: string): Promise<void> {
    await this.fillInput(this.logSearchInput, searchTerm);
    await this.pressKeyboard('Enter');
    await this.waitForLoadingToComplete();
  }

  /**
   * Get log entries
   */
  async getLogEntries(): Promise<Array<{
    timestamp: string;
    level: string;
    message: string;
    details?: string;
  }>> {
    await this.waitForVisible(this.errorLogContainer);
    const logCount = await this.logEntries.count();
    const logs: Array<{
      timestamp: string;
      level: string;
      message: string;
      details?: string;
    }> = [];

    for (let i = 0; i < logCount; i++) {
      const logEntry = this.logEntries.nth(i);

      const timestamp = await logEntry.locator('[data-testid="log-timestamp"]').textContent() || '';
      const level = await logEntry.locator('[data-testid="log-level"]').textContent() || '';
      const message = await logEntry.locator('[data-testid="log-message"]').textContent() || '';
      const detailsElement = logEntry.locator('[data-testid="log-details"]');
      const details = await detailsElement.isVisible() ? await detailsElement.textContent() || undefined : undefined;

      logs.push({ timestamp, level, message, details });
    }

    return logs;
  }

  /**
   * Clear logs
   */
  async clearLogs(): Promise<void> {
    await this.clickElement(this.clearLogsButton);

    // Confirm in dialog
    this.page.on('dialog', async dialog => {
      await dialog.accept();
    });
  }

  /**
   * Export logs
   */
  async exportLogs(): Promise<void> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.clickElement(this.exportLogsButton);

    const download = await downloadPromise;
    return download.path();
  }

  /**
   * Refresh logs
   */
  async refreshLogs(): Promise<void> {
    await this.clickElement(this.refreshLogsButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(): Promise<{
    cpuUsage?: string;
    memoryUsage?: string;
    databaseConnections?: string;
    processingSpeed?: string;
    systemHealth?: string;
  }> {
    await this.waitForVisible(this.performanceContainer);

    const cpuUsage = await this.cpuUsageChart.getAttribute('data-current-value');
    const memoryUsage = await this.memoryUsageChart.getAttribute('data-current-value');
    const dbConnections = await this.databaseConnectionsChart.getAttribute('data-current-value');
    const processingSpeed = await this.processingSpeedIndicator.textContent();
    const systemHealth = await this.systemHealthIndicator.textContent();

    return {
      cpuUsage,
      memoryUsage,
      databaseConnections: dbConnections,
      processingSpeed: processingSpeed || undefined,
      systemHealth: systemHealth || undefined
    };
  }

  /**
   * Get statistics cards data
   */
  async getStatistics(): Promise<{
    totalJobs: string;
    activeUsers: string;
    systemUptime: string;
    errorRate: string;
  }> {
    const totalJobs = await this.totalJobsProcessed.textContent() || '';
    const activeUsers = await this.activeUsers.textContent() || '';
    const systemUptime = await this.systemUptime.textContent() || '';
    const errorRate = await this.errorRate.textContent() || '';

    return { totalJobs, activeUsers, systemUptime, errorRate };
  }

  /**
   * Toggle auto refresh
   */
  async toggleAutoRefresh(): Promise<void> {
    await this.clickElement(this.autoRefreshToggle);
  }

  /**
   * Set refresh interval
   */
  async setRefreshInterval(interval: string): Promise<void> {
    await this.clickElement(this.refreshInterval);
    const intervalOption = this.refreshInterval.locator(`option[value="${interval}"]`);
    await this.clickElement(intervalOption);
  }

  /**
   * Set metrics time range
   */
  async setMetricsTimeRange(range: string): Promise<void> {
    await this.clickElement(this.metricsTimeRange);
    const rangeOption = this.metricsTimeRange.locator(`option[value="${range}"]`);
    await this.clickElement(rangeOption);
    await this.waitForLoadingToComplete();
  }

  /**
   * Generate report
   */
  async generateReport(reportType: string, startDate: string, endDate: string): Promise<void> {
    await this.clickElement(this.reportTypeSelect);
    const typeOption = this.reportTypeSelect.locator(`option[value="${reportType}"]`);
    await this.clickElement(typeOption);

    // Set date range
    await this.clickElement(this.dateRangePicker);
    const startDateInput = this.dateRangePicker.locator('[data-testid="start-date"]');
    const endDateInput = this.dateRangePicker.locator('[data-testid="end-date"]');

    await this.fillInput(startDateInput, startDate);
    await this.fillInput(endDateInput, endDate);

    await this.clickElement(this.generateReportButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Download generated report
   */
  async downloadReport(): Promise<void> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.clickElement(this.downloadReportButton);

    const download = await downloadPromise;
    return download.path();
  }

  /**
   * Save dashboard settings
   */
  async saveSettings(): Promise<void> {
    await this.clickElement(this.saveSettingsButton);
    await this.waitForLoadingToComplete();
  }

  /**
   * Logout from dashboard
   */
  async logout(): Promise<void> {
    await this.clickElement(this.logoutButton);
    await this.waitForUrlChange('/');
  }

  /**
   * Verify dashboard is loaded
   */
  async verifyDashboardLoaded(): Promise<void> {
    await this.waitForVisible(this.dashboardContainer);
    await this.waitForVisible(this.headerTitle);
    await this.waitForVisible(this.batchStatusContainer);
  }

  /**
   * Verify batch monitoring section
   */
  async verifyBatchMonitoring(): Promise<void> {
    await this.waitForVisible(this.batchStatusContainer);
    await this.waitForVisible(this.currentBatchStatus);
    await this.waitForVisible(this.batchProgressBar);
  }

  /**
   * Verify error log section
   */
  async verifyErrorLogSection(): Promise<void> {
    await this.waitForVisible(this.errorLogContainer);
    await this.waitForVisible(this.errorLogTabs);
    await this.waitForVisible(this.logSearchInput);
  }

  /**
   * Verify performance metrics section
   */
  async verifyPerformanceMetrics(): Promise<void> {
    await this.waitForVisible(this.performanceContainer);
    await this.waitForVisible(this.cpuUsageChart);
    await this.waitForVisible(this.memoryUsageChart);
  }

  /**
   * Wait for real-time updates
   */
  async waitForRealTimeUpdate(elementType: 'batch' | 'metrics' | 'logs'): Promise<void> {
    let targetElement: Locator;

    switch (elementType) {
      case 'batch':
        targetElement = this.batchProgressBar;
        break;
      case 'metrics':
        targetElement = this.cpuUsageChart;
        break;
      case 'logs':
        targetElement = this.logEntries.first();
        break;
    }

    // Wait for the element to change (indicating real-time update)
    const initialValue = await targetElement.getAttribute('data-last-updated');

    await this.page.waitForFunction(
      ([element, initial]) => {
        const current = element?.getAttribute('data-last-updated');
        return current !== initial;
      },
      [await targetElement.elementHandle(), initialValue],
      { timeout: 30000 }
    );
  }

  /**
   * Monitor dashboard for errors
   */
  async monitorDashboardErrors(): Promise<string[]> {
    return await this.monitorConsoleErrors();
  }
}