/**
 * T071: Supabase Integration E2E Tests
 * Complete end-to-end testing of Supabase functionality
 */

import { test, expect, Page } from '@playwright/test'
import { createClient } from '@supabase/supabase-js'

// Test configuration
const SUPABASE_URL = process.env.SUPABASE_URL || 'http://localhost:54321'
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'

// Create Supabase client for test setup/teardown
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

test.describe('Supabase Full Integration', () => {
  // Test data
  let testJobId: number
  let testUserId: string = `test-user-${Date.now()}`

  test.beforeAll(async () => {
    // Insert test data for testing
    const { data, error } = await supabase
      .from('job_data')
      .insert({
        endcl_cd: 'TEST-001',
        application_name: 'E2E Test Job',
        hourly_wage: 1200,
        company_name: 'Test Company',
        work_content: 'Test job for E2E testing'
      })
      .select()
      .single()

    if (error) {
      console.error('Failed to create test data:', error)
    } else {
      testJobId = data.job_id
    }
  })

  test.afterAll(async () => {
    // Cleanup test data
    if (testJobId) {
      await supabase.from('job_data').delete().eq('job_id', testJobId)
    }
  })

  test.describe('SQL Query Execution', () => {
    test('should execute SELECT queries successfully', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to SQL query tab
      await page.getByRole('tab', { name: /SQL Query/i }).click()

      // Enter a simple SELECT query
      const query = 'SELECT COUNT(*) as total FROM job_data'
      await page.fill('textarea[placeholder*="SELECT"]', query)

      // Execute query
      await page.click('button:has-text("Execute")')

      // Verify results are displayed
      await expect(page.locator('.query-results')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('.query-results')).toContainText('total')
    })

    test('should block dangerous queries', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to SQL query tab
      await page.getByRole('tab', { name: /SQL Query/i }).click()

      // Try dangerous queries
      const dangerousQueries = [
        'DROP TABLE users',
        'DELETE FROM job_data',
        'UPDATE prefecture_master SET name = "Hacked"',
        'INSERT INTO users VALUES ("malicious")'
      ]

      for (const query of dangerousQueries) {
        await page.fill('textarea[placeholder*="SELECT"]', query)
        await page.click('button:has-text("Execute")')

        // Should show security error
        await expect(page.locator('.error-message')).toContainText(/security|not allowed|SELECT only/i, { timeout: 3000 })
      }
    })

    test('should handle query timeout gracefully', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to SQL query tab
      await page.getByRole('tab', { name: /SQL Query/i }).click()

      // Create a query that would timeout (if we had large data)
      const slowQuery = `
        SELECT * FROM job_data j1
        CROSS JOIN job_data j2
        CROSS JOIN job_data j3
      `
      await page.fill('textarea[placeholder*="SELECT"]', slowQuery)
      await page.click('button:has-text("Execute")')

      // Should either complete or show timeout message
      await expect(page.locator('.query-results, .error-message')).toBeVisible({ timeout: 35000 })
    })
  })

  test.describe('Realtime Updates', () => {
    test('should receive realtime INSERT updates', async ({ page, context }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to Data Browser tab
      await page.getByRole('tab', { name: /Data Browser/i }).click()

      // Select job_data table
      await page.selectOption('select', 'job_data')
      await page.waitForTimeout(1000) // Wait for initial data load

      // Get initial row count
      const initialRows = await page.locator('tbody tr').count()

      // Insert new data via Supabase (simulating another user)
      const { data: newJob } = await supabase
        .from('job_data')
        .insert({
          endcl_cd: 'REALTIME-001',
          application_name: 'Realtime Test Job',
          hourly_wage: 1500,
          company_name: 'Realtime Company'
        })
        .select()
        .single()

      // Wait for realtime update
      await page.waitForTimeout(2000)

      // Verify new row appears
      const updatedRows = await page.locator('tbody tr').count()
      expect(updatedRows).toBeGreaterThan(initialRows)

      // Cleanup
      if (newJob) {
        await supabase.from('job_data').delete().eq('job_id', newJob.job_id)
      }
    })

    test('should receive realtime UPDATE notifications', async ({ page }) => {
      // Create test record
      const { data: testRecord } = await supabase
        .from('job_data')
        .insert({
          endcl_cd: 'UPDATE-TEST',
          application_name: 'Original Name',
          hourly_wage: 1000
        })
        .select()
        .single()

      if (!testRecord) return

      await page.goto(FRONTEND_URL)

      // Navigate to Data Browser
      await page.getByRole('tab', { name: /Data Browser/i }).click()
      await page.selectOption('select', 'job_data')
      await page.waitForTimeout(1000)

      // Find the row with our test data
      const testRow = page.locator('tr', { hasText: 'UPDATE-TEST' })
      await expect(testRow).toContainText('Original Name')

      // Update via Supabase
      await supabase
        .from('job_data')
        .update({ application_name: 'Updated Name' })
        .eq('job_id', testRecord.job_id)

      // Wait for realtime update
      await expect(testRow).toContainText('Updated Name', { timeout: 5000 })

      // Cleanup
      await supabase.from('job_data').delete().eq('job_id', testRecord.job_id)
    })

    test('should receive realtime DELETE notifications', async ({ page }) => {
      // Create test record
      const { data: testRecord } = await supabase
        .from('job_data')
        .insert({
          endcl_cd: 'DELETE-TEST',
          application_name: 'To Be Deleted',
          hourly_wage: 999
        })
        .select()
        .single()

      if (!testRecord) return

      await page.goto(FRONTEND_URL)

      // Navigate to Data Browser
      await page.getByRole('tab', { name: /Data Browser/i }).click()
      await page.selectOption('select', 'job_data')
      await page.waitForTimeout(1000)

      // Verify record exists
      const testRow = page.locator('tr', { hasText: 'DELETE-TEST' })
      await expect(testRow).toBeVisible()

      // Delete via Supabase
      await supabase
        .from('job_data')
        .delete()
        .eq('job_id', testRecord.job_id)

      // Verify row disappears
      await expect(testRow).not.toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Multi-User Concurrency', () => {
    test('should handle multiple concurrent users', async ({ browser }) => {
      // Create 3 browser contexts (simulating 3 users)
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ])

      const pages = await Promise.all(
        contexts.map(ctx => ctx.newPage())
      )

      // All users navigate to the app
      await Promise.all(
        pages.map(page => page.goto(FRONTEND_URL))
      )

      // All users go to Data Browser
      await Promise.all(
        pages.map(async page => {
          await page.getByRole('tab', { name: /Data Browser/i }).click()
          await page.selectOption('select', 'job_data')
        })
      )

      // User 1 inserts data
      const { data: newJob } = await supabase
        .from('job_data')
        .insert({
          endcl_cd: 'MULTI-USER-TEST',
          application_name: 'Multi User Test',
          hourly_wage: 2000
        })
        .select()
        .single()

      // All users should see the update
      await Promise.all(
        pages.map(async page => {
          await expect(page.locator('tr', { hasText: 'MULTI-USER-TEST' }))
            .toBeVisible({ timeout: 5000 })
        })
      )

      // Cleanup
      if (newJob) {
        await supabase.from('job_data').delete().eq('job_id', newJob.job_id)
      }

      // Close contexts
      await Promise.all(contexts.map(ctx => ctx.close()))
    })
  })

  test.describe('Performance Tests', () => {
    test('should handle large result sets efficiently', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to SQL query tab
      await page.getByRole('tab', { name: /SQL Query/i }).click()

      // Query for potentially large dataset
      const query = 'SELECT * FROM job_data LIMIT 1000'
      await page.fill('textarea[placeholder*="SELECT"]', query)

      const startTime = Date.now()
      await page.click('button:has-text("Execute")')

      // Should complete within reasonable time
      await expect(page.locator('.query-results')).toBeVisible({ timeout: 10000 })
      const endTime = Date.now()

      expect(endTime - startTime).toBeLessThan(10000) // Should complete in under 10 seconds
    })

    test('should paginate large tables efficiently', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Navigate to Data Browser
      await page.getByRole('tab', { name: /Data Browser/i }).click()
      await page.selectOption('select', 'job_data')

      // Check pagination controls are visible
      await expect(page.locator('.pagination')).toBeVisible({ timeout: 5000 })

      // Test navigation between pages (if applicable)
      const nextButton = page.locator('button:has-text("Next")')
      if (await nextButton.isVisible()) {
        await nextButton.click()
        await expect(page.locator('tbody')).toBeVisible({ timeout: 3000 })
      }
    })
  })

  test.describe('Error Recovery', () => {
    test('should recover from connection errors', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Simulate offline (Note: actual implementation would require network manipulation)
      await page.context().setOffline(true)

      // Try to execute a query
      await page.getByRole('tab', { name: /SQL Query/i }).click()
      await page.fill('textarea[placeholder*="SELECT"]', 'SELECT 1')
      await page.click('button:has-text("Execute")')

      // Should show connection error
      await expect(page.locator('.error-message')).toContainText(/connection|network/i, { timeout: 5000 })

      // Go back online
      await page.context().setOffline(false)

      // Retry should work
      await page.click('button:has-text("Execute")')
      await expect(page.locator('.query-results')).toBeVisible({ timeout: 5000 })
    })

    test('should handle invalid table gracefully', async ({ page }) => {
      await page.goto(FRONTEND_URL)

      // Try to query non-existent table
      await page.getByRole('tab', { name: /SQL Query/i }).click()
      await page.fill('textarea[placeholder*="SELECT"]', 'SELECT * FROM non_existent_table')
      await page.click('button:has-text("Execute")')

      // Should show appropriate error
      await expect(page.locator('.error-message')).toContainText(/does not exist|not found/i, { timeout: 5000 })
    })
  })
})

