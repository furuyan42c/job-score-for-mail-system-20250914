import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { JobCard } from '@/components/molecules';
import { Job } from '@/types';

const mockJob: Job = {
  id: '1',
  title: 'Senior Frontend Developer',
  company: 'TechCorp Inc.',
  description: 'We are looking for a skilled Frontend Developer to join our dynamic team and help build the next generation of web applications. You will work with React, TypeScript, and modern tools.',
  requirements: ['React', 'TypeScript', 'Next.js', '5+ years experience'],
  location: 'San Francisco, CA',
  locationType: 'hybrid',
  salary: { min: 120000, max: 160000, currency: 'USD', period: 'year' },
  experienceLevel: 'senior',
  jobType: 'full-time',
  skills: ['React', 'TypeScript', 'Next.js', 'GraphQL', 'Node.js'],
  benefits: ['Health Insurance', 'Remote Work', 'Stock Options', 'Unlimited PTO'],
  postedAt: new Date('2024-01-15'),
  status: 'active',
  applicantCount: 45,
  views: 230,
  companyLogo: 'https://via.placeholder.com/64x64?text=TC',
  companySize: 'medium',
  industry: 'Technology'
};

const meta = {
  title: 'Molecules/JobCard',
  component: JobCard,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A compact job display card showing essential job information with actions.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'compact', 'featured'],
      description: 'Visual variant of the job card',
    },
    showActions: {
      control: 'boolean',
      description: 'Whether to show action buttons',
    },
  },
  args: {
    job: mockJob,
    onClick: fn(),
    onSave: fn(),
    onApply: fn(),
  },
} satisfies Meta<typeof JobCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    variant: 'default',
  },
};

export const Compact: Story = {
  args: {
    variant: 'compact',
  },
};

export const Featured: Story = {
  args: {
    variant: 'featured',
  },
};

export const WithoutActions: Story = {
  args: {
    showActions: false,
  },
};

export const RemoteJob: Story = {
  args: {
    job: {
      ...mockJob,
      location: 'Remote',
      locationType: 'remote',
      company: 'Remote Corp',
    },
  },
};

export const EntryLevelJob: Story = {
  args: {
    job: {
      ...mockJob,
      title: 'Junior Frontend Developer',
      experienceLevel: 'entry',
      salary: { min: 60000, max: 80000, currency: 'USD', period: 'year' },
      applicantCount: 123,
    },
  },
};

export const ContractJob: Story = {
  args: {
    job: {
      ...mockJob,
      title: 'Contract React Developer',
      jobType: 'contract',
      salary: { min: 80, max: 120, currency: 'USD', period: 'hour' },
      benefits: ['Flexible Schedule', 'Remote Work'],
    },
  },
};

export const StartupJob: Story = {
  args: {
    job: {
      ...mockJob,
      company: 'StartupXYZ',
      companySize: 'startup',
      industry: 'Fintech',
      skills: ['React', 'TypeScript', 'Web3', 'Blockchain'],
      benefits: ['Equity', 'Remote Work', 'Learning Budget'],
    },
  },
};

export const JobGrid: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <JobCard job={mockJob} variant="compact" />
      <JobCard
        job={{
          ...mockJob,
          id: '2',
          title: 'Backend Engineer',
          skills: ['Node.js', 'Python', 'PostgreSQL'],
          company: 'DataCorp',
        }}
        variant="compact"
      />
      <JobCard
        job={{
          ...mockJob,
          id: '3',
          title: 'Full Stack Developer',
          locationType: 'remote',
          location: 'Remote',
          company: 'RemoteFirst',
        }}
        variant="compact"
      />
      <JobCard
        job={{
          ...mockJob,
          id: '4',
          title: 'DevOps Engineer',
          skills: ['AWS', 'Docker', 'Kubernetes'],
          company: 'CloudTech',
        }}
        variant="compact"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Grid layout of job cards showing different job types.',
      },
    },
  },
};