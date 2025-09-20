#!/usr/bin/env python3
"""
T025: Duplicate Control Service

Prevents duplicate job recommendations by filtering jobs from companies
where the user has recently applied within a configurable time window.

This service provides comprehensive duplicate detection and prevention:
- Company-level duplicate filtering (14-day exclusion window)
- Job-level duplicate detection
- User application history tracking
- Configurable duplicate resolution strategies
- Database-backed application queries
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum

try:
    from app.models.job import Job
except ImportError:
    # Fallback for testing environments
    Job = None

logger = logging.getLogger(__name__)


class DuplicateStrategy(Enum):
    """Strategies for resolving duplicate jobs."""
    KEEP_NEWEST = "keep_newest"
    KEEP_OLDEST = "keep_oldest"
    MERGE = "merge"
    KEEP_FIRST = "keep_first"


class DuplicateControlConfig:
    """Configuration constants for duplicate control."""

    # Time window configurations
    DEFAULT_WINDOW_DAYS = 14
    MIN_WINDOW_DAYS = 1
    MAX_WINDOW_DAYS = 90

    # Similarity thresholds
    HIGH_SIMILARITY_THRESHOLD = 0.8
    MEDIUM_SIMILARITY_THRESHOLD = 0.6
    LOW_SIMILARITY_THRESHOLD = 0.3

    # Job comparison weights
    COMPANY_WEIGHT = 0.3
    TITLE_WEIGHT = 0.25
    LOCATION_WEIGHT = 0.2
    SALARY_WEIGHT = 0.15
    EMPLOYMENT_TYPE_WEIGHT = 0.1

    # Database query limits
    MAX_APPLICATIONS_QUERY = 1000
    MAX_COMPANIES_QUERY = 500


class DuplicateControlService:
    """
    Service for filtering duplicate job recommendations.

    Provides comprehensive duplicate detection and prevention capabilities:
    - Company-level filtering with configurable time windows
    - Job similarity detection and resolution
    - User application history management
    - Multiple duplicate resolution strategies
    """

    def __init__(
        self,
        db=None,
        window_days: int = DuplicateControlConfig.DEFAULT_WINDOW_DAYS,
        config: Optional[DuplicateControlConfig] = None
    ):
        """
        Initialize duplicate control service.

        Args:
            db: Database session (optional for testing)
            window_days: Number of days to check for duplicates
            config: Custom configuration object (optional)
        """
        self.db = db
        self.config = config or DuplicateControlConfig()

        # Validate and set window_days parameter
        self.window_days = self._validate_window_days(window_days)

        logger.info(
            "DuplicateControlService initialized with %d day window, similarity threshold %.2f",
            self.window_days,
            self.config.HIGH_SIMILARITY_THRESHOLD
        )

    def _validate_window_days(self, window_days: int) -> int:
        """
        Validate window_days parameter.

        Args:
            window_days: Requested window days

        Returns:
            Validated window days within acceptable range
        """
        if window_days < self.config.MIN_WINDOW_DAYS:
            logger.warning(
                "Window days %d below minimum (%d), using minimum",
                window_days,
                self.config.MIN_WINDOW_DAYS,
            )
            return self.config.MIN_WINDOW_DAYS
        elif window_days > self.config.MAX_WINDOW_DAYS:
            logger.warning(
                "Window days %d exceeds maximum (%d), using maximum",
                window_days,
                self.config.MAX_WINDOW_DAYS,
            )
            return self.config.MAX_WINDOW_DAYS

        return window_days

    async def filter_duplicates(
        self, jobs: List[Job], applications: List[Dict[str, Any]]
    ) -> List[Job]:
        """
        Filter out jobs from companies where user has recently applied.

        Args:
            jobs: List of candidate jobs
            applications: List of user's application history with 'company_id' and 'applied_at' fields

        Returns:
            Filtered list of jobs excluding recent company applications
        """
        # Return all jobs if no application history
        if not applications:
            logger.debug(
                "No application history provided, returning all %d jobs", len(jobs) if jobs else 0
            )
            return jobs if jobs else []

        # Return empty list if no jobs
        if not jobs:
            logger.debug("No jobs provided for duplicate filtering")
            return []

        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.window_days)
            recent_company_ids = set()

            # Identify companies with recent applications
            for application in applications:
                if not isinstance(application, dict):
                    logger.warning("Skipping invalid application record: %s", type(application))
                    continue

                # Extract and validate company_id
                company_id = application.get("company_id")
                if not company_id:
                    continue

                # Extract and parse applied_at timestamp
                applied_at = application.get("applied_at")
                if not applied_at:
                    continue

                # Convert string timestamp if needed
                if isinstance(applied_at, str):
                    try:
                        applied_at = datetime.fromisoformat(applied_at.replace("Z", "+00:00"))
                    except (ValueError, AttributeError) as e:
                        logger.warning("Invalid timestamp format: %s", applied_at)
                        continue

                # Check if application is within window
                if applied_at >= cutoff_date:
                    recent_company_ids.add(company_id)
                    days_ago = (now - applied_at).days
                    logger.debug(
                        "Found recent application to company %s (%d days ago)", company_id, days_ago
                    )

            logger.info(
                "Identified %d companies with applications in last %d days",
                len(recent_company_ids),
                self.window_days,
            )

            # Filter jobs
            filtered_jobs = []
            filtered_count = 0

            for job in jobs:
                job_company_id = getattr(job, "company_id", None)

                # Keep job if no company_id or not in recent applications
                if not job_company_id or job_company_id not in recent_company_ids:
                    filtered_jobs.append(job)
                else:
                    filtered_count += 1
                    logger.debug(
                        "Filtering job %s from recently applied company %s",
                        getattr(job, "job_id", "unknown"),
                        job_company_id,
                    )

            logger.info(
                "Filtered %d duplicate jobs, returning %d unique jobs",
                filtered_count,
                len(filtered_jobs),
            )
            return filtered_jobs

        except Exception as e:
            logger.error("Error filtering duplicates: %s", e)
            # Return original jobs on error to avoid losing recommendations
            return jobs

    async def get_recent_companies(self, applications: List[Dict[str, Any]]) -> List[str]:
        """
        Get list of company IDs with recent applications.

        Args:
            applications: List of user's application history

        Returns:
            List of company IDs with recent applications
        """
        if not applications:
            return []

        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.window_days)
            recent_companies = []

            for application in applications:
                if not isinstance(application, dict):
                    continue

                company_id = application.get("company_id")
                if not company_id:
                    continue

                applied_at = application.get("applied_at")
                if not applied_at:
                    continue

                if isinstance(applied_at, str):
                    try:
                        applied_at = datetime.fromisoformat(applied_at.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue

                if applied_at >= cutoff_date:
                    recent_companies.append(company_id)

            return recent_companies

        except Exception as e:
            logger.error("Error getting recent companies: %s", e)
            return []

    # ============================================================================
    # GREEN PHASE: Additional methods to pass tests
    # ============================================================================

    async def detect_duplicate_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect duplicate job entries.
        GREEN PHASE: Minimal implementation that groups by company code.
        """
        if not jobs:
            return {'by_company': [], 'by_content': []}

        # Group jobs by company code (endcl_cd)
        company_groups = {}
        for job in jobs:
            company_cd = job.get('endcl_cd')
            if company_cd:
                if company_cd not in company_groups:
                    company_groups[company_cd] = []
                company_groups[company_cd].append(job)

        # Find groups with more than one job (duplicates)
        duplicate_groups = []
        for company_cd, company_jobs in company_groups.items():
            if len(company_jobs) > 1:
                duplicate_groups.append({
                    'endcl_cd': company_cd,
                    'jobs': company_jobs
                })

        return {
            'by_company': duplicate_groups,
            'by_content': []  # Not implemented in GREEN phase
        }

    async def detect_user_job_duplicates(
        self,
        user_id: int,
        job_ids: List[str],
        existing_applications: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Detect user-job pair duplicates.
        GREEN PHASE: Simple comparison of job IDs.
        """
        applied_job_ids = set()
        for app in existing_applications:
            if app.get('user_id') == user_id:
                applied_job_ids.add(app.get('job_id'))

        # Return job IDs that user has already applied to
        duplicates = [job_id for job_id in job_ids if job_id in applied_job_ids]
        return duplicates

    async def is_time_based_duplicate(
        self,
        user_id: int,
        job_id: str,
        time_window_days: int,
        existing_applications: List[Dict[str, Any]]
    ) -> bool:
        """
        Check for time-based duplicates.
        GREEN PHASE: Simple time window check.
        """
        if time_window_days <= 0:
            raise ValueError("Time window must be positive")

        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        for app in existing_applications:
            if (app.get('user_id') == user_id and
                app.get('job_id') == job_id and
                app.get('applied_at') > cutoff_date):
                return True

        return False

    async def resolve_duplicates(
        self,
        duplicate_groups: List[Dict[str, Any]],
        strategy: str = DuplicateStrategy.KEEP_NEWEST.value
    ) -> List[Dict[str, Any]]:
        """
        Resolve duplicates using specified strategy.

        Args:
            duplicate_groups: Groups of duplicate jobs to resolve
            strategy: Resolution strategy (keep_newest, keep_oldest, merge, keep_first)

        Returns:
            List of resolved jobs (one per group)
        """
        if not duplicate_groups:
            return []

        resolved = []
        strategy_enum = self._parse_strategy(strategy)

        for group in duplicate_groups:
            jobs = group.get('jobs', [])
            if not jobs:
                continue

            resolved_job = self._resolve_job_group(jobs, strategy_enum)
            if resolved_job:
                resolved.append(resolved_job)

        return resolved

    def _parse_strategy(self, strategy: str) -> DuplicateStrategy:
        """Parse strategy string to enum."""
        try:
            return DuplicateStrategy(strategy)
        except ValueError:
            logger.warning(f"Unknown strategy '{strategy}', using default")
            return DuplicateStrategy.KEEP_NEWEST

    def _resolve_job_group(self, jobs: List[Dict[str, Any]], strategy: DuplicateStrategy) -> Optional[Dict[str, Any]]:
        """Resolve a single group of duplicate jobs."""
        if not jobs:
            return None

        if strategy == DuplicateStrategy.KEEP_NEWEST:
            return max(jobs, key=lambda j: j.get('updated_at', datetime.min))
        elif strategy == DuplicateStrategy.KEEP_OLDEST:
            return min(jobs, key=lambda j: j.get('created_at', datetime.max))
        elif strategy == DuplicateStrategy.MERGE:
            merged_job = jobs[0].copy()
            merged_job['merged_from'] = [j.get('job_id') for j in jobs[1:]]
            merged_job['merge_count'] = len(jobs)
            return merged_job
        else:  # KEEP_FIRST
            return jobs[0]

    async def check_application_allowed(
        self,
        user_id: int,
        job_id: str,
        existing_applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if application is allowed (not a duplicate).
        GREEN PHASE: Simple duplicate check.
        """
        if not existing_applications:
            return {'allowed': True}

        for app in existing_applications:
            if app.get('user_id') == user_id and app.get('job_id') == job_id:
                return {
                    'allowed': False,
                    'reason': 'Duplicate application detected',
                    'previous_application_date': app.get('applied_at')
                }

        return {'allowed': True}

    async def check_company_application_allowed(
        self,
        user_id: int,
        company_cd: str,
        time_window_days: int = 14,
        existing_applications: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if application to company is allowed within time window.
        GREEN PHASE: Basic time window enforcement.
        """
        if not existing_applications:
            return {'allowed': True}

        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        for app in existing_applications:
            if (app.get('user_id') == user_id and
                app.get('endcl_cd') == company_cd and
                app.get('applied_at') > cutoff_date):

                retry_date = app.get('applied_at') + timedelta(days=time_window_days)
                return {
                    'allowed': False,
                    'reason': 'Recent application to same company',
                    'retry_after_date': retry_date
                }

        return {'allowed': True}

    async def check_job_creation_allowed(
        self,
        new_job: Dict[str, Any],
        existing_jobs: List[Dict[str, Any]],
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check if job creation is allowed (not a duplicate).

        Args:
            new_job: Job to check for duplicates
            existing_jobs: List of existing jobs to compare against
            similarity_threshold: Custom threshold (defaults to config)

        Returns:
            Dict containing allowed status and details
        """
        threshold = similarity_threshold or self.config.HIGH_SIMILARITY_THRESHOLD

        for existing_job in existing_jobs:
            similarity_score = self._calculate_job_similarity(new_job, existing_job)
            if similarity_score > threshold:
                return {
                    'allowed': False,
                    'duplicate_job_id': existing_job.get('job_id'),
                    'similarity_score': similarity_score,
                    'threshold_used': threshold
                }

        return {'allowed': True, 'max_similarity': max(
            [self._calculate_job_similarity(new_job, job) for job in existing_jobs],
            default=0.0
        )}

    def _calculate_job_similarity(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> float:
        """
        Calculate weighted similarity between two jobs.

        Uses configurable weights for different job attributes:
        - Company: 30%
        - Title: 25%
        - Location: 20%
        - Salary: 15%
        - Employment type: 10%

        Args:
            job1: First job to compare
            job2: Second job to compare

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not job1 or not job2:
            return 0.0

        weighted_score = 0.0

        # Company similarity
        company_match = self._compare_field(job1.get('endcl_cd'), job2.get('endcl_cd'))
        weighted_score += company_match * self.config.COMPANY_WEIGHT

        # Title similarity
        title_match = self._compare_field(job1.get('application_name'), job2.get('application_name'))
        weighted_score += title_match * self.config.TITLE_WEIGHT

        # Location similarity
        location_match = self._compare_field(job1.get('location_pref_cd'), job2.get('location_pref_cd'))
        weighted_score += location_match * self.config.LOCATION_WEIGHT

        # Salary similarity
        salary_match = self._compare_salary_range(job1, job2)
        weighted_score += salary_match * self.config.SALARY_WEIGHT

        # Employment type similarity
        employment_match = self._compare_field(job1.get('employment_type_cd'), job2.get('employment_type_cd'))
        weighted_score += employment_match * self.config.EMPLOYMENT_TYPE_WEIGHT

        return min(weighted_score, 1.0)  # Cap at 1.0

    def _compare_field(self, value1: Any, value2: Any) -> float:
        """Compare two field values."""
        if value1 is None or value2 is None:
            return 0.0
        return 1.0 if value1 == value2 else 0.0

    def _compare_salary_range(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> float:
        """Compare salary ranges with tolerance for minor differences."""
        min1, max1 = job1.get('salary_min'), job1.get('salary_max')
        min2, max2 = job2.get('salary_min'), job2.get('salary_max')

        if any(val is None for val in [min1, max1, min2, max2]):
            return 0.0

        # Calculate overlap percentage
        overlap_start = max(min1, min2)
        overlap_end = min(max1, max2)

        if overlap_start > overlap_end:
            return 0.0  # No overlap

        overlap_size = overlap_end - overlap_start
        range1_size = max1 - min1
        range2_size = max2 - min2

        if range1_size == 0 or range2_size == 0:
            return 1.0 if min1 == min2 and max1 == max2 else 0.0

        # Return average overlap ratio
        overlap_ratio = overlap_size / ((range1_size + range2_size) / 2)
        return min(overlap_ratio, 1.0)

    async def get_user_applications(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user applications from database.

        Args:
            user_id: User ID to fetch applications for
            limit: Maximum number of applications to return

        Returns:
            List of user applications ordered by applied_at DESC
        """
        if not self.db:
            # For testing without database
            return []

        query_limit = min(
            limit or self.config.MAX_APPLICATIONS_QUERY,
            self.config.MAX_APPLICATIONS_QUERY
        )

        query = """
            SELECT user_id, job_id, endcl_cd, applied_at, created_at
            FROM user_applications
            WHERE user_id = :user_id
            ORDER BY applied_at DESC
            LIMIT :limit
        """

        try:
            from sqlalchemy import text
            result = await self.db.execute(text(query), {
                "user_id": user_id,
                "limit": query_limit
            })
            rows = result.fetchall()

            applications = []
            for row in rows:
                applications.append({
                    'user_id': row.user_id,
                    'job_id': row.job_id,
                    'endcl_cd': row.endcl_cd,
                    'applied_at': row.applied_at,
                    'created_at': row.created_at
                })

            logger.debug(f"Retrieved {len(applications)} applications for user {user_id}")
            return applications

        except Exception as e:
            logger.error(f"Error fetching user applications for user {user_id}: {e}")
            raise

    async def get_recent_company_applications(
        self,
        user_id: int,
        days: int = None
    ) -> Set[str]:
        """
        Get companies user applied to within specified days.

        Args:
            user_id: User ID to check
            days: Number of days to look back (defaults to configured window)

        Returns:
            Set of company codes (endcl_cd) with recent applications
        """
        days = days or self.window_days
        cutoff_date = datetime.now() - timedelta(days=days)

        if not self.db:
            # For testing without database
            return set()

        query = """
            SELECT DISTINCT endcl_cd
            FROM user_applications
            WHERE user_id = :user_id
            AND applied_at > :cutoff_date
            AND endcl_cd IS NOT NULL
            LIMIT :limit
        """

        try:
            from sqlalchemy import text
            result = await self.db.execute(text(query), {
                "user_id": user_id,
                "cutoff_date": cutoff_date,
                "limit": self.config.MAX_COMPANIES_QUERY
            })
            rows = result.fetchall()

            excluded_companies = {row.endcl_cd for row in rows if row.endcl_cd}

            logger.debug(
                f"Found {len(excluded_companies)} companies with recent applications "
                f"for user {user_id} in last {days} days"
            )

            return excluded_companies

        except Exception as e:
            logger.error(f"Error fetching recent company applications for user {user_id}: {e}")
            raise

    async def filter_jobs_exclude_recent_companies(
        self,
        jobs: List[Dict[str, Any]],
        user_id: int,
        exclusion_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs to exclude companies user applied to recently.

        Args:
            jobs: List of jobs to filter
            user_id: User ID to check applications for
            exclusion_days: Days to look back (defaults to configured window)

        Returns:
            Filtered list of jobs excluding recent company applications
        """
        if not jobs:
            return []

        exclusion_days = exclusion_days or self.window_days

        try:
            # Get companies to exclude
            excluded_companies = await self.get_recent_company_applications(user_id, exclusion_days)

            if not excluded_companies:
                logger.debug(f"No recent companies to exclude for user {user_id}")
                return jobs

            # Filter jobs
            filtered_jobs = []
            excluded_count = 0

            for job in jobs:
                job_company = job.get('endcl_cd')
                if job_company and job_company in excluded_companies:
                    excluded_count += 1
                    logger.debug(f"Excluding job {job.get('job_id')} from company {job_company}")
                else:
                    filtered_jobs.append(job)

            logger.info(
                f"Filtered {len(jobs)} jobs -> {len(filtered_jobs)} jobs "
                f"(excluded {excluded_count} from {len(excluded_companies)} companies)"
            )

            return filtered_jobs

        except Exception as e:
            logger.error(f"Error filtering jobs by recent companies for user {user_id}: {e}")
            # Return original jobs if filtering fails (failsafe)
            return jobs
