// Activity feed component
// Basic implementation to resolve import errors

export interface ActivityFeedProps {
  className?: string;
}

export function ActivityFeed({ className }: ActivityFeedProps) {
  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500">
            <p>No recent activity.</p>
            <p className="text-sm mt-2">Your activity will appear here as you use the platform.</p>
          </div>
        </div>
      </div>
    </div>
  );
}