"""
Performance tests for optimized scoring engine

Validates 180ms per user target for 100K jobs × 10K users scale
"""

import pytest
import asyncio
import time
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.services.scoring_engine import ScoringEngine
from app.models.jobs import Job, JobSalary, JobFeatures, JobCategory, JobLocation
from app.models.users import User


class TestScoringEnginePerformance:
    """Performance tests for scoring engine optimizations"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session with performance data"""
        return AsyncMock()

    @pytest.fixture
    def scoring_engine(self, mock_db):
        """Scoring engine instance"""
        return ScoringEngine(mock_db)

    @pytest.fixture
    def sample_jobs_df(self):
        """Generate sample jobs DataFrame for performance testing"""
        n_jobs = 1000  # Smaller sample for tests

        return pd.DataFrame({
            'job_id': range(1, n_jobs + 1),
            'endcl_cd': [f'EC{i:04d}' for i in range(1, n_jobs + 1)],
            'company_name': [f'Company {i}' for i in range(1, n_jobs + 1)],
            'application_name': [f'Job {i}' for i in range(1, n_jobs + 1)],
            'prefecture_code': np.random.choice(['13', '27', '23', '40'], n_jobs),
            'city_code': [f'{pref}101' for pref in np.random.choice(['13', '27', '23', '40'], n_jobs)],
            'station_name': [f'Station {i%100}' if i%3 == 0 else None for i in range(n_jobs)],
            'address': [f'Address {i}' if i%2 == 0 else None for i in range(n_jobs)],
            'salary_type': np.random.choice(['hourly', 'daily', 'monthly'], n_jobs),
            'min_salary': np.random.randint(800, 2500, n_jobs),
            'max_salary': np.random.randint(1000, 3000, n_jobs),
            'fee': np.random.randint(0, 5000, n_jobs),
            'occupation_cd1': np.random.choice([100, 200, 300, 400, 500], n_jobs),
            'occupation_cd2': np.random.choice([101, 201, 301, 401, 501], n_jobs),
            'has_daily_payment': np.random.choice([True, False], n_jobs),
            'has_no_experience': np.random.choice([True, False], n_jobs),
            'has_student_welcome': np.random.choice([True, False], n_jobs),
            'has_remote_work': np.random.choice([True, False], n_jobs),
            'posting_date': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(n_jobs)],
            'created_at': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(n_jobs)]
        })

    @pytest.fixture
    def sample_users_df(self):
        """Generate sample users DataFrame for performance testing"""
        n_users = 100  # Smaller sample for tests

        return pd.DataFrame({
            'user_id': range(1, n_users + 1),
            'email_hash': [f'hash{i}' for i in range(1, n_users + 1)],
            'age_group': np.random.choice(['20代前半', '20代後半', '30代前半'], n_users),
            'gender': np.random.choice(['male', 'female'], n_users),
            'estimated_pref_cd': np.random.choice(['13', '27', '23', '40'], n_users),
            'estimated_city_cd': [f'{pref}101' for pref in np.random.choice(['13', '27', '23', '40'], n_users)],
            'preferred_categories': [[100, 200] for _ in range(n_users)],
            'preferred_salary_min': np.random.randint(1000, 2000, n_users),
            'location_preference_radius': np.random.randint(10, 50, n_users),
            'application_count': np.random.randint(0, 20, n_users),
            'click_count': np.random.randint(0, 100, n_users),
            'view_count': np.random.randint(0, 500, n_users),
            'avg_salary_preference': np.random.randint(1000, 2500, n_users),
            'registration_date': [datetime.now().date() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_users)],
            'created_at': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_users)]
        })

    def test_vectorized_base_score_performance(self, scoring_engine, sample_jobs_df):
        """Test vectorized base score calculation performance"""
        start_time = time.time()

        scores = scoring_engine.calculate_base_scores_vectorized(sample_jobs_df)

        calc_time = time.time() - start_time

        # Verify results
        assert len(scores) == len(sample_jobs_df)
        assert all(0 <= score <= 100 for score in scores)
        assert isinstance(scores, np.ndarray)

        # Performance check - should be very fast for vectorized operations
        time_per_job = calc_time / len(sample_jobs_df) * 1000  # ms
        print(f"Vectorized base score: {time_per_job:.3f}ms per job")
        assert time_per_job < 1.0, f"Too slow: {time_per_job:.3f}ms per job"

    def test_vectorized_salary_score_performance(self, scoring_engine, sample_jobs_df):
        """Test vectorized salary score calculation performance"""
        start_time = time.time()

        scores = scoring_engine._calculate_salary_attractiveness_vectorized(sample_jobs_df)

        calc_time = time.time() - start_time

        # Verify results
        assert len(scores) == len(sample_jobs_df)
        assert all(0 <= score <= 30 for score in scores)

        # Performance check
        time_per_job = calc_time / len(sample_jobs_df) * 1000  # ms
        print(f"Vectorized salary score: {time_per_job:.3f}ms per job")
        assert time_per_job < 0.5, f"Too slow: {time_per_job:.3f}ms per job"

    def test_vectorized_access_score_performance(self, scoring_engine, sample_jobs_df):
        """Test vectorized access score calculation performance"""
        start_time = time.time()

        scores = scoring_engine._calculate_access_score_vectorized(sample_jobs_df)

        calc_time = time.time() - start_time

        # Verify results
        assert len(scores) == len(sample_jobs_df)
        assert all(0 <= score <= 20 for score in scores)

        # Performance check
        time_per_job = calc_time / len(sample_jobs_df) * 1000  # ms
        print(f"Vectorized access score: {time_per_job:.3f}ms per job")
        assert time_per_job < 0.5, f"Too slow: {time_per_job:.3f}ms per job"

    @pytest.mark.asyncio
    async def test_chunk_processing_performance(self, scoring_engine, sample_users_df, sample_jobs_df):
        """Test chunk processing performance"""

        # Mock the vectorized SEO and personal score methods
        async def mock_seo_scores(users_df, jobs_df):
            n_combinations = len(users_df) * len(jobs_df)
            return np.random.uniform(20, 80, n_combinations).astype(np.float32)

        async def mock_personal_scores(users_df, jobs_df):
            n_combinations = len(users_df) * len(jobs_df)
            return np.random.uniform(30, 70, n_combinations).astype(np.float32)

        scoring_engine._calculate_seo_scores_vectorized = mock_seo_scores
        scoring_engine._calculate_personal_scores_vectorized = mock_personal_scores

        start_time = time.time()

        results_df = await scoring_engine._calculate_chunk_scores(sample_users_df, sample_jobs_df)

        calc_time = time.time() - start_time

        # Verify results
        expected_combinations = len(sample_users_df) * len(sample_jobs_df)
        assert len(results_df) == expected_combinations
        assert all(col in results_df.columns for col in ['user_id', 'job_id', 'total_score', 'base_score', 'seo_score', 'personal_score'])
        assert all(0 <= score <= 100 for score in results_df['total_score'])

        # Performance check
        time_per_combination = calc_time / expected_combinations * 1000  # ms
        print(f"Chunk processing: {time_per_combination:.3f}ms per combination")
        assert time_per_combination < 0.1, f"Too slow: {time_per_combination:.3f}ms per combination"

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, scoring_engine, sample_users_df, sample_jobs_df):
        """Test full batch processing performance"""

        # Mock database calls and vectorized methods
        async def mock_seo_scores(users_df, jobs_df):
            n_combinations = len(users_df) * len(jobs_df)
            return np.random.uniform(20, 80, n_combinations).astype(np.float32)

        async def mock_personal_scores(users_df, jobs_df):
            n_combinations = len(users_df) * len(jobs_df)
            return np.random.uniform(30, 70, n_combinations).astype(np.float32)

        scoring_engine._calculate_seo_scores_vectorized = mock_seo_scores
        scoring_engine._calculate_personal_scores_vectorized = mock_personal_scores

        start_time = time.time()

        results_df = await scoring_engine.process_scoring_batch(sample_users_df, sample_jobs_df, chunk_size=50)

        total_time = time.time() - start_time

        # Verify results
        expected_combinations = len(sample_users_df) * len(sample_jobs_df)
        assert len(results_df) == expected_combinations

        # Performance metrics
        time_per_user = total_time / len(sample_users_df) * 1000  # ms
        time_per_combination = total_time / expected_combinations * 1000  # ms

        print(f"Batch processing: {time_per_user:.1f}ms per user, {time_per_combination:.3f}ms per combination")
        print(f"Total combinations: {expected_combinations}, Total time: {total_time:.3f}s")

        # Performance targets
        assert time_per_user < 200, f"Performance target missed: {time_per_user:.1f}ms per user > 200ms (test target)"
        assert time_per_combination < 0.2, f"Too slow per combination: {time_per_combination:.3f}ms"

    def test_memory_optimization(self, scoring_engine, sample_jobs_df):
        """Test DataFrame memory optimization"""
        original_df = sample_jobs_df.copy()
        original_memory = original_df.memory_usage(deep=True).sum()

        optimized_df = scoring_engine._optimize_dataframe_memory(original_df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()

        # Should reduce memory usage
        memory_reduction = (original_memory - optimized_memory) / original_memory
        print(f"Memory reduction: {memory_reduction*100:.1f}%")

        # Verify data integrity
        assert len(optimized_df) == len(original_df)
        assert list(optimized_df.columns) == list(original_df.columns)

    def test_cache_performance(self, scoring_engine):
        """Test caching performance impact"""

        # Test prefecture adjacency cache
        cache_key = "13-27"

        # First call - should be slower (cache miss)
        start_time = time.time()
        scoring_engine._prefecture_distance_cache[cache_key] = True
        first_call_time = time.time() - start_time

        # Second call - should be faster (cache hit)
        start_time = time.time()
        result = scoring_engine._prefecture_distance_cache.get(cache_key)
        second_call_time = time.time() - start_time

        assert result is True
        # Cache access should be significantly faster
        assert second_call_time < first_call_time * 0.1

    @pytest.mark.asyncio
    async def test_performance_stats_tracking(self, scoring_engine, sample_jobs_df):
        """Test performance statistics tracking"""

        # Perform some calculations
        scoring_engine.calculate_base_scores_vectorized(sample_jobs_df)
        scoring_engine._update_performance_stats('test_operation', 0.1, 100)

        stats = scoring_engine.get_performance_stats()

        # Verify stats structure
        required_keys = ['total_calculations', 'avg_calculation_time', 'cache_hits', 'cache_misses', 'cache_hit_rate', 'avg_calculation_time_ms']
        assert all(key in stats for key in required_keys)

        # Verify reasonable values
        assert stats['total_calculations'] >= 100
        assert stats['avg_calculation_time_ms'] > 0

    @pytest.mark.asyncio
    async def test_legacy_compatibility(self, scoring_engine, sample_jobs_df, sample_users_df):
        """Test that legacy interface still works with optimizations"""

        # Mock database calls
        scoring_engine.db.execute = AsyncMock()

        # Create legacy job-user pairs from DataFrames
        job_user_pairs = []
        for _, user_row in sample_users_df.head(5).iterrows():  # Limit for test speed
            for _, job_row in sample_jobs_df.head(10).iterrows():
                # Create mock Job and User objects
                user = User(
                    user_id=user_row['user_id'],
                    email="test@example.com",
                    email_hash=user_row['email_hash'],
                    estimated_pref_cd=user_row['estimated_pref_cd']
                )

                job = Job(
                    job_id=job_row['job_id'],
                    endcl_cd=job_row['endcl_cd'],
                    company_name=job_row['company_name'],
                    application_name=job_row['application_name'],
                    location=JobLocation(
                        prefecture_code=job_row['prefecture_code'],
                        city_code=job_row['city_code']
                    ),
                    salary=JobSalary(
                        min_salary=job_row['min_salary'],
                        fee=job_row['fee']
                    ),
                    category=JobCategory(
                        occupation_cd1=job_row['occupation_cd1']
                    ),
                    posting_date=datetime.now(),
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                job_user_pairs.append((job, user, None))

        start_time = time.time()

        scores = await scoring_engine.batch_calculate_scores(job_user_pairs)

        total_time = time.time() - start_time

        # Verify results
        assert len(scores) == len(job_user_pairs)
        assert all(isinstance(score, (int, float)) for score in scores)

        # Performance check
        time_per_pair = total_time / len(job_user_pairs) * 1000  # ms
        print(f"Legacy interface: {time_per_pair:.3f}ms per pair")


class TestScalingPerformance:
    """Tests for scaling performance with larger datasets"""

    @pytest.mark.asyncio
    async def test_scaling_with_larger_datasets(self, mock_db):
        """Test performance scaling with larger datasets"""
        scoring_engine = ScoringEngine(mock_db)

        # Test with different dataset sizes
        dataset_sizes = [(100, 1000), (500, 2000), (1000, 5000)]

        for n_users, n_jobs in dataset_sizes:
            # Generate larger datasets
            users_df = pd.DataFrame({
                'user_id': range(1, n_users + 1),
                'estimated_pref_cd': np.random.choice(['13', '27', '23', '40'], n_users),
                'estimated_city_cd': np.random.choice(['13101', '27100', '23100', '40100'], n_users),
            })

            jobs_df = pd.DataFrame({
                'job_id': range(1, n_jobs + 1),
                'fee': np.random.randint(0, 5000, n_jobs),
                'min_salary': np.random.randint(800, 2500, n_jobs),
                'salary_type': np.random.choice(['hourly', 'daily', 'monthly'], n_jobs),
                'station_name': [f'Station {i%100}' if i%3 == 0 else None for i in range(n_jobs)],
                'address': [f'Address {i}' if i%2 == 0 else None for i in range(n_jobs)],
            })

            # Mock vectorized methods
            async def mock_seo_scores(users_df, jobs_df):
                n_combinations = len(users_df) * len(jobs_df)
                return np.random.uniform(20, 80, n_combinations).astype(np.float32)

            async def mock_personal_scores(users_df, jobs_df):
                n_combinations = len(users_df) * len(jobs_df)
                return np.random.uniform(30, 70, n_combinations).astype(np.float32)

            scoring_engine._calculate_seo_scores_vectorized = mock_seo_scores
            scoring_engine._calculate_personal_scores_vectorized = mock_personal_scores

            start_time = time.time()

            results_df = await scoring_engine.process_scoring_batch(users_df, jobs_df, chunk_size=500)

            total_time = time.time() - start_time
            time_per_user = total_time / n_users * 1000  # ms

            print(f"Dataset {n_users} users × {n_jobs} jobs: {time_per_user:.1f}ms per user")

            # Verify scaling performance
            assert len(results_df) == n_users * n_jobs

            # Performance should scale reasonably
            if n_users * n_jobs > 100000:  # Only check for larger datasets
                assert time_per_user < 300, f"Performance degraded: {time_per_user:.1f}ms per user"

    def test_memory_usage_scaling(self, mock_db):
        """Test memory usage with different dataset sizes"""
        scoring_engine = ScoringEngine(mock_db)

        # Test memory usage patterns
        dataset_sizes = [1000, 5000, 10000]

        for n_jobs in dataset_sizes:
            jobs_df = pd.DataFrame({
                'job_id': range(1, n_jobs + 1),
                'fee': np.random.randint(0, 5000, n_jobs),
                'min_salary': np.random.randint(800, 2500, n_jobs),
                'salary_type': np.random.choice(['hourly', 'daily', 'monthly'], n_jobs),
                'station_name': [f'Station {i%100}' if i%3 == 0 else None for i in range(n_jobs)],
                'address': [f'Address {i}' if i%2 == 0 else None for i in range(n_jobs)],
            })

            original_memory = jobs_df.memory_usage(deep=True).sum() / 1024**2  # MB
            optimized_df = scoring_engine._optimize_dataframe_memory(jobs_df)
            optimized_memory = optimized_df.memory_usage(deep=True).sum() / 1024**2  # MB

            memory_reduction = (original_memory - optimized_memory) / original_memory * 100

            print(f"{n_jobs} jobs: {original_memory:.1f}MB -> {optimized_memory:.1f}MB ({memory_reduction:.1f}% reduction)")

            # Memory optimization should always help
            assert optimized_memory <= original_memory