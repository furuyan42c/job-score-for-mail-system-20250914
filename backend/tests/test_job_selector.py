#!/usr/bin/env python3
"""
T024: Job Selection Logic Tests (RED Phase)
Tests for 6-section job selection (editorial_picks, top5, etc.)
"""

import pytest
from app.services.job_selector import JobSelectorService
from app.models.job import Job
from app.models.user import User


class TestJobSelector:
    """Test suite for job selection logic"""

    @pytest.fixture
    def selector_service(self):
        """Create job selector service"""
        return JobSelectorService()

    @pytest.fixture
    def sample_jobs(self):
        """Create sample jobs with varying scores"""
        jobs = []
        for i in range(50):
            jobs.append(Job(
                job_id=f"job_{i:03d}",
                title=f"Job Title {i}",
                company=f"Company {i}",
                fee=500 + (i * 10),
                application_clicks=i * 2,
                basic_score=50 + i,
                seo_score=40 + i,
                personalized_score=45 + i
            ))
        return jobs

    @pytest.fixture
    def sample_user(self):
        """Sample user for selection"""
        return User(
            user_id="test_user",
            preferences={"location": "tokyo"}
        )

    @pytest.mark.asyncio
    async def test_editorial_picks_selection(self, selector_service, sample_jobs, sample_user):
        """Test editorial picks selection (fee × clicks)"""
        editorial = await selector_service.select_editorial_picks(
            sample_jobs, sample_user
        )

        assert len(editorial) == 5
        # Should be sorted by fee × clicks
        for i in range(len(editorial) - 1):
            score_i = editorial[i].fee * editorial[i].application_clicks
            score_next = editorial[i + 1].fee * editorial[i + 1].application_clicks
            assert score_i >= score_next

    @pytest.mark.asyncio
    async def test_top5_selection(self, selector_service, sample_jobs, sample_user):
        """Test top 5 jobs selection"""
        top5 = await selector_service.select_top5(
            sample_jobs, sample_user
        )

        assert len(top5) == 5
        # Should be highest scoring jobs
        for i in range(len(top5) - 1):
            assert top5[i].basic_score >= top5[i + 1].basic_score

    @pytest.mark.asyncio
    async def test_six_sections_complete(self, selector_service, sample_jobs, sample_user):
        """Test all 6 sections are returned"""
        sections = await selector_service.select_all_sections(
            sample_jobs, sample_user
        )

        assert "editorial_picks" in sections
        assert "top5" in sections
        assert "recommended" in sections
        assert "new_arrivals" in sections
        assert "popular" in sections
        assert "personalized" in sections

        # Each section should have appropriate number of jobs
        assert len(sections["editorial_picks"]) == 5
        assert len(sections["top5"]) == 5

    @pytest.mark.asyncio
    async def test_no_duplicates_across_sections(self, selector_service, sample_jobs, sample_user):
        """Test that jobs don't appear in multiple sections"""
        sections = await selector_service.select_all_sections(
            sample_jobs, sample_user
        )

        all_job_ids = []
        for section_jobs in sections.values():
            all_job_ids.extend([job.job_id for job in section_jobs])

        # Check no duplicates
        assert len(all_job_ids) == len(set(all_job_ids))