'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Clock,
  Database,
  Download,
  Eye,
  Filter,
  Mail,
  Monitor,
  Pause,
  Play,
  RefreshCw,
  Settings,
  TrendingDown,
  TrendingUp,
  Users,
  Zap,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Server
} from 'lucide-react';

// Mock data interfaces
interface SystemMetrics {
  totalJobs: number;
  totalUsers: number;
  totalMatches: number;
  emailsSent: number;
  jobsTrend: number;
  usersTrend: number;
  matchesTrend: number;
  emailsTrend: number;
}

interface BatchJob {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  progress: number;
  startTime: string;
  duration: number;
  type: string;
}

interface PerformanceMetric {
  timestamp: string;
  apiResponseTime: number;
  dbQueryTime: number;
  memoryUsage: number;
  cpuUsage: number;
  errorRate: number;
  throughput: number;
}

interface EmailStats {
  sent: number;
  opened: number;
  clicked: number;
  bounced: number;
  openRate: number;
  clickRate: number;
  bounceRate: number;
}

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  source: string;
}

// Mock data generators
const generateMockSystemMetrics = (): SystemMetrics => ({
  totalJobs: 15647,
  totalUsers: 8923,
  totalMatches: 45231,
  emailsSent: 23456,
  jobsTrend: 12.5,
  usersTrend: 8.3,
  matchesTrend: -2.1,
  emailsTrend: 15.7
});

const generateMockBatchJobs = (): BatchJob[] => [
  {
    id: 'job-001',
    name: 'Daily Job Matching',
    status: 'running',
    progress: 67,
    startTime: '2024-01-15T10:30:00Z',
    duration: 1200,
    type: 'matching'
  },
  {
    id: 'job-002',
    name: 'Email Campaign Send',
    status: 'completed',
    progress: 100,
    startTime: '2024-01-15T09:00:00Z',
    duration: 1800,
    type: 'email'
  },
  {
    id: 'job-003',
    name: 'User Profile Sync',
    status: 'failed',
    progress: 34,
    startTime: '2024-01-15T08:15:00Z',
    duration: 450,
    type: 'sync'
  },
  {
    id: 'job-004',
    name: 'Database Cleanup',
    status: 'pending',
    progress: 0,
    startTime: '2024-01-15T11:00:00Z',
    duration: 0,
    type: 'maintenance'
  }
];

const generateMockPerformanceData = (): PerformanceMetric[] => {
  const data: PerformanceMetric[] = [];
  const now = new Date();

  for (let i = 23; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      timestamp: timestamp.toISOString().substr(11, 5),
      apiResponseTime: 120 + Math.random() * 80,
      dbQueryTime: 45 + Math.random() * 30,
      memoryUsage: 65 + Math.random() * 20,
      cpuUsage: 40 + Math.random() * 30,
      errorRate: Math.random() * 2,
      throughput: 1000 + Math.random() * 500
    });
  }

  return data;
};

const generateMockEmailStats = (): EmailStats => ({
  sent: 23456,
  opened: 18734,
  clicked: 5623,
  bounced: 234,
  openRate: 79.9,
  clickRate: 24.0,
  bounceRate: 1.0
});

const generateMockAlerts = (): Alert[] => [
  {
    id: 'alert-001',
    type: 'error',
    message: 'Database connection pool exhausted',
    timestamp: '2024-01-15T10:45:00Z',
    severity: 'critical',
    source: 'database'
  },
  {
    id: 'alert-002',
    type: 'warning',
    message: 'High memory usage detected (85%)',
    timestamp: '2024-01-15T10:30:00Z',
    severity: 'medium',
    source: 'system'
  },
  {
    id: 'alert-003',
    type: 'info',
    message: 'Daily backup completed successfully',
    timestamp: '2024-01-15T09:00:00Z',
    severity: 'low',
    source: 'backup'
  }
];

