'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DashboardProps, DashboardData, DashboardMetric, BatchJobStatus, SystemHealth } from '@/types';
import { clsx } from 'clsx';
import {
  RefreshCw,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  Briefcase,
  Target,
  Mail,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import MetricCard from './MetricCard';
import StatusIndicator from './StatusIndicator';

const REFRESH_INTERVALS = {
  30: 30000,   // 30 seconds
  60: 60000,   // 1 minute
  300: 300000, // 5 minutes
};

export default function Dashboard({
  autoRefresh = true,
  refreshInterval = 30,
  showBatchJobs = true,
  showSystemHealth = true,
  showCharts = true,
  onRefresh,
  className,
  'data-testid': testId,
}: DashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [refreshIntervalId, setRefreshIntervalId] = useState<NodeJS.Timeout | null>(null);

  // Mock data for demonstration - in real app, this would come from an API
  const mockData: DashboardData = {
    metrics: [
      {
        id: '1',
        label: 'Total Users',
        value: '12,547',
        previousValue: '11,832',
        trend: 'up',
        change: 6.0,
        format: 'number',
        icon: 'users',
        color: 'blue',
      },
      {
        id: '2',
        label: 'Active Jobs',
        value: '2,841',
        previousValue: '2,756',
        trend: 'up',
        change: 3.1,
        format: 'number',
        icon: 'briefcase',
        color: 'green',
      },
      {
        id: '3',
        label: 'Matches Today',
        value: '1,293',
        previousValue: '1,456',
        trend: 'down',
        change: -11.2,
        format: 'number',
        icon: 'target',
        color: 'yellow',
      },
      {
        id: '4',
        label: 'Emails Sent',
        value: '8,674',
        previousValue: '7,921',
        trend: 'up',
        change: 9.5,
        format: 'number',
        icon: 'mail',
        color: 'purple',
      },
    ],
    systemHealth: {
      status: 'healthy',
      services: [
        { name: 'API Gateway', status: 'up', responseTime: 45, lastCheck: new Date() },
        { name: 'Database', status: 'up', responseTime: 12, lastCheck: new Date() },
        { name: 'Email Service', status: 'up', responseTime: 78, lastCheck: new Date() },
        { name: 'Matching Engine', status: 'up', responseTime: 156, lastCheck: new Date() },
        { name: 'Redis Cache', status: 'up', responseTime: 3, lastCheck: new Date() },
      ],
      lastCheck: new Date(),
      uptime: 99.97,
    },
    batchJobs: [
      {
        id: '1',
        name: 'Daily Job Matching',
        type: 'matching',
        status: 'completed',
        progress: 100,
        startTime: new Date(Date.now() - 3600000), // 1 hour ago
        endTime: new Date(Date.now() - 3300000), // 55 minutes ago
        duration: 300000, // 5 minutes
        processedItems: 12547,
        totalItems: 12547,
      },
      {
        id: '2',
        name: 'Weekly Email Campaign',
        type: 'email',
        status: 'running',
        progress: 68,
        startTime: new Date(Date.now() - 900000), // 15 minutes ago
        processedItems: 5823,
        totalItems: 8574,
      },
      {
        id: '3',
        name: 'Data Sync',
        type: 'sync',
        status: 'pending',
        processedItems: 0,
        totalItems: 2841,
      },
    ],
    recentActivity: [
      {
        id: '1',
        type: 'user_registered',
        description: 'New user registration: john.doe@example.com',
        timestamp: new Date(Date.now() - 300000), // 5 minutes ago
      },
      {
        id: '2',
        type: 'job_posted',
        description: 'New job posted: Senior React Developer at TechCorp',
        timestamp: new Date(Date.now() - 600000), // 10 minutes ago
      },
      {
        id: '3',
        type: 'match_created',
        description: '152 new job matches generated',
        timestamp: new Date(Date.now() - 900000), // 15 minutes ago
      },
    ],
    chartData: [
      { date: '2024-01-01', value: 1200, label: 'Jan 1' },
      { date: '2024-01-02', value: 1350, label: 'Jan 2' },
      { date: '2024-01-03', value: 1180, label: 'Jan 3' },
      { date: '2024-01-04', value: 1420, label: 'Jan 4' },
      { date: '2024-01-05', value: 1680, label: 'Jan 5' },
      { date: '2024-01-06', value: 1540, label: 'Jan 6' },
      { date: '2024-01-07', value: 1720, label: 'Jan 7' },
    ],
  };

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real application, this would be an API call
      // const response = await fetch('/api/dashboard');
      // const data = await response.json();

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));

      setData(mockData);
      setLastRefresh(new Date());
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, [onRefresh]);

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh && !loading) {
      const intervalMs = REFRESH_INTERVALS[refreshInterval as keyof typeof REFRESH_INTERVALS] || REFRESH_INTERVALS[30];

      const intervalId = setInterval(() => {
        fetchDashboardData();
      }, intervalMs);

      setRefreshIntervalId(intervalId);

      return () => {
        if (intervalId) clearInterval(intervalId);
      };
    }

    return () => {
      if (refreshIntervalId) clearInterval(refreshIntervalId);
    };
  }, [autoRefresh, refreshInterval, loading, fetchDashboardData]);

  const handleManualRefresh = () => {
    fetchDashboardData();
  };

  const getIcon = (iconName: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      users: <Users className="w-6 h-6" />,
      briefcase: <Briefcase className="w-6 h-6" />,
      target: <Target className="w-6 h-6" />,
      mail: <Mail className="w-6 h-6" />,
    };
    return iconMap[iconName] || <Activity className="w-6 h-6" />;
  };

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getActivityIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      user_registered: <Users className="w-4 h-4 text-blue-600" />,
      job_posted: <Briefcase className="w-4 h-4 text-green-600" />,
      match_created: <Target className="w-4 h-4 text-purple-600" />,
      application_submitted: <Mail className="w-4 h-4 text-orange-600" />,
    };
    return iconMap[type] || <Activity className="w-4 h-4 text-gray-600" />;
  };

  if (loading && !data) {
    return (
      <div className={clsx('p-8 text-center', className)} data-testid={testId}>
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p className="text-gray-600">Loading dashboard...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className={clsx('p-8 text-center', className)} data-testid={testId}>
        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={handleManualRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', className)} data-testid={testId}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={clsx('w-4 h-4', { 'animate-spin': loading })} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data?.metrics.map((metric) => (
          <MetricCard
            key={metric.id}
            metric={metric}
            showTrend={true}
          />
        ))}
      </div>

      {/* System Health */}
      {showSystemHealth && data?.systemHealth && (
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
            <div className="flex items-center space-x-2">
              <StatusIndicator
                status={data.systemHealth.status === 'healthy' ? 'up' : 'down'}
                size="sm"
              />
              <span className="text-sm text-gray-600">
                {data.systemHealth.uptime}% uptime
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.systemHealth.services.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 border rounded-md"
              >
                <div className="flex items-center space-x-3">
                  <StatusIndicator status={service.status} size="sm" />
                  <span className="text-sm font-medium text-gray-900">{service.name}</span>
                </div>
                {service.responseTime && (
                  <span className="text-xs text-gray-500">
                    {service.responseTime}ms
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      {showCharts && data?.chartData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Matches</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg border shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Overview</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Batch Jobs and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Batch Jobs */}
        {showBatchJobs && data?.batchJobs && (
          <div className="bg-white rounded-lg border shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Batch Jobs</h3>
            <div className="space-y-4">
              {data.batchJobs.map((job) => (
                <div key={job.id} className="border rounded-md p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <StatusIndicator status={job.status} size="sm" />
                      <span className="font-medium text-gray-900">{job.name}</span>
                    </div>
                    <span className="text-xs text-gray-500 capitalize">{job.type}</span>
                  </div>

                  {job.progress !== undefined && job.status === 'running' && (
                    <div className="mb-2">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Progress: {job.progress}%</span>
                        <span>{job.processedItems?.toLocaleString()} / {job.totalItems?.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {job.duration && (
                    <div className="text-xs text-gray-600">
                      Duration: {formatDuration(job.duration)}
                    </div>
                  )}

                  {job.error && (
                    <div className="text-xs text-red-600 mt-2">
                      Error: {job.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {data?.recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3">
                {getActivityIcon(activity.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500">
                    {new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(
                      Math.floor((activity.timestamp.getTime() - Date.now()) / 1000 / 60),
                      'minute'
                    )}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}