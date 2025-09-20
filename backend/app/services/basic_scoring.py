#!/usr/bin/env python3
"""
T021: Basic Scoring Service

Provides basic scoring functionality for job listings including:
- Fee-based scoring
- Hourly wage scoring
- Company popularity scoring
"""

import logging
from typing import Optional

from app.models.job import Job

logger = logging.getLogger(__name__)


class BasicScoringService:
    """Service for calculating basic job scores."""

    # Default configuration
    FEE_THRESHOLD = 1000
    WAGE_THRESHOLD = 1500
    MAX_SCORE = 100.0
    Z_SCORE_WEIGHT = 0.8

    def __init__(self):
        """Initialize basic scoring service."""
        self.fee_threshold = self.FEE_THRESHOLD
        self.wage_threshold = self.WAGE_THRESHOLD
        logger.info("BasicScoringService initialized")

    async def calculate_fee_score(self, job: Job) -> float:
        """
        Calculate score based on job fee.

        Args:
            job: Job object containing fee information

        Returns:
            Score between 0 and 100 based on fee
        """
        try:
            fee = getattr(job, "fee", None)

            if not fee or fee <= self.fee_threshold:
                return 0.0

            # Linear scaling from threshold to max
            score = min(((fee - self.fee_threshold) / 10000) * self.MAX_SCORE, self.MAX_SCORE)

            logger.debug(
                f"Fee score for job {getattr(job, 'job_id', 'unknown')}: {score:.2f} (fee: {fee})"
            )
            return score

        except Exception as e:
            logger.error(f"Error calculating fee score: {e}")
            return 0.0

    async def calculate_hourly_wage_score(self, job: Job) -> float:
        """
        Calculate score based on hourly wage.

        Args:
            job: Job object containing hourly wage information

        Returns:
            Score between 0 and 100 based on hourly wage
        """
        try:
            hourly_wage = getattr(job, "hourly_wage", None)

            if not hourly_wage or hourly_wage <= self.wage_threshold:
                return 0.0

            # Linear scaling from threshold to max
            score = min(
                ((hourly_wage - self.wage_threshold) / 3500) * self.MAX_SCORE, self.MAX_SCORE
            )

            logger.debug(
                f"Wage score for job {getattr(job, 'job_id', 'unknown')}: {score:.2f} (wage: {hourly_wage})"
            )
            return score

        except Exception as e:
            logger.error(f"Error calculating hourly wage score: {e}")
            return 0.0

    async def calculate_company_popularity_score(
        self, job: Job, mean_applications: float, std_applications: float
    ) -> float:
        """
        Calculate score based on company popularity using Z-score normalization.

        Args:
            job: Job object containing application clicks
            mean_applications: Mean number of applications across all jobs
            std_applications: Standard deviation of applications

        Returns:
            Score between 0 and 100 based on normalized popularity
        """
        try:
            application_clicks = getattr(job, "application_clicks", None)

            if application_clicks is None or application_clicks <= 0:
                return 0.0

            # Handle edge case where std is 0
            if std_applications == 0:
                return 50.0  # Return middle score if no variation

            # Calculate Z-score
            z_score = (application_clicks - mean_applications) / std_applications

            # Convert Z-score to 0-100 scale
            # Z-score typically ranges from -3 to 3, map to 0-100
            normalized_score = ((z_score + 3) / 6) * self.MAX_SCORE

            # Apply weight and clamp to valid range
            score = max(0.0, min(self.MAX_SCORE, normalized_score * self.Z_SCORE_WEIGHT))

            logger.debug(
                f"Popularity score for job {getattr(job, 'job_id', 'unknown')}: {score:.2f} "
                f"(clicks: {application_clicks}, z-score: {z_score:.2f})"
            )
            return score

        except Exception as e:
            logger.error(f"Error calculating company popularity score: {e}")
            return 0.0

    async def calculate_combined_score(
        self, job: Job, mean_applications: float = 100, std_applications: float = 50
    ) -> float:
        """
        Calculate combined basic score for a job.

        Args:
            job: Job object to score
            mean_applications: Mean number of applications
            std_applications: Standard deviation of applications

        Returns:
            Combined score between 0 and 100
        """
        try:
            # Calculate individual scores
            fee_score = await self.calculate_fee_score(job)
            wage_score = await self.calculate_hourly_wage_score(job)
            popularity_score = await self.calculate_company_popularity_score(
                job, mean_applications, std_applications
            )

            # Weight the scores (can be adjusted)
            weights = {"fee": 0.4, "wage": 0.3, "popularity": 0.3}

            combined = (
                fee_score * weights["fee"]
                + wage_score * weights["wage"]
                + popularity_score * weights["popularity"]
            )

            score = min(self.MAX_SCORE, combined)

            logger.info(
                f"Combined basic score for job {getattr(job, 'job_id', 'unknown')}: {score:.2f} "
                f"(fee: {fee_score:.2f}, wage: {wage_score:.2f}, popularity: {popularity_score:.2f})"
            )

            return score

        except Exception as e:
            logger.error(f"Error calculating combined score: {e}")
            return 0.0
