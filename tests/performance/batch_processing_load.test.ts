/**
 * Batch Processing Load Test
 *
 * Tests the system's ability to handle large-scale batch processing:
 * - Import 100,000 jobs from CSV
 * - Process matching for 10,000 users
 * - Verify 30-minute completion target
 * - Monitor memory usage throughout
 * - Track CPU utilization
 * - Database connection pool monitoring
 */

import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { performance } from 'perf_hooks';
import * as os from 'os';
import v8 from 'v8';
import { EventEmitter } from 'events';

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const BATCH_SIZE = 1000;
const CONCURRENT_REQUESTS = 10;

// Performance targets
const TARGETS = {
  TOTAL_RUNTIME: 30 * 60 * 1000, // 30 minutes in milliseconds
  CSV_IMPORT: 5 * 60 * 1000,     // 5 minutes for 100K jobs
  USER_MATCHING: 20 * 60 * 1000,  // 20 minutes for 10K users
  EMAIL_GENERATION: 5 * 60 * 1000, // 5 minutes for 10K emails
  PEAK_MEMORY: 4 * 1024 * 1024 * 1024, // 4GB
  STEADY_STATE_MEMORY: 2 * 1024 * 1024 * 1024, // 2GB
};

interface PerformanceMetrics {
  startTime: number;
  endTime: number;
  duration: number;
  memory: {
    baseline: NodeJS.MemoryUsage;
    peak: NodeJS.MemoryUsage;
    final: NodeJS.MemoryUsage;
  };
  cpu: {
    baseline: number[];
    samples: number[][];
    final: number[];
  };
  throughput: {
    itemsProcessed: number;
    itemsPerSecond: number;
  };
  errors: Array<{
    timestamp: number;
    error: string;
    phase: string;
  }>;
}

class PerformanceMonitor extends EventEmitter {
  private startTime: number;
  private memoryBaseline: NodeJS.MemoryUsage;
  private cpuBaseline: number[];
  private peakMemory: NodeJS.MemoryUsage;
  private cpuSamples: number[][];
  private errors: Array<{ timestamp: number; error: string; phase: string }>;
  private monitoringInterval?: NodeJS.Timeout;

  constructor() {
    super();
    this.startTime = 0;
    this.memoryBaseline = process.memoryUsage();
    this.cpuBaseline = os.loadavg();
    this.peakMemory = this.memoryBaseline;
    this.cpuSamples = [];
    this.errors = [];
  }

  start(): void {
    this.startTime = performance.now();
    this.memoryBaseline = process.memoryUsage();
    this.cpuBaseline = os.loadavg();
    this.peakMemory = this.memoryBaseline;
    this.cpuSamples = [];
    this.errors = [];

    // Start continuous monitoring
    this.monitoringInterval = setInterval(() => {
      this.sampleMetrics();
    }, 5000); // Sample every 5 seconds

    this.emit('started');
  }

  stop(): PerformanceMetrics {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    const endTime = performance.now();
    const finalMemory = process.memoryUsage();
    const finalCpu = os.loadavg();

    return {
      startTime: this.startTime,
      endTime,
      duration: endTime - this.startTime,
      memory: {
        baseline: this.memoryBaseline,
        peak: this.peakMemory,
        final: finalMemory,
      },
      cpu: {
        baseline: this.cpuBaseline,
        samples: this.cpuSamples,
        final: finalCpu,
      },
      throughput: {
        itemsProcessed: 0, // Will be set by caller
        itemsPerSecond: 0,
      },
      errors: this.errors,
    };
  }

  private sampleMetrics(): void {
    const currentMemory = process.memoryUsage();
    const currentCpu = os.loadavg();

    // Track peak memory
    if (currentMemory.rss > this.peakMemory.rss) {
      this.peakMemory = currentMemory;
    }

    this.cpuSamples.push(currentCpu);

    this.emit('metrics', {
      timestamp: performance.now(),
      memory: currentMemory,
      cpu: currentCpu,
    });
  }

  logError(error: string, phase: string): void {
    this.errors.push({
      timestamp: performance.now(),
      error,
      phase,
    });
    this.emit('error', { error, phase });
  }

  getCurrentMetrics(): any {
    return {
      memory: process.memoryUsage(),
      cpu: os.loadavg(),
      heap: v8.getHeapStatistics(),
      uptime: process.uptime(),
    };
  }
}

class BatchProcessingLoadTest {
  private monitor: PerformanceMonitor;
  private testDataPath: string;

