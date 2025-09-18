"use client"

import { useState, useEffect } from "react"
import { supabase, supabaseUtils } from "@/lib/supabase"
import { useRealtimeQuery } from "@/hooks/useRealtimeQuery"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  Database,
  Play,
  Edit,
  Eye,
  Trash2,
  Plus,
  Code,
  TableIcon,
  Settings,
  Activity,
  Bell,
  CheckCircle,
  AlertCircle,
  Zap,
} from "lucide-react"

const databaseTables = [
  { name: "users", rows: 10000, description: "ユーザー情報" },
  { name: "jobs", rows: 100000, description: "求人情報（メインテーブル）" },
  { name: "jobs_match_raw", rows: 100000, description: "求人マッチ生データ" },
  { name: "jobs_contents_raw", rows: 100000, description: "求人コンテンツ生データ" },
  { name: "user_actions", rows: 85000, description: "ユーザーアクション履歴" },
  { name: "daily_email_queue", rows: 30000, description: "日次メール配信キュー" },
  { name: "job_enrichment", rows: 100000, description: "求人エンリッチメント" },
  { name: "user_job_mapping", rows: 400000, description: "ユーザー求人マッピング" },
  { name: "daily_job_picks", rows: 40000, description: "日次求人選定" },
  { name: "user_profiles", rows: 10000, description: "ユーザープロファイル" },
  { name: "keyword_scoring", rows: 5000, description: "キーワードスコアリング" },
  { name: "semrush_keywords", rows: 5000, description: "SEMrushキーワード" },
  { name: "occupation_master", rows: 500, description: "職種マスター" },
  { name: "prefecture_master", rows: 47, description: "都道府県マスター" },
  { name: "city_master", rows: 1741, description: "市区町村マスター" },
  { name: "employment_type_master", rows: 10, description: "雇用形態マスター" },
  { name: "salary_type_master", rows: 5, description: "給与タイプマスター" },
  { name: "feature_master", rows: 200, description: "特徴マスター" },
  { name: "needs_category_master", rows: 14, description: "ニーズカテゴリマスター" },
]

