'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  RefreshCw,
  Download,
  Search,
  Filter,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Database,
  Mail,
  Users,
  Zap,
  TrendingUp,
  Server,
  Settings
} from 'lucide-react'

// Types for dashboard data
interface BatchStatus {
  id: string
  status: 'running' | 'completed' | 'failed' | 'pending'
  phase: 'import' | 'matching' | 'email' | 'complete'
  progress: number
  startTime: Date
  estimatedTimeRemaining: number
  totalUsers: number
  processedUsers: number
  currentSpeed: number
}

interface LogEntry {
  id: string
  timestamp: Date
  level: 'ERROR' | 'WARNING' | 'INFO'
  message: string
  details?: string
  component: string
}

interface MetricData {
  name: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'neutral'
  trendValue: number
  status: 'good' | 'warning' | 'error'
}

interface PerformanceData {
  timestamp: Date
  cpuUsage: number
  memoryUsage: number
  processingSpeed: number
  emailQueue: number
  dbConnections: number
}

// Mock data generators
const generateMockBatchStatus = (): BatchStatus => ({
  id: 'batch-2024-001',
  status: Math.random() > 0.7 ? 'running' : Math.random() > 0.5 ? 'completed' : 'failed',
  phase: ['import', 'matching', 'email', 'complete'][Math.floor(Math.random() * 4)] as any,
  progress: Math.floor(Math.random() * 100),
  startTime: new Date(Date.now() - Math.random() * 3600000),
  estimatedTimeRemaining: Math.floor(Math.random() * 1800),
  totalUsers: 15000,
  processedUsers: Math.floor(Math.random() * 15000),
  currentSpeed: Math.floor(Math.random() * 200) + 50
})

