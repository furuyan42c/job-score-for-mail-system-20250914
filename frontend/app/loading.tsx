/**
 * Global Loading Component
 * Displays while pages are loading
 */

import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        {/* Header Loading */}
        <div className="text-center space-y-4">
          <LoadingSkeleton className="h-8 w-64 mx-auto" />
          <LoadingSkeleton className="h-4 w-96 mx-auto" />
        </div>

        {/* Content Loading */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-3 p-4 border rounded-lg">
              <LoadingSkeleton className="h-4 w-full" />
              <LoadingSkeleton className="h-4 w-3/4" />
              <LoadingSkeleton className="h-4 w-1/2" />
            </div>
          ))}
        </div>

        {/* Action Loading */}
        <div className="flex justify-center space-x-4">
          <LoadingSkeleton className="h-10 w-24" />
          <LoadingSkeleton className="h-10 w-24" />
        </div>
      </div>
    </div>
  );
}