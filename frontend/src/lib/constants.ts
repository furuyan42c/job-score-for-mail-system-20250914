import { ExperienceLevel, JobType, CompanySize } from '@/types';

// Application Constants
export const APP_NAME = 'Job Match Pro';
export const APP_DESCRIPTION = 'AI-powered job matching platform';
export const APP_VERSION = '1.0.0';

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
export const API_TIMEOUT = 30000; // 30 seconds

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// File Upload
export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

// Experience Levels
export const EXPERIENCE_LEVELS: Array<{ value: ExperienceLevel; label: string; description: string }> = [
  {
    value: 'entry',
    label: 'Entry Level',
    description: '0-1 years of experience'
  },
  {
    value: 'junior',
    label: 'Junior',
    description: '1-3 years of experience'
  },
  {
    value: 'mid',
    label: 'Mid Level',
    description: '3-5 years of experience'
  },
  {
    value: 'senior',
    label: 'Senior',
    description: '5-8 years of experience'
  },
  {
    value: 'lead',
    label: 'Lead',
    description: '8+ years of experience'
  },
  {
    value: 'executive',
    label: 'Executive',
    description: '10+ years of experience'
  }
];

// Job Types
export const JOB_TYPES: Array<{ value: JobType; label: string; description: string }> = [
  {
    value: 'full-time',
    label: 'Full-time',
    description: '40+ hours per week'
  },
  {
    value: 'part-time',
    label: 'Part-time',
    description: 'Less than 40 hours per week'
  },
  {
    value: 'contract',
    label: 'Contract',
    description: 'Fixed-term employment'
  },
  {
    value: 'freelance',
    label: 'Freelance',
    description: 'Project-based work'
  },
  {
    value: 'internship',
    label: 'Internship',
    description: 'Learning opportunity'
  }
];

// Location Types
export const LOCATION_TYPES = [
  {
    value: 'remote',
    label: 'Remote',
    description: 'Work from anywhere'
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    description: 'Mix of remote and office'
  },
  {
    value: 'onsite',
    label: 'On-site',
    description: 'Work from office'
  }
];

// Company Sizes
export const COMPANY_SIZES: Array<{ value: CompanySize; label: string; description: string }> = [
  {
    value: 'startup',
    label: 'Startup',
    description: '1-10 employees'
  },
  {
    value: 'small',
    label: 'Small',
    description: '11-50 employees'
  },
  {
    value: 'medium',
    label: 'Medium',
    description: '51-200 employees'
  },
  {
    value: 'large',
    label: 'Large',
    description: '201-1000 employees'
  },
  {
    value: 'enterprise',
    label: 'Enterprise',
    description: '1000+ employees'
  }
];

// Popular Skills (for autocomplete)
export const POPULAR_SKILLS = [
  // Programming Languages
  'JavaScript', 'TypeScript', 'Python', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby',
  'Swift', 'Kotlin', 'Dart', 'Scala', 'R', 'MATLAB', 'SQL',

  // Frontend
  'React', 'Vue.js', 'Angular', 'Svelte', 'Next.js', 'Nuxt.js', 'HTML', 'CSS', 'Sass',
  'Tailwind CSS', 'Bootstrap', 'Material-UI', 'Chakra UI', 'Styled Components',

  // Backend
  'Node.js', 'Express.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Laravel',
  'Ruby on Rails', 'ASP.NET', 'GraphQL', 'REST API', 'Microservices',

  // Databases
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'SQLite', 'Oracle',
  'Cassandra', 'DynamoDB', 'Firebase',

  // Cloud & DevOps
  'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Terraform', 'Jenkins',
  'GitLab CI', 'GitHub Actions', 'Ansible', 'Nginx', 'Apache',

  // Mobile
  'React Native', 'Flutter', 'iOS Development', 'Android Development', 'Xamarin',

  // Data & AI
  'Machine Learning', 'Deep Learning', 'Data Science', 'Pandas', 'NumPy', 'TensorFlow',
  'PyTorch', 'Scikit-learn', 'Jupyter', 'Apache Spark', 'Tableau', 'Power BI',

  // Design
  'UI/UX Design', 'Figma', 'Adobe XD', 'Sketch', 'Photoshop', 'Illustrator',
  'User Research', 'Prototyping', 'Wireframing',

  // Project Management
  'Agile', 'Scrum', 'Kanban', 'Jira', 'Confluence', 'Trello', 'Asana',
  'Project Management', 'Product Management',

  // Other
  'Git', 'Linux', 'Testing', 'Jest', 'Cypress', 'Selenium', 'Unit Testing',
  'Integration Testing', 'Security', 'Performance Optimization'
];

