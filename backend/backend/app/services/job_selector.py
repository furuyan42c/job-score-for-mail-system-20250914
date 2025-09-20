#!/usr/bin/env python3
"""
T024: Job Selector Service

Provides job selection algorithms for different email sections.
Implements editorial picks, top-rated, and personalized selection strategies.
"""
import logging
from typing import List, Dict, Optional
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)

class JobSelectorService:
    """Service for selecting jobs for different email sections."""

    # Selection limits for each section
    SECTION_LIMITS = {
        "editorial_picks": 5,
        "top5": 5,
        "recommended": 5,
        "new_arrivals": 5,
        "popular": 5,
        "personalized": 5
    }

    # Scoring weights
    EDITORIAL_FEE_WEIGHT = 1.0
    EDITORIAL_CLICKS_WEIGHT = 1.0

    def __init__(self):
        """Initialize job selector service."""
        self.section_limits = self.SECTION_LIMITS.copy()
        logger.info("JobSelectorService initialized with section limits: %s", self.section_limits)

    async def select_editorial_picks(self, jobs: List[Job], user: User) -> List[Job]:
        """
        Select editorial picks based on fee and click metrics.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            List of selected editorial pick jobs
        """
        if not jobs:
            logger.debug("No jobs available for editorial picks")
            return []

        try:
            # Calculate composite scores for editorial selection
            scored_jobs = []

            for job in jobs:
                # Skip jobs without required metrics
                if not hasattr(job, "fee") or not hasattr(job, "application_clicks"):
                    continue

                fee = getattr(job, "fee", 0) or 0
                clicks = getattr(job, "application_clicks", 0) or 0

                # Calculate editorial score (fee * clicks as business value metric)
                editorial_score = (fee * self.EDITORIAL_FEE_WEIGHT) * (clicks * self.EDITORIAL_CLICKS_WEIGHT)
                scored_jobs.append((job, editorial_score))

            # Sort by score and select top N
            scored_jobs.sort(key=lambda x: x[1], reverse=True)
            selected = [job for job, score in scored_jobs[:self.section_limits["editorial_picks"]]]

            logger.info("Selected %d editorial picks from %d candidates", len(selected), len(jobs))
            return selected

        except Exception as e:
            logger.error("Error selecting editorial picks: %s", e)
            return []

    async def select_top5(self, jobs: List[Job], user: User) -> List[Job]:
        """
        Select top 5 jobs based on basic scoring.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            List of top 5 jobs
        """
        if not jobs:
            logger.debug("No jobs available for top5 selection")
            return []

        try:
            # Sort by basic score
            jobs_with_scores = []

            for job in jobs:
                score = getattr(job, "basic_score", 0)
                jobs_with_scores.append((job, score))

            # Sort and select top N
            jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
            selected = [job for job, score in jobs_with_scores[:self.section_limits["top5"]]]

            logger.info("Selected %d top5 jobs from %d candidates", len(selected), len(jobs))
            return selected

        except Exception as e:
            logger.error("Error selecting top5 jobs: %s", e)
            return []

    async def select_all_sections(self, jobs: List[Job], user: User) -> Dict[str, List[Job]]:
        """
        Select jobs for all email sections with no duplicates between sections.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            Dictionary mapping section names to job lists
        """
        if not jobs:
            logger.warning("No jobs available for section selection")
            return {section: [] for section in self.section_limits.keys()}

        try:
            used_job_ids = set()
            sections = {}

            # 1. Editorial picks (highest priority)
            editorial = await self.select_editorial_picks(jobs, user)
            sections["editorial_picks"] = editorial
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in editorial)
            logger.debug("Editorial picks selected: %d jobs", len(editorial))

            # 2. Top 5 (from remaining jobs)
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            top5 = await self.select_top5(remaining, user)
            sections["top5"] = top5
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in top5)
            logger.debug("Top5 selected: %d jobs from %d remaining", len(top5), len(remaining))

            # 3. Other sections (simplified selection from remaining)
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]

            # Recommended section
            recommended_limit = self.section_limits["recommended"]
            sections["recommended"] = remaining[:recommended_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["recommended"])

            # New arrivals section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            new_arrivals_limit = self.section_limits["new_arrivals"]
            sections["new_arrivals"] = remaining[:new_arrivals_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["new_arrivals"])

            # Popular section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            popular_limit = self.section_limits["popular"]
            sections["popular"] = remaining[:popular_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["popular"])

            # Personalized section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            personalized_limit = self.section_limits["personalized"]
            sections["personalized"] = remaining[:personalized_limit]

            # Log section statistics
            total_selected = sum(len(jobs) for jobs in sections.values())
            logger.info("Selected %d unique jobs across %d sections from %d candidates",
                       total_selected, len(sections), len(jobs))

            for section_name, section_jobs in sections.items():
                logger.debug("Section '%s': %d jobs", section_name, len(section_jobs))

            return sections

        except Exception as e:
            logger.error("Error selecting all sections: %s", e)
            return {section: [] for section in self.section_limits.keys()}
