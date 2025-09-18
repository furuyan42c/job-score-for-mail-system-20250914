# Performance Test Suite

Comprehensive performance testing for the job matching system designed to handle **100,000 jobs × 10,000 users** at scale.

## 📊 Performance Targets

### Batch Processing
- **Total Runtime**: 30 minutes for complete cycle
- **CSV Import**: 100,000 jobs in 5 minutes
- **User Matching**: 10,000 users in 20 minutes
- **Email Generation**: 10,000 emails in 5 minutes

### Scoring Engine
- **Single User**: <180ms for 100K jobs
- **Throughput**: 55+ users/second
- **Batch Processing**: 1,000 users in <180 seconds
- **Cache Hit Rate**: >90% after warmup

### Memory Constraints
- **Peak Memory**: <4GB for batch processing
- **Steady State**: <2GB during normal operation
- **No Memory Leaks**: Stable over 24 hours

### Database Performance
- **Connection Pool**: Max 50 connections
- **Query Response**: 95th percentile <100ms
- **Transaction Throughput**: 1000+ TPS

## 🗂️ Test Suite Structure

```
tests/performance/
├── batch_processing_load.test.ts    # End-to-end batch processing
├── scoring_engine_benchmark.test.ts # Scoring performance & optimization
├── memory_usage.test.ts            # Memory analysis & leak detection
├── database_stress.test.ts         # Database performance & stress
├── generate-test-data.ts           # Test data generation utility
├── run-load-test.sh               # Test runner script with monitoring
├── package.json                   # Dependencies & scripts
├── jest.setup.js                  # Test configuration
├── tsconfig.json                  # TypeScript configuration
└── test-data/                     # Generated test data & reports
```

## 🚀 Quick Start

### Prerequisites

1. **System Requirements**:
   - Node.js 18+ with TypeScript support
   - 4GB+ available memory
   - Backend API running at `http://localhost:8000`

2. **Install Dependencies**:
   ```bash
   cd tests/performance
   npm install
   ```

### Running Tests

#### Complete Performance Suite
```bash
# Run all performance tests with monitoring
./run-load-test.sh

# Run in parallel (faster but may affect individual measurements)
./run-load-test.sh --parallel

# Quick test without stress tests
./run-load-test.sh --parallel --no-stress
```

#### Individual Test Categories
```bash
# Generate test data first
npm run generate-data

# Memory analysis with GC profiling
npm run memory-test

# Scoring engine benchmarks
npm run benchmark

# Database stress testing
npm run stress-test

# Batch processing load test
npm run batch-test
```

### Environment Configuration

Set environment variables for different test scenarios:

```bash
# Production-like testing
export API_BASE_URL=http://staging.api.com
export NODE_ENV=production
export PARALLEL_TESTS=true

# Memory leak detection
export NODE_OPTIONS="--expose-gc --max-old-space-size=4096"

# Debug mode
export DEBUG=performance:*
```

## 📋 Test Descriptions

### 1. Batch Processing Load Test (`batch_processing_load.test.ts`)

**Purpose**: Validates end-to-end system performance under production load.

**Tests**:
- CSV import of 100K jobs with memory monitoring
- Concurrent processing of 10K users
- Email generation for matched results
- Resource utilization tracking throughout

**Key Metrics**:
- Total execution time vs 30-minute target
- Peak memory usage during each phase
- CPU utilization patterns
- Error rates and recovery

### 2. Scoring Engine Benchmark (`scoring_engine_benchmark.test.ts`)

**Purpose**: Measures core scoring algorithm performance and optimization effectiveness.

**Tests**:
- Single user vs 100K jobs (<180ms target)
- Batch processing of 1K users (<180s target)
- Vectorized operations vs individual calculations
- Cache hit rate analysis (>90% target)
- Memory efficiency optimization

**Key Metrics**:
- Response times (average, 95th, 99th percentile)
- Throughput (users/second)
- Cache effectiveness
- Memory usage optimization ratios
- Vectorization speedup factors

### 3. Memory Usage Analysis (`memory_usage.test.ts`)

**Purpose**: Comprehensive memory profiling and leak detection.

**Tests**:
- Baseline memory measurement
- Memory growth during job import
- User processing memory patterns
- Memory leak detection through repeated operations
- Garbage collection effectiveness
- Sustained load memory stability

**Key Metrics**:
- Peak memory usage during operations
- Memory growth rates
- Garbage collection recovery ratios
- Memory leak detection (heap growth trends)
- Steady-state memory consumption

### 4. Database Stress Test (`database_stress.test.ts`)

**Purpose**: Database performance under high concurrency and stress conditions.

**Tests**:
- Connection pool stress (up to max limits)
- Concurrent query performance
- Transaction deadlock handling
- Index effectiveness analysis
- Long-running query impact
- Bulk operation performance

**Key Metrics**:
- Connection pool utilization
- Query response times under load
- Transaction throughput (TPS)
- Deadlock rates and recovery
- Index scan vs table scan ratios
- Bulk operation efficiency

### 5. Test Data Generator (`generate-test-data.ts`)

**Purpose**: Generates realistic, large-scale test datasets.

**Features**:
- 100K jobs with realistic distribution patterns
- 10K users with varied preferences and activity levels
- 500K user actions with temporal patterns
- Multiple export formats (CSV, JSON, SQL)
- Configurable data patterns and sizes
- Seeded random generation for reproducibility

## 📊 Monitoring & Reporting

### Automated Monitoring

The test runner (`run-load-test.sh`) provides:
- **System Resource Monitoring**: CPU, memory, disk usage
- **Real-time Progress Tracking**: Test completion percentages
- **Automated Report Generation**: HTML and JSON formats
- **Alert System**: Notifications for target failures
- **Performance Charts**: Visual representation of metrics

