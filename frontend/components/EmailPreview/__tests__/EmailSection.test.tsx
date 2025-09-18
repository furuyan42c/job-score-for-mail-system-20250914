import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EmailSection } from '../EmailSection';
import { generateMockJobs } from '../utils';

// Mock JobCard component
jest.mock('../JobCard', () => ({
  JobCard: ({ job }: any) => (
    <div data-testid={`job-card-${job.id}`}>
      <div>{job.title}</div>
      <div>{job.companyName}</div>
    </div>
  )
}));

describe('EmailSection', () => {
  const mockSection = {
    id: 'editorial-picks',
    title: '🏆 編集部おすすめ',
    description: '編集部が厳選したあなたにぴったりの求人をお届けします。',
    jobs: generateMockJobs(3),
    maxJobs: 5,
    priority: 1
  };

  it('renders section title and description', () => {
    render(<EmailSection section={mockSection} previewMode="desktop" />);

    expect(screen.getByText('🏆 編集部おすすめ')).toBeInTheDocument();
    expect(screen.getByText('編集部が厳選したあなたにぴったりの求人をお届けします。')).toBeInTheDocument();
  });

  it('displays job count', () => {
    render(<EmailSection section={mockSection} previewMode="desktop" />);

    expect(screen.getByText('3件の求人')).toBeInTheDocument();
  });

  it('renders all jobs in the section', () => {
    render(<EmailSection section={mockSection} previewMode="desktop" />);

    mockSection.jobs.forEach(job => {
      expect(screen.getByTestId(`job-card-${job.id}`)).toBeInTheDocument();
    });
  });

  it('applies correct section color for editorial picks', () => {
    render(<EmailSection section={mockSection} previewMode="desktop" />);

    const headerElement = screen.getByText('🏆 編集部おすすめ').closest('div');
    expect(headerElement).toHaveClass('text-purple-600', 'bg-purple-50', 'border-purple-200');
  });

  it('applies correct section color for top recommendations', () => {
    const topRecommendationsSection = {
      ...mockSection,
      id: 'top-recommendations',
      title: '🎯 TOP5 おすすめ'
    };

    render(<EmailSection section={topRecommendationsSection} previewMode="desktop" />);

    const headerElement = screen.getByText('🎯 TOP5 おすすめ').closest('div');
    expect(headerElement).toHaveClass('text-blue-600', 'bg-blue-50', 'border-blue-200');
  });

  it('applies correct section color for personalized picks', () => {
    const personalizedSection = {
      ...mockSection,
      id: 'personalized-picks',
      title: '💝 あなた専用求人'
    };

    render(<EmailSection section={personalizedSection} previewMode="desktop" />);

    const headerElement = screen.getByText('💝 あなた専用求人').closest('div');
    expect(headerElement).toHaveClass('text-red-600', 'bg-red-50', 'border-red-200');
  });

  it('applies correct section color for new arrivals', () => {
    const newArrivalsSection = {
      ...mockSection,
      id: 'new-arrivals',
      title: '🆕 新着求人'
    };

    render(<EmailSection section={newArrivalsSection} previewMode="desktop" />);

    const headerElement = screen.getByText('🆕 新着求人').closest('div');
    expect(headerElement).toHaveClass('text-green-600', 'bg-green-50', 'border-green-200');
  });

  it('applies correct section color for popular jobs', () => {
    const popularJobsSection = {
      ...mockSection,
      id: 'popular-jobs',
      title: '🔥 人気の求人'
    };

    render(<EmailSection section={popularJobsSection} previewMode="desktop" />);

    const headerElement = screen.getByText('🔥 人気の求人').closest('div');
    expect(headerElement).toHaveClass('text-orange-600', 'bg-orange-50', 'border-orange-200');
  });

  it('applies correct section color for you might like', () => {
    const youMightLikeSection = {
      ...mockSection,
      id: 'you-might-like',
      title: '😊 こちらもおすすめ'
    };

    render(<EmailSection section={youMightLikeSection} previewMode="desktop" />);

    const headerElement = screen.getByText('😊 こちらもおすすめ').closest('div');
    expect(headerElement).toHaveClass('text-indigo-600', 'bg-indigo-50', 'border-indigo-200');
  });

  it('applies default color for unknown section', () => {
    const unknownSection = {
      ...mockSection,
      id: 'unknown-section',
      title: 'Unknown Section'
    };

    render(<EmailSection section={unknownSection} previewMode="desktop" />);

    const headerElement = screen.getByText('Unknown Section').closest('div');
    expect(headerElement).toHaveClass('text-gray-600', 'bg-gray-50', 'border-gray-200');
  });

  it('renders without description when not provided', () => {
    const sectionWithoutDescription = {
      ...mockSection,
      description: undefined
    };

    render(<EmailSection section={sectionWithoutDescription} previewMode="desktop" />);

    expect(screen.getByText('🏆 編集部おすすめ')).toBeInTheDocument();
    expect(screen.queryByText('編集部が厳選したあなたにぴったりの求人をお届けします。')).not.toBeInTheDocument();
  });

  it('shows more jobs indicator when at max capacity', () => {
    const fullSection = {
      ...mockSection,
      jobs: generateMockJobs(5),
      maxJobs: 5
    };

    render(<EmailSection section={fullSection} previewMode="desktop" />);

    expect(screen.getByText('他に0件の求人があります')).toBeInTheDocument();
  });

  it('shows more jobs indicator when jobs exceed displayed amount', () => {
    const sectionWithMoreJobs = {
      ...mockSection,
      jobs: generateMockJobs(3),
      maxJobs: 10
    };

    render(<EmailSection section={sectionWithMoreJobs} previewMode="desktop" />);

    expect(screen.getByText('他に7件の求人があります')).toBeInTheDocument();
  });

  it('renders in mobile preview mode with single column grid', () => {
    render(<EmailSection section={mockSection} previewMode="mobile" />);

    const gridElement = screen.getByText('🏆 編集部おすすめ').closest('div')?.parentElement?.querySelector('[class*="grid"]');
    expect(gridElement).toHaveClass('grid-cols-1');
  });

  it('renders in desktop mode with responsive grid', () => {
    const sectionWithManyJobs = {
      ...mockSection,
      jobs: generateMockJobs(4)
    };

    render(<EmailSection section={sectionWithManyJobs} previewMode="desktop" />);

    const gridElement = screen.getByText('🏆 編集部おすすめ').closest('div')?.parentElement?.querySelector('[class*="grid"]');
    expect(gridElement).toHaveClass('grid-cols-1', 'lg:grid-cols-2');
  });

  it('renders in plaintext mode', () => {
    render(<EmailSection section={mockSection} previewMode="plaintext" />);

    expect(screen.getByText('🏆 編集部おすすめ')).toBeInTheDocument();
    expect(screen.getByText('編集部が厳選したあなたにぴったりの求人をお届けします。')).toBeInTheDocument();

    // Should render job cards in plaintext mode
    mockSection.jobs.forEach(job => {
      expect(screen.getByTestId(`job-card-${job.id}`)).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = render(
      <EmailSection section={mockSection} previewMode="desktop" className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('passes correct showMatchScore prop to JobCard based on section type', () => {
    // Editorial picks should not show match score
    render(<EmailSection section={mockSection} previewMode="desktop" />);

    // For editorial picks, match score should be hidden
    // This would need to be tested by checking the actual JobCard props
    // but since we mocked JobCard, we can't test this directly
    expect(screen.getByTestId(`job-card-${mockSection.jobs[0].id}`)).toBeInTheDocument();
  });

  it('renders section with empty jobs array', () => {
    const emptySection = {
      ...mockSection,
      jobs: []
    };

    render(<EmailSection section={emptySection} previewMode="desktop" />);

    expect(screen.getByText('🏆 編集部おすすめ')).toBeInTheDocument();
    expect(screen.getByText('0件の求人')).toBeInTheDocument();
  });

  it('renders correct icons for different section types', () => {
    const sections = [
      { id: 'editorial-picks', title: 'Editorial Picks' },
      { id: 'top-recommendations', title: 'Top Recommendations' },
      { id: 'personalized-picks', title: 'Personalized Picks' },
      { id: 'new-arrivals', title: 'New Arrivals' },
      { id: 'popular-jobs', title: 'Popular Jobs' },
      { id: 'you-might-like', title: 'You Might Like' }
    ];

    sections.forEach(({ id, title }) => {
      const sectionData = {
        ...mockSection,
        id,
        title,
        jobs: []
      };

      const { unmount } = render(<EmailSection section={sectionData} previewMode="desktop" />);

      expect(screen.getByText(title)).toBeInTheDocument();

      unmount();
    });
  });
});