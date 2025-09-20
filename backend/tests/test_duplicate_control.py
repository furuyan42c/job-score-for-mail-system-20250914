"""
T025: Duplicate Control Service Tests
RED PHASE - Failing tests for duplicate control functionality

This test validates duplicate detection and prevention:
1. Detection of duplicate job entries
2. User-job pair duplicate prevention
3. Time-based duplicate rules (e.g., same job within 7 days)
4. Duplicate resolution strategies
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from app.services.duplicate_control import DuplicateControlService
from app.models.users import User
from app.models.jobs import Job


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
async def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def duplicate_service(mock_db_session):
    """Duplicate control service instance."""
    return DuplicateControlService(mock_db_session)


@pytest.fixture
def test_user():
    """Test user for duplicate control testing."""
    return {
        'user_id': 1001,
        'email': 'test@example.com',
        'created_at': datetime.now() - timedelta(days=30)
    }


@pytest.fixture
def test_jobs():
    """Test job entries."""
    return [
        {
            'job_id': 'JOB_001',
            'endcl_cd': 'COMPANY_001',
            'application_name': 'Software Engineer',
            'created_at': datetime.now() - timedelta(days=10),
            'updated_at': datetime.now() - timedelta(days=5)
        },
        {
            'job_id': 'JOB_002',
            'endcl_cd': 'COMPANY_001',
            'application_name': 'Senior Software Engineer',
            'created_at': datetime.now() - timedelta(days=8),
            'updated_at': datetime.now() - timedelta(days=3)
        },
        {
            'job_id': 'JOB_003',
            'endcl_cd': 'COMPANY_002',
            'application_name': 'Product Manager',
            'created_at': datetime.now() - timedelta(days=5),
            'updated_at': datetime.now() - timedelta(days=1)
        }
    ]


# ============================================================================
# DUPLICATE DETECTION TESTS (RED PHASE)
# ============================================================================

class TestDuplicateDetection:
    """Test duplicate detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_duplicate_job_entries(self, duplicate_service, test_jobs):
        """
        Test detection of duplicate job entries.

        Should detect jobs with same endcl_cd (company code).
        """
        # This test will FAIL until we implement the service
        duplicates = await duplicate_service.detect_duplicate_jobs(test_jobs)

        # Should detect JOB_001 and JOB_002 as duplicates (same company)
        assert len(duplicates) > 0, "Should detect duplicate jobs from same company"

        # Should group by endcl_cd
        duplicate_groups = duplicates.get('by_company', [])
        assert len(duplicate_groups) >= 1, "Should find at least one duplicate group"

        # COMPANY_001 should have 2 jobs
        company_001_group = next((g for g in duplicate_groups if g['endcl_cd'] == 'COMPANY_001'), None)
        assert company_001_group is not None, "Should find COMPANY_001 duplicate group"
        assert len(company_001_group['jobs']) == 2, "COMPANY_001 should have 2 duplicate jobs"

    @pytest.mark.asyncio
    async def test_detect_user_job_pair_duplicates(self, duplicate_service, test_user, test_jobs):
        """
        Test detection of user-job pair duplicates.

        Should detect if user already applied to specific jobs.
        """
        # Mock existing user applications
        existing_applications = [
            {'user_id': 1001, 'job_id': 'JOB_001', 'applied_at': datetime.now() - timedelta(days=3)},
            {'user_id': 1001, 'job_id': 'JOB_003', 'applied_at': datetime.now() - timedelta(days=1)}
        ]

        # This test will FAIL until we implement the service
        duplicates = await duplicate_service.detect_user_job_duplicates(
            test_user['user_id'],
            [job['job_id'] for job in test_jobs],
            existing_applications
        )

        assert len(duplicates) == 2, "Should detect 2 user-job duplicates"
        assert 'JOB_001' in duplicates, "Should detect JOB_001 as already applied"
        assert 'JOB_003' in duplicates, "Should detect JOB_003 as already applied"
        assert 'JOB_002' not in duplicates, "Should not detect JOB_002 as duplicate"

    @pytest.mark.asyncio
    async def test_time_based_duplicate_rules(self, duplicate_service, test_user):
        """
        Test time-based duplicate rules (same job within 7 days).

        Should prevent duplicate applications within specified time window.
        """
        job_id = 'JOB_001'

        # Mock recent application (within 7 days)
        recent_application = {
            'user_id': 1001,
            'job_id': job_id,
            'applied_at': datetime.now() - timedelta(days=3)
        }

        # This test will FAIL until we implement the service
        is_duplicate = await duplicate_service.is_time_based_duplicate(
            test_user['user_id'],
            job_id,
            time_window_days=7,
            existing_applications=[recent_application]
        )

        assert is_duplicate is True, "Should detect time-based duplicate within 7 days"

        # Test outside time window
        old_application = {
            'user_id': 1001,
            'job_id': job_id,
            'applied_at': datetime.now() - timedelta(days=10)
        }

        is_old_duplicate = await duplicate_service.is_time_based_duplicate(
            test_user['user_id'],
            job_id,
            time_window_days=7,
            existing_applications=[old_application]
        )

        assert is_old_duplicate is False, "Should not detect duplicate outside 7-day window"

    @pytest.mark.asyncio
    async def test_duplicate_resolution_strategies(self, duplicate_service, test_jobs):
        """
        Test duplicate resolution strategies.

        Should provide options for resolving duplicates (keep newest, merge, etc.).
        """
        duplicate_groups = [
            {
                'endcl_cd': 'COMPANY_001',
                'jobs': [test_jobs[0], test_jobs[1]]  # JOB_001 and JOB_002
            }
        ]

        # This test will FAIL until we implement the service

        # Test "keep_newest" strategy
        resolved = await duplicate_service.resolve_duplicates(
            duplicate_groups,
            strategy='keep_newest'
        )

        assert len(resolved) == 1, "Should resolve to single job per company"
        assert resolved[0]['job_id'] == 'JOB_002', "Should keep newest job (JOB_002)"

        # Test "keep_oldest" strategy
        resolved_oldest = await duplicate_service.resolve_duplicates(
            duplicate_groups,
            strategy='keep_oldest'
        )

        assert resolved_oldest[0]['job_id'] == 'JOB_001', "Should keep oldest job (JOB_001)"

        # Test "merge" strategy
        merged = await duplicate_service.resolve_duplicates(
            duplicate_groups,
            strategy='merge'
        )

        assert len(merged) == 1, "Should merge to single job"
        assert 'merged_from' in merged[0], "Should indicate merged job"


