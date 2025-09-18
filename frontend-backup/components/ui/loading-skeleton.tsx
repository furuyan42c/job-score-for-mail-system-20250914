// Loading skeleton component
// Basic implementation to resolve import errors

import { cn } from "@/lib/utils";

export interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
  width?: string;
  height?: string;
}

export function LoadingSkeleton({
  className,
  lines = 1,
  width = "100%",
  height = "1rem"
}: LoadingSkeletonProps) {
  return (
    <div className={cn("animate-pulse", className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="bg-gray-200 rounded"
          style={{
            width: typeof width === 'string' ? width : `${width}px`,
            height: typeof height === 'string' ? height : `${height}px`,
            marginBottom: lines > 1 && index < lines - 1 ? '0.5rem' : '0'
          }}
        />
      ))}
    </div>
  );
}