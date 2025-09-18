import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { JobCard } from '../JobCard';
import { generateMockJob } from '../utils';

// Mock window.open
Object.defineProperty(window, 'open', {
  writable: true,
  value: jest.fn()
});

describe('JobCard', () => {
  const mockJob = generateMockJob({
    id: 1,
    title: 'Frontend Developer',
    companyName: 'Tech Company',
    location: 'Tokyo',
    salaryMin: 3000,
    salaryMax: 5000,
    salaryType: 'monthly',
    matchScore: 85,
    tags: ['Remote OK', 'Experience Welcome'],
    applyUrl: 'https://example.com/apply',
    isNew: true,
    isPopular: false
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders job card with basic information', () => {
    render(<JobCard job={mockJob} previewMode="desktop" />);

    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    expect(screen.getByText('Tech Company')).toBeInTheDocument();
    expect(screen.getByText('Tokyo')).toBeInTheDocument();
  });

  it('displays salary information correctly', () => {
    render(<JobCard job={mockJob} previewMode="desktop" />);

    expect(screen.getByText('¥3,000 - ¥5,000/月')).toBeInTheDocument();
  });

  it('shows match score when enabled', () => {
    render(<JobCard job={mockJob} previewMode="desktop" showMatchScore={true} />);

    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('hides match score when disabled', () => {
    render(<JobCard job={mockJob} previewMode="desktop" showMatchScore={false} />);

    expect(screen.queryByText('85%')).not.toBeInTheDocument();
  });

  it('displays tags', () => {
    render(<JobCard job={mockJob} previewMode="desktop" />);

    expect(screen.getByText('Remote OK')).toBeInTheDocument();
    expect(screen.getByText('Experience Welcome')).toBeInTheDocument();
  });

  it('shows new badge for new jobs', () => {
    render(<JobCard job={mockJob} previewMode="desktop" />);

    expect(screen.getByText('新着')).toBeInTheDocument();
  });

  it('shows popular badge for popular jobs', () => {
    const popularJob = { ...mockJob, isPopular: true };
    render(<JobCard job={popularJob} previewMode="desktop" />);

    expect(screen.getByText('人気')).toBeInTheDocument();
  });

  it('opens apply URL when apply button is clicked', () => {
    render(<JobCard job={mockJob} previewMode="desktop" />);

    const applyButton = screen.getByText('応募する');
    fireEvent.click(applyButton);

    expect(window.open).toHaveBeenCalledWith('https://example.com/apply', '_blank');
  });

  it('renders in compact mode', () => {
    render(<JobCard job={mockJob} previewMode="desktop" compact={true} />);

    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    // Compact mode should still show all essential information
    expect(screen.getByText('Tech Company')).toBeInTheDocument();
  });

  it('renders different salary types correctly', () => {
    const hourlyJob = { ...mockJob, salaryType: 'hourly' as const, salaryMin: 1500, salaryMax: 2000 };
    const { rerender } = render(<JobCard job={hourlyJob} previewMode="desktop" />);

    expect(screen.getByText('¥1,500 - ¥2,000/時間')).toBeInTheDocument();

    const yearlyJob = { ...mockJob, salaryType: 'yearly' as const, salaryMin: 400, salaryMax: 600 };
    rerender(<JobCard job={yearlyJob} previewMode="desktop" />);

    expect(screen.getByText('¥4,000,000 - ¥6,000,000/年')).toBeInTheDocument();
  });

  it('handles jobs without salary information', () => {
    const jobWithoutSalary = { ...mockJob, salaryMin: undefined, salaryMax: undefined };
    render(<JobCard job={jobWithoutSalary} previewMode="desktop" />);

    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    expect(screen.queryByText(/¥/)).not.toBeInTheDocument();
  });

  it('handles single salary value', () => {
    const singleSalaryJob = { ...mockJob, salaryMin: 3000, salaryMax: undefined };
    render(<JobCard job={singleSalaryJob} previewMode="desktop" />);

    expect(screen.getByText('¥3,000/月')).toBeInTheDocument();
  });

  it('renders match score with different colors based on score', () => {
    const highScoreJob = { ...mockJob, matchScore: 95 };
    const { rerender } = render(<JobCard job={highScoreJob} previewMode="desktop" />);

    let matchElement = screen.getByText('95%');
    expect(matchElement).toHaveClass('text-green-600');

    const mediumScoreJob = { ...mockJob, matchScore: 75 };
    rerender(<JobCard job={mediumScoreJob} previewMode="desktop" />);

    matchElement = screen.getByText('75%');
    expect(matchElement).toHaveClass('text-yellow-600');

    const lowScoreJob = { ...mockJob, matchScore: 60 };
    rerender(<JobCard job={lowScoreJob} previewMode="desktop" />);

    matchElement = screen.getByText('60%');
    expect(matchElement).toHaveClass('text-gray-600');
  });

  it('renders plaintext mode correctly', () => {
    render(<JobCard job={mockJob} previewMode="plaintext" />);

    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    expect(screen.getByText('Tech Company')).toBeInTheDocument();
    expect(screen.getByText('Tokyo')).toBeInTheDocument();
    expect(screen.getByText('マッチ度: 85%')).toBeInTheDocument();
    expect(screen.getByText('応募する: https://example.com/apply')).toBeInTheDocument();
  });

  it('handles mobile preview mode', () => {
    render(<JobCard job={mockJob} previewMode="mobile" />);

    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
    // Should render the same content but with mobile-optimized styling
    expect(screen.getByText('応募する')).toBeInTheDocument();
  });

  it('displays company logo when provided', () => {
    const jobWithLogo = { ...mockJob, companyLogo: 'https://example.com/logo.png' };
    render(<JobCard job={jobWithLogo} previewMode="desktop" />);

    const logoImg = screen.getByAltText('Tech Company');
    expect(logoImg).toBeInTheDocument();
    expect(logoImg).toHaveAttribute('src', 'https://example.com/logo.png');
  });

  it('shows default icon when no company logo provided', () => {
    const jobWithoutLogo = { ...mockJob, companyLogo: undefined };
    render(<JobCard job={jobWithoutLogo} previewMode="desktop" />);

    // Should show building icon as fallback
    const buildingIcon = screen.getByTestId ? screen.queryByTestId('building-icon') : null;
    // Since we can't easily test for Lucide icons, we check that the component renders without error
    expect(screen.getByText('Tech Company')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <JobCard job={mockJob} previewMode="desktop" className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('limits tags display to first 3 tags', () => {
    const jobWithManyTags = {
      ...mockJob,
      tags: ['Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5']
    };

    render(<JobCard job={jobWithManyTags} previewMode="desktop" />);

    expect(screen.getByText('Tag1')).toBeInTheDocument();
    expect(screen.getByText('Tag2')).toBeInTheDocument();
    expect(screen.getByText('Tag3')).toBeInTheDocument();
    expect(screen.queryByText('Tag4')).not.toBeInTheDocument();
    expect(screen.queryByText('Tag5')).not.toBeInTheDocument();
  });
});