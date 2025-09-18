import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { cn } from '@/lib/utils';
import { Avatar, Button, Typography } from '@/components/atoms';
import { User } from '@/types';
import {
  Search,
  Briefcase,
  User as UserIcon,
  Settings,
  Bell,
  Menu,
  X,
  LogOut,
  ChevronDown
} from 'lucide-react';

interface NavigationProps {
  user?: User | null;
  onSignOut?: () => void;
  variant?: 'header' | 'sidebar';
  className?: string;
  'data-testid'?: string;
}

const navigationItems = [
  { href: '/jobs', label: 'Jobs', icon: Search },
  { href: '/dashboard', label: 'Dashboard', icon: Briefcase },
  { href: '/profile', label: 'Profile', icon: UserIcon },
  { href: '/preferences', label: 'Preferences', icon: Settings }
];

export const Navigation: React.FC<NavigationProps> = ({
  user,
  onSignOut,
  variant = 'header',
  className,
  'data-testid': testId
}) => {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const isHeader = variant === 'header';
  const isSidebar = variant === 'sidebar';

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
  };

  const isActiveRoute = (href: string): boolean => {
    if (href === '/') {
      return router.pathname === '/';
    }
    return router.pathname.startsWith(href);
  };

  const NavLink: React.FC<{
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    onClick?: () => void;
  }> = ({ href, label, icon: Icon, onClick }) => {
    const isActive = isActiveRoute(href);

    return (
      <Link
        href={href}
        onClick={onClick}
        className={cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-200',
          'hover:bg-secondary-100',
          isActive && 'bg-primary-50 text-primary-700 border border-primary-200',
          isSidebar && 'w-full',
          isHeader && 'text-sm'
        )}
      >
        <Icon className="w-5 h-5" />
        <span className={cn(isSidebar && 'font-medium')}>{label}</span>
      </Link>
    );
  };

  if (isSidebar) {
    return (
      <aside
        className={cn(
          'h-full bg-white border-r border-secondary-200 overflow-y-auto',
          'w-64 flex flex-col',
          className
        )}
        data-testid={testId}
      >
        {/* Logo */}
        <div className="p-6 border-b border-secondary-200">
          <Typography variant="h5" weight="bold" color="primary">
            Job Match Pro
          </Typography>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {navigationItems.map((item) => (
              <NavLink
                key={item.href}
                href={item.href}
                label={item.label}
                icon={item.icon}
              />
            ))}
          </div>
        </nav>

        {/* User Section */}
        {user && (
          <div className="p-4 border-t border-secondary-200">
            <div className="flex items-center gap-3 mb-4">
              <Avatar src={user.avatar} name={user.name} size="md" />
              <div className="flex-1 min-w-0">
                <Typography variant="body" weight="medium" truncate>
                  {user.name}
                </Typography>
                <Typography variant="caption" className="text-secondary-500" truncate>
                  {user.email}
                </Typography>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              icon={<LogOut />}
              onClick={onSignOut}
              fullWidth
              className="justify-start"
            >
              Sign Out
            </Button>
          </div>
        )}
      </aside>
    );
  }

  return (
    <header
      className={cn(
        'bg-white border-b border-secondary-200 sticky top-0 z-40',
        className
      )}
      data-testid={testId}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <Typography variant="h6" weight="bold" color="primary">
                Job Match Pro
              </Typography>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-4">
            {navigationItems.map((item) => (
              <NavLink
                key={item.href}
                href={item.href}
                label={item.label}
                icon={item.icon}
              />
            ))}
          </nav>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Notifications */}
            {user && (
              <Button
                variant="ghost"
                size="sm"
                icon={<Bell />}
                className="relative"
              >
                {/* Notification badge */}
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-danger-500 rounded-full" />
              </Button>
            )}

            {/* User Menu */}
            {user ? (
              <div className="relative">
                <button
                  onClick={toggleUserMenu}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-secondary-100 transition-colors"
                >
                  <Avatar src={user.avatar} name={user.name} size="sm" />
                  <ChevronDown className="w-4 h-4 hidden sm:block" />
                </button>

                {/* User Dropdown */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-secondary-200 rounded-lg shadow-lg py-1">
                    <div className="px-4 py-2 border-b border-secondary-100">
                      <Typography variant="body" weight="medium">
                        {user.name}
                      </Typography>
                      <Typography variant="caption" className="text-secondary-500">
                        {user.email}
                      </Typography>
                    </div>

                    <Link
                      href="/profile"
                      className="flex items-center gap-2 px-4 py-2 hover:bg-secondary-50"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <UserIcon className="w-4 h-4" />
                      Profile
                    </Link>

                    <Link
                      href="/preferences"
                      className="flex items-center gap-2 px-4 py-2 hover:bg-secondary-50"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Settings className="w-4 h-4" />
                      Preferences
                    </Link>

                    <button
                      onClick={() => {
                        onSignOut?.();
                        setIsUserMenuOpen(false);
                      }}
                      className="flex items-center gap-2 w-full px-4 py-2 hover:bg-secondary-50 text-danger-600"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/auth/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/auth/register">
                  <Button variant="primary" size="sm">
                    Sign Up
                  </Button>
                </Link>
              </div>
            )}

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              icon={isMobileMenuOpen ? <X /> : <Menu />}
              onClick={toggleMobileMenu}
              className="md:hidden"
            />
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-secondary-200 py-4">
            <nav className="space-y-2">
              {navigationItems.map((item) => (
                <NavLink
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  icon={item.icon}
                  onClick={() => setIsMobileMenuOpen(false)}
                />
              ))}
            </nav>
          </div>
        )}
      </div>

      {/* Overlay for mobile user menu */}
      {(isMobileMenuOpen || isUserMenuOpen) && (
        <div
          className="fixed inset-0 bg-black bg-opacity-25 z-30"
          onClick={() => {
            setIsMobileMenuOpen(false);
            setIsUserMenuOpen(false);
          }}
        />
      )}
    </header>
  );
};