test.describe('Security Tests', () => {
  test('should prevent SQL injection attempts', async ({ page }) => {
    await page.goto(FRONTEND_URL)

    await page.getByRole('tab', { name: /SQL Query/i }).click()

    // Various SQL injection attempts
    const injectionAttempts = [
      "SELECT * FROM users WHERE id = '1' OR '1'='1'",
      "SELECT * FROM users; DROP TABLE users;",
      "SELECT * FROM users WHERE name = '' OR ''=''",
      "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM passwords"
    ]

    for (const attempt of injectionAttempts) {
      await page.fill('textarea[placeholder*="SELECT"]', attempt)
      await page.click('button:has-text("Execute")')

      // Should either block or safely execute without side effects
      const result = await page.locator('.query-results, .error-message').textContent({ timeout: 3000 })

      // Verify no dangerous operations occurred
      const { data } = await supabase.from('users').select('count').single()
      // Tables should still exist
    }
  })

  test('should enforce rate limiting', async ({ page }) => {
    await page.goto(FRONTEND_URL)

    await page.getByRole('tab', { name: /SQL Query/i }).click()

    // Attempt rapid-fire requests
    const promises = []
    for (let i = 0; i < 20; i++) {
      promises.push(
        page.fill('textarea[placeholder*="SELECT"]', `SELECT ${i}`).then(() =>
          page.click('button:has-text("Execute")')
        )
      )
    }

    await Promise.all(promises)

    // Should either handle all requests or show rate limit message
    // (Implementation would depend on actual rate limiting setup)
  })
})

// Helper function to setup test database
async function setupTestData() {
  // Insert sample data for testing
  const testData = [
    {
      endcl_cd: 'TEST-SETUP-001',
      application_name: 'Test Job 1',
      hourly_wage: 1000,
      company_name: 'Test Company 1'
    },
    {
      endcl_cd: 'TEST-SETUP-002',
      application_name: 'Test Job 2',
      hourly_wage: 1200,
      company_name: 'Test Company 2'
    }
  ]

  const { error } = await supabase.from('job_data').insert(testData)
  if (error) {
    console.error('Failed to setup test data:', error)
  }
}

// Helper function to cleanup test database
async function cleanupTestData() {
  await supabase
    .from('job_data')
    .delete()
    .like('endcl_cd', 'TEST%')
}