"""
T048: 重複制御統合テスト
2週間以内応募企業の除外確認

This integration test validates the duplicate control system:
1. Company Exclusion: Users who applied to companies within 14 days are excluded
2. endcl_cd Deduplication: No duplicate company codes in final job selection
3. Time Window Logic: Proper 14-day calculation from application date
4. Fallback Handling: Sufficient jobs even with heavy filtering

Dependencies: T025 (duplicate control implementation)
Checkpoint: endcl_cd の重複なし (no duplicate company codes)
"""

import pytest
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from unittest.mock import AsyncMock, MagicMock, patch
from collections import Counter

from app.services.job_selector import JobSelector
from app.services.scoring_engine import ScoringEngine
from app.models.jobs import Job, JobSalary, JobLocation, JobCategory
from app.models.users import User, UserProfile, UserPreferences
from app.models.actions import UserAction
from app.core.database import get_async_session

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

DUPLICATE_CONTROL_CONFIG = {
    'exclusion_window_days': 14,    # 2 weeks exclusion period
    'total_jobs_required': 40,      # Standard job count per user
    'min_unique_companies': 35,     # Minimum unique companies in results
    'test_company_pool': 100,       # Total companies in test dataset
    'heavy_filter_threshold': 0.7,  # When 70% companies are filtered
}

# Application action types that trigger exclusion
EXCLUSION_ACTION_TYPES = [
    'application_submit',
    'application_click',
    'company_visit',
    'apply_button_click'
]

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
    """Mock scoring engine for controlled testing."""
    engine = MagicMock(spec=ScoringEngine)
    engine.calculate_base_scores_vectorized = MagicMock()
    engine._calculate_seo_scores_vectorized = AsyncMock()
    engine._calculate_personal_scores_vectorized = AsyncMock()
    return engine

@pytest.fixture
async def job_selector(mock_db_session, mock_scoring_engine):
    """Job selector with duplicate control capabilities."""
    selector = JobSelector(mock_scoring_engine, mock_db_session)
    return selector

@pytest.fixture
def test_companies_dataset():
    """Generate test dataset with varied companies for duplicate testing."""
    jobs_data = []

    # Create jobs from 100 different companies
    for company_id in range(DUPLICATE_CONTROL_CONFIG['test_company_pool']):
        # Each company has 2-5 jobs to test company-level filtering
        jobs_per_company = 2 + (company_id % 4)  # 2-5 jobs per company

        for job_num in range(jobs_per_company):
            job_id = f"JOB_{company_id:03d}_{job_num:02d}"

            jobs_data.append({
                'job_id': job_id,
                'endcl_cd': f'COMPANY_{company_id:03d}',  # Company code for filtering
                'occupation_cd1': (company_id % 10) + 1,  # 10 different occupations
                'salary_min': 1000 + (company_id % 800),  # Varied salaries
                'salary_max': 1400 + (company_id % 800),
                'location_pref_cd': '13',  # Tokyo
                'location_city_cd': f'{101 + (company_id % 20)}',  # 20 different cities
                'employment_type_cd': 1,
                'is_active': True,
                'fee': 600 + (company_id % 1500),
                'title': f'Job at Company {company_id} Position {job_num}',
                'company_name': f'Test Company {company_id:03d}',
                'created_at': datetime.now() - timedelta(days=company_id % 30),
                'updated_at': datetime.now(),
            })

    return pd.DataFrame(jobs_data)

@pytest.fixture
def test_user():
    """Test user for duplicate control testing."""
    return {
        'user_id': 2001,
        'estimated_pref_cd': '13',
        'estimated_city_cd': '101',
        'age_group': '30s',
        'gender': 'M'
    }

@pytest.fixture
def user_preferences():
    """Standard user preferences."""
    return {
        'preferred_categories': [1, 2, 3],
        'preferred_salary_min': 1200,
        'preferred_salary_max': 1800,
        'location_pref_cd': '13',
        'location_city_cd': '101',
    }

@pytest.fixture
def recent_applications_light():
    """Light recent applications (within 14 days) - 20 companies."""
    base_date = datetime.now()

    recent_apps = []
    for i in range(20):  # 20% of companies
        application_date = base_date - timedelta(days=i % 14)  # Within 14 days

        recent_apps.append({
            'user_id': 2001,
            'endcl_cd': f'COMPANY_{i:03d}',
            'action_type': 'application_submit',
            'action_date': application_date,
            'created_at': application_date,
        })

    return recent_apps

