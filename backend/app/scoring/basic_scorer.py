"""
Basic Scorer - Stage 1 of 3-stage scoring system.
Handles location and category matching with simple rule-based scoring.
"""
from typing import Dict, Any, List
import re


class BasicScorer:
    """Basic scorer for location and category matching."""

    def __init__(self):
        """Initialize BasicScorer."""
        pass

    def score_location(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Score job location against user preferences.

        Args:
            job_data: Job information containing location
            user_preferences: User preferences containing preferred_location

        Returns:
            Score between 0.0 and 1.0
        """
        job_location = job_data.get("location", "").lower().strip()
        preferred_location = user_preferences.get("preferred_location", "").lower().strip()

        if not job_location or not preferred_location:
            return 0.0

        # Exact match
        if job_location == preferred_location:
            return 1.0

        # Partial match - check if preferred location is contained in job location
        if preferred_location in job_location or job_location in preferred_location:
            return 0.6

        # City name extraction and comparison
        job_city = job_location.split(",")[0].strip()
        preferred_city = preferred_location.split(",")[0].strip()

        if job_city == preferred_city:
            return 0.8

        return 0.0

    def score_category(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Score job category against user preferences.

        Args:
            job_data: Job information containing category
            user_preferences: User preferences containing preferred_categories

        Returns:
            Score between 0.0 and 1.0
        """
        job_category = job_data.get("category", "").lower().strip()
        preferred_categories = user_preferences.get("preferred_categories", [])

        if not job_category or not preferred_categories:
            return 0.0

        # Normalize preferred categories to lowercase
        preferred_categories_lower = [cat.lower().strip() for cat in preferred_categories]

        # Exact match
        if job_category in preferred_categories_lower:
            return 1.0

        # Partial match - check if any preferred category is contained in job category
        for preferred_cat in preferred_categories_lower:
            if preferred_cat in job_category or job_category in preferred_cat:
                return 0.7

        return 0.0

    def calculate_score(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Calculate overall basic score combining location and category.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            Combined score between 0.0 and 1.0
        """
        location_score = self.score_location(job_data, user_preferences)
        category_score = self.score_category(job_data, user_preferences)

        # Weight location and category equally
        return (location_score + category_score) / 2.0