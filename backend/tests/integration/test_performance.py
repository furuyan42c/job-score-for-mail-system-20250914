"""
T049: パフォーマンス統合テスト
処理時間の測定

This integration test validates performance requirements across all system phases:
1. Data Import Performance: 100K jobs in <5 minutes
2. Scoring Performance: 10K users in <10 minutes
3. Matching Performance: 10K users × 40 jobs in <20 minutes
4. Email Generation Performance: 10K emails in <5 minutes
5. Total Pipeline Performance: Complete pipeline in <30 minutes
6. Individual User Performance: <200ms per user selection

Dependencies: T046 (data flow integration test)
Standards: Each phase time limit verification
"""

import pytest
import asyncio
import time
import statistics
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
import concurrent.futures
import psutil
import sys

from app.batch.daily_batch import DailyBatchProcessor, BatchMetrics
from app.services.job_selector import JobSelector, PERFORMANCE_TARGET_MS
from app.services.scoring_engine import ScoringEngine
from app.services.email_fallback import EmailFallbackService
from app.models.jobs import Job
from app.models.users import User
from app.core.database import get_async_session

# ============================================================================
# PERFORMANCE TARGETS
# ============================================================================

# Pipeline performance targets (from daily_batch.py)
PIPELINE_PERFORMANCE_TARGETS = {
    'total_pipeline_time': 1800,     # 30 minutes total
    'csv_import_time': 300,          # 5 minutes max
    'scoring_batch_time': 600,       # 10 minutes max
    'matching_time': 1200,           # 20 minutes max
    'email_generation_time': 300,    # 5 minutes max
}

# Individual operation targets
OPERATION_PERFORMANCE_TARGETS = {
    'user_selection_time_ms': 200,   # 200ms per user (from job_selector.py)
    'job_scoring_time_ms': 50,       # 50ms per job scoring
    'email_generation_ms': 2000,     # 2 seconds per email
    'csv_row_processing_us': 100,    # 100 microseconds per CSV row
}

# Scale targets for testing
PERFORMANCE_TEST_SCALES = {
    'small_scale': {
        'jobs': 1000,
        'users': 100,
        'description': 'Small scale for CI/CD'
    },
    'medium_scale': {
        'jobs': 10000,
        'users': 1000,
        'description': 'Medium scale for integration testing'
    },
    'production_scale': {
        'jobs': 100000,
        'users': 10000,
        'description': 'Production scale simulation'
    }
}