// Industries
export const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'E-commerce',
  'Gaming',
  'Media & Entertainment',
  'Manufacturing',
  'Real Estate',
  'Transportation',
  'Energy',
  'Government',
  'Non-profit',
  'Consulting',
  'Marketing',
  'Sales',
  'Legal',
  'Construction',
  'Agriculture',
  'Hospitality'
];

// Benefits
export const COMMON_BENEFITS = [
  'Health Insurance',
  'Dental Insurance',
  'Vision Insurance',
  'Life Insurance',
  '401(k) Plan',
  'Paid Time Off',
  'Sick Leave',
  'Parental Leave',
  'Flexible Schedule',
  'Remote Work',
  'Professional Development',
  'Training Budget',
  'Conference Attendance',
  'Gym Membership',
  'Commuter Benefits',
  'Free Meals',
  'Stock Options',
  'Bonus Opportunities',
  'Tuition Reimbursement',
  'Mental Health Support'
];

// Work Culture Keywords
export const WORK_CULTURE_KEYWORDS = [
  'Collaborative',
  'Innovative',
  'Fast-paced',
  'Startup Culture',
  'Work-life Balance',
  'Diverse & Inclusive',
  'Results-oriented',
  'Learning & Growth',
  'Flexible',
  'Team-oriented',
  'Autonomous',
  'Creative',
  'Data-driven',
  'Customer-focused',
  'Mission-driven'
];

// Salary Ranges (in USD per year)
export const SALARY_RANGES = [
  { min: 0, max: 40000, label: 'Under $40k' },
  { min: 40000, max: 60000, label: '$40k - $60k' },
  { min: 60000, max: 80000, label: '$60k - $80k' },
  { min: 80000, max: 100000, label: '$80k - $100k' },
  { min: 100000, max: 120000, label: '$100k - $120k' },
  { min: 120000, max: 150000, label: '$120k - $150k' },
  { min: 150000, max: 200000, label: '$150k - $200k' },
  { min: 200000, max: 300000, label: '$200k - $300k' },
  { min: 300000, max: Infinity, label: '$300k+' }
];

// Match Score Thresholds
export const MATCH_SCORE_THRESHOLDS = {
  EXCELLENT: 90,
  GOOD: 75,
  FAIR: 60,
  POOR: 40
};

// Animation Durations (in milliseconds)
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500
};

// Breakpoints (matches Tailwind defaults)
export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536
};

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'job-match-user-preferences',
  SEARCH_HISTORY: 'job-match-search-history',
  VIEWED_JOBS: 'job-match-viewed-jobs',
  THEME: 'job-match-theme',
  SIDEBAR_COLLAPSED: 'job-match-sidebar-collapsed'
};

// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/profile'
  },
  JOBS: {
    LIST: '/jobs',
    DETAIL: (id: string) => `/jobs/${id}`,
    SEARCH: '/jobs/search',
    RECOMMENDATIONS: '/jobs/recommendations',
    APPLY: (id: string) => `/jobs/${id}/apply`
  },
  USERS: {
    PROFILE: '/users/profile',
    PREFERENCES: '/users/preferences',
    SKILLS: '/users/skills',
    RESUME: '/users/resume'
  },
  MATCHES: {
    LIST: '/matches',
    FEEDBACK: (id: string) => `/matches/${id}/feedback`
  },
  APPLICATIONS: {
    LIST: '/applications',
    DETAIL: (id: string) => `/applications/${id}`,
    WITHDRAW: (id: string) => `/applications/${id}/withdraw`
  }
};

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'Something went wrong. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION: 'Please check your input and try again.',
  FILE_TOO_LARGE: `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`,
  INVALID_FILE_TYPE: 'Invalid file type. Please upload a PDF or Word document.'
};

// Success Messages
export const SUCCESS_MESSAGES = {
  PROFILE_UPDATED: 'Profile updated successfully',
  APPLICATION_SUBMITTED: 'Application submitted successfully',
  PREFERENCES_SAVED: 'Preferences saved successfully',
  FILE_UPLOADED: 'File uploaded successfully'
};