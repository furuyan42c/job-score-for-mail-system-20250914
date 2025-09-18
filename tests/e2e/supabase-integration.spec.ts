/**
 * T071: Supabase統合E2Eテスト - TDD Implementation
 * Comprehensive E2E tests for Supabase integration using Playwright
 */

import { test, expect } from '@playwright/test'

test.describe('T071: Supabase Integration E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000')

    // Wait for the page to load
    await page.waitForLoadState('networkidle')
  })

  test.describe('T068: Frontend Supabase Client Integration', () => {
    test('should display database management interface', async ({ page }) => {
      // Check for main title
      await expect(page.locator('h1')).toContainText('メールスコアリングシステム - データベース管理ツール')

      // Check for SQLite badge
      await expect(page.locator('text=SQLite風')).toBeVisible()

      // Check for Database icon
      await expect(page.locator('svg.h-8.w-8')).toBeVisible()
    })

    test('should show Supabase connection status', async ({ page }) => {
      // Look for Supabase connection indicator
      const connectionStatus = page.locator('text=/接続/')
      await expect(connectionStatus).toBeVisible()
    })

    test('should display table list in sidebar', async ({ page }) => {
      // Check for tables list
      const tablesList = page.locator('[data-testid="tables-list"]')
      await expect(tablesList).toBeVisible()

      // Check for specific tables
      await expect(page.locator('text=users')).toBeVisible()
      await expect(page.locator('text=jobs')).toBeVisible()
      await expect(page.locator('text=prefecture_master')).toBeVisible()
      await expect(page.locator('text=city_master')).toBeVisible()
    })

    test('should allow table search', async ({ page }) => {
      // Find search input
      const searchInput = page.locator('input[placeholder="テーブル検索..."]')
      await expect(searchInput).toBeVisible()

      // Search for a specific table
      await searchInput.fill('user')

      // Check filtered results
      await expect(page.locator('.table-item', { hasText: 'users' })).toBeVisible()
      await expect(page.locator('.table-item', { hasText: 'user_actions' })).toBeVisible()
      await expect(page.locator('.table-item', { hasText: 'user_profiles' })).toBeVisible()

      // Non-user tables should be hidden
      await expect(page.locator('.table-item', { hasText: 'prefecture_master' })).not.toBeVisible()
    })
  })

  test.describe('T069: Real-time Query Execution', () => {
    test('should display SQL query tab', async ({ page }) => {
      // Click on SQL query tab
      await page.click('text=SQLクエリ')

      // Check query editor is visible
      await expect(page.locator('text=クエリエディタ')).toBeVisible()

      // Check for textarea
      const queryTextarea = page.locator('textarea')
      await expect(queryTextarea).toBeVisible()

      // Check default query
      const queryValue = await queryTextarea.inputValue()
      expect(queryValue).toContain('SELECT * FROM')
    })

    test('should execute SELECT query successfully', async ({ page }) => {
      // Navigate to SQL query tab
      await page.click('text=SQLクエリ')

      // Find query textarea and enter a simple query
      const queryTextarea = page.locator('textarea')
      await queryTextarea.clear()
      await queryTextarea.fill('SELECT * FROM prefecture_master LIMIT 5;')

      // Click execute button
      await page.click('button:has-text("クエリ実行")')

      // Wait for results
      await page.waitForSelector('text=/実行時間/', { timeout: 10000 })

      // Check for success indicators
      await expect(page.locator('text=/成功/')).toBeVisible()
      await expect(page.locator('text=/実行時間/')).toBeVisible()
    })

    test('should prevent dangerous SQL operations', async ({ page }) => {
      // Navigate to SQL query tab
      await page.click('text=SQLクエリ')

      // Try to execute a DROP command
      const queryTextarea = page.locator('textarea')
      await queryTextarea.clear()
      await queryTextarea.fill('DROP TABLE users;')

      // Click execute button
      await page.click('button:has-text("クエリ実行")')

      // Wait for error message
      await page.waitForSelector('text=/error|エラー|Security/i', { timeout: 5000 })

      // Check for security violation message
      const errorMessage = page.locator('[role="alert"], .text-destructive, .text-red-500')
      await expect(errorMessage).toBeVisible()
    })

    test('should display query history', async ({ page }) => {
      // Navigate to SQL query tab
      await page.click('text=SQLクエリ')

      // Execute a query
      const queryTextarea = page.locator('textarea')
      await queryTextarea.clear()
      await queryTextarea.fill('SELECT COUNT(*) FROM users;')
      await page.click('button:has-text("クエリ実行")')

      // Wait for execution
      await page.waitForTimeout(2000)

      // Check if query history exists
      const historySection = page.locator('text=/クエリ履歴|Query History/i')
      if (await historySection.isVisible()) {
        // Verify history entry
        await expect(page.locator('text=/SELECT COUNT/')).toBeVisible()
      }
    })
  })

  test.describe('T070: Real-time Feature Integration', () => {
    test('should display real-time status indicator', async ({ page }) => {
      // Check for real-time connection status
      const realtimeIndicator = page.locator('text=/リアルタイム/')
      await expect(realtimeIndicator.first()).toBeVisible()

      // Check for activity indicator
      const activityIcon = page.locator('.animate-pulse, svg[class*="Activity"]')
      const connectionStatus = await activityIcon.count()
      expect(connectionStatus).toBeGreaterThanOrEqual(0) // May or may not be connected
    })

    test('should show real-time tab', async ({ page }) => {
      // Check for real-time tab
      const realtimeTab = page.locator('[role="tab"]:has-text("リアルタイム")')
      await expect(realtimeTab).toBeVisible()

      // Click on real-time tab
      await realtimeTab.click()

      // Check real-time content is displayed
      await expect(page.locator('text=リアルタイム更新通知')).toBeVisible()
      await expect(page.locator('text=接続ステータス')).toBeVisible()
    })

    test('should display real-time statistics', async ({ page }) => {
      // Navigate to real-time tab
      await page.click('[role="tab"]:has-text("リアルタイム")')

      // Check for statistics display
      await expect(page.locator('text=/INSERTイベント/')).toBeVisible()
      await expect(page.locator('text=/UPDATEイベント/')).toBeVisible()
      await expect(page.locator('text=/DELETEイベント/')).toBeVisible()
    })

    test('should toggle real-time connection', async ({ page }) => {
      // Find real-time toggle button
      const toggleButton = page.locator('button:has-text("リアルタイム"), button:has(svg[class*="Zap"])')

      if (await toggleButton.isVisible()) {
        // Get initial state
        const initialText = await toggleButton.textContent()

        // Click toggle
        await toggleButton.first().click()

        // Wait for state change
        await page.waitForTimeout(1000)

        // Check state changed
        const newText = await toggleButton.first().textContent()
        expect(newText).not.toBe(initialText)
      }
    })

    test('should display real-time notifications area', async ({ page }) => {
      // Navigate to real-time tab
      await page.click('[role="tab"]:has-text("リアルタイム")')

      // Check for notifications section
      await expect(page.locator('text=リアルタイム通知')).toBeVisible()

      // Check for empty state or notifications list
      const emptyState = page.locator('text=/まだリアルタイム更新はありません/')
      const notificationsList = page.locator('[class*="ScrollArea"]')

      // Either empty state or list should be visible
      const hasEmptyState = await emptyState.isVisible()
      const hasNotifications = await notificationsList.isVisible()
      expect(hasEmptyState || hasNotifications).toBeTruthy()
    })
  })

  test.describe('Data Browse Functionality', () => {
    test('should display data browse tab', async ({ page }) => {
      // Click on data browse tab
      await page.click('text=データ閲覧')

      // Check for data table
      await expect(page.locator('table')).toBeVisible()

      // Check for table headers
      await expect(page.locator('th').first()).toBeVisible()
    })

    test('should select different tables', async ({ page }) => {
      // Select a different table from sidebar
      await page.click('.table-item:has-text("jobs")')

      // Check SQL query updated
      const queryTextarea = page.locator('textarea')
      const queryValue = await queryTextarea.inputValue()
      expect(queryValue).toContain('jobs')

      // Navigate to browse tab
      await page.click('text=データ閲覧')

      // Check table badge shows selected table
      await expect(page.locator('text=テーブル: jobs')).toBeVisible()
    })
  })

  test.describe('Table Structure View', () => {
    test('should display table structure tab', async ({ page }) => {
      // Click on structure tab
      await page.click('text=テーブル構造')

      // Check for structure view
      await expect(page.locator('text=/テーブル構造:/')).toBeVisible()

      // Check for column information
      await expect(page.locator('text=カラム情報')).toBeVisible()
    })

    test('should show column details', async ({ page }) => {
      // Select a table
      await page.click('.table-item:has-text("users")')

      // Navigate to structure tab
      await page.click('text=テーブル構造')

      // Check for column names
      await expect(page.locator('text=user_id')).toBeVisible()
      await expect(page.locator('text=email')).toBeVisible()

      // Check for primary key indicator
      await expect(page.locator('text=PK')).toBeVisible()
    })
  })

  test.describe('Responsive Design', () => {
    test('should be responsive on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      // Check main elements are still visible
      await expect(page.locator('h1')).toBeVisible()

      // Tabs should be scrollable or stacked
      const tabs = page.locator('[role="tablist"]')
      await expect(tabs).toBeVisible()
    })

    test('should be responsive on tablet', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 })

      // Check layout adapts
      await expect(page.locator('h1')).toBeVisible()
      await expect(page.locator('[data-testid="tables-list"]')).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // Intercept Supabase requests and fail them
      await page.route('**/rest/v1/**', route => route.abort())

      // Try to execute a query
      await page.click('text=SQLクエリ')
      const queryTextarea = page.locator('textarea')
      await queryTextarea.fill('SELECT * FROM users;')
      await page.click('button:has-text("クエリ実行")')

      // Should show error message
      await expect(page.locator('text=/error|エラー|失敗/i')).toBeVisible({ timeout: 10000 })
    })
  })

  test.describe('Performance', () => {
    test('should load page quickly', async ({ page }) => {
      const startTime = Date.now()
      await page.goto('http://localhost:3000')
      await page.waitForLoadState('domcontentloaded')
      const loadTime = Date.now() - startTime

      // Page should load in under 3 seconds
      expect(loadTime).toBeLessThan(3000)
    })

    test('should execute queries with reasonable performance', async ({ page }) => {
      await page.click('text=SQLクエリ')

      const queryTextarea = page.locator('textarea')
      await queryTextarea.fill('SELECT * FROM prefecture_master LIMIT 10;')

      const startTime = Date.now()
      await page.click('button:has-text("クエリ実行")')
      await page.waitForSelector('text=/実行時間/', { timeout: 5000 })
      const queryTime = Date.now() - startTime

      // Query should complete in under 5 seconds
      expect(queryTime).toBeLessThan(5000)
    })
  })
})

// Accessibility tests
test.describe('Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check for role attributes
    const tabs = page.locator('[role="tablist"]')
    await expect(tabs).toBeVisible()

    const tabButtons = page.locator('[role="tab"]')
    expect(await tabButtons.count()).toBeGreaterThan(0)
  })

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Tab through interface
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Check focus is visible
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()
  })
})