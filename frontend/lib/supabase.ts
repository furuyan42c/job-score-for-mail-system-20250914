/**
 * T068: v0フロントエンドSupabase統合 - TDD実装
 * Supabaseクライアント設定とユーティリティ
 */

import { createClient } from '@supabase/supabase-js'
import { createClientComponentClient } from '@supabase/ssr'

// Supabase環境変数
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://127.0.0.1:54321'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

// データベーステーブル型定義（20テーブル対応）
export interface Database {
  public: {
    Tables: {
      // Master Tables
      prefecture_master: {
        Row: {
          code: string
          name: string
          region: string | null
          sort_order: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          code: string
          name: string
          region?: string | null
          sort_order?: number | null
        }
        Update: {
          code?: string
          name?: string
          region?: string | null
          sort_order?: number | null
        }
      }
      city_master: {
        Row: {
          code: string
          pref_cd: string
          name: string
          latitude: number | null
          longitude: number | null
          nearby_city_codes: string[] | null
          created_at: string
          updated_at: string
        }
        Insert: {
          code: string
          pref_cd: string
          name: string
          latitude?: number | null
          longitude?: number | null
          nearby_city_codes?: string[] | null
        }
        Update: {
          code?: string
          pref_cd?: string
          name?: string
          latitude?: number | null
          longitude?: number | null
          nearby_city_codes?: string[] | null
        }
      }
      job_data: {
        Row: {
          job_id: number
          endcl_cd: string
          fee: number | null
          hourly_wage: number | null
          application_name: string | null
          employment_type_code: number | null
          prefecture_cd: string | null
          city_cd: string | null
          occupation_code: number | null
          work_place: string | null
          work_content: string | null
          company_name: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          endcl_cd: string
          fee?: number | null
          hourly_wage?: number | null
          application_name?: string | null
          employment_type_code?: number | null
          prefecture_cd?: string | null
          city_cd?: string | null
          occupation_code?: number | null
          work_place?: string | null
          work_content?: string | null
          company_name?: string | null
        }
        Update: {
          endcl_cd?: string
          fee?: number | null
          hourly_wage?: number | null
          application_name?: string | null
          employment_type_code?: number | null
          prefecture_cd?: string | null
          city_cd?: string | null
          occupation_code?: number | null
          work_place?: string | null
          work_content?: string | null
          company_name?: string | null
        }
      }
      // 他の17テーブルは実装時に追加
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

// Supabaseクライアント（クライアントサイド用）
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)

// コンポーネント用クライアント（SSR対応）
export const createSupabaseClient = () =>
  createClientComponentClient<Database>()

// ユーティリティ関数
export const supabaseUtils = {
  /**
   * データベース接続テスト
   */
  async testConnection(): Promise<{ success: boolean; error?: string }> {
    try {
      const { data, error } = await supabase
        .from('prefecture_master')
        .select('count(*)')
        .limit(1)

      if (error) {
        return { success: false, error: error.message }
      }

      return { success: true }
    } catch (err) {
      return {
        success: false,
        error: err instanceof Error ? err.message : 'Unknown error'
      }
    }
  },

  /**
   * テーブル一覧取得（システム確認用）
   */
  async getTableList(): Promise<{ tables: string[]; error?: string }> {
    try {
      const { data, error } = await supabase.rpc('get_table_list')

      if (error) {
        // RPCが利用できない場合の代替手段
        return {
          tables: [],
          error: 'RPC not available, using limited functionality'
        }
      }

      return { tables: data || [] }
    } catch (err) {
      return {
        tables: [],
        error: err instanceof Error ? err.message : 'Unknown error'
      }
    }
  },

  /**
   * SQLクエリ実行（SELECT専用、セキュリティ制限付き）
   * T069 REFACTOR Phase: セキュリティ、パフォーマンス、エラーハンドリング強化
   */
  async executeQuery(
    query: string
  ): Promise<{ data: any[] | null; error?: string; success: boolean; execution_time?: number; query_plan?: any }> {
    const startTime = Date.now()

    try {
      // REFACTOR: 入力検証の強化
      if (!query || typeof query !== 'string') {
        return {
          data: null,
          error: 'Query must be a non-empty string',
          success: false,
          execution_time: Date.now() - startTime
        }
      }

      // REFACTOR: クエリ長の制限（セキュリティ対策）
      if (query.length > 10000) {
        return {
          data: null,
          error: 'Query too long (max 10,000 characters)',
          success: false,
          execution_time: Date.now() - startTime
        }
      }

      // REFACTOR: より厳密なセキュリティチェック
      const trimmedQuery = query.trim().toLowerCase()
      if (!trimmedQuery.startsWith('select')) {
        return {
          data: null,
          error: 'Only SELECT queries are allowed for security reasons',
          success: false,
          execution_time: Date.now() - startTime
        }
      }

      // REFACTOR: 拡張された危険キーワードチェック
      const dangerousKeywords = [
        'drop', 'delete', 'update', 'insert', 'create', 'alter', 'truncate',
        'grant', 'revoke', 'exec', 'execute', 'xp_', 'sp_', 'declare',
        'cursor', 'bulk', 'openrowset', 'opendatasource', 'into outfile',
        'load_file', 'dumpfile'
      ]

      for (const keyword of dangerousKeywords) {
        if (trimmedQuery.includes(keyword)) {
          return {
            data: null,
            error: `Security violation: keyword '${keyword}' is not allowed`,
            success: false,
            execution_time: Date.now() - startTime
          }
        }
      }

      // REFACTOR: SQLインジェクション対策の追加チェック
      const suspiciousPatterns = [
        /union\s+select/i,
        /;\s*drop/i,
        /'\s*or\s*'1'\s*=\s*'1/i,
        /--\s*$/,
        /\/\*[\s\S]*?\*\//,
        /xp_cmdshell/i,
        /';\s*exec/i
      ]

      for (const pattern of suspiciousPatterns) {
        if (pattern.test(query)) {
          return {
            data: null,
            error: 'Security violation: suspicious query pattern detected',
            success: false,
            execution_time: Date.now() - startTime
          }
        }
      }

      // REFACTOR: パフォーマンス監視とタイムアウト設定
      const timeoutMs = 30000 // 30秒タイムアウト
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Query timeout after 30 seconds')), timeoutMs)
      })

      // T069 REFACTOR Phase: より堅牢なSupabase RPC実行
      const queryPromise = supabase.rpc('execute_readonly_sql', {
        sql_query: query
      })

      const { data, error } = await Promise.race([queryPromise, timeoutPromise]) as any

      if (error) {
        // REFACTOR: エラーメッセージの分類と詳細化
        let errorMessage = error.message
        let errorType = 'execution_error'

        if (error.message.includes('permission denied')) {
          errorType = 'permission_error'
          errorMessage = 'Permission denied: insufficient privileges'
        } else if (error.message.includes('does not exist')) {
          errorType = 'table_not_found'
          errorMessage = 'Table or column does not exist'
        } else if (error.message.includes('syntax error')) {
          errorType = 'syntax_error'
          errorMessage = 'SQL syntax error'
        }

        return {
          data: null,
          error: errorMessage,
          success: false,
          execution_time: Date.now() - startTime
        }
      }

      // REFACTOR: 結果セットサイズの制限（パフォーマンス対策）
      const maxRows = 10000
      let resultData = data || []

      if (Array.isArray(resultData) && resultData.length > maxRows) {
        resultData = resultData.slice(0, maxRows)
        console.warn(`Query result truncated to ${maxRows} rows for performance`)
      }

      // REFACTOR: パフォーマンスメトリクス
      const executionTime = Date.now() - startTime
      if (executionTime > 5000) {
        console.warn(`Slow query detected: ${executionTime}ms - Consider optimization`)
      }

      return {
        data: resultData,
        error: undefined,
        success: true,
        execution_time: executionTime
      }

    } catch (err) {
      // REFACTOR: エラーハンドリングの改善
      const executionTime = Date.now() - startTime
      let errorMessage = 'Unknown error occurred'

      if (err instanceof Error) {
        if (err.message.includes('timeout')) {
          errorMessage = 'Query execution timeout - please simplify your query'
        } else if (err.message.includes('network')) {
          errorMessage = 'Network error - please check your connection'
        } else {
          errorMessage = err.message
        }
      }

      return {
        data: null,
        error: errorMessage,
        success: false,
        execution_time: executionTime
      }
    }
  }
}

// エラーハンドリング型
export type SupabaseResponse<T> = {
  data: T | null
  error: string | null
  success: boolean
}

// よく使用されるクエリのヘルパー
export const supabaseQueries = {
  /**
   * 都道府県一覧取得
   */
  async getPrefectures(): Promise<SupabaseResponse<Database['public']['Tables']['prefecture_master']['Row'][]>> {
    try {
      const { data, error } = await supabase
        .from('prefecture_master')
        .select('*')
        .order('sort_order')

      return {
        data,
        error: error?.message || null,
        success: !error
      }
    } catch (err) {
      return {
        data: null,
        error: err instanceof Error ? err.message : 'Unknown error',
        success: false
      }
    }
  },

  /**
   * 求人データ取得（サンプル）
   */
  async getJobs(limit: number = 10): Promise<SupabaseResponse<Database['public']['Tables']['job_data']['Row'][]>> {
    try {
      const { data, error } = await supabase
        .from('job_data')
        .select('*')
        .limit(limit)

      return {
        data,
        error: error?.message || null,
        success: !error
      }
    } catch (err) {
      return {
        data: null,
        error: err instanceof Error ? err.message : 'Unknown error',
        success: false
      }
    }
  }
}

// デフォルトエクスポート
export default supabase