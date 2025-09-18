import React from 'react';
import Head from 'next/head';
import { cn } from '@/lib/utils';
import { Navigation } from '@/components/organisms';
import { User } from '@/types';
import { Typography } from '@/components/atoms';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  user?: User | null;
  onSignOut?: () => void;
  showNavigation?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  title = 'Job Match Pro',
  description = 'AI-powered job matching platform',
  user,
  onSignOut,
  showNavigation = true,
  className,
  'data-testid': testId
}) => {
  const pageTitle = title === 'Job Match Pro' ? title : `${title} | Job Match Pro`;

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div
        className={cn('min-h-screen bg-secondary-50', className)}
        data-testid={testId}
      >
        {/* Navigation */}
        {showNavigation && (
          <Navigation
            user={user}
            onSignOut={onSignOut}
            variant="header"
          />
        )}

        {/* Main Content */}
        <main className="flex-1">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-secondary-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {/* Company Info */}
              <div className="space-y-4">
                <Typography variant="h6" weight="bold" color="primary">
                  Job Match Pro
                </Typography>
                <Typography variant="body" className="text-secondary-600">
                  AI-powered job matching platform that connects talent with opportunities.
                </Typography>
              </div>

              {/* Quick Links */}
              <div className="space-y-4">
                <Typography variant="h6" weight="semibold">
                  Quick Links
                </Typography>
                <div className="space-y-2">
                  <a href="/jobs" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Browse Jobs
                  </a>
                  <a href="/dashboard" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Dashboard
                  </a>
                  <a href="/profile" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Profile
                  </a>
                  <a href="/preferences" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Preferences
                  </a>
                </div>
              </div>

              {/* Support */}
              <div className="space-y-4">
                <Typography variant="h6" weight="semibold">
                  Support
                </Typography>
                <div className="space-y-2">
                  <a href="/help" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Help Center
                  </a>
                  <a href="/contact" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Contact Us
                  </a>
                  <a href="/faq" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    FAQ
                  </a>
                  <a href="/feedback" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Feedback
                  </a>
                </div>
              </div>

              {/* Legal */}
              <div className="space-y-4">
                <Typography variant="h6" weight="semibold">
                  Legal
                </Typography>
                <div className="space-y-2">
                  <a href="/privacy" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Privacy Policy
                  </a>
                  <a href="/terms" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Terms of Service
                  </a>
                  <a href="/cookies" className="block text-secondary-600 hover:text-primary-600 transition-colors">
                    Cookie Policy
                  </a>
                </div>
              </div>
            </div>

            {/* Bottom Bar */}
            <div className="border-t border-secondary-200 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center">
              <Typography variant="body" className="text-secondary-500">
                © 2024 Job Match Pro. All rights reserved.
              </Typography>
              <div className="flex items-center space-x-6 mt-4 sm:mt-0">
                <a href="/social/twitter" className="text-secondary-400 hover:text-primary-600 transition-colors">
                  Twitter
                </a>
                <a href="/social/linkedin" className="text-secondary-400 hover:text-primary-600 transition-colors">
                  LinkedIn
                </a>
                <a href="/social/github" className="text-secondary-400 hover:text-primary-600 transition-colors">
                  GitHub
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};