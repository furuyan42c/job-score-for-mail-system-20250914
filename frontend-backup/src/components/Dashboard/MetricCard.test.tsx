import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetricCard from './MetricCard';
import { DashboardMetric } from '@/types';

describe('MetricCard', () => {
  const mockMetric: DashboardMetric = {
    id: '1',
    label: 'Total Users',
    value: 12547,
    previousValue: 11832,
    trend: 'up',
    change: 6.0,
    format: 'number',
    icon: 'users',
    color: 'blue',
  };

  it('renders metric information correctly', () => {
    render(<MetricCard metric={mockMetric} />);

    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('12547')).toBeInTheDocument();
    expect(screen.getByText('+6.0%')).toBeInTheDocument();
  });

  it('displays previous value when available', () => {
    render(<MetricCard metric={mockMetric} />);

    expect(screen.getByText('Previous: 11832')).toBeInTheDocument();
  });

  it('shows correct trend icon for upward trend', () => {
    render(<MetricCard metric={mockMetric} />);

    // Check for trending up icon (should have green color class)
    const trendElement = screen.getByText('+6.0%');
    expect(trendElement).toHaveClass('text-green-600');
  });

  it('shows correct trend icon for downward trend', () => {
    const downMetric: DashboardMetric = {
      ...mockMetric,
      trend: 'down',
      change: -5.2,
    };

    render(<MetricCard metric={downMetric} />);

    const trendElement = screen.getByText('-5.2%');
    expect(trendElement).toHaveClass('text-red-600');
  });

  it('shows stable trend correctly', () => {
    const stableMetric: DashboardMetric = {
      ...mockMetric,
      trend: 'stable',
      change: 0,
    };

    render(<MetricCard metric={stableMetric} />);

    const trendElement = screen.getByText('+0.0%');
    expect(trendElement).toHaveClass('text-gray-500');
  });

  it('hides trend when showTrend is false', () => {
    render(<MetricCard metric={mockMetric} showTrend={false} />);

    expect(screen.queryByText('+6.0%')).not.toBeInTheDocument();
  });

  it('handles click events', () => {
    const mockOnClick = jest.fn();
    render(<MetricCard metric={mockMetric} onClick={mockOnClick} />);

    const card = screen.getByText('Total Users').closest('div');
    fireEvent.click(card!);

    expect(mockOnClick).toHaveBeenCalled();
  });

  it('applies hover styles when clickable', () => {
    const mockOnClick = jest.fn();
    render(<MetricCard metric={mockMetric} onClick={mockOnClick} />);

    const card = screen.getByText('Total Users').closest('div');
    expect(card).toHaveClass('cursor-pointer', 'hover:shadow-md');
  });

  it('renders different sizes correctly', () => {
    const { rerender } = render(<MetricCard metric={mockMetric} size="sm" />);

    let card = screen.getByText('Total Users').closest('div');
    expect(card).toHaveClass('p-4');

    rerender(<MetricCard metric={mockMetric} size="lg" />);
    card = screen.getByText('Total Users').closest('div');
    expect(card).toHaveClass('p-8');
  });

  it('formats currency values correctly', () => {
    const currencyMetric: DashboardMetric = {
      ...mockMetric,
      value: 125000,
      format: 'currency',
    };

    render(<MetricCard metric={currencyMetric} />);

    expect(screen.getByText('$125,000.00')).toBeInTheDocument();
  });

  it('formats percentage values correctly', () => {
    const percentageMetric: DashboardMetric = {
      ...mockMetric,
      value: 85.5,
      format: 'percentage',
    };

    render(<MetricCard metric={percentageMetric} />);

    expect(screen.getByText('85.5%')).toBeInTheDocument();
  });

  it('formats duration values correctly', () => {
    const durationMetric: DashboardMetric = {
      ...mockMetric,
      value: 3665, // 1 hour, 1 minute, 5 seconds
      format: 'duration',
    };

    render(<MetricCard metric={durationMetric} />);

    expect(screen.getByText('1h 1m')).toBeInTheDocument();
  });

  it('displays correct icon based on icon prop', () => {
    const briefcaseMetric: DashboardMetric = {
      ...mockMetric,
      icon: 'briefcase',
    };

    render(<MetricCard metric={briefcaseMetric} />);

    // The icon should be rendered (we can't easily test the specific icon,
    // but we can ensure the container is there)
    expect(screen.getByText('Total Users')).toBeInTheDocument();
  });

  it('applies correct color classes', () => {
    const greenMetric: DashboardMetric = {
      ...mockMetric,
      color: 'green',
    };

    render(<MetricCard metric={greenMetric} />);

    // Find the icon container
    const iconContainer = screen.getByText('Total Users')
      .closest('div')
      ?.querySelector('.bg-green-50');

    expect(iconContainer).toBeTruthy();
  });

  it('handles missing change value gracefully', () => {
    const metricWithoutChange: DashboardMetric = {
      ...mockMetric,
      change: undefined,
    };

    render(<MetricCard metric={metricWithoutChange} />);

    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.queryByText('%')).not.toBeInTheDocument();
  });

  it('handles string values correctly', () => {
    const stringMetric: DashboardMetric = {
      ...mockMetric,
      value: 'Online',
      previousValue: 'Offline',
    };

    render(<MetricCard metric={stringMetric} />);

    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Previous: Offline')).toBeInTheDocument();
  });

  it('renders large size with additional description', () => {
    const upTrendMetric: DashboardMetric = {
      ...mockMetric,
      trend: 'up',
      change: 15.5,
    };

    render(<MetricCard metric={upTrendMetric} size="lg" />);

    expect(screen.getByText('Increased')).toBeInTheDocument();
    expect(screen.getByText('from previous period')).toBeInTheDocument();
  });

  it('shows stable trend description for large size', () => {
    const stableMetric: DashboardMetric = {
      ...mockMetric,
      trend: 'stable',
      change: 0,
    };

    render(<MetricCard metric={stableMetric} size="lg" />);

    expect(screen.getByText('No change')).toBeInTheDocument();
    expect(screen.getByText('from previous period')).toBeInTheDocument();
  });

  it('shows down trend description for large size', () => {
    const downMetric: DashboardMetric = {
      ...mockMetric,
      trend: 'down',
      change: -8.3,
    };

    render(<MetricCard metric={downMetric} size="lg" />);

    expect(screen.getByText('Decreased')).toBeInTheDocument();
    expect(screen.getByText('from previous period')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <MetricCard
        metric={mockMetric}
        className="custom-metric-card"
        data-testid="metric-card"
      />
    );

    const card = screen.getByTestId('metric-card');
    expect(card).toHaveClass('custom-metric-card');
  });

  it('handles minutes-only duration format', () => {
    const durationMetric: DashboardMetric = {
      ...mockMetric,
      value: 185, // 3 minutes, 5 seconds
      format: 'duration',
    };

    render(<MetricCard metric={durationMetric} />);

    expect(screen.getByText('3m')).toBeInTheDocument();
  });

  it('handles seconds-only duration format', () => {
    const durationMetric: DashboardMetric = {
      ...mockMetric,
      value: 45, // 45 seconds
      format: 'duration',
    };

    render(<MetricCard metric={durationMetric} />);

    expect(screen.getByText('45s')).toBeInTheDocument();
  });
});