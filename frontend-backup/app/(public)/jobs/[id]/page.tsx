/**
 * Job Detail Page
 * Server-side rendered job details with SEO optimization
 */

import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { Share2, Bookmark, MapPin, Building, Clock, DollarSign } from 'lucide-react';

import { getJob, getRelatedJobs } from '@/lib/api/jobs';
import { getCompany } from '@/lib/api/companies';
import { Container } from '@/components/ui/container';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { JobCard } from '@/components/jobs/job-card';
import { CompanyCard } from '@/components/companies/company-card';
import { JobApplicationForm } from '@/components/jobs/job-application-form';
import { ShareButton } from '@/components/ui/share-button';
import { SaveJobButton } from '@/components/jobs/save-job-button';
import { JobActions } from '@/components/jobs/job-actions';
import { JobRequirements } from '@/components/jobs/job-requirements';
import { JobBenefits } from '@/components/jobs/job-benefits';

import { formatSalary, formatDate, formatExperience } from '@/lib/utils/format';
import { RouteParams } from '@/types/routing';

interface JobPageProps {
  params: RouteParams;
}

// Generate metadata for SEO
export async function generateMetadata({ params }: JobPageProps): Promise<Metadata> {
  try {
    const job = await getJob(params.id);

    if (!job) {
      return {
        title: 'Job Not Found',
        description: 'The job you are looking for could not be found.',
      };
    }

    const title = `${job.title} at ${job.company.name} | JobMatch Pro`;
    const description = `${job.summary || job.description.slice(0, 160)}...`;

    return {
      title,
      description,
      keywords: [
        job.title,
        job.company.name,
        ...job.skills,
        job.location,
        job.category,
        'job opportunity',
      ],
      openGraph: {
        title,
        description,
        url: `https://jobmatch.pro/jobs/${job.id}`,
        images: [
          {
            url: job.company.logo || '/images/default-company.jpg',
            width: 1200,
            height: 630,
            alt: `${job.title} at ${job.company.name}`,
          },
        ],
      },
      twitter: {
        card: 'summary_large_image',
        title,
        description,
        images: [job.company.logo || '/images/default-company.jpg'],
      },
      alternates: {
        canonical: `https://jobmatch.pro/jobs/${job.id}`,
      },
    };
  } catch (error) {
    return {
      title: 'Job Not Found',
      description: 'The job you are looking for could not be found.',
    };
  }
}

