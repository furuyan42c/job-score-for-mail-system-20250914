#!/usr/bin/env python3
"""
T025: Duplicate Control Service

Prevents duplicate job recommendations by filtering jobs from companies
where the user has recently applied within a configurable time window.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.job import Job

logger = logging.getLogger(__name__)


class DuplicateControlService:
    """Service for filtering duplicate job recommendations."""

    # Configuration constants
    DEFAULT_WINDOW_DAYS = 14
    MIN_WINDOW_DAYS = 1
    MAX_WINDOW_DAYS = 90

    def __init__(self, db=None, window_days: int = DEFAULT_WINDOW_DAYS):
        """
        Initialize duplicate control service.

        Args:
            db: Database session (optional for testing)
            window_days: Number of days to check for duplicates (default: 14)
        """
        self.db = db

        # Validate window_days parameter
        if window_days < self.MIN_WINDOW_DAYS:
            logger.warning(
                "Window days %d is below minimum (%d), using minimum",
                window_days,
                self.MIN_WINDOW_DAYS,
            )
            window_days = self.MIN_WINDOW_DAYS
        elif window_days > self.MAX_WINDOW_DAYS:
            logger.warning(
                "Window days %d exceeds maximum (%d), using maximum",
                window_days,
                self.MAX_WINDOW_DAYS,
            )
            window_days = self.MAX_WINDOW_DAYS

        self.window_days = window_days
        logger.info("DuplicateControlService initialized with %d day window", self.window_days)

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
        strategy: str = 'keep_newest'
    ) -> List[Dict[str, Any]]:
        """
        Resolve duplicates using specified strategy.
        GREEN PHASE: Basic implementation for keep_newest and keep_oldest.
        """
        resolved = []

        for group in duplicate_groups:
            jobs = group.get('jobs', [])
            if not jobs:
                continue

            if strategy == 'keep_newest':
                # Keep job with most recent updated_at
                newest_job = max(jobs, key=lambda j: j.get('updated_at', datetime.min))
                resolved.append(newest_job)
            elif strategy == 'keep_oldest':
                # Keep job with oldest created_at
                oldest_job = min(jobs, key=lambda j: j.get('created_at', datetime.max))
                resolved.append(oldest_job)
            elif strategy == 'merge':
                # Simple merge - keep first job and mark as merged
                merged_job = jobs[0].copy()
                merged_job['merged_from'] = [j.get('job_id') for j in jobs[1:]]
                resolved.append(merged_job)
            else:
                # Default: keep first job
                resolved.append(jobs[0])

        return resolved

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
        existing_jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if job creation is allowed (not a duplicate).
        GREEN PHASE: Simple field comparison.
        """
        for existing_job in existing_jobs:
            similarity_score = self._calculate_job_similarity(new_job, existing_job)
            if similarity_score > 0.8:
                return {
                    'allowed': False,
                    'duplicate_job_id': existing_job.get('job_id'),
                    'similarity_score': similarity_score
                }

        return {'allowed': True}

    def _calculate_job_similarity(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two jobs.
        GREEN PHASE: Simple field matching.
        """
        if not job1 or not job2:
            return 0.0

        matches = 0
        total_fields = 0

        # Check key fields
        fields_to_check = ['endcl_cd', 'application_name', 'location_pref_cd', 'salary_min', 'salary_max']

        for field in fields_to_check:
            total_fields += 1
            if job1.get(field) == job2.get(field):
                matches += 1

        return matches / total_fields if total_fields > 0 else 0.0

    async def get_user_applications(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user applications from database.
        GREEN PHASE: Simple query.
        """
        if not self.db:
            # For testing without database
            return []

        query = """
            SELECT user_id, job_id, endcl_cd, applied_at, created_at
            FROM user_applications
            WHERE user_id = :user_id
            ORDER BY applied_at DESC
        """

        try:
            from sqlalchemy import text
            result = await self.db.execute(text(query), {"user_id": user_id})
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

            return applications
        except Exception as e:
            logger.error(f"Error fetching user applications: {e}")
            raise
