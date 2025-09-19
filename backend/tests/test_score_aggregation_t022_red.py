"""
T022-RED: Failing tests for score aggregation and weighting
Tests for advanced score aggregation strategies and dynamic weight adjustment.
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import the modules we'll implement
from app.services.score_aggregator import ScoreAggregator
from app.services.weight_optimizer import WeightOptimizer
from app.services.scoring_service_t021 import ScoringService


class TestScoreAggregator:
    """Tests for ScoreAggregator - advanced aggregation strategies."""

    def test_score_aggregator_initialization(self):
        """Test ScoreAggregator can be initialized."""
        aggregator = ScoreAggregator()
        assert aggregator is not None

    def test_weighted_average_aggregation(self):
        """Test weighted average aggregation strategy."""
        aggregator = ScoreAggregator()
        scores = {
            "basic_score": 0.8,
            "keyword_score": 0.6,
            "ai_score": 0.9
        }
        weights = {
            "basic_weight": 0.3,
            "keyword_weight": 0.5,
            "ai_weight": 0.2
        }

        result = aggregator.weighted_average(scores, weights)
        expected = 0.8 * 0.3 + 0.6 * 0.5 + 0.9 * 0.2
        assert abs(result - expected) < 0.001

    def test_harmonic_mean_aggregation(self):
        """Test harmonic mean aggregation for balanced scoring."""
        aggregator = ScoreAggregator()
        scores = [0.8, 0.6, 0.9]

        result = aggregator.harmonic_mean(scores)
        expected = 3 / (1/0.8 + 1/0.6 + 1/0.9)
        assert abs(result - expected) < 0.001

    def test_geometric_mean_aggregation(self):
        """Test geometric mean aggregation."""
        aggregator = ScoreAggregator()
        scores = [0.8, 0.6, 0.9]

        result = aggregator.geometric_mean(scores)
        expected = (0.8 * 0.6 * 0.9) ** (1/3)
        assert abs(result - expected) < 0.001

    def test_power_mean_aggregation(self):
        """Test power mean aggregation with different power values."""
        aggregator = ScoreAggregator()
        scores = [0.8, 0.6, 0.9]

        # Test with power = 2 (quadratic mean)
        result = aggregator.power_mean(scores, power=2)
        expected = (0.8**2 + 0.6**2 + 0.9**2) / 3
        expected = expected ** 0.5
        assert abs(result - expected) < 0.001

    def test_percentile_aggregation(self):
        """Test percentile-based aggregation."""
        aggregator = ScoreAggregator()
        scores = [0.2, 0.4, 0.6, 0.8, 1.0]

        # Test median (50th percentile)
        result = aggregator.percentile_aggregate(scores, percentile=50)
        assert result == 0.6

        # Test 75th percentile
        result = aggregator.percentile_aggregate(scores, percentile=75)
        assert result == 0.8

    def test_min_max_aggregation(self):
        """Test min and max aggregation strategies."""
        aggregator = ScoreAggregator()
        scores = [0.3, 0.7, 0.5]

        min_result = aggregator.min_aggregate(scores)
        assert min_result == 0.3

        max_result = aggregator.max_aggregate(scores)
        assert max_result == 0.7

    def test_threshold_based_aggregation(self):
        """Test threshold-based aggregation."""
        aggregator = ScoreAggregator()
        scores = {
            "basic_score": 0.8,
            "keyword_score": 0.3,  # Below threshold
            "ai_score": 0.9
        }
        threshold = 0.5

        result = aggregator.threshold_aggregate(scores, threshold)
        # Should only consider scores above threshold
        assert result > 0  # Implementation details in GREEN phase

    def test_adaptive_aggregation(self):
        """Test adaptive aggregation based on score confidence."""
        aggregator = ScoreAggregator()
        scores = {
            "basic_score": 0.8,
            "keyword_score": 0.6,
            "ai_score": 0.9
        }
        confidence_scores = {
            "basic_confidence": 0.9,
            "keyword_confidence": 0.7,
            "ai_confidence": 0.5  # Low confidence in AI score
        }

        result = aggregator.adaptive_aggregate(scores, confidence_scores)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


class TestWeightOptimizer:
    """Tests for WeightOptimizer - dynamic weight adjustment."""

    def test_weight_optimizer_initialization(self):
        """Test WeightOptimizer can be initialized."""
        optimizer = WeightOptimizer()
        assert optimizer is not None

    def test_optimize_weights_by_user_feedback(self):
        """Test weight optimization based on user feedback."""
        optimizer = WeightOptimizer()

        # Sample feedback data: user liked jobs with high keyword scores
        feedback_data = [
            {
                "job_id": 1,
                "scores": {"basic": 0.6, "keyword": 0.9, "ai": 0.7},
                "user_rating": 5  # Liked
            },
            {
                "job_id": 2,
                "scores": {"basic": 0.8, "keyword": 0.4, "ai": 0.6},
                "user_rating": 2  # Disliked
            }
        ]

        new_weights = optimizer.optimize_by_feedback(feedback_data)
        assert isinstance(new_weights, dict)
        assert "basic_weight" in new_weights
        assert "keyword_weight" in new_weights
        assert "ai_weight" in new_weights
        assert abs(sum(new_weights.values()) - 1.0) < 0.001

    def test_optimize_weights_by_performance(self):
        """Test weight optimization based on matching performance."""
        optimizer = WeightOptimizer()

        performance_data = [
            {
                "weights": {"basic": 0.4, "keyword": 0.4, "ai": 0.2},
                "precision": 0.8,
                "recall": 0.7,
                "f1_score": 0.75
            },
            {
                "weights": {"basic": 0.3, "keyword": 0.5, "ai": 0.2},
                "precision": 0.85,
                "recall": 0.75,
                "f1_score": 0.8
            }
        ]

        optimal_weights = optimizer.optimize_by_performance(performance_data)
        assert isinstance(optimal_weights, dict)
        assert abs(sum(optimal_weights.values()) - 1.0) < 0.001

    def test_category_specific_weights(self):
        """Test category-specific weight optimization."""
        optimizer = WeightOptimizer()

        # Different job categories might need different weight strategies
        category_data = {
            "Software Engineering": [
                {"basic": 0.3, "keyword": 0.6, "ai": 0.1, "performance": 0.85}
            ],
            "Data Science": [
                {"basic": 0.2, "keyword": 0.4, "ai": 0.4, "performance": 0.82}
            ]
        }

        weights = optimizer.optimize_by_category(category_data)
        assert isinstance(weights, dict)
        assert "Software Engineering" in weights
        assert "Data Science" in weights

    def test_time_decay_weights(self):
        """Test weight optimization with time decay for recent data."""
        optimizer = WeightOptimizer()

        historical_data = [
            {"timestamp": 1000, "weights": {"basic": 0.4, "keyword": 0.4, "ai": 0.2}, "score": 0.8},
            {"timestamp": 2000, "weights": {"basic": 0.3, "keyword": 0.5, "ai": 0.2}, "score": 0.85},
            {"timestamp": 3000, "weights": {"basic": 0.2, "keyword": 0.6, "ai": 0.2}, "score": 0.9}
        ]

        weights = optimizer.optimize_with_time_decay(historical_data, decay_factor=0.9)
        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_constraint_based_optimization(self):
        """Test weight optimization with constraints."""
        optimizer = WeightOptimizer()

        constraints = {
            "min_basic_weight": 0.2,
            "max_ai_weight": 0.3,
            "keyword_weight_range": (0.3, 0.7)
        }

        performance_data = [
            {"weights": {"basic": 0.4, "keyword": 0.4, "ai": 0.2}, "score": 0.8}
        ]

        weights = optimizer.optimize_with_constraints(performance_data, constraints)
        assert weights["basic_weight"] >= 0.2
        assert weights["ai_weight"] <= 0.3
        assert 0.3 <= weights["keyword_weight"] <= 0.7


class TestAdvancedScoringService:
    """Tests for enhanced ScoringService with aggregation and weighting."""

    def test_scoring_service_with_aggregation_strategy(self):
        """Test ScoringService with custom aggregation strategy."""
        service = ScoringService()
        job_data = {
            "title": "Python Developer",
            "location": "San Francisco, CA",
            "category": "Software Engineering"
        }
        user_preferences = {
            "skills": ["Python"],
            "preferred_location": "SF"
        }

        # Test with different aggregation strategies
        harmonic_score = service.calculate_score_with_strategy(
            job_data, user_preferences, strategy="harmonic_mean"
        )
        assert isinstance(harmonic_score, float)
        assert 0.0 <= harmonic_score <= 1.0

        geometric_score = service.calculate_score_with_strategy(
            job_data, user_preferences, strategy="geometric_mean"
        )
        assert isinstance(geometric_score, float)
        assert 0.0 <= geometric_score <= 1.0

    def test_dynamic_weight_adjustment(self):
        """Test dynamic weight adjustment during scoring."""
        service = ScoringService()
        job_data = {"title": "Senior Python Developer", "category": "Software Engineering"}
        user_preferences = {"skills": ["Python"], "experience_level": "Senior"}

        # Simulate user feedback to adjust weights
        feedback = [
            {"job_id": 1, "user_rating": 5, "scores": {"basic": 0.6, "keyword": 0.9, "ai": 0.7}}
        ]

        service.update_weights_from_feedback(feedback)
        score = service.calculate_composite_score(job_data, user_preferences)
        assert isinstance(score, float)

    def test_multi_objective_optimization(self):
        """Test multi-objective optimization for scoring."""
        service = ScoringService()

        objectives = {
            "precision": 0.8,
            "diversity": 0.7,
            "user_satisfaction": 0.9
        }

        weights = service.optimize_for_objectives(objectives)
        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_a_b_testing_weights(self):
        """Test A/B testing framework for different weight configurations."""
        service = ScoringService()

        weight_configs = [
            {"basic": 0.4, "keyword": 0.4, "ai": 0.2},  # Configuration A
            {"basic": 0.3, "keyword": 0.5, "ai": 0.2},  # Configuration B
        ]

        results = service.ab_test_weights(weight_configs, sample_size=100)
        assert isinstance(results, dict)
        assert "winner" in results
        assert "confidence" in results

    def test_ensemble_scoring(self):
        """Test ensemble scoring with multiple aggregation strategies."""
        service = ScoringService()
        job_data = {"title": "Data Scientist", "category": "Data Science"}
        user_preferences = {"skills": ["Python", "Machine Learning"]}

        ensemble_score = service.calculate_ensemble_score(job_data, user_preferences)
        assert isinstance(ensemble_score, float)
        assert 0.0 <= ensemble_score <= 1.0


class TestScoringEdgeCasesAndErrors:
    """Test edge cases and error handling in aggregation system."""

    def test_empty_scores_aggregation(self):
        """Test handling of empty scores."""
        aggregator = ScoreAggregator()

        empty_scores = []
        result = aggregator.safe_aggregate(empty_scores, strategy="weighted_average")
        assert result == 0.0

    def test_invalid_weights_handling(self):
        """Test handling of invalid weight configurations."""
        optimizer = WeightOptimizer()

        with pytest.raises(ValueError):
            optimizer.validate_weights({"basic": 0.5, "keyword": 0.3})  # Sum != 1.0

        with pytest.raises(ValueError):
            optimizer.validate_weights({"basic": -0.1, "keyword": 0.6, "ai": 0.5})  # Negative

    def test_zero_scores_aggregation(self):
        """Test aggregation with zero scores."""
        aggregator = ScoreAggregator()

        scores_with_zeros = [0.0, 0.5, 0.8]

        # Harmonic mean should handle zeros gracefully
        result = aggregator.safe_harmonic_mean(scores_with_zeros)
        assert result >= 0.0

        # Geometric mean should handle zeros
        result = aggregator.safe_geometric_mean(scores_with_zeros)
        assert result >= 0.0

    def test_nan_and_inf_handling(self):
        """Test handling of NaN and infinity values."""
        aggregator = ScoreAggregator()

        import math
        problematic_scores = [0.5, float('nan'), 0.8, float('inf')]

        result = aggregator.robust_aggregate(problematic_scores)
        assert not math.isnan(result)
        assert not math.isinf(result)
        assert 0.0 <= result <= 1.0