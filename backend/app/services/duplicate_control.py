#!/usr/bin/env python3
"""
T025: Duplicate Control Service

Prevents duplicate job recommendations by filtering jobs from companies
where the user has recently applied within a configurable time window.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.job import Job

logger = logging.getLogger(__name__)

class DuplicateControlService:
    """Service for filtering duplicate job recommendations."""

    # Configuration constants
    DEFAULT_WINDOW_DAYS = 14
    MIN_WINDOW_DAYS = 1
    MAX_WINDOW_DAYS = 90

    def __init__(self, window_days: int = DEFAULT_WINDOW_DAYS):
        """
        Initialize duplicate control service.

        Args:
            window_days: Number of days to check for duplicates (default: 14)
        """
        # Validate window_days parameter
        if window_days < self.MIN_WINDOW_DAYS:
            logger.warning("Window days %d is below minimum (%d), using minimum",
                         window_days, self.MIN_WINDOW_DAYS)
            window_days = self.MIN_WINDOW_DAYS
        elif window_days > self.MAX_WINDOW_DAYS:
            logger.warning("Window days %d exceeds maximum (%d), using maximum",
                         window_days, self.MAX_WINDOW_DAYS)
            window_days = self.MAX_WINDOW_DAYS

        self.window_days = window_days
        logger.info("DuplicateControlService initialized with %d day window", self.window_days)

    async def filter_duplicates(self, jobs: List[Job], applications: List[Dict[str, Any]]) -> List[Job]:
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
            logger.debug("No application history provided, returning all %d jobs", len(jobs) if jobs else 0)
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
                        applied_at = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError) as e:
                        logger.warning("Invalid timestamp format: %s", applied_at)
                        continue

                # Check if application is within window
                if applied_at >= cutoff_date:
                    recent_company_ids.add(company_id)
                    days_ago = (now - applied_at).days
                    logger.debug("Found recent application to company %s (%d days ago)",
                               company_id, days_ago)

            logger.info("Identified %d companies with applications in last %d days",
                       len(recent_company_ids), self.window_days)

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
                    logger.debug("Filtering job %s from recently applied company %s",
                               getattr(job, "job_id", "unknown"), job_company_id)

            logger.info("Filtered %d duplicate jobs, returning %d unique jobs",
                       filtered_count, len(filtered_jobs))
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
                        applied_at = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        continue

                if applied_at >= cutoff_date:
                    recent_companies.append(company_id)

            return recent_companies

        except Exception as e:
            logger.error("Error getting recent companies: %s", e)
            return []
