"use client";

/**
 * Global 404 Not Found Page
 * Handles pages that don't exist
 */

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { SearchX, Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        {/* 404 Icon */}
        <div className="flex justify-center">
          <div className="bg-muted p-4 rounded-full">
            <SearchX className="h-12 w-12 text-muted-foreground" />
          </div>
        </div>

        {/* 404 Message */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">404</h1>
          <h2 className="text-xl font-semibold">Page not found</h2>
          <p className="text-muted-foreground">
            The page you are looking for doesn't exist or has been moved.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild>
            <Link href="/" className="flex items-center gap-2">
              <Home className="h-4 w-4" />
              Go home
            </Link>
          </Button>

          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go back
          </Button>
        </div>

        {/* Helpful Links */}
        <div className="pt-4 border-t">
          <p className="text-sm text-muted-foreground mb-3">
            Looking for something specific?
          </p>
          <div className="flex flex-wrap justify-center gap-2 text-sm">
            <Link
              href="/jobs"
              className="text-primary hover:underline"
            >
              Browse Jobs
            </Link>
            <span className="text-muted-foreground">•</span>
            <Link
              href="/companies"
              className="text-primary hover:underline"
            >
              View Companies
            </Link>
            <span className="text-muted-foreground">•</span>
            <Link
              href="/contact"
              className="text-primary hover:underline"
            >
              Contact Us
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}