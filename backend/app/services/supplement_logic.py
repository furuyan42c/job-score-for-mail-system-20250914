#!/usr/bin/env python3
"""
T026 REFACTOR PHASE: Enhanced 40-item Supplement Logic Implementation
Improved code quality, maintainability, and error handling.
"""

import logging
from typing import List, Any, Optional, Dict, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ===== PROTOCOLS & INTERFACES =====

class JobLike(Protocol):
    """Protocol defining the interface for job-like objects."""
    job_id: str
    basic_score: float
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

class UserLike(Protocol):
    """Protocol defining the interface for user-like objects."""
    preferences: Optional[Dict[str, Any]] = None

# ===== DATA CLASSES =====

@dataclass
class SupplementConfig:
    """Configuration for supplement logic."""
    target_count: int = 40
    fallback_score: float = 25.0
    min_quality_threshold: float = 0.0
    max_fallback_ratio: float = 0.8  # Max 80% fallback jobs

    def __post_init__(self):
        """Validate configuration values."""
        if self.target_count < 1:
            raise ValueError("target_count must be positive")
        if self.fallback_score < 0:
            raise ValueError("fallback_score must be non-negative")
        if not 0 <= self.max_fallback_ratio <= 1:
            raise ValueError("max_fallback_ratio must be between 0 and 1")

@dataclass
class FallbackJob:
    """Enhanced fallback job with better error handling."""
    job_id: str
    basic_score: float = 25.0
    title: str = "Fallback Job"
    company: str = "Fallback Company"
    location: str = "Unknown"

    def __post_init__(self):
        """Validate fallback job data."""
        if not self.job_id:
            raise ValueError("job_id cannot be empty")
        if self.basic_score < 0:
            raise ValueError("basic_score must be non-negative")

@dataclass
class SupplementResult:
    """Result object for supplement operation with metrics."""
    jobs: List[Any]
    original_count: int
    supplemented_count: int
    fallback_count: int
    total_count: int
    config_used: SupplementConfig

    @property
    def supplemented_ratio(self) -> float:
        """Ratio of supplemented jobs to total."""
        return self.supplemented_count / self.total_count if self.total_count > 0 else 0.0

# ===== ABSTRACT BASE CLASS =====

class BaseSupplementService(ABC):
    """Abstract base class for supplement services."""

    @abstractmethod
    async def ensure_minimum_items(self, jobs: List[Any], user: Any, target_count: int = None) -> List[Any]:
        """Ensure minimum number of items through supplementation."""
        pass

# ===== MAIN SERVICE =====

