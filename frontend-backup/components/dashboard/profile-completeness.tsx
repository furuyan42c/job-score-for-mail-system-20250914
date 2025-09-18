// Profile completeness component
// Basic implementation to resolve import errors

export interface ProfileCompletenessProps {
  className?: string;
}

export function ProfileCompleteness({ className }: ProfileCompletenessProps) {
  const completionPercentage = 30; // Mock data

  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Profile Completeness</h3>
        </div>
        <div className="p-6">
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium text-gray-900">{completionPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${completionPercentage}%` }}
              ></div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm text-gray-600">Complete your profile to:</div>
            <ul className="text-sm text-gray-500 space-y-1">
              <li>• Get better job recommendations</li>
              <li>• Increase application success rate</li>
              <li>• Stand out to employers</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}