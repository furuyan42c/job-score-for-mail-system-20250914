import type { Meta, StoryObj } from '@storybook/react';
import { ScoreDisplay } from '@/components/molecules';
import { MatchFactor } from '@/types';

const mockFactors: MatchFactor[] = [
  { type: 'skills', weight: 0.4, score: 90, description: 'Skills Match - React, TypeScript, Next.js' },
  { type: 'experience', weight: 0.3, score: 85, description: 'Experience Level - Senior' },
  { type: 'location', weight: 0.2, score: 75, description: 'Location Preference - Hybrid work' },
  { type: 'salary', weight: 0.1, score: 95, description: 'Salary Range - Within expectations' }
];

const meta = {
  title: 'Molecules/ScoreDisplay',
  component: ScoreDisplay,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Displays match scores with visual progress indicators and optional factor breakdown.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'compact', 'detailed'],
      description: 'Visual variant of the score display',
    },
    showPercentage: {
      control: 'boolean',
      description: 'Whether to show percentage in the circle',
    },
    showLabel: {
      control: 'boolean',
      description: 'Whether to show the score label',
    },
  },
} satisfies Meta<typeof ScoreDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    score: 85,
    variant: 'default',
  },
};

export const Compact: Story = {
  args: {
    score: 75,
    variant: 'compact',
  },
};

export const Detailed: Story = {
  args: {
    score: 85,
    variant: 'detailed',
    factors: mockFactors,
  },
  parameters: {
    layout: 'padded',
  },
};

export const ExcellentScore: Story = {
  args: {
    score: 95,
    factors: [
      { type: 'skills', weight: 0.4, score: 98, description: 'Perfect Skills Match' },
      { type: 'experience', weight: 0.3, score: 95, description: 'Ideal Experience Level' },
      { type: 'location', weight: 0.2, score: 90, description: 'Preferred Location' },
      { type: 'salary', weight: 0.1, score: 100, description: 'Salary Expectations Met' }
    ],
    variant: 'detailed',
  },
  parameters: {
    layout: 'padded',
  },
};

export const PoorScore: Story = {
  args: {
    score: 35,
    factors: [
      { type: 'skills', weight: 0.4, score: 40, description: 'Partial Skills Match' },
      { type: 'experience', weight: 0.3, score: 25, description: 'Experience Level Mismatch' },
      { type: 'location', weight: 0.2, score: 50, description: 'Location Not Ideal' },
      { type: 'salary', weight: 0.1, score: 20, description: 'Salary Below Expectations' }
    ],
    variant: 'detailed',
  },
  parameters: {
    layout: 'padded',
  },
};

export const WithoutLabel: Story = {
  args: {
    score: 72,
    showLabel: false,
  },
};

export const WithoutPercentage: Story = {
  args: {
    score: 85,
    maxScore: 100,
    showPercentage: false,
  },
};

export const ScoreComparison: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Score Ranges</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <ScoreDisplay score={95} variant="compact" />
            <p className="mt-2 text-sm text-gray-600">Excellent (90+)</p>
          </div>
          <div className="text-center">
            <ScoreDisplay score={80} variant="compact" />
            <p className="mt-2 text-sm text-gray-600">Good (75-89)</p>
          </div>
          <div className="text-center">
            <ScoreDisplay score={65} variant="compact" />
            <p className="mt-2 text-sm text-gray-600">Fair (60-74)</p>
          </div>
          <div className="text-center">
            <ScoreDisplay score={35} variant="compact" />
            <p className="mt-2 text-sm text-gray-600">Poor (0-59)</p>
          </div>
        </div>
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Comparison of different score ranges with their visual representations.',
      },
    },
  },
};