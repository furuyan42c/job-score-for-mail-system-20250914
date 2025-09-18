"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Play,
  Save,
  FolderOpen,
  History,
  Share,
  Download,
  RefreshCw,
  Maximize,
  Minimize,
  Database,
  Code,
  Clock,
  Users,
  BarChart3,
  Search,
  FileCode,
  AlertTriangle,
  CheckCircle,
  Copy,
  BookOpen,
  Sun,
  Moon,
  Shield,
} from "lucide-react"

// Template queries for common operations
const templateQueries = [
  {
    category: "User Analytics",
    queries: [
      {
        name: "User Activity Summary",
        description: "Users with application counts and activity metrics",
        sql: `SELECT
  u.user_id,
  u.email,
  u.age_range,
  u.gender,
  up.total_applications,
  up.avg_applied_score,
  up.first_application_at,
  up.last_application_at
FROM users u
LEFT JOIN user_profiles up ON u.user_id = up.user_id
WHERE u.is_active = true
ORDER BY up.total_applications DESC
LIMIT 50;`
      },
      {
        name: "New User Registration Trends",
        description: "Daily new user registrations in the last 30 days",
        sql: `SELECT
  DATE(created_at) as registration_date,
  COUNT(*) as new_users,
  COUNT(CASE WHEN gender = '男性' THEN 1 END) as male_users,
  COUNT(CASE WHEN gender = '女性' THEN 1 END) as female_users
FROM users
WHERE created_at >= NOW() - INTERVAL 30 DAY
GROUP BY DATE(created_at)
ORDER BY registration_date DESC;`
      }
    ]
  },
  {
    category: "Job Performance",
    queries: [
      {
        name: "Top Performing Jobs",
        description: "Jobs with highest application rates and scores",
        sql: `SELECT
  j.job_id,
  j.application_name,
  j.company_name,
  j.score,
  COUNT(ua.action_id) as application_count,
  AVG(ujm.personalized_score) as avg_personalized_score
FROM jobs j
LEFT JOIN user_actions ua ON j.job_id = ua.job_id
  AND ua.action_type = 'applied'
LEFT JOIN user_job_mapping ujm ON j.job_id = ujm.job_id
WHERE j.is_delivery = true
GROUP BY j.job_id, j.application_name, j.company_name, j.score
HAVING application_count > 0
ORDER BY application_count DESC, j.score DESC
LIMIT 25;`
      },
      {
        name: "Job Category Analysis",
        description: "Performance metrics by occupation category",
        sql: `SELECT
  om.occupation_name,
  COUNT(DISTINCT j.job_id) as total_jobs,
  COUNT(DISTINCT ua.action_id) as total_applications,
  ROUND(COUNT(DISTINCT ua.action_id) * 100.0 / COUNT(DISTINCT j.job_id), 2) as application_rate,
  AVG(j.score) as avg_job_score
FROM jobs j
JOIN occupation_master om ON j.occupation_cd1 = om.occupation_cd1
LEFT JOIN user_actions ua ON j.job_id = ua.job_id
  AND ua.action_type = 'applied'
GROUP BY om.occupation_name, om.occupation_cd1
ORDER BY application_rate DESC;`
      }
    ]
  },
  {
    category: "Email Campaign",
    queries: [
      {
        name: "Email Delivery Status",
        description: "Daily email queue delivery status and metrics",
        sql: `SELECT
  delivery_date,
  delivery_status,
  COUNT(*) as email_count,
  AVG(total_job_count) as avg_jobs_per_email,
  MIN(total_job_count) as min_jobs,
  MAX(total_job_count) as max_jobs
FROM daily_email_queue
WHERE delivery_date >= CURRENT_DATE - INTERVAL 7 DAY
GROUP BY delivery_date, delivery_status
ORDER BY delivery_date DESC, delivery_status;`
      },
      {
        name: "Email Performance by Location",
        description: "Email engagement metrics by user location",
        sql: `SELECT
  pm.name as prefecture,
  COUNT(DISTINCT deq.user_id) as users_count,
  COUNT(deq.queue_id) as emails_sent,
  COUNT(CASE WHEN deq.delivery_status = 'sent' THEN 1 END) as delivered_count,
  ROUND(COUNT(CASE WHEN deq.delivery_status = 'sent' THEN 1 END) * 100.0 / COUNT(deq.queue_id), 2) as delivery_rate
FROM daily_email_queue deq
JOIN users u ON deq.user_id = u.user_id
JOIN user_actions ua ON u.user_id = ua.user_id
JOIN prefecture_master pm ON ua.pref_cd = pm.pref_cd
WHERE deq.delivery_date >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY pm.pref_cd, pm.name
HAVING users_count >= 10
ORDER BY delivery_rate DESC;`
      }
    ]
  },
  {
    category: "Matching Analytics",
    queries: [
      {
        name: "User-Job Matching Success",
        description: "Analysis of matching algorithm performance",
        sql: `SELECT
  mapping_date,
  COUNT(*) as total_mappings,
  COUNT(CASE WHEN is_selected = true THEN 1 END) as selected_mappings,
  ROUND(COUNT(CASE WHEN is_selected = true THEN 1 END) * 100.0 / COUNT(*), 2) as selection_rate,
  AVG(personalized_score) as avg_score,
  AVG(CASE WHEN is_selected = true THEN personalized_score END) as avg_selected_score
FROM user_job_mapping
WHERE mapping_date >= CURRENT_DATE - INTERVAL 14 DAY
GROUP BY mapping_date
ORDER BY mapping_date DESC;`
      },
      {
        name: "Keyword Scoring Effectiveness",
        description: "Performance analysis of keyword scoring system",
        sql: `SELECT
  ks.processed_keyword,
  ks.base_score,
  ks.weight_factor,
  sk.volume as search_volume,
  sk.keyword_difficulty,
  COUNT(DISTINCT djp.job_id) as jobs_using_keyword
FROM keyword_scoring ks
LEFT JOIN semrush_keywords sk ON ks.keyword_id = sk.keyword_id
LEFT JOIN daily_job_picks djp ON ks.processed_keyword = djp.needs_category
GROUP BY ks.scoring_id, ks.processed_keyword, ks.base_score, ks.weight_factor, sk.volume, sk.keyword_difficulty
HAVING jobs_using_keyword > 0
ORDER BY ks.base_score * ks.weight_factor DESC;`
      }
    ]
  }
]

