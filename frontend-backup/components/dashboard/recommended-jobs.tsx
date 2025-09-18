// Recommended jobs component
// Basic implementation to resolve import errors

export interface RecommendedJobsProps {
  className?: string;
}

export function RecommendedJobs({ className }: RecommendedJobsProps) {
  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Recommended Jobs</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500">
            <p>No job recommendations available.</p>
            <p className="text-sm mt-2">Complete your profile to get personalized job recommendations.</p>
          </div>
        </div>
      </div>
    </div>
  );
}