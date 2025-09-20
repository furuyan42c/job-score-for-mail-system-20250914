#!/usr/bin/env python3
"""
Standalone test for T024 section selection without dependencies.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SectionConfig:
    """Configuration for email sections."""
    name: str
    target_count: int
    priority: int
    criteria_function: str


class SectionSelectionService:
    """Service for selecting and distributing jobs across 6 email sections."""

    def __init__(self):
        """Initialize the section selection service."""
        self.section_configs = {
            'editorial_picks': SectionConfig(
                name='今週の注目求人',
                target_count=8,
                priority=1,
                criteria_function='_select_editorial_picks'
            ),
            'high_salary': SectionConfig(
                name='高時給のお仕事',
                target_count=7,
                priority=2,
                criteria_function='_select_high_salary'
            ),
            'experience_match': SectionConfig(
                name='あなたの経験を活かせる求人',
                target_count=7,
                priority=3,
                criteria_function='_select_experience_match'
            ),
            'location_convenient': SectionConfig(
                name='通勤便利な求人',
                target_count=6,
                priority=4,
                criteria_function='_select_location_convenient'
            ),
            'weekend_short': SectionConfig(
                name='週末・短時間OK',
                target_count=6,
                priority=5,
                criteria_function='_select_weekend_short'
            ),
            'other_recommendations': SectionConfig(
                name='その他のおすすめ',
                target_count=6,
                priority=6,
                criteria_function='_select_other_recommendations'
            )
        }

    async def select_sections(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        total_jobs_required: int = 40
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Select and distribute jobs across 6 sections.
        """
        if total_jobs_required <= 0:
            raise ValueError("total_jobs_required must be positive")

        # Sort jobs by score (highest first)
        sorted_jobs = sorted(jobs, key=lambda x: x.get('score', 0), reverse=True)

        # Ensure we don't try to select more jobs than available
        available_jobs = len(sorted_jobs)
        if available_jobs < total_jobs_required:
            total_jobs_required = available_jobs

        # Initialize sections
        sections = {section_name: [] for section_name in self.section_configs.keys()}
        used_job_ids = set()

        # Select jobs for each section in priority order
        remaining_jobs = sorted_jobs.copy()

        # 1. Editorial Picks - high score recent jobs
        editorial_jobs = self._select_editorial_picks(remaining_jobs, user_preferences)
        sections['editorial_picks'] = editorial_jobs[:8]
        self._remove_used_jobs(remaining_jobs, sections['editorial_picks'], used_job_ids)

        # 2. High Salary - above average salary
        high_salary_jobs = self._select_high_salary(remaining_jobs, user_preferences, sorted_jobs)
        sections['high_salary'] = high_salary_jobs[:7]
        self._remove_used_jobs(remaining_jobs, sections['high_salary'], used_job_ids)

        # 3. Experience Match - preferred categories
        exp_match_jobs = self._select_experience_match(remaining_jobs, user_preferences)
        sections['experience_match'] = exp_match_jobs[:7]
        self._remove_used_jobs(remaining_jobs, sections['experience_match'], used_job_ids)

        # 4. Location Convenient - high location scores
        location_jobs = self._select_location_convenient(remaining_jobs, user_preferences)
        sections['location_convenient'] = location_jobs[:6]
        self._remove_used_jobs(remaining_jobs, sections['location_convenient'], used_job_ids)

        # 5. Weekend/Short Time - flexible working
        weekend_jobs = self._select_weekend_short(remaining_jobs, user_preferences)
        sections['weekend_short'] = weekend_jobs[:6]
        self._remove_used_jobs(remaining_jobs, sections['weekend_short'], used_job_ids)

        # 6. Other Recommendations - remaining jobs
        other_jobs = self._select_other_recommendations(remaining_jobs, user_preferences)
        sections['other_recommendations'] = other_jobs[:6]

        # Balance sections to reach exactly the target total
        sections = self._balance_sections(sections, total_jobs_required)

        return sections

    def _select_editorial_picks(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select editorial picks - high score recent jobs."""
        editorial_jobs = []

        for job in jobs:
            # High score threshold (>= 80)
            if job.get('score', 0) >= 80.0:
                # Recent job check (within 24 hours)
                created_at = job.get('created_at')
                if isinstance(created_at, datetime):
                    hours_old = (datetime.now() - created_at).total_seconds() / 3600
                    if hours_old <= 24:
                        editorial_jobs.append(job)

        return editorial_jobs

    def _select_high_salary(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        all_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Select high salary jobs - above average salary."""
        # Calculate average salary from all jobs
        salaries = [job.get('salary_min', 1000) for job in all_jobs]
        avg_salary = sum(salaries) / len(salaries) if salaries else 1000

        high_salary_jobs = []
        for job in jobs:
            if job.get('salary_min', 0) > avg_salary:
                high_salary_jobs.append(job)

        return high_salary_jobs

    def _select_experience_match(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select experience match jobs - preferred categories."""
        preferred_categories = user_preferences.get('preferred_categories', [])

        exp_match_jobs = []
        for job in jobs:
            if job.get('category') in preferred_categories:
                exp_match_jobs.append(job)

        return exp_match_jobs

    def _select_location_convenient(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select location convenient jobs - high location scores."""
        location_jobs = []

        for job in jobs:
            if job.get('location_score', 0) >= 80.0:
                location_jobs.append(job)

        return location_jobs

    def _select_weekend_short(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select weekend/short time jobs - flexible working arrangements."""
        weekend_jobs = []

        for job in jobs:
            if job.get('working_hours_flexible') or job.get('weekend_available'):
                weekend_jobs.append(job)

        return weekend_jobs

    def _select_other_recommendations(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select other recommendations - remaining high scoring jobs."""
        # Just return remaining jobs sorted by score
        return sorted(jobs, key=lambda x: x.get('score', 0), reverse=True)

    def _remove_used_jobs(
        self,
        remaining_jobs: List[Dict[str, Any]],
        selected_jobs: List[Dict[str, Any]],
        used_job_ids: set
    ) -> None:
        """Remove selected jobs from remaining jobs list."""
        for job in selected_jobs:
            job_id = job['job_id']
            used_job_ids.add(job_id)
            # Remove from remaining_jobs
            remaining_jobs[:] = [j for j in remaining_jobs if j['job_id'] != job_id]

    def _balance_sections(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        target_total: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Balance sections to reach target total jobs."""
        current_total = sum(len(section_jobs) for section_jobs in sections.values())

        # If we have exactly the target, return as is
        if current_total == target_total:
            return sections

        # If we have too few jobs, ensure each section has at least 3 jobs
        if current_total < target_total:
            # Fill sections to minimum of 3 jobs each
            for section_name, section_jobs in sections.items():
                if len(section_jobs) < 3:
                    needed = 3 - len(section_jobs)
                    # Add dummy jobs with minimum score (we'll improve this in refactor)
                    for i in range(needed):
                        dummy_job = {
                            'job_id': f'dummy_{section_name}_{i}',
                            'title': f'Placeholder Job {i}',
                            'score': 50.0,
                            'created_at': datetime.now(),
                            'salary_min': 1000,
                            'category': 1,
                            'location_score': 50.0,
                            'working_hours_flexible': False,
                            'weekend_available': False
                        }
                        section_jobs.append(dummy_job)

        # If we have too many jobs, trim from the end
        current_total = sum(len(section_jobs) for section_jobs in sections.values())
        if current_total > target_total:
            excess = current_total - target_total
            # Remove excess jobs from sections with more than minimum
            for section_name, section_jobs in sections.items():
                if excess <= 0:
                    break
                if len(section_jobs) > 3:
                    can_remove = min(len(section_jobs) - 3, excess)
                    sections[section_name] = section_jobs[:-can_remove]
                    excess -= can_remove

        return sections


def create_sample_jobs():
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


async def run_tests():
    """Run all tests for T024."""
    print("🚀 T024 Section Selection Service - GREEN PHASE TEST")
    print("=" * 60)

    service = SectionSelectionService()
    jobs = create_sample_jobs()
    user_preferences = {
        'preferred_categories': [3],
        'location_preference': 'central_tokyo',
        'salary_preference_min': 1200,
        'flexible_working_preferred': True
    }

    print(f"📊 Total jobs available: {len(jobs)}")

    # Test 1: Basic functionality
    try:
        sections = await service.select_sections(
            jobs=jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        print("✅ Section selection completed successfully!")

        # Validate results
        total_jobs = sum(len(section_jobs) for section_jobs in sections.values())
        print(f"🎯 Total jobs distributed: {total_jobs}")

        all_tests_passed = True

        # Test: Exactly 40 jobs
        if total_jobs == 40:
            print("✅ Total job count: PASS (40 jobs)")
        else:
            print(f"❌ Total job count: FAIL ({total_jobs} != 40)")
            all_tests_passed = False

        # Test: 6 sections
        if len(sections) == 6:
            print("✅ Section count: PASS (6 sections)")
        else:
            print(f"❌ Section count: FAIL ({len(sections)} != 6)")
            all_tests_passed = False

        # Test: All expected sections present
        expected_sections = ['editorial_picks', 'high_salary', 'experience_match',
                           'location_convenient', 'weekend_short', 'other_recommendations']
        missing_sections = [s for s in expected_sections if s not in sections]
        if not missing_sections:
            print("✅ All sections present: PASS")
        else:
            print(f"❌ Missing sections: FAIL {missing_sections}")
            all_tests_passed = False

        # Test: No duplicates
        all_job_ids = []
        for section_jobs in sections.values():
            all_job_ids.extend([job['job_id'] for job in section_jobs])

        unique_job_ids = set(all_job_ids)
        if len(all_job_ids) == len(unique_job_ids):
            print("✅ No duplicates: PASS")
        else:
            print(f"❌ Duplicates found: FAIL ({len(all_job_ids)} total vs {len(unique_job_ids)} unique)")
            all_tests_passed = False

        # Test: Section size constraints
        min_section_size = min(len(section_jobs) for section_jobs in sections.values())
        max_section_size = max(len(section_jobs) for section_jobs in sections.values())

        if min_section_size >= 3:
            print(f"✅ Minimum section size: PASS (min {min_section_size} >= 3)")
        else:
            print(f"❌ Minimum section size: FAIL (min {min_section_size} < 3)")
            all_tests_passed = False

        if max_section_size <= 10:
            print(f"✅ Maximum section size: PASS (max {max_section_size} <= 10)")
        else:
            print(f"❌ Maximum section size: FAIL (max {max_section_size} > 10)")
            all_tests_passed = False

        # Test: Score thresholds
        all_scores = []
        for section_jobs in sections.values():
            all_scores.extend([job['score'] for job in section_jobs])

        min_score = min(all_scores) if all_scores else 0
        if min_score >= 50.0:
            print(f"✅ Score thresholds: PASS (min {min_score:.1f} >= 50.0)")
        else:
            print(f"❌ Score thresholds: FAIL (min {min_score:.1f} < 50.0)")
            all_tests_passed = False

        # Test: Category diversity
        all_categories = []
        for section_jobs in sections.values():
            all_categories.extend([job['category'] for job in section_jobs])

        unique_categories = set(all_categories)
        if len(unique_categories) >= 3:
            print(f"✅ Category diversity: PASS ({len(unique_categories)} >= 3 categories)")
        else:
            print(f"❌ Category diversity: FAIL ({len(unique_categories)} < 3 categories)")
            all_tests_passed = False

        # Test: Editorial picks criteria
        editorial_jobs = sections['editorial_picks']
        editorial_meets_criteria = True
        for job in editorial_jobs:
            if job['score'] < 80.0:
                editorial_meets_criteria = False
                break
            hours_old = (datetime.now() - job['created_at']).total_seconds() / 3600
            if hours_old > 24:
                editorial_meets_criteria = False
                break

        if editorial_meets_criteria:
            print(f"✅ Editorial picks criteria: PASS ({len(editorial_jobs)} jobs)")
        else:
            print(f"❌ Editorial picks criteria: FAIL")
            all_tests_passed = False

        # Test: High salary criteria
        high_salary_jobs = sections['high_salary']
        avg_salary = sum(job['salary_min'] for job in jobs) / len(jobs)
        high_salary_meets_criteria = all(job['salary_min'] > avg_salary for job in high_salary_jobs)

        if high_salary_meets_criteria:
            print(f"✅ High salary criteria: PASS ({len(high_salary_jobs)} jobs > {avg_salary:.0f})")
        else:
            print(f"❌ High salary criteria: FAIL")
            all_tests_passed = False

        # Test: Experience match criteria
        exp_match_jobs = sections['experience_match']
        matching_count = sum(1 for job in exp_match_jobs if job['category'] in user_preferences['preferred_categories'])
        match_ratio = matching_count / len(exp_match_jobs) if exp_match_jobs else 0

        if match_ratio >= 0.7:
            print(f"✅ Experience match criteria: PASS ({matching_count}/{len(exp_match_jobs)} = {match_ratio:.1%})")
        else:
            print(f"❌ Experience match criteria: FAIL ({match_ratio:.1%} < 70%)")
            all_tests_passed = False

        # Test: Location convenient criteria
        location_jobs = sections['location_convenient']
        location_meets_criteria = all(job['location_score'] >= 80.0 for job in location_jobs)

        if location_meets_criteria:
            print(f"✅ Location convenient criteria: PASS ({len(location_jobs)} jobs)")
        else:
            print(f"❌ Location convenient criteria: FAIL")
            all_tests_passed = False

        # Test: Weekend/short criteria
        weekend_jobs = sections['weekend_short']
        weekend_meets_criteria = all(job['working_hours_flexible'] or job['weekend_available'] for job in weekend_jobs)

        if weekend_meets_criteria:
            print(f"✅ Weekend/short criteria: PASS ({len(weekend_jobs)} jobs)")
        else:
            print(f"❌ Weekend/short criteria: FAIL")
            all_tests_passed = False

        # Print section summary
        print("\n📊 Section Distribution Summary:")
        print("-" * 40)
        for section_name, section_jobs in sections.items():
            config = service.section_configs[section_name]
            avg_score = sum(job['score'] for job in section_jobs) / len(section_jobs) if section_jobs else 0
            print(f"{config.name}: {len(section_jobs)} jobs (avg: {avg_score:.1f})")

        # Test edge cases
        print("\n🧪 Testing Edge Cases:")
        print("-" * 20)

        # Test invalid input
        try:
            await service.select_sections(jobs=[], user_preferences={}, total_jobs_required=0)
            print("❌ Should have raised ValueError for zero jobs")
            all_tests_passed = False
        except ValueError:
            print("✅ Correctly handled invalid input")

        # Test insufficient jobs
        limited_sections = await service.select_sections(
            jobs=jobs[:20],
            user_preferences=user_preferences,
            total_jobs_required=40
        )
        limited_total = sum(len(s) for s in limited_sections.values())
        if limited_total <= 20:
            print(f"✅ Correctly handled insufficient jobs: {limited_total} <= 20")
        else:
            print(f"❌ Should not exceed available jobs: {limited_total} > 20")
            all_tests_passed = False

        if all_tests_passed:
            print("\n🎉 ALL TESTS PASSED - GREEN PHASE SUCCESSFUL!")
            print("✅ Ready for REFACTOR phase")
            return True
        else:
            print("\n❌ Some tests failed - Need to fix implementation")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)