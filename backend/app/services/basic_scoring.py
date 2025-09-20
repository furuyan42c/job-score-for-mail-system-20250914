#!/usr/bin/env python3
"""
T021: Basic Scoring Service (GREEN Phase)
Implements fee, hourly_wage, and company_popularity scoring
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from app.models.job import Job

logger = logging.getLogger(__name__)


class BasicScoringService:
    """Service for calculating basic job scoring components"""

    def __init__(self):
        """Initialize the basic scoring service"""
        self.fee_threshold = 500
        self.wage_weight = 0.3
        self.fee_weight = 0.4
        self.popularity_weight = 0.3

    async def calculate_fee_score(self, job: Job) -> float:
        """
        Calculate fee score (fee > 500 check)

        Args:
            job: Job object with fee information

        Returns:
            Score from 0 to 100
        """
        if not job.fee or job.fee <= self.fee_threshold:
            return 0.0

        # Linear scaling from 500 to 1000+
        # 600 -> 80, 700 -> 85, 800 -> 90, 900 -> 95, 1000+ -> 100
        normalized_fee = min((job.fee - self.fee_threshold) / 500, 1.0)
        score = 80 + (normalized_fee * 20)

        return min(score, 100.0)

    async def calculate_hourly_wage_score(
        self,
        job: Job,
        area_stats: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate hourly wage score using Z-score normalization

        Args:
            job: Job object with hourly_wage
            area_stats: Area statistics (mean, std_dev, prefecture_cd)

        Returns:
            Score from 0 to 100
        """
        if not job.hourly_wage:
            return 0.0

        if not area_stats:
            # Fallback to simple normalization
            # Assume typical wage range 1000-5000
            normalized = min((job.hourly_wage - 1000) / 4000, 1.0)
            return max(0, normalized * 100)

        mean = area_stats.get("mean", 2000)
        std_dev = area_stats.get("std_dev", 500)

        # Handle edge case of zero standard deviation
        if std_dev == 0:
            return 50.0

        # Calculate Z-score
        z_score = (job.hourly_wage - mean) / std_dev

        # Convert Z-score to 0-100 scale
        # Z-score of -2 -> 0, 0 -> 50, +2 -> 100
        score = 50 + (z_score * 25)

        return max(0, min(score, 100))

    async def calculate_company_popularity_score(
        self,
        company_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate company popularity based on 360-day metrics

        Args:
            company_data: Dictionary with application_count_360d and view_count_360d

        Returns:
            Score from 0 to 100
        """
        if not company_data:
            return 0.0

        applications = company_data.get("application_count_360d", 0)
        views = company_data.get("view_count_360d", 0)

        # Weight applications more heavily (70/30 split)
        application_weight = 0.7
        view_weight = 0.3

        # Normalize applications (assume 0-2000 range)
        app_score = min(applications / 1000, 1.0) * 100

        # Normalize views (assume 0-10000 range)
        view_score = min(views / 5000, 1.0) * 100

        # Weighted average
        total_score = (app_score * application_weight) + (view_score * view_weight)

        return min(total_score, 100.0)

    async def calculate_basic_score(
        self,
        job: Job,
        area_stats: Optional[Dict[str, Any]] = None,
        company_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Calculate combined basic score from all components

        Args:
            job: Job object
            area_stats: Area wage statistics
            company_data: Company popularity data

        Returns:
            Dictionary with individual scores and total
        """
        # Calculate individual scores
        fee_score = await self.calculate_fee_score(job)
        hourly_wage_score = await self.calculate_hourly_wage_score(job, area_stats)
        company_popularity_score = await self.calculate_company_popularity_score(company_data)

        # Calculate weighted total
        total_basic_score = (
            fee_score * self.fee_weight +
            hourly_wage_score * self.wage_weight +
            company_popularity_score * self.popularity_weight
        )

        return {
            "fee_score": fee_score,
            "hourly_wage_score": hourly_wage_score,
            "company_popularity_score": company_popularity_score,
            "total_basic_score": total_basic_score
        }