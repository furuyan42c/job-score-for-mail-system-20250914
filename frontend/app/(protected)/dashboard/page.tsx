/**
 * Dashboard Page
 * Protected user dashboard with personalized content
 */

import { Metadata } from 'next';
import { Suspense } from 'react';
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';

import { authOptions } from '@/lib/auth';
import { getUserDashboardData } from '@/lib/api/users';
import { DashboardStats } from '@/components/dashboard/dashboard-stats';
import { RecentApplications } from '@/components/dashboard/recent-applications';
import { RecommendedJobs } from '@/components/dashboard/recommended-jobs';
import { SavedJobs } from '@/components/dashboard/saved-jobs';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { ProfileCompleteness } from '@/components/dashboard/profile-completeness';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { PageHeader } from '@/components/ui/page-header';

// Page metadata
export const metadata: Metadata = {
  title: 'Dashboard - Your Job Search Command Center',
  description: 'Track your job applications, discover new opportunities, and manage your career journey from your personalized dashboard.',
  robots: {
    index: false, // Don't index private dashboard pages
    follow: false,
  },
};

export default async function DashboardPage() {
  // Get user session
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/auth/signin');
  }

  try {
    // Fetch dashboard data
    const dashboardData = await getUserDashboardData(session.user.id);

    const {
      stats,
      recentApplications,
      recommendedJobs,
      savedJobs,
      activities,
      profileCompleteness,
    } = dashboardData;

    return (
      <div className="space-y-8">
        {/* Page Header */}
        <PageHeader
          title={`Welcome back, ${session.user.name?.split(' ')[0] || 'there'}!`}
          description="Here's what's happening with your job search today."
        />

        {/* Profile Completeness Alert */}
        {profileCompleteness.percentage < 80 && (
          <Suspense fallback={<LoadingSkeleton className="h-24" />}>
            <ProfileCompleteness data={profileCompleteness} />
          </Suspense>
        )}

        {/* Dashboard Stats */}
        <Suspense fallback={<LoadingSkeleton className="h-32" />}>
          <DashboardStats stats={stats} />
        </Suspense>

        {/* Quick Actions */}
        <Suspense fallback={<LoadingSkeleton className="h-16" />}>
          <QuickActions />
        </Suspense>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Recommended Jobs */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Recommended for You</h2>
                <a
                  href="/recommendations"
                  className="text-sm text-primary hover:underline"
                >
                  View all
                </a>
              </div>
              <Suspense fallback={<LoadingSkeleton className="h-64" />}>
                <RecommendedJobs jobs={recommendedJobs} />
              </Suspense>
            </section>

            {/* Recent Applications */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Recent Applications</h2>
                <a
                  href="/applied"
                  className="text-sm text-primary hover:underline"
                >
                  View all
                </a>
              </div>
              <Suspense fallback={<LoadingSkeleton className="h-48" />}>
                <RecentApplications applications={recentApplications} />
              </Suspense>
            </section>
          </div>

          {/* Right Column - Sidebar */}
          <div className="lg:col-span-1 space-y-8">
            {/* Saved Jobs */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Saved Jobs</h2>
                <a
                  href="/saved"
                  className="text-sm text-primary hover:underline"
                >
                  View all
                </a>
              </div>
              <Suspense fallback={<LoadingSkeleton className="h-48" />}>
                <SavedJobs jobs={savedJobs} />
              </Suspense>
            </section>

            {/* Activity Feed */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Recent Activity</h2>
                <a
                  href="/history"
                  className="text-sm text-primary hover:underline"
                >
                  View all
                </a>
              </div>
              <Suspense fallback={<LoadingSkeleton className="h-64" />}>
                <ActivityFeed activities={activities} />
              </Suspense>
            </section>
          </div>
        </div>

        {/* Additional Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Job Search Tips */}
          <section className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-4">💡 Job Search Tips</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                <p>Complete your profile to get better job recommendations</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                <p>Set up job alerts for positions that match your criteria</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                <p>Follow up on your applications within a week</p>
              </div>
            </div>
          </section>

          {/* Market Insights */}
          <section className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-4">📊 Market Insights</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg. Response Time:</span>
                <span className="font-medium">3-5 days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Top Skills in Demand:</span>
                <span className="font-medium">React, Python, AWS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Success Rate:</span>
                <span className="font-medium text-green-600">87%</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw new Error('Failed to load dashboard');
  }
}

// Disable caching for protected pages
export const dynamic = 'force-dynamic';