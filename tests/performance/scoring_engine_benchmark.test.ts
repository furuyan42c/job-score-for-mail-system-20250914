/**
 * Scoring Engine Benchmark Test
 *
 * Benchmarks the scoring calculations at scale:
 * - Single user vs 100,000 jobs (target: <180ms)
 * - Batch of 1,000 users (target: <180 seconds)
 * - Vectorized operations performance
 * - Cache hit rate verification (>90%)
 * - Memory usage optimization testing
 */

import axios from 'axios';
import { performance } from 'perf_hooks';
import * as os from 'os';
import v8 from 'v8';
import fs from 'fs';
import path from 'path';

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Performance targets
const SCORING_TARGETS = {
  SINGLE_USER_100K_JOBS: 180, // milliseconds
  BATCH_1K_USERS: 180 * 1000, // 180 seconds
  THROUGHPUT_USERS_PER_SECOND: 55,
  CACHE_HIT_RATE: 0.90, // 90%
  MEMORY_EFFICIENCY: 0.70, // 30% reduction from naive implementation
  VECTORIZED_SPEEDUP: 10.0, // 10x faster than individual calculations
};

interface ScoringBenchmarkResult {
  testName: string;
  duration: number;
  itemsProcessed: number;
  itemsPerSecond: number;
  memoryUsage: {
    initial: NodeJS.MemoryUsage;
    peak: NodeJS.MemoryUsage;
    final: NodeJS.MemoryUsage;
  };
  cacheStats?: {
    hits: number;
    misses: number;
    hitRate: number;
  };
  targetMet: boolean;
  additionalMetrics?: Record<string, any>;
}

interface VectorizedPerformanceTest {
  operationName: string;
  vectorizedTime: number;
  individualTime: number;
  speedupRatio: number;
  memoryEfficiency: number;
}

class ScoringEngineBenchmark {
  private testDataPath: string;
  private baselineMemory: NodeJS.MemoryUsage;

  constructor() {
    this.testDataPath = path.join(__dirname, 'test-data');
    this.baselineMemory = process.memoryUsage();
    this.ensureTestDataDirectory();
  }

  private ensureTestDataDirectory(): void {
    if (!fs.existsSync(this.testDataPath)) {
      fs.mkdirSync(this.testDataPath, { recursive: true });
    }
  }

  async runComprehensiveBenchmark(): Promise<ScoringBenchmarkResult[]> {
    console.log('🚀 Starting Comprehensive Scoring Engine Benchmark');

    const results: ScoringBenchmarkResult[] = [];

    // Test 1: Single user vs 100K jobs
    console.log('\n🎯 Test 1: Single User vs 100K Jobs');
    results.push(await this.benchmarkSingleUserLargeJobset());

    // Test 2: Batch of 1K users
    console.log('\n📊 Test 2: Batch of 1K Users');
    results.push(await this.benchmarkBatch1KUsers());

    // Test 3: Vectorized operations performance
    console.log('\n⚡ Test 3: Vectorized Operations Performance');
    results.push(await this.benchmarkVectorizedOperations());

    // Test 4: Cache performance
    console.log('\n💾 Test 4: Cache Performance Analysis');
    results.push(await this.benchmarkCachePerformance());

    // Test 5: Memory optimization
    console.log('\n🧠 Test 5: Memory Optimization');
    results.push(await this.benchmarkMemoryOptimization());

    // Test 6: Concurrent processing
    console.log('\n🔀 Test 6: Concurrent Processing');
    results.push(await this.benchmarkConcurrentProcessing());

    this.generateBenchmarkReport(results);
    return results;
  }

