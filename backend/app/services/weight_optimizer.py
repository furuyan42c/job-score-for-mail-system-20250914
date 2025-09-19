"""
Weight Optimizer - Dynamic weight optimization for scoring system.
Provides methods to optimize scoring weights based on feedback and performance.
"""
from typing import Dict, List, Any, Optional, Tuple
import math


class WeightOptimizer:
    """Dynamic weight optimization for scoring systems."""

    def __init__(self):
        """Initialize WeightOptimizer."""
        pass

    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """
        Validate weight configuration.

        Args:
            weights: Weight dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If weights are invalid
        """
        if not weights:
            raise ValueError("Weights cannot be empty")

        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Weights cannot be negative")

        return True

    def optimize_by_feedback(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Optimize weights based on user feedback.

        Args:
            feedback_data: List of feedback records with scores and ratings

        Returns:
            Optimized weights
        """
        # Simple implementation: increase weights for score types that correlate with high ratings
        score_type_performance = {"basic": 0.0, "keyword": 0.0, "ai": 0.0}
        total_ratings = 0

        for feedback in feedback_data:
            scores = feedback.get("scores", {})
            rating = feedback.get("user_rating", 0)

            for score_type, score_value in scores.items():
                score_type_performance[score_type] += score_value * rating

            total_ratings += rating

        # Normalize by total ratings
        if total_ratings > 0:
            for score_type in score_type_performance:
                score_type_performance[score_type] /= total_ratings

        # Convert to weights (normalize to sum to 1.0)
        total_performance = sum(score_type_performance.values())
        if total_performance > 0:
            return {
                f"{k}_weight": v / total_performance
                for k, v in score_type_performance.items()
            }
        else:
            # Default weights if no valid feedback
            return {"basic_weight": 0.4, "keyword_weight": 0.4, "ai_weight": 0.2}

    def optimize_by_performance(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Optimize weights based on matching performance metrics.

        Args:
            performance_data: List of performance records

        Returns:
            Optimal weights based on best performing configuration
        """
        best_performance = 0.0
        best_weights = {"basic_weight": 0.4, "keyword_weight": 0.4, "ai_weight": 0.2}

        for record in performance_data:
            weights = record.get("weights", {})
            f1_score = record.get("f1_score", 0.0)

            if f1_score > best_performance:
                best_performance = f1_score
                # Convert to our weight format
                best_weights = {
                    "basic_weight": weights.get("basic", 0.4),
                    "keyword_weight": weights.get("keyword", 0.4),
                    "ai_weight": weights.get("ai", 0.2)
                }

        return best_weights

    def optimize_by_category(self, category_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
        """
        Optimize weights for different job categories.

        Args:
            category_data: Category -> performance data mapping

        Returns:
            Category-specific optimal weights
        """
        category_weights = {}

        for category, data in category_data.items():
            best_performance = 0.0
            best_weights = {"basic_weight": 0.4, "keyword_weight": 0.4, "ai_weight": 0.2}

            for record in data:
                performance = record.get("performance", 0.0)
                if performance > best_performance:
                    best_performance = performance
                    best_weights = {
                        "basic_weight": record.get("basic", 0.4),
                        "keyword_weight": record.get("keyword", 0.4),
                        "ai_weight": record.get("ai", 0.2)
                    }

            category_weights[category] = best_weights

        return category_weights

    def optimize_with_time_decay(
        self,
        historical_data: List[Dict[str, Any]],
        decay_factor: float = 0.9
    ) -> Dict[str, float]:
        """
        Optimize weights with time decay for recent data.

        Args:
            historical_data: Historical performance data with timestamps
            decay_factor: Decay factor for older data (0-1)

        Returns:
            Time-weighted optimal weights
        """
        if not historical_data:
            return {"basic_weight": 0.4, "keyword_weight": 0.4, "ai_weight": 0.2}

        # Sort by timestamp (most recent first)
        sorted_data = sorted(historical_data, key=lambda x: x.get("timestamp", 0), reverse=True)

        weighted_scores = {"basic": 0.0, "keyword": 0.0, "ai": 0.0}
        total_weight = 0.0

        for i, record in enumerate(sorted_data):
            weight = decay_factor ** i
            score = record.get("score", 0.0)
            weights = record.get("weights", {})

            for score_type in weighted_scores:
                weighted_scores[score_type] += weights.get(score_type, 0.0) * score * weight

            total_weight += weight

        # Normalize
        if total_weight > 0:
            for score_type in weighted_scores:
                weighted_scores[score_type] /= total_weight

        # Convert to final weights
        total = sum(weighted_scores.values())
        if total > 0:
            return {
                f"{k}_weight": v / total
                for k, v in weighted_scores.items()
            }
        else:
            return {"basic_weight": 0.4, "keyword_weight": 0.4, "ai_weight": 0.2}

    def optimize_with_constraints(
        self,
        performance_data: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Optimize weights with constraints.

        Args:
            performance_data: Performance data
            constraints: Weight constraints

        Returns:
            Constrained optimal weights
        """
        # Start with best unconstrained solution
        best_weights = self.optimize_by_performance(performance_data)

        # Apply constraints
        for constraint_name, constraint_value in constraints.items():
            if constraint_name == "min_basic_weight":
                best_weights["basic_weight"] = max(best_weights["basic_weight"], constraint_value)
            elif constraint_name == "max_ai_weight":
                best_weights["ai_weight"] = min(best_weights["ai_weight"], constraint_value)
            elif constraint_name == "keyword_weight_range":
                min_val, max_val = constraint_value
                best_weights["keyword_weight"] = max(min_val, min(max_val, best_weights["keyword_weight"]))

        # Renormalize to sum to 1.0
        total = sum(best_weights.values())
        if total > 0:
            for key in best_weights:
                best_weights[key] /= total

        return best_weights