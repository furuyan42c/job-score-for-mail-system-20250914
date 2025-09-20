"""
T024: 6-Section Selection Logic - GREEN PHASE Implementation

Minimal implementation to satisfy the test requirements for distributing
40 jobs across 6 email sections with specific criteria.

This is a basic implementation focused on passing tests, not optimization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


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

        Args:
            jobs: List of job dictionaries
            user_preferences: User preference dictionary
            total_jobs_required: Total number of jobs to select (default 40)

        Returns:
            Dictionary with section names as keys and job lists as values

        Raises:
            ValueError: If total_jobs_required is not positive
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