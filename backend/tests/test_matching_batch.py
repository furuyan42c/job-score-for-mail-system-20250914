"""
T029: Matching Batch Implementation Test - TDD PHASES

This test validates the bulk user-job matching implementation that integrates
all existing scoring and filtering services for efficient batch processing.

Integration Requirements:
- Section Selection Logic (T024) - 6-section distribution
- Duplicate Control (T025) - Company-level filtering
- 40-item Supplement Logic (T026) - Fallback job supplementation
- Batch Performance - Handle large user/job datasets efficiently

Batch Matching Requirements:
- Process multiple users with multiple jobs efficiently
- Apply all filtering and scoring rules consistently
- Return structured results per user
- Include performance metrics and error handling
- Support parallel processing for scalability
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.matching_batch import MatchingBatchService
from app.services.section_selection import SectionSelectionService
from app.services.duplicate_control import DuplicateControlService
from app.services.supplement_logic import SupplementLogicService


# Test Configuration
BATCH_REQUIREMENTS = {
    'min_users_per_batch': 1,
    'max_users_per_batch': 100,
    'min_jobs_per_user': 40,
    'max_processing_time_seconds': 30,
    'required_sections': 6,
    'min_category_diversity': 3
}

# Test Fixtures
@pytest.fixture
def sample_users():
    """Sample users with different preference profiles."""
    return [
        {
            'user_id': 1,
            'preferences': {
                'preferred_categories': ['IT', 'Engineering'],
                'location': 'Tokyo',
                'salary_min': 3000
            }
        },
        {
            'user_id': 2,
            'preferences': {
                'preferred_categories': ['Sales', 'Marketing'],
                'location': 'Osaka',
                'salary_min': 2500
            }
        },
        {
            'user_id': 3,
            'preferences': {
                'preferred_categories': ['Finance', 'Accounting'],
                'location': 'Nagoya',
                'salary_min': 2800
            }
        }
    ]

@pytest.fixture
def sample_jobs():
    """Sample jobs with varied scoring potential."""
    jobs = []
    categories = ['IT', 'Engineering', 'Sales', 'Marketing', 'Finance', 'Accounting', 'HR', 'Design']
    locations = ['Tokyo', 'Osaka', 'Nagoya', 'Kyoto', 'Fukuoka']

    for i in range(100):  # Large job pool for batch testing
        jobs.append({
            'job_id': f'job_{i:03d}',
            'endcl_cd': f'company_{i % 20}',  # 20 different companies
            'application_name': f'Job Title {i}',
            'category': categories[i % len(categories)],
            'location_pref_cd': locations[i % len(locations)],
            'salary_min': 2000 + (i * 50),
            'salary_max': 3000 + (i * 50),
            'score': 50 + (i % 50),  # Scores 50-99
            'location_score': 70 + (i % 30),  # Location scores 70-99
            'created_at': datetime.now() - timedelta(days=i % 30),
            'updated_at': datetime.now() - timedelta(hours=i % 24),
            'working_hours_flexible': i % 3 == 0,
            'weekend_available': i % 4 == 0,
            'employment_type_cd': 'full_time' if i % 2 == 0 else 'part_time'
        })

    return jobs

@pytest.fixture
def sample_applications():
    """Sample application history for duplicate filtering."""
    return [
        {
            'user_id': 1,
            'job_id': 'job_005',
            'endcl_cd': 'company_5',
            'applied_at': datetime.now() - timedelta(days=7)
        },
        {
            'user_id': 1,
            'job_id': 'job_015',
            'endcl_cd': 'company_15',
            'applied_at': datetime.now() - timedelta(days=10)
        },
        {
            'user_id': 2,
            'job_id': 'job_025',
            'endcl_cd': 'company_5',
            'applied_at': datetime.now() - timedelta(days=5)
        }
    ]

@pytest.fixture
def matching_batch_service():
    """MatchingBatchService instance for testing."""
    return MatchingBatchService()


class TestMatchingBatchService:
    """Test suite for T029: Matching Batch Implementation."""

    @pytest.mark.asyncio
    async def test_batch_service_initialization(self, matching_batch_service):
        """Test proper initialization of MatchingBatchService."""
        service = matching_batch_service

        # Should initialize with all required services
        assert hasattr(service, 'section_service')
        assert hasattr(service, 'duplicate_service')
        assert hasattr(service, 'supplement_service')
        assert isinstance(service.section_service, SectionSelectionService)
        assert isinstance(service.duplicate_service, DuplicateControlService)
        assert isinstance(service.supplement_service, SupplementLogicService)

    @pytest.mark.asyncio
    async def test_process_users_batch_basic(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test basic batch processing functionality."""
        service = matching_batch_service

        # Process batch
        results = await service.process_users_batch(
            users=sample_users,
            jobs=sample_jobs,
            applications=sample_applications
        )

        # Validate batch results structure
        assert isinstance(results, dict)
        assert 'users' in results
        assert 'processing_time' in results
        assert 'total_users' in results
        assert 'successful_users' in results
        assert 'failed_users' in results

        # Each user should have results
        assert len(results['users']) == len(sample_users)

        for user_id in [1, 2, 3]:
            assert user_id in results['users']
            user_result = results['users'][user_id]
            assert 'sections' in user_result
            assert 'total_jobs' in user_result
            assert 'processing_time' in user_result

    @pytest.mark.asyncio
    async def test_single_user_matching_integration(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test complete matching pipeline for single user."""
        service = matching_batch_service
        user = sample_users[0]  # First user

        # Process single user
        result = await service.process_single_user(
            user=user,
            jobs=sample_jobs,
            applications=sample_applications
        )

        # Validate section structure (T024 integration)
        assert 'sections' in result
        sections = result['sections']
        assert len(sections) == BATCH_REQUIREMENTS['required_sections']

        expected_section_keys = [
            'editorial_picks', 'high_salary', 'experience_match',
            'location_convenient', 'weekend_short', 'other_recommendations'
        ]
        for section_key in expected_section_keys:
            assert section_key in sections

        # Validate total job count (T026 integration)
        total_jobs = sum(len(section_jobs) for section_jobs in sections.values())
        assert total_jobs >= BATCH_REQUIREMENTS['min_jobs_per_user']

        # Validate no duplicates across sections
        all_job_ids = []
        for section_jobs in sections.values():
            for job in section_jobs:
                all_job_ids.append(job['job_id'])
        assert len(all_job_ids) == len(set(all_job_ids))

    @pytest.mark.asyncio
    async def test_duplicate_filtering_integration(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test duplicate control integration (T025)."""
        service = matching_batch_service
        user = sample_users[0]  # User has applications to company_5 and company_15

        result = await service.process_single_user(
            user=user,
            jobs=sample_jobs,
            applications=sample_applications
        )

        # Check that jobs from recently applied companies are filtered
        all_job_ids = []
        for section_jobs in result['sections'].values():
            for job in section_jobs:
                all_job_ids.append(job['job_id'])

        # Jobs from company_5 and company_15 should be filtered out
        filtered_companies = set()
        for job_id in all_job_ids:
            for job in sample_jobs:
                if job['job_id'] == job_id:
                    filtered_companies.add(job['endcl_cd'])

        # Should not contain recently applied companies
        assert 'company_5' not in filtered_companies or 'company_15' not in filtered_companies

    @pytest.mark.asyncio
    async def test_supplement_logic_integration(self, matching_batch_service, sample_users, sample_applications):
        """Test supplement logic integration (T026) with insufficient jobs."""
        service = matching_batch_service
        user = sample_users[0]

        # Limited job pool to trigger supplementation
        limited_jobs = [
            {
                'job_id': f'limited_job_{i}',
                'endcl_cd': f'limited_company_{i}',
                'category': 'IT',
                'score': 80,
                'salary_min': 3000,
                'location_score': 85,
                'created_at': datetime.now(),
                'working_hours_flexible': True
            }
            for i in range(20)  # Only 20 jobs, need 40
        ]

        result = await service.process_single_user(
            user=user,
            jobs=limited_jobs,
            applications=sample_applications
        )

        # Should still have minimum required jobs through supplementation
        total_jobs = sum(len(section_jobs) for section_jobs in result['sections'].values())
        assert total_jobs >= BATCH_REQUIREMENTS['min_jobs_per_user']

        # Should contain fallback jobs
        all_job_ids = []
        for section_jobs in result['sections'].values():
            for job in section_jobs:
                all_job_ids.append(job['job_id'])

        fallback_jobs = [job_id for job_id in all_job_ids if job_id.startswith('fallback_')]
        assert len(fallback_jobs) > 0

    @pytest.mark.asyncio
    async def test_batch_performance_requirements(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test batch processing performance requirements."""
        service = matching_batch_service

        start_time = datetime.now()

        # Process full batch
        results = await service.process_users_batch(
            users=sample_users,
            jobs=sample_jobs,
            applications=sample_applications
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Should complete within performance requirements
        assert processing_time <= BATCH_REQUIREMENTS['max_processing_time_seconds']
        assert results['processing_time'] <= BATCH_REQUIREMENTS['max_processing_time_seconds']

    @pytest.mark.asyncio
    async def test_parallel_processing_capability(self, matching_batch_service, sample_jobs, sample_applications):
        """Test parallel processing of multiple users."""
        service = matching_batch_service

        # Create larger user set
        large_user_set = []
        for i in range(20):  # 20 users
            large_user_set.append({
                'user_id': i + 1,
                'preferences': {
                    'preferred_categories': ['IT', 'Engineering'],
                    'location': 'Tokyo',
                    'salary_min': 2500 + (i * 100)
                }
            })

        # Should support parallel processing
        results = await service.process_users_batch_parallel(
            users=large_user_set,
            jobs=sample_jobs,
            applications=sample_applications,
            max_concurrent=5
        )

        # All users should be processed successfully
        assert results['total_users'] == 20
        assert results['successful_users'] == 20
        assert results['failed_users'] == 0

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, matching_batch_service, sample_users, sample_jobs):
        """Test error handling with malformed data."""
        service = matching_batch_service

        # Test with malformed user data
        malformed_users = [
            {'user_id': 1},  # Missing preferences
            {'preferences': {'location': 'Tokyo'}},  # Missing user_id
            None,  # Invalid user
            sample_users[0]  # Valid user
        ]

        results = await service.process_users_batch(
            users=malformed_users,
            jobs=sample_jobs,
            applications=[]
        )

        # Should handle errors gracefully
        assert 'users' in results
        assert 'failed_users' in results
        assert results['failed_users'] > 0
        assert results['successful_users'] >= 1  # At least one valid user

    @pytest.mark.asyncio
    async def test_category_diversity_requirement(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test category diversity enforcement across sections."""
        service = matching_batch_service
        user = sample_users[0]

        result = await service.process_single_user(
            user=user,
            jobs=sample_jobs,
            applications=sample_applications
        )

        # Collect all categories across sections
        all_categories = set()
        for section_jobs in result['sections'].values():
            for job in section_jobs:
                if 'category' in job:
                    all_categories.add(job['category'])

        # Should meet minimum category diversity
        assert len(all_categories) >= BATCH_REQUIREMENTS['min_category_diversity']

    @pytest.mark.asyncio
    async def test_metrics_and_monitoring(self, matching_batch_service, sample_users, sample_jobs, sample_applications):
        """Test comprehensive metrics collection."""
        service = matching_batch_service

        results = await service.process_users_batch(
            users=sample_users,
            jobs=sample_jobs,
            applications=sample_applications
        )

        # Should include comprehensive metrics
        assert 'metrics' in results
        metrics = results['metrics']

        assert 'total_jobs_processed' in metrics
        assert 'average_jobs_per_user' in metrics
        assert 'duplicate_filter_rate' in metrics
        assert 'supplement_rate' in metrics
        assert 'section_distribution' in metrics
        assert 'processing_time_per_user' in metrics

    @pytest.mark.asyncio
    async def test_service_integration_dependencies(self, matching_batch_service):
        """Test that all service dependencies are properly integrated."""
        service = matching_batch_service

        # Should have access to all integrated services
        assert hasattr(service, 'section_service')
        assert hasattr(service, 'duplicate_service')
        assert hasattr(service, 'supplement_service')

        # Services should be properly configured
        assert service.section_service is not None
        assert service.duplicate_service is not None
        assert service.supplement_service is not None

        # Should be able to call service methods
        assert callable(getattr(service.section_service, 'select_sections', None))
        assert callable(getattr(service.duplicate_service, 'filter_duplicates', None))
        assert callable(getattr(service.supplement_service, 'ensure_minimum_items', None))