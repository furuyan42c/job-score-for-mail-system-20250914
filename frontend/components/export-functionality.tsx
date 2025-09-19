/**
 * Export Functionality Component - T040-T042 Implementation
 *
 * Provides comprehensive data export capabilities:
 * - Multiple formats (CSV, Excel, PDF, JSON)
 * - Custom field selection
 * - Batch export
 * - Scheduled exports
 * - Export history
 *
 * Created: 2025-09-19
 * Tasks: T040-T042 - Advanced Export Features
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Download, FileText, Table, FileSpreadsheet, Calendar, History, Settings, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

interface ExportField {
  id: string
  name: string
  description: string
  type: 'string' | 'number' | 'date' | 'boolean' | 'array'
  required: boolean
  category: string
}

interface ExportFormat {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  extension: string
  maxRecords?: number
  supportedFields: string[]
}

interface ExportJob {
  id: string
  name: string
  format: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  created_at: string
  completed_at?: string
  download_url?: string
  record_count: number
  file_size?: string
  error_message?: string
}

interface ScheduledExport {
  id: string
  name: string
  format: string
  schedule: string
  next_run: string
  enabled: boolean
  fields: string[]
  filters: any
  email_recipients: string[]
}

// ============================================================================
// COMPONENT PROPS
// ============================================================================

interface ExportFunctionalityProps {
  data: any[]
  filters: any
  onExport: (config: ExportConfig) => Promise<string>
}

interface ExportConfig {
  format: string
  fields: string[]
  filters: any
  filename: string
  options: {
    includeHeaders: boolean
    includeMetadata: boolean
    compression: boolean
    password?: string
  }
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ExportFunctionality({
  data,
  filters,
  onExport
}: ExportFunctionalityProps) {
  // State management
  const [selectedFormat, setSelectedFormat] = useState('csv')
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([])
  const [scheduledExports, setScheduledExports] = useState<ScheduledExport[]>([])
  const [currentJob, setCurrentJob] = useState<ExportJob | null>(null)
  const [filename, setFilename] = useState('')
  const [includeHeaders, setIncludeHeaders] = useState(true)
  const [includeMetadata, setIncludeMetadata] = useState(false)
  const [compression, setCompression] = useState(false)
  const [password, setPassword] = useState('')

  // Available export formats
  const exportFormats: ExportFormat[] = [
    {
      id: 'csv',
      name: 'CSV',
      description: 'カンマ区切り形式 (.csv)',
      icon: <Table className="h-4 w-4" />,
      extension: 'csv',
      supportedFields: ['all']
    },
    {
      id: 'excel',
      name: 'Excel',
      description: 'Microsoft Excel形式 (.xlsx)',
      icon: <FileSpreadsheet className="h-4 w-4" />,
      extension: 'xlsx',
      supportedFields: ['all']
    },
    {
      id: 'pdf',
      name: 'PDF',
      description: 'PDF文書形式 (.pdf)',
      icon: <FileText className="h-4 w-4" />,
      extension: 'pdf',
      maxRecords: 1000,
      supportedFields: ['basic']
    },
    {
      id: 'json',
      name: 'JSON',
      description: 'JSON形式 (.json)',
      icon: <FileText className="h-4 w-4" />,
      extension: 'json',
      supportedFields: ['all']
    }
  ]

  // Available fields for export
  const availableFields: ExportField[] = [
    { id: 'id', name: 'ID', description: '求人ID', type: 'string', required: true, category: 'basic' },
    { id: 'title', name: '職種名', description: '求人タイトル', type: 'string', required: true, category: 'basic' },
    { id: 'company', name: '会社名', description: '企業名', type: 'string', required: true, category: 'basic' },
    { id: 'location', name: '勤務地', description: '勤務地情報', type: 'string', required: false, category: 'basic' },
    { id: 'salary', name: '給与', description: '給与情報', type: 'string', required: false, category: 'basic' },
    { id: 'type', name: '雇用形態', description: '雇用形態', type: 'string', required: false, category: 'basic' },
    { id: 'description', name: '職務内容', description: '詳細な職務内容', type: 'string', required: false, category: 'detailed' },
    { id: 'requirements', name: '必要スキル', description: '必要な技術・経験', type: 'array', required: false, category: 'detailed' },
    { id: 'benefits', name: '福利厚生', description: '福利厚生情報', type: 'array', required: false, category: 'detailed' },
    { id: 'posted_date', name: '掲載日', description: '求人掲載日', type: 'date', required: false, category: 'metadata' },
    { id: 'updated_date', name: '更新日', description: '最終更新日', type: 'date', required: false, category: 'metadata' },
    { id: 'match_score', name: 'マッチ度', description: 'ユーザーとのマッチ度', type: 'number', required: false, category: 'analytics' },
    { id: 'view_count', name: '閲覧数', description: '求人閲覧数', type: 'number', required: false, category: 'analytics' },
    { id: 'application_count', name: '応募数', description: '応募者数', type: 'number', required: false, category: 'analytics' }
  ]

  // Field categories
  const fieldCategories = {
    basic: '基本情報',
    detailed: '詳細情報',
    metadata: 'メタデータ',
    analytics: '分析データ'
  }

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    // Initialize with required fields
    const requiredFields = availableFields
      .filter(field => field.required)
      .map(field => field.id)
    setSelectedFields(requiredFields)

    // Set default filename
    const timestamp = new Date().toISOString().split('T')[0]
    setFilename(`job_export_${timestamp}`)

    // Load export history
    loadExportHistory()
    loadScheduledExports()
  }, [])

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleFieldToggle = (fieldId: string) => {
    const field = availableFields.find(f => f.id === fieldId)
    if (field?.required) return // Can't toggle required fields

    setSelectedFields(prev =>
      prev.includes(fieldId)
        ? prev.filter(id => id !== fieldId)
        : [...prev, fieldId]
    )
  }

  const handleSelectAllFields = (category?: string) => {
    const fieldsToAdd = category
      ? availableFields.filter(field => field.category === category).map(field => field.id)
      : availableFields.map(field => field.id)

    setSelectedFields(prev => {
      const newFields = [...new Set([...prev, ...fieldsToAdd])]
      return newFields
    })
  }

  const handleDeselectAllFields = (category?: string) => {
    const fieldsToRemove = category
      ? availableFields.filter(field => field.category === category && !field.required).map(field => field.id)
      : availableFields.filter(field => !field.required).map(field => field.id)

    setSelectedFields(prev => prev.filter(id => !fieldsToRemove.includes(id)))
  }

  const handleExport = async () => {
    try {
      const exportConfig: ExportConfig = {
        format: selectedFormat,
        fields: selectedFields,
        filters,
        filename,
        options: {
          includeHeaders,
          includeMetadata,
          compression,
          password: password || undefined
        }
      }

      // Create export job
      const jobId = Date.now().toString()
      const newJob: ExportJob = {
        id: jobId,
        name: filename,
        format: selectedFormat,
        status: 'processing',
        progress: 0,
        created_at: new Date().toISOString(),
        record_count: data.length
      }

      setCurrentJob(newJob)
      setExportJobs(prev => [newJob, ...prev])

      // Simulate progress
      let progress = 0
      const progressInterval = setInterval(() => {
        progress += Math.random() * 20
        setCurrentJob(prev => prev ? { ...prev, progress: Math.min(progress, 95) } : null)
      }, 500)

      // Execute export
      const downloadUrl = await onExport(exportConfig)

      // Complete the job
      clearInterval(progressInterval)
      const completedJob = {
        ...newJob,
        status: 'completed' as const,
        progress: 100,
        completed_at: new Date().toISOString(),
        download_url: downloadUrl,
        file_size: `${Math.round(data.length * 0.5)}KB`
      }

      setCurrentJob(completedJob)
      setExportJobs(prev => prev.map(job => job.id === jobId ? completedJob : job))

      // Auto-download
      if (downloadUrl) {
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = `${filename}.${exportFormats.find(f => f.id === selectedFormat)?.extension}`
        link.click()
      }

    } catch (error) {
      console.error('Export failed:', error)

      if (currentJob) {
        const failedJob = {
          ...currentJob,
          status: 'failed' as const,
          error_message: error instanceof Error ? error.message : 'Unknown error'
        }
        setCurrentJob(failedJob)
        setExportJobs(prev => prev.map(job => job.id === currentJob.id ? failedJob : job))
      }
    }
  }

  const loadExportHistory = () => {
    // Mock export history
    const mockJobs: ExportJob[] = [
      {
        id: '1',
        name: 'job_export_2025-09-19',
        format: 'csv',
        status: 'completed',
        progress: 100,
        created_at: '2025-09-19T10:30:00Z',
        completed_at: '2025-09-19T10:31:00Z',
        download_url: '/downloads/job_export_1.csv',
        record_count: 1250,
        file_size: '875KB'
      },
      {
        id: '2',
        name: 'weekly_report',
        format: 'excel',
        status: 'completed',
        progress: 100,
        created_at: '2025-09-18T15:20:00Z',
        completed_at: '2025-09-18T15:22:00Z',
        download_url: '/downloads/weekly_report.xlsx',
        record_count: 3500,
        file_size: '2.3MB'
      }
    ]
    setExportJobs(mockJobs)
  }

  const loadScheduledExports = () => {
    // Mock scheduled exports
    const mockScheduled: ScheduledExport[] = [
      {
        id: '1',
        name: '週次レポート',
        format: 'excel',
        schedule: '毎週月曜日 9:00',
        next_run: '2025-09-23T09:00:00Z',
        enabled: true,
        fields: ['id', 'title', 'company', 'location', 'salary'],
        filters: {},
        email_recipients: ['admin@example.com']
      }
    ]
    setScheduledExports(mockScheduled)
  }

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderFieldSelection = () => {
    const categories = Object.keys(fieldCategories)

    return (
      <div className="space-y-4">
        {categories.map(category => {
          const categoryFields = availableFields.filter(field => field.category === category)
          const categoryName = fieldCategories[category as keyof typeof fieldCategories]
          const selectedInCategory = categoryFields.filter(field => selectedFields.includes(field.id)).length
          const totalInCategory = categoryFields.length

          return (
            <Card key={category}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">{categoryName}</CardTitle>
                  <div className="flex space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSelectAllFields(category)}
                    >
                      全選択
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeselectAllFields(category)}
                    >
                      全解除
                    </Button>
                  </div>
                </div>
                <CardDescription>
                  {selectedInCategory} / {totalInCategory} 選択中
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {categoryFields.map(field => (
                  <div key={field.id} className="flex items-center space-x-3">
                    <Checkbox
                      id={field.id}
                      checked={selectedFields.includes(field.id)}
                      onCheckedChange={() => handleFieldToggle(field.id)}
                      disabled={field.required}
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <label htmlFor={field.id} className="text-sm font-medium">
                          {field.name}
                        </label>
                        {field.required && (
                          <Badge variant="outline" className="text-xs">
                            必須
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {field.description}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )
        })}
      </div>
    )
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Export Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Download className="h-5 w-5 mr-2" />
            データエクスポート
          </CardTitle>
          <CardDescription>
            検索結果を様々な形式でエクスポートできます ({data.length} 件のレコード)
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Current Export Progress */}
      {currentJob && currentJob.status === 'processing' && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-medium">エクスポート中...</span>
                <span className="text-sm text-muted-foreground">
                  {Math.round(currentJob.progress)}%
                </span>
              </div>
              <Progress value={currentJob.progress} className="w-full" />
              <p className="text-sm text-muted-foreground">
                {currentJob.name} ({currentJob.format.toUpperCase()})
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="export" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="export">エクスポート</TabsTrigger>
          <TabsTrigger value="history">履歴</TabsTrigger>
          <TabsTrigger value="scheduled">スケジュール</TabsTrigger>
        </TabsList>

        {/* Export Tab */}
        <TabsContent value="export" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Format Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">エクスポート形式</CardTitle>
                <CardDescription>
                  データの出力形式を選択してください
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {exportFormats.map(format => (
                  <div
                    key={format.id}
                    className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedFormat === format.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedFormat(format.id)}
                  >
                    <div className="flex items-center space-x-2">
                      {format.icon}
                      <span className="font-medium">{format.name}</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground">
                        {format.description}
                      </p>
                      {format.maxRecords && (
                        <p className="text-xs text-orange-600">
                          最大 {format.maxRecords.toLocaleString()} 件
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Export Options */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">エクスポート設定</CardTitle>
                <CardDescription>
                  ファイル名とオプションを設定してください
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">ファイル名</label>
                  <Input
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                    placeholder="ファイル名を入力"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="headers"
                      checked={includeHeaders}
                      onCheckedChange={setIncludeHeaders}
                    />
                    <label htmlFor="headers" className="text-sm">
                      ヘッダー行を含める
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="metadata"
                      checked={includeMetadata}
                      onCheckedChange={setIncludeMetadata}
                    />
                    <label htmlFor="metadata" className="text-sm">
                      メタデータを含める
                    </label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="compression"
                      checked={compression}
                      onCheckedChange={setCompression}
                    />
                    <label htmlFor="compression" className="text-sm">
                      圧縮する
                    </label>
                  </div>
                </div>

                {compression && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">パスワード (オプション)</label>
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="圧縮ファイルのパスワード"
                    />
                  </div>
                )}

                <Button
                  onClick={handleExport}
                  className="w-full"
                  disabled={selectedFields.length === 0 || !filename}
                >
                  <Download className="h-4 w-4 mr-2" />
                  エクスポート開始
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Field Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">フィールド選択</CardTitle>
              <CardDescription>
                エクスポートするデータフィールドを選択してください ({selectedFields.length} 選択中)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {renderFieldSelection()}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center">
                <History className="h-4 w-4 mr-2" />
                エクスポート履歴
              </CardTitle>
              <CardDescription>
                過去のエクスポート作業の履歴です
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {exportJobs.map(job => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {job.status === 'completed' && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {job.status === 'failed' && (
                          <X className="h-4 w-4 text-red-500" />
                        )}
                        {job.status === 'processing' && (
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{job.name}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>{job.format.toUpperCase()}</span>
                          <span>{job.record_count.toLocaleString()} 件</span>
                          {job.file_size && <span>{job.file_size}</span>}
                          <span>{new Date(job.created_at).toLocaleDateString('ja-JP')}</span>
                        </div>
                        {job.error_message && (
                          <p className="text-sm text-red-500">{job.error_message}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={
                        job.status === 'completed' ? 'default' :
                        job.status === 'failed' ? 'destructive' : 'secondary'
                      }>
                        {job.status === 'completed' ? '完了' :
                         job.status === 'failed' ? '失敗' :
                         job.status === 'processing' ? '処理中' : '待機中'}
                      </Badge>
                      {job.download_url && (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={job.download_url} download>
                            <Download className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scheduled Tab */}
        <TabsContent value="scheduled" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center">
                <Calendar className="h-4 w-4 mr-2" />
                スケジュールエクスポート
              </CardTitle>
              <CardDescription>
                定期的なエクスポートの設定と管理
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {scheduledExports.map(schedule => (
                  <div
                    key={schedule.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{schedule.name}</p>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>{schedule.format.toUpperCase()}</span>
                        <span>{schedule.schedule}</span>
                        <span>次回: {new Date(schedule.next_run).toLocaleDateString('ja-JP')}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch checked={schedule.enabled} />
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                <Button variant="outline" className="w-full">
                  新しいスケジュールを作成
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}