### Report Structure

Generated reports include:
```
test-data/reports/
├── performance_report_[timestamp].html    # Comprehensive HTML report
├── performance_summary_[timestamp].json   # Machine-readable summary
├── charts_[timestamp]/                    # Performance visualization
└── individual test reports...             # Detailed test-specific data
```

### Sample Report Sections

1. **Executive Summary**: Pass/fail rates, overall performance
2. **Performance Metrics**: Detailed timing and resource usage
3. **Target Compliance**: Color-coded target achievement
4. **System Information**: Environment and configuration details
5. **Recommendations**: Specific optimization suggestions
6. **Historical Trends**: Performance over time (if available)

## 🎯 Performance Optimization Guidelines

### Memory Optimization
- **Streaming Processing**: Use data streams for large datasets
- **Memory Pooling**: Reuse objects to reduce GC pressure
- **Batch Size Tuning**: Optimize chunk sizes for memory usage
- **Garbage Collection**: Tune GC settings for workload

### Database Optimization
- **Connection Pooling**: Configure optimal pool sizes
- **Query Optimization**: Use EXPLAIN ANALYZE for slow queries
- **Index Strategy**: Ensure indexes cover query patterns
- **Transaction Scope**: Minimize transaction duration

### Application Performance
- **Caching Strategy**: Implement multi-level caching
- **Vectorization**: Use batch operations where possible
- **Asynchronous Processing**: Leverage concurrent execution
- **Resource Management**: Monitor and optimize resource usage

## 🔧 Configuration Options

### Test Configuration

Modify test behavior via environment variables or configuration files:

```javascript
// Example configuration in generate-test-data.ts
const config = {
  jobs: {
    count: 100000,
    distribution: {
      prefectures: [
        { code: '13', weight: 0.3 }, // Tokyo - 30%
        { code: '27', weight: 0.15 }, // Osaka - 15%
        // ...
      ],
      salaryRanges: [
        { min: 800, max: 1200, weight: 0.2 },
        // ...
      ]
    }
  },
  users: {
    count: 10000,
    // User distribution patterns
  },
  output: {
    formats: ['csv', 'json', 'sql'],
    chunkSize: 1000,
    compression: true
  }
};
```

### Performance Targets

Customize performance targets in each test file:

```typescript
const TARGETS = {
  TOTAL_RUNTIME: 30 * 60 * 1000, // 30 minutes
  SINGLE_USER_RESPONSE: 180,      // 180ms
  CACHE_HIT_RATE: 0.90,          // 90%
  PEAK_MEMORY_MB: 4 * 1024,      // 4GB
  // ...
};
```

## 🚨 Troubleshooting

### Common Issues

**Memory Errors**:
```bash
# Increase Node.js heap size
export NODE_OPTIONS="--max-old-space-size=8192"

# Enable garbage collection debugging
export NODE_OPTIONS="--expose-gc --trace-gc"
```

**API Connection Issues**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check API configuration
export API_BASE_URL=http://your-api-server:port
```

**Test Timeouts**:
```bash
# Increase Jest timeout
npx jest --testTimeout=600000

# Run tests individually
npm run benchmark -- --testNamePattern="specific test"
```

**Database Connection Issues**:
- Verify database is accessible
- Check connection pool configuration
- Monitor database logs for errors
- Ensure sufficient database resources

### Performance Analysis

**Slow Tests**:
1. Check system resource usage
2. Analyze database query performance
3. Review memory allocation patterns
4. Consider concurrent request limits

**Memory Leaks**:
1. Run tests with `--expose-gc` flag
2. Monitor heap growth over time
3. Use memory profilers for detailed analysis
4. Check for event listener leaks

**Database Bottlenecks**:
1. Monitor connection pool usage
2. Analyze slow query logs
3. Check index effectiveness
4. Review transaction patterns

## 📈 Continuous Integration

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Performance Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd tests/performance
          npm ci
      - name: Run performance tests
        run: |
          cd tests/performance
          ./run-load-test.sh --no-alerts
        env:
          API_BASE_URL: ${{ secrets.STAGING_API_URL }}
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: tests/performance/test-data/reports/
```

### Monitoring Integration

- **Metrics Collection**: Export results to monitoring systems
- **Alerting**: Configure alerts for performance regressions
- **Dashboards**: Create performance trend dashboards
- **Historical Analysis**: Track performance over time

## 🤝 Contributing

### Adding New Tests

1. **Create Test File**: Follow naming convention `*.test.ts`
2. **Define Targets**: Set clear performance targets
3. **Implement Monitoring**: Track relevant metrics
4. **Update Runner**: Add to `run-load-test.sh`
5. **Document**: Update this README

### Test Standards

- **Clear Objectives**: Each test should have specific targets
- **Comprehensive Monitoring**: Track all relevant metrics
- **Reproducible**: Tests should be deterministic where possible
- **Efficient**: Minimize test execution time while maintaining accuracy
- **Documented**: Clear documentation for setup and interpretation

## 📚 Resources

### Documentation
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)
- [TypeScript Configuration](https://www.typescriptlang.org/docs/)
- [Node.js Performance Monitoring](https://nodejs.org/api/perf_hooks.html)

### Performance Tools
- [Node.js Built-in Profiler](https://nodejs.org/en/docs/guides/simple-profiling/)
- [Chrome DevTools](https://developers.google.com/web/tools/chrome-devtools)
- [Artillery Load Testing](https://artillery.io/)

### Best Practices
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Database Performance Optimization](https://use-the-index-luke.com/)
- [Memory Management in Node.js](https://nodejs.org/en/docs/guides/debugging-getting-started/)

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Maintainer**: Performance Engineering Team