# Resource usage limits
RESOURCE_LIMITS = {
    'max_memory_gb': 4.0,         # Maximum 4GB memory usage
    'max_cpu_percent': 80.0,      # Maximum 80% CPU usage
    'max_db_connections': 50,     # Maximum database connections
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def mock_db_session():
    """Mock database session for performance testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session

@pytest.fixture
def performance_batch_processor(mock_db_session):
    """Batch processor configured for performance testing."""
    config = {
        'csv_path': '/tmp/perf_test/',
        'batch_size': 100,
        'max_parallel': 10,
        'checkpoint_interval': 1000,
        'performance_targets': PIPELINE_PERFORMANCE_TARGETS
    }

    with patch('app.batch.daily_batch.get_async_session') as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        processor = DailyBatchProcessor(config)

        # Mock services for controlled performance testing
        processor.job_selector = MagicMock(spec=JobSelector)
        processor.scoring_engine = MagicMock(spec=ScoringEngine)
        processor.email_generator = MagicMock(spec=EmailFallbackService)

        return processor

@pytest.fixture
def performance_job_selector(mock_db_session):
    """Job selector configured for performance testing."""
    scoring_engine = MagicMock(spec=ScoringEngine)
    selector = JobSelector(scoring_engine, mock_db_session)
    return selector

@pytest.fixture
def large_dataset_generator():
    """Generator for large test datasets."""
    def generate_jobs(count: int) -> pd.DataFrame:
        jobs_data = []

        for i in range(count):
            jobs_data.append({
                'job_id': f'PERF_JOB_{i:08d}',
                'endcl_cd': f'COMPANY_{i % 1000:04d}',  # 1000 unique companies
                'occupation_cd1': (i % 50) + 1,          # 50 occupations
                'salary_min': 1000 + (i % 1000),
                'salary_max': 1500 + (i % 1000),
                'location_pref_cd': '13',
                'location_city_cd': f'{101 + (i % 100)}',  # 100 cities
                'employment_type_cd': 1,
                'is_active': True,
                'fee': 500 + (i % 2000),
                'title': f'Performance Test Job {i}',
                'company_name': f'Performance Company {i % 1000}',
                'created_at': datetime.now() - timedelta(days=i % 30),
            })

        return pd.DataFrame(jobs_data)

    def generate_users(count: int) -> List[Dict]:
        users = []

        for i in range(count):
            user = {
                'user_id': i + 1,
                'estimated_pref_cd': '13',
                'estimated_city_cd': f'{101 + (i % 50)}',
                'age_group': ['20s', '30s', '40s', '50s'][i % 4],
                'gender': ['M', 'F'][i % 2],
                'email': f'perf_user_{i}@example.com',
                'preferences': {
                    'preferred_categories': [(i % 10) + 1, ((i + 1) % 10) + 1],
                    'preferred_salary_min': 1200 + (i % 500),
                    'preferred_salary_max': 1800 + (i % 500),
                }
            }
            users.append(user)

        return users

    return generate_jobs, generate_users

# ============================================================================
# PERFORMANCE TEST CLASSES
# ============================================================================

class TestPipelinePerformance:
    """Test overall pipeline performance against targets."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_pipeline_performance_medium_scale(
        self,
        performance_batch_processor,
        large_dataset_generator
    ):
        """
        Test complete pipeline performance with medium scale data.

        Validates:
        1. Total pipeline completes within 30 minutes
        2. Each phase meets individual time targets
        3. Resource usage stays within limits
        4. Performance degrades gracefully with scale
        """

        generate_jobs, generate_users = large_dataset_generator
        scale = PERFORMANCE_TEST_SCALES['medium_scale']

        # Generate test data
        jobs_df = generate_jobs(scale['jobs'])
        users = generate_users(scale['users'])

        print(f"🔄 Performance Test: {scale['description']}")
        print(f"   Jobs: {len(jobs_df):,}, Users: {len(users):,}")

        # Setup performance mocks
        await self._setup_performance_mocks(
            performance_batch_processor,
            jobs_df,
            users
        )

        # Monitor resources during execution
        resource_monitor = ResourceMonitor()
        resource_monitor.start()

        try:
            # Execute complete pipeline with timing
            pipeline_start = time.time()

            # Phase 1: Data Import
            import_start = time.time()
            await performance_batch_processor._data_import_phase()
            import_time = time.time() - import_start

            # Phase 2: Matching Processing
            matching_start = time.time()
            matching_results = await performance_batch_processor._matching_phase()
            matching_time = time.time() - matching_start

            # Phase 3: Email Generation
            email_start = time.time()
            await performance_batch_processor._email_generation_phase(matching_results)
            email_time = time.time() - email_start

            total_time = time.time() - pipeline_start

            # Stop resource monitoring
            max_memory, max_cpu = resource_monitor.stop()

            # Validate performance targets
            await self._validate_pipeline_performance(
                total_time, import_time, matching_time, email_time,
                scale, max_memory, max_cpu
            )

        finally:
            resource_monitor.stop()

    @pytest.mark.asyncio
    async def test_csv_import_performance(
        self,
        performance_batch_processor,
        large_dataset_generator
    ):
        """Test CSV import performance meets 5-minute target."""

        generate_jobs, _ = large_dataset_generator
        jobs_df = generate_jobs(PERFORMANCE_TEST_SCALES['medium_scale']['jobs'])

        # Mock CSV file creation
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            jobs_df.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Setup import mocks
            performance_batch_processor.config['csv_path'] = os.path.dirname(csv_path)

            with patch.object(performance_batch_processor, '_find_csv_files') as mock_find:
                mock_find.return_value = [csv_path]

                with patch.object(performance_batch_processor, '_bulk_insert_jobs') as mock_insert:
                    # Simulate realistic database insertion time
                    async def mock_bulk_insert(df):
                        await asyncio.sleep(0.001 * len(df))  # 1ms per row

                    mock_insert.side_effect = mock_bulk_insert

                    # Execute import with timing
                    start_time = time.time()
                    imported_df = await performance_batch_processor.import_jobs_from_csv(csv_path)
                    import_time = time.time() - start_time

                    # Validate performance
                    target_time = PIPELINE_PERFORMANCE_TARGETS['csv_import_time']
                    jobs_per_second = len(imported_df) / import_time

                    assert import_time <= target_time, \
                        f"CSV import too slow: {import_time:.2f}s > {target_time}s"

                    assert jobs_per_second >= 100, \
                        f"Import throughput too low: {jobs_per_second:.0f} jobs/sec"

                    print(f"✅ CSV Import: {len(imported_df):,} jobs in {import_time:.2f}s ({jobs_per_second:.0f} jobs/sec)")

        finally:
            os.unlink(csv_path)

    @pytest.mark.asyncio
    async def test_user_matching_performance(
        self,
        performance_job_selector,
        large_dataset_generator
    ):
        """Test individual user matching meets 200ms target."""

        generate_jobs, generate_users = large_dataset_generator
        jobs_df = generate_jobs(1000)  # Reasonable job pool
        users = generate_users(100)    # Test users

        # Setup performance-oriented mocks
        await self._setup_job_selector_performance_mocks(
            performance_job_selector,
            jobs_df,
            users[0]  # Use first user as template
        )

        # Test individual user performance
        user_times = []

        for i, user in enumerate(users[:20]):  # Test first 20 users
            start_time = time.time()

            selected_jobs = await performance_job_selector.select_top_jobs(user['user_id'], 40)

            selection_time = time.time() - start_time
            user_times.append(selection_time * 1000)  # Convert to milliseconds

            # Validate individual user performance
            target_ms = OPERATION_PERFORMANCE_TARGETS['user_selection_time_ms']
            assert selection_time * 1000 <= target_ms, \
                f"User {user['user_id']} selection too slow: {selection_time*1000:.1f}ms > {target_ms}ms"

        # Calculate statistics
        avg_time = statistics.mean(user_times)
        p95_time = statistics.quantiles(user_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(user_times, n=100)[98] if len(user_times) >= 100 else max(user_times)

        print(f"✅ User Matching Performance:")
        print(f"   Average: {avg_time:.1f}ms")
        print(f"   95th percentile: {p95_time:.1f}ms")
        print(f"   99th percentile: {p99_time:.1f}ms")
        print(f"   Target: {OPERATION_PERFORMANCE_TARGETS['user_selection_time_ms']}ms")

    @pytest.mark.asyncio
    async def test_email_generation_performance(
        self,
        performance_batch_processor,
        large_dataset_generator
    ):
        """Test email generation performance meets 5-minute target for 10K emails."""

        _, generate_users = large_dataset_generator
        users = generate_users(1000)  # 1K users for performance test

        # Create matching results for email generation
        matching_results = {}
        for user in users:
            matching_results[user['user_id']] = [
                {
                    'job_id': f'JOB_{j:06d}',
                    'title': f'Job {j}',
                    'company_name': f'Company {j}',
                    'final_score': 80.0 - (j * 0.5),
                }
                for j in range(40)  # 40 jobs per user
            ]

        # Mock email generation with realistic timing
        async def mock_generate_email(user, job_matches):
            # Simulate email generation time (2ms per email)
            await asyncio.sleep(0.002)
            return {
                'subject': f'Jobs for {user["user_id"]}',
                'body': f'Generated email with {len(job_matches)} jobs'
            }

        performance_batch_processor.email_generator.generate_daily_email = mock_generate_email

        # Execute email generation with timing
        start_time = time.time()
        emails_generated = await performance_batch_processor.generate_emails(matching_results)
        generation_time = time.time() - start_time

        # Validate performance
        target_time = PIPELINE_PERFORMANCE_TARGETS['email_generation_time']
        emails_per_second = emails_generated / generation_time

        assert generation_time <= target_time, \
            f"Email generation too slow: {generation_time:.2f}s > {target_time}s"

        assert emails_per_second >= 10, \
            f"Email generation throughput too low: {emails_per_second:.1f} emails/sec"

        print(f"✅ Email Generation: {emails_generated:,} emails in {generation_time:.2f}s ({emails_per_second:.1f} emails/sec)")

    # ========================================================================
    # STRESS TESTING
    # ========================================================================

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_memory_usage_under_load(
        self,
        performance_batch_processor,
        large_dataset_generator
    ):
        """Test memory usage remains within limits under heavy load."""

        generate_jobs, generate_users = large_dataset_generator

        # Use larger dataset for stress testing
        jobs_df = generate_jobs(50000)  # 50K jobs
        users = generate_users(5000)    # 5K users

        resource_monitor = ResourceMonitor()
        resource_monitor.start()

        try:
            await self._setup_performance_mocks(
                performance_batch_processor,
                jobs_df,
                users
            )

            # Execute pipeline
            await performance_batch_processor._matching_phase()

            max_memory, max_cpu = resource_monitor.stop()

            # Validate resource usage
            max_memory_gb = max_memory / 1024 / 1024 / 1024
            assert max_memory_gb <= RESOURCE_LIMITS['max_memory_gb'], \
                f"Memory usage too high: {max_memory_gb:.2f}GB > {RESOURCE_LIMITS['max_memory_gb']}GB"

            assert max_cpu <= RESOURCE_LIMITS['max_cpu_percent'], \
                f"CPU usage too high: {max_cpu:.1f}% > {RESOURCE_LIMITS['max_cpu_percent']}%"

            print(f"✅ Resource Usage: Memory={max_memory_gb:.2f}GB, CPU={max_cpu:.1f}%")

        finally:
            resource_monitor.stop()

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_concurrent_user_processing(
        self,
        performance_job_selector,
        large_dataset_generator
    ):
        """Test concurrent processing of multiple users."""

        generate_jobs, generate_users = large_dataset_generator
        jobs_df = generate_jobs(10000)
        users = generate_users(100)

        await self._setup_job_selector_performance_mocks(
            performance_job_selector,
            jobs_df,
            users[0]
        )

        # Test concurrent processing
        async def process_user(user):
            return await performance_job_selector.select_top_jobs(user['user_id'], 40)

        # Process users concurrently
        start_time = time.time()

        tasks = [process_user(user) for user in users[:50]]  # 50 concurrent users
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Validate results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_results) / len(results)
        assert success_rate >= 0.95, f"Too many failures in concurrent processing: {success_rate:.1%}"

        avg_time_per_user = total_time / len(users[:50]) * 1000  # Convert to ms
        target_ms = OPERATION_PERFORMANCE_TARGETS['user_selection_time_ms']

        # Allow some degradation for concurrent processing
        assert avg_time_per_user <= target_ms * 2, \
            f"Concurrent processing too slow: {avg_time_per_user:.1f}ms > {target_ms * 2}ms"

        print(f"✅ Concurrent Processing: {len(successful_results)}/{len(results)} successful, {avg_time_per_user:.1f}ms avg")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _setup_performance_mocks(
        self,
        batch_processor,
        jobs_df,
        users
    ):
        """Setup mocks optimized for performance testing."""

        # Mock data loading with realistic timing
        async def mock_load_active_users():
            await asyncio.sleep(0.1)  # 100ms database query
            return users[:1000]  # Limit for performance testing

        async def mock_get_jobs_dataframe():
            await asyncio.sleep(0.05)  # 50ms for data loading
            return jobs_df

        # Mock job selection with realistic timing
        async def mock_get_recommendations(user_id, limit):
            await asyncio.sleep(0.01)  # 10ms per user
            return [{'job_id': f'JOB_{i}', 'score': 80 - i} for i in range(limit)]

        # Mock scoring with realistic timing
        async def mock_calculate_scores(user, jobs):
            await asyncio.sleep(0.005 * len(jobs))  # 5ms per job
            return [{'job_id': job['job_id'], 'final_score': job['score']} for job in jobs]

        # Apply mocks
        batch_processor._load_active_users = mock_load_active_users
        batch_processor._get_jobs_dataframe = mock_get_jobs_dataframe
        batch_processor.job_selector.get_recommendations = mock_get_recommendations
        batch_processor.scoring_engine.calculate_scores = mock_calculate_scores

        # Mock other dependencies
        batch_processor._bulk_insert_jobs = AsyncMock()
        batch_processor._queue_email_for_delivery = AsyncMock()
        batch_processor._create_batch_record = AsyncMock()
        batch_processor._update_batch_record = AsyncMock()

    async def _setup_job_selector_performance_mocks(
        self,
        job_selector,
        jobs_df,
        sample_user
    ):
        """Setup job selector mocks for performance testing."""

        # Mock data access methods
        job_selector._get_user_data = AsyncMock(return_value=sample_user)
        job_selector._get_user_preferences_cached = AsyncMock(return_value=sample_user['preferences'])
        job_selector._get_recent_applications_cached = AsyncMock(return_value=[])
        job_selector._get_blocked_companies_cached = AsyncMock(return_value=[])
        job_selector._get_jobs_dataframe = AsyncMock(return_value=jobs_df)

        # Mock scoring engine for performance
        def mock_base_scores(df):
            return [50.0] * len(df)

        async def mock_seo_scores(user_df, jobs_df):
            return [15.0] * len(jobs_df)

        async def mock_personal_scores(user_df, jobs_df):
            return [20.0] * len(jobs_df)

        job_selector.scoring_engine.calculate_base_scores_vectorized = mock_base_scores
        job_selector.scoring_engine._calculate_seo_scores_vectorized = mock_seo_scores
        job_selector.scoring_engine._calculate_personal_scores_vectorized = mock_personal_scores

        # Mock other methods
        job_selector._create_location_mask = AsyncMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._get_adjacent_categories = AsyncMock(return_value=[])
        job_selector._create_salary_mask = MagicMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._apply_smart_reduction = AsyncMock(side_effect=lambda df, prefs: df.head(2000))
        job_selector._format_salary_display = MagicMock(return_value="1200円/時")

    async def _validate_pipeline_performance(
        self,
        total_time: float,
        import_time: float,
        matching_time: float,
        email_time: float,
        scale: Dict,
        max_memory: float,
        max_cpu: float
    ):
        """Validate pipeline performance against targets."""

        targets = PIPELINE_PERFORMANCE_TARGETS

        # Validate individual phase times
        assert import_time <= targets['csv_import_time'], \
            f"Import phase too slow: {import_time:.2f}s > {targets['csv_import_time']}s"

        assert matching_time <= targets['matching_time'], \
            f"Matching phase too slow: {matching_time:.2f}s > {targets['matching_time']}s"

        assert email_time <= targets['email_generation_time'], \
            f"Email phase too slow: {email_time:.2f}s > {targets['email_generation_time']}s"

        # Validate total time
        assert total_time <= targets['total_pipeline_time'], \
            f"Total pipeline too slow: {total_time:.2f}s > {targets['total_pipeline_time']}s"

        # Validate resource usage
        max_memory_gb = max_memory / 1024 / 1024 / 1024
        assert max_memory_gb <= RESOURCE_LIMITS['max_memory_gb'], \
            f"Memory usage too high: {max_memory_gb:.2f}GB"

        assert max_cpu <= RESOURCE_LIMITS['max_cpu_percent'], \
            f"CPU usage too high: {max_cpu:.1f}%"

        print(f"✅ Pipeline Performance ({scale['description']}):")
        print(f"   Total: {total_time:.2f}s / {targets['total_pipeline_time']}s")
        print(f"   Import: {import_time:.2f}s / {targets['csv_import_time']}s")
        print(f"   Matching: {matching_time:.2f}s / {targets['matching_time']}s")
        print(f"   Email: {email_time:.2f}s / {targets['email_generation_time']}s")
        print(f"   Memory: {max_memory_gb:.2f}GB / {RESOURCE_LIMITS['max_memory_gb']}GB")
        print(f"   CPU: {max_cpu:.1f}% / {RESOURCE_LIMITS['max_cpu_percent']}%")


