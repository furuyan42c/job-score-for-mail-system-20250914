'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/templates';
import { JobCard, ScoreDisplay } from '@/components/molecules';
import { Typography, Button, Badge, Avatar } from '@/components/atoms';
import { Job, JobMatch, Application, UserProfile } from '@/types';
import {
  TrendingUp,
  Briefcase,
  Eye,
  Heart,
  Calendar,
  Target,
  Users,
  Award
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';

// Mock data
const mockUser = {
  id: 'user1',
  email: 'john.doe@example.com',
  name: 'John Doe',
  avatar: '/images/avatar.jpg',
  createdAt: new Date(),
  updatedAt: new Date()
};

const mockProfile: UserProfile = {
  id: 'profile1',
  userId: 'user1',
  title: 'Senior Frontend Developer',
  bio: 'Passionate frontend developer with 5+ years of experience...',
  location: 'San Francisco, CA',
  skills: ['React', 'TypeScript', 'Next.js', 'GraphQL'],
  experience: 'senior',
  salaryExpectation: { min: 120000, max: 160000, currency: 'USD', period: 'year' },
  preferences: {
    jobTypes: ['full-time'],
    locationTypes: ['remote', 'hybrid'],
    industries: ['Technology'],
    companySizes: ['medium', 'large'],
    benefits: ['Health Insurance', 'Remote Work'],
    workCulture: ['Innovative', 'Collaborative']
  }
};

const mockRecommendations: Job[] = [
  {
    id: '1',
    title: 'Senior Frontend Developer',
    company: 'TechCorp Inc.',
    description: 'We are looking for a skilled Frontend Developer...',
    requirements: ['React', 'TypeScript', 'Next.js'],
    location: 'San Francisco, CA',
    locationType: 'hybrid',
    salary: { min: 120000, max: 160000, currency: 'USD', period: 'year' },
    experienceLevel: 'senior',
    jobType: 'full-time',
    skills: ['React', 'TypeScript', 'Next.js'],
    benefits: ['Health Insurance', 'Remote Work'],
    postedAt: new Date('2024-01-15'),
    status: 'active',
    applicantCount: 45,
    views: 230,
    companySize: 'medium',
    industry: 'Technology'
  }
];

const mockMatches: JobMatch[] = [
  {
    id: '1',
    userId: 'user1',
    jobId: '1',
    score: 85,
    factors: [],
    createdAt: new Date(),
    status: 'new'
  }
];

const mockApplications: Application[] = [
  {
    id: 'app1',
    userId: 'user1',
    jobId: '1',
    status: 'pending',
    appliedAt: new Date('2024-01-10'),
    timeline: [
      {
        id: 'event1',
        type: 'applied',
        description: 'Application submitted',
        date: new Date('2024-01-10')
      }
    ]
  }
];

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
  color?: 'primary' | 'success' | 'warning' | 'info';
}> = ({ title, value, subtitle, icon, trend, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    info: 'bg-blue-50 text-blue-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-soft p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={cn('p-3 rounded-lg', colorClasses[color])}>
          {icon}
        </div>
        {trend && (
          <div className="flex items-center gap-1 text-sm">
            <TrendingUp className={cn(
              'w-4 h-4',
              trend.isPositive ? 'text-success-500' : 'text-danger-500'
            )} />
            <span className={cn(
              'font-medium',
              trend.isPositive ? 'text-success-500' : 'text-danger-500'
            )}>
              {trend.isPositive ? '+' : ''}{trend.value}%
            </span>
          </div>
        )}
      </div>

      <div>
        <Typography variant="h4" weight="bold" className="mb-1">
          {value}
        </Typography>
        <Typography variant="body" className="text-secondary-600 mb-1">
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" className="text-secondary-500">
            {subtitle}
          </Typography>
        )}
      </div>
    </div>
  );
};