export default function MonitoringDashboard() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(generateMockSystemMetrics());
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>(generateMockBatchJobs());
  const [performanceData, setPerformanceData] = useState<PerformanceMetric[]>(generateMockPerformanceData());
  const [emailStats, setEmailStats] = useState<EmailStats>(generateMockEmailStats());
  const [alerts, setAlerts] = useState<Alert[]>(generateMockAlerts());
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [timeRange, setTimeRange] = useState('24h');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Auto-refresh logic
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      setSystemMetrics(generateMockSystemMetrics());
      setBatchJobs(generateMockBatchJobs());
      setPerformanceData(generateMockPerformanceData());
      setEmailStats(generateMockEmailStats());
      // Don't refresh alerts as frequently
      if (Math.random() > 0.7) {
        setAlerts(generateMockAlerts());
      }
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [isAutoRefresh, refreshInterval]);

  const handleExportDashboard = useCallback(() => {
    // Mock export functionality
    console.log('Exporting dashboard as PDF...');
    // In real implementation, this would generate and download a PDF
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };

    return (
      <Badge className={variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800'}>
        {status}
      </Badge>
    );
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  return (
    <div className={`min-h-screen bg-gray-50 p-6 ${isFullscreen ? 'fixed inset-0 z-50 overflow-auto' : ''}`}>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoring Dashboard</h1>
          <p className="text-gray-600">Real-time system monitoring and analytics</p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          {/* Auto-refresh Controls */}
          <div className="flex items-center space-x-2">
            <Button
              variant={isAutoRefresh ? "default" : "outline"}
              size="sm"
              onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            >
              {isAutoRefresh ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {isAutoRefresh ? 'Pause' : 'Resume'}
            </Button>

            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none"
              disabled={!isAutoRefresh}
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
            </select>
          </div>

          {/* Action Buttons */}
          <Button variant="outline" size="sm" onClick={handleExportDashboard}>
            <Download className="h-4 w-4" />
            Export PDF
          </Button>

          <Button variant="outline" size="sm" onClick={toggleFullscreen}>
            <Monitor className="h-4 w-4" />
            {isFullscreen ? 'Exit' : 'Fullscreen'}
          </Button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.totalJobs.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {systemMetrics.jobsTrend > 0 ? (
                <TrendingUp className="h-3 w-3 text-green-500" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-500" />
              )}
              <span className={systemMetrics.jobsTrend > 0 ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(systemMetrics.jobsTrend)}%
              </span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.totalUsers.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-green-600">{systemMetrics.usersTrend}%</span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Matches Made</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.totalMatches.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingDown className="h-3 w-3 text-red-500" />
              <span className="text-red-600">{Math.abs(systemMetrics.matchesTrend)}%</span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emails Sent</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.emailsSent.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-green-600">{systemMetrics.emailsTrend}%</span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="batch-jobs">Batch Jobs</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="email-campaigns">Email Campaigns</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* API Response Times */}
            <Card>
              <CardHeader>
                <CardTitle>API Response Times</CardTitle>
                <CardDescription>Average response times over the last 24 hours</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="apiResponseTime" stroke="#8884d8" name="API (ms)" />
                    <Line type="monotone" dataKey="dbQueryTime" stroke="#82ca9d" name="DB (ms)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* System Resource Usage */}
            <Card>
              <CardHeader>
                <CardTitle>System Resources</CardTitle>
                <CardDescription>CPU and memory usage trends</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="cpuUsage" stackId="1" stroke="#8884d8" fill="#8884d8" name="CPU %" />
                    <Area type="monotone" dataKey="memoryUsage" stackId="1" stroke="#82ca9d" fill="#82ca9d" name="Memory %" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Batch Jobs Tab */}
        <TabsContent value="batch-jobs" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Active Batch Jobs</CardTitle>
                  <CardDescription>Currently running and recent batch operations</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Job Name</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Progress</TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead>Type</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {batchJobs.map((job) => (
                        <TableRow key={job.id}>
                          <TableCell className="font-medium">
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(job.status)}
                              <span>{job.name}</span>
                            </div>
                          </TableCell>
                          <TableCell>{getStatusBadge(job.status)}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-blue-500 transition-all duration-300"
                                  style={{ width: `${job.progress}%` }}
                                />
                              </div>
                              <span className="text-sm text-gray-600">{job.progress}%</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {job.duration > 0 ? `${Math.floor(job.duration / 60)}m ${job.duration % 60}s` : '-'}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{job.type}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>

            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Job Statistics</CardTitle>
                  <CardDescription>Success rate and performance metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Success Rate</span>
                      <span className="font-medium text-green-600">94.2%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: '94.2%' }} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Average Duration</span>
                      <span className="font-medium">12m 34s</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Queue Depth</span>
                      <span className="font-medium">7 jobs</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Failed Jobs (24h)</span>
                      <span className="font-medium text-red-600">3</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Request Throughput</CardTitle>
                <CardDescription>Requests per minute over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="throughput" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Rate</CardTitle>
                <CardDescription>Application error rate percentage</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="errorRate" stroke="#ff7300" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Database Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Query Time</span>
                      <span className="font-medium">avg 45ms</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: '60%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Connection Pool</span>
                      <span className="font-medium">12/20</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: '60%' }} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Hit Rate</span>
                      <span className="font-medium text-green-600">89.3%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: '89.3%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Memory Usage</span>
                      <span className="font-medium">2.1GB / 4GB</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-yellow-500" style={{ width: '52.5%' }} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>API Endpoints</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>/api/jobs</span>
                    <span className="text-green-600">98.2%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>/api/users</span>
                    <span className="text-green-600">99.1%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>/api/matches</span>
                    <span className="text-yellow-600">95.7%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>/api/emails</span>
                    <span className="text-green-600">97.8%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Email Campaigns Tab */}
        <TabsContent value="email-campaigns" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Campaign Performance</CardTitle>
                  <CardDescription>Email campaign metrics and engagement rates</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Open Rate</span>
                          <span className="font-medium text-green-600">{emailStats.openRate}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-green-500" style={{ width: `${emailStats.openRate}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Click Rate</span>
                          <span className="font-medium text-blue-600">{emailStats.clickRate}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500" style={{ width: `${emailStats.clickRate}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Bounce Rate</span>
                          <span className="font-medium text-red-600">{emailStats.bounceRate}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500" style={{ width: `${emailStats.bounceRate * 10}%` }} />
                        </div>
                      </div>
                    </div>

                    <div>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Opened', value: emailStats.opened },
                              { name: 'Clicked', value: emailStats.clicked },
                              { name: 'Bounced', value: emailStats.bounced },
                              { name: 'Unread', value: emailStats.sent - emailStats.opened }
                            ]}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {COLORS.map((color, index) => (
                              <Cell key={`cell-${index}`} fill={color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Email Statistics</CardTitle>
                  <CardDescription>Today's email metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4 text-blue-500" />
                      <span className="text-sm">Sent</span>
                    </div>
                    <span className="font-medium">{emailStats.sent.toLocaleString()}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Eye className="h-4 w-4 text-green-500" />
                      <span className="text-sm">Opened</span>
                    </div>
                    <span className="font-medium">{emailStats.opened.toLocaleString()}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Activity className="h-4 w-4 text-purple-500" />
                      <span className="text-sm">Clicked</span>
                    </div>
                    <span className="font-medium">{emailStats.clicked.toLocaleString()}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-red-500" />
                      <span className="text-sm">Bounced</span>
                    </div>
                    <span className="font-medium">{emailStats.bounced.toLocaleString()}</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Top Performing Sections</CardTitle>
                  <CardDescription>Most engaging job categories</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Technology</span>
                      <span className="font-medium text-green-600">34.2%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Healthcare</span>
                      <span className="font-medium text-green-600">28.7%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Finance</span>
                      <span className="font-medium text-blue-600">22.1%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Education</span>
                      <span className="font-medium text-blue-600">15.0%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>System Alerts</CardTitle>
                  <CardDescription>Recent alerts and system notifications</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    <div className="space-y-4">
                      {alerts.map((alert) => (
                        <div key={alert.id} className="flex items-start space-x-3 rounded-lg border p-4">
                          <div className="flex-shrink-0">
                            {getAlertIcon(alert.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-gray-900">
                                {alert.message}
                              </p>
                              <Badge
                                className={
                                  alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                                  alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                                  alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-blue-100 text-blue-800'
                                }
                              >
                                {alert.severity}
                              </Badge>
                            </div>
                            <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                              <span>{alert.source}</span>
                              <span>•</span>
                              <span>{new Date(alert.timestamp).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Alert Summary</CardTitle>
                  <CardDescription>Alert distribution by severity</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded-full bg-red-500" />
                        <span className="text-sm">Critical</span>
                      </div>
                      <span className="font-medium">1</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded-full bg-orange-500" />
                        <span className="text-sm">High</span>
                      </div>
                      <span className="font-medium">0</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded-full bg-yellow-500" />
                        <span className="text-sm">Medium</span>
                      </div>
                      <span className="font-medium">1</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="h-3 w-3 rounded-full bg-blue-500" />
                        <span className="text-sm">Low</span>
                      </div>
                      <span className="font-medium">1</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>Current system health</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Server className="h-4 w-4 text-green-500" />
                        <span className="text-sm">API Server</span>
                      </div>
                      <Badge className="bg-green-100 text-green-800">Healthy</Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Database className="h-4 w-4 text-red-500" />
                        <span className="text-sm">Database</span>
                      </div>
                      <Badge className="bg-red-100 text-red-800">Warning</Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-green-500" />
                        <span className="text-sm">Email Service</span>
                      </div>
                      <Badge className="bg-green-100 text-green-800">Healthy</Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Activity className="h-4 w-4 text-green-500" />
                        <span className="text-sm">Background Jobs</span>
                      </div>
                      <Badge className="bg-green-100 text-green-800">Running</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}