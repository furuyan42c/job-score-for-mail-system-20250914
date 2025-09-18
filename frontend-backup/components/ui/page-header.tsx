// Page header component
// Basic implementation to resolve import errors

import { cn } from "@/lib/utils";

export interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  children,
  className
}: PageHeaderProps) {
  return (
    <div className={cn("mb-8", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          {description && (
            <p className="mt-2 text-gray-600">{description}</p>
          )}
        </div>
        {children && (
          <div className="flex items-center space-x-4">
            {children}
          </div>
        )}
      </div>
    </div>
  );
}