export default function DashboardPage() {
  const [profile] = useState<UserProfile>(mockProfile);
  const [recommendations] = useState<Job[]>(mockRecommendations);
  const [matches] = useState<JobMatch[]>(mockMatches);
  const [applications] = useState<Application[]>(mockApplications);

  const stats = {
    profileViews: 156,
    jobMatches: 24,
    applications: applications.length,
    savedJobs: 12
  };

  const getJobMatch = (jobId: string): JobMatch | undefined => {
    return matches.find(match => match.jobId === jobId);
  };

  const averageMatchScore = matches.length > 0
    ? Math.round(matches.reduce((sum, match) => sum + match.score, 0) / matches.length)
    : 0;

  return (
    <DashboardLayout
      title="Dashboard"
      user={mockUser}
      sidebarContent={
        <div className="space-y-6">
          {/* Profile Completion */}
          <div className="bg-white rounded-lg shadow-soft p-6">
            <Typography variant="h6" weight="semibold" className="mb-4">
              Profile Completion
            </Typography>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Typography variant="body">Overall</Typography>
                <Typography variant="body" weight="semibold">85%</Typography>
              </div>
              <div className="w-full bg-secondary-200 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full" style={{ width: '85%' }} />
              </div>
              <Typography variant="caption" className="text-secondary-600">
                Complete your profile to get better job matches
              </Typography>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-soft p-6">
            <Typography variant="h6" weight="semibold" className="mb-4">
              Quick Actions
            </Typography>
            <div className="space-y-3">
              <Button variant="ghost" fullWidth className="justify-start">
                Update Resume
              </Button>
              <Button variant="ghost" fullWidth className="justify-start">
                Edit Preferences
              </Button>
              <Button variant="ghost" fullWidth className="justify-start">
                View Applications
              </Button>
            </div>
          </div>
        </div>
      }
    >
      <div className="space-y-8">
        {/* Welcome Section */}
        <div>
          <Typography variant="h4" weight="bold" className="mb-2">
            Welcome back, {mockUser.name}! 👋
          </Typography>
          <Typography variant="body" className="text-secondary-600">
            Here's what's happening with your job search
          </Typography>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Profile Views"
            value={stats.profileViews}
            subtitle="This month"
            icon={<Eye className="w-6 h-6" />}
            trend={{ value: 12, isPositive: true }}
            color="primary"
          />
          <StatCard
            title="Job Matches"
            value={stats.jobMatches}
            subtitle="New this week"
            icon={<Target className="w-6 h-6" />}
            trend={{ value: 8, isPositive: true }}
            color="success"
          />
          <StatCard
            title="Applications"
            value={stats.applications}
            subtitle="In progress"
            icon={<Briefcase className="w-6 h-6" />}
            color="info"
          />
          <StatCard
            title="Saved Jobs"
            value={stats.savedJobs}
            subtitle="Waiting for you"
            icon={<Heart className="w-6 h-6" />}
            color="warning"
          />
        </div>

        {/* Match Score Overview */}
        <div className="bg-white rounded-lg shadow-soft p-8">
          <div className="flex items-center justify-between mb-6">
            <Typography variant="h5" weight="semibold">
              Your Match Score
            </Typography>
            <Badge variant="success">
              {averageMatchScore}% Average
            </Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <ScoreDisplay
                score={averageMatchScore}
                variant="detailed"
                factors={[
                  { type: 'skills', weight: 0.4, score: 90, description: 'Skills Match' },
                  { type: 'experience', weight: 0.3, score: 85, description: 'Experience Level' },
                  { type: 'location', weight: 0.2, score: 75, description: 'Location Preference' },
                  { type: 'salary', weight: 0.1, score: 95, description: 'Salary Range' }
                ]}
              />
            </div>

            <div className="space-y-4">
              <Typography variant="h6" weight="semibold">
                Improve Your Score
              </Typography>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-secondary-50 rounded-lg">
                  <Award className="w-5 h-5 text-primary-500 mt-0.5" />
                  <div>
                    <Typography variant="body" weight="medium">
                      Add More Skills
                    </Typography>
                    <Typography variant="caption" className="text-secondary-600">
                      Include relevant skills from job postings
                    </Typography>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-secondary-50 rounded-lg">
                  <Users className="w-5 h-5 text-primary-500 mt-0.5" />
                  <div>
                    <Typography variant="body" weight="medium">
                      Update Preferences
                    </Typography>
                    <Typography variant="caption" className="text-secondary-600">
                      Refine your job preferences for better matches
                    </Typography>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recommended Jobs */}
        <div className="bg-white rounded-lg shadow-soft p-8">
          <div className="flex items-center justify-between mb-6">
            <Typography variant="h5" weight="semibold">
              Recommended for You
            </Typography>
            <Button variant="outline" size="sm">
              View All
            </Button>
          </div>

          <div className="space-y-4">
            {recommendations.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                variant="compact"
                showActions={true}
              />
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Applications */}
          <div className="bg-white rounded-lg shadow-soft p-8">
            <Typography variant="h5" weight="semibold" className="mb-6">
              Recent Applications
            </Typography>

            <div className="space-y-4">
              {applications.map((application) => {
                const job = recommendations.find(j => j.id === application.jobId);
                if (!job) return null;

                return (
                  <div key={application.id} className="flex items-center gap-4 p-4 border border-secondary-200 rounded-lg">
                    <Avatar
                      src={job.companyLogo}
                      name={job.company}
                      size="md"
                      shape="square"
                    />
                    <div className="flex-1 min-w-0">
                      <Typography variant="body" weight="medium" truncate>
                        {job.title}
                      </Typography>
                      <Typography variant="caption" className="text-secondary-600">
                        {job.company} • Applied {application.appliedAt.toLocaleDateString()}
                      </Typography>
                    </div>
                    <Badge
                      variant={
                        application.status === 'pending' ? 'warning' :
                        application.status === 'interview' ? 'info' :
                        application.status === 'offered' ? 'success' : 'default'
                      }
                      size="sm"
                    >
                      {application.status}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Upcoming Events */}
          <div className="bg-white rounded-lg shadow-soft p-8">
            <Typography variant="h5" weight="semibold" className="mb-6">
              Upcoming Events
            </Typography>

            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 border border-secondary-200 rounded-lg">
                <div className="p-3 bg-primary-50 text-primary-600 rounded-lg">
                  <Calendar className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <Typography variant="body" weight="medium">
                    Interview with TechCorp
                  </Typography>
                  <Typography variant="caption" className="text-secondary-600">
                    Tomorrow at 2:00 PM
                  </Typography>
                </div>
              </div>

              <div className="text-center py-8">
                <Typography variant="body" className="text-secondary-500">
                  No upcoming events
                </Typography>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}