# ============================================================================
# DUPLICATE PREVENTION TESTS (RED PHASE)
# ============================================================================

class TestDuplicatePrevention:
    """Test duplicate prevention functionality."""

    @pytest.mark.asyncio
    async def test_prevent_user_job_duplicate_application(self, duplicate_service, test_user):
        """
        Test prevention of duplicate user-job applications.

        Should block duplicate applications and return clear error.
        """
        job_id = 'JOB_001'

        # Mock existing application
        existing_applications = [
            {'user_id': 1001, 'job_id': job_id, 'applied_at': datetime.now() - timedelta(days=2)}
        ]

        # This test will FAIL until we implement the service
        result = await duplicate_service.check_application_allowed(
            test_user['user_id'],
            job_id,
            existing_applications
        )

        assert result['allowed'] is False, "Should not allow duplicate application"
        assert 'reason' in result, "Should provide reason for rejection"
        assert 'duplicate' in result['reason'].lower(), "Reason should mention duplicate"
        assert 'previous_application_date' in result, "Should include previous application date"

    @pytest.mark.asyncio
    async def test_company_duplicate_time_window_enforcement(self, duplicate_service, test_user):
        """
        Test enforcement of company duplicate time windows.

        Should prevent applications to same company within time window.
        """
        company_cd = 'COMPANY_001'

        # Mock recent application to same company
        recent_company_application = {
            'user_id': 1001,
            'endcl_cd': company_cd,
            'applied_at': datetime.now() - timedelta(days=5)
        }

        # This test will FAIL until we implement the service
        result = await duplicate_service.check_company_application_allowed(
            test_user['user_id'],
            company_cd,
            time_window_days=14,  # 14-day exclusion window
            existing_applications=[recent_company_application]
        )

        assert result['allowed'] is False, "Should not allow application to same company within 14 days"
        assert result['reason'] == "Recent application to same company", "Should provide specific reason"
        assert result['retry_after_date'] is not None, "Should provide retry date"

    @pytest.mark.asyncio
    async def test_duplicate_job_creation_prevention(self, duplicate_service):
        """
        Test prevention of duplicate job creation.

        Should detect and prevent creation of duplicate job postings.
        """
        new_job = {
            'endcl_cd': 'COMPANY_001',
            'application_name': 'Software Engineer',
            'location_pref_cd': '13',
            'salary_min': 3000,
            'salary_max': 5000
        }

        # Mock existing similar job
        existing_jobs = [
            {
                'job_id': 'JOB_001',
                'endcl_cd': 'COMPANY_001',
                'application_name': 'Software Engineer',
                'location_pref_cd': '13',
                'salary_min': 3000,
                'salary_max': 5000,
                'created_at': datetime.now() - timedelta(days=2)
            }
        ]

        # This test will FAIL until we implement the service
        result = await duplicate_service.check_job_creation_allowed(new_job, existing_jobs)

        assert result['allowed'] is False, "Should not allow duplicate job creation"
        assert result['duplicate_job_id'] == 'JOB_001', "Should identify duplicate job"
        assert result['similarity_score'] > 0.8, "Should calculate high similarity score"


# ============================================================================
# EDGE CASES AND ERROR HANDLING (RED PHASE)
# ============================================================================

class TestDuplicateControlEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_input_handling(self, duplicate_service):
        """Test handling of empty inputs."""
        # This test will FAIL until we implement the service

        # Empty job list
        duplicates = await duplicate_service.detect_duplicate_jobs([])
        assert duplicates == {'by_company': [], 'by_content': []}, "Should handle empty job list"

        # Empty application list
        result = await duplicate_service.check_application_allowed(1001, 'JOB_001', [])
        assert result['allowed'] is True, "Should allow application when no existing applications"

    @pytest.mark.asyncio
    async def test_invalid_time_window_handling(self, duplicate_service, test_user):
        """Test handling of invalid time windows."""
        # This test will FAIL until we implement the service

        with pytest.raises(ValueError, match="Time window must be positive"):
            await duplicate_service.is_time_based_duplicate(
                test_user['user_id'],
                'JOB_001',
                time_window_days=-1,  # Invalid negative time window
                existing_applications=[]
            )

        with pytest.raises(ValueError, match="Time window must be positive"):
            await duplicate_service.is_time_based_duplicate(
                test_user['user_id'],
                'JOB_001',
                time_window_days=0,  # Invalid zero time window
                existing_applications=[]
            )

    @pytest.mark.asyncio
    async def test_database_error_handling(self, duplicate_service, mock_db_session):
        """Test database error handling."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # This test will FAIL until we implement the service
        with pytest.raises(Exception, match="Database connection failed"):
            await duplicate_service.get_user_applications(1001)


if __name__ == "__main__":
    # For manual testing
    pytest.main([__file__, "-v", "--tb=short"])