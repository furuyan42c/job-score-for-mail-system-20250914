/**
 * Memory Usage Analysis Test
 *
 * Monitors memory consumption during various operations:
 * - Baseline memory usage
 * - Memory during 100K job import
 * - Memory during 10K user processing
 * - Memory leak detection
 * - Garbage collection impact
 * - Peak memory usage tracking
 */

import axios from 'axios';
import { performance } from 'perf_hooks';
import * as os from 'os';
import v8 from 'v8';
import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Memory targets and thresholds
const MEMORY_TARGETS = {
  BASELINE_MEMORY_MB: 100, // Under 100MB at rest
  PEAK_MEMORY_MB: 4 * 1024, // Under 4GB peak
  STEADY_STATE_MB: 2 * 1024, // Under 2GB steady state
  MEMORY_LEAK_THRESHOLD: 1.1, // 10% growth tolerance
  GC_EFFECTIVENESS: 0.7, // 70% memory recovery after GC
  HEAP_GROWTH_RATE: 1.05, // 5% heap growth per operation max
};

interface MemorySnapshot {
  timestamp: number;
  rss: number; // Resident Set Size
  heapTotal: number;
  heapUsed: number;
  external: number;
  arrayBuffers: number;
  heapStats?: v8.HeapSpaceStatistics[];
  phase: string;
  operationCount?: number;
}

interface MemoryAnalysisResult {
  testName: string;
  duration: number;
  snapshots: MemorySnapshot[];
  baseline: MemorySnapshot;
  peak: MemorySnapshot;
  final: MemorySnapshot;
  memoryLeakDetected: boolean;
  gcEffectiveness: number;
  metrics: {
    memoryGrowthRate: number;
    peakMemoryMB: number;
    finalMemoryMB: number;
    avgMemoryMB: number;
    memoryEfficiency: number;
  };
  targetsMet: {
    peakMemory: boolean;
    steadyState: boolean;
    noMemoryLeak: boolean;
    gcEffectiveness: boolean;
  };
  recommendations: string[];
}

class MemoryMonitor extends EventEmitter {
  private snapshots: MemorySnapshot[] = [];
  private monitoringInterval?: NodeJS.Timeout;
  private isMonitoring = false;

  start(intervalMs: number = 1000): void {
    if (this.isMonitoring) return;

    this.snapshots = [];
    this.isMonitoring = true;

    // Take baseline snapshot
    this.takeSnapshot('baseline');

    this.monitoringInterval = setInterval(() => {
      this.takeSnapshot('monitoring');
    }, intervalMs);

    this.emit('started');
  }

  stop(): MemorySnapshot[] {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    this.isMonitoring = false;
    this.takeSnapshot('final');

    this.emit('stopped', this.snapshots);
    return [...this.snapshots];
  }

  takeSnapshot(phase: string, operationCount?: number): MemorySnapshot {
    const memoryUsage = process.memoryUsage();
    const heapStats = v8.getHeapSpaceStatistics();

    const snapshot: MemorySnapshot = {
      timestamp: performance.now(),
      rss: memoryUsage.rss,
      heapTotal: memoryUsage.heapTotal,
      heapUsed: memoryUsage.heapUsed,
      external: memoryUsage.external,
      arrayBuffers: memoryUsage.arrayBuffers,
      heapStats,
      phase,
      operationCount,
    };

    this.snapshots.push(snapshot);
    this.emit('snapshot', snapshot);

    return snapshot;
  }

  forceGC(): MemorySnapshot | null {
    if (global.gc) {
      const beforeGC = this.takeSnapshot('before-gc');
      global.gc();
      const afterGC = this.takeSnapshot('after-gc');

      this.emit('gc', { before: beforeGC, after: afterGC });
      return afterGC;
    } else {
      console.warn('Garbage collection not available. Run with --expose-gc flag.');
      return null;
    }
  }

