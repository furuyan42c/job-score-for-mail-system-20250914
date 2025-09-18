/**
 * Test data fixtures for E2E tests
 */

export const TEST_USERS = {
  newUser: {
    firstName: 'Test',
    lastName: 'User',
    email: `testuser${Date.now()}@example.com`,
    password: 'SecurePassword123!',
    skills: 'JavaScript, TypeScript, React, Node.js',
    experience: '3-5 years',
    location: 'New York, NY'
  },

  existingUser: {
    email: 'existing.user@example.com',
    password: 'ExistingPassword123!',
    firstName: 'Existing',
    lastName: 'User'
  },

  adminUser: {
    email: 'admin@example.com',
    password: 'AdminPassword123!',
    role: 'admin'
  }
};

export const SAMPLE_JOBS = {
  frontendDeveloper: {
    title: 'Frontend Developer',
    company: 'TechCorp Inc.',
    location: 'San Francisco, CA',
    salary: '$80,000 - $120,000',
    type: 'full-time',
    experience: 'mid-level',
    skills: ['React', 'TypeScript', 'CSS', 'JavaScript'],
    description: 'We are looking for a talented Frontend Developer...'
  },

  backendEngineer: {
    title: 'Backend Engineer',
    company: 'DataSystems LLC',
    location: 'Austin, TX',
    salary: '$90,000 - $140,000',
    type: 'full-time',
    experience: 'senior',
    skills: ['Node.js', 'Python', 'PostgreSQL', 'AWS'],
    description: 'Join our backend team to build scalable systems...'
  },

  fullStackDeveloper: {
    title: 'Full Stack Developer',
    company: 'StartupXYZ',
    location: 'Remote',
    salary: '$70,000 - $100,000',
    type: 'full-time',
    experience: 'mid-level',
    skills: ['React', 'Node.js', 'MongoDB', 'Docker'],
    description: 'Looking for a versatile full stack developer...'
  }
};

export const SQL_QUERIES = {
  simple: {
    select: 'SELECT * FROM users LIMIT 10;',
    count: 'SELECT COUNT(*) as total_users FROM users;',
    basic_where: 'SELECT email, created_at FROM users WHERE active = true;'
  },

  complex: {
    join: `
      SELECT u.email, p.first_name, p.last_name, j.title as job_title
      FROM users u
      JOIN profiles p ON u.id = p.user_id
      LEFT JOIN applications a ON u.id = a.user_id
      LEFT JOIN jobs j ON a.job_id = j.id
      WHERE u.created_at > '2024-01-01'
      ORDER BY u.created_at DESC
      LIMIT 50;
    `,

    aggregation: `
      SELECT
        u.email,
        COUNT(DISTINCT a.id) as application_count,
        AVG(j.salary_min) as avg_salary_applied,
        MAX(a.created_at) as last_application
      FROM users u
      LEFT JOIN applications a ON u.id = a.user_id
      LEFT JOIN jobs j ON a.job_id = j.id
      WHERE u.created_at > '2023-01-01'
      GROUP BY u.id, u.email
      HAVING application_count > 0
      ORDER BY application_count DESC, avg_salary_applied DESC;
    `,

    window_function: `
      SELECT
        job_title,
        salary_min,
        salary_max,
        ROW_NUMBER() OVER (ORDER BY salary_max DESC) as salary_rank,
        DENSE_RANK() OVER (PARTITION BY industry ORDER BY salary_max DESC) as industry_rank
      FROM jobs
      WHERE status = 'active'
      ORDER BY salary_max DESC;
    `
  },

  invalid: {
    syntax_error: 'SELCT * FORM users;', // Deliberate typos
    missing_table: 'SELECT * FROM nonexistent_table;',
    permission_denied: 'DROP TABLE users;'
  },

  slow: {
    cartesian_product: 'SELECT * FROM users, jobs;', // Potentially slow without proper joins
    large_sort: 'SELECT * FROM users ORDER BY RANDOM() LIMIT 10000;'
  }
};