class SupplementLogicService(BaseSupplementService):
    """
    Enhanced 40-item supplement logic service with improved architecture.

    This service ensures that job recommendation lists always contain
    the target number of items by supplementing with fallback jobs
    when necessary.
    """

    def __init__(self, config: Optional[SupplementConfig] = None):
        """
        Initialize supplement service with configuration.

        Args:
            config: Optional configuration. Uses defaults if None.
        """
        self.config = config or SupplementConfig()
        logger.info(f"SupplementLogicService initialized with target_count={self.config.target_count}")

    async def ensure_minimum_items(self,
                                 jobs: List[Any],
                                 user: Any,
                                 target_count: int = None) -> List[Any]:
        """
        Ensure minimum number of items through supplementation.

        Args:
            jobs: Original list of jobs
            user: User object for preference-based supplementation
            target_count: Override target count (uses config default if None)

        Returns:
            List of jobs supplemented to target count

        Raises:
            ValueError: If target_count is invalid
        """
        target = self._validate_target_count(target_count)

        if len(jobs) >= target:
            return self._select_top_jobs(jobs, target)

        # Calculate supplement requirements
        original_count = len(jobs)
        needed = target - original_count

        # Check if we exceed fallback ratio limits
        if self._exceeds_fallback_limits(original_count, needed):
            logger.warning(f"Supplement would exceed max fallback ratio of {self.config.max_fallback_ratio}")
            # Still proceed but log the warning

        # Perform supplementation
        result = await self._supplement_jobs(jobs, user, needed)

        # Sort and return top jobs
        sorted_result = self._sort_jobs_by_score(result)
        return sorted_result[:target]

    async def ensure_minimum_items_with_metrics(self,
                                              jobs: List[Any],
                                              user: Any,
                                              target_count: int = None) -> SupplementResult:
        """
        Ensure minimum items and return detailed metrics.

        Args:
            jobs: Original list of jobs
            user: User object for preferences
            target_count: Override target count

        Returns:
            SupplementResult with jobs and metrics
        """
        target = self._validate_target_count(target_count)
        original_count = len(jobs)

        supplemented_jobs = await self.ensure_minimum_items(jobs, user, target)

        # Calculate metrics
        fallback_count = sum(1 for job in supplemented_jobs
                           if self._is_fallback_job(job))
        supplemented_count = len(supplemented_jobs) - original_count

        return SupplementResult(
            jobs=supplemented_jobs,
            original_count=original_count,
            supplemented_count=supplemented_count,
            fallback_count=fallback_count,
            total_count=len(supplemented_jobs),
            config_used=self.config
        )

    # ===== PRIVATE METHODS =====

    def _validate_target_count(self, target_count: Optional[int]) -> int:
        """Validate and return target count."""
        target = target_count or self.config.target_count
        if target < 1:
            raise ValueError("target_count must be positive")
        return target

    def _exceeds_fallback_limits(self, original_count: int, needed: int) -> bool:
        """Check if supplement would exceed fallback ratio limits."""
        total = original_count + needed
        fallback_ratio = needed / total if total > 0 else 0
        return fallback_ratio > self.config.max_fallback_ratio

    def _select_top_jobs(self, jobs: List[Any], target: int) -> List[Any]:
        """Select top jobs when we already have enough."""
        sorted_jobs = self._sort_jobs_by_score(jobs)
        return sorted_jobs[:target]

    async def _supplement_jobs(self, jobs: List[Any], user: Any, needed: int) -> List[Any]:
        """Supplement jobs with fallbacks."""
        result = jobs.copy()
        existing_ids = self._extract_job_ids(jobs)
        user_location = self._extract_user_location(user)

        for i in range(needed):
            fallback_job = self._create_fallback_job(i, existing_ids, user_location)
            result.append(fallback_job)
            existing_ids.add(fallback_job.job_id)

        return result

    def _extract_job_ids(self, jobs: List[Any]) -> set:
        """Extract job IDs from job list."""
        return {getattr(job, 'job_id', f'job_{i}') for i, job in enumerate(jobs)}

    def _extract_user_location(self, user: Any) -> str:
        """Extract user's preferred location."""
        if not hasattr(user, 'preferences'):
            return "Unknown"

        preferences = getattr(user, 'preferences', {})
        if not isinstance(preferences, dict):
            return "Unknown"

        return preferences.get('location', 'Unknown')

    def _create_fallback_job(self, index: int, existing_ids: set, location: str) -> FallbackJob:
        """Create a unique fallback job."""
        fallback_id = self._generate_unique_id(index, existing_ids)

        return FallbackJob(
            job_id=fallback_id,
            basic_score=self.config.fallback_score,
            title=f"Fallback Job {index + 1}",
            company=f"Fallback Company {index + 1}",
            location=location
        )

    def _generate_unique_id(self, base_index: int, existing_ids: set) -> str:
        """Generate a unique fallback job ID."""
        counter = base_index
        while True:
            candidate_id = f"fallback_{counter:03d}"
            if candidate_id not in existing_ids:
                return candidate_id
            counter += 1

    def _sort_jobs_by_score(self, jobs: List[Any]) -> List[Any]:
        """Sort jobs by score in descending order."""
        return sorted(jobs, key=lambda x: getattr(x, 'basic_score', 0), reverse=True)

    def _is_fallback_job(self, job: Any) -> bool:
        """Check if a job is a fallback job."""
        job_id = getattr(job, 'job_id', '')
        return job_id.startswith('fallback_')

# ===== BACKWARD COMPATIBILITY =====

class MinimalJobSupplementService(SupplementLogicService):
    """Backward compatibility alias."""

    def __init__(self, target_count: int = 40):
        """Initialize with simple target count for backward compatibility."""
        config = SupplementConfig(target_count=target_count)
        super().__init__(config)