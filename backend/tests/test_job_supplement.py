#!/usr/bin/env python3
"""
T026: Job Supplement Service Tests

Tests for the 40-item supplement logic that ensures
we always have enough jobs to send in emails.
"""
import pytest
from typing import List
from datetime import datetime

from unittest.mock import MagicMock
from app.services.job_supplement import JobSupplementService


class TestJobSupplementService:
    """Test suite for job supplement service."""

    @pytest.fixture
    def service(self):
        """Create job supplement service instance."""
        return JobSupplementService()

    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = MagicMock()
        user.user_id = "test_user_001"
        user.email = "test@example.com"
        user.preferences = {"location": "Tokyo", "job_type": "full-time"}
        return user

    @pytest.fixture
    def high_score_jobs(self):
        """Create high-scoring jobs."""
        jobs = []
        for i in range(15):
            job = MagicMock()
            job.job_id = f"high_{i:03d}"
            job.title = f"High Score Job {i}"
            job.company = f"Top Company {i}"
            job.basic_score = 90 - i  # 90, 89, 88, ...
            job.location = "Tokyo"
            job.created_at = datetime.now()
            jobs.append(job)
        return jobs

    @pytest.fixture
    def medium_score_jobs(self):
        """Create medium-scoring jobs."""
        jobs = []
        for i in range(20):
            job = MagicMock()
            job.job_id = f"medium_{i:03d}"
            job.title = f"Medium Score Job {i}"
            job.company = f"Average Company {i}"
            job.basic_score = 50 - i * 0.5  # 50, 49.5, 49, ...
            job.location = "Tokyo"
            job.created_at = datetime.now()
            jobs.append(job)
        return jobs

    @pytest.fixture
    def low_score_jobs(self):
        """Create low-scoring jobs."""
        jobs = []
        for i in range(30):
            job = MagicMock()
            job.job_id = f"low_{i:03d}"
            job.title = f"Low Score Job {i}"
            job.company = f"Regular Company {i}"
            job.basic_score = 30 - i * 0.3  # 30, 29.7, 29.4, ...
            job.location = "Tokyo"
            job.created_at = datetime.now()
            jobs.append(job)
        return jobs

    @pytest.mark.asyncio
    async def test_supplement_when_insufficient_jobs(self, service, sample_user, high_score_jobs):
        """Test that supplement adds jobs when there are fewer than 40 high-quality jobs."""
        # Only 15 high-score jobs available
        supplemented_jobs = await service.supplement_to_target(
            high_score_jobs,
            sample_user,
            target_count=40
        )

        # Should supplement to exactly 40 jobs
        assert len(supplemented_jobs) == 40

        # High-score jobs should be first
        for i in range(15):
            assert supplemented_jobs[i].job_id == f"high_{i:03d}"

    @pytest.mark.asyncio
    async def test_no_supplement_when_sufficient_jobs(self, service, sample_user):
        """Test that no supplement occurs when there are already 40+ jobs."""
        # Create exactly 40 jobs
        jobs = []
        for i in range(40):
            job = MagicMock()
            job.job_id = f"job_{i:03d}"
            job.basic_score = 80 - i
            jobs.append(job)

        supplemented_jobs = await service.supplement_to_target(
            jobs,
            sample_user,
            target_count=40
        )

        # Should return exactly the same 40 jobs
        assert len(supplemented_jobs) == 40
        assert all(j.job_id == f"job_{i:03d}" for i, j in enumerate(supplemented_jobs))

    @pytest.mark.asyncio
    async def test_supplement_with_pool(self, service, sample_user, high_score_jobs, medium_score_jobs):
        """Test supplement using a pool of additional jobs."""
        # 15 selected + 20 pool = 35 total available
        supplemented_jobs = await service.supplement_from_pool(
            selected_jobs=high_score_jobs,
            job_pool=medium_score_jobs,
            user=sample_user,
            target_count=40
        )

        # Should supplement to 40 (15 high + 20 medium + 5 from fallback)
        assert len(supplemented_jobs) == 40

        # First 15 should be high-score jobs
        for i in range(15):
            assert supplemented_jobs[i].job_id == f"high_{i:03d}"

        # Next 20 should be medium-score jobs
        for i in range(20):
            assert supplemented_jobs[15 + i].job_id == f"medium_{i:03d}"

    @pytest.mark.asyncio
    async def test_supplement_fallback_strategy(self, service, sample_user, high_score_jobs):
        """Test fallback strategy when not enough jobs in pool."""
        # Only 15 jobs available, need 40
        supplemented_jobs = await service.supplement_with_fallback(
            jobs=high_score_jobs,
            user=sample_user,
            target_count=40
        )

        # Should use fallback to reach 40
        assert len(supplemented_jobs) == 40

        # First 15 should be original jobs
        for i in range(15):
            assert supplemented_jobs[i].job_id == f"high_{i:03d}"

        # Remaining 25 should be fallback jobs
        for i in range(15, 40):
            assert supplemented_jobs[i].job_id.startswith("fallback_")

    @pytest.mark.asyncio
    async def test_maintain_score_ordering(self, service, sample_user, high_score_jobs, medium_score_jobs, low_score_jobs):
        """Test that supplement maintains score-based ordering."""
        all_jobs = high_score_jobs[:10] + medium_score_jobs[:10] + low_score_jobs[:10]

        supplemented_jobs = await service.supplement_to_target(
            all_jobs,
            sample_user,
            target_count=40
        )

        # Should have 40 jobs
        assert len(supplemented_jobs) == 40

        # Should be ordered by score (descending)
        for i in range(len(supplemented_jobs) - 1):
            current_score = getattr(supplemented_jobs[i], 'basic_score', 0)
            next_score = getattr(supplemented_jobs[i + 1], 'basic_score', 0)
            assert current_score >= next_score, f"Jobs not ordered by score at index {i}"

    @pytest.mark.asyncio
    async def test_supplement_respects_user_preferences(self, service):
        """Test that supplement considers user preferences."""
        # Create user with specific preferences
        user = MagicMock()
        user.user_id = "pref_user"
        user.preferences = {"location": "Osaka", "job_type": "part-time"}

        # Create jobs with different locations
        tokyo_jobs = []
        osaka_jobs = []

        for i in range(10):
            job = MagicMock()
            job.job_id = f"tokyo_{i:03d}"
            job.location = "Tokyo"
            job.basic_score = 70 + i
            tokyo_jobs.append(job)

            job = MagicMock()
            job.job_id = f"osaka_{i:03d}"
            job.location = "Osaka"
            job.basic_score = 60 + i
            osaka_jobs.append(job)

        all_jobs = tokyo_jobs[:5] + osaka_jobs[:5]

        supplemented_jobs = await service.supplement_with_preferences(
            jobs=all_jobs,
            user=user,
            target_count=40
        )

        # Should prioritize Osaka jobs despite lower scores
        assert len(supplemented_jobs) == 40
        osaka_count = sum(1 for j in supplemented_jobs[:10] if "osaka" in j.job_id)
        assert osaka_count >= 5, "Should prioritize user's preferred location"

    @pytest.mark.asyncio
    async def test_supplement_handles_empty_input(self, service, sample_user):
        """Test supplement when no jobs are provided."""
        supplemented_jobs = await service.supplement_to_target(
            [],
            sample_user,
            target_count=40
        )

        # Should generate 40 fallback jobs
        assert len(supplemented_jobs) == 40
        assert all(j.job_id.startswith("fallback_") for j in supplemented_jobs)

    @pytest.mark.asyncio
    async def test_supplement_configuration(self, service):
        """Test supplement service configuration."""
        # Check default configuration
        assert service.target_count == 40
        assert service.min_quality_threshold == 30.0
        assert service.fallback_enabled == True

        # Test configuration update
        service.update_config(
            target_count=50,
            min_quality_threshold=40.0,
            fallback_enabled=False
        )

        assert service.target_count == 50
        assert service.min_quality_threshold == 40.0
        assert service.fallback_enabled == False

    @pytest.mark.asyncio
    async def test_supplement_metrics(self, service, sample_user, high_score_jobs):
        """Test that supplement tracks metrics."""
        result = await service.supplement_with_metrics(
            jobs=high_score_jobs[:10],
            user=sample_user,
            target_count=40
        )

        # Check result structure
        assert "jobs" in result
        assert "metrics" in result

        # Check jobs
        assert len(result["jobs"]) == 40

        # Check metrics
        metrics = result["metrics"]
        assert metrics["original_count"] == 10
        assert metrics["supplemented_count"] == 30
        assert metrics["total_count"] == 40
        assert metrics["fallback_used"] == True
        assert "supplement_sources" in metrics