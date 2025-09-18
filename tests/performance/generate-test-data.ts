/**
 * Test Data Generator for Performance Tests
 *
 * Generates large-scale test data for performance testing:
 * - 100K jobs with realistic distribution
 * - 10K users with varied preferences
 * - Historical action data
 * - Export to CSV/JSON formats
 * - Configurable data patterns and sizes
 */

import fs from 'fs';
import path from 'path';
import { performance } from 'perf_hooks';
import { createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';
import { Transform } from 'stream';

// Configuration
interface DataGenerationConfig {
  jobs: {
    count: number;
    distribution: JobDistribution;
  };
  users: {
    count: number;
    distribution: UserDistribution;
  };
  actions: {
    count: number;
    types: ActionType[];
  };
  output: {
    formats: ('csv' | 'json' | 'sql')[];
    chunkSize: number;
    compression: boolean;
  };
}

interface JobDistribution {
  prefectures: { code: string; weight: number }[];
  salaryRanges: { min: number; max: number; weight: number }[];
  categories: { code: number; name: string; weight: number }[];
  companies: { sizes: ('startup' | 'small' | 'medium' | 'large')[] };
  features: { [key: string]: number }; // probability of each feature
}

interface UserDistribution {
  ageGroups: { range: string; weight: number }[];
  genders: { type: string; weight: number }[];
  locations: { prefecture: string; weight: number }[];
  preferences: { categories: number[]; salaryExpectations: number[] };
  activityLevels: { level: string; weight: number }[];
}

interface ActionType {
  type: 'view' | 'click' | 'apply' | 'save' | 'search';
  weight: number;
  frequency: number; // actions per user on average
}

interface GeneratedJob {
  endcl_cd: string;
  company_name: string;
  application_name: string;
  prefecture_code: string;
  city_code: string;
  station_name?: string;
  address?: string;
  salary_type: 'hourly' | 'daily' | 'monthly';
  min_salary: number;
  max_salary: number;
  fee: number;
  occupation_cd1: number;
  occupation_cd2: number;
  has_daily_payment: boolean;
  has_no_experience: boolean;
  has_student_welcome: boolean;
  has_remote_work: boolean;
  posting_date: string;
  created_at: string;
  updated_at: string;
}

interface GeneratedUser {
  user_id: number;
  email: string;
  email_hash: string;
  age_group: string;
  gender: string;
  estimated_pref_cd: string;
  estimated_city_cd: string;
  preferred_categories: number[];
  preferred_salary_min: number;
  location_preference_radius: number;
  application_count: number;
  click_count: number;
  view_count: number;
  avg_salary_preference: number;
  registration_date: string;
  created_at: string;
  updated_at: string;
}

interface GeneratedAction {
  action_id: number;
  user_id: number;
  job_id: number;
  action_type: string;
  timestamp: string;
  session_id: string;
  additional_data?: Record<string, any>;
}

class TestDataGenerator {
  private config: DataGenerationConfig;
  private outputDir: string;
  private random: () => number;

  constructor(config?: Partial<DataGenerationConfig>) {
    this.outputDir = path.join(__dirname, 'test-data');
    this.ensureOutputDirectory();

    this.config = this.mergeConfig(config);
    this.random = this.createSeededRandom(42); // Fixed seed for reproducible data
  }

  private mergeConfig(config?: Partial<DataGenerationConfig>): DataGenerationConfig {
    return {
      jobs: {
        count: 100000,
        distribution: {
          prefectures: [
            { code: '13', weight: 0.3 }, // Tokyo
            { code: '27', weight: 0.15 }, // Osaka
            { code: '23', weight: 0.1 }, // Aichi (Nagoya)
            { code: '40', weight: 0.08 }, // Fukuoka
            { code: '14', weight: 0.07 }, // Kanagawa (Yokohama)
            { code: '12', weight: 0.05 }, // Chiba
            { code: '11', weight: 0.05 }, // Saitama
            { code: '28', weight: 0.04 }, // Hyogo (Kobe)
            { code: '01', weight: 0.03 }, // Hokkaido
            { code: '22', weight: 0.13 }, // Other prefectures
          ],
          salaryRanges: [
            { min: 800, max: 1200, weight: 0.2 },
            { min: 1000, max: 1500, weight: 0.25 },
            { min: 1300, max: 1800, weight: 0.2 },
            { min: 1600, max: 2200, weight: 0.15 },
            { min: 2000, max: 3000, weight: 0.1 },
            { min: 2500, max: 4000, weight: 0.07 },
            { min: 3500, max: 5000, weight: 0.03 },
          ],
          categories: [
            { code: 100, name: 'Office Work', weight: 0.25 },
            { code: 200, name: 'Sales', weight: 0.18 },
            { code: 300, name: 'Service Industry', weight: 0.15 },
            { code: 400, name: 'Manufacturing', weight: 0.12 },
            { code: 500, name: 'IT/Tech', weight: 0.1 },
            { code: 600, name: 'Healthcare', weight: 0.08 },
            { code: 700, name: 'Education', weight: 0.05 },
            { code: 800, name: 'Construction', weight: 0.04 },
            { code: 900, name: 'Transportation', weight: 0.03 },
          ],
          companies: {
            sizes: ['startup', 'small', 'medium', 'large'],
          },
          features: {
            has_daily_payment: 0.3,
            has_no_experience: 0.4,
            has_student_welcome: 0.25,
            has_remote_work: 0.15,
          },
        },
        ...config?.jobs,
      },
      users: {
        count: 10000,
        distribution: {
          ageGroups: [
            { range: '18-22', weight: 0.15 },
            { range: '23-27', weight: 0.2 },
            { range: '28-32', weight: 0.18 },
            { range: '33-37', weight: 0.15 },
            { range: '38-42', weight: 0.12 },
            { range: '43-47', weight: 0.1 },
            { range: '48-52', weight: 0.05 },
            { range: '53+', weight: 0.05 },
          ],
          genders: [
            { type: 'male', weight: 0.52 },
            { type: 'female', weight: 0.48 },
          ],
          locations: [
            { prefecture: '13', weight: 0.28 },
            { prefecture: '27', weight: 0.12 },
            { prefecture: '23', weight: 0.08 },
            { prefecture: '40', weight: 0.06 },
            { prefecture: '14', weight: 0.05 },
            { prefecture: 'other', weight: 0.41 },
          ],
          preferences: {
            categories: [100, 200, 300, 400, 500],
            salaryExpectations: [1000, 1300, 1600, 2000, 2500],
          },
          activityLevels: [
            { level: 'low', weight: 0.4 }, // 0-5 applications
            { level: 'medium', weight: 0.4 }, // 5-15 applications
            { level: 'high', weight: 0.15 }, // 15-30 applications
            { level: 'very_high', weight: 0.05 }, // 30+ applications
          ],
        },
        ...config?.users,
      },
      actions: {
        count: 500000,
        types: [
          { type: 'view', weight: 0.5, frequency: 50 },
          { type: 'click', weight: 0.25, frequency: 15 },
          { type: 'apply', weight: 0.1, frequency: 3 },
          { type: 'save', weight: 0.1, frequency: 8 },
          { type: 'search', weight: 0.05, frequency: 20 },
        ],
        ...config?.actions,
      },
      output: {
        formats: ['csv', 'json'],
        chunkSize: 1000,
        compression: true,
        ...config?.output,
      },
    };
  }

  private ensureOutputDirectory(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  private createSeededRandom(seed: number): () => number {
    let current = seed;
    return () => {
      current = (current * 9301 + 49297) % 233280;
      return current / 233280;
    };
  }

  async generateAllTestData(): Promise<{
    jobs: { file: string; count: number };
    users: { file: string; count: number };
    actions: { file: string; count: number };
    duration: number;
  }> {
    console.log('🚀 Starting comprehensive test data generation...');

    const startTime = performance.now();

    console.log(`📊 Configuration:`);
    console.log(`  Jobs: ${this.config.jobs.count.toLocaleString()}`);
    console.log(`  Users: ${this.config.users.count.toLocaleString()}`);
    console.log(`  Actions: ${this.config.actions.count.toLocaleString()}`);
    console.log(`  Output formats: ${this.config.output.formats.join(', ')}`);

    // Generate data in parallel where possible
    const [jobsResult, usersResult] = await Promise.all([
      this.generateJobs(),
      this.generateUsers(),
    ]);

    // Generate actions after users and jobs are available
    const actionsResult = await this.generateActions();

    const endTime = performance.now();
    const duration = endTime - startTime;

    console.log(`\n✅ Test data generation completed in ${Math.round(duration / 1000)}s`);
    console.log(`📁 Output directory: ${this.outputDir}`);

    return {
      jobs: jobsResult,
      users: usersResult,
      actions: actionsResult,
      duration,
    };
  }

  private async generateJobs(): Promise<{ file: string; count: number }> {
    console.log('\n📋 Generating jobs...');

    const count = this.config.jobs.count;
    const batchSize = this.config.output.chunkSize;

    // Generate jobs in batches to manage memory
    const jobs: GeneratedJob[] = [];
    const startTime = performance.now();

    for (let batch = 0; batch < Math.ceil(count / batchSize); batch++) {
      const batchStart = batch * batchSize;
      const batchEnd = Math.min(batchStart + batchSize, count);
      const batchJobs = [];

      for (let i = batchStart; i < batchEnd; i++) {
        batchJobs.push(this.generateJob(i + 1));
      }

      jobs.push(...batchJobs);

      if ((batch + 1) % 100 === 0) {
        const progress = Math.round(((batch + 1) * batchSize / count) * 100);
        console.log(`  Progress: ${progress}% (${jobs.length.toLocaleString()} jobs)`);
      }
    }

    const generationTime = performance.now() - startTime;
    console.log(`  Generated ${jobs.length.toLocaleString()} jobs in ${Math.round(generationTime / 1000)}s`);

    // Export to configured formats
    const results = await Promise.all(
      this.config.output.formats.map(format => this.exportJobs(jobs, format))
    );

    return {
      file: results[0], // Return primary format file
      count: jobs.length,
    };
  }

  private generateJob(id: number): GeneratedJob {
    const prefecture = this.selectWeighted(this.config.jobs.distribution.prefectures);
    const salaryRange = this.selectWeighted(this.config.jobs.distribution.salaryRanges);
    const category = this.selectWeighted(this.config.jobs.distribution.categories);
    const companySize = this.selectRandom(this.config.jobs.distribution.companies.sizes);

    // Generate realistic salary within range
    const salaryVariation = this.random() * 0.4 + 0.8; // 80-120% of base
    const minSalary = Math.round(salaryRange.min * salaryVariation);
    const maxSalary = Math.round(salaryRange.max * salaryVariation);

    // Company name based on size and category
    const companyName = this.generateCompanyName(companySize, category.name, id);

    // Job features based on probabilities
    const features = this.config.jobs.distribution.features;

    const now = new Date();
    const postingDate = new Date(now.getTime() - Math.random() * 30 * 24 * 60 * 60 * 1000); // Last 30 days

    return {
      endcl_cd: `JOB${id.toString().padStart(8, '0')}`,
      company_name: companyName,
      application_name: this.generateJobTitle(category.name, id),
      prefecture_code: prefecture.code,
      city_code: `${prefecture.code}${Math.floor(this.random() * 900 + 100)}`,
      station_name: this.random() < 0.6 ? this.generateStationName() : undefined,
      address: this.random() < 0.8 ? this.generateAddress(prefecture.code) : undefined,
      salary_type: this.selectRandom(['hourly', 'daily', 'monthly'] as const),
      min_salary: minSalary,
      max_salary: maxSalary,
      fee: Math.round(this.random() * 3000 + 500),
      occupation_cd1: category.code,
      occupation_cd2: category.code + Math.floor(this.random() * 10) + 1,
      has_daily_payment: this.random() < features.has_daily_payment,
      has_no_experience: this.random() < features.has_no_experience,
      has_student_welcome: this.random() < features.has_student_welcome,
      has_remote_work: this.random() < features.has_remote_work,
      posting_date: postingDate.toISOString().split('T')[0],
      created_at: postingDate.toISOString(),
      updated_at: postingDate.toISOString(),
    };
  }

  private async generateUsers(): Promise<{ file: string; count: number }> {
    console.log('\n👥 Generating users...');

    const count = this.config.users.count;
    const users: GeneratedUser[] = [];
    const startTime = performance.now();

    for (let i = 1; i <= count; i++) {
      users.push(this.generateUser(i));

      if (i % 1000 === 0) {
        const progress = Math.round((i / count) * 100);
        console.log(`  Progress: ${progress}% (${i.toLocaleString()} users)`);
      }
    }

    const generationTime = performance.now() - startTime;
    console.log(`  Generated ${users.length.toLocaleString()} users in ${Math.round(generationTime / 1000)}s`);

    // Export to configured formats
    const results = await Promise.all(
      this.config.output.formats.map(format => this.exportUsers(users, format))
    );

    return {
      file: results[0],
      count: users.length,
    };
  }

  private generateUser(id: number): GeneratedUser {
    const ageGroup = this.selectWeighted(this.config.users.distribution.ageGroups);
    const gender = this.selectWeighted(this.config.users.distribution.genders);
    const location = this.selectWeighted(this.config.users.distribution.locations);
    const activityLevel = this.selectWeighted(this.config.users.distribution.activityLevels);

    const prefecture = location.prefecture === 'other' ?
      this.selectRandom(['01', '02', '03', '04', '05', '06']) : location.prefecture;

    // Activity counts based on level
    const activityMultipliers = {
      low: { applications: [0, 5], clicks: [5, 25], views: [20, 100] },
      medium: { applications: [5, 15], clicks: [25, 75], views: [100, 300] },
      high: { applications: [15, 30], clicks: [75, 150], views: [300, 600] },
      very_high: { applications: [30, 50], clicks: [150, 250], views: [600, 1000] },
    };

    const multiplier = activityMultipliers[activityLevel.level as keyof typeof activityMultipliers];

    // Registration date (last 2 years)
    const registrationDate = new Date();
    registrationDate.setDate(registrationDate.getDate() - Math.floor(this.random() * 730));

    return {
      user_id: id,
      email: `user${id}@testdomain${Math.floor(this.random() * 10) + 1}.com`,
      email_hash: this.generateEmailHash(id),
      age_group: ageGroup.range,
      gender: gender.type,
      estimated_pref_cd: prefecture,
      estimated_city_cd: `${prefecture}${Math.floor(this.random() * 900 + 100)}`,
      preferred_categories: this.selectMultiple(
        this.config.users.distribution.preferences.categories,
        Math.floor(this.random() * 3) + 1
      ),
      preferred_salary_min: this.selectRandom(this.config.users.distribution.preferences.salaryExpectations),
      location_preference_radius: Math.floor(this.random() * 40) + 10,
      application_count: Math.floor(
        this.random() * (multiplier.applications[1] - multiplier.applications[0]) + multiplier.applications[0]
      ),
      click_count: Math.floor(
        this.random() * (multiplier.clicks[1] - multiplier.clicks[0]) + multiplier.clicks[0]
      ),
      view_count: Math.floor(
        this.random() * (multiplier.views[1] - multiplier.views[0]) + multiplier.views[0]
      ),
      avg_salary_preference: Math.floor(this.random() * 2000) + 1200,
      registration_date: registrationDate.toISOString().split('T')[0],
      created_at: registrationDate.toISOString(),
      updated_at: registrationDate.toISOString(),
    };
  }

  private async generateActions(): Promise<{ file: string; count: number }> {
    console.log('\n🎯 Generating user actions...');

    const count = this.config.actions.count;
    const actions: GeneratedAction[] = [];
    const startTime = performance.now();

    // Generate actions based on user and job distributions
    for (let i = 1; i <= count; i++) {
      actions.push(this.generateAction(i));

      if (i % 10000 === 0) {
        const progress = Math.round((i / count) * 100);
        console.log(`  Progress: ${progress}% (${i.toLocaleString()} actions)`);
      }
    }

    const generationTime = performance.now() - startTime;
    console.log(`  Generated ${actions.length.toLocaleString()} actions in ${Math.round(generationTime / 1000)}s`);

    // Export to configured formats
    const results = await Promise.all(
      this.config.output.formats.map(format => this.exportActions(actions, format))
    );

    return {
      file: results[0],
      count: actions.length,
    };
  }

  private generateAction(id: number): GeneratedAction {
    const actionType = this.selectWeighted(this.config.actions.types);
    const userId = Math.floor(this.random() * this.config.users.count) + 1;
    const jobId = Math.floor(this.random() * this.config.jobs.count) + 1;

    // Generate realistic timestamp (last 90 days)
    const timestamp = new Date();
    timestamp.setTime(timestamp.getTime() - Math.random() * 90 * 24 * 60 * 60 * 1000);

    return {
      action_id: id,
      user_id: userId,
      job_id: jobId,
      action_type: actionType.type,
      timestamp: timestamp.toISOString(),
      session_id: this.generateSessionId(userId, timestamp),
      additional_data: this.generateActionData(actionType.type),
    };
  }

  // Export functions
  private async exportJobs(jobs: GeneratedJob[], format: 'csv' | 'json' | 'sql'): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `jobs_${jobs.length}_${timestamp}.${format}`;
    const filepath = path.join(this.outputDir, filename);

    console.log(`  Exporting to ${format.toUpperCase()}: ${filename}`);

    switch (format) {
      case 'csv':
        await this.exportJobsCSV(jobs, filepath);
        break;
      case 'json':
        await this.exportJobsJSON(jobs, filepath);
        break;
      case 'sql':
        await this.exportJobsSQL(jobs, filepath);
        break;
    }

    return filepath;
  }

  private async exportJobsCSV(jobs: GeneratedJob[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    // Write CSV header
    const headers = Object.keys(jobs[0]).join(',');
    writeStream.write(headers + '\n');

    // Write data in chunks
    const chunkSize = 1000;
    for (let i = 0; i < jobs.length; i += chunkSize) {
      const chunk = jobs.slice(i, i + chunkSize);
      const csvChunk = chunk.map(job => {
        return Object.values(job).map(value => {
          if (value === null || value === undefined) return '';
          if (typeof value === 'string' && value.includes(',')) return `"${value}"`;
          if (Array.isArray(value)) return `"${value.join(';')}"`;
          return String(value);
        }).join(',');
      }).join('\n');

      writeStream.write(csvChunk + '\n');
    }

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  private async exportJobsJSON(jobs: GeneratedJob[], filepath: string): Promise<void> {
    const data = {
      metadata: {
        count: jobs.length,
        generated_at: new Date().toISOString(),
        format: 'jobs_test_data',
        version: '1.0',
      },
      jobs,
    };

    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  }

  private async exportJobsSQL(jobs: GeneratedJob[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    writeStream.write('-- Generated Jobs Test Data\n');
    writeStream.write('-- Generated at: ' + new Date().toISOString() + '\n\n');

    writeStream.write('CREATE TABLE IF NOT EXISTS jobs (\n');
    writeStream.write('  id SERIAL PRIMARY KEY,\n');
    writeStream.write('  endcl_cd VARCHAR(20) UNIQUE NOT NULL,\n');
    writeStream.write('  company_name VARCHAR(200),\n');
    writeStream.write('  application_name VARCHAR(200),\n');
    writeStream.write('  prefecture_code VARCHAR(2),\n');
    writeStream.write('  city_code VARCHAR(5),\n');
    writeStream.write('  station_name VARCHAR(100),\n');
    writeStream.write('  address TEXT,\n');
    writeStream.write('  salary_type VARCHAR(20),\n');
    writeStream.write('  min_salary INTEGER,\n');
    writeStream.write('  max_salary INTEGER,\n');
    writeStream.write('  fee INTEGER,\n');
    writeStream.write('  occupation_cd1 INTEGER,\n');
    writeStream.write('  occupation_cd2 INTEGER,\n');
    writeStream.write('  has_daily_payment BOOLEAN,\n');
    writeStream.write('  has_no_experience BOOLEAN,\n');
    writeStream.write('  has_student_welcome BOOLEAN,\n');
    writeStream.write('  has_remote_work BOOLEAN,\n');
    writeStream.write('  posting_date DATE,\n');
    writeStream.write('  created_at TIMESTAMP,\n');
    writeStream.write('  updated_at TIMESTAMP\n');
    writeStream.write(');\n\n');

    // Write data in batches
    const batchSize = 100;
    for (let i = 0; i < jobs.length; i += batchSize) {
      const batch = jobs.slice(i, i + batchSize);

      writeStream.write('INSERT INTO jobs (endcl_cd, company_name, application_name, prefecture_code, city_code, station_name, address, salary_type, min_salary, max_salary, fee, occupation_cd1, occupation_cd2, has_daily_payment, has_no_experience, has_student_welcome, has_remote_work, posting_date, created_at, updated_at) VALUES\n');

      const values = batch.map((job, index) => {
        const values = [
          `'${job.endcl_cd}'`,
          `'${job.company_name.replace(/'/g, "''")}'`,
          `'${job.application_name.replace(/'/g, "''")}'`,
          `'${job.prefecture_code}'`,
          `'${job.city_code}'`,
          job.station_name ? `'${job.station_name.replace(/'/g, "''")}'` : 'NULL',
          job.address ? `'${job.address.replace(/'/g, "''")}'` : 'NULL',
          `'${job.salary_type}'`,
          job.min_salary,
          job.max_salary,
          job.fee,
          job.occupation_cd1,
          job.occupation_cd2,
          job.has_daily_payment,
          job.has_no_experience,
          job.has_student_welcome,
          job.has_remote_work,
          `'${job.posting_date}'`,
          `'${job.created_at}'`,
          `'${job.updated_at}'`,
        ];

        return `  (${values.join(', ')})`;
      });

      writeStream.write(values.join(',\n') + ';\n\n');
    }

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  private async exportUsers(users: GeneratedUser[], format: 'csv' | 'json' | 'sql'): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `users_${users.length}_${timestamp}.${format}`;
    const filepath = path.join(this.outputDir, filename);

    console.log(`  Exporting to ${format.toUpperCase()}: ${filename}`);

    switch (format) {
      case 'csv':
        await this.exportUsersCSV(users, filepath);
        break;
      case 'json':
        fs.writeFileSync(filepath, JSON.stringify({ metadata: { count: users.length, generated_at: new Date().toISOString() }, users }, null, 2));
        break;
      case 'sql':
        await this.exportUsersSQL(users, filepath);
        break;
    }

    return filepath;
  }

  private async exportUsersCSV(users: GeneratedUser[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    const headers = Object.keys(users[0]).join(',');
    writeStream.write(headers + '\n');

    users.forEach(user => {
      const row = Object.values(user).map(value => {
        if (value === null || value === undefined) return '';
        if (Array.isArray(value)) return `"${value.join(';')}"`;
        if (typeof value === 'string' && value.includes(',')) return `"${value}"`;
        return String(value);
      }).join(',');
      writeStream.write(row + '\n');
    });

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  private async exportUsersSQL(users: GeneratedUser[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    writeStream.write('-- Generated Users Test Data\n\n');

    writeStream.write('CREATE TABLE IF NOT EXISTS users (\n');
    writeStream.write('  user_id INTEGER PRIMARY KEY,\n');
    writeStream.write('  email VARCHAR(255) UNIQUE,\n');
    writeStream.write('  email_hash VARCHAR(64),\n');
    writeStream.write('  age_group VARCHAR(10),\n');
    writeStream.write('  gender VARCHAR(10),\n');
    writeStream.write('  estimated_pref_cd VARCHAR(2),\n');
    writeStream.write('  estimated_city_cd VARCHAR(5),\n');
    writeStream.write('  preferred_categories TEXT,\n');
    writeStream.write('  preferred_salary_min INTEGER,\n');
    writeStream.write('  location_preference_radius INTEGER,\n');
    writeStream.write('  application_count INTEGER,\n');
    writeStream.write('  click_count INTEGER,\n');
    writeStream.write('  view_count INTEGER,\n');
    writeStream.write('  avg_salary_preference INTEGER,\n');
    writeStream.write('  registration_date DATE,\n');
    writeStream.write('  created_at TIMESTAMP,\n');
    writeStream.write('  updated_at TIMESTAMP\n');
    writeStream.write(');\n\n');

    // Insert users in batches
    const batchSize = 100;
    for (let i = 0; i < users.length; i += batchSize) {
      const batch = users.slice(i, i + batchSize);

      writeStream.write('INSERT INTO users (user_id, email, email_hash, age_group, gender, estimated_pref_cd, estimated_city_cd, preferred_categories, preferred_salary_min, location_preference_radius, application_count, click_count, view_count, avg_salary_preference, registration_date, created_at, updated_at) VALUES\n');

      const values = batch.map(user => {
        return `  (${user.user_id}, '${user.email}', '${user.email_hash}', '${user.age_group}', '${user.gender}', '${user.estimated_pref_cd}', '${user.estimated_city_cd}', '${user.preferred_categories.join(',')}', ${user.preferred_salary_min}, ${user.location_preference_radius}, ${user.application_count}, ${user.click_count}, ${user.view_count}, ${user.avg_salary_preference}, '${user.registration_date}', '${user.created_at}', '${user.updated_at}')`;
      });

      writeStream.write(values.join(',\n') + ';\n\n');
    }

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  private async exportActions(actions: GeneratedAction[], format: 'csv' | 'json' | 'sql'): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `actions_${actions.length}_${timestamp}.${format}`;
    const filepath = path.join(this.outputDir, filename);

    console.log(`  Exporting to ${format.toUpperCase()}: ${filename}`);

    switch (format) {
      case 'csv':
        await this.exportActionsCSV(actions, filepath);
        break;
      case 'json':
        fs.writeFileSync(filepath, JSON.stringify({ metadata: { count: actions.length, generated_at: new Date().toISOString() }, actions }, null, 2));
        break;
      case 'sql':
        await this.exportActionsSQL(actions, filepath);
        break;
    }

    return filepath;
  }

  private async exportActionsCSV(actions: GeneratedAction[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    const headers = 'action_id,user_id,job_id,action_type,timestamp,session_id,additional_data';
    writeStream.write(headers + '\n');

    actions.forEach(action => {
      const additionalData = action.additional_data ? JSON.stringify(action.additional_data) : '';
      const row = [
        action.action_id,
        action.user_id,
        action.job_id,
        action.action_type,
        action.timestamp,
        action.session_id,
        `"${additionalData.replace(/"/g, '""')}"`
      ].join(',');
      writeStream.write(row + '\n');
    });

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  private async exportActionsSQL(actions: GeneratedAction[], filepath: string): Promise<void> {
    const writeStream = createWriteStream(filepath);

    writeStream.write('-- Generated Actions Test Data\n\n');

    writeStream.write('CREATE TABLE IF NOT EXISTS user_actions (\n');
    writeStream.write('  action_id INTEGER PRIMARY KEY,\n');
    writeStream.write('  user_id INTEGER,\n');
    writeStream.write('  job_id INTEGER,\n');
    writeStream.write('  action_type VARCHAR(20),\n');
    writeStream.write('  timestamp TIMESTAMP,\n');
    writeStream.write('  session_id VARCHAR(50),\n');
    writeStream.write('  additional_data JSONB\n');
    writeStream.write(');\n\n');

    const batchSize = 100;
    for (let i = 0; i < actions.length; i += batchSize) {
      const batch = actions.slice(i, i + batchSize);

      writeStream.write('INSERT INTO user_actions (action_id, user_id, job_id, action_type, timestamp, session_id, additional_data) VALUES\n');

      const values = batch.map(action => {
        const additionalData = action.additional_data ? `'${JSON.stringify(action.additional_data).replace(/'/g, "''")}'::jsonb` : 'NULL';
        return `  (${action.action_id}, ${action.user_id}, ${action.job_id}, '${action.action_type}', '${action.timestamp}', '${action.session_id}', ${additionalData})`;
      });

      writeStream.write(values.join(',\n') + ';\n\n');
    }

    writeStream.end();
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }

  // Utility functions
  private selectWeighted<T extends { weight: number }>(items: T[]): T {
    const totalWeight = items.reduce((sum, item) => sum + item.weight, 0);
    let random = this.random() * totalWeight;

    for (const item of items) {
      random -= item.weight;
      if (random <= 0) {
        return item;
      }
    }

    return items[items.length - 1];
  }

  private selectRandom<T>(items: readonly T[]): T {
    return items[Math.floor(this.random() * items.length)];
  }

  private selectMultiple<T>(items: T[], count: number): T[] {
    const shuffled = [...items].sort(() => this.random() - 0.5);
    return shuffled.slice(0, count);
  }

  private generateCompanyName(size: string, category: string, id: number): string {
    const prefixes = {
      startup: ['New', 'Smart', 'Digital', 'Next', 'Future', 'Modern'],
      small: ['Family', 'Local', 'Community', 'Regional', 'Traditional'],
      medium: ['Professional', 'Quality', 'Reliable', 'Trusted', 'Expert'],
      large: ['Global', 'International', 'Nationwide', 'Premier', 'Leading'],
    };

    const suffixes = {
      'Office Work': ['Systems', 'Solutions', 'Consulting', 'Services', 'Partners'],
      'Sales': ['Trading', 'Commerce', 'Sales', 'Marketing', 'Distribution'],
      'Service Industry': ['Services', 'Hospitality', 'Care', 'Support', 'Assistance'],
      'Manufacturing': ['Manufacturing', 'Industries', 'Production', 'Factory', 'Works'],
      'IT/Tech': ['Tech', 'Systems', 'Software', 'Digital', 'IT'],
      'Healthcare': ['Medical', 'Healthcare', 'Clinic', 'Hospital', 'Care'],
      'Education': ['Education', 'Academy', 'School', 'Learning', 'Institute'],
      'Construction': ['Construction', 'Building', 'Development', 'Engineering', 'Projects'],
      'Transportation': ['Transport', 'Logistics', 'Delivery', 'Shipping', 'Movement'],
    };

    const sizePrefix = this.selectRandom(prefixes[size as keyof typeof prefixes]);
    const categorySuffix = this.selectRandom(suffixes[category as keyof typeof suffixes] || suffixes['Office Work']);

    return `${sizePrefix} ${categorySuffix} ${id % 1000 === 0 ? 'Corporation' : 'Co., Ltd.'}`;
  }

  private generateJobTitle(category: string, id: number): string {
    const titles = {
      'Office Work': ['Administrative Assistant', 'Data Entry Clerk', 'Office Manager', 'Receptionist', 'Customer Service Representative'],
      'Sales': ['Sales Associate', 'Account Manager', 'Sales Representative', 'Business Development', 'Customer Success Manager'],
      'Service Industry': ['Service Staff', 'Customer Support', 'Front Desk', 'Hospitality Staff', 'Service Coordinator'],
      'Manufacturing': ['Production Worker', 'Quality Control', 'Assembly Line Worker', 'Machine Operator', 'Manufacturing Technician'],
      'IT/Tech': ['Software Developer', 'System Administrator', 'IT Support', 'Database Administrator', 'Technical Specialist'],
      'Healthcare': ['Nursing Assistant', 'Medical Clerk', 'Healthcare Support', 'Clinical Assistant', 'Medical Technician'],
      'Education': ['Teaching Assistant', 'Administrative Staff', 'Student Support', 'Academic Coordinator', 'Education Specialist'],
      'Construction': ['Construction Worker', 'Site Supervisor', 'Project Coordinator', 'Safety Inspector', 'Equipment Operator'],
      'Transportation': ['Delivery Driver', 'Logistics Coordinator', 'Warehouse Worker', 'Transportation Clerk', 'Fleet Manager'],
    };

    const categoryTitles = titles[category as keyof typeof titles] || titles['Office Work'];
    const baseTitle = this.selectRandom(categoryTitles);

    const modifiers = ['', 'Senior', 'Junior', 'Assistant', 'Lead'];
    const modifier = this.selectRandom(modifiers);

    return modifier ? `${modifier} ${baseTitle}` : baseTitle;
  }

  private generateStationName(): string {
    const prefixes = ['JR', 'Tokyo Metro', 'Keio', 'Odakyu', 'Tobu', 'Seibu'];
    const locations = ['Shinjuku', 'Shibuya', 'Ikebukuro', 'Ueno', 'Tokyo', 'Shinagawa', 'Yokohama', 'Omiya', 'Kawasaki'];

    const prefix = this.selectRandom(prefixes);
    const location = this.selectRandom(locations);

    return `${prefix} ${location} Station`;
  }

  private generateAddress(prefectureCode: string): string {
    const prefectureNames = {
      '13': 'Tokyo',
      '27': 'Osaka',
      '23': 'Aichi',
      '40': 'Fukuoka',
      '14': 'Kanagawa',
    };

    const prefectureName = prefectureNames[prefectureCode as keyof typeof prefectureNames] || 'Tokyo';
    const district = `District ${Math.floor(this.random() * 20) + 1}`;
    const block = `${Math.floor(this.random() * 10) + 1}-${Math.floor(this.random() * 20) + 1}`;

    return `${block} ${district}, ${prefectureName}`;
  }

  private generateEmailHash(id: number): string {
    // Simple hash for testing purposes
    return `hash_${id}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateSessionId(userId: number, timestamp: Date): string {
    const dateStr = timestamp.toISOString().split('T')[0].replace(/-/g, '');
    const randomStr = Math.random().toString(36).substr(2, 8);
    return `sess_${userId}_${dateStr}_${randomStr}`;
  }

  private generateActionData(actionType: string): Record<string, any> | undefined {
    switch (actionType) {
      case 'view':
        return {
          duration_seconds: Math.floor(this.random() * 300) + 30,
          referrer: this.selectRandom(['search', 'category', 'direct', 'recommendation']),
        };
      case 'click':
        return {
          element: this.selectRandom(['title', 'company', 'salary', 'location', 'description']),
          position: Math.floor(this.random() * 20) + 1,
        };
      case 'apply':
        return {
          application_type: this.selectRandom(['quick_apply', 'full_application', 'external_redirect']),
          completed: this.random() > 0.15, // 85% completion rate
        };
      case 'save':
        return {
          save_type: this.selectRandom(['favorites', 'watchlist', 'comparison']),
        };
      case 'search':
        return {
          query: this.generateSearchQuery(),
          filters_used: Math.floor(this.random() * 5),
          results_count: Math.floor(this.random() * 500) + 10,
        };
      default:
        return undefined;
    }
  }

  private generateSearchQuery(): string {
    const terms = [
      'office work', 'part time', 'full time', 'tokyo', 'osaka', 'remote',
      'no experience', 'student', 'weekend', 'evening', 'morning',
      'high salary', 'english', 'customer service', 'data entry'
    ];

    const termCount = Math.floor(this.random() * 3) + 1;
    return this.selectMultiple(terms, termCount).join(' ');
  }
}

// Test suite and CLI usage
describe('Test Data Generator', () => {
  test('Generate complete test dataset', async () => {
    const generator = new TestDataGenerator({
      jobs: { count: 1000 }, // Smaller for tests
      users: { count: 100 },
      actions: { count: 500 },
    });

    const result = await generator.generateAllTestData();

    expect(result.jobs.count).toBe(1000);
    expect(result.users.count).toBe(100);
    expect(result.actions.count).toBe(500);
    expect(result.duration).toBeGreaterThan(0);

    // Verify files exist
    expect(fs.existsSync(result.jobs.file)).toBe(true);
    expect(fs.existsSync(result.users.file)).toBe(true);
    expect(fs.existsSync(result.actions.file)).toBe(true);
  }, 60000);

  test('Generate jobs with realistic distribution', async () => {
    const generator = new TestDataGenerator({
      jobs: { count: 100 },
      users: { count: 0 },
      actions: { count: 0 },
      output: { formats: ['json'] },
    });

    const result = await generator.generateAllTestData();

    // Read the generated JSON file and verify structure
    const jobsData = JSON.parse(fs.readFileSync(result.jobs.file, 'utf8'));
    expect(jobsData.metadata.count).toBe(100);
    expect(jobsData.jobs).toHaveLength(100);

    const firstJob = jobsData.jobs[0];
    expect(firstJob).toHaveProperty('endcl_cd');
    expect(firstJob).toHaveProperty('company_name');
    expect(firstJob).toHaveProperty('prefecture_code');
    expect(firstJob).toHaveProperty('min_salary');
    expect(firstJob).toHaveProperty('max_salary');
  }, 30000);
});

// CLI Usage
if (require.main === module) {
  const generator = new TestDataGenerator();

  console.log('🚀 Starting test data generation for performance tests...');

  generator.generateAllTestData()
    .then(result => {
      console.log('\n✅ Test data generation completed successfully!');
      console.log(`📁 Files generated in: ${path.join(__dirname, 'test-data')}`);
      console.log(`⏱️  Total time: ${Math.round(result.duration / 1000)}s`);
      process.exit(0);
    })
    .catch(error => {
      console.error('❌ Test data generation failed:', error);
      process.exit(1);
    });
}

export default TestDataGenerator;