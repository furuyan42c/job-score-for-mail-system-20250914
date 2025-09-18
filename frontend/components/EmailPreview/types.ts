export interface Job {
  id: number;
  title: string;
  companyName: string;
  companyLogo?: string;
  location: string;
  salaryMin?: number;
  salaryMax?: number;
  salaryType?: 'hourly' | 'monthly' | 'yearly';
  matchScore: number;
  tags?: string[];
  description?: string;
  applyUrl: string;
  isNew?: boolean;
  isPopular?: boolean;
  occupationCategory?: string;
  employmentType?: string;
}

export interface EmailSection {
  id: string;
  title: string;
  description?: string;
  jobs: Job[];
  maxJobs: number;
  priority: number;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  fromAddress: string;
  sections: EmailSection[];
  metadata: EmailMetadata;
}

export interface EmailMetadata {
  generatedAt: string;
  userId: string;
  userName: string;
  userLocation: string;
  totalJobCount: number;
  gptUsage?: {
    model: string;
    tokens: number;
    cost: number;
  };
  isFallbackTemplate: boolean;
  deliveryDate: string;
  templateVersion: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  location: string;
  preferences: {
    occupations: string[];
    locations: string[];
    salaryRange: {
      min: number;
      max: number;
    };
    employmentTypes: string[];
  };
}

export type PreviewMode = 'desktop' | 'mobile' | 'plaintext' | 'html';

export interface EmailPreviewProps {
  emailTemplate?: EmailTemplate;
  users?: User[];
  selectedUserId?: string;
  onUserChange?: (userId: string) => void;
  onRegenerateEmail?: () => void;
  onSendTestEmail?: () => void;
  onSubjectChange?: (subject: string) => void;
  isLoading?: boolean;
  error?: string;
}

export interface EmailSectionProps {
  section: EmailSection;
  previewMode: PreviewMode;
  className?: string;
}

export interface JobCardProps {
  job: Job;
  previewMode: PreviewMode;
  showMatchScore?: boolean;
  compact?: boolean;
  className?: string;
}

export interface DeviceFrameProps {
  children: React.ReactNode;
  device: 'desktop' | 'mobile';
  className?: string;
}

export interface EmailGenerationResponse {
  success: boolean;
  emailTemplate?: EmailTemplate;
  error?: string;
  fallbackUsed?: boolean;
}

export interface TestEmailRequest {
  userId: string;
  emailTemplate: EmailTemplate;
  testEmailAddress?: string;
}

export interface TestEmailResponse {
  success: boolean;
  messageId?: string;
  error?: string;
}