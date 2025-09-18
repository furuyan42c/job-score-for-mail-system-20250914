"""
T047: 6セクション選定統合テスト
各セクションの正確な選定確認

This integration test validates the 6-section email job selection:
1. Editorial Picks (注目求人)
2. High Salary (高時給のお仕事)
3. Experience Match (あなたの経験を活かせる求人)
4. Location Convenient (通勤便利な求人)
5. Weekend/Short Time (週末・短時間OK)
6. Other Recommendations (その他のおすすめ)

Dependencies: T024 (6-section logic), T025 (duplicate control), T026 (40-job supplement)
Checkpoint: Accurate distribution of 40 jobs across 6 sections
"""

import pytest
import asyncio
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from collections import Counter, defaultdict

from app.services.job_selector import JobSelector, FINAL_SELECTION_LIMIT, MAX_JOBS_PER_CATEGORY, MIN_CATEGORIES_DIVERSITY
from app.services.scoring_engine import ScoringEngine
from app.models.jobs import Job, JobSalary, JobLocation, JobCategory, JobFeatures
from app.models.users import User, UserProfile, UserPreferences
from app.core.database import get_async_session

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

SECTION_SELECTION_CONFIG = {
    'total_jobs_required': 40,  # As per specification
    'sections_required': 6,     # As per T031 email template
    'max_jobs_per_section': 10, # Distribution limit
    'min_jobs_per_section': 3,  # Minimum for meaningful section
    'category_diversity_min': 3, # Minimum categories required
}