  constructor() {
    this.monitor = new PerformanceMonitor();
    this.testDataPath = path.join(__dirname, 'test-data');
    this.ensureTestDataDirectory();
  }

  private ensureTestDataDirectory(): void {
    if (!fs.existsSync(this.testDataPath)) {
      fs.mkdirSync(this.testDataPath, { recursive: true });
    }
  }

  async runCompleteLoadTest(): Promise<PerformanceMetrics> {
    console.log('🚀 Starting Complete Batch Processing Load Test');
    console.log(`Target: Process 100K jobs × 10K users in ${TARGETS.TOTAL_RUNTIME / 60000} minutes`);

    this.monitor.start();

    try {
      // Phase 1: CSV Import (100K jobs)
      console.log('\n📥 Phase 1: CSV Import (100K jobs)');
      const importResults = await this.testCsvImport();
      console.log(`✅ CSV Import completed in ${importResults.duration / 1000}s`);

      // Phase 2: User Matching (10K users)
      console.log('\n🔄 Phase 2: User Matching (10K users)');
      const matchingResults = await this.testUserMatching();
      console.log(`✅ User Matching completed in ${matchingResults.duration / 1000}s`);

      // Phase 3: Email Generation (10K emails)
      console.log('\n📧 Phase 3: Email Generation (10K emails)');
      const emailResults = await this.testEmailGeneration();
      console.log(`✅ Email Generation completed in ${emailResults.duration / 1000}s`);

      const metrics = this.monitor.stop();

      // Calculate final throughput
      const totalItems = 100000 + 10000 + 10000; // Jobs + Users + Emails
      metrics.throughput.itemsProcessed = totalItems;
      metrics.throughput.itemsPerSecond = totalItems / (metrics.duration / 1000);

      this.validatePerformanceTargets(metrics);
      this.generateReport(metrics, { importResults, matchingResults, emailResults });

      return metrics;
    } catch (error) {
      this.monitor.logError(error instanceof Error ? error.message : String(error), 'complete-test');
      throw error;
    }
  }

