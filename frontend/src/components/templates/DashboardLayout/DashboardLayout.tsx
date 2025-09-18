import React, { useState } from 'react';
import Head from 'next/head';
import { cn } from '@/lib/utils';
import { Navigation } from '@/components/organisms';
import { Button, Typography } from '@/components/atoms';
import { User } from '@/types';
import { Menu, X } from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  user?: User | null;
  onSignOut?: () => void;
  sidebarContent?: React.ReactNode;
  showSidebar?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title = 'Dashboard',
  description = 'Job Match Pro Dashboard',
  user,
  onSignOut,
  sidebarContent,
  showSidebar = true,
  className,
  'data-testid': testId
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const pageTitle = `${title} | Job Match Pro`;

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div
        className={cn('min-h-screen bg-secondary-50 flex', className)}
        data-testid={testId}
      >
        {/* Sidebar */}
        {showSidebar && (
          <>
            {/* Desktop Sidebar */}
            <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0">
              <Navigation
                user={user}
                onSignOut={onSignOut}
                variant="sidebar"
              />
            </div>

            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
              <div className="fixed inset-0 z-50 lg:hidden">
                <div
                  className="fixed inset-0 bg-black bg-opacity-50"
                  onClick={toggleSidebar}
                />
                <div className="fixed inset-y-0 left-0 w-64 bg-white">
                  <div className="flex items-center justify-between p-4 border-b border-secondary-200">
                    <Typography variant="h6" weight="bold" color="primary">
                      Job Match Pro
                    </Typography>
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<X />}
                      onClick={toggleSidebar}
                    />
                  </div>
                  <Navigation
                    user={user}
                    onSignOut={onSignOut}
                    variant="sidebar"
                  />
                </div>
              </div>
            )}
          </>
        )}

        {/* Main Content Area */}
        <div className={cn('flex-1 flex flex-col', showSidebar && 'lg:ml-64')}>
          {/* Top Header */}
          <header className="bg-white border-b border-secondary-200 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Mobile Menu Button */}
              {showSidebar && (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<Menu />}
                  onClick={toggleSidebar}
                  className="lg:hidden"
                />
              )}

              {/* Page Title */}
              <div className="flex-1">
                <Typography variant="h5" weight="semibold">
                  {title}
                </Typography>
              </div>

              {/* Header Actions */}
              <div className="flex items-center gap-4">
                {/* User info for mobile */}
                {user && (
                  <div className="lg:hidden">
                    <div className="flex items-center gap-2">
                      <Typography variant="body" weight="medium">
                        {user.name}
                      </Typography>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="p-4 sm:p-6 lg:p-8">
              {children}
            </div>
          </main>
        </div>

        {/* Additional Sidebar Content */}
        {sidebarContent && (
          <aside className="hidden xl:block xl:w-80 xl:border-l xl:border-secondary-200 xl:bg-white">
            <div className="p-6">
              {sidebarContent}
            </div>
          </aside>
        )}
      </div>
    </>
  );
};