  private async benchmarkSingleUserLargeJobset(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();
    let peakMemory = initialMemory;

    // Create a single user
    const user = {
      user_id: 1,
      email: 'benchmark@example.com',
      email_hash: 'benchmark_hash',
      age_group: '20代前半',
      gender: 'male',
      estimated_pref_cd: '13',
      estimated_city_cd: '13101',
      preferred_categories: [100, 200],
      preferred_salary_min: 1500,
      location_preference_radius: 30,
    };

    console.log('Preparing to score single user against 100K jobs...');

    const startTime = performance.now();

    try {
      // Monitor memory during execution
      const memoryMonitor = setInterval(() => {
        const currentMemory = process.memoryUsage();
        if (currentMemory.rss > peakMemory.rss) {
          peakMemory = currentMemory;
        }
      }, 100);

      // Make API call to score single user against all jobs
      const response = await axios.post(`${API_BASE_URL}/api/scoring/single-user-all-jobs`, {
        user,
        limit: 100000,
        include_cache_stats: true,
      }, {
        timeout: 5000, // 5 second timeout
      });

      clearInterval(memoryMonitor);

      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      if (response.status !== 200) {
        throw new Error(`Scoring API failed with status: ${response.status}`);
      }

      const data = response.data;
      const jobsScored = data.scores?.length || 0;
      const itemsPerSecond = jobsScored / (duration / 1000);

      return {
        testName: 'Single User vs 100K Jobs',
        duration,
        itemsProcessed: jobsScored,
        itemsPerSecond,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: finalMemory,
        },
        cacheStats: data.cache_stats,
        targetMet: duration <= SCORING_TARGETS.SINGLE_USER_100K_JOBS,
        additionalMetrics: {
          avgScoreCalculationTime: duration / jobsScored,
          memoryPerJob: (peakMemory.rss - initialMemory.rss) / jobsScored,
          topScoresCount: data.scores?.filter((s: any) => s.score > 80).length || 0,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Single User vs 100K Jobs',
        duration,
        itemsProcessed: 0,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private async benchmarkBatch1KUsers(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();
    let peakMemory = initialMemory;

    // Generate 1K users
    const users = this.generateBenchmarkUsers(1000);

    console.log('Processing batch of 1000 users...');

    const startTime = performance.now();

    try {
      // Monitor memory during execution
      const memoryMonitor = setInterval(() => {
        const currentMemory = process.memoryUsage();
        if (currentMemory.rss > peakMemory.rss) {
          peakMemory = currentMemory;
        }
      }, 1000);

      // Process in smaller chunks to avoid timeout
      const chunkSize = 100;
      const chunks = [];
      for (let i = 0; i < users.length; i += chunkSize) {
        chunks.push(users.slice(i, i + chunkSize));
      }

      let totalScoresGenerated = 0;
      let combinedCacheStats = { hits: 0, misses: 0, hitRate: 0 };

      for (const [index, chunk] of chunks.entries()) {
        console.log(`Processing chunk ${index + 1}/${chunks.length} (${chunk.length} users)`);

        const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
          users: chunk,
          max_jobs_per_user: 100,
          include_cache_stats: true,
        }, {
          timeout: 30000, // 30 seconds per chunk
        });

        if (response.status !== 200) {
          throw new Error(`Batch scoring failed on chunk ${index + 1} with status: ${response.status}`);
        }

        const chunkData = response.data;
        totalScoresGenerated += chunkData.total_scores || chunk.length * 100;

        if (chunkData.cache_stats) {
          combinedCacheStats.hits += chunkData.cache_stats.hits;
          combinedCacheStats.misses += chunkData.cache_stats.misses;
        }
      }

      clearInterval(memoryMonitor);

      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      combinedCacheStats.hitRate = combinedCacheStats.hits / (combinedCacheStats.hits + combinedCacheStats.misses);
      const usersPerSecond = users.length / (duration / 1000);

      return {
        testName: 'Batch 1K Users',
        duration,
        itemsProcessed: users.length,
        itemsPerSecond: usersPerSecond,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: finalMemory,
        },
        cacheStats: combinedCacheStats,
        targetMet: duration <= SCORING_TARGETS.BATCH_1K_USERS && usersPerSecond >= SCORING_TARGETS.THROUGHPUT_USERS_PER_SECOND,
        additionalMetrics: {
          totalScoresGenerated,
          avgScoresPerUser: totalScoresGenerated / users.length,
          memoryPerUser: (peakMemory.rss - initialMemory.rss) / users.length,
          chunkCount: chunks.length,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Batch 1K Users',
        duration,
        itemsProcessed: users.length,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private async benchmarkVectorizedOperations(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();

    console.log('Comparing vectorized vs individual operations...');

    const startTime = performance.now();

    try {
      // Test vectorized operations performance
      const response = await axios.post(`${API_BASE_URL}/api/scoring/vectorized-benchmark`, {
        num_jobs: 10000,
        num_users: 100,
        operations: ['base_score', 'salary_score', 'location_score', 'category_match'],
      });

      if (response.status !== 200) {
        throw new Error(`Vectorized benchmark failed with status: ${response.status}`);
      }

      const data = response.data;
      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      // Calculate performance metrics
      const vectorizedTests: VectorizedPerformanceTest[] = data.results || [];
      const avgSpeedup = vectorizedTests.reduce((sum, test) => sum + test.speedupRatio, 0) / vectorizedTests.length;
      const avgMemoryEfficiency = vectorizedTests.reduce((sum, test) => sum + test.memoryEfficiency, 0) / vectorizedTests.length;

      return {
        testName: 'Vectorized Operations Performance',
        duration,
        itemsProcessed: data.total_operations || 0,
        itemsPerSecond: (data.total_operations || 0) / (duration / 1000),
        memoryUsage: {
          initial: initialMemory,
          peak: finalMemory, // Approximate since we're not monitoring continuously
          final: finalMemory,
        },
        targetMet: avgSpeedup >= SCORING_TARGETS.VECTORIZED_SPEEDUP && avgMemoryEfficiency >= SCORING_TARGETS.MEMORY_EFFICIENCY,
        additionalMetrics: {
          vectorizedTests,
          avgSpeedup,
          avgMemoryEfficiency,
          operationBreakdown: data.operation_breakdown,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Vectorized Operations Performance',
        duration,
        itemsProcessed: 0,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: initialMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private async benchmarkCachePerformance(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();

    console.log('Analyzing cache performance...');

    const startTime = performance.now();

    try {
      // Clear cache first, then warm it up, then test hit rates
      await axios.post(`${API_BASE_URL}/api/scoring/clear-cache`);

      // Warm-up phase - same operations twice to populate cache
      const warmupUsers = this.generateBenchmarkUsers(50);

      console.log('Warming up cache...');
      await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
        users: warmupUsers,
        max_jobs_per_user: 100,
      });

      // Test phase - repeat similar operations to test cache hits
      console.log('Testing cache hit rates...');
      const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
        users: warmupUsers, // Same users for maximum cache hits
        max_jobs_per_user: 100,
        include_cache_stats: true,
        cache_analysis: true,
      });

      if (response.status !== 200) {
        throw new Error(`Cache performance test failed with status: ${response.status}`);
      }

      const data = response.data;
      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      const cacheStats = data.cache_stats || { hits: 0, misses: 1, hitRate: 0 };
      cacheStats.hitRate = cacheStats.hits / (cacheStats.hits + cacheStats.misses);

      return {
        testName: 'Cache Performance Analysis',
        duration,
        itemsProcessed: warmupUsers.length * 2, // Warmup + test
        itemsPerSecond: (warmupUsers.length * 2) / (duration / 1000),
        memoryUsage: {
          initial: initialMemory,
          peak: finalMemory,
          final: finalMemory,
        },
        cacheStats,
        targetMet: cacheStats.hitRate >= SCORING_TARGETS.CACHE_HIT_RATE,
        additionalMetrics: {
          cacheDetails: data.cache_details,
          cacheTypes: data.cache_types,
          warmupTime: data.warmup_time,
          testTime: data.test_time,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Cache Performance Analysis',
        duration,
        itemsProcessed: 0,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: initialMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private async benchmarkMemoryOptimization(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();

    console.log('Testing memory optimization techniques...');

    const startTime = performance.now();

    try {
      // Test memory usage with and without optimizations
      const response = await axios.post(`${API_BASE_URL}/api/scoring/memory-benchmark`, {
        num_jobs: 50000,
        num_users: 500,
        test_scenarios: ['naive', 'optimized', 'compressed'],
      });

      if (response.status !== 200) {
        throw new Error(`Memory benchmark failed with status: ${response.status}`);
      }

      const data = response.data;
      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      // Calculate memory efficiency
      const scenarios = data.scenarios || {};
      const naiveMemory = scenarios.naive?.peak_memory || 1;
      const optimizedMemory = scenarios.optimized?.peak_memory || naiveMemory;
      const memoryEfficiency = 1 - (optimizedMemory / naiveMemory);

      return {
        testName: 'Memory Optimization',
        duration,
        itemsProcessed: data.total_calculations || 0,
        itemsPerSecond: (data.total_calculations || 0) / (duration / 1000),
        memoryUsage: {
          initial: initialMemory,
          peak: finalMemory,
          final: finalMemory,
        },
        targetMet: memoryEfficiency >= SCORING_TARGETS.MEMORY_EFFICIENCY,
        additionalMetrics: {
          scenarios,
          memoryEfficiency,
          memoryReduction: naiveMemory - optimizedMemory,
          optimizationTechniques: data.techniques_used,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Memory Optimization',
        duration,
        itemsProcessed: 0,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: initialMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private async benchmarkConcurrentProcessing(): Promise<ScoringBenchmarkResult> {
    const initialMemory = process.memoryUsage();
    let peakMemory = initialMemory;

    console.log('Testing concurrent processing performance...');

    const startTime = performance.now();

    try {
      // Test concurrent processing with different thread counts
      const concurrentUsers = this.generateBenchmarkUsers(500);
      const chunkSize = 50;
      const chunks = [];

      for (let i = 0; i < concurrentUsers.length; i += chunkSize) {
        chunks.push(concurrentUsers.slice(i, i + chunkSize));
      }

      // Monitor memory during concurrent execution
      const memoryMonitor = setInterval(() => {
        const currentMemory = process.memoryUsage();
        if (currentMemory.rss > peakMemory.rss) {
          peakMemory = currentMemory;
        }
      }, 500);

      // Execute chunks concurrently
      console.log(`Processing ${chunks.length} chunks concurrently...`);
      const concurrentPromises = chunks.map(async (chunk, index) => {
        const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
          users: chunk,
          max_jobs_per_user: 50,
          chunk_id: index,
        }, {
          timeout: 25000,
        });

        return {
          chunkId: index,
          usersProcessed: chunk.length,
          response: response.data,
        };
      });

      const results = await Promise.all(concurrentPromises);
      clearInterval(memoryMonitor);

      const endTime = performance.now();
      const duration = endTime - startTime;
      const finalMemory = process.memoryUsage();

      const totalUsersProcessed = results.reduce((sum, result) => sum + result.usersProcessed, 0);
      const usersPerSecond = totalUsersProcessed / (duration / 1000);

      return {
        testName: 'Concurrent Processing',
        duration,
        itemsProcessed: totalUsersProcessed,
        itemsPerSecond: usersPerSecond,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: finalMemory,
        },
        targetMet: usersPerSecond >= SCORING_TARGETS.THROUGHPUT_USERS_PER_SECOND * 1.5, // 1.5x target for concurrent
        additionalMetrics: {
          concurrentChunks: chunks.length,
          chunkSize,
          chunkResults: results.map(r => ({
            chunkId: r.chunkId,
            usersProcessed: r.usersProcessed,
          })),
          concurrencySpeedup: usersPerSecond / SCORING_TARGETS.THROUGHPUT_USERS_PER_SECOND,
        },
      };
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;

      return {
        testName: 'Concurrent Processing',
        duration,
        itemsProcessed: 0,
        itemsPerSecond: 0,
        memoryUsage: {
          initial: initialMemory,
          peak: peakMemory,
          final: process.memoryUsage(),
        },
        targetMet: false,
        additionalMetrics: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  private generateBenchmarkUsers(count: number): any[] {
    const users = [];
    const prefectures = ['13', '27', '23', '40', '14', '12', '11'];
    const ageGroups = ['20代前半', '20代後半', '30代前半', '30代後半'];
    const genders = ['male', 'female'];
    const categories = [[100, 200], [200, 300], [300, 400], [400, 500]];

    for (let i = 1; i <= count; i++) {
      const pref = prefectures[i % prefectures.length];
      users.push({
        user_id: i,
        email: `benchmark${i}@example.com`,
        email_hash: `benchmark_hash_${i}`,
        age_group: ageGroups[i % ageGroups.length],
        gender: genders[i % genders.length],
        estimated_pref_cd: pref,
        estimated_city_cd: `${pref}101`,
        preferred_categories: categories[i % categories.length],
        preferred_salary_min: Math.floor(Math.random() * 1000) + 1000,
        location_preference_radius: Math.floor(Math.random() * 40) + 10,
        application_count: Math.floor(Math.random() * 20),
        click_count: Math.floor(Math.random() * 100),
        view_count: Math.floor(Math.random() * 500),
      });
    }

    return users;
  }

  private generateBenchmarkReport(results: ScoringBenchmarkResult[]): void {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: results.length,
        testsPassedTargets: results.filter(r => r.targetMet).length,
        overallSuccessRate: results.filter(r => r.targetMet).length / results.length,
        totalDuration: results.reduce((sum, r) => sum + r.duration, 0),
        totalItemsProcessed: results.reduce((sum, r) => sum + r.itemsProcessed, 0),
      },
      targets: SCORING_TARGETS,
      testResults: results,
      systemInfo: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        cpuCount: os.cpus().length,
        totalMemory: os.totalmem(),
        freeMemory: os.freemem(),
      },
      recommendations: this.generateRecommendations(results),
    };

    const reportPath = path.join(this.testDataPath, `scoring-benchmark-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log('\n📊 Benchmark Results Summary:');
    results.forEach(result => {
      const status = result.targetMet ? '✅' : '❌';
      const duration = Math.round(result.duration);
      const throughput = Math.round(result.itemsPerSecond);
      console.log(`${status} ${result.testName}: ${duration}ms, ${throughput} items/sec`);

      if (result.cacheStats) {
        console.log(`   Cache: ${Math.round(result.cacheStats.hitRate * 100)}% hit rate`);
      }
    });

    console.log(`\n📄 Detailed report saved to: ${reportPath}`);
  }

  private generateRecommendations(results: ScoringBenchmarkResult[]): string[] {
    const recommendations: string[] = [];

    const singleUserTest = results.find(r => r.testName.includes('Single User'));
    if (singleUserTest && !singleUserTest.targetMet) {
      recommendations.push('Optimize single-user scoring algorithm to meet 180ms target for 100K jobs');
    }

    const batchTest = results.find(r => r.testName.includes('Batch 1K'));
    if (batchTest && !batchTest.targetMet) {
      recommendations.push('Improve batch processing throughput to achieve 55+ users/second');
    }

    const cacheTest = results.find(r => r.testName.includes('Cache'));
    if (cacheTest && cacheTest.cacheStats && cacheTest.cacheStats.hitRate < 0.9) {
      recommendations.push('Optimize caching strategy to achieve >90% cache hit rate');
    }

    const memoryTest = results.find(r => r.testName.includes('Memory'));
    if (memoryTest && !memoryTest.targetMet) {
      recommendations.push('Implement memory optimization techniques for better efficiency');
    }

    const vectorizedTest = results.find(r => r.testName.includes('Vectorized'));
    if (vectorizedTest && !vectorizedTest.targetMet) {
      recommendations.push('Enhance vectorized operations for better performance speedup');
    }

    if (recommendations.length === 0) {
      recommendations.push('All performance targets met - consider increasing targets for further optimization');
    }

    return recommendations;
  }
}

// Test suite
describe('Scoring Engine Benchmark Tests', () => {
  let benchmark: ScoringEngineBenchmark;

  beforeAll(() => {
    benchmark = new ScoringEngineBenchmark();
  });

  test('Complete scoring engine benchmark', async () => {
    const results = await benchmark.runComprehensiveBenchmark();

    // Ensure we have results for all tests
    expect(results).toHaveLength(6);

    // Check that critical performance targets are met
    const singleUserTest = results.find(r => r.testName.includes('Single User'));
    expect(singleUserTest?.targetMet).toBe(true);

    const batchTest = results.find(r => r.testName.includes('Batch 1K'));
    expect(batchTest?.targetMet).toBe(true);

    const cacheTest = results.find(r => r.testName.includes('Cache'));
    expect(cacheTest?.cacheStats?.hitRate).toBeGreaterThanOrEqual(SCORING_TARGETS.CACHE_HIT_RATE);

    // Overall success rate should be high
    const passedTests = results.filter(r => r.targetMet).length;
    const successRate = passedTests / results.length;
    expect(successRate).toBeGreaterThanOrEqual(0.8); // At least 80% success rate
  }, 300000); // 5 minute timeout

  test('Single user vs 100K jobs target', async () => {
    const result = await benchmark['benchmarkSingleUserLargeJobset']();

    expect(result.duration).toBeLessThanOrEqual(SCORING_TARGETS.SINGLE_USER_100K_JOBS);
    expect(result.itemsProcessed).toBeGreaterThan(90000); // Should process most jobs
    expect(result.itemsPerSecond).toBeGreaterThan(500); // Reasonable throughput
  }, 10000);

  test('Batch 1K users target', async () => {
    const result = await benchmark['benchmarkBatch1KUsers']();

    expect(result.duration).toBeLessThanOrEqual(SCORING_TARGETS.BATCH_1K_USERS);
    expect(result.itemsProcessed).toBe(1000);
    expect(result.itemsPerSecond).toBeGreaterThanOrEqual(SCORING_TARGETS.THROUGHPUT_USERS_PER_SECOND);
  }, 200000);

  test('Vectorized operations performance', async () => {
    const result = await benchmark['benchmarkVectorizedOperations']();

    expect(result.targetMet).toBe(true);
    expect(result.additionalMetrics?.avgSpeedup).toBeGreaterThanOrEqual(SCORING_TARGETS.VECTORIZED_SPEEDUP);
  }, 30000);

  test('Cache hit rate target', async () => {
    const result = await benchmark['benchmarkCachePerformance']();

    expect(result.cacheStats?.hitRate).toBeGreaterThanOrEqual(SCORING_TARGETS.CACHE_HIT_RATE);
    expect(result.targetMet).toBe(true);
  }, 60000);

  test('Memory optimization efficiency', async () => {
    const result = await benchmark['benchmarkMemoryOptimization']();

    expect(result.targetMet).toBe(true);
    expect(result.additionalMetrics?.memoryEfficiency).toBeGreaterThanOrEqual(SCORING_TARGETS.MEMORY_EFFICIENCY);
  }, 60000);

  test('Concurrent processing performance', async () => {
    const result = await benchmark['benchmarkConcurrentProcessing']();

    expect(result.itemsPerSecond).toBeGreaterThanOrEqual(SCORING_TARGETS.THROUGHPUT_USERS_PER_SECOND);
    expect(result.additionalMetrics?.concurrencySpeedup).toBeGreaterThan(1.0);
  }, 120000);
});

export default ScoringEngineBenchmark;