const generateMockLogs = (count: number): LogEntry[] => {
  const levels: ('ERROR' | 'WARNING' | 'INFO')[] = ['ERROR', 'WARNING', 'INFO']
  const components = ['BatchProcessor', 'EmailService', 'DatabaseManager', 'MatchingEngine']
  const messages = [
    'Processing completed successfully',
    'Database connection pool exhausted',
    'Email delivery failed for user',
    'Matching algorithm updated',
    'Memory usage threshold exceeded',
    'Batch import started',
    'User preferences updated',
    'Performance optimization applied'
  ]

  return Array.from({ length: count }, (_, i) => ({
    id: `log-${i}`,
    timestamp: new Date(Date.now() - Math.random() * 86400000),
    level: levels[Math.floor(Math.random() * levels.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    details: Math.random() > 0.7 ? 'Additional error details and stack trace information' : undefined,
    component: components[Math.floor(Math.random() * components.length)]
  }))
}

const generateMockMetrics = (): MetricData[] => [
  {
    name: 'Processing Speed',
    value: Math.floor(Math.random() * 200) + 50,
    unit: 'users/min',
    trend: Math.random() > 0.5 ? 'up' : 'down',
    trendValue: Math.floor(Math.random() * 20),
    status: 'good'
  },
  {
    name: 'Memory Usage',
    value: Math.floor(Math.random() * 40) + 40,
    unit: '%',
    trend: Math.random() > 0.5 ? 'up' : 'down',
    trendValue: Math.floor(Math.random() * 10),
    status: Math.random() > 0.3 ? 'good' : 'warning'
  },
  {
    name: 'Email Queue',
    value: Math.floor(Math.random() * 500),
    unit: 'emails',
    trend: Math.random() > 0.5 ? 'up' : 'down',
    trendValue: Math.floor(Math.random() * 50),
    status: 'good'
  },
  {
    name: 'DB Connections',
    value: Math.floor(Math.random() * 80) + 10,
    unit: 'active',
    trend: 'neutral',
    trendValue: 0,
    status: 'good'
  },
  {
    name: 'Success Rate',
    value: Math.floor(Math.random() * 10) + 90,
    unit: '%',
    trend: 'up',
    trendValue: Math.floor(Math.random() * 5),
    status: 'good'
  },
  {
    name: 'CPU Usage',
    value: Math.floor(Math.random() * 60) + 20,
    unit: '%',
    trend: Math.random() > 0.5 ? 'up' : 'down',
    trendValue: Math.floor(Math.random() * 15),
    status: Math.random() > 0.2 ? 'good' : 'warning'
  }
]

const generateMockPerformanceData = (hours: number): PerformanceData[] => {
  return Array.from({ length: hours }, (_, i) => ({
    timestamp: new Date(Date.now() - (hours - i) * 3600000),
    cpuUsage: Math.floor(Math.random() * 40) + 30,
    memoryUsage: Math.floor(Math.random() * 30) + 40,
    processingSpeed: Math.floor(Math.random() * 100) + 100,
    emailQueue: Math.floor(Math.random() * 200),
    dbConnections: Math.floor(Math.random() * 20) + 40
  }))
}

// Component definitions
const BatchStatusCard = ({ batch }: { batch: BatchStatus }) => {
  const getStatusIcon = () => {
    switch (batch.status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getStatusColor = () => {
    switch (batch.status) {
      case 'running':
        return 'bg-blue-500'
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      default:
        return 'bg-yellow-500'
    }
  }

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {getStatusIcon()}
            Batch Processing Status
          </CardTitle>
          <Badge variant={batch.status === 'completed' ? 'default' : 'secondary'}>
            {batch.id}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Progress ({batch.phase.charAt(0).toUpperCase() + batch.phase.slice(1)})</span>
              <span>{batch.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
                style={{ width: `${batch.progress}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Processed</div>
              <div className="font-medium">{batch.processedUsers.toLocaleString()} / {batch.totalUsers.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Speed</div>
              <div className="font-medium">{batch.currentSpeed} users/min</div>
            </div>
            <div>
              <div className="text-muted-foreground">Started</div>
              <div className="font-medium">{batch.startTime.toLocaleTimeString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">ETA</div>
              <div className="font-medium">
                {batch.status === 'running' ? formatTime(batch.estimatedTimeRemaining) : '--'}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const ErrorLogPanel = ({ logs }: { logs: LogEntry[] }) => {
  const [filteredLogs, setFilteredLogs] = useState(logs)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')

  useEffect(() => {
    let filtered = logs

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.component.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter)
    }

    setFilteredLogs(filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()))
  }, [logs, searchTerm, levelFilter])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-500 bg-red-50'
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50'
      case 'INFO':
        return 'text-blue-500 bg-blue-50'
      default:
        return 'text-gray-500 bg-gray-50'
    }
  }

  const exportLogs = () => {
    const logData = filteredLogs.map(log => ({
      timestamp: log.timestamp.toISOString(),
      level: log.level,
      component: log.component,
      message: log.message,
      details: log.details || ''
    }))

    const csv = [
      'Timestamp,Level,Component,Message,Details',
      ...logData.map(row => `"${row.timestamp}","${row.level}","${row.component}","${row.message}","${row.details}"`)
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `error-logs-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <Card className="col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Error Log Viewer</CardTitle>
            <CardDescription>Real-time system logs and error tracking</CardDescription>
          </div>
          <Button onClick={exportLogs} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
        <div className="flex gap-4 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            {['all', 'ERROR', 'WARNING', 'INFO'].map((level) => (
              <Button
                key={level}
                variant={levelFilter === level ? 'default' : 'outline'}
                size="sm"
                onClick={() => setLevelFilter(level)}
              >
                {level === 'all' ? 'All' : level}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          <div className="space-y-2">
            {filteredLogs.map((log) => (
              <div key={log.id} className="border rounded-lg p-3 hover:bg-muted/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={getLevelColor(log.level)}>
                      {log.level}
                    </Badge>
                    <span className="text-sm font-medium">{log.component}</span>
                    <span className="text-xs text-muted-foreground">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <div className="mt-1 text-sm">{log.message}</div>
                {log.details && (
                  <div className="mt-2 text-xs text-muted-foreground bg-muted p-2 rounded">
                    {log.details}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

const MetricCard = ({ metric }: { metric: MetricData }) => {
  const getTrendIcon = () => {
    if (metric.trend === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />
    if (metric.trend === 'down') return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />
    return <div className="h-4 w-4" />
  }

  const getStatusColor = () => {
    switch (metric.status) {
      case 'good':
        return 'border-green-200 bg-green-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      case 'error':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200'
    }
  }

  return (
    <Card className={getStatusColor()}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{metric.name}</p>
            <p className="text-2xl font-bold">
              {metric.value.toLocaleString()}
              <span className="text-sm font-normal text-muted-foreground ml-1">
                {metric.unit}
              </span>
            </p>
          </div>
          <div className="flex items-center gap-1">
            {getTrendIcon()}
            {metric.trendValue > 0 && (
              <span className={`text-xs ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {metric.trend === 'up' ? '+' : '-'}{metric.trendValue}%
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const PerformanceChart = ({ data }: { data: PerformanceData[] }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Trends</CardTitle>
        <CardDescription>System performance over the last 24 hours</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64 flex items-center justify-center bg-muted/20 rounded">
          <div className="text-center">
            <Activity className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Chart visualization would be rendered here</p>
            <p className="text-xs text-muted-foreground mt-1">
              Integration with recharts library for real charts
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const SystemHealthIndicator = ({ metrics }: { metrics: MetricData[] }) => {
  const getOverallHealth = () => {
    const errorCount = metrics.filter(m => m.status === 'error').length
    const warningCount = metrics.filter(m => m.status === 'warning').length

    if (errorCount > 0) return { status: 'error', message: 'System Issues Detected' }
    if (warningCount > 0) return { status: 'warning', message: 'Performance Warnings' }
    return { status: 'good', message: 'All Systems Operational' }
  }

  const health = getOverallHealth()

  const getHealthIcon = () => {
    switch (health.status) {
      case 'good':
        return <CheckCircle className="h-6 w-6 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-6 w-6 text-yellow-500" />
      case 'error':
        return <XCircle className="h-6 w-6 text-red-500" />
    }
  }

  const getHealthColor = () => {
    switch (health.status) {
      case 'good':
        return 'border-green-200 bg-green-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      case 'error':
        return 'border-red-200 bg-red-50'
    }
  }

  return (
    <Card className={getHealthColor()}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {getHealthIcon()}
          <div>
            <p className="font-semibold">{health.message}</p>
            <p className="text-sm text-muted-foreground">
              Last updated: {new Date().toLocaleTimeString()}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const [batchStatus, setBatchStatus] = useState<BatchStatus>(generateMockBatchStatus())
  const [logs, setLogs] = useState<LogEntry[]>(generateMockLogs(50))
  const [metrics, setMetrics] = useState<MetricData[]>(generateMockMetrics())
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>(generateMockPerformanceData(24))
  const [lastRefresh, setLastRefresh] = useState(new Date())
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      setBatchStatus(generateMockBatchStatus())
      setLogs(prev => [...generateMockLogs(5), ...prev].slice(0, 100))
      setMetrics(generateMockMetrics())
      setLastRefresh(new Date())
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [autoRefresh])

  const handleManualRefresh = () => {
    setBatchStatus(generateMockBatchStatus())
    setLogs(prev => [...generateMockLogs(3), ...prev].slice(0, 100))
    setMetrics(generateMockMetrics())
    setLastRefresh(new Date())
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">System Dashboard</h1>
            <p className="text-muted-foreground">
              Job matching system monitoring and administration
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
            <Button
              onClick={handleManualRefresh}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              variant={autoRefresh ? 'default' : 'outline'}
              size="sm"
            >
              <Settings className="h-4 w-4 mr-2" />
              Auto: {autoRefresh ? 'ON' : 'OFF'}
            </Button>
          </div>
        </div>

        {/* System Health Overview */}
        <SystemHealthIndicator metrics={metrics} />

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="processing">Processing</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <BatchStatusCard batch={batchStatus} />
              </div>
              <div className="lg:col-span-2">
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                  {metrics.map((metric, index) => (
                    <MetricCard key={index} metric={metric} />
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="processing" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <BatchStatusCard batch={batchStatus} />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Processing Queue
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <Users className="h-4 w-4 text-blue-500" />
                        <span>User Import</span>
                      </div>
                      <Badge>Waiting</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <Zap className="h-4 w-4 text-green-500" />
                        <span>Job Matching</span>
                      </div>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <Mail className="h-4 w-4 text-purple-500" />
                        <span>Email Delivery</span>
                      </div>
                      <Badge>Queue: 234</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="logs" className="space-y-6">
            <ErrorLogPanel logs={logs} />
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PerformanceChart data={performanceData} />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5" />
                    System Resources
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {metrics.slice(0, 4).map((metric, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{metric.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                metric.status === 'good' ? 'bg-green-500' :
                                metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(metric.value, 100)}%` }}
                            />
                          </div>
                          <span className="text-sm text-muted-foreground w-16 text-right">
                            {metric.value}{metric.unit}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}