'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/templates';
import { ScoreDisplay } from '@/components/molecules';
import { Button, Typography, Badge, Avatar, Loader } from '@/components/atoms';
import { Job, JobMatch, Application } from '@/types';
import {
  MapPin,
  Clock,
  Building2,
  Users,
  ExternalLink,
  Bookmark,
  Share2,
  ArrowLeft,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { cn, formatCurrency, formatRelativeTime, getJobTypeDisplay, getLocationTypeDisplay } from '@/lib/utils';
import Link from 'next/link';

// Mock data - replace with actual API calls
const mockJob: Job = {
  id: '1',
  title: 'Senior Frontend Developer',
  company: 'TechCorp Inc.',
  description: `We are looking for a skilled Frontend Developer to join our dynamic team and help build the next generation of web applications.

As a Senior Frontend Developer, you will be responsible for developing user-facing features, ensuring the technical feasibility of UI/UX designs, and optimizing applications for maximum speed and scalability.

You'll work closely with our design and backend teams to deliver exceptional user experiences and drive our product forward.`,
  requirements: [
    '5+ years of experience in frontend development',
    'Strong proficiency in React and TypeScript',
    'Experience with Next.js and modern build tools',
    'Knowledge of state management libraries (Redux, Zustand)',
    'Understanding of RESTful APIs and GraphQL',
    'Experience with testing frameworks (Jest, React Testing Library)',
    'Familiarity with CI/CD pipelines',
    'Strong problem-solving skills and attention to detail'
  ],
  location: 'San Francisco, CA',
  locationType: 'hybrid',
  salary: { min: 120000, max: 160000, currency: 'USD', period: 'year' },
  experienceLevel: 'senior',
  jobType: 'full-time',
  skills: ['React', 'TypeScript', 'Next.js', 'GraphQL', 'Redux', 'Jest'],
  benefits: [
    'Health Insurance',
    'Dental Insurance',
    'Vision Insurance',
    'Remote Work',
    'Stock Options',
    'Unlimited PTO',
    'Professional Development',
    '401(k) Plan'
  ],
  postedAt: new Date('2024-01-15'),
  expiresAt: new Date('2024-02-15'),
  status: 'active',
  applicantCount: 45,
  views: 230,
  companyLogo: '/images/techcorp-logo.png',
  companySize: 'medium',
  industry: 'Technology'
};

const mockMatch: JobMatch = {
  id: '1',
  userId: 'user1',
  jobId: '1',
  score: 85,
  factors: [
    { type: 'skills', weight: 0.4, score: 90, description: 'Skills Match - React, TypeScript, Next.js' },
    { type: 'experience', weight: 0.3, score: 85, description: 'Experience Level - Senior' },
    { type: 'location', weight: 0.2, score: 75, description: 'Location Preference - Hybrid work' },
    { type: 'salary', weight: 0.1, score: 95, description: 'Salary Range - Within expectations' }
  ],
  createdAt: new Date(),
  status: 'new'
};

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [match, setMatch] = useState<JobMatch | null>(null);
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    const loadJobDetails = async () => {
      setLoading(true);
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (jobId === '1') {
        setJob(mockJob);
        setMatch(mockMatch);
      }

      setLoading(false);
    };

    loadJobDetails();
  }, [jobId]);

  const handleApply = async () => {
    setIsApplying(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Create mock application
    const newApplication: Application = {
      id: 'app1',
      userId: 'user1',
      jobId: jobId,
      status: 'pending',
      appliedAt: new Date(),
      timeline: [
        {
          id: 'event1',
          type: 'applied',
          description: 'Application submitted',
          date: new Date()
        }
      ]
    };

    setApplication(newApplication);
    setIsApplying(false);
  };

  const handleSave = () => {
    setIsSaved(!isSaved);
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    // Show success toast
  };

  if (loading) {
    return (
      <MainLayout title="Loading Job..." description="Loading job details">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader size="lg" />
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!job) {
    return (
      <MainLayout title="Job Not Found" description="The requested job could not be found">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <Typography variant="h4" weight="semibold" className="mb-2">
              Job Not Found
            </Typography>
            <Typography variant="body" className="text-secondary-600 mb-4">
              The job you're looking for doesn't exist or has been removed.
            </Typography>
            <Link href="/jobs">
              <Button variant="primary">
                Browse All Jobs
              </Button>
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title={job.title} description={`${job.title} at ${job.company}`}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <div className="mb-6">
          <Link href="/jobs">
            <Button variant="ghost" icon={<ArrowLeft />} size="sm">
              Back to Jobs
            </Button>
          </Link>
        </div>

        {/* Job Header */}
        <div className="bg-white rounded-lg shadow-soft p-8 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-start gap-6 flex-1">
              {/* Company Logo */}
              <Avatar
                src={job.companyLogo}
                name={job.company}
                size="xl"
                shape="square"
              />

              {/* Job Info */}
              <div className="flex-1">
                <Typography variant="h3" weight="bold" className="mb-2">
                  {job.title}
                </Typography>

                <div className="flex items-center gap-2 mb-4">
                  <Typography variant="h6" weight="medium" color="secondary">
                    {job.company}
                  </Typography>
                  {job.companySize && (
                    <>
                      <span className="text-secondary-300">•</span>
                      <div className="flex items-center gap-1 text-secondary-500">
                        <Users className="w-4 h-4" />
                        <Typography variant="body">
                          {job.companySize}
                        </Typography>
                      </div>
                    </>
                  )}
                </div>

                {/* Meta Information */}
                <div className="flex flex-wrap items-center gap-4 text-secondary-500 mb-4">
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    <Typography variant="body">
                      {job.location} • {getLocationTypeDisplay(job.locationType)}
                    </Typography>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <Typography variant="body">
                      Posted {formatRelativeTime(job.postedAt)}
                    </Typography>
                  </div>
                  {job.industry && (
                    <div className="flex items-center gap-1">
                      <Building2 className="w-4 h-4" />
                      <Typography variant="body">
                        {job.industry}
                      </Typography>
                    </div>
                  )}
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-6">
                  <Badge variant="default">
                    {getJobTypeDisplay(job.jobType)}
                  </Badge>
                  <Badge variant="default">
                    {job.experienceLevel}
                  </Badge>
                  {job.skills.map((skill) => (
                    <Badge key={skill} variant="default">
                      {skill}
                    </Badge>
                  ))}
                </div>

                {/* Salary */}
                <div className="mb-6">
                  <Typography variant="h5" weight="bold" color="primary" className="mb-1">
                    {formatCurrency(job.salary.min)} - {formatCurrency(job.salary.max)}
                  </Typography>
                  <Typography variant="body" className="text-secondary-600">
                    per {job.salary.period} • {job.applicantCount} applicants
                  </Typography>
                </div>
              </div>
            </div>

            {/* Match Score */}
            {match && (
              <div className="ml-6">
                <ScoreDisplay
                  score={match.score}
                  factors={match.factors}
                  variant="detailed"
                />
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-4">
            {application ? (
              <div className="flex items-center gap-2 px-4 py-2 bg-success-50 text-success-700 rounded-lg">
                <CheckCircle className="w-5 h-5" />
                <Typography variant="body" weight="medium">
                  Application Submitted
                </Typography>
              </div>
            ) : (
              <Button
                variant="primary"
                size="lg"
                onClick={handleApply}
                loading={isApplying}
                disabled={job.status !== 'active'}
              >
                Apply Now
              </Button>
            )}

            <Button
              variant={isSaved ? "primary" : "outline"}
              size="lg"
              icon={<Bookmark />}
              onClick={handleSave}
            >
              {isSaved ? 'Saved' : 'Save Job'}
            </Button>

            <Button
              variant="ghost"
              size="lg"
              icon={<Share2 />}
              onClick={handleShare}
            >
              Share
            </Button>

            <Button
              variant="ghost"
              size="lg"
              icon={<ExternalLink />}
              onClick={() => window.open(`https://${job.company.toLowerCase()}.com`, '_blank')}
            >
              Company Website
            </Button>
          </div>

          {/* Expiration Warning */}
          {job.expiresAt && new Date(job.expiresAt).getTime() - new Date().getTime() < 7 * 24 * 60 * 60 * 1000 && (
            <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-warning-600" />
                <Typography variant="body" className="text-warning-700">
                  This job posting expires on {formatRelativeTime(job.expiresAt)}
                </Typography>
              </div>
            </div>
          )}
        </div>

        {/* Job Description */}
        <div className="bg-white rounded-lg shadow-soft p-8 mb-6">
          <Typography variant="h5" weight="semibold" className="mb-4">
            Job Description
          </Typography>
          <div className="prose prose-secondary max-w-none">
            {job.description.split('\n\n').map((paragraph, index) => (
              <Typography key={index} variant="body" className="mb-4 text-secondary-700">
                {paragraph}
              </Typography>
            ))}
          </div>
        </div>

        {/* Requirements */}
        <div className="bg-white rounded-lg shadow-soft p-8 mb-6">
          <Typography variant="h5" weight="semibold" className="mb-4">
            Requirements
          </Typography>
          <ul className="space-y-2">
            {job.requirements.map((requirement, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0" />
                <Typography variant="body" className="text-secondary-700">
                  {requirement}
                </Typography>
              </li>
            ))}
          </ul>
        </div>

        {/* Benefits */}
        {job.benefits.length > 0 && (
          <div className="bg-white rounded-lg shadow-soft p-8 mb-6">
            <Typography variant="h5" weight="semibold" className="mb-4">
              Benefits & Perks
            </Typography>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {job.benefits.map((benefit) => (
                <div key={benefit} className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-success-500" />
                  <Typography variant="body" className="text-secondary-700">
                    {benefit}
                  </Typography>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Similar Jobs CTA */}
        <div className="bg-primary-50 rounded-lg p-8 text-center">
          <Typography variant="h5" weight="semibold" className="mb-2">
            Looking for Similar Opportunities?
          </Typography>
          <Typography variant="body" className="text-secondary-600 mb-4">
            Discover more jobs that match your skills and preferences
          </Typography>
          <Link href="/jobs">
            <Button variant="primary">
              Browse Similar Jobs
            </Button>
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}