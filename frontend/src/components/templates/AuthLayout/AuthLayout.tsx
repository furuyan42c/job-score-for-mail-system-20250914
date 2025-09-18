import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Typography } from '@/components/atoms';

interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  subtitle?: string;
  showBackToHome?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title = 'Authentication',
  description = 'Job Match Pro Authentication',
  subtitle,
  showBackToHome = true,
  className,
  'data-testid': testId
}) => {
  const pageTitle = `${title} | Job Match Pro`;

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div
        className={cn(
          'min-h-screen bg-gradient-to-br from-primary-50 to-secondary-100',
          'flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8',
          className
        )}
        data-testid={testId}
      >
        <div className="w-full max-w-md space-y-8">
          {/* Header */}
          <div className="text-center">
            {/* Logo */}
            <Link href="/" className="inline-block">
              <Typography variant="h4" weight="bold" color="primary" className="mb-2">
                Job Match Pro
              </Typography>
            </Link>

            {/* Title */}
            <Typography variant="h5" weight="semibold" className="mb-2">
              {title}
            </Typography>

            {/* Subtitle */}
            {subtitle && (
              <Typography variant="body" className="text-secondary-600">
                {subtitle}
              </Typography>
            )}
          </div>

          {/* Auth Form */}
          <div className="bg-white rounded-lg shadow-medium p-8 space-y-6">
            {children}
          </div>

          {/* Footer Links */}
          <div className="text-center space-y-4">
            {showBackToHome && (
              <Link
                href="/"
                className="text-sm text-primary-600 hover:text-primary-700 transition-colors"
              >
                ← Back to Home
              </Link>
            )}

            <div className="flex items-center justify-center space-x-4 text-sm text-secondary-500">
              <Link
                href="/privacy"
                className="hover:text-secondary-700 transition-colors"
              >
                Privacy Policy
              </Link>
              <span>•</span>
              <Link
                href="/terms"
                className="hover:text-secondary-700 transition-colors"
              >
                Terms of Service
              </Link>
              <span>•</span>
              <Link
                href="/help"
                className="hover:text-secondary-700 transition-colors"
              >
                Help
              </Link>
            </div>

            <Typography variant="caption" className="text-secondary-400">
              © 2024 Job Match Pro. All rights reserved.
            </Typography>
          </div>
        </div>

        {/* Background Decoration */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary-200 rounded-full opacity-20 transform translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-secondary-300 rounded-full opacity-20 transform -translate-x-1/2 translate-y-1/2" />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-primary-100 rounded-full opacity-30 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
      </div>
    </>
  );
};