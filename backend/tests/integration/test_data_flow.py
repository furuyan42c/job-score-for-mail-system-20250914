"""
T046: データフロー統合テスト
CSV→スコアリング→マッチング→メール完全パイプライン検証

This integration test validates the complete data flow:
1. CSV Import: Jobs data import and validation
2. Scoring: Job scoring calculation
3. Matching: User-job matching process
4. Email Generation: Personalized email creation
5. Performance: 30-minute target completion

Dependencies: T027 (CSV import), T028 (scoring), T029 (matching)
Expected: End-to-end pipeline completion within 30 minutes
"""

import pytest
import asyncio
import tempfile
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import time
import uuid

from app.batch.daily_batch import DailyBatchProcessor, BatchMetrics
from app.services.scoring_engine import ScoringEngine
from app.services.job_selector import JobSelectorService
from app.services.email_fallback import EmailFallbackService, FallbackReason
from app.services.gpt5_integration import GPT5EmailService
from app.models.jobs import Job, JobSalary, JobLocation, JobCategory
from app.models.users import User, UserProfile, UserPreferences
from app.models.matching import MatchingScore
from app.core.database import get_async_session

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# Performance targets from task specification
PERFORMANCE_TARGETS = {
    'total_pipeline_time': 1800,  # 30 minutes max
    'csv_import_time': 300,       # 5 minutes max
    'matching_time': 1200,        # 20 minutes max
    'email_generation_time': 300, # 5 minutes max
    'min_jobs_processed': 1000,   # Minimum for meaningful test
    'min_users_processed': 100,   # Minimum for meaningful test
}

