/**
 * Public Layout for Job Matching System
 * Handles public pages that don't require authentication
 */

import { Suspense } from 'react';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { PublicLoadingSpinner } from '@/components/ui/loading-spinner';

interface PublicLayoutProps {
  children: React.ReactNode;
}

export default function PublicLayout({ children }: PublicLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Public Header */}
      <Suspense fallback={<div className="h-16 border-b bg-background" />}>
        <Header variant="public" />
      </Suspense>

      {/* Main Content */}
      <main className="flex-1">
        <Suspense fallback={<PublicLoadingSpinner />}>
          {children}
        </Suspense>
      </main>

      {/* Footer */}
      <Suspense fallback={<div className="h-20 border-t bg-muted" />}>
        <Footer />
      </Suspense>
    </div>
  );
}