export default async function JobPage({ params }: JobPageProps) {
  try {
    // Fetch job details and related data in parallel
    const [job, relatedJobs] = await Promise.all([
      getJob(params.id),
      getRelatedJobs(params.id, { limit: 3 }),
    ]);

    if (!job) {
      notFound();
    }

    // Generate structured data for job posting
    const structuredData = {
      '@context': 'https://schema.org',
      '@type': 'JobPosting',
      title: job.title,
      description: job.description,
      identifier: {
        '@type': 'PropertyValue',
        name: job.company.name,
        value: job.id,
      },
      datePosted: job.createdAt,
      validThrough: job.expiresAt,
      employmentType: job.employmentType,
      hiringOrganization: {
        '@type': 'Organization',
        name: job.company.name,
        logo: job.company.logo,
        url: job.company.website,
      },
      jobLocation: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressLocality: job.location,
          addressCountry: job.country || 'US',
        },
      },
      baseSalary: job.salary && {
        '@type': 'MonetaryAmount',
        currency: job.salary.currency || 'USD',
        value: {
          '@type': 'QuantitativeValue',
          minValue: job.salary.min,
          maxValue: job.salary.max,
          unitText: job.salary.period || 'YEAR',
        },
      },
      qualifications: job.requirements,
      skills: job.skills,
      workHours: job.workHours,
      benefits: job.benefits,
    };

    return (
      <>
        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(structuredData),
          }}
        />

        <Container className="py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <main className="lg:col-span-2">
              {/* Job Header */}
              <div className="mb-8">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
                  <div className="flex-1">
                    <h1 className="text-3xl font-bold tracking-tight mb-2">
                      {job.title}
                    </h1>
                    <div className="flex flex-wrap items-center gap-4 text-muted-foreground mb-4">
                      <div className="flex items-center gap-1">
                        <Building className="h-4 w-4" />
                        <span>{job.company.name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        <span>{job.location}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>Posted {formatDate(job.createdAt)}</span>
                      </div>
                      {job.salary && (
                        <div className="flex items-center gap-1">
                          <DollarSign className="h-4 w-4" />
                          <span>{formatSalary(job.salary)}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary">{job.employmentType}</Badge>
                      <Badge variant="outline">{job.experienceLevel}</Badge>
                      {job.remote && <Badge variant="default">Remote</Badge>}
                      {job.urgent && <Badge variant="destructive">Urgent</Badge>}
                    </div>
                  </div>

                  {/* Job Actions */}
                  <div className="flex items-center gap-2">
                    <SaveJobButton jobId={job.id} />
                    <ShareButton
                      url={`https://jobmatch.pro/jobs/${job.id}`}
                      title={`${job.title} at ${job.company.name}`}
                    />
                    <JobActions job={job} />
                  </div>
                </div>

                {/* Job Summary */}
                {job.summary && (
                  <div className="p-4 bg-muted rounded-lg mb-6">
                    <p className="text-sm">{job.summary}</p>
                  </div>
                )}
              </div>

              {/* Job Description */}
              <section className="mb-8">
                <h2 className="text-xl font-semibold mb-4">Job Description</h2>
                <div
                  className="prose prose-gray max-w-none"
                  dangerouslySetInnerHTML={{ __html: job.description }}
                />
              </section>

              {/* Requirements */}
              {job.requirements && job.requirements.length > 0 && (
                <section className="mb-8">
                  <JobRequirements requirements={job.requirements} />
                </section>
              )}

              {/* Skills */}
              {job.skills && job.skills.length > 0 && (
                <section className="mb-8">
                  <h2 className="text-xl font-semibold mb-4">Required Skills</h2>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.map((skill) => (
                      <Badge key={skill} variant="outline">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </section>
              )}

              {/* Benefits */}
              {job.benefits && job.benefits.length > 0 && (
                <section className="mb-8">
                  <JobBenefits benefits={job.benefits} />
                </section>
              )}

              {/* Application Section */}
              <section className="mb-8">
                <Suspense fallback={<LoadingSkeleton className="h-64" />}>
                  <JobApplicationForm job={job} />
                </Suspense>
              </section>
            </main>

            {/* Sidebar */}
            <aside className="lg:col-span-1">
              <div className="sticky top-8 space-y-6">
                {/* Company Info */}
                <Suspense fallback={<LoadingSkeleton className="h-48" />}>
                  <CompanyCard
                    company={job.company}
                    showJobs={true}
                    className="w-full"
                  />
                </Suspense>

                {/* Job Stats */}
                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-3">Job Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Experience:</span>
                      <span>{formatExperience(job.experienceLevel)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Category:</span>
                      <span>{job.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Job Type:</span>
                      <span>{job.employmentType}</span>
                    </div>
                    {job.workHours && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Work Hours:</span>
                        <span>{job.workHours}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Applications:</span>
                      <span>{job.applicationCount || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Related Jobs */}
                {relatedJobs.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">Similar Jobs</h3>
                    <div className="space-y-3">
                      {relatedJobs.map((relatedJob) => (
                        <JobCard
                          key={relatedJob.id}
                          job={relatedJob}
                          variant="compact"
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </aside>
          </div>
        </Container>
      </>
    );
  } catch (error) {
    console.error('Error fetching job:', error);
    throw new Error('Failed to load job details');
  }
}

// Enable ISR for job pages
export const revalidate = 1800; // Revalidate every 30 minutes

// Generate static params for popular jobs
export async function generateStaticParams() {
  // In a real app, you would fetch popular job IDs from your API
  // For now, return an empty array to generate pages on-demand
  return [];
}