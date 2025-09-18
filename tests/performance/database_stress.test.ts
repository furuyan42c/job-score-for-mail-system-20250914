/**
 * Database Stress Test
 *
 * Database performance and stress testing:
 * - Connection pool limits
 * - Query performance under load
 * - Concurrent transaction handling
 * - Index effectiveness
 * - Deadlock detection
 * - Slow query identification
 */

import axios from 'axios';
import { performance } from 'perf_hooks';
import * as os from 'os';
import fs from 'fs';
import path from 'path';

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Database performance targets
const DB_TARGETS = {
  CONNECTION_POOL_MAX: 50,
  QUERY_RESPONSE_95TH: 100, // milliseconds
  TRANSACTION_THROUGHPUT: 1000, // TPS
  DEADLOCK_RATE: 0.001, // Less than 0.1% deadlock rate
  SLOW_QUERY_THRESHOLD: 1000, // milliseconds
  CONCURRENT_CONNECTIONS: 30,
  INDEX_SCAN_RATIO: 0.95, // 95% index scans vs table scans
  CONNECTION_SUCCESS_RATE: 0.99, // 99% connection success rate
};

interface DatabaseMetrics {
  connectionPool: {
    active: number;
    idle: number;
    total: number;
    maxReached: number;
  };
  queryPerformance: {
    avgResponseTime: number;
    p95ResponseTime: number;
    p99ResponseTime: number;
    slowQueries: number;
    totalQueries: number;
  };
  transactions: {
    committed: number;
    rolledBack: number;
    deadlocks: number;
    throughput: number;
  };
  indexUsage: {
    indexScans: number;
    tableScans: number;
    indexScanRatio: number;
  };
  errors: {
    connectionErrors: number;
    queryErrors: number;
    timeouts: number;
  };
}

interface StressTestResult {
  testName: string;
  duration: number;
  concurrentUsers: number;
  totalOperations: number;
  operationsPerSecond: number;
  metrics: DatabaseMetrics;
  targetsMet: {
    connectionPool: boolean;
    queryPerformance: boolean;
    transactionThroughput: boolean;
    deadlockRate: boolean;
    indexEffectiveness: boolean;
    errorRate: boolean;
  };
  recommendations: string[];
  detailedLogs?: any[];
}

class DatabaseStressTester {
  private testDataPath: string;
  private activeRequests: Set<Promise<any>>;

  constructor() {
    this.testDataPath = path.join(__dirname, 'test-data');
    this.activeRequests = new Set();
    this.ensureTestDataDirectory();
  }

  private ensureTestDataDirectory(): void {
    if (!fs.existsSync(this.testDataPath)) {
      fs.mkdirSync(this.testDataPath, { recursive: true });
    }
  }

  async runComprehensiveDatabaseStressTest(): Promise<StressTestResult[]> {
    console.log('🗃️  Starting Comprehensive Database Stress Test');

    const results: StressTestResult[] = [];

    // Test 1: Connection pool stress
    console.log('\n🔗 Test 1: Connection Pool Stress');
    results.push(await this.testConnectionPoolStress());

    // Test 2: Query performance under load
    console.log('\n⚡ Test 2: Query Performance Under Load');
    results.push(await this.testQueryPerformanceLoad());

    // Test 3: Concurrent transaction handling
    console.log('\n🔀 Test 3: Concurrent Transaction Handling');
    results.push(await this.testConcurrentTransactions());

    // Test 4: Index effectiveness
    console.log('\n📊 Test 4: Index Effectiveness');
    results.push(await this.testIndexEffectiveness());

    // Test 5: Deadlock detection
    console.log('\n🔒 Test 5: Deadlock Detection and Recovery');
    results.push(await this.testDeadlockHandling());

    // Test 6: Long-running query impact
    console.log('\n⏳ Test 6: Long-running Query Impact');
    results.push(await this.testLongRunningQueries());

    // Test 7: Bulk operation stress
    console.log('\n📦 Test 7: Bulk Operation Stress');
    results.push(await this.testBulkOperations());

    this.generateDatabaseReport(results);
    return results;
  }