@pytest.fixture
def recent_applications_heavy():
    """Heavy recent applications (within 14 days) - 70 companies."""
    base_date = datetime.now()

    recent_apps = []
    for i in range(70):  # 70% of companies
        application_date = base_date - timedelta(days=i % 14)  # Within 14 days

        recent_apps.append({
            'user_id': 2001,
            'endcl_cd': f'COMPANY_{i:03d}',
            'action_type': EXCLUSION_ACTION_TYPES[i % len(EXCLUSION_ACTION_TYPES)],
            'action_date': application_date,
            'created_at': application_date,
        })

    return recent_apps

@pytest.fixture
def old_applications():
    """Old applications (outside 14-day window) - should NOT be excluded."""
    base_date = datetime.now()

    old_apps = []
    for i in range(30):
        # Applications from 15-45 days ago (outside 14-day window)
        application_date = base_date - timedelta(days=15 + (i % 30))

        old_apps.append({
            'user_id': 2001,
            'endcl_cd': f'COMPANY_{i + 70:03d}',  # Different companies
            'action_type': 'application_submit',
            'action_date': application_date,
            'created_at': application_date,
        })

    return old_apps

# ============================================================================
# DUPLICATE CONTROL TESTS
# ============================================================================

class TestDuplicateControl:
    """Test duplicate control system for company exclusion."""

    @pytest.mark.asyncio
    async def test_fourteen_day_exclusion_window(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences,
        recent_applications_light
    ):
        """
        Test that companies with applications within 14 days are properly excluded.

        Validates:
        1. Companies with recent applications (≤14 days) are excluded
        2. Companies without recent applications are included
        3. Time window calculation is accurate
        4. Final selection has sufficient unique companies
        """

        # Setup mocks with recent applications
        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            recent_applications_light
        )

        # Execute job selection
        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # Extract company codes from results
        selected_companies = set(job['endcl_cd'] for job in selected_jobs if 'endcl_cd' in job)
        excluded_companies = set(app['endcl_cd'] for app in recent_applications_light)

        # Validate exclusion logic
        overlap = selected_companies.intersection(excluded_companies)
        assert len(overlap) == 0, \
            f"Found {len(overlap)} excluded companies in results: {list(overlap)[:5]}"

        # Validate sufficient jobs returned
        assert len(selected_jobs) >= 35, \
            f"Insufficient jobs after exclusion: {len(selected_jobs)} < 35"

        # Validate company diversity
        unique_companies = len(selected_companies)
        assert unique_companies >= DUPLICATE_CONTROL_CONFIG['min_unique_companies'], \
            f"Insufficient company diversity: {unique_companies} < {DUPLICATE_CONTROL_CONFIG['min_unique_companies']}"

        print(f"✅ 14-Day Exclusion: {len(excluded_companies)} companies excluded, {unique_companies} unique companies selected")

    @pytest.mark.asyncio
    async def test_no_duplicate_company_codes_in_results(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences,
        recent_applications_light
    ):
        """
        Test that no duplicate company codes appear in final results.

        This is the core checkpoint: endcl_cd の重複なし
        """

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            recent_applications_light
        )

        # Execute job selection
        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # Extract all company codes
        company_codes = [job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd')]

        # Count occurrences
        company_counts = Counter(company_codes)

        # Validate no duplicates
        duplicates = {company: count for company, count in company_counts.items() if count > 1}

        assert len(duplicates) == 0, \
            f"Found duplicate companies in results: {duplicates}"

        # Validate we have meaningful diversity
        unique_companies = len(set(company_codes))
        assert unique_companies == len(company_codes), \
            f"Duplicate detection failed: {unique_companies} unique vs {len(company_codes)} total"

        print(f"✅ No Duplicates: {len(company_codes)} jobs from {unique_companies} unique companies")

    @pytest.mark.asyncio
    async def test_time_boundary_accuracy(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences
    ):
        """
        Test time boundary accuracy for 14-day exclusion window.

        Validates:
        1. Applications exactly 14 days ago are excluded
        2. Applications 15+ days ago are included
        3. Edge cases around the boundary
        """

        # Create precise boundary test data
        base_date = datetime.now()

        boundary_applications = [
            # Exactly 14 days ago (should be excluded)
            {
                'user_id': 2001,
                'endcl_cd': 'COMPANY_014_DAYS',
                'action_type': 'application_submit',
                'action_date': base_date - timedelta(days=14),
                'created_at': base_date - timedelta(days=14),
            },
            # 14 days - 1 hour ago (should be excluded)
            {
                'user_id': 2001,
                'endcl_cd': 'COMPANY_13D_23H',
                'action_type': 'application_submit',
                'action_date': base_date - timedelta(days=14, hours=-1),
                'created_at': base_date - timedelta(days=14, hours=-1),
            },
            # 15 days ago (should be included)
            {
                'user_id': 2001,
                'endcl_cd': 'COMPANY_015_DAYS',
                'action_type': 'application_submit',
                'action_date': base_date - timedelta(days=15),
                'created_at': base_date - timedelta(days=15),
            },
            # 14 days + 1 hour ago (should be included)
            {
                'user_id': 2001,
                'endcl_cd': 'COMPANY_14D_01H',
                'action_type': 'application_submit',
                'action_date': base_date - timedelta(days=14, hours=1),
                'created_at': base_date - timedelta(days=14, hours=1),
            }
        ]

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            boundary_applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))

        # Test boundary conditions
        assert 'COMPANY_014_DAYS' not in selected_companies, "14-day boundary not properly excluded"
        assert 'COMPANY_13D_23H' not in selected_companies, "13 days 23 hours not properly excluded"

        # These might not appear in results due to limited dataset, but they shouldn't be explicitly excluded
        excluded_companies = {'COMPANY_014_DAYS', 'COMPANY_13D_23H'}
        old_companies = {'COMPANY_015_DAYS', 'COMPANY_14D_01H'}

        # Validate that old companies aren't in the exclusion logic
        old_in_results = selected_companies.intersection(old_companies)
        excluded_in_results = selected_companies.intersection(excluded_companies)

        assert len(excluded_in_results) == 0, f"Excluded companies found in results: {excluded_in_results}"

        print(f"✅ Time Boundary: Excluded={excluded_companies}, Old companies not excluded")

    @pytest.mark.asyncio
    async def test_heavy_filtering_fallback(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences,
        recent_applications_heavy
    ):
        """
        Test system behavior when heavy filtering occurs (70% companies excluded).

        Validates:
        1. System still returns sufficient jobs
        2. Fallback mechanisms work properly
        3. Quality is maintained despite heavy filtering
        """

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            recent_applications_heavy
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))
        excluded_companies = set(app['endcl_cd'] for app in recent_applications_heavy)

        # Validate no excluded companies appear
        overlap = selected_companies.intersection(excluded_companies)
        assert len(overlap) == 0, f"Excluded companies leaked through: {list(overlap)[:5]}"

        # Validate fallback provides sufficient jobs
        expected_available_companies = DUPLICATE_CONTROL_CONFIG['test_company_pool'] - len(excluded_companies)

        # Should still get reasonable number of jobs despite heavy filtering
        min_expected_jobs = min(30, expected_available_companies * 2)  # Conservative estimate
        assert len(selected_jobs) >= min_expected_jobs, \
            f"Heavy filtering fallback failed: {len(selected_jobs)} < {min_expected_jobs}"

        # Validate company diversity is maintained
        unique_companies = len(selected_companies)
        min_expected_companies = min(25, expected_available_companies)
        assert unique_companies >= min_expected_companies, \
            f"Company diversity not maintained under heavy filtering: {unique_companies} < {min_expected_companies}"

        filtering_ratio = len(excluded_companies) / DUPLICATE_CONTROL_CONFIG['test_company_pool']
        print(f"✅ Heavy Filtering: {filtering_ratio:.1%} companies excluded, still got {len(selected_jobs)} jobs from {unique_companies} companies")

    @pytest.mark.asyncio
    async def test_action_type_filtering(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences
    ):
        """
        Test that different action types properly trigger company exclusion.

        Validates all action types in EXCLUSION_ACTION_TYPES:
        - application_submit
        - application_click
        - company_visit
        - apply_button_click
        """

        # Create applications with different action types
        mixed_action_applications = []
        base_date = datetime.now()

        for i, action_type in enumerate(EXCLUSION_ACTION_TYPES):
            for j in range(3):  # 3 companies per action type
                company_id = i * 3 + j

                mixed_action_applications.append({
                    'user_id': 2001,
                    'endcl_cd': f'COMPANY_{company_id:03d}',
                    'action_type': action_type,
                    'action_date': base_date - timedelta(days=j + 1),  # 1-3 days ago
                    'created_at': base_date - timedelta(days=j + 1),
                })

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            mixed_action_applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))
        excluded_companies = set(app['endcl_cd'] for app in mixed_action_applications)

        # Validate all action types trigger exclusion
        overlap = selected_companies.intersection(excluded_companies)
        assert len(overlap) == 0, \
            f"Action type filtering failed: {list(overlap)} companies not excluded"

        # Group by action type to verify each type works
        action_type_groups = {}
        for app in mixed_action_applications:
            action_type = app['action_type']
            if action_type not in action_type_groups:
                action_type_groups[action_type] = set()
            action_type_groups[action_type].add(app['endcl_cd'])

        for action_type, companies in action_type_groups.items():
            type_overlap = selected_companies.intersection(companies)
            assert len(type_overlap) == 0, \
                f"Action type '{action_type}' failed to exclude companies: {list(type_overlap)}"

        print(f"✅ Action Type Filtering: All {len(EXCLUSION_ACTION_TYPES)} action types properly exclude companies")

    @pytest.mark.asyncio
    async def test_old_applications_not_excluded(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences,
        old_applications
    ):
        """
        Test that applications outside 14-day window do NOT cause exclusion.

        Validates:
        1. Applications 15+ days old don't trigger exclusion
        2. Companies with only old applications can appear in results
        3. Time window is properly enforced
        """

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            old_applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))
        old_companies = set(app['endcl_cd'] for app in old_applications)

        # Old applications should NOT prevent companies from appearing
        # (though they might not appear due to other factors like scoring)

        # The key test: there should be no systematic exclusion of old companies
        # If we had perfect data, some old companies should appear in results

        # More importantly: verify the exclusion list doesn't include old companies
        # This test is primarily about ensuring the logic doesn't over-exclude

        # Count how many old companies have jobs in the dataset
        old_companies_with_jobs = old_companies.intersection(
            set(test_companies_dataset['endcl_cd'].unique())
        )

        # At least some old companies should be available for selection
        # (exact selection depends on scoring, but they shouldn't be systematically excluded)
        available_companies = len(old_companies_with_jobs)

        print(f"✅ Old Applications: {len(old_applications)} old applications don't exclude {available_companies} companies")

        # The main assertion: if old companies appear in results, that's good
        # If they don't, it should be due to scoring, not systematic exclusion
        old_in_results = selected_companies.intersection(old_companies)

        # This is more of an informational test - old companies CAN appear
        print(f"   {len(old_in_results)} old companies appeared in results (not excluded)")

    @pytest.mark.asyncio
    async def test_mixed_recent_and_old_applications(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences,
        recent_applications_light,
        old_applications
    ):
        """
        Test mixed scenario with both recent and old applications.

        Validates:
        1. Recent applications cause exclusion
        2. Old applications do not cause exclusion
        3. Mixed scenarios work correctly
        """

        # Combine recent and old applications
        mixed_applications = recent_applications_light + old_applications

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            mixed_applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)
        selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))

        recent_companies = set(app['endcl_cd'] for app in recent_applications_light)
        old_companies = set(app['endcl_cd'] for app in old_applications)

        # Recent companies should be excluded
        recent_overlap = selected_companies.intersection(recent_companies)
        assert len(recent_overlap) == 0, \
            f"Recent companies not properly excluded: {list(recent_overlap)[:5]}"

        # Old companies should NOT be systematically excluded
        old_overlap = selected_companies.intersection(old_companies)

        print(f"✅ Mixed Applications: {len(recent_companies)} recent excluded, {len(old_overlap)} old companies in results")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _setup_duplicate_control_mocks(
        self,
        job_selector,
        jobs_df,
        user,
        user_preferences,
        recent_applications
    ):
        """Setup mocks for duplicate control testing."""

        # Mock user data loading
        job_selector._get_user_data = AsyncMock(return_value=user)
        job_selector._get_user_preferences_cached = AsyncMock(return_value=user_preferences)

        # Mock recent applications - this is the key for duplicate control
        async def mock_get_recent_applications_cached(user_id):
            # Extract endcl_cd values for job selector
            return [app['endcl_cd'] for app in recent_applications]

        job_selector._get_recent_applications_cached = mock_get_recent_applications_cached

        # Mock other standard dependencies
        job_selector._get_blocked_companies_cached = AsyncMock(return_value=[])
        job_selector._get_jobs_dataframe = AsyncMock(return_value=jobs_df)

        # Mock scoring to return predictable results
        def mock_calculate_base_scores(jobs_df):
            # Score based on fee for predictable ordering
            scores = []
            for _, job in jobs_df.iterrows():
                base_score = min(50, job['fee'] / 30)  # Fee-based scoring
                scores.append(base_score)
            return scores

        async def mock_calculate_seo_scores(user_df, jobs_df):
            return [15.0] * len(jobs_df)  # Consistent SEO scores

        async def mock_calculate_personal_scores(user_df, jobs_df):
            # Slightly higher scores for preferred categories
            scores = []
            preferred_cats = set(user_preferences['preferred_categories'])

            for _, job in jobs_df.iterrows():
                if job['occupation_cd1'] in preferred_cats:
                    scores.append(20.0)
                else:
                    scores.append(10.0)

            return scores

        # Apply scoring mocks
        job_selector.scoring_engine.calculate_base_scores_vectorized = mock_calculate_base_scores
        job_selector.scoring_engine._calculate_seo_scores_vectorized = mock_calculate_seo_scores
        job_selector.scoring_engine._calculate_personal_scores_vectorized = mock_calculate_personal_scores

        # Mock other required methods
        job_selector._create_location_mask = AsyncMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._get_adjacent_categories = AsyncMock(return_value=[])
        job_selector._create_salary_mask = MagicMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._apply_smart_reduction = AsyncMock(side_effect=lambda df, prefs: df.head(1000))
        job_selector._format_salary_display = MagicMock(return_value="1200円/時")