export const DASHBOARD_DATA = {
  batchStatuses: ['Running', 'Paused', 'Completed', 'Failed', 'Pending'],

  batchPhases: [
    'Initialization',
    'Data Collection',
    'Profile Analysis',
    'Job Matching',
    'Score Calculation',
    'Email Generation',
    'Finalization'
  ],

  logLevels: ['ERROR', 'WARNING', 'INFO', 'DEBUG'],

  reportTypes: ['performance', 'errors', 'usage', 'batch-history'],

  timeRanges: ['5m', '15m', '1h', '6h', '24h', '7d', '30d']
};

export const ERROR_MESSAGES = {
  auth: {
    invalidCredentials: 'Invalid email or password',
    accountLocked: 'Account temporarily locked',
    emailRequired: 'Email is required',
    passwordRequired: 'Password is required',
    passwordMismatch: 'Passwords do not match',
    invalidEmail: 'Please enter a valid email address',
    weakPassword: 'Password must be at least 8 characters long'
  },

  jobs: {
    noResults: 'No jobs found matching your criteria',
    loadError: 'Unable to load jobs',
    applicationError: 'Failed to submit application',
    networkError: 'Network error occurred'
  },

  sql: {
    syntaxError: 'syntax error',
    connectionError: 'connection',
    timeoutError: 'timeout',
    permissionError: 'permission'
  },

  dashboard: {
    loadError: 'unable to load',
    authError: 'authentication required',
    networkError: 'network error'
  }
};

export const PERFORMANCE_THRESHOLDS = {
  pageLoad: {
    fast: 1000,    // < 1s is fast
    acceptable: 3000, // < 3s is acceptable
    slow: 5000     // > 5s is slow
  },

  apiResponse: {
    fast: 500,     // < 500ms is fast
    acceptable: 2000, // < 2s is acceptable
    slow: 5000     // > 5s is slow
  },

  search: {
    fast: 1000,    // < 1s is fast
    acceptable: 3000, // < 3s is acceptable
    slow: 5000     // > 5s is slow
  }
};

export const VIEWPORT_SIZES = {
  mobile: {
    phone: { width: 375, height: 667 },
    phoneSmall: { width: 320, height: 568 }
  },

  tablet: {
    portrait: { width: 768, height: 1024 },
    landscape: { width: 1024, height: 768 }
  },

  desktop: {
    small: { width: 1280, height: 720 },
    medium: { width: 1440, height: 900 },
    large: { width: 1920, height: 1080 }
  }
};

/**
 * Utility functions for test data
 */
export class TestDataHelper {
  /**
   * Generate a unique email for testing
   */
  static generateUniqueEmail(prefix: string = 'test'): string {
    return `${prefix}${Date.now()}@example.com`;
  }

  /**
   * Generate test user with unique email
   */
  static generateTestUser(overrides: Partial<typeof TEST_USERS.newUser> = {}) {
    return {
      ...TEST_USERS.newUser,
      email: this.generateUniqueEmail(),
      ...overrides
    };
  }

  /**
   * Get random job from sample jobs
   */
  static getRandomJob() {
    const jobs = Object.values(SAMPLE_JOBS);
    return jobs[Math.floor(Math.random() * jobs.length)];
  }

  /**
   * Generate search keywords based on job data
   */
  static generateSearchKeywords(): string[] {
    const keywords = [
      'developer', 'engineer', 'frontend', 'backend', 'full stack',
      'javascript', 'react', 'node.js', 'python', 'typescript'
    ];
    return keywords;
  }

  /**
   * Get random SQL query by category
   */
  static getRandomQuery(category: keyof typeof SQL_QUERIES = 'simple'): string {
    const queries = Object.values(SQL_QUERIES[category]);
    return queries[Math.floor(Math.random() * queries.length)];
  }

  /**
   * Generate random date range for reports
   */
  static generateDateRange(daysBack: number = 30): { start: string; end: string } {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - daysBack);

    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  }
}