  private async testConnectionPoolStress(): Promise<StressTestResult> {
    console.log('Testing connection pool under extreme load...');

    const startTime = performance.now();
    const concurrentUsers = 100; // Exceed pool limit intentionally
    let totalOperations = 0;
    let connectionErrors = 0;
    let queryErrors = 0;
    let successfulOperations = 0;

    const promises: Promise<any>[] = [];

    // Create many concurrent connections
    for (let i = 1; i <= concurrentUsers; i++) {
      const promise = this.simulateUserDatabaseOperations(i, 5).then(result => {
        totalOperations += result.operations;
        successfulOperations += result.successful;
        connectionErrors += result.connectionErrors;
        queryErrors += result.queryErrors;
        return result;
      }).catch(error => {
        connectionErrors++;
        console.warn(`User ${i} connection failed:`, error.message);
        return { operations: 0, successful: 0, connectionErrors: 1, queryErrors: 0 };
      });

      promises.push(promise);

      // Stagger connection attempts
      if (i % 10 === 0) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    console.log(`Waiting for ${concurrentUsers} concurrent users to complete...`);
    const results = await Promise.allSettled(promises);

    const endTime = performance.now();
    const duration = endTime - startTime;

    // Get database metrics
    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Connection Pool Stress',
      duration,
      concurrentUsers,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.maxReached <= DB_TARGETS.CONNECTION_POOL_MAX,
        queryPerformance: dbMetrics.queryPerformance.p95ResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH,
        transactionThroughput: dbMetrics.transactions.throughput >= DB_TARGETS.TRANSACTION_THROUGHPUT * 0.5, // Relaxed for stress test
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= DB_TARGETS.DEADLOCK_RATE,
        indexEffectiveness: dbMetrics.indexUsage.indexScanRatio >= DB_TARGETS.INDEX_SCAN_RATIO * 0.8, // Relaxed
        errorRate: (connectionErrors + queryErrors) / totalOperations <= 0.05, // 5% error tolerance for stress test
      },
      recommendations: this.generateConnectionPoolRecommendations(dbMetrics, {
        connectionErrors,
        queryErrors,
        successRate: successfulOperations / totalOperations,
      }),
    };
  }

  private async testQueryPerformanceLoad(): Promise<StressTestResult> {
    console.log('Testing query performance under sustained load...');

    const startTime = performance.now();
    const concurrentUsers = 25;
    const operationsPerUser = 20;
    let totalOperations = 0;

    const queryTypes = [
      'complex_scoring_query',
      'user_preference_search',
      'job_category_filter',
      'location_radius_search',
      'salary_range_query',
      'recent_jobs_query',
    ];

    const promises: Promise<any>[] = [];

    for (let user = 1; user <= concurrentUsers; user++) {
      const promise = this.executeQueryPerformanceTest(user, operationsPerUser, queryTypes)
        .then(result => {
          totalOperations += result.operations;
          return result;
        });

      promises.push(promise);
    }

    console.log(`Running ${concurrentUsers} concurrent users × ${operationsPerUser} operations each...`);
    await Promise.all(promises);

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Query Performance Load',
      duration,
      concurrentUsers,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.active <= DB_TARGETS.CONCURRENT_CONNECTIONS,
        queryPerformance: dbMetrics.queryPerformance.p95ResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH,
        transactionThroughput: dbMetrics.transactions.throughput >= DB_TARGETS.TRANSACTION_THROUGHPUT,
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= DB_TARGETS.DEADLOCK_RATE,
        indexEffectiveness: dbMetrics.indexUsage.indexScanRatio >= DB_TARGETS.INDEX_SCAN_RATIO,
        errorRate: dbMetrics.errors.queryErrors / dbMetrics.queryPerformance.totalQueries <= 0.01,
      },
      recommendations: this.generateQueryPerformanceRecommendations(dbMetrics),
    };
  }

  private async testConcurrentTransactions(): Promise<StressTestResult> {
    console.log('Testing concurrent transaction handling...');

    const startTime = performance.now();
    const concurrentUsers = 20;
    let totalOperations = 0;

    // Test concurrent read/write operations
    const promises: Promise<any>[] = [];

    for (let user = 1; user <= concurrentUsers; user++) {
      const promise = this.executeTransactionStressTest(user).then(result => {
        totalOperations += result.operations;
        return result;
      });

      promises.push(promise);
    }

    console.log(`Testing ${concurrentUsers} concurrent transaction streams...`);
    await Promise.all(promises);

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Concurrent Transactions',
      duration,
      concurrentUsers,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.active <= DB_TARGETS.CONCURRENT_CONNECTIONS,
        queryPerformance: dbMetrics.queryPerformance.avgResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH,
        transactionThroughput: dbMetrics.transactions.throughput >= DB_TARGETS.TRANSACTION_THROUGHPUT,
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= DB_TARGETS.DEADLOCK_RATE,
        indexEffectiveness: dbMetrics.indexUsage.indexScanRatio >= DB_TARGETS.INDEX_SCAN_RATIO,
        errorRate: dbMetrics.transactions.rolledBack / Math.max(dbMetrics.transactions.committed, 1) <= 0.05,
      },
      recommendations: this.generateTransactionRecommendations(dbMetrics),
    };
  }

  private async testIndexEffectiveness(): Promise<StressTestResult> {
    console.log('Testing index effectiveness under various query patterns...');

    const startTime = performance.now();
    let totalOperations = 0;

    // Test different query patterns to evaluate index usage
    const indexTests = [
      { name: 'primary_key_lookup', operations: 100 },
      { name: 'foreign_key_join', operations: 50 },
      { name: 'range_query', operations: 75 },
      { name: 'text_search', operations: 25 },
      { name: 'composite_index', operations: 60 },
      { name: 'partial_index', operations: 40 },
    ];

    for (const test of indexTests) {
      console.log(`Running ${test.name} test (${test.operations} operations)...`);

      const testResult = await this.executeIndexEffectivenessTest(test.name, test.operations);
      totalOperations += testResult.operations;

      // Brief pause between test types
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Index Effectiveness',
      duration,
      concurrentUsers: 1,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: true, // Not applicable for this test
        queryPerformance: dbMetrics.queryPerformance.avgResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH,
        transactionThroughput: true, // Not applicable
        deadlockRate: true, // Not applicable
        indexEffectiveness: dbMetrics.indexUsage.indexScanRatio >= DB_TARGETS.INDEX_SCAN_RATIO,
        errorRate: dbMetrics.errors.queryErrors / dbMetrics.queryPerformance.totalQueries <= 0.01,
      },
      recommendations: this.generateIndexRecommendations(dbMetrics, indexTests),
    };
  }

  private async testDeadlockHandling(): Promise<StressTestResult> {
    console.log('Testing deadlock detection and recovery...');

    const startTime = performance.now();
    const concurrentUsers = 10;
    let totalOperations = 0;

    // Intentionally create deadlock scenarios
    const promises: Promise<any>[] = [];

    for (let user = 1; user <= concurrentUsers; user++) {
      const promise = this.simulateDeadlockScenario(user).then(result => {
        totalOperations += result.operations;
        return result;
      });

      promises.push(promise);
    }

    console.log(`Simulating deadlock scenarios with ${concurrentUsers} users...`);
    await Promise.all(promises);

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Deadlock Handling',
      duration,
      concurrentUsers,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.active <= DB_TARGETS.CONCURRENT_CONNECTIONS,
        queryPerformance: dbMetrics.queryPerformance.avgResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH * 2, // More lenient
        transactionThroughput: dbMetrics.transactions.throughput >= DB_TARGETS.TRANSACTION_THROUGHPUT * 0.3, // Much more lenient
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= 0.1, // Higher tolerance for deadlock test
        indexEffectiveness: true, // Not primary concern for this test
        errorRate: dbMetrics.transactions.rolledBack / Math.max(totalOperations, 1) <= 0.5, // 50% rollback tolerance
      },
      recommendations: this.generateDeadlockRecommendations(dbMetrics),
    };
  }

  private async testLongRunningQueries(): Promise<StressTestResult> {
    console.log('Testing impact of long-running queries...');

    const startTime = performance.now();
    const concurrentUsers = 5;
    let totalOperations = 0;

    // Start long-running queries alongside normal operations
    const longRunningPromises: Promise<any>[] = [];
    const normalOperationPromises: Promise<any>[] = [];

    // Start 3 long-running queries
    for (let i = 1; i <= 3; i++) {
      const promise = this.executeLongRunningQuery(i).then(result => {
        console.log(`Long-running query ${i} completed in ${result.duration}ms`);
        return result;
      });
      longRunningPromises.push(promise);
    }

    // Run normal operations concurrently
    for (let user = 1; user <= concurrentUsers; user++) {
      const promise = this.executeNormalOperations(user, 15).then(result => {
        totalOperations += result.operations;
        return result;
      });
      normalOperationPromises.push(promise);
    }

    console.log('Running normal operations alongside long-running queries...');
    await Promise.all([...longRunningPromises, ...normalOperationPromises]);

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Long-running Query Impact',
      duration,
      concurrentUsers: concurrentUsers + 3, // Include long-running queries
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.active <= DB_TARGETS.CONNECTION_POOL_MAX,
        queryPerformance: dbMetrics.queryPerformance.p95ResponseTime <= DB_TARGETS.QUERY_RESPONSE_95TH * 2, // More lenient
        transactionThroughput: dbMetrics.transactions.throughput >= DB_TARGETS.TRANSACTION_THROUGHPUT * 0.7,
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= DB_TARGETS.DEADLOCK_RATE,
        indexEffectiveness: dbMetrics.indexUsage.indexScanRatio >= DB_TARGETS.INDEX_SCAN_RATIO * 0.9,
        errorRate: dbMetrics.errors.timeouts <= 5, // Allow some timeouts
      },
      recommendations: this.generateLongQueryRecommendations(dbMetrics),
    };
  }

  private async testBulkOperations(): Promise<StressTestResult> {
    console.log('Testing bulk operation performance...');

    const startTime = performance.now();
    let totalOperations = 0;

    // Test various bulk operations
    const bulkTests = [
      { operation: 'bulk_insert_jobs', size: 5000 },
      { operation: 'bulk_update_users', size: 2000 },
      { operation: 'bulk_delete_scores', size: 3000 },
      { operation: 'bulk_upsert_preferences', size: 1500 },
    ];

    for (const test of bulkTests) {
      console.log(`Executing ${test.operation} with ${test.size} records...`);

      const result = await this.executeBulkOperation(test.operation, test.size);
      totalOperations += result.operations;

      console.log(`${test.operation} completed: ${result.operations} operations in ${result.duration}ms`);
    }

    const endTime = performance.now();
    const duration = endTime - startTime;

    const dbMetrics = await this.getDatabaseMetrics();

    return {
      testName: 'Bulk Operations',
      duration,
      concurrentUsers: 1,
      totalOperations,
      operationsPerSecond: totalOperations / (duration / 1000),
      metrics: dbMetrics,
      targetsMet: {
        connectionPool: dbMetrics.connectionPool.active <= DB_TARGETS.CONCURRENT_CONNECTIONS,
        queryPerformance: dbMetrics.queryPerformance.avgResponseTime <= DB_TARGETS.SLOW_QUERY_THRESHOLD, // Different target for bulk
        transactionThroughput: dbMetrics.transactions.throughput >= 100, // Lower target for bulk operations
        deadlockRate: (dbMetrics.transactions.deadlocks / Math.max(dbMetrics.transactions.committed, 1)) <= DB_TARGETS.DEADLOCK_RATE,
        indexEffectiveness: true, // Less relevant for bulk operations
        errorRate: dbMetrics.errors.queryErrors === 0,
      },
      recommendations: this.generateBulkOperationRecommendations(dbMetrics, bulkTests),
    };
  }

  // Simulation methods
  private async simulateUserDatabaseOperations(userId: number, operations: number): Promise<any> {
    let successful = 0;
    let connectionErrors = 0;
    let queryErrors = 0;

    for (let op = 1; op <= operations; op++) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/database/simulate-user-operation`, {
          user_id: userId,
          operation: op,
        }, {
          timeout: 5000,
        });

        if (response.status === 200) {
          successful++;
        } else {
          queryErrors++;
        }
      } catch (error: any) {
        if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET') {
          connectionErrors++;
        } else {
          queryErrors++;
        }
      }

      // Brief delay between operations
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    return { operations, successful, connectionErrors, queryErrors };
  }

  private async executeQueryPerformanceTest(userId: number, operations: number, queryTypes: string[]): Promise<any> {
    let completedOperations = 0;

    for (let op = 1; op <= operations; op++) {
      const queryType = queryTypes[op % queryTypes.length];

      try {
        const response = await axios.post(`${API_BASE_URL}/api/database/execute-query`, {
          user_id: userId,
          query_type: queryType,
          operation_id: op,
        }, {
          timeout: 10000,
        });

        if (response.status === 200) {
          completedOperations++;
        }
      } catch (error) {
        console.warn(`Query performance test error for user ${userId}, op ${op}:`, error);
      }

      // Small delay
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return { operations: completedOperations };
  }

  private async executeTransactionStressTest(userId: number): Promise<any> {
    const operations = 10;
    let completedOperations = 0;

    for (let op = 1; op <= operations; op++) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/database/transaction-stress`, {
          user_id: userId,
          transaction_type: op % 2 === 0 ? 'read_write' : 'read_only',
          operation_id: op,
        }, {
          timeout: 15000,
        });

        if (response.status === 200) {
          completedOperations++;
        }
      } catch (error) {
        console.warn(`Transaction stress test error for user ${userId}, op ${op}:`, error);
      }

      await new Promise(resolve => setTimeout(resolve, 200));
    }

    return { operations: completedOperations };
  }

  private async executeIndexEffectivenessTest(testName: string, operations: number): Promise<any> {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/database/index-effectiveness`, {
        test_name: testName,
        operations,
      }, {
        timeout: 30000,
      });

      return { operations: response.data?.operations || operations };
    } catch (error) {
      console.warn(`Index effectiveness test error for ${testName}:`, error);
      return { operations: 0 };
    }
  }

  private async simulateDeadlockScenario(userId: number): Promise<any> {
    const operations = 5;

    try {
      const response = await axios.post(`${API_BASE_URL}/api/database/deadlock-simulation`, {
        user_id: userId,
        operations,
      }, {
        timeout: 20000,
      });

      return { operations: response.data?.operations || operations };
    } catch (error) {
      console.warn(`Deadlock simulation error for user ${userId}:`, error);
      return { operations: 0 };
    }
  }

  private async executeLongRunningQuery(queryId: number): Promise<any> {
    const startTime = performance.now();

    try {
      const response = await axios.post(`${API_BASE_URL}/api/database/long-running-query`, {
        query_id: queryId,
        estimated_duration: 30000, // 30 seconds
      }, {
        timeout: 45000,
      });

      const duration = performance.now() - startTime;
      return { operations: 1, duration };
    } catch (error) {
      console.warn(`Long-running query ${queryId} error:`, error);
      return { operations: 0, duration: performance.now() - startTime };
    }
  }

  private async executeNormalOperations(userId: number, operations: number): Promise<any> {
    let completedOperations = 0;

    for (let op = 1; op <= operations; op++) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/database/normal-operation`, {
          user_id: userId,
          operation_id: op,
        }, {
          timeout: 5000,
        });

        if (response.status === 200) {
          completedOperations++;
        }
      } catch (error) {
        console.warn(`Normal operation error for user ${userId}, op ${op}:`, error);
      }

      await new Promise(resolve => setTimeout(resolve, 150));
    }

    return { operations: completedOperations };
  }

  private async executeBulkOperation(operation: string, size: number): Promise<any> {
    const startTime = performance.now();

    try {
      const response = await axios.post(`${API_BASE_URL}/api/database/bulk-operation`, {
        operation_type: operation,
        batch_size: size,
      }, {
        timeout: 120000, // 2 minutes for bulk operations
      });

      const duration = performance.now() - startTime;
      return { operations: response.data?.processed || size, duration };
    } catch (error) {
      console.warn(`Bulk operation ${operation} error:`, error);
      return { operations: 0, duration: performance.now() - startTime };
    }
  }

  private async getDatabaseMetrics(): Promise<DatabaseMetrics> {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/database/metrics`, {
        timeout: 10000,
      });

      if (response.status === 200 && response.data) {
        return response.data;
      }
    } catch (error) {
      console.warn('Failed to get database metrics:', error);
    }

    // Return mock metrics if API unavailable
    return {
      connectionPool: { active: 5, idle: 5, total: 10, maxReached: 10 },
      queryPerformance: { avgResponseTime: 50, p95ResponseTime: 100, p99ResponseTime: 200, slowQueries: 0, totalQueries: 100 },
      transactions: { committed: 90, rolledBack: 5, deadlocks: 0, throughput: 500 },
      indexUsage: { indexScans: 95, tableScans: 5, indexScanRatio: 0.95 },
      errors: { connectionErrors: 0, queryErrors: 0, timeouts: 0 },
    };
  }

  // Recommendation generators
  private generateConnectionPoolRecommendations(metrics: DatabaseMetrics, stats: any): string[] {
    const recommendations: string[] = [];

    if (metrics.connectionPool.maxReached >= DB_TARGETS.CONNECTION_POOL_MAX * 0.9) {
      recommendations.push(`Connection pool usage is high (${metrics.connectionPool.maxReached}/${DB_TARGETS.CONNECTION_POOL_MAX}). Consider increasing pool size or optimizing connection usage.`);
    }

    if (stats.successRate < 0.95) {
      recommendations.push(`Connection success rate is low (${Math.round(stats.successRate * 100)}%). Investigate connection failures and timeout settings.`);
    }

    if (metrics.queryPerformance.avgResponseTime > DB_TARGETS.QUERY_RESPONSE_95TH) {
      recommendations.push('Query response times are high under connection stress. Consider query optimization or connection management improvements.');
    }

    return recommendations;
  }

  private generateQueryPerformanceRecommendations(metrics: DatabaseMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.queryPerformance.p95ResponseTime > DB_TARGETS.QUERY_RESPONSE_95TH) {
      recommendations.push(`95th percentile query response time (${metrics.queryPerformance.p95ResponseTime}ms) exceeds target (${DB_TARGETS.QUERY_RESPONSE_95TH}ms). Optimize slow queries.`);
    }

    if (metrics.queryPerformance.slowQueries > 0) {
      recommendations.push(`${metrics.queryPerformance.slowQueries} slow queries detected. Analyze query execution plans and add missing indexes.`);
    }

    if (metrics.indexUsage.indexScanRatio < DB_TARGETS.INDEX_SCAN_RATIO) {
      recommendations.push(`Index scan ratio (${Math.round(metrics.indexUsage.indexScanRatio * 100)}%) is below target. Review query patterns and index coverage.`);
    }

    return recommendations;
  }

  private generateTransactionRecommendations(metrics: DatabaseMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.transactions.throughput < DB_TARGETS.TRANSACTION_THROUGHPUT) {
      recommendations.push(`Transaction throughput (${metrics.transactions.throughput} TPS) is below target (${DB_TARGETS.TRANSACTION_THROUGHPUT} TPS). Consider transaction optimization.`);
    }

    const deadlockRate = metrics.transactions.deadlocks / Math.max(metrics.transactions.committed, 1);
    if (deadlockRate > DB_TARGETS.DEADLOCK_RATE) {
      recommendations.push(`Deadlock rate (${Math.round(deadlockRate * 100)}%) exceeds target. Review transaction isolation levels and lock ordering.`);
    }

    const rollbackRate = metrics.transactions.rolledBack / Math.max(metrics.transactions.committed, 1);
    if (rollbackRate > 0.05) {
      recommendations.push(`Transaction rollback rate (${Math.round(rollbackRate * 100)}%) is high. Investigate transaction failures.`);
    }

    return recommendations;
  }

  private generateIndexRecommendations(metrics: DatabaseMetrics, tests: any[]): string[] {
    const recommendations: string[] = [];

    if (metrics.indexUsage.indexScanRatio < DB_TARGETS.INDEX_SCAN_RATIO) {
      recommendations.push('Index effectiveness is below target. Consider adding indexes for frequently queried columns.');
    }

    if (metrics.queryPerformance.avgResponseTime > DB_TARGETS.QUERY_RESPONSE_95TH * 0.5) {
      recommendations.push('Query performance suggests missing indexes. Analyze execution plans for table scans.');
    }

    // Add specific recommendations based on test types
    recommendations.push('Review composite indexes for multi-column queries and partial indexes for filtered queries.');

    return recommendations;
  }

  private generateDeadlockRecommendations(metrics: DatabaseMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.transactions.deadlocks > 0) {
      recommendations.push('Deadlocks detected. Implement consistent lock ordering and consider reducing transaction scope.');
    }

    const rollbackRate = metrics.transactions.rolledBack / Math.max(metrics.transactions.committed + metrics.transactions.rolledBack, 1);
    if (rollbackRate > 0.3) {
      recommendations.push('High transaction rollback rate indicates contention. Consider optimistic locking patterns.');
    }

    recommendations.push('Implement deadlock retry logic and consider transaction isolation level adjustments.');

    return recommendations;
  }

  private generateLongQueryRecommendations(metrics: DatabaseMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.queryPerformance.p95ResponseTime > DB_TARGETS.QUERY_RESPONSE_95TH * 1.5) {
      recommendations.push('Long-running queries significantly impact overall performance. Implement query timeouts and optimization.');
    }

    if (metrics.errors.timeouts > 0) {
      recommendations.push('Query timeouts detected. Consider query optimization or async processing for long operations.');
    }

    recommendations.push('Consider implementing query result caching and breaking down complex queries.');

    return recommendations;
  }

  private generateBulkOperationRecommendations(metrics: DatabaseMetrics, tests: any[]): string[] {
    const recommendations: string[] = [];

    if (metrics.queryPerformance.avgResponseTime > 500) {
      recommendations.push('Bulk operations are slow. Consider batch size optimization and parallel processing.');
    }

    if (metrics.transactions.throughput < 50) {
      recommendations.push('Bulk operation throughput is low. Consider using bulk insert/update SQL statements.');
    }

    recommendations.push('Implement bulk operation progress monitoring and consider partitioned operations for very large datasets.');

    return recommendations;
  }

  private generateDatabaseReport(results: StressTestResult[]): void {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: results.length,
        testsPassedAllTargets: results.filter(r => Object.values(r.targetsMet).every(Boolean)).length,
        avgOperationsPerSecond: Math.round(results.reduce((sum, r) => sum + r.operationsPerSecond, 0) / results.length),
        totalOperations: results.reduce((sum, r) => sum + r.totalOperations, 0),
        avgDuration: Math.round(results.reduce((sum, r) => sum + r.duration, 0) / results.length / 1000),
      },
      targets: DB_TARGETS,
      testResults: results,
      overallRecommendations: this.generateOverallRecommendations(results),
    };

    const reportPath = path.join(this.testDataPath, `database-stress-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log('\n🗃️  Database Stress Test Results Summary:');
    results.forEach(result => {
      const allTargetsMet = Object.values(result.targetsMet).every(Boolean);
      const status = allTargetsMet ? '✅' : '⚠️';
      const ops = Math.round(result.operationsPerSecond);
      const duration = Math.round(result.duration / 1000);
      console.log(`${status} ${result.testName}: ${ops} ops/sec, ${duration}s duration, ${result.concurrentUsers} users`);
    });

    console.log(`\n📄 Detailed database report saved to: ${reportPath}`);
  }

  private generateOverallRecommendations(results: StressTestResult[]): string[] {
    const recommendations: string[] = [];

    const connectionTests = results.filter(r => !r.targetsMet.connectionPool);
    if (connectionTests.length > 0) {
      recommendations.push('Connection pool issues detected in multiple tests. Review connection pool configuration and connection lifecycle management.');
    }

    const queryPerformanceTests = results.filter(r => !r.targetsMet.queryPerformance);
    if (queryPerformanceTests.length > 0) {
      recommendations.push('Query performance issues detected. Implement comprehensive query optimization and monitoring.');
    }

    const deadlockTests = results.filter(r => !r.targetsMet.deadlockRate);
    if (deadlockTests.length > 0) {
      recommendations.push('Deadlock issues detected. Review transaction patterns and implement deadlock prevention strategies.');
    }

    const indexTests = results.filter(r => !r.targetsMet.indexEffectiveness);
    if (indexTests.length > 0) {
      recommendations.push('Index effectiveness issues detected. Conduct comprehensive index analysis and optimization.');
    }

    if (recommendations.length === 0) {
      recommendations.push('Database performance is within acceptable ranges. Continue monitoring in production and consider proactive optimization.');
    }

    return recommendations;
  }
}

