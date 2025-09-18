import { test, expect } from '@playwright/test';
import { SqlExecutionPage } from './page-objects/SqlExecutionPage';

test.describe('SQL Execution Screen E2E Tests', () => {
  let sqlPage: SqlExecutionPage;

  test.beforeEach(async ({ page }) => {
    sqlPage = new SqlExecutionPage(page);
    await sqlPage.goto();
    await sqlPage.verifySqlExecutionPageLoaded();
  });

  test.describe('Query Input and Execution', () => {
    test('should execute simple SELECT query successfully', async ({ page }) => {
      const query = 'SELECT * FROM users LIMIT 10;';

      await test.step('Enter and execute query', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Verify results are displayed', async () => {
        const results = await sqlPage.getQueryResults();
        expect(results.length).toBeGreaterThan(0);
        expect(results.length).toBeLessThanOrEqual(10);

        // Verify table headers are present
        const headers = Object.keys(results[0]);
        expect(headers.length).toBeGreaterThan(0);
      });

      await test.step('Verify execution metrics', async () => {
        const executionTime = await sqlPage.getExecutionTime();
        expect(executionTime).toMatch(/\d+\.?\d*\s?(ms|s)/); // Should show time with units

        const rowCount = await sqlPage.getTotalRowCount();
        expect(rowCount).toContain('10'); // Should show row count
      });
    });

    test('should execute query using Ctrl+Enter keyboard shortcut', async ({ page }) => {
      const query = 'SELECT COUNT(*) as total_users FROM users;';

      await test.step('Execute query with keyboard shortcut', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQueryWithKeyboard();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Verify single row result', async () => {
        const results = await sqlPage.getQueryResults();
        expect(results.length).toBe(1);
        expect(results[0]).toHaveProperty('total_users');
      });
    });

    test('should handle complex JOIN queries', async ({ page }) => {
      const complexQuery = `
        SELECT u.email, p.first_name, p.last_name, j.title as job_title
        FROM users u
        JOIN profiles p ON u.id = p.user_id
        LEFT JOIN applications a ON u.id = a.user_id
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE u.created_at > '2024-01-01'
        ORDER BY u.created_at DESC
        LIMIT 50;
      `;

      await test.step('Execute complex JOIN query', async () => {
        await sqlPage.enterQuery(complexQuery);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Verify complex results structure', async () => {
        const results = await sqlPage.getQueryResults();
        expect(results.length).toBeGreaterThan(0);

        // Verify expected columns exist
        const firstResult = results[0];
        expect(firstResult).toHaveProperty('email');
        expect(firstResult).toHaveProperty('first_name');
        expect(firstResult).toHaveProperty('last_name');
      });

      await test.step('Verify performance metrics for complex query', async () => {
        const metrics = await sqlPage.getPerformanceMetrics();
        expect(metrics.duration).toBeTruthy();
        expect(metrics.memoryUsage).toBeTruthy();
        expect(metrics.connectionStatus).toBe('Connected');
      });
    });

    test('should format SQL query properly', async ({ page }) => {
      const messyQuery = 'select*from users where id=1and status="active"order by created_at;';
      const expectedFormatted = `SELECT *
FROM users
WHERE id = 1
  AND status = "active"
ORDER BY created_at;`;

      await test.step('Format messy query', async () => {
        await sqlPage.enterQuery(messyQuery);
        await sqlPage.formatQuery();

        // Verify query is formatted (this would depend on implementation)
        const formattedQuery = await sqlPage.queryInput.inputValue();
        expect(formattedQuery).toContain('SELECT *');
        expect(formattedQuery).toContain('FROM users');
        expect(formattedQuery).toContain('WHERE id = 1');
      });
    });

    test('should clear query input', async ({ page }) => {
      const query = 'SELECT * FROM users;';

      await test.step('Clear query', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.clearQuery();

        const queryContent = await sqlPage.queryInput.inputValue();
        expect(queryContent).toBe('');
      });
    });
  });

  test.describe('Results Display and Pagination', () => {
    test('should display results with proper pagination', async ({ page }) => {
      const largeResultQuery = 'SELECT * FROM users ORDER BY id;';

      await test.step('Execute query that returns many results', async () => {
        await sqlPage.enterQuery(largeResultQuery);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Verify pagination controls', async () => {
        const pageInfo = await sqlPage.getPageInfo();
        expect(pageInfo).toContain('Page 1');

        // Test next page if available
        if (await sqlPage.nextPageButton.isEnabled()) {
          await sqlPage.goToNextPage();

          const newPageInfo = await sqlPage.getPageInfo();
          expect(newPageInfo).toContain('Page 2');
        }
      });

      await test.step('Change page size', async () => {
        await sqlPage.changePageSize('50');

        // Verify more results are displayed
        const resultCount = await sqlPage.getResultRowCount();
        expect(resultCount).toBeGreaterThan(10); // Should be more than default
      });

      await test.step('Navigate back to previous page', async () => {
        if (await sqlPage.prevPageButton.isEnabled()) {
          await sqlPage.goToPreviousPage();

          const pageInfo = await sqlPage.getPageInfo();
          expect(pageInfo).toContain('Page 1');
        }
      });
    });

    test('should handle empty result sets', async ({ page }) => {
      const emptyQuery = 'SELECT * FROM users WHERE id = -1;'; // Should return no results

      await test.step('Execute query with no results', async () => {
        await sqlPage.enterQuery(emptyQuery);
        await sqlPage.executeQuery();
      });

      await test.step('Verify empty results handling', async () => {
        const noResultsMessage = sqlPage.noResultsMessage;
        await expect(noResultsMessage).toBeVisible();

        const executionTime = await sqlPage.getExecutionTime();
        expect(executionTime).toBeTruthy(); // Should still show execution time

        const rowCount = await sqlPage.getTotalRowCount();
        expect(rowCount).toContain('0'); // Should show 0 rows
      });
    });
  });

  test.describe('CSV Export Functionality', () => {
    test('should export query results to CSV', async ({ page }) => {
      const query = 'SELECT id, email, created_at FROM users LIMIT 20;';

      await test.step('Execute query for export', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Export results as CSV', async () => {
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          sqlPage.exportAsCsv()
        ]);

        expect(download.suggestedFilename()).toContain('.csv');

        // Verify file was downloaded
        const path = await download.path();
        expect(path).toBeTruthy();
      });
    });

    test('should export large result sets to CSV', async ({ page }) => {
      const largeQuery = 'SELECT * FROM users ORDER BY id LIMIT 1000;';

      await test.step('Execute large query', async () => {
        await sqlPage.enterQuery(largeQuery);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Export large result set', async () => {
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          sqlPage.exportAsCsv()
        ]);

        expect(download.suggestedFilename()).toContain('.csv');

        // Verify download completed (large files may take time)
        const path = await download.path();
        expect(path).toBeTruthy();
      });
    });

    test('should export results as JSON', async ({ page }) => {
      const query = 'SELECT * FROM jobs LIMIT 5;';

      await test.step('Execute query for JSON export', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Export results as JSON', async () => {
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          sqlPage.exportAsJson()
        ]);

        expect(download.suggestedFilename()).toContain('.json');

        // Verify file was downloaded
        const path = await download.path();
        expect(path).toBeTruthy();
      });
    });
  });

  test.describe('Query History Management', () => {
    test('should save and load queries from history', async ({ page }) => {
      const queries = [
        'SELECT * FROM users LIMIT 5;',
        'SELECT COUNT(*) FROM jobs;',
        'SELECT * FROM applications WHERE status = "pending";'
      ];

      await test.step('Execute multiple queries to build history', async () => {
        for (const query of queries) {
          await sqlPage.enterQuery(query);
          await sqlPage.executeQuery();
          await page.waitForTimeout(1000); // Small delay between queries
        }
      });

      await test.step('Verify queries are in history', async () => {
        const historyCount = await sqlPage.getQueryHistoryCount();
        expect(historyCount).toBeGreaterThanOrEqual(3);
      });

      await test.step('Load query from history', async () => {
        await sqlPage.loadQueryFromHistory(0); // Load most recent query

        const queryContent = await sqlPage.queryInput.inputValue();
        expect(queryContent).toBe(queries[queries.length - 1]);
      });

      await test.step('Clear query history', async () => {
        await sqlPage.clearQueryHistory();

        const historyCount = await sqlPage.getQueryHistoryCount();
        expect(historyCount).toBe(0);
      });
    });

    test('should persist query history across page reloads', async ({ page }) => {
      const query = 'SELECT * FROM users WHERE email LIKE "%@example.com";';

      await test.step('Execute query and reload page', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();

        // Reload page
        await page.reload();
        await sqlPage.verifySqlExecutionPageLoaded();
      });

      await test.step('Verify history persisted', async () => {
        const historyCount = await sqlPage.getQueryHistoryCount();
        expect(historyCount).toBeGreaterThan(0);

        // Load from history should work
        await sqlPage.loadQueryFromHistory(0);
        const loadedQuery = await sqlPage.queryInput.inputValue();
        expect(loadedQuery).toContain('example.com');
      });
    });
  });

  test.describe('Sample Queries', () => {
    test('should load and execute sample queries', async ({ page }) => {
      await test.step('Load a sample query', async () => {
        await sqlPage.loadSampleQuery('user-stats');

        const queryContent = await sqlPage.queryInput.inputValue();
        expect(queryContent).toBeTruthy();
        expect(queryContent.toLowerCase()).toContain('select');
      });

      await test.step('Execute sample query', async () => {
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();

        const results = await sqlPage.getQueryResults();
        expect(results.length).toBeGreaterThan(0);
      });
    });

    test('should provide different categories of sample queries', async ({ page }) => {
      const sampleCategories = ['basic-queries', 'joins', 'aggregations', 'advanced'];

      for (const category of sampleCategories) {
        await test.step(`Test ${category} sample queries`, async () => {
          // This would depend on the actual implementation of sample queries
          const sampleButton = page.getByTestId(`sample-${category}`);

          if (await sampleButton.isVisible()) {
            await sampleButton.click();

            const queryContent = await sqlPage.queryInput.inputValue();
            expect(queryContent).toBeTruthy();
          }
        });
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle SQL syntax errors gracefully', async ({ page }) => {
      const invalidQuery = 'SELCT * FORM users;'; // Deliberate syntax errors

      await test.step('Execute invalid query', async () => {
        await sqlPage.enterQuery(invalidQuery);
        await sqlPage.executeQuery();
        await sqlPage.verifyErrorDisplayed();
      });

      await test.step('Verify error message details', async () => {
        const errorMessage = await sqlPage.getErrorMessage();
        expect(errorMessage.toLowerCase()).toContain('syntax error');

        const errorDetails = await sqlPage.getErrorDetails();
        expect(errorDetails).toBeTruthy();
        expect(errorDetails).toContain('SELCT'); // Should highlight the error
      });

      await test.step('Dismiss error and continue', async () => {
        await sqlPage.dismissError();

        // Should be able to enter a new query
        const validQuery = 'SELECT 1 as test;';
        await sqlPage.enterQuery(validQuery);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });
    });

    test('should handle database connection errors', async ({ page }) => {
      await test.step('Simulate connection failure', async () => {
        // Mock network failure
        await page.route('**/api/sql/execute', route => {
          route.abort('failed');
        });

        const query = 'SELECT * FROM users LIMIT 1;';
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();
      });

      await test.step('Verify connection error handling', async () => {
        await sqlPage.verifyErrorDisplayed();

        const errorMessage = await sqlPage.getErrorMessage();
        expect(errorMessage.toLowerCase()).toContain('connection');

        // Verify connection status shows disconnected
        await sqlPage.verifyConnectionStatus('Disconnected');
      });
    });

    test('should handle query timeout scenarios', async ({ page }) => {
      const slowQuery = 'SELECT * FROM users, jobs; -- This would be slow without proper joins';

      await test.step('Simulate query timeout', async () => {
        // Mock slow response
        await page.route('**/api/sql/execute', async route => {
          await page.waitForTimeout(35000); // Longer than typical timeout
          await route.continue();
        });

        await sqlPage.enterQuery(slowQuery);
        await sqlPage.executeQuery();
      });

      await test.step('Verify timeout handling', async () => {
        await sqlPage.verifyErrorDisplayed();

        const errorMessage = await sqlPage.getErrorMessage();
        expect(errorMessage.toLowerCase()).toContain('timeout');
      });
    });

    test('should handle permission errors', async ({ page }) => {
      const restrictedQuery = 'DROP TABLE users;'; // Should be restricted

      await test.step('Attempt restricted operation', async () => {
        await page.route('**/api/sql/execute', route => {
          route.fulfill({
            status: 403,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Permission denied: DROP operations not allowed'
            })
          });
        });

        await sqlPage.enterQuery(restrictedQuery);
        await sqlPage.executeQuery();
      });

      await test.step('Verify permission error handling', async () => {
        await sqlPage.verifyErrorDisplayed();

        const errorMessage = await sqlPage.getErrorMessage();
        expect(errorMessage.toLowerCase()).toContain('permission');
        expect(errorMessage).toContain('DROP operations not allowed');
      });
    });
  });

  test.describe('Performance and Monitoring', () => {
    test('should display query execution metrics', async ({ page }) => {
      const query = 'SELECT COUNT(*) as total, status FROM applications GROUP BY status;';

      await test.step('Execute query with performance monitoring', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQuery();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Verify performance metrics', async () => {
        const metrics = await sqlPage.getPerformanceMetrics();

        expect(metrics.duration).toMatch(/\d+\.?\d*\s?(ms|s)/);
        expect(metrics.memoryUsage).toBeTruthy();
        expect(metrics.connectionStatus).toBe('Connected');
      });

      await test.step('Verify execution time is reasonable', async () => {
        const executionTime = await sqlPage.getExecutionTime();
        const timeMatch = executionTime.match(/(\d+\.?\d*)/);

        if (timeMatch) {
          const timeValue = parseFloat(timeMatch[1]);

          if (executionTime.includes('s')) {
            expect(timeValue).toBeLessThan(30); // Less than 30 seconds
          } else {
            expect(timeValue).toBeLessThan(5000); // Less than 5000 ms
          }
        }
      });
    });

    test('should monitor long-running queries', async ({ page }) => {
      const complexQuery = `
        SELECT
          u.email,
          COUNT(DISTINCT a.id) as application_count,
          AVG(j.salary_min) as avg_salary_applied,
          MAX(a.created_at) as last_application
        FROM users u
        LEFT JOIN applications a ON u.id = a.user_id
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE u.created_at > '2023-01-01'
        GROUP BY u.id, u.email
        HAVING application_count > 0
        ORDER BY application_count DESC, avg_salary_applied DESC;
      `;

      await test.step('Start long-running query', async () => {
        await sqlPage.enterQuery(complexQuery);
        await sqlPage.executeQuery();

        // Verify query execution indicator appears
        const isExecuting = await sqlPage.isQueryExecuting();
        expect(isExecuting).toBe(true);
      });

      await test.step('Monitor query completion', async () => {
        await sqlPage.waitForQueryExecution();

        // Verify query completed
        const isExecuting = await sqlPage.isQueryExecuting();
        expect(isExecuting).toBe(false);

        await sqlPage.verifyQueryResultsDisplayed();
      });
    });
  });

  test.describe('Keyboard Shortcuts and Usability', () => {
    test('should support keyboard shortcuts', async ({ page }) => {
      const query = 'SELECT * FROM jobs WHERE status = "active";';

      await test.step('Test Ctrl+Enter for execution', async () => {
        await sqlPage.enterQuery(query);
        await sqlPage.executeQueryWithKeyboard();
        await sqlPage.verifyQueryResultsDisplayed();
      });

      await test.step('Test Ctrl+K for clearing (if implemented)', async () => {
        await sqlPage.queryInput.focus();
        await page.keyboard.press('Control+k');

        // If implemented, query should be cleared
        const queryContent = await sqlPage.queryInput.inputValue();
        // This depends on implementation - might clear or just select all
      });

      await test.step('Test Tab for indentation in query editor', async () => {
        await sqlPage.clearQuery();
        await sqlPage.queryInput.focus();
        await page.keyboard.type('SELECT');
        await page.keyboard.press('Enter');
        await page.keyboard.press('Tab');
        await page.keyboard.type('id,');

        const queryContent = await sqlPage.queryInput.inputValue();
        expect(queryContent).toContain('SELECT');
        expect(queryContent).toContain('id,');
      });
    });

    test('should provide helpful query suggestions (if implemented)', async ({ page }) => {
      await test.step('Test autocomplete suggestions', async () => {
        await sqlPage.queryInput.focus();
        await page.keyboard.type('SEL');

        // If autocomplete is implemented, suggestions should appear
        const suggestions = page.getByTestId('query-suggestions');

        if (await suggestions.isVisible()) {
          expect(suggestions).toBeVisible();

          const suggestionItems = suggestions.locator('[data-testid="suggestion-item"]');
          const count = await suggestionItems.count();
          expect(count).toBeGreaterThan(0);
        }
      });
    });
  });

  test.describe('Concurrent User Scenarios', () => {
    test('should handle multiple concurrent query executions', async ({ page, context }) => {
      // This test simulates what happens when multiple users execute queries
      // In a real application, this would test server-side concurrency handling

      const queries = [
        'SELECT COUNT(*) FROM users;',
        'SELECT COUNT(*) FROM jobs;',
        'SELECT COUNT(*) FROM applications;'
      ];

      await test.step('Execute multiple queries in sequence', async () => {
        for (const query of queries) {
          await sqlPage.enterQuery(query);
          await sqlPage.executeQuery();
          await sqlPage.verifyQueryResultsDisplayed();

          // Small delay to simulate realistic usage
          await page.waitForTimeout(500);
        }
      });

      await test.step('Verify all queries were executed successfully', async () => {
        const historyCount = await sqlPage.getQueryHistoryCount();
        expect(historyCount).toBeGreaterThanOrEqual(queries.length);
      });
    });
  });
});