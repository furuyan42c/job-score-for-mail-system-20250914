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
    <div className="min-h-screen">
      <Header />
      <main className="flex-1">
        <Suspense fallback={<PublicLoadingSpinner />}>
          {children}
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}