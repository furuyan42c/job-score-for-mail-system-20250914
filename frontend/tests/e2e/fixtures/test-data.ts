/**
 * Test data fixtures for E2E tests
 */

export const testTables = [
  'users',
  'jobs',
  'jobs_match_raw',
  'jobs_contents_raw',
  'user_actions',
  'daily_email_queue',
  'job_enrichment',
  'user_job_mapping',
  'daily_job_picks',
  'user_profiles',
  'keyword_scoring',
  'semrush_keywords',
  'occupation_master',
  'prefecture_master',
  'city_master',
  'employment_type_master',
  'salary_type_master',
  'feature_master',
  'needs_category_master'
];

export const testQueries = {
  simple: {
    valid: [
      'SELECT * FROM users LIMIT 5;',
      'SELECT * FROM prefecture_master WHERE name = "東京都";',
      'SELECT COUNT(*) FROM jobs;',
      'SELECT job_id, application_name FROM jobs LIMIT 3;'
    ],
    invalid: [
      'INVALID SQL QUERY',
      'SELECT * FROM nonexistent_table;',
      'SELECT missing_column FROM users;',
      'DROPP TABLE users;' // Typo in DROP
    ]
  },
  complex: {
    joins: [
      `SELECT u.email, j.application_name
       FROM users u
       JOIN user_actions ua ON u.user_id = ua.user_id
       JOIN jobs j ON ua.job_id = j.job_id
       LIMIT 5;`,
      `SELECT p.name AS prefecture, COUNT(j.job_id) AS job_count
       FROM prefecture_master p
       LEFT JOIN jobs j ON p.pref_cd = j.pref_cd
       GROUP BY p.name
       ORDER BY job_count DESC
       LIMIT 10;`
    ],
    aggregates: [
      'SELECT COUNT(*) as total_users FROM users WHERE is_active = true;',
      'SELECT AVG(score) as avg_score FROM jobs WHERE score > 0;',
      'SELECT MAX(created_at) as latest_job FROM jobs;'
    ]
  }
};

export const testViewports = {
  desktop: { width: 1920, height: 1080 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 },
  ultrawide: { width: 2560, height: 1440 },
  laptop: { width: 1366, height: 768 }
};

export const expectedTableCounts = {
  users: 10000,
  jobs: 100000,
  jobs_match_raw: 100000,
  jobs_contents_raw: 100000,
  user_actions: 85000,
  daily_email_queue: 30000,
  job_enrichment: 100000,
  user_job_mapping: 400000,
  daily_job_picks: 40000,
  user_profiles: 10000,
  keyword_scoring: 5000,
  semrush_keywords: 5000,
  occupation_master: 500,
  prefecture_master: 47,
  city_master: 1741,
  employment_type_master: 10,
  salary_type_master: 5,
  feature_master: 200,
  needs_category_master: 14
};

export const testUsers = {
  valid: [
    {
      user_id: "550e8400-e29b-41d4-a716-446655440000",
      email: "test1@example.com",
      age_range: "20-24",
      gender: "男性",
      is_active: true
    },
    {
      user_id: "550e8400-e29b-41d4-a716-446655440001",
      email: "test2@example.com",
      age_range: "25-29",
      gender: "女性",
      is_active: false
    }
  ]
};

export const testJobs = {
  valid: [
    {
      job_id: 421505257,
      import_from: "giga-baito",
      client_cd: "arubaitoex",
      application_name: "テストバイト募集",
      company_name: "テスト会社",
      min_salary: 1000,
      max_salary: 1500,
      pref_cd: 13,
      city_cd: 13113,
      score: 100000
    }
  ]
};

export const sampleSearchTerms = [
  'users',
  'jobs',
  'master',
  'prefecture',
  'salary',
  'employment',
  'nonexistent' // Should return no results
];

export const expectedColumns = {
  users: ['user_id', 'email', 'age_range', 'gender', 'is_active', 'created_at', 'updated_at'],
  jobs: ['job_id', 'import_from', 'client_cd', 'endcl_cd', 'application_name', 'company_name'],
  prefecture_master: ['pref_cd', 'url_segment', 'name', 'region', 'category_id']
};

export const testTimeouts = {
  short: 5000,
  medium: 10000,
  long: 30000,
  query: 15000,
  navigation: 30000
};

export const testMessages = {
  loading: [
    '実行中...',
    'Loading...',
    '読み込み中'
  ],
  error: [
    'エラー',
    'Error',
    'failed',
    'not found',
    'invalid'
  ],
  success: [
    '完了',
    'success',
    'Success',
    'rows'
  ],
  notImplemented: [
    'モック',
    'mock',
    'not implemented',
    '実装予定',
    'coming soon'
  ]
};

export const performanceThresholds = {
  pageLoad: 5000, // 5 seconds
  queryExecution: 10000, // 10 seconds
  tabSwitch: 1000, // 1 second
  search: 2000, // 2 seconds
  tableLoad: 3000 // 3 seconds
};