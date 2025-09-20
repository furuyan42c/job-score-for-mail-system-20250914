#!/usr/bin/env python3
"""
T025: Duplicate Control Tests (RED Phase)
Tests for excluding companies applied to within 2 weeks
"""

import pytest
from datetime import datetime, timedelta
from app.services.duplicate_control import DuplicateControlService
from app.models.job import Job
from app.models.user import User


class TestDuplicateControl:
    """Test suite for duplicate control service"""

    @pytest.fixture
    def control_service(self):
        """Create duplicate control service"""
        return DuplicateControlService()

    @pytest.fixture
    def user_applications(self):
        """Sample user application history"""
        now = datetime.now()
        return [
            {
                "company_id": "company_001",
                "applied_at": now - timedelta(days=5)  # 5 days ago
            },
            {
                "company_id": "company_002",
                "applied_at": now - timedelta(days=10)  # 10 days ago
            },
            {
                "company_id": "company_003",
                "applied_at": now - timedelta(days=20)  # 20 days ago (outside 2 weeks)
            }
        ]

    @pytest.fixture
    def sample_jobs(self):
        """Sample jobs from different companies"""
        return [
            Job(job_id="job_001", company="company_001", company_id="company_001"),
            Job(job_id="job_002", company="company_002", company_id="company_002"),
            Job(job_id="job_003", company="company_003", company_id="company_003"),
            Job(job_id="job_004", company="company_004", company_id="company_004"),
        ]

    @pytest.mark.asyncio
    async def test_exclude_recent_applications(
        self, control_service, sample_jobs, user_applications
    ):
        """Test exclusion of companies applied to within 2 weeks"""
        filtered_jobs = await control_service.filter_duplicates(
            sample_jobs,
            user_applications
        )

        # company_001 and company_002 should be excluded (within 2 weeks)
        # company_003 and company_004 should be included
        job_ids = [job.job_id for job in filtered_jobs]

        assert "job_001" not in job_ids  # Applied 5 days ago
        assert "job_002" not in job_ids  # Applied 10 days ago
        assert "job_003" in job_ids  # Applied 20 days ago (outside window)
        assert "job_004" in job_ids  # Never applied

    @pytest.mark.asyncio
    async def test_two_week_window(self, control_service):
        """Test exact 2-week (14 days) window"""
        now = datetime.now()

        # Job applied exactly 14 days ago
        applications = [{
            "company_id": "company_001",
            "applied_at": now - timedelta(days=14, hours=0, minutes=1)  # Just over 14 days
        }]

        jobs = [Job(job_id="job_001", company_id="company_001")]

        filtered = await control_service.filter_duplicates(jobs, applications)

        # Should be included (outside 14-day window)
        assert len(filtered) == 1

        # Job applied exactly within 14 days
        applications[0]["applied_at"] = now - timedelta(days=13, hours=23, minutes=59)
        filtered = await control_service.filter_duplicates(jobs, applications)

        # Should be excluded (within 14-day window)
        assert len(filtered) == 0

    @pytest.mark.asyncio
    async def test_no_application_history(self, control_service, sample_jobs):
        """Test behavior when user has no application history"""
        filtered = await control_service.filter_duplicates(
            sample_jobs,
            []  # No application history
        )

        # All jobs should be included
        assert len(filtered) == len(sample_jobs)

    @pytest.mark.asyncio
    async def test_batch_filtering_performance(self, control_service):
        """Test performance with large number of jobs"""
        # Create 1000 jobs
        jobs = [
            Job(job_id=f"job_{i:04d}", company_id=f"company_{i % 100:03d}")
            for i in range(1000)
        ]

        # Create application history for 50 companies
        now = datetime.now()
        applications = [
            {
                "company_id": f"company_{i:03d}",
                "applied_at": now - timedelta(days=i % 14)
            }
            for i in range(50)
        ]

        filtered = await control_service.filter_duplicates(jobs, applications)

        # Should complete within reasonable time
        assert len(filtered) < len(jobs)
        assert len(filtered) > 0