const sampleTableData = {
  users: [
    {
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      email: "user1@example.com",
      age_range: "20-24",
      gender: "男性",
      is_active: true,
      created_at: "2024-01-15 10:30:00+09",
      updated_at: "2024-08-29 14:20:00+09",
    },
    {
      user_id: "550e8400-e29b-41d4-a716-446655440001",
      email: "user2@example.com",
      age_range: "25-29",
      gender: "女性",
      is_active: true,
      created_at: "2024-02-20 14:15:00+09",
      updated_at: "2024-08-29 14:20:00+09",
    },
  ],
  jobs: [
    {
      job_id: 421505257,
      import_from: "giga-baito",
      client_cd: "arubaitoex",
      endcl_cd: "EX00969530",
      application_name: "ちよだ鮨の調理＆販売スタッフ",
      company_name: "ちよだ鮨　笹塚店",
      occupation_cd1: 100,
      min_salary: 1260,
      max_salary: 1400,
      pref_cd: 13,
      city_cd: 13113,
      score: 104983,
      is_delivery: true,
      created_at: "2025-07-04 03:50:20+09",
      updated_at: "2025-07-17 02:40:29+09",
    },
  ],
  jobs_match_raw: [
    {
      job_id: 421505257,
      client_cd: "arubaitoex",
      endcl_cd: "EX00969530",
      occupation_cd1: 100,
      min_salary: 1260,
      max_salary: 1400,
      pref_cd: 13,
      city_cd: 13113,
      score: 104983,
      is_delivery: true,
      created_at: "2025-07-04 03:50:20+09",
      updated_at: "2025-07-17 02:40:29+09",
    },
  ],
  jobs_contents_raw: [
    {
      job_id: 421505257,
      application_name: "＜「ちよだ鮨」の調理＆販売スタッフ♪＞丁寧な研修あり×未経験でも安心スタート★",
      company_name: "ちよだ鮨　笹塚店",
      salary: "時給1260円～（月払い）",
      hours: "シフト1：08:00～13:00 シフト2：13:00～17:00",
      endcl_name: "ちよだ鮨　笹塚店",
    },
  ],
  user_actions: [
    {
      action_id: "123e4567-e89b-12d3-a456-426614174000",
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      job_id: 421505257,
      action_type: "applied",
      source_type: "email",
      pref_cd: 13,
      city_cd: 13113,
      occupation_cd1: 100,
      min_salary: 1260,
      max_salary: 1400,
      action_date: "2024-08-20 16:45:00+09",
    },
  ],
  daily_email_queue: [
    {
      queue_id: "abc12345-e89b-12d3-a456-426614174000",
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      delivery_date: "2024-08-29",
      user_name: "直己",
      user_location: "東京都小金井市",
      email_subject: "📧 ゲットバイト通信　2025年7月15日号",
      total_job_count: 40,
      delivery_status: "sent",
      scheduled_at: "2024-08-29 06:00:00+09",
      sent_at: "2024-08-29 06:00:15+09",
      created_at: "2024-08-29 03:00:00+09",
    },
  ],
  job_enrichment: [
    {
      job_id: 421505257,
      score: 104983,
      occupation_category: "100",
      jobtype_detail: 5,
      updated_at: "2024-08-29 02:00:00+09",
    },
  ],
  user_job_mapping: [
    {
      mapping_id: "def45678-e89b-12d3-a456-426614174000",
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      job_id: 421505257,
      mapping_date: "2024-08-29",
      personalized_score: 125000,
      rank_in_user: 1,
      is_selected: true,
      selection_reason: "high_score_match",
      created_at: "2024-08-29 03:00:00+09",
    },
  ],
  daily_job_picks: [
    {
      pick_id: "789e0123-e89b-12d3-a456-426614174000",
      job_id: 421505257,
      pick_date: "2024-08-29",
      client_cd: "arubaitoex",
      application_name: "＜「ちよだ鮨」の調理＆販売スタッフ♪＞",
      company_name: "ちよだ鮨　笹塚店",
      salary: "時給1260円～（月払い）",
      pref_cd: 13,
      city_cd: 13113,
      needs_category: "日払い・週払い",
      occupation_category: "100",
      job_score: 104983,
      email_title: "【夕方4hで7,400円】駅ナカベーカリー品出し",
      created_at: "2024-08-29 03:00:00+09",
    },
  ],
  user_profiles: [
    {
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      applied_pref_cds: "13:5,14:3,11:1",
      applied_city_cds: "13113:3,13104:2,14101:1",
      applied_occupation_cd1s: "1:5,2:2,5:1",
      total_applications: 8,
      avg_applied_score: 98450.5,
      first_application_at: "2024-02-10 09:15:00+09",
      last_application_at: "2024-08-20 16:45:00+09",
      created_at: "2024-02-10 09:15:00+09",
    },
  ],
  keyword_scoring: [
    {
      scoring_id: 1,
      keyword_id: 1,
      processed_keyword: "コンビニバイト",
      base_score: 100,
      weight_factor: 1.5,
      llm_analysis: "高需要・低競争キーワード",
      processed_at: "2024-08-29 01:00:00+09",
    },
  ],
  semrush_keywords: [
    {
      keyword_id: 1,
      keyword: "コンビニ バイト",
      intent: "Commercial",
      volume: 12000,
      keyword_difficulty: 45.2,
      cpc_usd: 0.85,
      potential_traffic: 397,
      imported_at: "2024-08-24 10:00:00+09",
    },
  ],
  occupation_master: [
    {
      occupation_cd1: 1,
      occupation_cd2: 1,
      occupation_cd3: 1,
      occupation_name: "飲食・フード系",
      jobtype_detail: 5,
      jobtype_detail_name: "ホールスタッフ",
    },
  ],
  prefecture_master: [
    {
      pref_cd: 13,
      url_segment: "tokyo",
      name: "東京都",
      region: "関東",
      category_id: 38,
    },
  ],
  city_master: [
    {
      city_cd: 13113,
      pref_cd: 13,
      pref_name: "東京都",
      name: "渋谷区",
      kana: "しぶやく",
      latitude: 35.658517,
      longitude: 139.701334,
      is_conflicted_name: false,
      is_special_city: false,
    },
  ],
  employment_type_master: [
    {
      employment_type_cd: 1,
      group_cd: "parttime",
      json_ld_type: "PART_TIME",
      name: "アルバイト",
    },
  ],
  salary_type_master: [
    {
      salary_type_cd: 1,
      json_ld_type: "HOUR",
      name: "時給",
    },
  ],
  feature_master: [
    {
      feature_cd: 100,
      name: "学歴不問",
      group_name: "〜な人歓迎",
      is_enabled: true,
      match_keywords: "学歴",
      ng_keywords: "学歴必須",
    },
  ],
  needs_category_master: [
    {
      category_id: 1,
      category_name: "日払い・週払い",
      matching_type: "keyword",
      matching_value: "日払い,週払い",
      priority: 1,
      created_at: "2024-01-01 00:00:00+09",
    },
  ],
}

