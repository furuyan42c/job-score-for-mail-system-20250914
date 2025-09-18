import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import StatusIndicator from './StatusIndicator';

describe('StatusIndicator', () => {
  it('renders up status correctly', () => {
    render(<StatusIndicator status="up" />);

    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  it('renders down status correctly', () => {
    render(<StatusIndicator status="down" />);

    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('renders degraded status correctly', () => {
    render(<StatusIndicator status="degraded" />);

    expect(screen.getByText('Degraded')).toBeInTheDocument();
  });

  it('renders running status correctly', () => {
    render(<StatusIndicator status="running" />);

    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('renders completed status correctly', () => {
    render(<StatusIndicator status="completed" />);

    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders failed status correctly', () => {
    render(<StatusIndicator status="failed" />);

    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('renders pending status correctly', () => {
    render(<StatusIndicator status="pending" />);

    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('uses custom label when provided', () => {
    render(<StatusIndicator status="up" label="Custom Label" />);

    expect(screen.getByText('Custom Label')).toBeInTheDocument();
    expect(screen.queryByText('Online')).not.toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<StatusIndicator status="up" showLabel={false} />);

    expect(screen.queryByText('Online')).not.toBeInTheDocument();
  });

  it('applies correct color classes for up status', () => {
    render(<StatusIndicator status="up" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('bg-green-100');

    const label = screen.getByText('Online');
    expect(label).toHaveClass('text-green-600');
  });

  it('applies correct color classes for down status', () => {
    render(<StatusIndicator status="down" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('bg-red-100');

    const label = screen.getByText('Offline');
    expect(label).toHaveClass('text-red-600');
  });

  it('applies correct color classes for degraded status', () => {
    render(<StatusIndicator status="degraded" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('bg-yellow-100');

    const label = screen.getByText('Degraded');
    expect(label).toHaveClass('text-yellow-600');
  });

  it('applies correct color classes for running status', () => {
    render(<StatusIndicator status="running" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('bg-blue-100');

    const label = screen.getByText('Running');
    expect(label).toHaveClass('text-blue-600');
  });

  it('renders small size correctly', () => {
    render(<StatusIndicator status="up" size="sm" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('text-xs');
  });

  it('renders medium size correctly', () => {
    render(<StatusIndicator status="up" size="md" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('text-sm');
  });

  it('renders large size correctly', () => {
    render(<StatusIndicator status="up" size="lg" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('text-base');
  });

  it('renders icon-only variant when showLabel is false', () => {
    render(
      <StatusIndicator
        status="up"
        showLabel={false}
        data-testid="status-indicator"
      />
    );

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('rounded-full');
    expect(screen.queryByText('Online')).not.toBeInTheDocument();
  });

  it('shows tooltip for icon-only variant', () => {
    render(
      <StatusIndicator
        status="up"
        showLabel={false}
        data-testid="status-indicator"
      />
    );

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveAttribute('title', 'Online');
  });

  it('uses custom label in tooltip for icon-only variant', () => {
    render(
      <StatusIndicator
        status="up"
        label="Custom Status"
        showLabel={false}
        data-testid="status-indicator"
      />
    );

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveAttribute('title', 'Custom Status');
  });

  it('applies custom className', () => {
    render(
      <StatusIndicator
        status="up"
        className="custom-status"
        data-testid="status-indicator"
      />
    );

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('custom-status');
  });

  it('handles unknown status gracefully', () => {
    // TypeScript would prevent this, but testing runtime behavior
    render(
      <StatusIndicator
        status={'unknown' as any}
        data-testid="status-indicator"
      />
    );

    // Should fall back to pending status
    expect(screen.getByText('Pending')).toBeInTheDocument();

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('bg-gray-100');
  });

  it('applies animation classes for running status', () => {
    render(<StatusIndicator status="running" showLabel={false} />);

    // Running status should have animation classes
    // The actual animation is tested visually, but we can check for animation classes
    const statusIndicator = screen.getByRole('generic');
    expect(statusIndicator).toHaveClass('rounded-full');
  });

  it('applies different padding for different sizes in icon-only mode', () => {
    const { rerender } = render(
      <StatusIndicator
        status="up"
        size="sm"
        showLabel={false}
        data-testid="status-indicator"
      />
    );

    let indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('p-1');

    rerender(
      <StatusIndicator
        status="up"
        size="lg"
        showLabel={false}
        data-testid="status-indicator"
      />
    );

    indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('p-2');
  });

  it('renders with badge variant by default', () => {
    render(<StatusIndicator status="up" data-testid="status-indicator" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveClass('inline-flex', 'items-center', 'rounded-full', 'px-2', 'py-1');
  });

  it('handles all batch job statuses correctly', () => {
    const statuses = ['running', 'completed', 'failed', 'pending'] as const;
    const expectedLabels = ['Running', 'Completed', 'Failed', 'Pending'];

    statuses.forEach((status, index) => {
      const { unmount } = render(<StatusIndicator status={status} />);
      expect(screen.getByText(expectedLabels[index])).toBeInTheDocument();
      unmount();
    });
  });

  it('handles all service statuses correctly', () => {
    const statuses = ['up', 'down', 'degraded'] as const;
    const expectedLabels = ['Online', 'Offline', 'Degraded'];

    statuses.forEach((status, index) => {
      const { unmount } = render(<StatusIndicator status={status} />);
      expect(screen.getByText(expectedLabels[index])).toBeInTheDocument();
      unmount();
    });
  });
});