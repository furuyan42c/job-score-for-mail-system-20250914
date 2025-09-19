"""
T021 - 3-stage scoring service implementation.
Orchestrates basic, keyword, and AI scoring for comprehensive job matching.

This service implements a weighted scoring system that combines:
1. Basic scoring: Location and category matching
2. Keyword scoring: Skills and requirements matching
3. AI scoring: Semantic analysis (optional)

The service supports batch processing and configurable weights.
"""
from typing import Dict, Any, List, Optional
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from app.scoring.basic_scorer import BasicScorer
from app.scoring.keyword_scorer import KeywordScorer
from app.scoring.ai_scorer import AIScorer

logger = logging.getLogger(__name__)


class ScoringService:
    """Service that orchestrates 3-stage scoring system."""

    def __init__(self, weights: Optional[Dict[str, float]] = None, ai_api_key: Optional[str] = None):
        """
        Initialize ScoringService with optional custom weights and AI configuration.

        Args:
            weights: Custom weights for each scoring stage
            ai_api_key: OpenAI API key for AI scoring (optional)
        """
        # Initialize scoring components
        self.basic_scorer = BasicScorer()
        self.keyword_scorer = KeywordScorer()
        self.ai_scorer = AIScorer(api_key=ai_api_key)

        # Set default weights
        default_weights = {
            "basic_weight": 0.4,
            "keyword_weight": 0.4,
            "ai_weight": 0.2
        }

        if weights:
            # Validate weights
            self._validate_weights(weights)
            self.weights = weights
        else:
            self.weights = default_weights

        # Performance tracking
        self.score_cache = {}  # Simple in-memory cache
        self.performance_metrics = {
            "total_scores_calculated": 0,
            "total_time_spent": 0.0,
            "cache_hits": 0
        }

    def _validate_weights(self, weights: Dict[str, float]) -> None:
        """
        Validate that weights are valid.

        Args:
            weights: Weights to validate

        Raises:
            ValueError: If weights are invalid
        """
        required_keys = {"basic_weight", "keyword_weight", "ai_weight"}
        if not all(key in weights for key in required_keys):
            raise ValueError(f"Missing weight keys. Required: {required_keys}")

        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Weights cannot be negative")

        logger.info(f"Weights validated: {weights}")

    def calculate_composite_score(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Calculate composite score from all three stages.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            Weighted composite score between 0.0 and 1.0
        """
        # Get individual stage scores
        basic_score = self.basic_scorer.calculate_score(job_data, user_preferences)
        keyword_score = self.keyword_scorer.calculate_score(job_data, user_preferences)
        ai_score = self.ai_scorer.calculate_score(job_data, user_preferences)

        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(job_data, user_preferences)
        if cache_key in self.score_cache:
            self.performance_metrics["cache_hits"] += 1
            return self.score_cache[cache_key]

        try:
            # Calculate weighted composite score
            composite_score = (
                basic_score * self.weights["basic_weight"] +
                keyword_score * self.weights["keyword_weight"] +
                ai_score * self.weights["ai_weight"]
            )

            # Cache the result
            self.score_cache[cache_key] = composite_score

            # Update performance metrics
            self.performance_metrics["total_scores_calculated"] += 1
            self.performance_metrics["total_time_spent"] += time.time() - start_time

            return composite_score

        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            # Return a reasonable fallback score
            return (basic_score + keyword_score) / 2.0  # Exclude AI score on error

    def get_stage_scores(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, float]:
        """
        Get individual scores from each stage.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            Dictionary containing scores from each stage
        """
        return {
            "basic_score": self.basic_scorer.calculate_score(job_data, user_preferences),
            "keyword_score": self.keyword_scorer.calculate_score(job_data, user_preferences),
            "ai_score": self.ai_scorer.calculate_score(job_data, user_preferences)
        }

    def score_jobs_batch(self, jobs: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score multiple jobs for a single user.

        Args:
            jobs: List of job dictionaries
            user_preferences: User preferences

        Returns:
            List of scoring results
        """
        results = []

        for job in jobs:
            composite_score = self.calculate_composite_score(job, user_preferences)
            stage_scores = self.get_stage_scores(job, user_preferences)

            result = {
                "job_id": job.get("id", job.get("job_id")),
                "composite_score": composite_score,
                "stage_scores": stage_scores
            }
            results.append(result)

        return results

    def _generate_cache_key(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """
        Generate a cache key for the scoring request.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            Cache key string
        """
        # Simple cache key based on relevant fields
        job_key = f"{job_data.get('title', '')}-{job_data.get('location', '')}-{job_data.get('category', '')}"
        user_key = f"{'-'.join(user_preferences.get('skills', []))}-{user_preferences.get('preferred_location', '')}"
        return f"{hash(job_key)}-{hash(user_key)}"

    def clear_cache(self) -> None:
        """Clear the scoring cache."""
        self.score_cache.clear()
        logger.info("Scoring cache cleared")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the scoring service.

        Returns:
            Dictionary containing performance metrics
        """
        metrics = self.performance_metrics.copy()
        if metrics["total_scores_calculated"] > 0:
            metrics["average_time_per_score"] = metrics["total_time_spent"] / metrics["total_scores_calculated"]
        else:
            metrics["average_time_per_score"] = 0.0

        metrics["cache_hit_rate"] = (
            metrics["cache_hits"] / max(metrics["total_scores_calculated"], 1)
        )
        return metrics