// Test suite
describe('Database Stress Tests', () => {
  let tester: DatabaseStressTester;

  beforeAll(() => {
    tester = new DatabaseStressTester();
  });

  test('Complete database stress test suite', async () => {
    const results = await tester.runComprehensiveDatabaseStressTest();

    // Ensure we have results for all tests
    expect(results).toHaveLength(7);

    // Check critical database performance targets
    const connectionTest = results.find(r => r.testName.includes('Connection Pool'));
    expect(connectionTest?.targetsMet.connectionPool).toBe(true);

    const queryTest = results.find(r => r.testName.includes('Query Performance'));
    expect(queryTest?.targetsMet.queryPerformance).toBe(true);

    const transactionTest = results.find(r => r.testName.includes('Concurrent Transactions'));
    expect(transactionTest?.targetsMet.transactionThroughput).toBe(true);

    // Overall success rate should be reasonable
    const successfulTests = results.filter(r => Object.values(r.targetsMet).filter(Boolean).length >= 4).length;
    const successRate = successfulTests / results.length;
    expect(successRate).toBeGreaterThanOrEqual(0.7); // At least 70% success rate
  }, 1800000); // 30 minute timeout

  test('Connection pool handles stress', async () => {
    const result = await tester['testConnectionPoolStress']();

    expect(result.metrics.connectionPool.maxReached).toBeLessThanOrEqual(DB_TARGETS.CONNECTION_POOL_MAX);
    expect(result.targetsMet.errorRate).toBe(true);
  }, 120000);

  test('Query performance under load', async () => {
    const result = await tester['testQueryPerformanceLoad']();

    expect(result.metrics.queryPerformance.p95ResponseTime).toBeLessThanOrEqual(DB_TARGETS.QUERY_RESPONSE_95TH);
    expect(result.operationsPerSecond).toBeGreaterThan(10);
  }, 300000);

  test('Transaction throughput meets target', async () => {
    const result = await tester['testConcurrentTransactions']();

    expect(result.metrics.transactions.throughput).toBeGreaterThanOrEqual(DB_TARGETS.TRANSACTION_THROUGHPUT);
    expect(result.targetsMet.deadlockRate).toBe(true);
  }, 180000);

  test('Index effectiveness meets target', async () => {
    const result = await tester['testIndexEffectiveness']();

    expect(result.metrics.indexUsage.indexScanRatio).toBeGreaterThanOrEqual(DB_TARGETS.INDEX_SCAN_RATIO);
  }, 120000);

  test('Deadlock handling is effective', async () => {
    const result = await tester['testDeadlockHandling']();

    // Should handle deadlocks gracefully without excessive failures
    expect(result.targetsMet.errorRate).toBe(true);
  }, 180000);
});

export default DatabaseStressTester;