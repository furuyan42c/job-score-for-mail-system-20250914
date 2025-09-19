"""
T021 - 3-stage scoring service implementation.
Simple implementation that orchestrates basic, keyword, and AI scoring.
"""
from typing import Dict, Any, List, Optional
from app.scoring.basic_scorer import BasicScorer
from app.scoring.keyword_scorer import KeywordScorer
from app.scoring.ai_scorer import AIScorer


class ScoringService:
    """Service that orchestrates 3-stage scoring system."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize ScoringService with optional custom weights.

        Args:
            weights: Custom weights for each scoring stage
        """
        # Initialize scoring components
        self.basic_scorer = BasicScorer()
        self.keyword_scorer = KeywordScorer()
        self.ai_scorer = AIScorer()

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

        # Calculate weighted composite score
        composite_score = (
            basic_score * self.weights["basic_weight"] +
            keyword_score * self.weights["keyword_weight"] +
            ai_score * self.weights["ai_weight"]
        )

        return composite_score

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