/**
 * Protected Layout for Job Matching System
 * Handles authenticated pages with user-specific navigation
 */

import { Suspense } from 'react';
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';

import { authOptions } from '@/lib/auth';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardSidebar } from '@/components/layout/dashboard-sidebar';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { ProtectedLoadingSpinner } from '@/components/ui/loading-spinner';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';

interface ProtectedLayoutProps {
  children: React.ReactNode;
}

export default async function ProtectedLayout({ children }: ProtectedLayoutProps) {
  // Check authentication on server side
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/auth/signin');
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Suspense fallback={<div className="hidden lg:block w-64 border-r bg-muted/30" />}>
        <DashboardSidebar user={session.user} />
      </Suspense>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Suspense fallback={<div className="h-16 border-b bg-background" />}>
          <DashboardHeader user={session.user} />
        </Suspense>

        {/* Breadcrumbs */}
        <div className="border-b bg-muted/30">
          <div className="container py-3">
            <Suspense fallback={<div className="h-5 w-48 bg-muted rounded animate-pulse" />}>
              <Breadcrumbs />
            </Suspense>
          </div>
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className="container py-6">
            <Suspense fallback={<ProtectedLoadingSpinner />}>
              {children}
            </Suspense>
          </div>
        </main>

        {/* Footer */}
        <Suspense fallback={<div className="h-16 border-t bg-muted/30" />}>
          <DashboardFooter />
        </Suspense>
      </div>
    </div>
  );
}