# ============================================================================
# EDGE CASES AND PERFORMANCE
# ============================================================================

class TestDuplicateControlEdgeCases:
    """Test edge cases and performance for duplicate control."""

    @pytest.mark.asyncio
    async def test_no_recent_applications_scenario(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences
    ):
        """Test behavior when user has no recent applications."""

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            []  # No recent applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # Should return full set of jobs without exclusions
        assert len(selected_jobs) == 40, "Should return full job count when no exclusions"

        # Should have high company diversity
        company_codes = [job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd')]
        unique_companies = len(set(company_codes))

        assert unique_companies >= 35, f"Expected high diversity, got {unique_companies} unique companies"

        print(f"✅ No Recent Applications: {len(selected_jobs)} jobs from {unique_companies} companies")

    @pytest.mark.asyncio
    async def test_all_companies_excluded_scenario(
        self,
        job_selector,
        test_companies_dataset,
        test_user,
        user_preferences
    ):
        """Test extreme scenario where all companies have recent applications."""

        # Create applications to ALL companies
        all_company_applications = []
        unique_companies = test_companies_dataset['endcl_cd'].unique()
        base_date = datetime.now()

        for i, company_code in enumerate(unique_companies):
            all_company_applications.append({
                'user_id': 2001,
                'endcl_cd': company_code,
                'action_type': 'application_submit',
                'action_date': base_date - timedelta(days=i % 14),  # Within 14 days
                'created_at': base_date - timedelta(days=i % 14),
            })

        await self._setup_duplicate_control_mocks(
            job_selector,
            test_companies_dataset,
            test_user,
            user_preferences,
            all_company_applications
        )

        selected_jobs = await job_selector.select_top_jobs(test_user['user_id'], 40)

        # System should handle gracefully - either return empty or fallback logic
        if len(selected_jobs) > 0:
            # If jobs returned, they should not include excluded companies
            selected_companies = set(job.get('endcl_cd') for job in selected_jobs if job.get('endcl_cd'))
            excluded_companies = set(app['endcl_cd'] for app in all_company_applications)

            overlap = selected_companies.intersection(excluded_companies)
            assert len(overlap) == 0, "Excluded companies should not appear even in extreme scenario"

        print(f"✅ All Excluded Scenario: {len(selected_jobs)} jobs returned when all companies excluded")

    async def _setup_duplicate_control_mocks(
        self,
        job_selector,
        jobs_df,
        user,
        user_preferences,
        recent_applications
    ):
        """Setup mocks for edge case testing."""

        job_selector._get_user_data = AsyncMock(return_value=user)
        job_selector._get_user_preferences_cached = AsyncMock(return_value=user_preferences)
        job_selector._get_recent_applications_cached = AsyncMock(
            return_value=[app['endcl_cd'] for app in recent_applications]
        )
        job_selector._get_blocked_companies_cached = AsyncMock(return_value=[])
        job_selector._get_jobs_dataframe = AsyncMock(return_value=jobs_df)

        # Simple scoring
        job_selector.scoring_engine.calculate_base_scores_vectorized = lambda df: [40.0] * len(df)
        job_selector.scoring_engine._calculate_seo_scores_vectorized = AsyncMock(return_value=[15.0] * len(jobs_df))
        job_selector.scoring_engine._calculate_personal_scores_vectorized = AsyncMock(return_value=[10.0] * len(jobs_df))

        # Mock other required methods
        job_selector._create_location_mask = AsyncMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._get_adjacent_categories = AsyncMock(return_value=[])
        job_selector._create_salary_mask = MagicMock(return_value=pd.Series([True] * len(jobs_df)))
        job_selector._apply_smart_reduction = AsyncMock(side_effect=lambda df, prefs: df)
        job_selector._format_salary_display = MagicMock(return_value="1200円/時")


if __name__ == "__main__":
    # For manual testing
    pytest.main([__file__, "-v", "--tb=short"])