  getMemoryTrend(): 'increasing' | 'decreasing' | 'stable' {
    if (this.snapshots.length < 3) return 'stable';

    const recent = this.snapshots.slice(-3);
    const trend = recent[2].heapUsed - recent[0].heapUsed;

    if (trend > recent[0].heapUsed * 0.05) return 'increasing';
    if (trend < -recent[0].heapUsed * 0.05) return 'decreasing';
    return 'stable';
  }

  getCurrentMemoryMB(): number {
    return Math.round(process.memoryUsage().rss / 1024 / 1024);
  }
}

class MemoryUsageAnalyzer {
  private monitor: MemoryMonitor;
  private testDataPath: string;

  constructor() {
    this.monitor = new MemoryMonitor();
    this.testDataPath = path.join(__dirname, 'test-data');
    this.ensureTestDataDirectory();
  }

  private ensureTestDataDirectory(): void {
    if (!fs.existsSync(this.testDataPath)) {
      fs.mkdirSync(this.testDataPath, { recursive: true });
    }
  }

  async runCompleteMemoryAnalysis(): Promise<MemoryAnalysisResult[]> {
    console.log('🧠 Starting Complete Memory Usage Analysis');
    console.log(`System Memory: ${Math.round(os.totalmem() / 1024 / 1024 / 1024)}GB total, ${Math.round(os.freemem() / 1024 / 1024 / 1024)}GB free`);

    const results: MemoryAnalysisResult[] = [];

    // Test 1: Baseline memory measurement
    console.log('\n📏 Test 1: Baseline Memory Measurement');
    results.push(await this.analyzeBaselineMemory());

    // Test 2: Memory during job import
    console.log('\n📥 Test 2: Memory During 100K Job Import');
    results.push(await this.analyzeJobImportMemory());

    // Test 3: Memory during user processing
    console.log('\n👥 Test 3: Memory During 10K User Processing');
    results.push(await this.analyzeUserProcessingMemory());

    // Test 4: Memory leak detection
    console.log('\n🔍 Test 4: Memory Leak Detection');
    results.push(await this.analyzeMemoryLeaks());

    // Test 5: Garbage collection analysis
    console.log('\n🗑️  Test 5: Garbage Collection Analysis');
    results.push(await this.analyzeGarbageCollection());

    // Test 6: Sustained load memory tracking
    console.log('\n⏱️  Test 6: Sustained Load Memory Tracking');
    results.push(await this.analyzeSustainedLoad());

    this.generateMemoryReport(results);
    return results;
  }

  private async analyzeBaselineMemory(): Promise<MemoryAnalysisResult> {
    console.log('Measuring baseline memory usage...');

    const startTime = performance.now();
    this.monitor.start(500); // Sample every 500ms

    // Just idle for a few seconds to establish baseline
    await new Promise(resolve => setTimeout(resolve, 5000));

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('Baseline Memory', snapshots, duration);
  }

