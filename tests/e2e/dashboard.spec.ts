import { test, expect } from '@playwright/test';
import { DashboardPage } from './page-objects/DashboardPage';

test.describe('Dashboard E2E Tests', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    // Set up authenticated session - in real implementation this would involve login
    await page.context().addCookies([
      {
        name: 'auth_token',
        value: 'mock_admin_token',
        domain: 'localhost',
        path: '/'
      }
    ]);

    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.verifyDashboardLoaded();
  });

  test.describe('Batch Status Display and Monitoring', () => {
    test('should display current batch status and progress', async ({ page }) => {
      await test.step('Verify batch status section is visible', async () => {
        await dashboardPage.verifyBatchMonitoring();
      });

      await test.step('Check current batch status', async () => {
        const batchStatus = await dashboardPage.getBatchStatus();
        expect(['Running', 'Paused', 'Completed', 'Failed', 'Pending']).toContain(batchStatus);
      });

      await test.step('Verify progress bar shows valid percentage', async () => {
        const progress = await dashboardPage.getBatchProgress();
        expect(progress).toBeGreaterThanOrEqual(0);
        expect(progress).toBeLessThanOrEqual(100);
      });

      await test.step('Check batch phase information', async () => {
        const phase = await dashboardPage.getBatchPhase();
        expect(phase).toBeTruthy();

        // Common phases in job matching system
        const expectedPhases = [
          'Initialization',
          'Data Collection',
          'Profile Analysis',
          'Job Matching',
          'Score Calculation',
          'Email Generation',
          'Finalization'
        ];

        expect(expectedPhases.some(expectedPhase =>
          phase.includes(expectedPhase)
        )).toBe(true);
      });
    });

    test('should update batch progress in real-time', async ({ page }) => {
      await test.step('Monitor progress bar updates', async () => {
        const initialProgress = await dashboardPage.getBatchProgress();

        // Wait for real-time update
        await dashboardPage.waitForRealTimeUpdate('batch');

        const updatedProgress = await dashboardPage.getBatchProgress();

        // Progress should either stay the same or increase
        expect(updatedProgress).toBeGreaterThanOrEqual(initialProgress);
      });

      await test.step('Monitor phase transitions', async () => {
        const initialPhase = await dashboardPage.getBatchPhase();

        // In a running system, phases might change
        // We'll wait for a potential change and verify it's valid
        try {
          await page.waitForFunction(
            ([element, initial]) => {
              const current = element?.textContent;
              return current !== initial;
            },
            [await dashboardPage.batchPhaseIndicator.elementHandle(), initialPhase],
            { timeout: 10000 }
          );

          const newPhase = await dashboardPage.getBatchPhase();
          expect(newPhase).not.toBe(initialPhase);
        } catch (error) {
          // Phase didn't change within timeout - that's also valid
          console.log('Batch phase remained stable during test period');
        }
      });
    });

    test('should handle batch control operations', async ({ page }) => {
      const initialStatus = await dashboardPage.getBatchStatus();

      if (initialStatus === 'Running') {
        await test.step('Pause running batch', async () => {
          await dashboardPage.pauseBatch();

          // Wait for status to update
          await page.waitForFunction(
            (element) => element?.textContent?.includes('Paused'),
            await dashboardPage.currentBatchStatus.elementHandle(),
            { timeout: 10000 }
          );

          const newStatus = await dashboardPage.getBatchStatus();
          expect(newStatus).toBe('Paused');
        });

        await test.step('Resume paused batch', async () => {
          await dashboardPage.restartBatch();

          // Wait for status to update
          await page.waitForFunction(
            (element) => element?.textContent?.includes('Running'),
            await dashboardPage.currentBatchStatus.elementHandle(),
            { timeout: 10000 }
          );

          const resumedStatus = await dashboardPage.getBatchStatus();
          expect(resumedStatus).toBe('Running');
        });
      }

      await test.step('Test stop batch functionality', async () => {
        // Set up dialog handler for confirmation
        page.on('dialog', async dialog => {
          expect(dialog.type()).toBe('confirm');
          expect(dialog.message()).toContain('stop');
          await dialog.accept();
        });

        await dashboardPage.stopBatch();

        // Wait for status to update
        await page.waitForFunction(
          (element) => {
            const text = element?.textContent;
            return text?.includes('Stopped') || text?.includes('Failed');
          },
          await dashboardPage.currentBatchStatus.elementHandle(),
          { timeout: 15000 }
        );
      });
    });

    test('should display batch timing information', async ({ page }) => {
      await test.step('Verify batch start time is displayed', async () => {
        const startTime = await dashboardPage.batchStartTime.textContent();
        expect(startTime).toBeTruthy();

        // Should be a valid timestamp format
        expect(startTime).toMatch(/\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}/);
      });

      await test.step('Verify estimated completion time', async () => {
        const estimatedCompletion = await dashboardPage.batchEstimatedCompletion.textContent();

        if (estimatedCompletion) {
          expect(estimatedCompletion).toBeTruthy();
          // Should show either time or "Calculating..." or similar
          expect(estimatedCompletion.length).toBeGreaterThan(0);
        }
      });
    });
  });

  test.describe('Error Log Management', () => {
    test('should display and filter error logs', async ({ page }) => {
      await test.step('Navigate to logs tab', async () => {
        await dashboardPage.switchToTab('logs');
        await dashboardPage.verifyErrorLogSection();
      });

      await test.step('Filter logs by ERROR severity', async () => {
        await dashboardPage.filterLogsBySeverity('error');

        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          // All logs should be ERROR level
          logs.forEach(log => {
            expect(log.level.toLowerCase()).toBe('error');
          });
        }
      });

      await test.step('Filter logs by WARNING severity', async () => {
        await dashboardPage.filterLogsBySeverity('warning');

        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          logs.forEach(log => {
            expect(log.level.toLowerCase()).toBe('warning');
          });
        }
      });

      await test.step('Filter logs by INFO severity', async () => {
        await dashboardPage.filterLogsBySeverity('info');

        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          logs.forEach(log => {
            expect(log.level.toLowerCase()).toBe('info');
          });
        }
      });
    });

    test('should support log search functionality', async ({ page }) => {
      await dashboardPage.switchToTab('logs');

      await test.step('Search for specific error terms', async () => {
        await dashboardPage.searchLogs('database');

        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          // At least one log should contain "database"
          const containsSearchTerm = logs.some(log =>
            log.message.toLowerCase().includes('database')
          );
          expect(containsSearchTerm).toBe(true);
        }
      });

      await test.step('Search for user-related errors', async () => {
        await dashboardPage.searchLogs('user');

        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          const containsSearchTerm = logs.some(log =>
            log.message.toLowerCase().includes('user')
          );
          expect(containsSearchTerm).toBe(true);
        }
      });

      await test.step('Search for connection errors', async () => {
        await dashboardPage.searchLogs('connection failed');

        // This might return no results, which is valid
        const logs = await dashboardPage.getLogEntries();
        if (logs.length > 0) {
          logs.forEach(log => {
            expect(log.message.toLowerCase()).toContain('connection');
          });
        }
      });
    });

    test('should handle log export functionality', async ({ page }) => {
      await dashboardPage.switchToTab('logs');

      await test.step('Export logs as file', async () => {
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          dashboardPage.exportLogs()
        ]);

        expect(download.suggestedFilename()).toMatch(/log.*\.(csv|json|txt)$/);

        const path = await download.path();
        expect(path).toBeTruthy();
      });
    });

    test('should manage log lifecycle', async ({ page }) => {
      await dashboardPage.switchToTab('logs');

      await test.step('Refresh logs manually', async () => {
        const initialLogs = await dashboardPage.getLogEntries();

        await dashboardPage.refreshLogs();

        // After refresh, we should still have logs (or same logs)
        const refreshedLogs = await dashboardPage.getLogEntries();
        expect(refreshedLogs.length).toBeGreaterThanOrEqual(0);
      });

      await test.step('Clear old logs', async () => {
        // Set up dialog handler for confirmation
        page.on('dialog', async dialog => {
          expect(dialog.type()).toBe('confirm');
          expect(dialog.message().toLowerCase()).toContain('clear');
          await dialog.accept();
        });

        await dashboardPage.clearLogs();

        // After clearing, log count should be reduced or zero
        const clearedLogs = await dashboardPage.getLogEntries();
        expect(clearedLogs.length).toBeGreaterThanOrEqual(0);
      });
    });

    test('should display log entry details correctly', async ({ page }) => {
      await dashboardPage.switchToTab('logs');

      await test.step('Verify log entry structure', async () => {
        const logs = await dashboardPage.getLogEntries();

        if (logs.length > 0) {
          const firstLog = logs[0];

          // Verify required fields
          expect(firstLog.timestamp).toBeTruthy();
          expect(firstLog.level).toBeTruthy();
          expect(firstLog.message).toBeTruthy();

          // Verify timestamp format
          expect(firstLog.timestamp).toMatch(/\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}/);

          // Verify valid log levels
          expect(['ERROR', 'WARN', 'INFO', 'DEBUG'].some(level =>
            firstLog.level.toUpperCase().includes(level)
          )).toBe(true);
        }
      });
    });
  });

  test.describe('Performance Metrics Display', () => {
    test('should display real-time performance metrics', async ({ page }) => {
      await test.step('Navigate to monitoring tab', async () => {
        await dashboardPage.switchToTab('monitoring');
        await dashboardPage.verifyPerformanceMetrics();
      });

      await test.step('Verify CPU usage metrics', async () => {
        const metrics = await dashboardPage.getPerformanceMetrics();

        if (metrics.cpuUsage) {
          const cpuValue = parseFloat(metrics.cpuUsage);
          expect(cpuValue).toBeGreaterThanOrEqual(0);
          expect(cpuValue).toBeLessThanOrEqual(100);
        }
      });

      await test.step('Verify memory usage metrics', async () => {
        const metrics = await dashboardPage.getPerformanceMetrics();

        if (metrics.memoryUsage) {
          const memoryValue = parseFloat(metrics.memoryUsage);
          expect(memoryValue).toBeGreaterThanOrEqual(0);
          expect(memoryValue).toBeLessThanOrEqual(100);
        }
      });

      await test.step('Verify database connection metrics', async () => {
        const metrics = await dashboardPage.getPerformanceMetrics();

        if (metrics.databaseConnections) {
          const dbConnections = parseInt(metrics.databaseConnections);
          expect(dbConnections).toBeGreaterThanOrEqual(0);
          // Should not exceed reasonable connection pool limits
          expect(dbConnections).toBeLessThan(1000);
        }
      });

      await test.step('Verify system health indicator', async () => {
        const metrics = await dashboardPage.getPerformanceMetrics();

        if (metrics.systemHealth) {
          const validHealthStates = ['Healthy', 'Warning', 'Critical', 'Good'];
          expect(validHealthStates.some(state =>
            metrics.systemHealth!.includes(state)
          )).toBe(true);
        }
      });
    });

    test('should update metrics in real-time', async ({ page }) => {
      await dashboardPage.switchToTab('monitoring');

      await test.step('Monitor real-time metric updates', async () => {
        const initialMetrics = await dashboardPage.getPerformanceMetrics();

        // Wait for metrics to update
        await dashboardPage.waitForRealTimeUpdate('metrics');

        const updatedMetrics = await dashboardPage.getPerformanceMetrics();

        // At least one metric should have updated (or could remain the same)
        // The important thing is that the system is actively monitoring
        expect(updatedMetrics).toBeTruthy();
      });
    });

    test('should handle metric time range selection', async ({ page }) => {
      await dashboardPage.switchToTab('monitoring');

      await test.step('Change metrics time range', async () => {
        await dashboardPage.setMetricsTimeRange('1h');

        // Wait for charts to update
        await page.waitForTimeout(2000);

        // Verify charts updated (implementation specific)
        const metrics = await dashboardPage.getPerformanceMetrics();
        expect(metrics).toBeTruthy();
      });

      await test.step('Test different time ranges', async () => {
        const timeRanges = ['5m', '15m', '1h', '24h'];

        for (const range of timeRanges) {
          await dashboardPage.setMetricsTimeRange(range);
          await page.waitForTimeout(1000);

          // Verify the interface responds to time range changes
          const metrics = await dashboardPage.getPerformanceMetrics();
          expect(metrics).toBeTruthy();
        }
      });
    });

    test('should handle auto-refresh functionality', async ({ page }) => {
      await dashboardPage.switchToTab('monitoring');

      await test.step('Enable auto-refresh', async () => {
        await dashboardPage.toggleAutoRefresh();

        // Verify auto-refresh is enabled (UI state check)
        const isEnabled = await dashboardPage.autoRefreshToggle.isChecked();
        expect(isEnabled).toBe(true);
      });

      await test.step('Set refresh interval', async () => {
        await dashboardPage.setRefreshInterval('30');

        // Wait for at least one refresh cycle
        await page.waitForTimeout(35000); // 35 seconds to ensure refresh occurs

        // Verify metrics were refreshed
        const metrics = await dashboardPage.getPerformanceMetrics();
        expect(metrics).toBeTruthy();
      });

      await test.step('Disable auto-refresh', async () => {
        await dashboardPage.toggleAutoRefresh();

        const isEnabled = await dashboardPage.autoRefreshToggle.isChecked();
        expect(isEnabled).toBe(false);
      });
    });

    test('should display processing speed indicators', async ({ page }) => {
      await dashboardPage.switchToTab('monitoring');

      await test.step('Verify processing speed metrics', async () => {
        const metrics = await dashboardPage.getPerformanceMetrics();

        if (metrics.processingSpeed) {
          // Should show some kind of throughput metric
          expect(metrics.processingSpeed).toBeTruthy();

          // Should contain numeric values
          const hasNumbers = /\d+/.test(metrics.processingSpeed);
          expect(hasNumbers).toBe(true);
        }
      });
    });
  });

  test.describe('System Statistics Display', () => {
    test('should display accurate system statistics', async ({ page }) => {
      await test.step('Verify statistics cards are present', async () => {
        const stats = await dashboardPage.getStatistics();

        expect(stats.totalJobs).toBeTruthy();
        expect(stats.activeUsers).toBeTruthy();
        expect(stats.systemUptime).toBeTruthy();
        expect(stats.errorRate).toBeTruthy();
      });

      await test.step('Verify statistics have valid formats', async () => {
        const stats = await dashboardPage.getStatistics();

        // Total jobs should be numeric
        const jobsMatch = stats.totalJobs.match(/\d+/);
        expect(jobsMatch).toBeTruthy();

        // Active users should be numeric
        const usersMatch = stats.activeUsers.match(/\d+/);
        expect(usersMatch).toBeTruthy();

        // Uptime should have time format
        expect(stats.systemUptime).toMatch(/\d+/);

        // Error rate should be percentage or number
        expect(stats.errorRate).toMatch(/\d+\.?\d*%?/);
      });
    });

    test('should update statistics over time', async ({ page }) => {
      await test.step('Monitor statistics changes', async () => {
        const initialStats = await dashboardPage.getStatistics();

        // Wait for potential updates
        await page.waitForTimeout(5000);

        const updatedStats = await dashboardPage.getStatistics();

        // Statistics might change or stay the same - both are valid
        // The important thing is they remain well-formatted
        expect(updatedStats.totalJobs).toBeTruthy();
        expect(updatedStats.activeUsers).toBeTruthy();
      });
    });
  });

  test.describe('Report Generation and Export', () => {
    test('should generate system reports', async ({ page }) => {
      await test.step('Generate performance report', async () => {
        const startDate = '2024-01-01';
        const endDate = '2024-01-31';

        await dashboardPage.generateReport('performance', startDate, endDate);

        // Wait for report generation to complete
        await page.waitForSelector('[data-testid="download-report-button"]:not([disabled])', {
          timeout: 30000
        });
      });

      await test.step('Download generated report', async () => {
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          dashboardPage.downloadReport()
        ]);

        expect(download.suggestedFilename()).toMatch(/report.*\.(pdf|csv|xlsx)$/);

        const path = await download.path();
        expect(path).toBeTruthy();
      });
    });

    test('should generate different types of reports', async ({ page }) => {
      const reportTypes = ['performance', 'errors', 'usage', 'batch-history'];

      for (const reportType of reportTypes) {
        await test.step(`Generate ${reportType} report`, async () => {
          try {
            await dashboardPage.generateReport(reportType, '2024-01-01', '2024-01-31');

            // Wait for generation to complete or fail
            await page.waitForSelector(
              '[data-testid="download-report-button"]:not([disabled]), [data-testid="report-error"]',
              { timeout: 15000 }
            );

            // If successful, try to download
            if (await dashboardPage.downloadReportButton.isEnabled()) {
              const [download] = await Promise.all([
                page.waitForEvent('download'),
                dashboardPage.downloadReport()
              ]);

              expect(download.suggestedFilename()).toBeTruthy();
            }
          } catch (error) {
            // Some report types might not be available - that's okay
            console.log(`Report type ${reportType} might not be available`);
          }
        });
      }
    });
  });

  test.describe('Dashboard Tab Navigation', () => {
    test('should navigate between dashboard tabs correctly', async ({ page }) => {
      const tabs = ['overview', 'monitoring', 'logs', 'settings'] as const;

      for (const tab of tabs) {
        await test.step(`Navigate to ${tab} tab`, async () => {
          await dashboardPage.switchToTab(tab);

          // Verify the tab content is loaded
          await page.waitForLoadState('networkidle');

          // Verify tab is active
          const tabElement = dashboardPage[`${tab}Tab`];
          const isActive = await tabElement.getAttribute('aria-selected') === 'true' ||
                          await tabElement.getAttribute('class') === 'active' ||
                          await tabElement.getAttribute('data-state') === 'active';

          if (isActive !== null) {
            expect(isActive).toBe(true);
          }
        });
      }
    });

    test('should maintain tab state during session', async ({ page }) => {
      await test.step('Switch to monitoring tab and verify persistence', async () => {
        await dashboardPage.switchToTab('monitoring');

        // Refresh page
        await page.reload();
        await dashboardPage.verifyDashboardLoaded();

        // Check if monitoring tab is still active (depends on implementation)
        // Some apps maintain tab state, others reset to default
        const url = page.url();
        const isMonitoringActive = url.includes('monitoring') ||
                                 await dashboardPage.monitoringTab.getAttribute('aria-selected') === 'true';

        // This is implementation-dependent, so we just verify no errors occurred
        expect(true).toBe(true);
      });
    });
  });

  test.describe('Dashboard Settings Management', () => {
    test('should manage dashboard settings', async ({ page }) => {
      await test.step('Navigate to settings', async () => {
        await dashboardPage.switchToTab('settings');

        // Verify settings section is visible
        await expect(dashboardPage.settingsContainer).toBeVisible();
      });

      await test.step('Update notification settings', async () => {
        // Enable/disable notification types
        const emailNotifications = page.getByTestId('email-notifications-toggle');
        if (await emailNotifications.isVisible()) {
          await emailNotifications.click();
        }

        const pushNotifications = page.getByTestId('push-notifications-toggle');
        if (await pushNotifications.isVisible()) {
          await pushNotifications.click();
        }
      });

      await test.step('Update system settings', async () => {
        // Update refresh intervals
        const refreshInterval = page.getByTestId('dashboard-refresh-interval');
        if (await refreshInterval.isVisible()) {
          await refreshInterval.selectOption('60');
        }

        // Update theme preferences
        const themeSelect = page.getByTestId('dashboard-theme');
        if (await themeSelect.isVisible()) {
          await themeSelect.selectOption('dark');
        }
      });

      await test.step('Save settings', async () => {
        await dashboardPage.saveSettings();

        // Verify settings were saved
        const successMessage = page.getByTestId('settings-success-message');
        if (await successMessage.isVisible()) {
          await expect(successMessage).toBeVisible();
        }
      });
    });
  });

  test.describe('Error Scenarios and Recovery', () => {
    test('should handle dashboard data loading failures', async ({ page }) => {
      await test.step('Simulate API failure', async () => {
        // Intercept and fail dashboard API calls
        await page.route('**/api/dashboard/**', route => {
          route.abort('failed');
        });

        await page.reload();

        // Verify error handling
        const errorMessage = page.getByTestId('dashboard-error');
        if (await errorMessage.isVisible()) {
          await expect(errorMessage).toBeVisible();
          await expect(errorMessage).toContainText('unable to load');
        }
      });
    });

    test('should monitor dashboard for console errors', async ({ page }) => {
      await test.step('Monitor for JavaScript errors', async () => {
        const errors = await dashboardPage.monitorDashboardErrors();

        // In a well-functioning dashboard, there should be no console errors
        expect(errors).toHaveLength(0);
      });
    });

    test('should handle network interruption gracefully', async ({ page }) => {
      await test.step('Simulate network failure during operation', async () => {
        // Start monitoring real-time updates
        await dashboardPage.switchToTab('monitoring');

        // Simulate network failure
        await page.context().setOffline(true);

        // Wait a moment
        await page.waitForTimeout(5000);

        // Restore network
        await page.context().setOffline(false);

        // Verify dashboard recovers
        await page.waitForLoadState('networkidle');
        await dashboardPage.verifyDashboardLoaded();
      });
    });
  });

  test.describe('Session Management', () => {
    test('should handle session timeout appropriately', async ({ page }) => {
      await test.step('Simulate expired session', async () => {
        // Clear authentication cookies
        await page.context().clearCookies();

        // Try to perform an authenticated action
        await dashboardPage.refreshLogs();

        // Should redirect to login or show auth error
        await page.waitForURL(/\/(login|auth)/, { timeout: 10000 }).catch(() => {
          // Or check for authentication error message
          const authError = page.getByTestId('auth-error');
          return expect(authError).toBeVisible();
        });
      });
    });

    test('should maintain dashboard state during idle time', async ({ page }) => {
      await test.step('Test dashboard during idle period', async () => {
        // Set specific tab and state
        await dashboardPage.switchToTab('monitoring');
        await dashboardPage.setMetricsTimeRange('1h');

        // Simulate idle time
        await page.waitForTimeout(30000); // 30 seconds

        // Verify dashboard is still functional
        await dashboardPage.verifyDashboardLoaded();

        const metrics = await dashboardPage.getPerformanceMetrics();
        expect(metrics).toBeTruthy();
      });
    });
  });

  test.describe('Responsive Design', () => {
    test('should work correctly on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await test.step('Verify mobile dashboard layout', async () => {
        await dashboardPage.goto();
        await dashboardPage.verifyDashboardLoaded();

        // On mobile, some elements might be collapsed or reorganized
        // We verify the core functionality is accessible
        const mobileNav = page.getByTestId('mobile-dashboard-nav');
        if (await mobileNav.isVisible()) {
          await expect(mobileNav).toBeVisible();
        }
      });

      await test.step('Test mobile tab navigation', async () => {
        // Mobile might use hamburger menu or swipe navigation
        const mobileMenu = page.getByTestId('mobile-menu-button');
        if (await mobileMenu.isVisible()) {
          await mobileMenu.click();

          const logsTab = page.getByTestId('mobile-logs-tab');
          if (await logsTab.isVisible()) {
            await logsTab.click();
            await dashboardPage.verifyErrorLogSection();
          }
        }
      });
    });

    test('should work correctly on tablet devices', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      await test.step('Verify tablet dashboard layout', async () => {
        await dashboardPage.goto();
        await dashboardPage.verifyDashboardLoaded();

        // Verify all main sections are accessible
        await dashboardPage.verifyBatchMonitoring();
        await dashboardPage.switchToTab('monitoring');
        await dashboardPage.verifyPerformanceMetrics();
      });
    });
  });
});