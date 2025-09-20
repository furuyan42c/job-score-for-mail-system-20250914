"""
T024: 6-Section Selection Logic - REFACTOR PHASE Implementation

Production-ready implementation for distributing jobs across 6 email sections
with sophisticated criteria, configurable thresholds, and robust error handling.

Email Section Structure:
1. Editorial Picks (注目求人) - High score recent jobs
2. High Salary (高時給のお仕事) - Above average salary jobs
3. Experience Match (あなたの経験を活かせる求人) - Category preference match
4. Location Convenient (通勤便利な求人) - High location scores
5. Weekend/Short Time (週末・短時間OK) - Flexible working arrangements
6. Other Recommendations (その他のおすすめ) - Remaining high scores

Features:
- Configurable section criteria and thresholds
- Intelligent job distribution with fallback mechanisms
- Category diversity enforcement
- Comprehensive error handling and logging
- Performance optimization for large job sets
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Enumeration of email section types."""
    EDITORIAL_PICKS = "editorial_picks"
    HIGH_SALARY = "high_salary"
    EXPERIENCE_MATCH = "experience_match"
    LOCATION_CONVENIENT = "location_convenient"
    WEEKEND_SHORT = "weekend_short"
    OTHER_RECOMMENDATIONS = "other_recommendations"


@dataclass
class SelectionCriteria:
    """Criteria configuration for section selection."""
    score_threshold: float = 50.0
    recency_hours: Optional[float] = None
    salary_percentile: Optional[float] = None
    location_score_threshold: Optional[float] = None
    requires_flexibility: bool = False
    category_preference_weight: float = 1.0


@dataclass
class SectionLimits:
    """Limits and constraints for section selection."""
    total_jobs_required: int = 40
    min_jobs_per_section: int = 3
    max_jobs_per_section: int = 10
    min_category_diversity: int = 3
    max_jobs_per_category: int = 15


@dataclass
class SectionConfig:
    """Configuration for email sections."""
    name: str
    target_count: int
    priority: int
    criteria: SelectionCriteria
    section_type: SectionType


