"""
T024: 6-Section Selection Logic Test - RED PHASE

This test validates the core 6-section job selection logic that distributes
40 jobs across 6 email sections with specific criteria and priority rules.

Section Priority Rules:
1. Editorial Picks (注目求人) - High score recent jobs
2. High Salary (高時給のお仕事) - Above average salary
3. Experience Match (あなたの経験を活かせる求人) - Category preference match
4. Location Convenient (通勤便利な求人) - High location scores
5. Weekend/Short Time (週末・短時間OK) - Flexible working arrangements
6. Other Recommendations (その他のおすすめ) - Remaining high scores

Requirements:
- Total: Exactly 40 jobs distributed across 6 sections
- Section Sizes: 3-10 jobs per section
- Diversity: At least 3 different categories
- No Duplicates: Each job appears in only one section
- Score Thresholds: Each section must meet minimum score criteria
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from app.services.section_selection import SectionSelectionService, SectionConfig
from app.models.jobs import Job


# Test Configuration
SECTION_REQUIREMENTS = {
    'total_jobs': 40,
    'total_sections': 6,
    'min_jobs_per_section': 3,
    'max_jobs_per_section': 10,
    'min_categories_diversity': 3,
    'min_score_threshold': 50.0
}

EXPECTED_SECTIONS = [
    'editorial_picks',
    'high_salary',
    'experience_match',
    'location_convenient',
    'weekend_short',
    'other_recommendations'
]


@pytest.fixture
def sample_jobs():
    """Create sample job data for testing."""
    jobs = []

    # High score recent jobs for editorial picks
    for i in range(10):
        jobs.append({
            'job_id': f'editorial_{i}',
            'title': f'Editorial Job {i}',
            'company_name': f'Premium Company {i}',
            'score': 85.0 + i,
            'created_at': datetime.now() - timedelta(hours=i),
            'salary_min': 1500,
            'salary_max': 2000,
            'category': 1,
            'location_score': 70.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # High salary jobs
    for i in range(10):
        jobs.append({
            'job_id': f'high_salary_{i}',
            'title': f'High Salary Job {i}',
            'company_name': f'High Pay Company {i}',
            'score': 75.0 + i,
            'created_at': datetime.now() - timedelta(days=i+1),
            'salary_min': 1800 + i*50,
            'salary_max': 2200 + i*50,
            'category': 2,
            'location_score': 60.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Experience match jobs (category 3)
    for i in range(10):
        jobs.append({
            'job_id': f'exp_match_{i}',
            'title': f'Experience Match Job {i}',
            'company_name': f'Experience Company {i}',
            'score': 70.0 + i,
            'created_at': datetime.now() - timedelta(days=i+2),
            'salary_min': 1300,
            'salary_max': 1600,
            'category': 3,  # User preferred category
            'location_score': 80.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Location convenient jobs
    for i in range(10):
        jobs.append({
            'job_id': f'location_{i}',
            'title': f'Location Job {i}',
            'company_name': f'Nearby Company {i}',
            'score': 65.0 + i,
            'created_at': datetime.now() - timedelta(days=i+3),
            'salary_min': 1200,
            'salary_max': 1500,
            'category': 4,
            'location_score': 90.0 + i,  # High location scores
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Weekend/flexible jobs
    for i in range(10):
        jobs.append({
            'job_id': f'weekend_{i}',
            'title': f'Weekend Job {i}',
            'company_name': f'Flexible Company {i}',
            'score': 60.0 + i,
            'created_at': datetime.now() - timedelta(days=i+4),
            'salary_min': 1100,
            'salary_max': 1400,
            'category': 5,
            'location_score': 50.0,
            'working_hours_flexible': True,
            'weekend_available': True
        })

    # Other recommendation jobs
    for i in range(10):
        jobs.append({
            'job_id': f'other_{i}',
            'title': f'Other Job {i}',
            'company_name': f'General Company {i}',
            'score': 55.0 + i,
            'created_at': datetime.now() - timedelta(days=i+5),
            'salary_min': 1000,
            'salary_max': 1300,
            'category': 6,
            'location_score': 40.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    return jobs


@pytest.fixture
def user_preferences():
    """User preferences for testing."""
    return {
        'preferred_categories': [3],  # Category 3 for experience match
        'location_preference': 'central_tokyo',
        'salary_preference_min': 1200,
        'flexible_working_preferred': True
    }


@pytest.fixture
def section_service():
    """Section selection service instance."""
    return SectionSelectionService()


class TestSectionSelectionLogic:
    """Test core 6-section selection logic."""

    @pytest.mark.asyncio
    async def test_select_exactly_40_jobs_across_6_sections(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """
        Test that exactly 40 jobs are selected and distributed across 6 sections.

        This is the core requirement for T024.
        """
        # Execute section selection
        sections = await section_service.select_sections(
            jobs=sample_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Validate 6 sections exist
        assert len(sections) == SECTION_REQUIREMENTS['total_sections'], \
            f"Expected {SECTION_REQUIREMENTS['total_sections']} sections, got {len(sections)}"

        # Validate all expected sections are present
        for expected_section in EXPECTED_SECTIONS:
            assert expected_section in sections, f"Missing section: {expected_section}"

        # Validate total job count is exactly 40
        total_jobs = sum(len(section_jobs) for section_jobs in sections.values())
        assert total_jobs == SECTION_REQUIREMENTS['total_jobs'], \
            f"Expected {SECTION_REQUIREMENTS['total_jobs']} jobs, got {total_jobs}"

        # Validate each section has at least minimum jobs
        for section_name, section_jobs in sections.items():
            assert len(section_jobs) >= SECTION_REQUIREMENTS['min_jobs_per_section'], \
                f"Section {section_name} has {len(section_jobs)} jobs, minimum is {SECTION_REQUIREMENTS['min_jobs_per_section']}"

            assert len(section_jobs) <= SECTION_REQUIREMENTS['max_jobs_per_section'], \
                f"Section {section_name} has {len(section_jobs)} jobs, maximum is {SECTION_REQUIREMENTS['max_jobs_per_section']}"

    @pytest.mark.asyncio
    async def test_section_priority_rules_enforced(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """Test that section priority rules are properly enforced."""

        sections = await section_service.select_sections(
            jobs=sample_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Editorial picks should have highest scores and recent jobs
        editorial_jobs = sections['editorial_picks']
        for job in editorial_jobs:
            assert job['score'] >= 80.0, f"Editorial pick has low score: {job['score']}"

            job_age_hours = (datetime.now() - job['created_at']).total_seconds() / 3600
            assert job_age_hours <= 24, f"Editorial pick is too old: {job_age_hours} hours"

        # High salary jobs should have above-average salaries
        high_salary_jobs = sections['high_salary']
        avg_salary = sum(job['salary_min'] for job in sample_jobs) / len(sample_jobs)

        for job in high_salary_jobs:
            assert job['salary_min'] > avg_salary, \
                f"High salary job below average: {job['salary_min']} <= {avg_salary}"

        # Experience match should prioritize preferred categories
        exp_match_jobs = sections['experience_match']
        preferred_cats = user_preferences['preferred_categories']

        matching_count = sum(1 for job in exp_match_jobs if job['category'] in preferred_cats)
        match_ratio = matching_count / len(exp_match_jobs)
        assert match_ratio >= 0.7, f"Experience match ratio too low: {match_ratio}"

        # Location convenient should have high location scores
        location_jobs = sections['location_convenient']
        for job in location_jobs:
            assert job['location_score'] >= 80.0, \
                f"Location job has low location score: {job['location_score']}"

        # Weekend/short time should have flexible options
        weekend_jobs = sections['weekend_short']
        for job in weekend_jobs:
            assert job['working_hours_flexible'] or job['weekend_available'], \
                f"Weekend job lacks flexibility: {job['job_id']}"

    @pytest.mark.asyncio
    async def test_no_duplicate_jobs_across_sections(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """Test that no job appears in multiple sections."""

        sections = await section_service.select_sections(
            jobs=sample_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Collect all job IDs across sections
        all_job_ids = []
        for section_name, section_jobs in sections.items():
            section_job_ids = [job['job_id'] for job in section_jobs]
            all_job_ids.extend(section_job_ids)

        # Validate no duplicates
        unique_job_ids = set(all_job_ids)
        assert len(all_job_ids) == len(unique_job_ids), \
            f"Found duplicate jobs: {len(all_job_ids)} total vs {len(unique_job_ids)} unique"

    @pytest.mark.asyncio
    async def test_category_diversity_requirement(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """Test that category diversity requirements are met."""

        sections = await section_service.select_sections(
            jobs=sample_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Collect all categories
        all_categories = []
        for section_jobs in sections.values():
            categories = [job['category'] for job in section_jobs]
            all_categories.extend(categories)

        unique_categories = set(all_categories)
        assert len(unique_categories) >= SECTION_REQUIREMENTS['min_categories_diversity'], \
            f"Insufficient category diversity: {len(unique_categories)} < {SECTION_REQUIREMENTS['min_categories_diversity']}"

    @pytest.mark.asyncio
    async def test_score_threshold_requirements(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """Test that all selected jobs meet minimum score thresholds."""

        sections = await section_service.select_sections(
            jobs=sample_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Check all jobs meet minimum score
        for section_name, section_jobs in sections.items():
            for job in section_jobs:
                assert job['score'] >= SECTION_REQUIREMENTS['min_score_threshold'], \
                    f"Job {job['job_id']} in section {section_name} has low score: {job['score']}"

    @pytest.mark.asyncio
    async def test_section_configuration_validation(
        self,
        section_service,
        sample_jobs,
        user_preferences
    ):
        """Test that section configuration is properly validated."""

        # Test with invalid total jobs requirement
        with pytest.raises(ValueError, match="total_jobs_required must be positive"):
            await section_service.select_sections(
                jobs=sample_jobs,
                user_preferences=user_preferences,
                total_jobs_required=0
            )

        # Test with insufficient input jobs
        limited_jobs = sample_jobs[:20]  # Only 20 jobs available

        sections = await section_service.select_sections(
            jobs=limited_jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        # Should return available jobs, not fail
        total_returned = sum(len(section_jobs) for section_jobs in sections.values())
        assert total_returned <= 20, "Should not exceed available jobs"
        assert total_returned > 0, "Should return some jobs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])