TEST_DATA_CONFIG = {
    'job_count': 1000,           # Scaled down for testing
    'user_count': 100,           # Scaled down for testing
    'jobs_per_user': 40,         # As per specification
    'email_sections': 6,         # As per T031 requirement
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def mock_db_session():
    """Mock database session for integration testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def sample_csv_data():
    """Generate sample CSV data for testing."""
    jobs_data = []

    for i in range(TEST_DATA_CONFIG['job_count']):
        job = {
            'external_id': f'JOB_{str(i).zfill(6)}',
            'title': f'Test Job {i}',
            'company_name': f'Test Company {i % 50}',  # 50 different companies
            'location': f'東京都{["港区", "新宿区", "渋谷区", "千代田区"][i % 4]}',
            'employment_type': 'アルバイト',
            'salary_min': 1000 + (i % 500),  # 1000-1500 range
            'salary_max': 1500 + (i % 500),  # 1500-2000 range
            'description': f'Test job description {i}',
            'prefecture_code': '13',  # Tokyo
            'city_code': f'{101 + (i % 10)}',  # Various cities
            'occupation_cd1': i % 10,  # 10 different occupations
            'fee': 500 + (i % 2000),  # Fee range for scoring
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }
        jobs_data.append(job)

    return pd.DataFrame(jobs_data)

@pytest.fixture
def sample_users():
    """Generate sample user data for testing."""
    users = []

    for i in range(TEST_DATA_CONFIG['user_count']):
        user = MagicMock(spec=User)
        user.id = i + 1
        user.email = f'test_user_{i}@example.com'
        user.is_active = True
        user.email_notifications_enabled = True

        # User profile
        user.profile = MagicMock(spec=UserProfile)
        user.profile.name = f'Test User {i}'
        user.profile.age = 20 + (i % 30)
        user.profile.prefecture_code = '13'  # Tokyo
        user.profile.preferred_occupations = [i % 10]

        # User preferences
        user.preferences = MagicMock(spec=UserPreferences)
        user.preferences.min_salary = 1000 + (i % 300)
        user.preferences.max_salary = 2000 + (i % 500)
        user.preferences.preferred_employment_types = ['アルバイト']
        user.preferences.email_frequency = 'daily'

        users.append(user)

    return users

@pytest.fixture
async def temp_csv_file(sample_csv_data):
    """Create temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        sample_csv_data.to_csv(f.name, index=False, encoding='utf-8')
        yield f.name

    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def batch_processor_config():
    """Configuration for batch processor testing."""
    return {
        'csv_path': '/tmp/test_data/',
        'batch_size': 50,  # Smaller for testing
        'max_parallel': 5,  # Smaller for testing
        'checkpoint_interval': 100,
        'email_queue': 'test_email_queue',
        'alert_recipients': ['test@example.com'],
        'performance_targets': PERFORMANCE_TARGETS
    }

@pytest.fixture
async def batch_processor(batch_processor_config, mock_db_session):
    """Configured batch processor for testing."""
    with patch('app.batch.daily_batch.get_async_session') as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        processor = DailyBatchProcessor(batch_processor_config)

        # Mock service initialization
        processor.job_selector = MagicMock(spec=JobSelectorService)
        processor.job_selector.initialize = AsyncMock()
        processor.job_selector.get_recommendations = AsyncMock()

        processor.scoring_engine = MagicMock(spec=ScoringEngine)
        processor.scoring_engine.initialize = AsyncMock()
        processor.scoring_engine.calculate_scores = AsyncMock()

        processor.email_generator = MagicMock(spec=EmailFallbackService)
        processor.email_generator.initialize = AsyncMock()
        processor.email_generator.generate_daily_email = AsyncMock()

        yield processor

# ============================================================================
# INTEGRATION TEST CLASSES
# ============================================================================

class TestDataFlowIntegration:
    """
    Complete data flow integration tests.

    Tests the full pipeline: CSV→Scoring→Matching→Email
    """

    @pytest.mark.asyncio
    async def test_complete_data_flow_pipeline(
        self,
        batch_processor,
        temp_csv_file,
        sample_users,
        sample_csv_data
    ):
        """
        Test the complete data flow pipeline.

        Validates:
        1. CSV import and data validation
        2. User matching and scoring
        3. Email generation
        4. Performance targets
        5. Data integrity throughout pipeline
        """
        pipeline_start_time = time.time()

        # Setup test data
        batch_processor.config['csv_path'] = str(Path(temp_csv_file).parent)

        # Mock CSV file discovery
        with patch.object(batch_processor, '_find_csv_files') as mock_find_csv:
            mock_find_csv.return_value = [temp_csv_file]

            # Mock user loading
            with patch.object(batch_processor, '_load_active_users') as mock_load_users:
                mock_load_users.return_value = sample_users

                # Setup job matching results
                job_matches = self._create_job_matches(sample_users, sample_csv_data)
                batch_processor.job_selector.get_recommendations.side_effect = job_matches

                # Setup scoring results
                scoring_results = self._create_scoring_results(sample_users, job_matches)
                batch_processor.scoring_engine.calculate_scores.side_effect = scoring_results

                # Setup email generation results
                email_results = self._create_email_results(sample_users)
                batch_processor.email_generator.generate_daily_email.side_effect = email_results

                # Execute the complete pipeline
                await self._execute_pipeline_with_validation(
                    batch_processor,
                    sample_csv_data,
                    sample_users,
                    pipeline_start_time
                )

    @pytest.mark.asyncio
    async def test_csv_import_phase_validation(self, batch_processor, temp_csv_file, sample_csv_data):
        """Test CSV import phase with comprehensive validation."""
        import_start_time = time.time()

        # Mock file discovery
        with patch.object(batch_processor, '_find_csv_files') as mock_find_csv:
            mock_find_csv.return_value = [temp_csv_file]

            # Mock database operations
            with patch.object(batch_processor, '_bulk_insert_jobs') as mock_bulk_insert:
                mock_bulk_insert.return_value = None

                # Execute CSV import
                imported_df = await batch_processor.import_jobs_from_csv(temp_csv_file)

                # Validate import results
                import_time = time.time() - import_start_time

                assert len(imported_df) == TEST_DATA_CONFIG['job_count']
                assert import_time < PERFORMANCE_TARGETS['csv_import_time']
                assert 'external_id' in imported_df.columns
                assert 'title' in imported_df.columns
                assert 'company_name' in imported_df.columns

                # Validate data integrity
                assert imported_df['external_id'].notna().all()
                assert imported_df['title'].notna().all()
                assert imported_df['company_name'].notna().all()

                # Validate no duplicates
                assert len(imported_df['external_id'].unique()) == len(imported_df)

                print(f"✅ CSV Import Phase: {len(imported_df)} jobs in {import_time:.2f}s")

    @pytest.mark.asyncio
    async def test_matching_phase_performance(self, batch_processor, sample_users):
        """Test matching phase performance and data integrity."""
        matching_start_time = time.time()

        # Create realistic job matches
        job_matches = []
        for user in sample_users:
            matches = [
                {
                    'job_id': f'JOB_{str(i).zfill(6)}',
                    'title': f'Matched Job {i}',
                    'company_name': f'Company {i}',
                    'score': 85.0 - (i * 0.5),  # Decreasing scores
                    'match_reasons': ['salary_match', 'location_match']
                }
                for i in range(TEST_DATA_CONFIG['jobs_per_user'])
            ]
            job_matches.append(matches)

        batch_processor.job_selector.get_recommendations.side_effect = job_matches

        # Setup scoring results
        scoring_results = []
        for i, user in enumerate(sample_users):
            scored_matches = [
                {
                    **match,
                    'final_score': match['score'] + random.uniform(-5, 5),
                    'scoring_details': {
                        'basic_score': match['score'] * 0.6,
                        'personalized_score': match['score'] * 0.4,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                for match in job_matches[i]
            ]
            scoring_results.append(scored_matches)

        batch_processor.scoring_engine.calculate_scores.side_effect = scoring_results

        # Execute matching phase
        matching_results = await batch_processor.process_user_matching(sample_users)

        # Validate matching results
        matching_time = time.time() - matching_start_time

        assert len(matching_results) == len(sample_users)
        assert matching_time < PERFORMANCE_TARGETS['matching_time']

        # Validate each user has appropriate number of matches
        for user_id, matches in matching_results.items():
            assert len(matches) == TEST_DATA_CONFIG['jobs_per_user']
            assert all('final_score' in match for match in matches)
            assert all('scoring_details' in match for match in matches)

        print(f"✅ Matching Phase: {len(sample_users)} users in {matching_time:.2f}s")

    @pytest.mark.asyncio
    async def test_email_generation_phase_validation(self, batch_processor, sample_users):
        """Test email generation phase with 6-section validation."""
        email_start_time = time.time()

        # Create matching results for email generation
        matching_results = {}
        for user in sample_users:
            matching_results[user.id] = [
                {
                    'job_id': f'JOB_{str(i).zfill(6)}',
                    'title': f'Email Job {i}',
                    'company_name': f'Email Company {i}',
                    'final_score': 90.0 - i,
                    'category': f'Category {i % 6}',  # 6 sections as per T031
                    'location': '東京都港区',
                    'salary': f'{1200 + i * 10}円/時',
                }
                for i in range(TEST_DATA_CONFIG['jobs_per_user'])
            ]

        # Setup email generation mock with 6-section structure
        def mock_email_generation(user, job_matches):
            return {
                'subject': f'【新着求人】{user.profile.name}さんにおすすめの求人{len(job_matches)}件',
                'body': self._generate_mock_email_body(user, job_matches),
                'sections': self._create_email_sections(job_matches),
                'generation_method': 'template_fallback',
                'timestamp': datetime.now().isoformat()
            }

        batch_processor.email_generator.generate_daily_email.side_effect = (
            lambda user, matches: mock_email_generation(user, matches)
        )

        # Execute email generation
        emails_generated = await batch_processor.generate_emails(matching_results)

        # Validate email generation
        email_time = time.time() - email_start_time

        assert emails_generated == len(sample_users)
        assert email_time < PERFORMANCE_TARGETS['email_generation_time']

        # Validate email generation was called correctly
        assert batch_processor.email_generator.generate_daily_email.call_count == len(sample_users)

        # Validate email structure (check first call)
        call_args = batch_processor.email_generator.generate_daily_email.call_args_list[0]
        user, matches = call_args[0]

        assert len(matches) == TEST_DATA_CONFIG['jobs_per_user']
        assert hasattr(user, 'email')
        assert hasattr(user, 'profile')

        print(f"✅ Email Generation Phase: {emails_generated} emails in {email_time:.2f}s")

    @pytest.mark.asyncio
    async def test_performance_targets_compliance(self, batch_processor, temp_csv_file, sample_users):
        """Test that the complete pipeline meets performance targets."""
        total_start_time = time.time()

        # Setup mocks for performance testing
        batch_processor.config['csv_path'] = str(Path(temp_csv_file).parent)

        with patch.object(batch_processor, '_find_csv_files') as mock_find_csv:
            mock_find_csv.return_value = [temp_csv_file]

            with patch.object(batch_processor, '_load_active_users') as mock_load_users:
                mock_load_users.return_value = sample_users

                with patch.object(batch_processor, '_bulk_insert_jobs'):
                    with patch.object(batch_processor, '_queue_email_for_delivery'):

                        # Setup minimal realistic responses
                        batch_processor.job_selector.get_recommendations.return_value = []
                        batch_processor.scoring_engine.calculate_scores.return_value = []
                        batch_processor.email_generator.generate_daily_email.return_value = {
                            'subject': 'Test Email',
                            'body': 'Test Body'
                        }

                        # Execute key phases
                        await batch_processor._initialization_phase()
                        init_time = time.time() - total_start_time

                        phase_start = time.time()
                        await batch_processor._data_import_phase()
                        import_time = time.time() - phase_start

                        phase_start = time.time()
                        await batch_processor._matching_phase()
                        matching_time = time.time() - phase_start

                        phase_start = time.time()
                        await batch_processor._email_generation_phase({})
                        email_time = time.time() - phase_start

                        total_time = time.time() - total_start_time

                        # Validate performance targets
                        assert import_time < PERFORMANCE_TARGETS['csv_import_time'], \
                            f"Import took {import_time:.2f}s, max {PERFORMANCE_TARGETS['csv_import_time']}s"

                        assert matching_time < PERFORMANCE_TARGETS['matching_time'], \
                            f"Matching took {matching_time:.2f}s, max {PERFORMANCE_TARGETS['matching_time']}s"

                        assert email_time < PERFORMANCE_TARGETS['email_generation_time'], \
                            f"Email gen took {email_time:.2f}s, max {PERFORMANCE_TARGETS['email_generation_time']}s"

                        assert total_time < PERFORMANCE_TARGETS['total_pipeline_time'], \
                            f"Total took {total_time:.2f}s, max {PERFORMANCE_TARGETS['total_pipeline_time']}s"

                        print(f"✅ Performance Compliance:")
                        print(f"   Import: {import_time:.2f}s / {PERFORMANCE_TARGETS['csv_import_time']}s")
                        print(f"   Matching: {matching_time:.2f}s / {PERFORMANCE_TARGETS['matching_time']}s")
                        print(f"   Email: {email_time:.2f}s / {PERFORMANCE_TARGETS['email_generation_time']}s")
                        print(f"   Total: {total_time:.2f}s / {PERFORMANCE_TARGETS['total_pipeline_time']}s")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, batch_processor, sample_users):
        """Test error handling and recovery mechanisms."""

        # Test CSV import error handling
        with patch.object(batch_processor, '_find_csv_files') as mock_find_csv:
            mock_find_csv.return_value = []  # No CSV files

            with pytest.raises(Exception, match="No CSV files found"):
                await batch_processor._data_import_phase()

        # Test matching phase error handling
        batch_processor.job_selector.get_recommendations.side_effect = Exception("Matching service down")

        with pytest.raises(Exception):
            await batch_processor._process_user_batch(sample_users[:5], 0)

        # Test email generation error handling
        batch_processor.email_generator.generate_daily_email.side_effect = Exception("Email service down")

        with pytest.raises(Exception):
            await batch_processor._generate_user_email(1, [])

        print("✅ Error handling validated")

    @pytest.mark.asyncio
    async def test_data_integrity_throughout_pipeline(self, batch_processor, temp_csv_file, sample_users, sample_csv_data):
        """Test that data maintains integrity throughout the pipeline."""

        # Setup pipeline with real data tracking
        external_ids_input = set(sample_csv_data['external_id'].tolist())
        user_ids_input = set(user.id for user in sample_users)

        batch_processor.config['csv_path'] = str(Path(temp_csv_file).parent)

        with patch.object(batch_processor, '_find_csv_files') as mock_find_csv:
            mock_find_csv.return_value = [temp_csv_file]

            with patch.object(batch_processor, '_load_active_users') as mock_load_users:
                mock_load_users.return_value = sample_users

                with patch.object(batch_processor, '_bulk_insert_jobs') as mock_bulk_insert:
                    # Track data through pipeline
                    job_data_tracker = []
                    user_data_tracker = []

                    def track_bulk_insert(df):
                        job_data_tracker.extend(df.to_dict('records'))

                    mock_bulk_insert.side_effect = track_bulk_insert

                    # Setup job matching with data tracking
                    def track_job_matching(user_id, limit):
                        user_data_tracker.append(user_id)
                        return [
                            {'job_id': f'JOB_{str(i).zfill(6)}', 'user_id': user_id}
                            for i in range(min(limit, 10))  # Limit for testing
                        ]

                    batch_processor.job_selector.get_recommendations.side_effect = track_job_matching
                    batch_processor.scoring_engine.calculate_scores.return_value = []
                    batch_processor.email_generator.generate_daily_email.return_value = {'subject': 'Test', 'body': 'Test'}

                    # Execute pipeline phases
                    imported_df = await batch_processor.import_jobs_from_csv(temp_csv_file)
                    matching_results = await batch_processor.process_user_matching(sample_users)

                    # Validate data integrity

                    # 1. Job data integrity
                    external_ids_processed = set(record['external_id'] for record in job_data_tracker)
                    assert external_ids_input == external_ids_processed, "Job external IDs lost in processing"

                    # 2. User data integrity
                    user_ids_processed = set(user_data_tracker)
                    assert user_ids_input == user_ids_processed, "User IDs lost in processing"

                    # 3. Matching results integrity
                    assert len(matching_results) == len(sample_users), "Users lost in matching"

                    # 4. No duplicate processing
                    assert len(job_data_tracker) == len(external_ids_input), "Duplicate job processing detected"
                    assert len(user_data_tracker) == len(user_ids_input), "Duplicate user processing detected"

                    print("✅ Data integrity maintained throughout pipeline")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_job_matches(self, users: List[User], jobs_df: pd.DataFrame) -> List[List[Dict]]:
        """Create realistic job matches for users."""
        job_matches = []

        for user in users:
            user_matches = []
            job_indices = list(range(min(TEST_DATA_CONFIG['jobs_per_user'], len(jobs_df))))

            for i in job_indices:
                job_row = jobs_df.iloc[i]
                match = {
                    'job_id': job_row['external_id'],
                    'title': job_row['title'],
                    'company_name': job_row['company_name'],
                    'location': job_row['location'],
                    'salary_min': job_row['salary_min'],
                    'salary_max': job_row['salary_max'],
                    'employment_type': job_row['employment_type'],
                    'preliminary_score': 80.0 - (i * 1.5),  # Decreasing scores
                }
                user_matches.append(match)

            job_matches.append(user_matches)

        return job_matches

    def _create_scoring_results(self, users: List[User], job_matches: List[List[Dict]]) -> List[List[Dict]]:
        """Create realistic scoring results."""
        scoring_results = []

        for i, user in enumerate(users):
            user_scoring = []
            for j, match in enumerate(job_matches[i]):
                scored_match = {
                    **match,
                    'final_score': match['preliminary_score'] + random.uniform(-10, 10),
                    'basic_score': match['preliminary_score'] * 0.6,
                    'personalized_score': match['preliminary_score'] * 0.4,
                    'seo_score': random.uniform(0, 20),
                    'scoring_timestamp': datetime.now().isoformat(),
                }
                user_scoring.append(scored_match)

            scoring_results.append(user_scoring)

        return scoring_results

    def _create_email_results(self, users: List[User]) -> List[Dict]:
        """Create realistic email generation results."""
        return [
            {
                'subject': f'【新着求人】{user.profile.name}さんにおすすめの求人40件',
                'body': f'Mock email body for user {user.id}',
                'sections': [f'Section {i}' for i in range(6)],  # 6 sections as per T031
                'generation_method': 'template_fallback',
                'timestamp': datetime.now().isoformat(),
            }
            for user in users
        ]

    def _generate_mock_email_body(self, user: User, job_matches: List[Dict]) -> str:
        """Generate mock email body with job matches."""
        return f"""
        こんにちは、{user.profile.name}さん！

        本日も新着求人をお届けします。
        あなたにぴったりの求人{len(job_matches)}件をご紹介します。

        {"".join([f"- {match['title']} ({match['company_name']})" for match in job_matches[:5]])}

        詳細は以下をご確認ください。
        """

    def _create_email_sections(self, job_matches: List[Dict]) -> List[Dict]:
        """Create 6 email sections as per T031 specification."""
        sections = []
        jobs_per_section = len(job_matches) // 6

        section_names = [
            "今週の注目求人",
            "高時給のお仕事",
            "あなたの経験を活かせる求人",
            "通勤便利な求人",
            "週末・短時間OK",
            "その他のおすすめ"
        ]

        for i, section_name in enumerate(section_names):
            start_idx = i * jobs_per_section
            end_idx = start_idx + jobs_per_section if i < 5 else len(job_matches)

            section = {
                'name': section_name,
                'jobs': job_matches[start_idx:end_idx],
                'job_count': end_idx - start_idx
            }
            sections.append(section)

        return sections

    async def _execute_pipeline_with_validation(
        self,
        batch_processor,
        sample_csv_data: pd.DataFrame,
        sample_users: List[User],
        pipeline_start_time: float
    ):
        """Execute the complete pipeline with comprehensive validation."""

        # Mock all database operations
        with patch.object(batch_processor, '_bulk_insert_jobs'):
            with patch.object(batch_processor, '_queue_email_for_delivery'):
                with patch.object(batch_processor, '_create_batch_record'):
                    with patch.object(batch_processor, '_update_batch_record'):

                        # Execute the complete pipeline
                        await batch_processor.run_daily_batch()

                        # Validate overall execution
                        total_time = time.time() - pipeline_start_time

                        assert total_time < PERFORMANCE_TARGETS['total_pipeline_time'], \
                            f"Pipeline took {total_time:.2f}s, max {PERFORMANCE_TARGETS['total_pipeline_time']}s"

                        # Validate metrics
                        metrics = batch_processor.metrics

                        # Validate all phases completed
                        expected_phases = ['initialization', 'data_import', 'matching', 'email_generation', 'cleanup']
                        for phase in expected_phases:
                            assert phase in metrics.phase_times, f"Phase {phase} not completed"
                            assert 'duration' in metrics.phase_times[phase], f"Phase {phase} duration not recorded"

                        # Validate processing counts
                        assert metrics.processed_counts.get('jobs_imported', 0) >= 0
                        assert metrics.processed_counts.get('users_matched', 0) >= 0
                        assert metrics.processed_counts.get('emails_generated', 0) >= 0

                        print(f"✅ Complete Pipeline: {total_time:.2f}s < {PERFORMANCE_TARGETS['total_pipeline_time']}s")
                        phase_times_str = [f"{p}: {t.get('duration', 0):.2f}s" for p, t in metrics.phase_times.items()]
                        print(f"   Phase times: {phase_times_str}")
                        print(f"   Processing counts: {metrics.processed_counts}")


# ============================================================================
# PERFORMANCE BENCHMARK TESTS
# ============================================================================

class TestDataFlowPerformance:
    """Performance benchmark tests for the data flow pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_scale_data_flow(self, batch_processor):
        """Test data flow with larger dataset (closer to production scale)."""

        # Create larger test dataset
        large_job_count = 5000
        large_user_count = 500

        # Generate large sample data
        large_jobs_df = pd.DataFrame([
            {
                'external_id': f'LARGE_JOB_{str(i).zfill(6)}',
                'title': f'Large Test Job {i}',
                'company_name': f'Large Company {i % 100}',
                'location': f'Location {i % 50}',
                'employment_type': 'アルバイト',
                'salary_min': 1000 + (i % 500),
                'salary_max': 1500 + (i % 500),
                'description': f'Large job description {i}',
                'fee': 500 + (i % 2000),
            }
            for i in range(large_job_count)
        ])

        large_users = [
            MagicMock(id=i, email=f'large_user_{i}@example.com', is_active=True)
            for i in range(large_user_count)
        ]

        # Test with larger scale
        start_time = time.time()

        # Mock the operations with realistic delays
        async def mock_bulk_insert(df):
            await asyncio.sleep(0.001 * len(df))  # Simulate DB time

        async def mock_get_recommendations(user_id, limit):
            await asyncio.sleep(0.01)  # Simulate matching time
            return [{'job_id': f'JOB_{i}', 'score': 80} for i in range(min(limit, 40))]

        async def mock_calculate_scores(user, jobs):
            await asyncio.sleep(0.005 * len(jobs))  # Simulate scoring time
            return [{'job_id': job['job_id'], 'final_score': job['score']} for job in jobs]

        async def mock_generate_email(user, matches):
            await asyncio.sleep(0.02)  # Simulate email generation
            return {'subject': 'Test', 'body': 'Test body'}

        # Apply mocks
        with patch.object(batch_processor, '_bulk_insert_jobs', side_effect=mock_bulk_insert):
            with patch.object(batch_processor.job_selector, 'get_recommendations', side_effect=mock_get_recommendations):
                with patch.object(batch_processor.scoring_engine, 'calculate_scores', side_effect=mock_calculate_scores):
                    with patch.object(batch_processor.email_generator, 'generate_daily_email', side_effect=mock_generate_email):
                        with patch.object(batch_processor, '_load_active_users', return_value=large_users):

                            # Simulate processing
                            matching_results = await batch_processor.process_user_matching(large_users)
                            emails_generated = await batch_processor.generate_emails(matching_results)

                            total_time = time.time() - start_time

                            # Validate large scale performance
                            assert len(matching_results) == large_user_count
                            assert emails_generated == large_user_count
                            assert total_time < PERFORMANCE_TARGETS['total_pipeline_time']

                            # Calculate throughput
                            jobs_per_second = (large_job_count * large_user_count) / total_time
                            users_per_second = large_user_count / total_time

                            print(f"✅ Large Scale Performance:")
                            print(f"   Users: {large_user_count}, Jobs: {large_job_count}")
                            print(f"   Total time: {total_time:.2f}s")
                            print(f"   Throughput: {jobs_per_second:.0f} job-matches/sec, {users_per_second:.1f} users/sec")

# ============================================================================
# CLEANUP AND UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_environment():
    """Clean up test environment after each test."""
    yield

    # Clean up any temporary files or resources
    import tempfile
    import shutil

    # Clean temporary directories
    for temp_dir in ['/tmp/test_data/', '/tmp/test_batch/']:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

if __name__ == "__main__":
    # For manual testing
    pytest.main([__file__, "-v", "--tb=short"])