// Example usage of Dashboard and SqlEditor components
// This file demonstrates how to use the components and helps verify they compile correctly

import { DashboardData, SqlQueryResult, SqlTemplate } from '@/types';
import Dashboard from './index';
import SqlEditor from '../SqlEditor';
import MetricCard from './MetricCard';
import StatusIndicator from './StatusIndicator';

// Example Dashboard usage
export const dashboardExample = {
  // Basic dashboard with auto-refresh
  basicDashboard: () => {
    return Dashboard({
      autoRefresh: true,
      refreshInterval: 30,
      showBatchJobs: true,
      showSystemHealth: true,
      showCharts: true,
    });
  },

  // Dashboard with custom refresh handler
  customDashboard: () => {
    const handleRefresh = () => {
      console.log('Dashboard refreshed');
    };

    return Dashboard({
      autoRefresh: false,
      onRefresh: handleRefresh,
    });
  },
};

// Example SqlEditor usage
export const sqlEditorExample = {
  // Basic SQL editor
  basicEditor: () => {
    const handleQueryExecute = async (query: string): Promise<SqlQueryResult> => {
      // Simulate API call
      return {
        columns: [
          { name: 'id', type: 'integer' },
          { name: 'name', type: 'varchar' },
        ],
        rows: [
          { id: 1, name: 'Test User' },
        ],
        rowCount: 1,
        executionTime: 150,
        query,
      };
    };

    return SqlEditor({
      onQueryExecute: handleQueryExecute,
      initialQuery: 'SELECT * FROM users LIMIT 10',
      height: '400px',
      showHistory: true,
      autoComplete: true,
    });
  },

  // Read-only editor with custom templates
  readOnlyEditor: () => {
    const customTemplates: SqlTemplate[] = [
      {
        id: 'custom1',
        name: 'Custom Query',
        description: 'A custom query example',
        category: 'general',
        query: 'SELECT COUNT(*) FROM custom_table',
      },
    ];

    return SqlEditor({
      readOnly: true,
      templates: customTemplates,
      initialQuery: 'SELECT 1',
    });
  },
};

// Example metric cards
export const metricCardExamples = {
  // Trending up metric
  upTrendingMetric: () => {
    return MetricCard({
      metric: {
        id: '1',
        label: 'Active Users',
        value: '1,234',
        previousValue: '1,100',
        trend: 'up',
        change: 12.2,
        format: 'number',
        icon: 'users',
        color: 'blue',
      },
      showTrend: true,
      size: 'md',
    });
  },

  // Currency metric
  currencyMetric: () => {
    return MetricCard({
      metric: {
        id: '2',
        label: 'Revenue',
        value: 125000,
        previousValue: 118000,
        trend: 'up',
        change: 5.9,
        format: 'currency',
        icon: 'dollar',
        color: 'green',
      },
      size: 'lg',
      onClick: () => console.log('Revenue clicked'),
    });
  },
};

// Example status indicators
export const statusIndicatorExamples = {
  // Service status indicators
  serviceStatuses: () => {
    const statuses = ['up', 'down', 'degraded'] as const;

    return statuses.map(status =>
      StatusIndicator({
        status,
        size: 'md',
        showLabel: true,
      })
    );
  },

  // Job status indicators
  jobStatuses: () => {
    const statuses = ['running', 'completed', 'failed', 'pending'] as const;

    return statuses.map(status =>
      StatusIndicator({
        status,
        size: 'sm',
        showLabel: false,
        label: `Job ${status}`,
      })
    );
  },
};

// Type validation - these should all compile without errors
export type ComponentValidation = {
  dashboard: ReturnType<typeof dashboardExample.basicDashboard>;
  sqlEditor: ReturnType<typeof sqlEditorExample.basicEditor>;
  metricCard: ReturnType<typeof metricCardExamples.upTrendingMetric>;
  statusIndicator: ReturnType<typeof statusIndicatorExamples.serviceStatuses>[0];
};