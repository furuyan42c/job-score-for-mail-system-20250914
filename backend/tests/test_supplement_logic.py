#!/usr/bin/env python3
"""
T026 TDD Implementation: 40-item Supplement Logic
RED PHASE: Create failing tests for supplement logic
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock
from typing import List, Any

# Add the parent directory to path to import our service
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supplement_logic import MinimalJobSupplementService

class MockJob:
    def __init__(self, job_id: str, score: float, location: str = "Tokyo"):
        self.job_id = job_id
        self.basic_score = score
        self.location = location
        self.title = f"Job {job_id}"
        self.company = f"Company {job_id}"

class MockUser:
    def __init__(self, user_id: str, preferences: dict = None):
        self.user_id = user_id
        self.preferences = preferences or {}

class TestSupplementLogicTDD:
    """TDD tests for 40-item supplement logic."""

    @pytest.fixture
    def service(self):
        return MinimalJobSupplementService()

    @pytest.fixture
    def sample_user(self):
        return MockUser("user_001", {"location": "Tokyo"})

    @pytest.mark.asyncio
    async def test_ensures_minimum_40_items_when_insufficient(self, service, sample_user):
        """GREEN: Test that supplement ensures minimum 40 items when fewer are provided."""
        # Arrange: Only 10 high-quality jobs
        jobs = [MockJob(f"job_{i}", 90 - i) for i in range(10)]

        # Act
        result = await service.ensure_minimum_items(jobs, sample_user, 40)

        # Assert
        assert len(result) == 40
        # First 10 should be original jobs (highest scores first due to sorting)
        original_job_ids = {f"job_{i}" for i in range(10)}
        result_original = [job for job in result if job.job_id in original_job_ids]
        assert len(result_original) == 10

    @pytest.mark.asyncio
    async def test_fallback_selection_when_not_enough_matches(self, service, sample_user):
        """GREEN: Test fallback when not enough high-score matches available."""
        # Arrange: Very few jobs
        jobs = [MockJob(f"job_{i}", 85) for i in range(5)]

        # Act
        result = await service.ensure_minimum_items(jobs, sample_user, 40)

        # Assert
        assert len(result) == 40
        # Should have 5 original + 35 fallback jobs
        fallback_jobs = [job for job in result if job.job_id.startswith("fallback_")]
        assert len(fallback_jobs) == 35

    @pytest.mark.asyncio
    async def test_priority_ordering_for_supplementation(self, service, sample_user):
        """GREEN: Test that supplement maintains priority order."""
        # Arrange: Mixed score jobs
        jobs = [
            MockJob("high_1", 90),
            MockJob("low_1", 30),
            MockJob("medium_1", 60),
        ]

        # Act
        result = await service.ensure_minimum_items(jobs, sample_user, 40)

        # Assert
        assert len(result) == 40
        # Check that higher score jobs come first
        assert result[0].job_id == "high_1"  # Highest score should be first
        # Verify descending score order for original jobs
        original_jobs = [job for job in result if job.job_id in ["high_1", "low_1", "medium_1"]]
        scores = [job.basic_score for job in original_jobs]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_avoids_already_selected_items(self, service, sample_user):
        """GREEN: Test that supplement doesn't duplicate already selected items."""
        # Arrange: Some pre-selected jobs
        jobs = [MockJob(f"selected_{i}", 80) for i in range(15)]

        # Act
        result = await service.ensure_minimum_items(jobs, sample_user, 40)

        # Assert
        assert len(result) == 40
        # Check no duplicates by job_id
        job_ids = [job.job_id for job in result]
        assert len(job_ids) == len(set(job_ids)), "Found duplicate job IDs"
        # Original jobs should all be present
        original_ids = {f"selected_{i}" for i in range(15)}
        result_original_ids = {job.job_id for job in result if job.job_id in original_ids}
        assert len(result_original_ids) == 15

    @pytest.mark.asyncio
    async def test_no_supplement_when_already_sufficient(self, service, sample_user):
        """GREEN: Test no supplement when already 40+ items."""
        # Arrange: Already 50 jobs
        jobs = [MockJob(f"job_{i}", 70) for i in range(50)]

        # Act
        result = await service.ensure_minimum_items(jobs, sample_user, 40)

        # Assert
        assert len(result) == 40  # Should return exactly 40
        # Should be the highest scoring 40 jobs
        result_ids = {job.job_id for job in result}
        # All should be original jobs (no fallback)
        assert all(not job_id.startswith("fallback_") for job_id in result_ids)

if __name__ == "__main__":
    # Run the failing tests for RED phase verification
    print("Running TDD RED phase tests...")
    pytest.main([__file__, "-v"])