EMAIL_SECTIONS = {
    'editorial_picks': {
        'name': '今週の注目求人',
        'criteria': 'high_score_recent',
        'target_count': 8,
        'priority': 1
    },
    'high_salary': {
        'name': '高時給のお仕事',
        'criteria': 'salary_above_average',
        'target_count': 7,
        'priority': 2
    },
    'experience_match': {
        'name': 'あなたの経験を活かせる求人',
        'criteria': 'category_preference_match',
        'target_count': 7,
        'priority': 3
    },
    'location_convenient': {
        'name': '通勤便利な求人',
        'criteria': 'location_score_high',
        'target_count': 6,
        'priority': 4
    },
    'weekend_short': {
        'name': '週末・短時間OK',
        'criteria': 'flexible_working_time',
        'target_count': 6,
        'priority': 5
    },
    'other_recommendations': {
        'name': 'その他のおすすめ',
        'criteria': 'remaining_high_scores',
        'target_count': 6,
        'priority': 6
    }
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock()
    return session

@pytest.fixture
def mock_scoring_engine():
    """Mock scoring engine for controlled scoring results."""
    engine = MagicMock(spec=ScoringEngine)
    engine.calculate_base_scores_vectorized = MagicMock()
    engine._calculate_seo_scores_vectorized = AsyncMock()
    engine._calculate_personal_scores_vectorized = AsyncMock()
    return engine

@pytest.fixture
async def job_selector(mock_db_session, mock_scoring_engine):
    """Job selector instance with mocked dependencies."""
    selector = JobSelector(mock_scoring_engine, mock_db_session)
    return selector

@pytest.fixture
def diverse_jobs_dataset():
    """Create diverse job dataset for section testing."""
    jobs_data = []

    # High salary jobs (above average 1300/hour)
    for i in range(15):
        jobs_data.append({
            'job_id': f'HIGH_SALARY_{i:03d}',
            'endcl_cd': f'COMPANY_HIGH_{i:03d}',
            'occupation_cd1': i % 5 + 1,  # 5 different categories
            'salary_min': 1500 + (i * 50),  # High salaries 1500-2200
            'salary_max': 2000 + (i * 50),
            'location_pref_cd': '13',  # Tokyo
            'location_city_cd': f'{101 + (i % 5)}',
            'employment_type_cd': 1,  # Part-time
            'is_active': True,
            'fee': 1500 + (i * 100),
            'title': f'High Salary Job {i}',
            'company_name': f'High Pay Company {i}',
            'created_at': datetime.now() - timedelta(days=i),
            'working_hours_flexible': i % 3 == 0,  # Some flexible
            'weekend_available': i % 4 == 0,  # Some weekend
        })

    # Experience match jobs (specific categories)
    for i in range(12):
        jobs_data.append({
            'job_id': f'EXP_MATCH_{i:03d}',
            'endcl_cd': f'COMPANY_EXP_{i:03d}',
            'occupation_cd1': 2,  # Specific category for user preference
            'salary_min': 1200 + (i * 30),
            'salary_max': 1500 + (i * 30),
            'location_pref_cd': '13',
            'location_city_cd': '101',  # Central location
            'employment_type_cd': 1,
            'is_active': True,
            'fee': 1000 + (i * 50),
            'title': f'Experience Match Job {i}',
            'company_name': f'Experience Company {i}',
            'created_at': datetime.now() - timedelta(days=i),
            'working_hours_flexible': False,
            'weekend_available': False,
        })

    # Location convenient jobs (high location scores)
    for i in range(10):
        jobs_data.append({
            'job_id': f'LOCATION_CONV_{i:03d}',
            'endcl_cd': f'COMPANY_LOC_{i:03d}',
            'occupation_cd1': i % 3 + 3,  # Different categories
            'salary_min': 1100 + (i * 20),
            'salary_max': 1400 + (i * 20),
            'location_pref_cd': '13',
            'location_city_cd': '101',  # Same as user preference
            'employment_type_cd': 1,
            'is_active': True,
            'fee': 800 + (i * 30),
            'title': f'Location Convenient Job {i}',
            'company_name': f'Nearby Company {i}',
            'created_at': datetime.now() - timedelta(days=i + 5),
            'working_hours_flexible': False,
            'weekend_available': False,
        })

    # Weekend/Short time jobs
    for i in range(8):
        jobs_data.append({
            'job_id': f'WEEKEND_SHORT_{i:03d}',
            'endcl_cd': f'COMPANY_FLEX_{i:03d}',
            'occupation_cd1': i % 4 + 1,
            'salary_min': 1000 + (i * 25),
            'salary_max': 1300 + (i * 25),
            'location_pref_cd': '13',
            'location_city_cd': f'{102 + (i % 3)}',
            'employment_type_cd': 1,
            'is_active': True,
            'fee': 700 + (i * 40),
            'title': f'Weekend/Short Job {i}',
            'company_name': f'Flexible Company {i}',
            'created_at': datetime.now() - timedelta(days=i + 10),
            'working_hours_flexible': True,
            'weekend_available': True,
        })

    # Editorial picks (recent high-quality jobs)
    for i in range(10):
        jobs_data.append({
            'job_id': f'EDITORIAL_{i:03d}',
            'endcl_cd': f'COMPANY_EDIT_{i:03d}',
            'occupation_cd1': i % 6 + 1,
            'salary_min': 1300 + (i * 40),
            'salary_max': 1600 + (i * 40),
            'location_pref_cd': '13',
            'location_city_cd': f'{101 + (i % 4)}',
            'employment_type_cd': 1,
            'is_active': True,
            'fee': 1200 + (i * 80),
            'title': f'Editorial Pick Job {i}',
            'company_name': f'Premium Company {i}',
            'created_at': datetime.now() - timedelta(hours=i * 2),  # Very recent
            'working_hours_flexible': i % 2 == 0,
            'weekend_available': i % 3 == 0,
        })

    # Other recommendations (filler jobs)
    for i in range(15):
        jobs_data.append({
            'job_id': f'OTHER_RECOM_{i:03d}',
            'endcl_cd': f'COMPANY_OTHER_{i:03d}',
            'occupation_cd1': i % 8 + 1,  # Wide variety
            'salary_min': 1000 + (i * 15),
            'salary_max': 1250 + (i * 15),
            'location_pref_cd': '13',
            'location_city_cd': f'{103 + (i % 6)}',
            'employment_type_cd': 1,
            'is_active': True,
            'fee': 600 + (i * 25),
            'title': f'Other Recommendation {i}',
            'company_name': f'General Company {i}',
            'created_at': datetime.now() - timedelta(days=i + 15),
            'working_hours_flexible': i % 5 == 0,
            'weekend_available': i % 6 == 0,
        })

    return pd.DataFrame(jobs_data)

@pytest.fixture
def test_user():
    """Test user with specific preferences for section testing."""
    user = {
        'user_id': 1001,
        'estimated_pref_cd': '13',  # Tokyo
        'estimated_city_cd': '101', # Central Tokyo
        'age_group': '20s',
        'gender': 'F'
    }
    return user

@pytest.fixture
def user_preferences():
    """User preferences aligned with test data."""
    return {
        'preferred_categories': [2, 3],  # Specific categories for experience match
        'preferred_salary_min': 1200,
        'preferred_salary_max': 2000,
        'location_pref_cd': '13',
        'location_city_cd': '101',
        'working_hours_flexible_preferred': True,
        'weekend_work_acceptable': True,
    }

# ============================================================================
# SECTION SELECTION TESTS
# ============================================================================

class TestSectionSelection:
    """Test 6-section job selection logic."""

    @pytest.mark.asyncio
    async def test_six_section_distribution_accuracy(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """
        Test accurate distribution of 40 jobs across 6 sections.

        Validates:
        1. Total job count = 40
        2. All 6 sections have jobs
        3. Section criteria are met
        4. No duplicate jobs across sections
        5. Category diversity maintained
        """
        # Setup mocks
        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        # Execute job selection
        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # Validate total count
        assert len(selected_jobs) == SECTION_SELECTION_CONFIG['total_jobs_required'], \
            f"Expected {SECTION_SELECTION_CONFIG['total_jobs_required']} jobs, got {len(selected_jobs)}"

        # Distribute jobs into sections based on criteria
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        # Validate section distribution
        await self._validate_section_distribution(sections)

        # Validate no duplicates
        await self._validate_no_duplicate_jobs(sections)

        # Validate category diversity
        await self._validate_category_diversity(selected_jobs)

        print("✅ 6-Section Distribution Test Passed")
        self._print_section_summary(sections)

    @pytest.mark.asyncio
    async def test_editorial_picks_section_criteria(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test editorial picks section meets high-score recent criteria."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        editorial_jobs = sections['editorial_picks']

        # Validate criteria: high scores and recent
        for job in editorial_jobs:
            # Should be in top score range
            assert job['score'] >= 75.0, f"Editorial pick has low score: {job['score']}"

            # Should be recent (created within last week)
            job_age = (datetime.now() - datetime.fromisoformat(job.get('created_at', datetime.now().isoformat()))).days
            assert job_age <= 7, f"Editorial pick is too old: {job_age} days"

        print(f"✅ Editorial Picks: {len(editorial_jobs)} jobs meet criteria")

    @pytest.mark.asyncio
    async def test_high_salary_section_criteria(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test high salary section meets salary threshold criteria."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        high_salary_jobs = sections['high_salary']

        # Calculate average salary from all jobs
        all_salaries = [job.get('salary_min', 1000) for job in selected_jobs]
        avg_salary = sum(all_salaries) / len(all_salaries)

        # Validate criteria: above average salary
        for job in high_salary_jobs:
            job_salary = job.get('salary_min', 0)
            assert job_salary > avg_salary, \
                f"High salary job below average: {job_salary} <= {avg_salary:.0f}"

        print(f"✅ High Salary: {len(high_salary_jobs)} jobs above {avg_salary:.0f}円/時")

    @pytest.mark.asyncio
    async def test_experience_match_section_criteria(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test experience match section prioritizes user's preferred categories."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        experience_jobs = sections['experience_match']
        preferred_categories = set(user_preferences['preferred_categories'])

        # Validate criteria: most jobs should match preferred categories
        matching_categories = 0
        for job in experience_jobs:
            if job.get('category') in preferred_categories:
                matching_categories += 1

        match_ratio = matching_categories / len(experience_jobs)
        assert match_ratio >= 0.6, \
            f"Experience match section has low category match: {match_ratio:.1%}"

        print(f"✅ Experience Match: {matching_categories}/{len(experience_jobs)} jobs match preferred categories")

    @pytest.mark.asyncio
    async def test_location_convenient_section_criteria(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test location convenient section prioritizes nearby jobs."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        location_jobs = sections['location_convenient']
        user_city = user_preferences['location_city_cd']

        # Validate criteria: jobs should be in same or nearby locations
        nearby_jobs = 0
        for job in location_jobs:
            job_city = job.get('location_city_cd', '')
            # Same city or adjacent (101-105 range for test data)
            if job_city == user_city or abs(int(job_city) - int(user_city)) <= 2:
                nearby_jobs += 1

        proximity_ratio = nearby_jobs / len(location_jobs)
        assert proximity_ratio >= 0.7, \
            f"Location convenient section has low proximity: {proximity_ratio:.1%}"

        print(f"✅ Location Convenient: {nearby_jobs}/{len(location_jobs)} jobs are nearby")

    @pytest.mark.asyncio
    async def test_weekend_short_section_criteria(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test weekend/short time section meets flexible working criteria."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        flexible_jobs = sections['weekend_short']

        # Validate criteria: jobs should offer flexible working arrangements
        flexible_count = 0
        for job in flexible_jobs:
            has_flexible_hours = job.get('working_hours_flexible', False)
            has_weekend_option = job.get('weekend_available', False)

            if has_flexible_hours or has_weekend_option:
                flexible_count += 1

        flexibility_ratio = flexible_count / len(flexible_jobs)
        assert flexibility_ratio >= 0.8, \
            f"Weekend/short section has low flexibility: {flexibility_ratio:.1%}"

        print(f"✅ Weekend/Short: {flexible_count}/{len(flexible_jobs)} jobs offer flexibility")

    @pytest.mark.asyncio
    async def test_section_size_balance(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test that sections are reasonably balanced in size."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        # Validate each section has reasonable number of jobs
        for section_name, jobs in sections.items():
            section_config = EMAIL_SECTIONS[section_name]
            expected_count = section_config['target_count']
            actual_count = len(jobs)

            # Allow ±2 jobs variance from target
            assert abs(actual_count - expected_count) <= 2, \
                f"Section {section_name} size imbalance: {actual_count} vs target {expected_count}"

            # No section should be empty
            assert actual_count > 0, f"Section {section_name} is empty"

        # Total should still be 40
        total_distributed = sum(len(jobs) for jobs in sections.values())
        assert total_distributed == 40, f"Total distributed jobs: {total_distributed} != 40"

        print("✅ Section Balance Test Passed")

    @pytest.mark.asyncio
    async def test_section_priority_ordering(
        self,
        job_selector,
        diverse_jobs_dataset,
        test_user,
        user_preferences
    ):
        """Test that higher priority sections get better jobs."""

        await self._setup_job_selector_mocks(
            job_selector,
            diverse_jobs_dataset,
            test_user,
            user_preferences
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        sections = await self._distribute_jobs_into_sections(selected_jobs, user_preferences)

        # Calculate average scores for each section
        section_avg_scores = {}
        for section_name, jobs in sections.items():
            if jobs:
                avg_score = sum(job['score'] for job in jobs) / len(jobs)
                section_avg_scores[section_name] = avg_score

        # Get section priorities
        section_priorities = {name: config['priority'] for name, config in EMAIL_SECTIONS.items()}

        # Validate that higher priority sections (lower number) have better average scores
        sorted_by_priority = sorted(section_priorities.items(), key=lambda x: x[1])

        for i in range(len(sorted_by_priority) - 1):
            current_section = sorted_by_priority[i][0]
            next_section = sorted_by_priority[i + 1][0]

            if current_section in section_avg_scores and next_section in section_avg_scores:
                current_avg = section_avg_scores[current_section]
                next_avg = section_avg_scores[next_section]

                # Allow some tolerance for priority ordering
                assert current_avg >= next_avg - 5.0, \
                    f"Priority violation: {current_section}({current_avg:.1f}) < {next_section}({next_avg:.1f})"

        print("✅ Section Priority Ordering Test Passed")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _setup_job_selector_mocks(
        self,
        job_selector,
        jobs_df,
        user,
        user_preferences
    ):
        """Setup mocks for job selector testing."""

        # Mock user data loading
        async def mock_get_user_data(user_id):
            return user

        # Mock user preferences
        async def mock_get_user_preferences_cached(user_id):
            return user_preferences

        # Mock recent applications (empty for testing)
        async def mock_get_recent_applications_cached(user_id):
            return []

        # Mock blocked companies (empty for testing)
        async def mock_get_blocked_companies_cached(user_id):
            return []

        # Mock jobs dataframe
        async def mock_get_jobs_dataframe():
            return jobs_df

        # Mock scoring results
        def mock_calculate_base_scores(jobs_df):
            # Return scores based on fee and salary
            scores = []
            for _, job in jobs_df.iterrows():
                base_score = min(50, job['fee'] / 50)  # Max 50 points from fee
                salary_score = min(30, (job['salary_min'] - 1000) / 20)  # Salary component
                scores.append(base_score + salary_score)
            return scores

        async def mock_calculate_seo_scores(user_df, jobs_df):
            # Return moderate SEO scores
            return [20.0] * len(jobs_df)

        async def mock_calculate_personal_scores(user_df, jobs_df):
            # Return personalized scores based on category match
            scores = []
            preferred_cats = set(user_preferences['preferred_categories'])

            for _, job in jobs_df.iterrows():
                if job['occupation_cd1'] in preferred_cats:
                    scores.append(25.0)  # High personal score for preferred categories
                else:
                    scores.append(15.0)  # Lower score for others

            return scores

        # Apply mocks
        job_selector._get_user_data = mock_get_user_data
        job_selector._get_user_preferences_cached = mock_get_user_preferences_cached
        job_selector._get_recent_applications_cached = mock_get_recent_applications_cached
        job_selector._get_blocked_companies_cached = mock_get_blocked_companies_cached
        job_selector._get_jobs_dataframe = mock_get_jobs_dataframe

        job_selector.scoring_engine.calculate_base_scores_vectorized = mock_calculate_base_scores
        job_selector.scoring_engine._calculate_seo_scores_vectorized = mock_calculate_seo_scores
        job_selector.scoring_engine._calculate_personal_scores_vectorized = mock_calculate_personal_scores

        # Mock additional methods that might be called
        job_selector._create_location_mask = AsyncMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._get_adjacent_categories = AsyncMock(return_value=[])
        job_selector._create_salary_mask = MagicMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._apply_smart_reduction = AsyncMock(side_effect=lambda df, prefs: df.head(2000))
        job_selector._format_salary_display = MagicMock(return_value="1200円/時")

    async def _distribute_jobs_into_sections(
        self,
        selected_jobs: List[Dict],
        user_preferences: Dict
    ) -> Dict[str, List[Dict]]:
        """Distribute jobs into 6 sections based on criteria."""

        sections = {section: [] for section in EMAIL_SECTIONS.keys()}
        remaining_jobs = selected_jobs.copy()

        # Sort jobs by score for priority allocation
        remaining_jobs.sort(key=lambda x: x['score'], reverse=True)

        # 1. Editorial Picks - highest scoring recent jobs
        for job in remaining_jobs[:]:
            if len(sections['editorial_picks']) >= EMAIL_SECTIONS['editorial_picks']['target_count']:
                break

            job_age = self._calculate_job_age_days(job)
            if job['score'] >= 75.0 and job_age <= 7:  # High score and recent
                sections['editorial_picks'].append(job)
                remaining_jobs.remove(job)

        # 2. High Salary - above average salary
        all_salaries = [job.get('salary_min', 1000) for job in selected_jobs]
        avg_salary = sum(all_salaries) / len(all_salaries)

        for job in remaining_jobs[:]:
            if len(sections['high_salary']) >= EMAIL_SECTIONS['high_salary']['target_count']:
                break

            if job.get('salary_min', 0) > avg_salary:
                sections['high_salary'].append(job)
                remaining_jobs.remove(job)

        # 3. Experience Match - preferred categories
        preferred_categories = set(user_preferences['preferred_categories'])

        for job in remaining_jobs[:]:
            if len(sections['experience_match']) >= EMAIL_SECTIONS['experience_match']['target_count']:
                break

            if job.get('category') in preferred_categories:
                sections['experience_match'].append(job)
                remaining_jobs.remove(job)

        # 4. Location Convenient - same/nearby city
        user_city = user_preferences['location_city_cd']

        for job in remaining_jobs[:]:
            if len(sections['location_convenient']) >= EMAIL_SECTIONS['location_convenient']['target_count']:
                break

            job_city = job.get('location_city_cd', '')
            if job_city == user_city or (job_city.isdigit() and abs(int(job_city) - int(user_city)) <= 2):
                sections['location_convenient'].append(job)
                remaining_jobs.remove(job)

        # 5. Weekend/Short - flexible working arrangements
        for job in remaining_jobs[:]:
            if len(sections['weekend_short']) >= EMAIL_SECTIONS['weekend_short']['target_count']:
                break

            if job.get('working_hours_flexible') or job.get('weekend_available'):
                sections['weekend_short'].append(job)
                remaining_jobs.remove(job)

        # 6. Other Recommendations - remaining jobs
        sections['other_recommendations'] = remaining_jobs[:EMAIL_SECTIONS['other_recommendations']['target_count']]

        return sections

    def _calculate_job_age_days(self, job: Dict) -> int:
        """Calculate job age in days."""
        try:
            created_at = datetime.fromisoformat(job.get('created_at', datetime.now().isoformat()))
            return (datetime.now() - created_at).days
        except:
            return 0

    async def _validate_section_distribution(self, sections: Dict[str, List[Dict]]):
        """Validate section distribution meets requirements."""

        # All sections should have jobs
        for section_name, jobs in sections.items():
            assert len(jobs) > 0, f"Section {section_name} is empty"

        # Total jobs should be 40
        total_jobs = sum(len(jobs) for jobs in sections.values())
        assert total_jobs == 40, f"Total jobs {total_jobs} != 40"

        # No section should exceed maximum
        for section_name, jobs in sections.items():
            max_allowed = SECTION_SELECTION_CONFIG['max_jobs_per_section']
            assert len(jobs) <= max_allowed, \
                f"Section {section_name} has {len(jobs)} jobs > max {max_allowed}"

    async def _validate_no_duplicate_jobs(self, sections: Dict[str, List[Dict]]):
        """Validate no job appears in multiple sections."""

        all_job_ids = []
        for section_name, jobs in sections.items():
            section_job_ids = [job['job_id'] for job in jobs]
            all_job_ids.extend(section_job_ids)

        unique_job_ids = set(all_job_ids)
        assert len(all_job_ids) == len(unique_job_ids), \
            f"Duplicate jobs found: {len(all_job_ids)} total vs {len(unique_job_ids)} unique"

    async def _validate_category_diversity(self, selected_jobs: List[Dict]):
        """Validate category diversity across selected jobs."""

        categories = [job.get('category') for job in selected_jobs if job.get('category')]
        unique_categories = set(categories)

        assert len(unique_categories) >= MIN_CATEGORIES_DIVERSITY, \
            f"Insufficient category diversity: {len(unique_categories)} < {MIN_CATEGORIES_DIVERSITY}"

        # No single category should dominate
        category_counts = Counter(categories)
        max_count = max(category_counts.values())
        assert max_count <= MAX_JOBS_PER_CATEGORY, \
            f"Category dominance: {max_count} jobs > max {MAX_JOBS_PER_CATEGORY}"

    def _print_section_summary(self, sections: Dict[str, List[Dict]]):
        """Print summary of section distribution."""

        print("\n📊 Section Distribution Summary:")
        print("=" * 50)

        for section_name, jobs in sections.items():
            section_config = EMAIL_SECTIONS[section_name]
            avg_score = sum(job['score'] for job in jobs) / len(jobs) if jobs else 0

            print(f"{section_config['name']}: {len(jobs)} jobs (平均スコア: {avg_score:.1f})")

            # Show top 2 jobs in each section
            for i, job in enumerate(jobs[:2]):
                print(f"  {i+1}. {job['title']} (Score: {job['score']:.1f})")

        print("=" * 50)


# ============================================================================
# PERFORMANCE AND EDGE CASES
# ============================================================================

class TestSectionSelectionEdgeCases:
    """Test edge cases and performance for section selection."""

    @pytest.mark.asyncio
    async def test_insufficient_jobs_for_all_sections(
        self,
        job_selector,
        test_user,
        user_preferences
    ):
        """Test behavior when insufficient jobs for all sections."""

        # Create minimal job dataset (only 20 jobs)
        minimal_jobs = pd.DataFrame([
            {
                'job_id': f'MINIMAL_{i:03d}',
                'endcl_cd': f'COMPANY_{i:03d}',
                'occupation_cd1': 1,
                'salary_min': 1200,
                'salary_max': 1500,
                'location_pref_cd': '13',
                'location_city_cd': '101',
                'employment_type_cd': 1,
                'is_active': True,
                'fee': 1000,
                'title': f'Minimal Job {i}',
                'company_name': f'Company {i}',
                'created_at': datetime.now().isoformat(),
                'working_hours_flexible': False,
                'weekend_available': False,
            }
            for i in range(20)
        ])

        await self._setup_minimal_mocks(job_selector, minimal_jobs, test_user, user_preferences)

        # Should still return available jobs, even if less than 40
        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        assert len(selected_jobs) <= 20, "Should not exceed available jobs"
        assert len(selected_jobs) > 0, "Should return some jobs"

        print(f"✅ Edge Case: Returned {len(selected_jobs)} jobs when only 20 available")

    @pytest.mark.asyncio
    async def test_single_category_dominance_prevention(
        self,
        job_selector,
        test_user,
        user_preferences
    ):
        """Test prevention of single category dominance."""

        # Create dataset with mostly one category
        dominant_category_jobs = pd.DataFrame([
            {
                'job_id': f'DOMINANT_{i:03d}',
                'endcl_cd': f'COMPANY_{i:03d}',
                'occupation_cd1': 1 if i < 35 else 2,  # 35 jobs in category 1, 5 in category 2
                'salary_min': 1200 + i,
                'salary_max': 1500 + i,
                'location_pref_cd': '13',
                'location_city_cd': '101',
                'employment_type_cd': 1,
                'is_active': True,
                'fee': 1000 + i * 10,
                'title': f'Dominant Job {i}',
                'company_name': f'Company {i}',
                'created_at': datetime.now().isoformat(),
                'working_hours_flexible': False,
                'weekend_available': False,
            }
            for i in range(40)
        ])

        await self._setup_minimal_mocks(job_selector, dominant_category_jobs, test_user, user_preferences)

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # Check category distribution
        categories = [job.get('category') for job in selected_jobs]
        category_counts = Counter(categories)

        # No single category should exceed the limit
        max_count = max(category_counts.values())
        assert max_count <= MAX_JOBS_PER_CATEGORY, \
            f"Category dominance not prevented: {max_count} > {MAX_JOBS_PER_CATEGORY}"

        print(f"✅ Category Dominance Prevention: Max category count {max_count}")

    async def _setup_minimal_mocks(self, job_selector, jobs_df, user, user_preferences):
        """Setup minimal mocks for edge case testing."""

        job_selector._get_user_data = AsyncMock(return_value=user)
        job_selector._get_user_preferences_cached = AsyncMock(return_value=user_preferences)
        job_selector._get_recent_applications_cached = AsyncMock(return_value=[])
        job_selector._get_blocked_companies_cached = AsyncMock(return_value=[])
        job_selector._get_jobs_dataframe = AsyncMock(return_value=jobs_df)

        # Simple scoring
        job_selector.scoring_engine.calculate_base_scores_vectorized = lambda df: [50.0] * len(df)
        job_selector.scoring_engine._calculate_seo_scores_vectorized = AsyncMock(return_value=[20.0] * len(jobs_df))
        job_selector.scoring_engine._calculate_personal_scores_vectorized = AsyncMock(return_value=[15.0] * len(jobs_df))

        # Mock other required methods
        job_selector._create_location_mask = AsyncMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._get_adjacent_categories = AsyncMock(return_value=[])
        job_selector._create_salary_mask = MagicMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._apply_smart_reduction = AsyncMock(side_effect=lambda df, prefs: df)
        job_selector._format_salary_display = MagicMock(return_value="1200円/時")


if __name__ == "__main__":
    # For manual testing
    pytest.main([__file__, "-v", "--tb=short"])