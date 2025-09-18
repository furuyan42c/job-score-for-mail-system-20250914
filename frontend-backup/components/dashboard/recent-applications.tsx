// Recent applications component
// Basic implementation to resolve import errors

export interface RecentApplicationsProps {
  className?: string;
}

export function RecentApplications({ className }: RecentApplicationsProps) {
  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Recent Applications</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500">
            <p>No recent applications found.</p>
            <p className="text-sm mt-2">Applications will appear here when you start applying to jobs.</p>
          </div>
        </div>
      </div>
    </div>
  );
}