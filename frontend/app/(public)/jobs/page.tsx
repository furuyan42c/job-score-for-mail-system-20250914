/**
 * Jobs Listing Page
 * Public job listing with search, filtering, and pagination
 * Uses SSG with ISR for optimal performance
 */

import { Metadata } from 'next';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';

import { JobsGrid } from '@/components/jobs/jobs-grid';
import { JobsFilters } from '@/components/jobs/jobs-filters';
import { JobsSearch } from '@/components/jobs/jobs-search';
import { JobsPagination } from '@/components/jobs/jobs-pagination';
import { JobsSort } from '@/components/jobs/jobs-sort';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Container } from '@/components/ui/container';
import { PageHeader } from '@/components/ui/page-header';

import { getJobs, getJobCategories, getJobLocations } from '@/lib/api/jobs';
import { SearchParams } from '@/types/routing';

// Page metadata
export const metadata: Metadata = {
  title: 'Browse Jobs - Find Your Perfect Career Opportunity',
  description: 'Explore thousands of job opportunities across various industries and locations. Filter by skills, salary, experience level, and more to find your ideal position.',
  keywords: [
    'job listings',
    'career opportunities',
    'job search',
    'employment',
    'job openings',
    'careers',
    'job board',
  ],
  openGraph: {
    title: 'Browse Jobs - Find Your Perfect Career Opportunity',
    description: 'Explore thousands of job opportunities across various industries and locations.',
    url: 'https://jobmatch.pro/jobs',
    images: [
      {
        url: '/images/jobs/og-jobs.jpg',
        width: 1200,
        height: 630,
        alt: 'Browse Job Opportunities',
      },
    ],
  },
  alternates: {
    canonical: 'https://jobmatch.pro/jobs',
  },
};

interface JobsPageProps {
  searchParams: SearchParams;
}

// Default page size and sorting
const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_SORT = 'relevance';

export default async function JobsPage({ searchParams }: JobsPageProps) {
  // Parse search parameters
  const query = typeof searchParams.q === 'string' ? searchParams.q : '';
  const page = typeof searchParams.page === 'string' ? parseInt(searchParams.page, 10) : 1;
  const pageSize = typeof searchParams.limit === 'string' ? parseInt(searchParams.limit, 10) : DEFAULT_PAGE_SIZE;
  const sort = typeof searchParams.sort === 'string' ? searchParams.sort : DEFAULT_SORT;
  const location = typeof searchParams.location === 'string' ? searchParams.location : '';
  const category = typeof searchParams.category === 'string' ? searchParams.category : '';
  const experience = typeof searchParams.experience === 'string' ? searchParams.experience : '';
  const salary = typeof searchParams.salary === 'string' ? searchParams.salary : '';
  const jobType = typeof searchParams.type === 'string' ? searchParams.type : '';
  const remote = searchParams.remote === 'true';

  // Validate page number
  if (page < 1 || pageSize < 1 || pageSize > 100) {
    notFound();
  }

  try {
    // Fetch data in parallel
    const [jobsData, categories, locations] = await Promise.all([
      getJobs({
        query,
        page,
        pageSize,
        sort,
        filters: {
          location,
          category,
          experience,
          salary,
          jobType,
          remote,
        },
      }),
      getJobCategories(),
      getJobLocations(),
    ]);

    const { jobs, total, pagination } = jobsData;

    // Generate structured data for job listings
    const structuredData = {
      '@context': 'https://schema.org',
      '@type': 'JobPosting',
      hiringOrganization: {
        '@type': 'Organization',
        name: 'JobMatch Pro',
      },
      jobLocation: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressCountry: 'US',
        },
      },
      description: 'Multiple job opportunities available through JobMatch Pro platform',
      numberOfJobs: total,
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
          {/* Page Header */}
          <PageHeader
            title="Find Your Dream Job"
            description={`Explore ${total.toLocaleString()} job opportunities tailored to your skills and preferences`}
            className="mb-8"
          />

          {/* Search Bar */}
          <div className="mb-6">
            <Suspense fallback={<LoadingSkeleton className="h-12" />}>
              <JobsSearch initialQuery={query} />
            </Suspense>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Filters Sidebar */}
            <aside className="lg:col-span-1">
              <div className="sticky top-8">
                <Suspense fallback={<LoadingSkeleton className="h-96" />}>
                  <JobsFilters
                    categories={categories}
                    locations={locations}
                    initialFilters={{
                      location,
                      category,
                      experience,
                      salary,
                      jobType,
                      remote,
                    }}
                  />
                </Suspense>
              </div>
            </aside>

            {/* Main Content */}
            <main className="lg:col-span-3">
              {/* Sort and Results Count */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
                <div className="text-sm text-muted-foreground">
                  Showing {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, total)} of {total.toLocaleString()} results
                  {query && (
                    <span className="ml-1">
                      for <strong>&quot;{query}&quot;</strong>
                    </span>
                  )}
                </div>

                <Suspense fallback={<LoadingSkeleton className="h-10 w-48" />}>
                  <JobsSort initialSort={sort} />
                </Suspense>
              </div>

              {/* Jobs Grid */}
              <Suspense fallback={<LoadingSkeleton className="h-96" />}>
                <JobsGrid jobs={jobs} />
              </Suspense>

              {/* Pagination */}
              {pagination.totalPages > 1 && (
                <div className="mt-8">
                  <Suspense fallback={<LoadingSkeleton className="h-12" />}>
                    <JobsPagination
                      currentPage={page}
                      totalPages={pagination.totalPages}
                      pageSize={pageSize}
                      total={total}
                    />
                  </Suspense>
                </div>
              )}

              {/* No Results */}
              {jobs.length === 0 && (
                <div className="text-center py-12">
                  <h3 className="text-lg font-semibold mb-2">No jobs found</h3>
                  <p className="text-muted-foreground mb-4">
                    Try adjusting your search criteria or filters to find more results.
                  </p>
                  <a
                    href="/jobs"
                    className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    Clear all filters
                  </a>
                </div>
              )}
            </main>
          </div>
        </Container>
      </>
    );
  } catch (error) {
    console.error('Error fetching jobs:', error);
    throw new Error('Failed to load jobs');
  }
}

// Enable static generation with ISR
export const revalidate = 300; // Revalidate every 5 minutes

// Generate static params for popular search terms
export async function generateStaticParams() {
  const popularSearches = [
    { q: 'frontend' },
    { q: 'backend' },
    { q: 'fullstack' },
    { q: 'react' },
    { q: 'nodejs' },
    { q: 'python' },
    { q: 'designer' },
    { q: 'manager' },
    { q: 'marketing' },
    { q: 'sales' },
  ];

  return popularSearches;
}