export default function DatabaseAdmin() {
  const [selectedTable, setSelectedTable] = useState("users")
  const [sqlQuery, setSqlQuery] = useState("SELECT * FROM users LIMIT 10;")
  const [searchTerm, setSearchTerm] = useState("")
  const [queryResult, setQueryResult] = useState<any[]>([])
  const [isQueryRunning, setIsQueryRunning] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [supabaseConnected, setSupabaseConnected] = useState(false)
  const [realtimeEnabled, setRealtimeEnabled] = useState(true)
  const [realtimeNotifications, setRealtimeNotifications] = useState<Array<{
    id: string
    type: 'INSERT' | 'UPDATE' | 'DELETE'
    table: string
    timestamp: Date
    data?: any
  }>>([])
  // T069 REFACTOR: パフォーマンス監視とクエリ履歴
  const [queryHistory, setQueryHistory] = useState<Array<{query: string, timestamp: Date, execution_time: number, status: 'success' | 'error'}>>([])
  const [lastExecutionTime, setLastExecutionTime] = useState<number>(0)
  const [queryStats, setQueryStats] = useState<{total: number, successful: number, failed: number}>({total: 0, successful: 0, failed: 0})

  // T070: リアルタイム機能統合 - Real-time subscription
  const {
    data: realtimeData,
    loading: realtimeLoading,
    error: realtimeError,
    isSubscribed,
    refetch: refetchRealtimeData,
    stats: realtimeStats
  } = useRealtimeQuery({
    table: selectedTable,
    enabled: realtimeEnabled && supabaseConnected,
    onInsert: (payload) => {
      console.log('Real-time INSERT detected:', payload)
      setRealtimeNotifications(prev => [
        {
          id: `${Date.now()}_insert`,
          type: 'INSERT',
          table: selectedTable,
          timestamp: new Date(),
          data: payload
        },
        ...prev.slice(0, 9) // Keep last 10 notifications
      ])
    },
    onUpdate: (payload) => {
      console.log('Real-time UPDATE detected:', payload)
      setRealtimeNotifications(prev => [
        {
          id: `${Date.now()}_update`,
          type: 'UPDATE',
          table: selectedTable,
          timestamp: new Date(),
          data: payload
        },
        ...prev.slice(0, 9)
      ])
    },
    onDelete: (payload) => {
      console.log('Real-time DELETE detected:', payload)
      setRealtimeNotifications(prev => [
        {
          id: `${Date.now()}_delete`,
          type: 'DELETE',
          table: selectedTable,
          timestamp: new Date(),
          data: payload
        },
        ...prev.slice(0, 9)
      ])
    },
    onError: (error) => {
      console.error('Real-time subscription error:', error)
      setErrorMessage(`Real-time error: ${error.message}`)
    }
  })

  // T068: Supabase統合 - E2Eテスト用のwindow.supabaseを設定
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).supabase = supabase;
    }

    // Supabase接続テスト
    const testConnection = async () => {
      const result = await supabaseUtils.testConnection();
      setSupabaseConnected(result.success);
      if (!result.success) {
        setErrorMessage(result.error || "Supabase connection failed");
      }
    };

    testConnection();
  }, [])

  const executeQuery = async () => {
    setIsQueryRunning(true)
    setErrorMessage("")

    try {
      // T069 REFACTOR Phase: 強化されたクエリ実行と監視
      const result = await supabaseUtils.executeQuery(sqlQuery)

      // クエリ統計の更新
      setQueryStats(prev => ({
        total: prev.total + 1,
        successful: result.success ? prev.successful + 1 : prev.successful,
        failed: result.success ? prev.failed : prev.failed + 1
      }))

      // クエリ履歴の記録
      setQueryHistory(prev => [
        {
          query: sqlQuery,
          timestamp: new Date(),
          execution_time: result.execution_time || 0,
          status: result.success ? 'success' : 'error'
        },
        ...prev.slice(0, 9) // 最新10件を保持
      ])

      setLastExecutionTime(result.execution_time || 0)

      if (!result.success) {
        throw new Error(result.error || "クエリ実行エラー")
      }

      setQueryResult(result.data || [])

      // REFACTOR: パフォーマンス警告
      if (result.execution_time && result.execution_time > 5000) {
        console.warn(`Slow query detected: ${result.execution_time}ms`)
      }

      setIsQueryRunning(false)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "クエリ実行エラー"
      setErrorMessage(errorMsg)
      setQueryResult([])
      setIsQueryRunning(false)

      // エラーも履歴に記録
      setQueryHistory(prev => [
        {
          query: sqlQuery,
          timestamp: new Date(),
          execution_time: 0,
          status: 'error'
        },
        ...prev.slice(0, 9)
      ])
    }
  }

  const getTableColumns = (tableName: string) => {
    const columnMap: Record<string, string[]> = {
      users: ["user_id", "email", "age_range", "gender", "is_active", "created_at", "updated_at"],
      jobs: [
        "job_id",
        "import_from",
        "client_cd",
        "endcl_cd",
        "application_name",
        "company_name",
        "occupation_cd1",
        "min_salary",
        "max_salary",
        "pref_cd",
        "city_cd",
        "score",
        "is_delivery",
        "created_at",
        "updated_at",
      ],
      jobs_match_raw: [
        "job_id",
        "client_cd",
        "endcl_cd",
        "occupation_cd1",
        "min_salary",
        "max_salary",
        "pref_cd",
        "city_cd",
        "score",
        "is_delivery",
        "created_at",
        "updated_at",
      ],
      jobs_contents_raw: ["job_id", "application_name", "company_name", "salary", "hours", "endcl_name"],
      user_actions: [
        "action_id",
        "user_id",
        "job_id",
        "action_type",
        "source_type",
        "pref_cd",
        "city_cd",
        "occupation_cd1",
        "min_salary",
        "max_salary",
        "action_date",
      ],
      daily_email_queue: [
        "queue_id",
        "user_id",
        "delivery_date",
        "user_name",
        "user_location",
        "email_subject",
        "total_job_count",
        "delivery_status",
        "scheduled_at",
        "sent_at",
        "created_at",
      ],
      job_enrichment: ["job_id", "score", "occupation_category", "jobtype_detail", "updated_at"],
      user_job_mapping: [
        "mapping_id",
        "user_id",
        "job_id",
        "mapping_date",
        "personalized_score",
        "rank_in_user",
        "is_selected",
        "selection_reason",
        "created_at",
      ],
      daily_job_picks: [
        "pick_id",
        "job_id",
        "pick_date",
        "client_cd",
        "application_name",
        "company_name",
        "salary",
        "pref_cd",
        "city_cd",
        "needs_category",
        "occupation_category",
        "job_score",
        "email_title",
        "created_at",
      ],
      user_profiles: [
        "user_id",
        "applied_pref_cds",
        "applied_city_cds",
        "applied_occupation_cd1s",
        "total_applications",
        "avg_applied_score",
        "first_application_at",
        "last_application_at",
        "created_at",
      ],
      keyword_scoring: [
        "scoring_id",
        "keyword_id",
        "processed_keyword",
        "base_score",
        "weight_factor",
        "llm_analysis",
        "processed_at",
      ],
      semrush_keywords: [
        "keyword_id",
        "keyword",
        "intent",
        "volume",
        "keyword_difficulty",
        "cpc_usd",
        "potential_traffic",
        "imported_at",
      ],
      occupation_master: [
        "occupation_cd1",
        "occupation_cd2",
        "occupation_cd3",
        "occupation_name",
        "jobtype_detail",
        "jobtype_detail_name",
      ],
      prefecture_master: ["pref_cd", "url_segment", "name", "region", "category_id"],
      city_master: [
        "city_cd",
        "pref_cd",
        "pref_name",
        "name",
        "kana",
        "latitude",
        "longitude",
        "is_conflicted_name",
        "is_special_city",
      ],
      employment_type_master: ["employment_type_cd", "group_cd", "json_ld_type", "name"],
      salary_type_master: ["salary_type_cd", "json_ld_type", "name"],
      feature_master: ["feature_cd", "name", "group_name", "is_enabled", "match_keywords", "ng_keywords"],
      needs_category_master: [
        "category_id",
        "category_name",
        "matching_type",
        "matching_value",
        "priority",
        "created_at",
      ],
    }
    return columnMap[tableName] || []
  }

  const filteredTables = databaseTables.filter(
    (table) => table.name.toLowerCase().includes(searchTerm.toLowerCase()) || table.description.includes(searchTerm),
  )

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Database className="h-8 w-8 text-primary" />
            <h1 className="text-xl font-bold text-foreground">メールスコアリングシステム - データベース管理ツール</h1>
            <Badge variant="outline">SQLite風</Badge>
          </div>
          <div className="flex items-center gap-2">
            {/* T070: Real-time status indicator */}
            <div className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-md">
              {isSubscribed ? (
                <>
                  <Activity className="h-4 w-4 text-green-500 animate-pulse" />
                  <span className="text-sm text-green-600">リアルタイム接続中</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">オフライン</span>
                </>
              )}
            </div>
            {/* Real-time stats */}
            {realtimeStats && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>INSERT: {realtimeStats.inserts}</span>
                <span>UPDATE: {realtimeStats.updates}</span>
                <span>DELETE: {realtimeStats.deletes}</span>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRealtimeEnabled(!realtimeEnabled)}
            >
              <Zap className={`h-4 w-4 mr-2 ${realtimeEnabled ? 'text-yellow-500' : ''}`} />
              {realtimeEnabled ? 'リアルタイム無効化' : 'リアルタイム有効化'}
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              接続更新
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              スキーマ出力
            </Button>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)]">
        <div className="w-80 border-r border-border bg-card">
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="テーブル検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>

          <ScrollArea className="h-[calc(100vh-8rem)]">
            <div className="p-2">
              <div className="mb-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-2 px-2">
                  データベーステーブル ({databaseTables.length})
                </h3>
                <div className="space-y-1" data-testid="tables-list">
                  {filteredTables.map((table) => (
                    <Button
                      key={table.name}
                      variant={selectedTable === table.name ? "secondary" : "ghost"}
                      className="w-full justify-start h-auto p-3 table-item"
                      onClick={() => {
                        setSelectedTable(table.name)
                        setSqlQuery(`SELECT * FROM ${table.name} LIMIT 10;`)
                      }}
                    >
                      <div className="flex items-center gap-2 w-full">
                        <TableIcon className="h-4 w-4" />
                        <div className="text-left flex-1">
                          <div className="font-medium">{table.name}</div>
                          <div className="text-xs text-muted-foreground">{table.description}</div>
                          <div className="text-xs text-muted-foreground">{table.rows.toLocaleString()} 行</div>
                        </div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>

        <div className="flex-1 flex flex-col" data-testid="main-content">
          <Tabs defaultValue="query" className="flex-1 flex flex-col">
            <div className="border-b border-border bg-card px-4">
              <TabsList className="grid w-full max-w-lg grid-cols-4">
                <TabsTrigger value="query">SQLクエリ</TabsTrigger>
                <TabsTrigger value="browse">データ閲覧</TabsTrigger>
                <TabsTrigger value="structure">テーブル構造</TabsTrigger>
                <TabsTrigger value="realtime">
                  <div className="flex items-center gap-1">
                    <Bell className="h-3 w-3" />
                    リアルタイム
                    {realtimeNotifications.length > 0 && (
                      <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 text-xs">
                        {realtimeNotifications.length}
                      </Badge>
                    )}
                  </div>
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="query" className="flex-1 flex flex-col m-0">
              <div className="p-4 border-b border-border bg-muted/30">
                <div className="flex items-center gap-2 mb-2">
                  <Code className="h-4 w-4" />
                  <span className="text-sm font-medium">クエリエディタ</span>
                  <Badge variant="outline" className="text-xs">
                    テーブル: {selectedTable}
                  </Badge>
                </div>
                <Textarea
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                  placeholder="SQL Query Editor - SELECT * FROM users WHERE is_active = true;"
                  className="min-h-[120px] font-mono text-sm"
                />
                <div className="flex items-center gap-2 mt-2">
                  <Button onClick={executeQuery} disabled={isQueryRunning} size="sm">
                    <Play className="h-4 w-4 mr-2" />
                    {isQueryRunning ? "実行中..." : "クエリ実行"}
                  </Button>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    実行計画
                  </Button>
                  <div className="text-xs text-muted-foreground ml-auto">Ctrl+Enter で実行</div>
                </div>

                {/* T069 REFACTOR: パフォーマンス監視とクエリ統計 */}
                {(lastExecutionTime > 0 || queryStats.total > 0) && (
                  <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-4">
                        <span className="text-blue-700">
                          実行時間: <strong>{lastExecutionTime}ms</strong>
                        </span>
                        {lastExecutionTime > 1000 && (
                          <Badge variant="secondary" className="text-orange-700 bg-orange-100">
                            遅いクエリ
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-blue-600">
                        <span>総実行: {queryStats.total}</span>
                        <span className="text-green-600">成功: {queryStats.successful}</span>
                        <span className="text-red-600">失敗: {queryStats.failed}</span>
                      </div>
                    </div>
                  </div>
                )}

                {errorMessage && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm" data-testid="error-message">
                    {errorMessage}
                  </div>
                )}
              </div>

              <div className="flex-1 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium">クエリ結果</h3>
                  {queryResult.length > 0 && <Badge variant="secondary">{queryResult.length} 行</Badge>}
                </div>

                <div data-testid="query-result">
                  {queryResult.length > 0 ? (
                    <div className="border border-border rounded-lg overflow-hidden">
                      <ScrollArea className="h-[400px]">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {Object.keys(queryResult[0]).map((column) => (
                                <TableHead key={column} className="font-mono text-xs">
                                  {column}
                                </TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {queryResult.map((row, index) => (
                              <TableRow key={index}>
                                {Object.values(row).map((value, cellIndex) => (
                                  <TableCell key={cellIndex} className="font-mono text-xs max-w-xs truncate">
                                    {typeof value === "boolean" ? (
                                      <Badge variant={value ? "default" : "secondary"}>{value ? "true" : "false"}</Badge>
                                    ) : typeof value === "string" && value.includes("-") && value.length > 10 ? (
                                      <span className="text-muted-foreground">{value}</span>
                                    ) : (
                                      String(value)
                                    )}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </ScrollArea>
                    </div>
                  ) : (
                    <div className="border border-dashed border-border rounded-lg p-8 text-center">
                      <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">SQL execution 実装予定 (T069 not implemented yet)</p>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="browse" className="flex-1 m-0 p-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">テーブル: {selectedTable}</h3>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      新規追加
                    </Button>
                    <Button variant="outline" size="sm">
                      <Filter className="h-4 w-4 mr-2" />
                      フィルター
                    </Button>
                  </div>
                </div>

                <div className="border border-border rounded-lg overflow-hidden">
                  <ScrollArea className="h-[500px]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12">#</TableHead>
                          {getTableColumns(selectedTable).map((column) => (
                            <TableHead key={column} className="font-mono text-xs">
                              {column}
                            </TableHead>
                          ))}
                          <TableHead className="w-24">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(sampleTableData[selectedTable as keyof typeof sampleTableData] || []).map((row, index) => (
                          <TableRow key={index} data-mock="true">
                            <TableCell className="text-muted-foreground">{index + 1}</TableCell>
                            {Object.values(row).map((value, cellIndex) => (
                              <TableCell key={cellIndex} className="font-mono text-xs max-w-xs truncate">
                                {typeof value === "boolean" ? (
                                  <Badge variant={value ? "default" : "secondary"}>{value ? "true" : "false"}</Badge>
                                ) : (
                                  String(value)
                                )}
                              </TableCell>
                            ))}
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Button variant="ghost" size="sm">
                                  <Edit className="h-3 w-3" />
                                </Button>
                                <Button variant="ghost" size="sm">
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="structure" className="flex-1 m-0 p-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">テーブル構造: {selectedTable}</h3>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-2" />
                    スキーマ編集
                  </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">カラム情報</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {getTableColumns(selectedTable).map((column, index) => (
                          <div
                            key={column}
                            className="flex items-center justify-between p-2 border border-border rounded"
                          >
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                {index === 0 ? "PK" : ""}
                              </Badge>
                              <span className="font-mono text-sm">{column}</span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {column.includes("id")
                                ? "UUID/BIGINT"
                                : column.includes("date") || column.includes("at")
                                  ? "TIMESTAMP"
                                  : column.includes("is_")
                                    ? "BOOLEAN"
                                    : column.includes("count") || column.includes("score") || column.includes("salary")
                                      ? "INTEGER"
                                      : "TEXT"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">テーブル統計</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm">総行数</span>
                          <span className="font-mono text-sm">
                            {databaseTables.find((t) => t.name === selectedTable)?.rows.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm">カラム数</span>
                          <span className="font-mono text-sm">{getTableColumns(selectedTable).length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm">インデックス</span>
                          <span className="font-mono text-sm">3</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm">最終更新</span>
                          <span className="font-mono text-sm">2024-08-29</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* T070: Real-time notifications tab */}
            <TabsContent value="realtime" className="flex-1 m-0 p-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">リアルタイム更新通知</h3>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setRealtimeNotifications([])}
                      disabled={realtimeNotifications.length === 0}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      通知クリア
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {/* Real-time connection status card */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        接続ステータス
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">現在のテーブル</span>
                          <Badge>{selectedTable}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">サブスクリプション状態</span>
                          <Badge variant={isSubscribed ? "default" : "secondary"}>
                            {isSubscribed ? '接続中' : '切断'}
                          </Badge>
                        </div>
                        {realtimeStats && (
                          <>
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-muted-foreground">INSERTイベント</span>
                              <span className="font-mono">{realtimeStats.inserts}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-muted-foreground">UPDATEイベント</span>
                              <span className="font-mono">{realtimeStats.updates}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-muted-foreground">DELETEイベント</span>
                              <span className="font-mono">{realtimeStats.deletes}</span>
                            </div>
                            {realtimeStats.lastUpdate && (
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">最終更新</span>
                                <span className="font-mono text-xs">
                                  {new Date(realtimeStats.lastUpdate).toLocaleTimeString('ja-JP')}
                                </span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Notifications list */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Bell className="h-5 w-5" />
                        リアルタイム通知
                        {realtimeNotifications.length > 0 && (
                          <Badge variant="secondary">{realtimeNotifications.length}</Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {realtimeNotifications.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <Bell className="h-12 w-12 mx-auto mb-3 opacity-30" />
                          <p className="text-sm">まだリアルタイム更新はありません</p>
                          <p className="text-xs mt-2">データベースへの変更がここに表示されます</p>
                        </div>
                      ) : (
                        <ScrollArea className="h-[400px]">
                          <div className="space-y-2">
                            {realtimeNotifications.map((notification) => (
                              <div
                                key={notification.id}
                                className="p-3 border border-border rounded-md hover:bg-muted/50 transition-colors"
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    {notification.type === 'INSERT' && (
                                      <Plus className="h-4 w-4 text-green-500" />
                                    )}
                                    {notification.type === 'UPDATE' && (
                                      <Edit className="h-4 w-4 text-blue-500" />
                                    )}
                                    {notification.type === 'DELETE' && (
                                      <Trash2 className="h-4 w-4 text-red-500" />
                                    )}
                                    <Badge
                                      variant={
                                        notification.type === 'INSERT'
                                          ? 'default'
                                          : notification.type === 'UPDATE'
                                          ? 'secondary'
                                          : 'destructive'
                                      }
                                    >
                                      {notification.type}
                                    </Badge>
                                    <span className="text-sm font-medium">
                                      {notification.table}
                                    </span>
                                  </div>
                                  <span className="text-xs text-muted-foreground">
                                    {notification.timestamp.toLocaleTimeString('ja-JP')}
                                  </span>
                                </div>
                                {notification.data && (
                                  <div className="text-xs font-mono bg-muted p-2 rounded">
                                    {JSON.stringify(notification.data, null, 2).slice(0, 200)}
                                    {JSON.stringify(notification.data).length > 200 && '...'}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
