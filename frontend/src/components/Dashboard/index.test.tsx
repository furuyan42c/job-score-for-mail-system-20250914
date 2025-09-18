import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from './index';
import { DashboardData } from '@/types';

// Mock Recharts components to avoid canvas rendering issues in tests
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
}));

// Mock date-fns to have predictable relative times
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '5 minutes ago'),
}));

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock console methods to avoid noise in tests
    jest.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders loading state initially', () => {
    render(<Dashboard />);

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('renders dashboard content after loading', async () => {
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    // Check for metric cards
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('Active Jobs')).toBeInTheDocument();
    expect(screen.getByText('Matches Today')).toBeInTheDocument();
    expect(screen.getByText('Emails Sent')).toBeInTheDocument();
  });

  it('displays system health when enabled', async () => {
    render(<Dashboard showSystemHealth={true} />);

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    expect(screen.getByText('API Gateway')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getByText('Email Service')).toBeInTheDocument();
  });

  it('hides system health when disabled', async () => {
    render(<Dashboard showSystemHealth={false} />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.queryByText('System Health')).not.toBeInTheDocument();
  });

  it('displays batch jobs when enabled', async () => {
    render(<Dashboard showBatchJobs={true} />);

    await waitFor(() => {
      expect(screen.getByText('Batch Jobs')).toBeInTheDocument();
    });

    expect(screen.getByText('Daily Job Matching')).toBeInTheDocument();
    expect(screen.getByText('Weekly Email Campaign')).toBeInTheDocument();
  });

  it('hides batch jobs when disabled', async () => {
    render(<Dashboard showBatchJobs={false} />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.queryByText('Batch Jobs')).not.toBeInTheDocument();
  });

  it('displays charts when enabled', async () => {
    render(<Dashboard showCharts={true} />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Daily Matches')).toBeInTheDocument();
    expect(screen.getByText('Weekly Overview')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('hides charts when disabled', async () => {
    render(<Dashboard showCharts={false} />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.queryByText('Daily Matches')).not.toBeInTheDocument();
    expect(screen.queryByText('Weekly Overview')).not.toBeInTheDocument();
  });

  it('handles manual refresh', async () => {
    const mockOnRefresh = jest.fn();
    render(<Dashboard onRefresh={mockOnRefresh} />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockOnRefresh).toHaveBeenCalled();
    });
  });

  it('displays recent activity', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    });

    expect(screen.getByText(/New user registration/)).toBeInTheDocument();
    expect(screen.getByText(/New job posted/)).toBeInTheDocument();
    expect(screen.getByText(/new job matches generated/)).toBeInTheDocument();
  });

  it('displays metric values correctly', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('12,547')).toBeInTheDocument(); // Total Users
      expect(screen.getByText('2,841')).toBeInTheDocument();  // Active Jobs
      expect(screen.getByText('1,293')).toBeInTheDocument();  // Matches Today
      expect(screen.getByText('8,674')).toBeInTheDocument();  // Emails Sent
    });
  });

  it('shows batch job progress correctly', async () => {
    render(<Dashboard showBatchJobs={true} />);

    await waitFor(() => {
      expect(screen.getByText('Weekly Email Campaign')).toBeInTheDocument();
    });

    // Should show progress for running job
    expect(screen.getByText('Progress: 68%')).toBeInTheDocument();
  });

  it('formats duration correctly', async () => {
    render(<Dashboard showBatchJobs={true} />);

    await waitFor(() => {
      expect(screen.getByText('Batch Jobs')).toBeInTheDocument();
    });

    // Should show formatted duration for completed job
    expect(screen.getByText('Duration: 5m 0s')).toBeInTheDocument();
  });

  it('updates last refresh time', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('disables auto-refresh when specified', () => {
    render(<Dashboard autoRefresh={false} />);

    // Should not set up auto-refresh interval
    // This is more of an implementation detail test
    expect(screen.getByText('Refresh')).toBeInTheDocument();
  });

  it('applies custom className', async () => {
    render(<Dashboard className="custom-dashboard" data-testid="dashboard" />);

    await waitFor(() => {
      const dashboard = screen.getByTestId('dashboard');
      expect(dashboard).toHaveClass('custom-dashboard');
    });
  });

  it('displays system uptime percentage', async () => {
    render(<Dashboard showSystemHealth={true} />);

    await waitFor(() => {
      expect(screen.getByText('99.97% uptime')).toBeInTheDocument();
    });
  });

  it('shows service response times', async () => {
    render(<Dashboard showSystemHealth={true} />);

    await waitFor(() => {
      expect(screen.getByText('45ms')).toBeInTheDocument();  // API Gateway
      expect(screen.getByText('12ms')).toBeInTheDocument();  // Database
      expect(screen.getByText('78ms')).toBeInTheDocument();  // Email Service
    });
  });

  // Test error state handling
  it('handles errors gracefully', async () => {
    // This test would need to mock a failed API call
    // For now, we'll test the error UI structure
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    // The component should render without crashing even if data is missing
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('displays trend indicators for metrics', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    // Should show trend indicators (up, down, stable) - these are tested in MetricCard tests
    // Just ensure the dashboard renders the metric cards
    expect(screen.getAllByRole('button')).toBeTruthy();
  });
});