  private async analyzeJobImportMemory(): Promise<MemoryAnalysisResult> {
    console.log('Analyzing memory during job import...');

    const startTime = performance.now();
    this.monitor.start(1000); // Sample every second

    try {
      // Generate test CSV data
      const csvData = this.generateJobsCsvData(100000);
      this.monitor.takeSnapshot('csv-generated', 100000);

      // Simulate CSV upload
      const formData = new FormData();
      const csvBlob = new Blob([csvData], { type: 'text/csv' });
      formData.append('file', csvBlob, 'memory-test-jobs.csv');

      this.monitor.takeSnapshot('before-upload');

      const response = await axios.post(`${API_BASE_URL}/api/jobs/import-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes
      });

      this.monitor.takeSnapshot('after-upload');

      if (response.status !== 200) {
        throw new Error(`Job import failed with status: ${response.status}`);
      }

      // Wait a bit for memory to stabilize
      await new Promise(resolve => setTimeout(resolve, 10000));
      this.monitor.takeSnapshot('stabilized');

    } catch (error) {
      console.error('Job import error:', error);
      this.monitor.takeSnapshot('error');
    }

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('Job Import Memory', snapshots, duration);
  }

  private async analyzeUserProcessingMemory(): Promise<MemoryAnalysisResult> {
    console.log('Analyzing memory during user processing...');

    const startTime = performance.now();
    this.monitor.start(2000); // Sample every 2 seconds

    try {
      // Generate user data
      const users = this.generateUsers(10000);
      this.monitor.takeSnapshot('users-generated', 10000);

      // Process users in batches
      const batchSize = 500;
      let processedCount = 0;

      for (let i = 0; i < users.length; i += batchSize) {
        const batch = users.slice(i, i + batchSize);

        this.monitor.takeSnapshot(`batch-${Math.floor(i/batchSize) + 1}-start`, processedCount);

        const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
          users: batch,
          max_jobs_per_user: 50,
        }, {
          timeout: 60000,
        });

        processedCount += batch.length;
        this.monitor.takeSnapshot(`batch-${Math.floor(i/batchSize) + 1}-end`, processedCount);

        console.log(`Processed ${processedCount}/${users.length} users (${Math.round(processedCount/users.length*100)}%) - Memory: ${this.monitor.getCurrentMemoryMB()}MB`);

        if (response.status !== 200) {
          console.warn(`Batch processing warning: status ${response.status}`);
        }

        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Wait for memory to stabilize
      await new Promise(resolve => setTimeout(resolve, 15000));
      this.monitor.takeSnapshot('processing-complete', processedCount);

    } catch (error) {
      console.error('User processing error:', error);
      this.monitor.takeSnapshot('error');
    }

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('User Processing Memory', snapshots, duration);
  }

  private async analyzeMemoryLeaks(): Promise<MemoryAnalysisResult> {
    console.log('Detecting memory leaks through repeated operations...');

    const startTime = performance.now();
    this.monitor.start(3000); // Sample every 3 seconds

    try {
      const testUsers = this.generateUsers(100);

      // Perform same operation multiple times
      for (let iteration = 1; iteration <= 10; iteration++) {
        console.log(`Memory leak test iteration ${iteration}/10 - Memory: ${this.monitor.getCurrentMemoryMB()}MB`);

        this.monitor.takeSnapshot(`iteration-${iteration}-start`, iteration);

        // Perform identical operations
        const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
          users: testUsers,
          max_jobs_per_user: 100,
        }, {
          timeout: 30000,
        });

        this.monitor.takeSnapshot(`iteration-${iteration}-end`, iteration);

        if (response.status !== 200) {
          console.warn(`Iteration ${iteration} warning: status ${response.status}`);
        }

        // Force garbage collection if available
        if (iteration % 3 === 0) {
          this.monitor.forceGC();
        }

        // Delay between iterations
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      // Final stabilization
      await new Promise(resolve => setTimeout(resolve, 10000));
      this.monitor.takeSnapshot('leak-test-complete');

    } catch (error) {
      console.error('Memory leak test error:', error);
      this.monitor.takeSnapshot('error');
    }

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('Memory Leak Detection', snapshots, duration);
  }

  private async analyzeGarbageCollection(): Promise<MemoryAnalysisResult> {
    console.log('Analyzing garbage collection effectiveness...');

    const startTime = performance.now();
    this.monitor.start(1000);

    try {
      // Allocate memory intentionally
      const largeArrays: any[] = [];

      for (let i = 0; i < 5; i++) {
        console.log(`GC test phase ${i + 1}/5 - allocating memory`);

        this.monitor.takeSnapshot(`gc-phase-${i + 1}-start`, i);

        // Allocate large amount of memory
        for (let j = 0; j < 10; j++) {
          largeArrays.push(new Array(100000).fill(Math.random()));
        }

        this.monitor.takeSnapshot(`gc-phase-${i + 1}-allocated`, i);

        // Clear some references
        if (i > 0) {
          largeArrays.splice(0, 5);
        }

        // Force GC
        const afterGC = this.monitor.forceGC();
        if (afterGC) {
          console.log(`After GC ${i + 1}: ${Math.round(afterGC.heapUsed / 1024 / 1024)}MB heap used`);
        }

        await new Promise(resolve => setTimeout(resolve, 3000));
      }

      // Clear all references
      largeArrays.length = 0;

      // Final GC
      this.monitor.forceGC();
      await new Promise(resolve => setTimeout(resolve, 5000));

      this.monitor.takeSnapshot('gc-analysis-complete');

    } catch (error) {
      console.error('GC analysis error:', error);
      this.monitor.takeSnapshot('error');
    }

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('Garbage Collection Analysis', snapshots, duration);
  }

  private async analyzeSustainedLoad(): Promise<MemoryAnalysisResult> {
    console.log('Analyzing memory under sustained load...');

    const startTime = performance.now();
    this.monitor.start(5000); // Sample every 5 seconds

    try {
      const testUsers = this.generateUsers(200);
      const duration = 10 * 60 * 1000; // 10 minutes
      const endTime = Date.now() + duration;
      let operationCount = 0;

      console.log('Running sustained load for 10 minutes...');

      while (Date.now() < endTime) {
        operationCount++;

        this.monitor.takeSnapshot(`sustained-op-${operationCount}`, operationCount);

        // Continuous processing
        try {
          const response = await axios.post(`${API_BASE_URL}/api/scoring/batch`, {
            users: testUsers.slice(0, 50), // Small batches for sustained load
            max_jobs_per_user: 20,
          }, {
            timeout: 20000,
          });

          if (response.status !== 200) {
            console.warn(`Sustained operation ${operationCount} warning: status ${response.status}`);
          }
        } catch (error) {
          console.warn(`Sustained operation ${operationCount} error:`, error);
        }

        // Periodic GC
        if (operationCount % 10 === 0) {
          this.monitor.forceGC();
          console.log(`Sustained load: ${operationCount} operations completed - Memory: ${this.monitor.getCurrentMemoryMB()}MB - Trend: ${this.monitor.getMemoryTrend()}`);
        }

        // Brief pause between operations
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      this.monitor.takeSnapshot('sustained-load-complete', operationCount);

    } catch (error) {
      console.error('Sustained load error:', error);
      this.monitor.takeSnapshot('error');
    }

    const snapshots = this.monitor.stop();
    const duration = performance.now() - startTime;

    return this.analyzeSnapshots('Sustained Load Memory', snapshots, duration);
  }

  private generateJobsCsvData(count: number): string {
    const headers = [
      'endcl_cd', 'company_name', 'application_name', 'prefecture_code',
      'city_code', 'min_salary', 'max_salary', 'fee', 'occupation_cd1'
    ];

    let csv = headers.join(',') + '\n';

    for (let i = 1; i <= count; i++) {
      const row = [
        `MEM${i.toString().padStart(6, '0')}`,
        `MemTest Company ${i}`,
        `Memory Test Job ${i}`,
        '13',
        '13101',
        '1000',
        '2000',
        '100',
        '100'
      ];
      csv += row.join(',') + '\n';
    }

    return csv;
  }

  private generateUsers(count: number): any[] {
    const users = [];

    for (let i = 1; i <= count; i++) {
      users.push({
        user_id: i,
        email: `memtest${i}@example.com`,
        email_hash: `memtest_hash_${i}`,
        age_group: '20代前半',
        gender: 'male',
        estimated_pref_cd: '13',
        estimated_city_cd: '13101',
        preferred_categories: [100],
        preferred_salary_min: 1500,
        location_preference_radius: 20,
      });
    }

    return users;
  }

  private analyzeSnapshots(testName: string, snapshots: MemorySnapshot[], duration: number): MemoryAnalysisResult {
    if (snapshots.length < 2) {
      return this.createErrorResult(testName, 'Insufficient snapshots for analysis');
    }

    const baseline = snapshots[0];
    const final = snapshots[snapshots.length - 1];
    const peak = snapshots.reduce((max, snapshot) =>
      snapshot.rss > max.rss ? snapshot : max, baseline
    );

    // Calculate metrics
    const memoryGrowthRate = (final.heapUsed - baseline.heapUsed) / baseline.heapUsed;
    const peakMemoryMB = Math.round(peak.rss / 1024 / 1024);
    const finalMemoryMB = Math.round(final.rss / 1024 / 1024);
    const avgMemoryMB = Math.round(
      snapshots.reduce((sum, s) => sum + s.rss, 0) / snapshots.length / 1024 / 1024
    );

    // Memory efficiency (how well memory is managed relative to peak)
    const memoryEfficiency = 1 - (final.rss / peak.rss);

    // Detect memory leaks
    const memoryLeakDetected = this.detectMemoryLeak(snapshots);

    // Calculate GC effectiveness
    const gcEffectiveness = this.calculateGCEffectiveness(snapshots);

    // Check targets
    const targetsMet = {
      peakMemory: peakMemoryMB <= MEMORY_TARGETS.PEAK_MEMORY_MB,
      steadyState: finalMemoryMB <= MEMORY_TARGETS.STEADY_STATE_MB,
      noMemoryLeak: !memoryLeakDetected,
      gcEffectiveness: gcEffectiveness >= MEMORY_TARGETS.GC_EFFECTIVENESS,
    };

    // Generate recommendations
    const recommendations = this.generateMemoryRecommendations({
      memoryGrowthRate,
      peakMemoryMB,
      finalMemoryMB,
      memoryLeakDetected,
      gcEffectiveness,
      targetsMet,
    });

    return {
      testName,
      duration,
      snapshots,
      baseline,
      peak,
      final,
      memoryLeakDetected,
      gcEffectiveness,
      metrics: {
        memoryGrowthRate,
        peakMemoryMB,
        finalMemoryMB,
        avgMemoryMB,
        memoryEfficiency,
      },
      targetsMet,
      recommendations,
    };
  }

  private detectMemoryLeak(snapshots: MemorySnapshot[]): boolean {
    if (snapshots.length < 5) return false;

    // Look for consistent upward trend in heap usage
    const recentSnapshots = snapshots.slice(-5);
    let increasingCount = 0;

    for (let i = 1; i < recentSnapshots.length; i++) {
      if (recentSnapshots[i].heapUsed > recentSnapshots[i-1].heapUsed * 1.02) { // 2% increase
        increasingCount++;
      }
    }

    // If memory increased in most recent samples, consider it a potential leak
    const leakSuspicion = increasingCount >= 3;

    // Also check overall growth
    const firstSnapshot = snapshots[0];
    const lastSnapshot = snapshots[snapshots.length - 1];
    const overallGrowth = (lastSnapshot.heapUsed - firstSnapshot.heapUsed) / firstSnapshot.heapUsed;

    return leakSuspicion && overallGrowth > MEMORY_TARGETS.MEMORY_LEAK_THRESHOLD - 1;
  }

  private calculateGCEffectiveness(snapshots: MemorySnapshot[]): number {
    // Find GC events (before-gc and after-gc pairs)
    const gcPairs: { before: MemorySnapshot; after: MemorySnapshot }[] = [];

    for (let i = 0; i < snapshots.length - 1; i++) {
      if (snapshots[i].phase === 'before-gc' && snapshots[i + 1].phase === 'after-gc') {
        gcPairs.push({ before: snapshots[i], after: snapshots[i + 1] });
      }
    }

    if (gcPairs.length === 0) {
      return 0.5; // Default neutral effectiveness if no GC events detected
    }

    // Calculate average memory recovery
    const totalRecovery = gcPairs.reduce((sum, pair) => {
      const recovery = (pair.before.heapUsed - pair.after.heapUsed) / pair.before.heapUsed;
      return sum + Math.max(0, recovery); // Only count positive recovery
    }, 0);

    return totalRecovery / gcPairs.length;
  }

  private generateMemoryRecommendations(analysis: any): string[] {
    const recommendations: string[] = [];

    if (!analysis.targetsMet.peakMemory) {
      recommendations.push(`Peak memory usage (${analysis.peakMemoryMB}MB) exceeds target (${MEMORY_TARGETS.PEAK_MEMORY_MB}MB). Consider optimizing data structures or implementing streaming.`);
    }

    if (!analysis.targetsMet.steadyState) {
      recommendations.push(`Final memory usage (${analysis.finalMemoryMB}MB) exceeds steady state target (${MEMORY_TARGETS.STEADY_STATE_MB}MB). Review object lifecycle management.`);
    }

    if (analysis.memoryLeakDetected) {
      recommendations.push('Potential memory leak detected. Review object references and ensure proper cleanup in event handlers and callbacks.');
    }

    if (analysis.gcEffectiveness < MEMORY_TARGETS.GC_EFFECTIVENESS) {
      recommendations.push(`Garbage collection effectiveness (${Math.round(analysis.gcEffectiveness * 100)}%) is below target (${Math.round(MEMORY_TARGETS.GC_EFFECTIVENESS * 100)}%). Consider memory allocation patterns.`);
    }

    if (analysis.memoryGrowthRate > MEMORY_TARGETS.HEAP_GROWTH_RATE - 1) {
      recommendations.push(`Memory growth rate (${Math.round(analysis.memoryGrowthRate * 100)}%) is high. Optimize memory allocation and consider object pooling.`);
    }

    if (recommendations.length === 0) {
      recommendations.push('Memory usage patterns look healthy. Consider monitoring in production for sustained performance.');
    }

    return recommendations;
  }

  private createErrorResult(testName: string, error: string): MemoryAnalysisResult {
    const currentMemory = this.monitor.takeSnapshot('error');

    return {
      testName,
      duration: 0,
      snapshots: [currentMemory],
      baseline: currentMemory,
      peak: currentMemory,
      final: currentMemory,
      memoryLeakDetected: false,
      gcEffectiveness: 0,
      metrics: {
        memoryGrowthRate: 0,
        peakMemoryMB: 0,
        finalMemoryMB: 0,
        avgMemoryMB: 0,
        memoryEfficiency: 0,
      },
      targetsMet: {
        peakMemory: false,
        steadyState: false,
        noMemoryLeak: false,
        gcEffectiveness: false,
      },
      recommendations: [`Test failed: ${error}`],
    };
  }

  private generateMemoryReport(results: MemoryAnalysisResult[]): void {
    const report = {
      timestamp: new Date().toISOString(),
      systemInfo: {
        totalMemory: Math.round(os.totalmem() / 1024 / 1024),
        freeMemory: Math.round(os.freemem() / 1024 / 1024),
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
      },
      summary: {
        totalTests: results.length,
        testsPassedAllTargets: results.filter(r => Object.values(r.targetsMet).every(Boolean)).length,
        avgPeakMemoryMB: Math.round(results.reduce((sum, r) => sum + r.metrics.peakMemoryMB, 0) / results.length),
        memoryLeaksDetected: results.filter(r => r.memoryLeakDetected).length,
        avgGCEffectiveness: results.reduce((sum, r) => sum + r.gcEffectiveness, 0) / results.length,
      },
      targets: MEMORY_TARGETS,
      testResults: results,
      overallRecommendations: this.generateOverallRecommendations(results),
    };

    const reportPath = path.join(this.testDataPath, `memory-analysis-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log('\n🧠 Memory Analysis Results Summary:');
    results.forEach(result => {
      const allTargetsMet = Object.values(result.targetsMet).every(Boolean);
      const status = allTargetsMet ? '✅' : '⚠️';
      const peakMB = result.metrics.peakMemoryMB;
      const finalMB = result.metrics.finalMemoryMB;
      const leakStatus = result.memoryLeakDetected ? '🔴 LEAK' : '✅ OK';
      console.log(`${status} ${result.testName}: Peak: ${peakMB}MB, Final: ${finalMB}MB, Leaks: ${leakStatus}`);
    });

    console.log(`\n📄 Detailed memory report saved to: ${reportPath}`);
  }

  private generateOverallRecommendations(results: MemoryAnalysisResult[]): string[] {
    const recommendations: string[] = [];

    const leakTests = results.filter(r => r.memoryLeakDetected);
    if (leakTests.length > 0) {
      recommendations.push('Memory leaks detected in multiple tests. Prioritize fixing object lifecycle management.');
    }

    const highPeakMemory = results.filter(r => r.metrics.peakMemoryMB > MEMORY_TARGETS.PEAK_MEMORY_MB);
    if (highPeakMemory.length > 0) {
      recommendations.push('Peak memory usage exceeds targets. Consider implementing data streaming and chunked processing.');
    }

    const poorGC = results.filter(r => r.gcEffectiveness < MEMORY_TARGETS.GC_EFFECTIVENESS);
    if (poorGC.length > 0) {
      recommendations.push('Garbage collection effectiveness is poor. Review memory allocation patterns and object references.');
    }

    const avgPeakMemory = results.reduce((sum, r) => sum + r.metrics.peakMemoryMB, 0) / results.length;
    if (avgPeakMemory > MEMORY_TARGETS.PEAK_MEMORY_MB * 0.8) {
      recommendations.push('Average peak memory usage is high. Consider memory optimization as a priority.');
    }

    if (recommendations.length === 0) {
      recommendations.push('Overall memory usage patterns are within acceptable ranges. Continue monitoring in production.');
    }

    return recommendations;
  }
}

// Test suite
describe('Memory Usage Analysis Tests', () => {
  let analyzer: MemoryUsageAnalyzer;

  beforeAll(() => {
    analyzer = new MemoryUsageAnalyzer();
  });

  test('Complete memory usage analysis', async () => {
    const results = await analyzer.runCompleteMemoryAnalysis();

    // Ensure we have results for all tests
    expect(results).toHaveLength(6);

    // Check critical memory targets
    const sustainedLoadTest = results.find(r => r.testName.includes('Sustained Load'));
    expect(sustainedLoadTest?.memoryLeakDetected).toBe(false);

    const jobImportTest = results.find(r => r.testName.includes('Job Import'));
    expect(jobImportTest?.metrics.peakMemoryMB).toBeLessThanOrEqual(MEMORY_TARGETS.PEAK_MEMORY_MB);

    // Overall memory health
    const leakDetectedTests = results.filter(r => r.memoryLeakDetected).length;
    expect(leakDetectedTests).toBeLessThanOrEqual(1); // Allow 1 potential false positive
  }, 900000); // 15 minute timeout

  test('Baseline memory within limits', async () => {
    const result = await analyzer['analyzeBaselineMemory']();

    expect(result.metrics.avgMemoryMB).toBeLessThanOrEqual(MEMORY_TARGETS.BASELINE_MEMORY_MB);
    expect(result.memoryLeakDetected).toBe(false);
    expect(result.targetsMet.steadyState).toBe(true);
  }, 30000);

  test('Job import memory efficiency', async () => {
    const result = await analyzer['analyzeJobImportMemory']();

    expect(result.metrics.peakMemoryMB).toBeLessThanOrEqual(MEMORY_TARGETS.PEAK_MEMORY_MB);
    expect(result.metrics.memoryEfficiency).toBeGreaterThan(0.3); // At least 30% efficiency
  }, 300000);

  test('No memory leaks in sustained operations', async () => {
    const result = await analyzer['analyzeSustainedLoad']();

    expect(result.memoryLeakDetected).toBe(false);
    expect(result.metrics.memoryGrowthRate).toBeLessThan(MEMORY_TARGETS.HEAP_GROWTH_RATE - 1);
  }, 600000);

  test('Garbage collection effectiveness', async () => {
    const result = await analyzer['analyzeGarbageCollection']();

    expect(result.gcEffectiveness).toBeGreaterThanOrEqual(MEMORY_TARGETS.GC_EFFECTIVENESS);
  }, 60000);
});

export default MemoryUsageAnalyzer;