// Sample data for demonstration
const sampleQueryResults = [
  {
    user_id: "550e8400-e29b-41d4-a716-446655440000",
    email: "user1@example.com",
    age_range: "25-29",
    gender: "女性",
    total_applications: 15,
    avg_applied_score: 98450.5,
    first_application_at: "2024-02-10 09:15:00+09",
    last_application_at: "2024-08-20 16:45:00+09"
  },
  {
    user_id: "550e8400-e29b-41d4-a716-446655440001",
    email: "user2@example.com",
    age_range: "20-24",
    gender: "男性",
    total_applications: 8,
    avg_applied_score: 87234.2,
    first_application_at: "2024-03-15 14:20:00+09",
    last_application_at: "2024-08-18 11:30:00+09"
  }
]

interface QueryHistory {
  id: string
  name?: string
  sql: string
  timestamp: Date
  executionTime?: number
  rowCount?: number
}

interface SavedQuery {
  id: string
  name: string
  sql: string
  createdAt: Date
  lastModified: Date
}

export default function SQLConsolePage() {
  const [query, setQuery] = useState("-- Select a template query or write your own SQL\nSELECT * FROM users WHERE is_active = true LIMIT 10;")
  const [queryResults, setQueryResults] = useState<any[]>([])
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionTime, setExecutionTime] = useState<number | null>(null)
  const [rowCount, setRowCount] = useState<number | null>(null)
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([])
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isDarkTheme, setIsDarkTheme] = useState(false)
  const [searchHistory, setSearchHistory] = useState("")
  const [saveQueryName, setSaveQueryName] = useState("")
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Simulate query execution
  const executeQuery = async () => {
    if (!query.trim()) return

    // Basic SQL injection prevention - only allow SELECT statements
    const trimmedQuery = query.trim().toUpperCase()
    if (!trimmedQuery.startsWith('SELECT')) {
      alert('セキュリティ上の理由により、SELECT文のみ実行可能です。')
      return
    }

    setIsExecuting(true)
    const startTime = Date.now()

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

      // Simulate results
      const results = sampleQueryResults
      setQueryResults(results)
      setRowCount(results.length)

      const endTime = Date.now()
      const execTime = endTime - startTime
      setExecutionTime(execTime)

      // Add to history
      const historyEntry: QueryHistory = {
        id: Date.now().toString(),
        sql: query,
        timestamp: new Date(),
        executionTime: execTime,
        rowCount: results.length
      }
      setQueryHistory(prev => [historyEntry, ...prev.slice(0, 99)]) // Keep last 100

    } catch (error) {
      console.error('Query execution failed:', error)
      alert('クエリの実行に失敗しました。')
    } finally {
      setIsExecuting(false)
    }
  }

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault()
        executeQuery()
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        setShowSaveDialog(true)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [query])

  // Save query
  const saveQuery = () => {
    if (!saveQueryName.trim() || !query.trim()) return

    const savedQuery: SavedQuery = {
      id: Date.now().toString(),
      name: saveQueryName,
      sql: query,
      createdAt: new Date(),
      lastModified: new Date()
    }

    setSavedQueries(prev => [savedQuery, ...prev])
    setSaveQueryName("")
    setShowSaveDialog(false)
  }

  // Load template query
  const loadTemplateQuery = (templateQuery: { sql: string; name: string }) => {
    setQuery(templateQuery.sql)
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }

  // Load saved query
  const loadSavedQuery = (savedQuery: SavedQuery) => {
    setQuery(savedQuery.sql)
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }

  // Copy to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  // Export results as CSV
  const exportResults = () => {
    if (queryResults.length === 0) return

    const headers = Object.keys(queryResults[0])
    const csv = [
      headers.join(','),
      ...queryResults.map(row =>
        headers.map(header => `"${row[header]}"`).join(',')
      )
    ].join('\\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `query_results_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filteredHistory = queryHistory.filter(item =>
    item.sql.toLowerCase().includes(searchHistory.toLowerCase()) ||
    (item.name && item.name.toLowerCase().includes(searchHistory.toLowerCase()))
  )

  return (
    <div className={`h-screen flex flex-col ${isFullscreen ? 'fixed inset-0 z-50' : ''} ${isDarkTheme ? 'dark' : ''}`}>
      {/* Header */}
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Database className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold">SQL Console</h1>
            <Badge variant="outline" className="text-xs">
              <Shield className="h-3 w-3 mr-1" />
              Read-Only
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            {/* Template Queries Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <BookOpen className="h-4 w-4 mr-2" />
                  テンプレート
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-80">
                <DropdownMenuLabel>クエリテンプレート</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {templateQueries.map((category) => (
                  <div key={category.category}>
                    <DropdownMenuLabel className="text-xs text-muted-foreground">
                      {category.category}
                    </DropdownMenuLabel>
                    {category.queries.map((template) => (
                      <DropdownMenuItem
                        key={template.name}
                        onClick={() => loadTemplateQuery(template)}
                        className="flex flex-col items-start p-3"
                      >
                        <div className="font-medium text-sm">{template.name}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {template.description}
                        </div>
                      </DropdownMenuItem>
                    ))}
                    <DropdownMenuSeparator />
                  </div>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Saved Queries */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <FolderOpen className="h-4 w-4 mr-2" />
                  保存済み ({savedQueries.length})
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-64">
                <DropdownMenuLabel>保存済みクエリ</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {savedQueries.length === 0 ? (
                  <div className="p-3 text-sm text-muted-foreground">
                    保存済みクエリがありません
                  </div>
                ) : (
                  savedQueries.map((saved) => (
                    <DropdownMenuItem
                      key={saved.id}
                      onClick={() => loadSavedQuery(saved)}
                      className="flex flex-col items-start p-3"
                    >
                      <div className="font-medium text-sm">{saved.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {saved.createdAt.toLocaleDateString('ja-JP')}
                      </div>
                    </DropdownMenuItem>
                  ))
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDarkTheme(!isDarkTheme)}
            >
              {isDarkTheme ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          {/* Left Panel - Query Editor */}
          <ResizablePanel defaultSize={60} minSize={30}>
            <div className="h-full flex flex-col">
              {/* Query Editor Header */}
              <div className="border-b border-border p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    <span className="text-sm font-medium">クエリエディタ</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowSaveDialog(true)}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      保存
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(query)}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      コピー
                    </Button>
                  </div>
                </div>

                {/* Save Dialog */}
                {showSaveDialog && (
                  <div className="mb-3 p-3 border border-border rounded-lg bg-muted/50">
                    <div className="flex items-center gap-2">
                      <Input
                        placeholder="クエリ名を入力..."
                        value={saveQueryName}
                        onChange={(e) => setSaveQueryName(e.target.value)}
                        className="flex-1"
                      />
                      <Button onClick={saveQuery} size="sm">
                        保存
                      </Button>
                      <Button
                        onClick={() => setShowSaveDialog(false)}
                        variant="outline"
                        size="sm"
                      >
                        キャンセル
                      </Button>
                    </div>
                  </div>
                )}

                <Textarea
                  ref={textareaRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="SELECT * FROM users WHERE is_active = true;"
                  className="min-h-[200px] font-mono text-sm resize-none"
                />

                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={executeQuery}
                      disabled={isExecuting || !query.trim()}
                      size="sm"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      {isExecuting ? "実行中..." : "実行"}
                    </Button>
                    <Button variant="outline" size="sm">
                      <FileCode className="h-4 w-4 mr-2" />
                      実行計画
                    </Button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Ctrl/Cmd + Enter で実行 | Ctrl/Cmd + S で保存
                  </div>
                </div>
              </div>

              {/* Results Area */}
              <div className="flex-1 p-4 overflow-hidden">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium">実行結果</h3>
                  <div className="flex items-center gap-2">
                    {executionTime && (
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {executionTime}ms
                      </Badge>
                    )}
                    {rowCount !== null && (
                      <Badge variant="secondary" className="text-xs">
                        {rowCount} 行
                      </Badge>
                    )}
                    {queryResults.length > 0 && (
                      <Button onClick={exportResults} variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        CSV出力
                      </Button>
                    )}
                  </div>
                </div>

                {queryResults.length > 0 ? (
                  <div className="border border-border rounded-lg overflow-hidden h-[calc(100%-60px)]">
                    <ScrollArea className="h-full">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {Object.keys(queryResults[0]).map((column) => (
                              <TableHead key={column} className="font-mono text-xs whitespace-nowrap">
                                {column}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {queryResults.map((row, index) => (
                            <TableRow key={index}>
                              {Object.values(row).map((value, cellIndex) => (
                                <TableCell key={cellIndex} className="font-mono text-xs max-w-xs">
                                  <div className="truncate">
                                    {typeof value === "boolean" ? (
                                      <Badge variant={value ? "default" : "secondary"}>
                                        {value ? "true" : "false"}
                                      </Badge>
                                    ) : typeof value === "string" && value.includes("@") ? (
                                      <span className="text-blue-600">{value}</span>
                                    ) : (
                                      String(value)
                                    )}
                                  </div>
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ScrollArea>
                  </div>
                ) : (
                  <div className="border border-dashed border-border rounded-lg p-8 text-center h-[calc(100%-60px)] flex items-center justify-center">
                    <div>
                      <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">
                        {isExecuting ? "クエリを実行中..." : "クエリを実行して結果を表示"}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* Right Panel - History & Info */}
          <ResizablePanel defaultSize={40} minSize={25}>
            <div className="h-full flex flex-col">
              {/* History Header */}
              <div className="border-b border-border p-4">
                <div className="flex items-center gap-2 mb-3">
                  <History className="h-4 w-4" />
                  <span className="text-sm font-medium">クエリ履歴</span>
                  <Badge variant="outline" className="text-xs">
                    {queryHistory.length}
                  </Badge>
                </div>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="履歴を検索..."
                    value={searchHistory}
                    onChange={(e) => setSearchHistory(e.target.value)}
                    className="pl-8 text-sm"
                  />
                </div>
              </div>

              {/* History List */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-3">
                  {filteredHistory.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-8 w-8 mx-auto mb-2" />
                      <p className="text-sm">
                        {queryHistory.length === 0 ? "履歴はありません" : "検索結果がありません"}
                      </p>
                    </div>
                  ) : (
                    filteredHistory.map((item) => (
                      <Card
                        key={item.id}
                        className="p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => setQuery(item.sql)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="text-xs text-muted-foreground">
                            {item.timestamp.toLocaleTimeString('ja-JP', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          <div className="flex items-center gap-1">
                            {item.executionTime && (
                              <Badge variant="outline" className="text-xs px-1 py-0">
                                {item.executionTime}ms
                              </Badge>
                            )}
                            {item.rowCount !== undefined && (
                              <Badge variant="secondary" className="text-xs px-1 py-0">
                                {item.rowCount}行
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="font-mono text-xs text-foreground/80 bg-muted p-2 rounded overflow-hidden">
                          <div className="truncate">
                            {item.sql.split('\\n')[0]}
                          </div>
                          {item.sql.split('\\n').length > 1 && (
                            <div className="text-muted-foreground">
                              ... +{item.sql.split('\\n').length - 1} 行
                            </div>
                          )}
                        </div>
                      </Card>
                    ))
                  )}
                </div>
              </ScrollArea>

              {/* Quick Stats */}
              <div className="border-t border-border p-4">
                <h4 className="text-sm font-medium mb-3">システム情報</h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">接続状態</span>
                    <span className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      接続中
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">権限</span>
                    <span>読み取り専用</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">レート制限</span>
                    <span>100クエリ/時間</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">実行履歴</span>
                    <span>{queryHistory.length}/100</span>
                  </div>
                </div>
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}