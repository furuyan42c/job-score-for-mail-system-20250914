// Jobs API client
// Basic implementation to resolve import errors

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  salary?: {
    min: number;
    max: number;
    currency: string;
  };
  type: "full-time" | "part-time" | "contract" | "internship";
  remote: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface JobApplication {
  id: string;
  jobId: string;
  userId: string;
  status: "pending" | "reviewing" | "interviewing" | "rejected" | "accepted";
  appliedAt: string;
  notes?: string;
}

// Mock API functions - should be replaced with actual API calls
export const getJobs = async (params?: {
  search?: string;
  location?: string;
  type?: string;
  remote?: boolean;
  page?: number;
  limit?: number;
}): Promise<{ jobs: Job[]; total: number; }> => {
  return { jobs: [], total: 0 };
};

export const getJobById = async (id: string): Promise<Job | null> => {
  return null;
};

export const applyToJob = async (jobId: string): Promise<JobApplication> => {
  throw new Error('Job application not implemented');
};

export const getMyApplications = async (): Promise<JobApplication[]> => {
  return [];
};

export const saveJob = async (jobId: string): Promise<void> => {
  throw new Error('Save job not implemented');
};

export const unsaveJob = async (jobId: string): Promise<void> => {
  throw new Error('Unsave job not implemented');
};

export const getSavedJobs = async (): Promise<Job[]> => {
  return [];
};

export const getJob = async (id: string): Promise<Job | null> => {
  return null;
};

export const getRelatedJobs = async (jobId: string, options?: { limit?: number }): Promise<Job[]> => {
  return [];
};