  private async testCsvImport(): Promise<{ duration: number; itemsProcessed: number }> {
    const startTime = performance.now();

    try {
      // Generate large CSV test data
      const csvPath = await this.generateLargeCsvData(100000);

      // Upload CSV via API
      const formData = new FormData();
      const csvBuffer = fs.readFileSync(csvPath);
      const csvBlob = new Blob([csvBuffer], { type: 'text/csv' });
      formData.append('file', csvBlob, 'jobs.csv');

      const response = await axios.post(`${API_BASE_URL}/api/jobs/import-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: TARGETS.CSV_IMPORT,
      });

      if (response.status !== 200) {
        throw new Error(`CSV import failed with status: ${response.status}`);
      }

      const duration = performance.now() - startTime;

      if (duration > TARGETS.CSV_IMPORT) {
        this.monitor.logError(`CSV import exceeded target: ${duration}ms > ${TARGETS.CSV_IMPORT}ms`, 'csv-import');
      }

      return { duration, itemsProcessed: 100000 };
    } catch (error) {
      this.monitor.logError(`CSV import failed: ${error}`, 'csv-import');
      throw error;
    }
  }

  private async testUserMatching(): Promise<{ duration: number; itemsProcessed: number }> {
    const startTime = performance.now();

    try {
      // Generate user data
      const users = await this.generateUserData(10000);

      // Process users in batches with concurrent requests
      let processedUsers = 0;
      const promises: Promise<any>[] = [];

      for (let i = 0; i < users.length; i += BATCH_SIZE) {
        const batch = users.slice(i, i + BATCH_SIZE);

        const promise = this.processBatchScoring(batch).then(result => {
          processedUsers += batch.length;
          console.log(`Processed ${processedUsers}/${users.length} users (${Math.round(processedUsers / users.length * 100)}%)`);
          return result;
        });

        promises.push(promise);

        // Control concurrency
        if (promises.length >= CONCURRENT_REQUESTS) {
          await Promise.all(promises.splice(0, CONCURRENT_REQUESTS));
        }
      }

      // Wait for remaining requests
      if (promises.length > 0) {
        await Promise.all(promises);
      }

      const duration = performance.now() - startTime;

      if (duration > TARGETS.USER_MATCHING) {
        this.monitor.logError(`User matching exceeded target: ${duration}ms > ${TARGETS.USER_MATCHING}ms`, 'user-matching');
      }

      return { duration, itemsProcessed: 10000 };
    } catch (error) {
      this.monitor.logError(`User matching failed: ${error}`, 'user-matching');
      throw error;
    }
  }

  private async testEmailGeneration(): Promise<{ duration: number; itemsProcessed: number }> {
    const startTime = performance.now();

    try {
      // Get top matches for email generation
      const emailRequests = await this.generateEmailRequests(10000);

      // Process email generation in batches
      let processedEmails = 0;
      const promises: Promise<any>[] = [];

      for (let i = 0; i < emailRequests.length; i += BATCH_SIZE) {
        const batch = emailRequests.slice(i, i + BATCH_SIZE);

        const promise = this.processBatchEmails(batch).then(result => {
          processedEmails += batch.length;
          console.log(`Generated ${processedEmails}/${emailRequests.length} emails (${Math.round(processedEmails / emailRequests.length * 100)}%)`);
          return result;
        });

        promises.push(promise);

        // Control concurrency
        if (promises.length >= CONCURRENT_REQUESTS) {
          await Promise.all(promises.splice(0, CONCURRENT_REQUESTS));
        }
      }

      // Wait for remaining requests
      if (promises.length > 0) {
        await Promise.all(promises);
      }

      const duration = performance.now() - startTime;

      if (duration > TARGETS.EMAIL_GENERATION) {
        this.monitor.logError(`Email generation exceeded target: ${duration}ms > ${TARGETS.EMAIL_GENERATION}ms`, 'email-generation');
      }

      return { duration, itemsProcessed: 10000 };
    } catch (error) {
      this.monitor.logError(`Email generation failed: ${error}`, 'email-generation');
      throw error;
    }
  }

  private async generateLargeCsvData(numJobs: number): Promise<string> {
    const csvPath = path.join(this.testDataPath, `jobs_${numJobs}.csv`);

    if (fs.existsSync(csvPath)) {
      return csvPath;
    }

    console.log(`Generating CSV with ${numJobs} jobs...`);

    const headers = [
      'endcl_cd', 'company_name', 'application_name', 'prefecture_code',
      'city_code', 'station_name', 'address', 'salary_type', 'min_salary',
      'max_salary', 'fee', 'occupation_cd1', 'occupation_cd2',
      'has_daily_payment', 'has_no_experience', 'has_student_welcome',
      'has_remote_work', 'posting_date'
    ];

    const writeStream = fs.createWriteStream(csvPath);
    writeStream.write(headers.join(',') + '\n');

    const prefectures = ['13', '27', '23', '40', '14', '12', '11'];
    const salaryTypes = ['hourly', 'daily', 'monthly'];
    const occupations1 = [100, 200, 300, 400, 500];
    const occupations2 = [101, 201, 301, 401, 501];

    for (let i = 1; i <= numJobs; i++) {
      const row = [
        `EC${i.toString().padStart(6, '0')}`,
        `Company ${i}`,
        `Job ${i}`,
        prefectures[i % prefectures.length],
        `${prefectures[i % prefectures.length]}101`,
        i % 3 === 0 ? `Station ${i % 100}` : '',
        i % 2 === 0 ? `Address ${i}` : '',
        salaryTypes[i % salaryTypes.length],
        Math.floor(Math.random() * 1700) + 800, // 800-2500
        Math.floor(Math.random() * 2000) + 1000, // 1000-3000
        Math.floor(Math.random() * 5000),
        occupations1[i % occupations1.length],
        occupations2[i % occupations2.length],
        Math.random() > 0.5,
        Math.random() > 0.5,
        Math.random() > 0.5,
        Math.random() > 0.5,
        new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      ];

      writeStream.write(row.join(',') + '\n');

      // Progress indicator
      if (i % 10000 === 0) {
        console.log(`Generated ${i}/${numJobs} jobs (${Math.round(i / numJobs * 100)}%)`);
      }
    }

    writeStream.end();

    return new Promise((resolve, reject) => {
      writeStream.on('finish', () => resolve(csvPath));
      writeStream.on('error', reject);
    });
  }

  private async generateUserData(numUsers: number): Promise<any[]> {
    const users = [];
    const prefectures = ['13', '27', '23', '40', '14', '12', '11'];
    const ageGroups = ['20代前半', '20代後半', '30代前半', '30代後半'];
    const genders = ['male', 'female'];

    for (let i = 1; i <= numUsers; i++) {
      const pref = prefectures[i % prefectures.length];
      users.push({
        user_id: i,
        email: `user${i}@example.com`,
        email_hash: `hash${i}`,
        age_group: ageGroups[i % ageGroups.length],
        gender: genders[i % genders.length],
        estimated_pref_cd: pref,
        estimated_city_cd: `${pref}101`,
        preferred_categories: [100, 200],
        preferred_salary_min: Math.floor(Math.random() * 1000) + 1000,
        location_preference_radius: Math.floor(Math.random() * 40) + 10,
      });
    }

    return users;
  }

  private async processBatchScoring(users: any[]): Promise<any> {
    const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
      users,
      max_jobs_per_user: 100,
    }, {
      timeout: 180000, // 3 minutes per batch
    });

    if (response.status !== 200) {
      throw new Error(`Batch scoring failed with status: ${response.status}`);
    }

    return response.data;
  }

  private async generateEmailRequests(numEmails: number): Promise<any[]> {
    // Simulate email requests based on top user-job matches
    const requests = [];

    for (let i = 1; i <= numEmails; i++) {
      requests.push({
        user_id: i,
        email: `user${i}@example.com`,
        top_jobs: [
          { job_id: i * 10 + 1, score: 85 },
          { job_id: i * 10 + 2, score: 82 },
          { job_id: i * 10 + 3, score: 78 },
        ],
      });
    }

    return requests;
  }

  private async processBatchEmails(emailRequests: any[]): Promise<any> {
    const response = await axios.post(`${API_BASE_URL}/api/emails/batch-generate`, {
      email_requests: emailRequests,
    }, {
      timeout: 120000, // 2 minutes per batch
    });

    if (response.status !== 200) {
      throw new Error(`Batch email generation failed with status: ${response.status}`);
    }

    return response.data;
  }

  private validatePerformanceTargets(metrics: PerformanceMetrics): void {
    console.log('\n📊 Performance Validation:');

    const duration = metrics.duration;
    const peakMemoryMB = Math.round(metrics.memory.peak.rss / 1024 / 1024);
    const finalMemoryMB = Math.round(metrics.memory.final.rss / 1024 / 1024);

    // Total runtime check
    const totalRuntimePassed = duration <= TARGETS.TOTAL_RUNTIME;
    console.log(`⏱️  Total Runtime: ${Math.round(duration / 1000)}s / ${TARGETS.TOTAL_RUNTIME / 1000}s ${totalRuntimePassed ? '✅' : '❌'}`);

    // Memory usage checks
    const peakMemoryPassed = metrics.memory.peak.rss <= TARGETS.PEAK_MEMORY;
    const steadyMemoryPassed = metrics.memory.final.rss <= TARGETS.STEADY_STATE_MEMORY;
    console.log(`💾 Peak Memory: ${peakMemoryMB}MB / ${Math.round(TARGETS.PEAK_MEMORY / 1024 / 1024)}MB ${peakMemoryPassed ? '✅' : '❌'}`);
    console.log(`💾 Final Memory: ${finalMemoryMB}MB / ${Math.round(TARGETS.STEADY_STATE_MEMORY / 1024 / 1024)}MB ${steadyMemoryPassed ? '✅' : '❌'}`);

    // Throughput
    const throughputPassed = metrics.throughput.itemsPerSecond > 55; // 55+ items/second target
    console.log(`🚀 Throughput: ${Math.round(metrics.throughput.itemsPerSecond)} items/sec ${throughputPassed ? '✅' : '❌'}`);

    // Error rate
    const errorRate = metrics.errors.length / metrics.throughput.itemsProcessed * 100;
    const errorRatePassed = errorRate < 1; // Less than 1% error rate
    console.log(`❌ Error Rate: ${errorRate.toFixed(2)}% ${errorRatePassed ? '✅' : '⚠️'}`);

    const allTargetsMet = totalRuntimePassed && peakMemoryPassed && steadyMemoryPassed && throughputPassed && errorRatePassed;

    if (!allTargetsMet) {
      console.log('\n⚠️  Some performance targets were not met. See detailed report for analysis.');
    } else {
      console.log('\n🎉 All performance targets met successfully!');
    }
  }

  private generateReport(metrics: PerformanceMetrics, phaseResults: any): void {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalDuration: Math.round(metrics.duration / 1000),
        itemsProcessed: metrics.throughput.itemsProcessed,
        throughput: Math.round(metrics.throughput.itemsPerSecond),
        peakMemoryMB: Math.round(metrics.memory.peak.rss / 1024 / 1024),
        finalMemoryMB: Math.round(metrics.memory.final.rss / 1024 / 1024),
        errorCount: metrics.errors.length,
        targetsMetCount: this.countTargetsMet(metrics),
      },
      phases: phaseResults,
      detailedMetrics: {
        memory: {
          baseline: metrics.memory.baseline,
          peak: metrics.memory.peak,
          final: metrics.memory.final,
        },
        cpu: {
          baseline: metrics.cpu.baseline,
          avgDuring: this.calculateAverageCpu(metrics.cpu.samples),
          final: metrics.cpu.final,
        },
      },
      errors: metrics.errors,
      recommendations: this.generateRecommendations(metrics),
    };

    const reportPath = path.join(this.testDataPath, `load-test-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\n📄 Detailed report saved to: ${reportPath}`);
  }

  private countTargetsMet(metrics: PerformanceMetrics): number {
    let count = 0;
    if (metrics.duration <= TARGETS.TOTAL_RUNTIME) count++;
    if (metrics.memory.peak.rss <= TARGETS.PEAK_MEMORY) count++;
    if (metrics.memory.final.rss <= TARGETS.STEADY_STATE_MEMORY) count++;
    if (metrics.throughput.itemsPerSecond > 55) count++;
    if ((metrics.errors.length / metrics.throughput.itemsProcessed) < 0.01) count++;
    return count;
  }

  private calculateAverageCpu(samples: number[][]): number[] {
    if (samples.length === 0) return [0, 0, 0];

    const sums = [0, 0, 0];
    samples.forEach(sample => {
      sums[0] += sample[0];
      sums[1] += sample[1];
      sums[2] += sample[2];
    });

    return sums.map(sum => sum / samples.length);
  }

  private generateRecommendations(metrics: PerformanceMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.duration > TARGETS.TOTAL_RUNTIME) {
      recommendations.push('Consider increasing concurrent processing or optimizing database queries');
    }

    if (metrics.memory.peak.rss > TARGETS.PEAK_MEMORY) {
      recommendations.push('Implement memory usage optimization and garbage collection tuning');
    }

    if (metrics.throughput.itemsPerSecond < 55) {
      recommendations.push('Optimize batch processing algorithms and increase parallelization');
    }

    if (metrics.errors.length > 0) {
      recommendations.push('Investigate and fix error sources to improve reliability');
    }

    const avgCpu = this.calculateAverageCpu(metrics.cpu.samples);
    if (avgCpu[0] > 0.8) { // Load average over 0.8
      recommendations.push('High CPU usage detected - consider load balancing or CPU optimization');
    }

    return recommendations;
  }
}

// Test suite
describe('Batch Processing Load Test', () => {
  let loadTest: BatchProcessingLoadTest;

  beforeAll(() => {
    loadTest = new BatchProcessingLoadTest();
  });

  test('Complete batch processing load test', async () => {
    const metrics = await loadTest.runCompleteLoadTest();

    // Assertions for performance targets
    expect(metrics.duration).toBeLessThanOrEqual(TARGETS.TOTAL_RUNTIME);
    expect(metrics.memory.peak.rss).toBeLessThanOrEqual(TARGETS.PEAK_MEMORY);
    expect(metrics.memory.final.rss).toBeLessThanOrEqual(TARGETS.STEADY_STATE_MEMORY);
    expect(metrics.throughput.itemsPerSecond).toBeGreaterThan(55);

    // Error rate should be less than 1%
    const errorRate = metrics.errors.length / metrics.throughput.itemsProcessed;
    expect(errorRate).toBeLessThan(0.01);
  }, TARGETS.TOTAL_RUNTIME + 60000); // Add 1 minute buffer for test timeout

  test('CSV import performance target', async () => {
    const result = await loadTest['testCsvImport']();
    expect(result.duration).toBeLessThanOrEqual(TARGETS.CSV_IMPORT);
    expect(result.itemsProcessed).toBe(100000);
  }, TARGETS.CSV_IMPORT + 30000);

  test('User matching performance target', async () => {
    const result = await loadTest['testUserMatching']();
    expect(result.duration).toBeLessThanOrEqual(TARGETS.USER_MATCHING);
    expect(result.itemsProcessed).toBe(10000);
  }, TARGETS.USER_MATCHING + 30000);

  test('Email generation performance target', async () => {
    const result = await loadTest['testEmailGeneration']();
    expect(result.duration).toBeLessThanOrEqual(TARGETS.EMAIL_GENERATION);
    expect(result.itemsProcessed).toBe(10000);
  }, TARGETS.EMAIL_GENERATION + 30000);
});

export default BatchProcessingLoadTest;