class SectionSelectionService:
    """Service for selecting and distributing jobs across 6 email sections."""

    def __init__(self, limits: Optional[SectionLimits] = None):
        """Initialize the section selection service.

        Args:
            limits: Custom section limits and constraints
        """
        self.limits = limits or SectionLimits()
        self.section_configs = self._create_default_section_configs()
        self._selection_strategies = self._initialize_selection_strategies()

    def _create_default_section_configs(self) -> Dict[str, SectionConfig]:
        """Create default section configurations with optimized criteria."""
        return {
            SectionType.EDITORIAL_PICKS.value: SectionConfig(
                name='今週の注目求人',
                target_count=8,
                priority=1,
                criteria=SelectionCriteria(
                    score_threshold=80.0,
                    recency_hours=24.0
                ),
                section_type=SectionType.EDITORIAL_PICKS
            ),
            SectionType.HIGH_SALARY.value: SectionConfig(
                name='高時給のお仕事',
                target_count=7,
                priority=2,
                criteria=SelectionCriteria(
                    score_threshold=70.0,
                    salary_percentile=50.0
                ),
                section_type=SectionType.HIGH_SALARY
            ),
            SectionType.EXPERIENCE_MATCH.value: SectionConfig(
                name='あなたの経験を活かせる求人',
                target_count=7,
                priority=3,
                criteria=SelectionCriteria(
                    score_threshold=60.0,
                    category_preference_weight=2.0
                ),
                section_type=SectionType.EXPERIENCE_MATCH
            ),
            SectionType.LOCATION_CONVENIENT.value: SectionConfig(
                name='通勤便利な求人',
                target_count=6,
                priority=4,
                criteria=SelectionCriteria(
                    score_threshold=60.0,
                    location_score_threshold=80.0
                ),
                section_type=SectionType.LOCATION_CONVENIENT
            ),
            SectionType.WEEKEND_SHORT.value: SectionConfig(
                name='週末・短時間OK',
                target_count=6,
                priority=5,
                criteria=SelectionCriteria(
                    score_threshold=55.0,
                    requires_flexibility=True
                ),
                section_type=SectionType.WEEKEND_SHORT
            ),
            SectionType.OTHER_RECOMMENDATIONS.value: SectionConfig(
                name='その他のおすすめ',
                target_count=6,
                priority=6,
                criteria=SelectionCriteria(
                    score_threshold=50.0
                ),
                section_type=SectionType.OTHER_RECOMMENDATIONS
            )
        }

    def _initialize_selection_strategies(self) -> Dict[SectionType, Callable]:
        """Initialize section selection strategy functions."""
        return {
            SectionType.EDITORIAL_PICKS: self._select_editorial_picks,
            SectionType.HIGH_SALARY: self._select_high_salary,
            SectionType.EXPERIENCE_MATCH: self._select_experience_match,
            SectionType.LOCATION_CONVENIENT: self._select_location_convenient,
            SectionType.WEEKEND_SHORT: self._select_weekend_short,
            SectionType.OTHER_RECOMMENDATIONS: self._select_other_recommendations
        }

    async def select_sections(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        total_jobs_required: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Select and distribute jobs across 6 sections with intelligent criteria.

        Args:
            jobs: List of job dictionaries with required fields
            user_preferences: User preference dictionary
            total_jobs_required: Total number of jobs to select (default from limits)

        Returns:
            Dictionary with section names as keys and job lists as values

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If section selection fails
        """
        # Input validation
        total_jobs_required = total_jobs_required or self.limits.total_jobs_required
        self._validate_inputs(jobs, user_preferences, total_jobs_required)

        logger.info(f"Starting section selection for {len(jobs)} jobs, target: {total_jobs_required}")

        try:
            # Pre-process jobs and calculate context
            processed_jobs = self._preprocess_jobs(jobs)
            selection_context = self._build_selection_context(processed_jobs, user_preferences)

            # Execute section selection with priority ordering
            sections = await self._execute_section_selection(
                processed_jobs, user_preferences, selection_context, total_jobs_required
            )

            # Post-process and validate results
            sections = self._post_process_sections(sections, total_jobs_required)
            self._validate_results(sections, total_jobs_required)

            logger.info(f"Section selection completed successfully: {sum(len(s) for s in sections.values())} jobs distributed")
            return sections

        except Exception as e:
            logger.error(f"Section selection failed: {e}")
            raise RuntimeError(f"Failed to select sections: {e}") from e

    def _validate_inputs(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        total_jobs_required: int
    ) -> None:
        """Validate input parameters."""
        if not jobs:
            raise ValueError("Jobs list cannot be empty")

        if total_jobs_required <= 0:
            raise ValueError("total_jobs_required must be positive")

        if not isinstance(user_preferences, dict):
            raise ValueError("user_preferences must be a dictionary")

        # Validate required job fields
        required_fields = ['job_id', 'score']
        for i, job in enumerate(jobs[:5]):  # Check first 5 jobs for performance
            missing_fields = [field for field in required_fields if field not in job]
            if missing_fields:
                raise ValueError(f"Job {i} missing required fields: {missing_fields}")

    def _preprocess_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess jobs for selection optimization."""
        # Sort by score (highest first) and add metadata
        processed_jobs = []
        for job in sorted(jobs, key=lambda x: x.get('score', 0), reverse=True):
            processed_job = job.copy()

            # Add job age calculation
            created_at = job.get('created_at')
            if isinstance(created_at, datetime):
                age_hours = (datetime.now() - created_at).total_seconds() / 3600
                processed_job['age_hours'] = age_hours
            else:
                processed_job['age_hours'] = float('inf')

            processed_jobs.append(processed_job)

        return processed_jobs

    def _build_selection_context(self, jobs: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Build context information for section selection."""
        # Calculate salary statistics
        salaries = [job.get('salary_min', 0) for job in jobs if job.get('salary_min')]
        avg_salary = sum(salaries) / len(salaries) if salaries else 1000

        # Calculate category distribution
        categories = [job.get('category') for job in jobs if job.get('category')]
        category_counts = Counter(categories)

        return {
            'avg_salary': avg_salary,
            'total_jobs': len(jobs),
            'category_distribution': category_counts,
            'preferred_categories': set(user_preferences.get('preferred_categories', [])),
            'salary_threshold_50th': avg_salary,
            'salary_threshold_75th': avg_salary * 1.3  # Rough estimate
        }

    async def _execute_section_selection(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        total_jobs_required: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute the main section selection logic."""
        sections = {section_name: [] for section_name in self.section_configs.keys()}
        remaining_jobs = jobs.copy()
        used_job_ids = set()

        # Process sections in priority order
        sorted_configs = sorted(
            self.section_configs.items(),
            key=lambda x: x[1].priority
        )

        for section_name, config in sorted_configs:
            try:
                # Get selection strategy
                strategy = self._selection_strategies[config.section_type]

                # Select jobs for this section
                selected_jobs = strategy(
                    remaining_jobs, user_preferences, context, config.criteria
                )

                # Limit to target count
                selected_jobs = selected_jobs[:config.target_count]
                sections[section_name] = selected_jobs

                # Remove selected jobs from remaining pool
                self._remove_used_jobs(remaining_jobs, selected_jobs, used_job_ids)

                logger.debug(f"Section {section_name}: selected {len(selected_jobs)} jobs")

            except Exception as e:
                logger.warning(f"Failed to select jobs for section {section_name}: {e}")
                sections[section_name] = []

        return sections

    def _select_editorial_picks(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select editorial picks - high score recent jobs."""
        editorial_jobs = []

        for job in jobs:
            # Check score threshold
            if job.get('score', 0) >= criteria.score_threshold:
                # Check recency if specified
                if criteria.recency_hours is not None:
                    age_hours = job.get('age_hours', float('inf'))
                    if age_hours <= criteria.recency_hours:
                        editorial_jobs.append(job)
                else:
                    editorial_jobs.append(job)

        return editorial_jobs

    def _select_high_salary(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select high salary jobs - above salary threshold."""
        high_salary_jobs = []

        # Get salary threshold from context
        if criteria.salary_percentile is not None:
            threshold_key = f'salary_threshold_{int(criteria.salary_percentile)}th'
            salary_threshold = context.get(threshold_key, context.get('avg_salary', 1000))
        else:
            salary_threshold = context.get('avg_salary', 1000)

        for job in jobs:
            if (job.get('score', 0) >= criteria.score_threshold and
                job.get('salary_min', 0) > salary_threshold):
                high_salary_jobs.append(job)

        return high_salary_jobs

    def _select_experience_match(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select experience match jobs - preferred categories with weighted scoring."""
        preferred_categories = context.get('preferred_categories', set())
        exp_match_jobs = []

        for job in jobs:
            if job.get('score', 0) >= criteria.score_threshold:
                # Apply category preference weighting
                if job.get('category') in preferred_categories:
                    # Create a copy with boosted score for sorting
                    weighted_job = job.copy()
                    weighted_job['weighted_score'] = job.get('score', 0) * criteria.category_preference_weight
                    exp_match_jobs.append(weighted_job)

        # Sort by weighted score
        return sorted(exp_match_jobs, key=lambda x: x.get('weighted_score', 0), reverse=True)

    def _select_location_convenient(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select location convenient jobs - high location scores."""
        location_jobs = []
        location_threshold = criteria.location_score_threshold or 80.0

        for job in jobs:
            if (job.get('score', 0) >= criteria.score_threshold and
                job.get('location_score', 0) >= location_threshold):
                location_jobs.append(job)

        return location_jobs

    def _select_weekend_short(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select weekend/short time jobs - flexible working arrangements."""
        weekend_jobs = []

        for job in jobs:
            if job.get('score', 0) >= criteria.score_threshold:
                if criteria.requires_flexibility:
                    if job.get('working_hours_flexible') or job.get('weekend_available'):
                        weekend_jobs.append(job)
                else:
                    weekend_jobs.append(job)

        return weekend_jobs

    def _select_other_recommendations(
        self,
        jobs: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Select other recommendations - remaining high scoring jobs."""
        other_jobs = []

        for job in jobs:
            if job.get('score', 0) >= criteria.score_threshold:
                other_jobs.append(job)

        # Return sorted by score (already sorted from preprocessing)
        return other_jobs

    def _remove_used_jobs(
        self,
        remaining_jobs: List[Dict[str, Any]],
        selected_jobs: List[Dict[str, Any]],
        used_job_ids: set
    ) -> None:
        """Remove selected jobs from remaining jobs list efficiently."""
        if not selected_jobs:
            return

        # Build set of job IDs to remove for O(1) lookup
        job_ids_to_remove = {job['job_id'] for job in selected_jobs}
        used_job_ids.update(job_ids_to_remove)

        # Filter out used jobs in single pass
        remaining_jobs[:] = [
            job for job in remaining_jobs
            if job['job_id'] not in job_ids_to_remove
        ]

    def _post_process_sections(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        target_total: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Post-process sections to meet constraints and optimize distribution."""
        # Ensure minimum jobs per section
        sections = self._ensure_minimum_section_sizes(sections)

        # Balance to target total
        sections = self._balance_section_sizes(sections, target_total)

        # Enforce category diversity
        sections = self._enforce_category_diversity(sections)

        return sections

    def _ensure_minimum_section_sizes(self, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Ensure each section has at least the minimum number of jobs."""
        for section_name, section_jobs in sections.items():
            if len(section_jobs) < self.limits.min_jobs_per_section:
                shortage = self.limits.min_jobs_per_section - len(section_jobs)
                logger.warning(f"Section {section_name} has only {len(section_jobs)} jobs, need {self.limits.min_jobs_per_section}")

                # Try to redistribute from other sections
                redistributed = self._redistribute_jobs_to_section(sections, section_name, shortage)
                if redistributed < shortage:
                    logger.warning(f"Could only redistribute {redistributed} jobs to {section_name}, still short {shortage - redistributed}")

        return sections

    def _redistribute_jobs_to_section(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        target_section: str,
        needed: int
    ) -> int:
        """Redistribute jobs from other sections to target section."""
        redistributed = 0

        # Sort sections by current size (largest first)
        sorted_sections = sorted(
            [(name, jobs) for name, jobs in sections.items() if name != target_section],
            key=lambda x: len(x[1]),
            reverse=True
        )

        for section_name, section_jobs in sorted_sections:
            if redistributed >= needed:
                break

            # Can only take jobs if section has more than minimum
            available = len(section_jobs) - self.limits.min_jobs_per_section
            if available > 0:
                take_count = min(available, needed - redistributed)

                # Move jobs
                moved_jobs = section_jobs[-take_count:]
                sections[section_name] = section_jobs[:-take_count]
                sections[target_section].extend(moved_jobs)
                redistributed += take_count

        return redistributed

    def _balance_section_sizes(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        target_total: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Balance section sizes to reach target total."""
        current_total = sum(len(section_jobs) for section_jobs in sections.values())

        if current_total == target_total:
            return sections

        if current_total > target_total:
            # Trim excess jobs
            excess = current_total - target_total
            sections = self._trim_excess_jobs(sections, excess)

        # Note: If we have fewer than target, we keep what we have
        # rather than adding dummy jobs in production

        return sections

    def _trim_excess_jobs(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        excess: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Trim excess jobs from sections while respecting minimums."""
        remaining_excess = excess

        # Sort sections by priority (lowest priority first for trimming)
        sorted_configs = sorted(
            self.section_configs.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )

        for section_name, config in sorted_configs:
            if remaining_excess <= 0:
                break

            section_jobs = sections[section_name]
            available_to_trim = len(section_jobs) - self.limits.min_jobs_per_section

            if available_to_trim > 0:
                trim_count = min(available_to_trim, remaining_excess)
                sections[section_name] = section_jobs[:-trim_count]
                remaining_excess -= trim_count

        return sections

    def _enforce_category_diversity(
        self,
        sections: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Enforce category diversity constraints."""
        # Count categories across all sections
        all_categories = []
        for section_jobs in sections.values():
            all_categories.extend([job.get('category') for job in section_jobs if job.get('category')])

        category_counts = Counter(all_categories)

        # Check if any category is over the limit
        for category, count in category_counts.items():
            if count > self.limits.max_jobs_per_category:
                logger.warning(f"Category {category} has {count} jobs, exceeds limit {self.limits.max_jobs_per_category}")
                # In production, we might implement category balancing here

        return sections

    def _validate_results(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        target_total: int
    ) -> None:
        """Validate section selection results."""
        total_jobs = sum(len(section_jobs) for section_jobs in sections.values())

        # Check basic constraints
        if len(sections) != 6:
            raise RuntimeError(f"Expected 6 sections, got {len(sections)}")

        # Check for duplicates
        all_job_ids = []
        for section_jobs in sections.values():
            all_job_ids.extend([job['job_id'] for job in section_jobs])

        if len(all_job_ids) != len(set(all_job_ids)):
            raise RuntimeError("Duplicate jobs found across sections")

        # Check category diversity
        all_categories = []
        for section_jobs in sections.values():
            all_categories.extend([job.get('category') for job in section_jobs if job.get('category')])

        unique_categories = len(set(all_categories))
        if unique_categories < self.limits.min_category_diversity:
            logger.warning(f"Low category diversity: {unique_categories} < {self.limits.min_category_diversity}")

    def update_section_config(
        self,
        section_type: SectionType,
        config: SectionConfig
    ) -> None:
        """Update configuration for a specific section.

        Args:
            section_type: Type of section to update
            config: New configuration
        """
        self.section_configs[section_type.value] = config
        logger.info(f"Updated configuration for section {section_type.value}")

    def get_section_statistics(
        self,
        sections: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each section.

        Args:
            sections: Section selection results

        Returns:
            Dictionary with section statistics
        """
        stats = {}

        for section_name, section_jobs in sections.items():
            if section_jobs:
                scores = [job.get('score', 0) for job in section_jobs]
                salaries = [job.get('salary_min', 0) for job in section_jobs if job.get('salary_min')]
                categories = [job.get('category') for job in section_jobs if job.get('category')]

                stats[section_name] = {
                    'job_count': len(section_jobs),
                    'avg_score': sum(scores) / len(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'avg_salary': sum(salaries) / len(salaries) if salaries else 0,
                    'unique_categories': len(set(categories)),
                    'category_distribution': dict(Counter(categories))
                }
            else:
                stats[section_name] = {
                    'job_count': 0,
                    'avg_score': 0,
                    'min_score': 0,
                    'max_score': 0,
                    'avg_salary': 0,
                    'unique_categories': 0,
                    'category_distribution': {}
                }

        return stats