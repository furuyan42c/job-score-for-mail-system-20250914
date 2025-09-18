// Saved jobs component
// Basic implementation to resolve import errors

export interface SavedJobsProps {
  className?: string;
}

export function SavedJobs({ className }: SavedJobsProps) {
  return (
    <div className={className}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Saved Jobs</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500">
            <p>No saved jobs yet.</p>
            <p className="text-sm mt-2">Save interesting jobs to view them here later.</p>
          </div>
        </div>
      </div>
    </div>
  );
}