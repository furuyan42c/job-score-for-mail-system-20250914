"""
Score Aggregator - Advanced aggregation strategies for scoring system.
Provides various mathematical aggregation methods beyond simple weighted averages.
"""
from typing import Dict, List, Any, Union
import math
import statistics


class ScoreAggregator:
    """Advanced score aggregation strategies."""

    def __init__(self):
        """Initialize ScoreAggregator."""
        pass

    def weighted_average(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """
        Calculate weighted average of scores.

        Args:
            scores: Dictionary of score name -> score value
            weights: Dictionary of score name -> weight value

        Returns:
            Weighted average score
        """
        total_weighted_score = 0.0
        total_weight = 0.0

        for score_name, score_value in scores.items():
            weight_key = f"{score_name.replace('_score', '')}_weight"
            if weight_key in weights:
                weight = weights[weight_key]
                total_weighted_score += score_value * weight
                total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def harmonic_mean(self, scores: List[float]) -> float:
        """
        Calculate harmonic mean of scores.
        Good for cases where all scores should be reasonably high.

        Args:
            scores: List of score values

        Returns:
            Harmonic mean
        """
        if not scores or any(score <= 0 for score in scores):
            return 0.0

        return len(scores) / sum(1.0 / score for score in scores)

    def geometric_mean(self, scores: List[float]) -> float:
        """
        Calculate geometric mean of scores.
        Good for multiplicative processes.

        Args:
            scores: List of score values

        Returns:
            Geometric mean
        """
        if not scores or any(score <= 0 for score in scores):
            return 0.0

        product = 1.0
        for score in scores:
            product *= score

        return product ** (1.0 / len(scores))

    def power_mean(self, scores: List[float], power: float = 2.0) -> float:
        """
        Calculate power mean (generalized mean) of scores.

        Args:
            scores: List of score values
            power: Power parameter (2.0 = quadratic mean)

        Returns:
            Power mean
        """
        if not scores:
            return 0.0

        return (sum(score ** power for score in scores) / len(scores)) ** (1.0 / power)

    def percentile_aggregate(self, scores: List[float], percentile: float = 50) -> float:
        """
        Aggregate using percentile strategy.

        Args:
            scores: List of score values
            percentile: Percentile to use (0-100)

        Returns:
            Percentile value
        """
        if not scores:
            return 0.0

        return statistics.quantiles(scores, n=100)[int(percentile) - 1] if len(scores) > 1 else scores[0]

    def min_aggregate(self, scores: List[float]) -> float:
        """Return minimum score."""
        return min(scores) if scores else 0.0

    def max_aggregate(self, scores: List[float]) -> float:
        """Return maximum score."""
        return max(scores) if scores else 0.0

    def threshold_aggregate(self, scores: Dict[str, float], threshold: float) -> float:
        """
        Aggregate only scores above threshold.

        Args:
            scores: Dictionary of scores
            threshold: Minimum threshold value

        Returns:
            Average of scores above threshold
        """
        above_threshold = [score for score in scores.values() if score >= threshold]
        return sum(above_threshold) / len(above_threshold) if above_threshold else 0.0

    def adaptive_aggregate(self, scores: Dict[str, float], confidence_scores: Dict[str, float]) -> float:
        """
        Aggregate with confidence-weighted scoring.

        Args:
            scores: Dictionary of scores
            confidence_scores: Dictionary of confidence values

        Returns:
            Confidence-weighted aggregate score
        """
        total_weighted_score = 0.0
        total_confidence = 0.0

        for score_name, score_value in scores.items():
            confidence_key = f"{score_name.replace('_score', '')}_confidence"
            if confidence_key in confidence_scores:
                confidence = confidence_scores[confidence_key]
                total_weighted_score += score_value * confidence
                total_confidence += confidence

        return total_weighted_score / total_confidence if total_confidence > 0 else 0.0

    def safe_aggregate(self, scores: List[float], strategy: str = "weighted_average") -> float:
        """
        Safe aggregation that handles edge cases.

        Args:
            scores: List of scores
            strategy: Aggregation strategy

        Returns:
            Aggregated score
        """
        if not scores:
            return 0.0

        if strategy == "harmonic_mean":
            return self.safe_harmonic_mean(scores)
        elif strategy == "geometric_mean":
            return self.safe_geometric_mean(scores)
        else:
            return sum(scores) / len(scores)  # Default to arithmetic mean

    def safe_harmonic_mean(self, scores: List[float]) -> float:
        """Safe harmonic mean that handles zeros."""
        valid_scores = [score for score in scores if score > 0]
        return self.harmonic_mean(valid_scores) if valid_scores else 0.0

    def safe_geometric_mean(self, scores: List[float]) -> float:
        """Safe geometric mean that handles zeros."""
        valid_scores = [score for score in scores if score > 0]
        return self.geometric_mean(valid_scores) if valid_scores else 0.0

    def robust_aggregate(self, scores: List[float]) -> float:
        """
        Robust aggregation that handles NaN and infinity values.

        Args:
            scores: List of potentially problematic scores

        Returns:
            Robust aggregated score
        """
        valid_scores = []
        for score in scores:
            if not math.isnan(score) and not math.isinf(score) and 0.0 <= score <= 1.0:
                valid_scores.append(score)

        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0