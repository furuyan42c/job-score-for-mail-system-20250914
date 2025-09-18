import React from 'react';
import { cn } from '@/lib/utils';
import { Button, Typography } from '@/components/atoms';
import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  maxVisiblePages?: number;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  'data-testid'?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  showPrevNext = true,
  maxVisiblePages = 7,
  disabled = false,
  size = 'md',
  className,
  'data-testid': testId
}) => {
  // Generate visible page numbers
  const getVisiblePages = (): (number | 'ellipsis')[] => {
    if (totalPages <= maxVisiblePages) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const half = Math.floor(maxVisiblePages / 2);
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxVisiblePages - 1);

    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }

    const pages: (number | 'ellipsis')[] = [];

    if (start > 1) {
      pages.push(1);
      if (start > 2) {
        pages.push('ellipsis');
      }
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (end < totalPages) {
      if (end < totalPages - 1) {
        pages.push('ellipsis');
      }
      pages.push(totalPages);
    }

    return pages;
  };

  const visiblePages = getVisiblePages();

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage && !disabled) {
      onPageChange(page);
    }
  };

  const buttonSizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2 text-base'
  };

  const buttonSize = size === 'sm' ? 'sm' : size === 'lg' ? 'lg' : 'md';

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      className={cn('flex items-center justify-center', className)}
      aria-label="Pagination"
      data-testid={testId}
    >
      <div className="flex items-center gap-1">
        {/* First Page Button */}
        {showFirstLast && currentPage > 1 && (
          <Button
            variant="ghost"
            size={buttonSize}
            onClick={() => handlePageChange(1)}
            disabled={disabled}
            data-testid={`${testId}-first`}
            className="hidden sm:flex"
          >
            First
          </Button>
        )}

        {/* Previous Page Button */}
        {showPrevNext && (
          <Button
            variant="ghost"
            size={buttonSize}
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={disabled || currentPage === 1}
            icon={<ChevronLeft className="w-4 h-4" />}
            data-testid={`${testId}-prev`}
            className="px-2"
          />
        )}

        {/* Page Numbers */}
        {visiblePages.map((page, index) => {
          if (page === 'ellipsis') {
            return (
              <div
                key={`ellipsis-${index}`}
                className={cn(
                  'flex items-center justify-center',
                  buttonSizeClasses[size]
                )}
              >
                <MoreHorizontal className="w-4 h-4 text-secondary-400" />
              </div>
            );
          }

          const isActive = page === currentPage;

          return (
            <Button
              key={page}
              variant={isActive ? 'primary' : 'ghost'}
              size={buttonSize}
              onClick={() => handlePageChange(page)}
              disabled={disabled}
              data-testid={`${testId}-page-${page}`}
              className={cn(
                'min-w-[40px]',
                isActive && 'pointer-events-none'
              )}
            >
              {page}
            </Button>
          );
        })}

        {/* Next Page Button */}
        {showPrevNext && (
          <Button
            variant="ghost"
            size={buttonSize}
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={disabled || currentPage === totalPages}
            icon={<ChevronRight className="w-4 h-4" />}
            data-testid={`${testId}-next`}
            className="px-2"
          />
        )}

        {/* Last Page Button */}
        {showFirstLast && currentPage < totalPages && (
          <Button
            variant="ghost"
            size={buttonSize}
            onClick={() => handlePageChange(totalPages)}
            disabled={disabled}
            data-testid={`${testId}-last`}
            className="hidden sm:flex"
          >
            Last
          </Button>
        )}
      </div>

      {/* Page Info */}
      <div className="ml-4 hidden md:block">
        <Typography variant="caption" className="text-secondary-500">
          Page {currentPage} of {totalPages}
        </Typography>
      </div>
    </nav>
  );
};