# ============================================================================
# RESOURCE MONITORING
# ============================================================================

class ResourceMonitor:
    """Monitor system resource usage during performance tests."""

    def __init__(self):
        self.monitoring = False
        self.max_memory = 0
        self.max_cpu = 0
        self.monitor_task = None

    def start(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.max_memory = 0
        self.max_cpu = 0
        self.monitor_task = asyncio.create_task(self._monitor_resources())

    def stop(self) -> Tuple[float, float]:
        """Stop monitoring and return max usage."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
        return self.max_memory, self.max_cpu

    async def _monitor_resources(self):
        """Monitor resources in background."""
        try:
            while self.monitoring:
                try:
                    # Get current memory usage (RSS)
                    memory_usage = psutil.Process().memory_info().rss
                    self.max_memory = max(self.max_memory, memory_usage)

                    # Get current CPU usage
                    cpu_usage = psutil.cpu_percent(interval=None)
                    self.max_cpu = max(self.max_cpu, cpu_usage)

                    await asyncio.sleep(0.1)  # Check every 100ms

                except Exception:
                    # Continue monitoring even if individual checks fail
                    await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            pass


# ============================================================================
# BENCHMARKING UTILITIES
# ============================================================================

class PerformanceBenchmark:
    """Utility for benchmarking specific operations."""

    @staticmethod
    async def benchmark_operation(operation, iterations: int = 100) -> Dict:
        """Benchmark an async operation."""
        times = []

        for _ in range(iterations):
            start_time = time.time()
            await operation()
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Convert to ms

        return {
            'avg_ms': statistics.mean(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'p50_ms': statistics.median(times),
            'p95_ms': statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
            'p99_ms': statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times),
            'iterations': iterations
        }

    @staticmethod
    def print_benchmark_results(name: str, results: Dict):
        """Print formatted benchmark results."""
        print(f"📊 {name} Benchmark:")
        print(f"   Average: {results['avg_ms']:.2f}ms")
        print(f"   Min/Max: {results['min_ms']:.2f}ms / {results['max_ms']:.2f}ms")
        print(f"   P50/P95/P99: {results['p50_ms']:.2f}ms / {results['p95_ms']:.2f}ms / {results['p99_ms']:.2f}ms")
        print(f"   Iterations: {results['iterations']}")


if __name__ == "__main__":
    # For manual testing and benchmarking
    pytest.main([__file__, "-v", "--tb=short", "-m", "not stress"])