/**
 * T068: v0フロントエンドSupabase統合 - TDD E2Eテスト
 * Playwrightを使用したブラウザテスト（RED Phase）
 */

import { test, expect } from '@playwright/test'

test.describe('Supabase Integration E2E Tests (RED Phase)', () => {
  // 期待される失敗: Supabase接続がまだ実装されていない

  test.beforeEach(async ({ page }) => {
    // v0 SQLite管理画面にアクセス
    await page.goto('http://localhost:3000')

    // ページが読み込まれるまで待機
    await page.waitForLoadState('networkidle')
  })

  test('🔴 RED: Supabase connection test should fail initially', async ({ page }) => {
    // v0ページが読み込まれることを確認
    await expect(page).toHaveTitle(/database/i)

    // ブラウザコンソールでSupabase接続テスト実行
    const connectionResult = await page.evaluate(async () => {
      try {
        // Supabaseクライアントがまだ統合されていないため失敗想定
        if (typeof window !== 'undefined' && (window as any).supabase) {
          const { data, error } = await (window as any).supabase
            .from('prefecture_master')
            .select('count(*)')
            .limit(1)

          return { success: !error, error: error?.message }
        } else {
          return {
            success: false,
            error: 'Supabase client not available on window object'
          }
        }
      } catch (err) {
        return {
          success: false,
          error: err instanceof Error ? err.message : 'Unknown error'
        }
      }
    })

    // RED Phase期待: 接続が失敗する
    expect(connectionResult.success).toBe(false)
    expect(connectionResult.error).toContain('not available')
  })

  test('🔴 RED: Database table count should be 0 initially', async ({ page }) => {
    // v0のSQLクエリタブをクリック
    await page.click('text=SQLクエリ')

    // テーブル一覧が表示されることを確認（v0のモック実装）
    const tableList = page.locator('[data-testid="table-list"]')

    // RED Phase期待: 実際のSupabaseデータがまだ表示されない
    const tableCount = await page.evaluate(() => {
      // v0のモックデータ確認
      const mockTables = document.querySelectorAll('.table-item')
      return mockTables.length
    })

    // モックデータ（19テーブル）は表示されるが、実データは0
    expect(tableCount).toBeGreaterThan(0) // v0モックデータ

    // 実際のSupabaseからのデータ取得テスト
    const realDataResult = await page.evaluate(async () => {
      try {
        // まだ実装されていないため失敗想定
        const response = await fetch('/api/supabase/tables')
        return response.ok
      } catch {
        return false
      }
    })

    expect(realDataResult).toBe(false) // API未実装のため失敗
  })

  test('🔴 RED: SQL query execution should return mock data', async ({ page }) => {
    // SQLクエリエディタにアクセス
    await page.click('text=SQLクエリ')

    // クエリ入力エリアを確認
    const queryInput = page.locator('textarea[placeholder*="SQL"]')
    await expect(queryInput).toBeVisible()

    // サンプルクエリを入力
    await queryInput.fill('SELECT * FROM prefecture_master LIMIT 5;')

    // 実行ボタンをクリック
    await page.click('button:has-text("実行")')

    // 結果エリアが表示されることを確認
    const resultArea = page.locator('[data-testid="query-result"]')
    await expect(resultArea).toBeVisible()

    // RED Phase期待: モックデータまたはエラーメッセージ
    const resultText = await resultArea.textContent()

    // v0のモック実装または「実装予定」メッセージを確認
    expect(resultText).toMatch(/(モック|実装予定|mock|not implemented)/i)
  })

  test('🔴 RED: Real-time data updates should not work yet', async ({ page }) => {
    // データ閲覧タブにアクセス
    await page.click('text=データ閲覧')

    // テーブル選択
    await page.click('text=prefecture_master')

    // データが表示されるエリア
    const dataTable = page.locator('[data-testid="data-table"]')

    // RED Phase期待: 実データが表示されない
    const hasRealData = await page.evaluate(() => {
      // Supabaseからの実データ確認
      const rows = document.querySelectorAll('tr[data-supabase="true"]')
      return rows.length > 0
    })

    expect(hasRealData).toBe(false) // 実データはまだ表示されない

    // v0のモックデータは表示される可能性がある
    const hasMockData = await page.evaluate(() => {
      const mockRows = document.querySelectorAll('tr[data-mock="true"]')
      return mockRows.length > 0
    })

    // モックデータの存在は許可（v0実装）
    console.log(`Mock data present: ${hasMockData}`)
  })

  test('🔴 RED: Environment variables should not be exposed', async ({ page }) => {
    // セキュリティテスト: 環境変数が公開されていないことを確認
    const envVarsExposed = await page.evaluate(() => {
      // ブラウザで環境変数が見えていないことを確認
      return !!(
        (window as any).SUPABASE_URL ||
        (window as any).SUPABASE_ANON_KEY ||
        document.body.innerHTML.includes('eyJhbGciOiJIUzI1NiI')
      )
    })

    expect(envVarsExposed).toBe(false) // 環境変数は公開されてはいけない
  })

  test('🔴 RED: Error handling should show user-friendly messages', async ({ page }) => {
    // エラー処理テスト
    await page.click('text=SQLクエリ')

    // 無効なクエリを入力
    const queryInput = page.locator('textarea[placeholder*="SQL"]')
    await queryInput.fill('INVALID SQL QUERY')

    // 実行ボタンをクリック
    await page.click('button:has-text("実行")')

    // エラーメッセージが表示されることを確認
    const errorMessage = page.locator('[data-testid="error-message"]')

    // エラーが適切にハンドリングされることを確認
    await expect(errorMessage).toBeVisible({ timeout: 5000 })

    const errorText = await errorMessage.textContent()
    expect(errorText).not.toContain('undefined')
    expect(errorText).not.toContain('null')
  })
})

test.describe('v0 Original Functionality (Should Work)', () => {
  // v0の既存機能は動作することを確認

  test('✅ v0 SQLite管理画面が正常に表示される', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // タイトル確認
    await expect(page).toHaveTitle(/database/i)

    // メインナビゲーションタブが表示される
    await expect(page.locator('text=SQLクエリ')).toBeVisible()
    await expect(page.locator('text=データ閲覧')).toBeVisible()
    await expect(page.locator('text=テーブル構造')).toBeVisible()
  })

  test('✅ テーブル一覧が表示される（v0モック）', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // サイドバーにテーブル一覧が表示される
    const tablesList = page.locator('[data-testid="tables-list"]')
    await expect(tablesList).toBeVisible()

    // 19テーブルが表示される（v0のモック実装）
    const tableItems = page.locator('.table-item')
    const count = await tableItems.count()
    expect(count).toBeGreaterThan(15) // 少なくとも15以上のテーブル
  })

  test('✅ レスポンシブデザインが機能する', async ({ page }) => {
    // デスクトップサイズ
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('http://localhost:3000')

    await expect(page.locator('[data-testid="main-content"]')).toBeVisible()

    // モバイルサイズ
    await page.setViewportSize({ width: 375, height: 667 })

    // モバイルでもコンテンツが表示される
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible()
  })
})