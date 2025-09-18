// Placeholder components to resolve build errors
// These are temporary implementations that should be replaced with actual components

export function JobCard({ job, variant = "default", ...props }: any) {
  return (
    <div className="p-4 border rounded-lg" {...props}>
      <h3 className="font-medium">Job Component Placeholder</h3>
      <p className="text-sm text-gray-500">JobCard component not yet implemented</p>
    </div>
  );
}

export function CompanyCard({ company, ...props }: any) {
  return (
    <div className="p-4 border rounded-lg" {...props}>
      <h3 className="font-medium">Company Component Placeholder</h3>
      <p className="text-sm text-gray-500">CompanyCard component not yet implemented</p>
    </div>
  );
}

export function JobApplicationForm({ job, ...props }: any) {
  return (
    <div className="p-4 border rounded-lg" {...props}>
      <h3 className="font-medium">Application Form Placeholder</h3>
      <p className="text-sm text-gray-500">JobApplicationForm component not yet implemented</p>
    </div>
  );
}

export function ShareButton({ url, title, ...props }: any) {
  return (
    <button className="px-3 py-2 border rounded-md text-sm" {...props}>
      Share
    </button>
  );
}

export function SaveJobButton({ jobId, ...props }: any) {
  return (
    <button className="px-3 py-2 border rounded-md text-sm" {...props}>
      Save
    </button>
  );
}

export function JobActions({ job, ...props }: any) {
  return (
    <div className="flex gap-2" {...props}>
      <button className="px-3 py-2 border rounded-md text-sm">Actions</button>
    </div>
  );
}

export function JobRequirements({ requirements, ...props }: any) {
  return (
    <div {...props}>
      <h3 className="font-medium mb-2">Requirements</h3>
      <p className="text-sm text-gray-500">JobRequirements component not yet implemented</p>
    </div>
  );
}

export function JobBenefits({ benefits, ...props }: any) {
  return (
    <div {...props}>
      <h3 className="font-medium mb-2">Benefits</h3>
      <p className="text-sm text-gray-500">JobBenefits component not yet implemented</p>
    </div>
  );
}

export function JobsGrid({ jobs, ...props }: any) {
  return (
    <div className="grid gap-4" {...props}>
      <p className="text-sm text-gray-500">JobsGrid component not yet implemented</p>
    </div>
  );
}

export function JobsFilters({ ...props }: any) {
  return (
    <div className="p-4 border rounded-lg" {...props}>
      <h3 className="font-medium mb-2">Filters</h3>
      <p className="text-sm text-gray-500">JobsFilters component not yet implemented</p>
    </div>
  );
}

export function JobsSearch({ ...props }: any) {
  return (
    <div className="p-4 border rounded-lg" {...props}>
      <input type="search" placeholder="Search jobs..." className="w-full p-2 border rounded" />
    </div>
  );
}

export function JobsPagination({ ...props }: any) {
  return (
    <div className="flex justify-center gap-2" {...props}>
      <button className="px-3 py-1 border rounded">Previous</button>
      <button className="px-3 py-1 border rounded bg-blue-100">1</button>
      <button className="px-3 py-1 border rounded">Next</button>
    </div>
  );
}

export function JobsSort({ ...props }: any) {
  return (
    <select className="p-2 border rounded" {...props}>
      <option>Sort by relevance</option>
      <option>Sort by date</option>
      <option>Sort by salary</option>
    </select>
  );
}