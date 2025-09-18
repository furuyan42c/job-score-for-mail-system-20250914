// Quick actions component
// Basic implementation to resolve import errors

export interface QuickActionsProps {
  className?: string;
}

export function QuickActions({ className }: QuickActionsProps) {
  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
              <h4 className="font-medium text-gray-900">Search Jobs</h4>
              <p className="text-sm text-gray-500">Find new opportunities</p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
              <h4 className="font-medium text-gray-900">Update Profile</h4>
              <p className="text-sm text-gray-500">Keep your profile current</p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
              <h4 className="font-medium text-gray-900">Upload Resume</h4>
              <p className="text-sm text-gray-500">Add your latest resume</p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:bg-gray-50">
              <h4 className="font-medium text-gray-900">View Applications</h4>
              <p className="text-sm text-gray-500">Track your progress</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}