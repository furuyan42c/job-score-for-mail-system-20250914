// Dashboard header component
// Basic implementation to resolve import errors

"use client";

import { Button } from "@/components/ui/button";

export interface DashboardHeaderProps {
  className?: string;
}

export function DashboardHeader({ className }: DashboardHeaderProps) {
  return (
    <header className={`bg-white border-b border-gray-200 ${className}`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">JobMatch Pro</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" size="sm">
              Profile
            </Button>
            <Button variant="outline" size="sm">
              Settings
            </Button>
            <Button variant="outline" size="sm">
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}