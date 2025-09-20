#!/usr/bin/env python3
"""
T023: Personalized Scoring Service TDD Implementation
RED PHASE: Complete failing tests for personalized scoring functionality

This test suite verifies:
1. User preference-based scoring
2. Historical interaction scoring
3. Skill matching algorithms
4. Experience level matching
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock, AsyncMock, patch

# Import the service that we'll implement
from app.services.personalized_scoring import PersonalizedScoringService
from app.models.user import User


class TestPersonalizedScoringRED:
    """RED Phase: Tests that should fail initially"""

    @pytest.fixture
    def scoring_service(self):
        """Personalized scoring service instance"""
        return PersonalizedScoringService()

    @pytest.fixture
    def sample_user_with_history(self):
        """User with substantial search history for testing"""
        return User(
            user_id="test_user_001",
            email="test@example.com",
            search_history=[
                {
                    "job_id": "job_001",
                    "interaction_type": "view",
                    "duration": 120,
                    "timestamp": datetime.now() - timedelta(days=5)
                },
                {
                    "job_id": "job_002",
                    "interaction_type": "apply",
                    "duration": 300,
                    "timestamp": datetime.now() - timedelta(days=3)
                },
                {
                    "job_id": "job_003",
                    "interaction_type": "view",
                    "duration": 60,
                    "timestamp": datetime.now() - timedelta(days=1)
                },
                {
                    "job_id": "job_004",
                    "interaction_type": "save",
                    "duration": 30,
                    "timestamp": datetime.now() - timedelta(hours=12)
                },
                {
                    "job_id": "job_005",
                    "interaction_type": "view",
                    "duration": 180,
                    "timestamp": datetime.now() - timedelta(hours=6)
                }
            ]
        )

    @pytest.fixture
    def sample_user_no_history(self):
        """User with no search history"""
        return User(
            user_id="new_user_001",
            email="newuser@example.com",
            search_history=[]
        )

    @pytest.fixture
    def sample_user_limited_history(self):
        """User with limited search history (below minimum threshold)"""
        return User(
            user_id="limited_user_001",
            email="limited@example.com",
            search_history=[
                {
                    "job_id": "job_001",
                    "interaction_type": "view",
                    "duration": 45,
                    "timestamp": datetime.now() - timedelta(days=2)
                },
                {
                    "job_id": "job_002",
                    "interaction_type": "view",
                    "duration": 30,
                    "timestamp": datetime.now() - timedelta(days=1)
                }
            ]
        )

    def test_service_initialization(self, scoring_service):
        """Test that PersonalizedScoringService initializes with correct parameters"""
        # Test ALS model parameters
        assert scoring_service.ALS_FACTORS == 50
        assert scoring_service.ALS_REGULARIZATION == 0.01
        assert scoring_service.ALS_ITERATIONS == 15

        # Test scoring parameters
        assert scoring_service.DEFAULT_SCORE == 50.0
        assert scoring_service.TRAINED_SCORE_BASE == 75.0
        assert scoring_service.BEHAVIOR_ANALYSIS_DAYS == 30
        assert scoring_service.MIN_HISTORY_SIZE == 5

    @pytest.mark.asyncio
    async def test_als_model_initialization(self, scoring_service):
        """Test ALS collaborative filtering model initialization"""
        model = await scoring_service.initialize_als_model()

        # Model should be initialized
        assert model is not None

        # Model should have correct parameters
        assert model.factors == 50
        assert model.regularization == 0.01
        assert model.iterations == 15

        # Model should not be fitted initially
        assert not model.is_fitted

    @pytest.mark.asyncio
    async def test_user_behavior_analysis_with_data(self, scoring_service, sample_user_with_history):
        """Test behavior analysis with sufficient user history"""
        analyzed_data = await scoring_service.analyze_user_behavior(
            sample_user_with_history.search_history,
            days=30
        )

        # Should return analyzed behavior patterns
        assert isinstance(analyzed_data, list)
        assert len(analyzed_data) > 0

        # Each record should have required fields
        for record in analyzed_data:
            assert "job_id" in record
            assert "interaction_type" in record
            assert "duration" in record
            assert "timestamp" in record

    @pytest.mark.asyncio
    async def test_user_behavior_analysis_empty_history(self, scoring_service):
        """Test behavior analysis with empty history"""
        analyzed_data = await scoring_service.analyze_user_behavior([], days=30)

        # Should return empty list
        assert isinstance(analyzed_data, list)
        assert len(analyzed_data) == 0

    @pytest.mark.asyncio
    async def test_user_behavior_analysis_time_filtering(self, scoring_service):
        """Test behavior analysis respects time window"""
        old_history = [
            {
                "job_id": "old_job",
                "interaction_type": "view",
                "duration": 60,
                "timestamp": datetime.now() - timedelta(days=60)  # Outside 30-day window
            }
        ]

        analyzed_data = await scoring_service.analyze_user_behavior(old_history, days=30)

        # Should filter out old interactions
        assert len(analyzed_data) == 0

    @pytest.mark.asyncio
    async def test_model_training_with_history(self, scoring_service, sample_user_with_history):
        """Test collaborative filtering model training"""
        await scoring_service.train_model(sample_user_with_history.search_history)

        # Model should be available and fitted
        assert scoring_service.model is not None
        assert scoring_service.model.is_fitted

    @pytest.mark.asyncio
    async def test_model_training_empty_history(self, scoring_service):
        """Test model training with empty history"""
        await scoring_service.train_model([])

        # Should handle empty history gracefully
        # Model might not be trained but should not crash

    @pytest.mark.asyncio
    async def test_personalized_score_with_sufficient_history(self, scoring_service, sample_user_with_history):
        """Test personalized scoring with sufficient user history"""
        score = await scoring_service.calculate_personalized_score(
            sample_user_with_history,
            "target_job_001"
        )

        # Should return a valid score
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

        # With trained model, should return score based on TRAINED_SCORE_BASE
        assert score != scoring_service.DEFAULT_SCORE

    @pytest.mark.asyncio
    async def test_personalized_score_no_history(self, scoring_service, sample_user_no_history):
        """Test personalized scoring with no user history"""
        score = await scoring_service.calculate_personalized_score(
            sample_user_no_history,
            "target_job_001"
        )

        # Should return default score
        assert score == scoring_service.DEFAULT_SCORE

    @pytest.mark.asyncio
    async def test_personalized_score_insufficient_history(self, scoring_service, sample_user_limited_history):
        """Test personalized scoring with insufficient history"""
        score = await scoring_service.calculate_personalized_score(
            sample_user_limited_history,
            "target_job_001"
        )

        # Should return default score due to insufficient history
        assert score == scoring_service.DEFAULT_SCORE

    @pytest.mark.asyncio
    async def test_skill_matching_algorithm(self, scoring_service):
        """Test skill matching algorithms in personalized scoring"""
        # Create user with specific skill preferences
        user_with_skills = User(
            user_id="skilled_user",
            email="skilled@example.com",
            search_history=[
                {
                    "job_id": "programming_job_001",
                    "interaction_type": "apply",
                    "duration": 400,
                    "timestamp": datetime.now() - timedelta(days=1),
                    "skills": ["python", "fastapi", "sql"]
                },
                {
                    "job_id": "programming_job_002",
                    "interaction_type": "view",
                    "duration": 200,
                    "timestamp": datetime.now() - timedelta(days=2),
                    "skills": ["python", "django", "postgresql"]
                },
                {
                    "job_id": "programming_job_003",
                    "interaction_type": "save",
                    "duration": 100,
                    "timestamp": datetime.now() - timedelta(days=3),
                    "skills": ["javascript", "react", "node.js"]
                },
                {
                    "job_id": "programming_job_004",
                    "interaction_type": "view",
                    "duration": 150,
                    "timestamp": datetime.now() - timedelta(days=4),
                    "skills": ["python", "machine learning", "tensorflow"]
                },
                {
                    "job_id": "programming_job_005",
                    "interaction_type": "apply",
                    "duration": 350,
                    "timestamp": datetime.now() - timedelta(days=5),
                    "skills": ["python", "fastapi", "docker"]
                }
            ]
        )

        # Test scoring for similar skill job
        python_job_score = await scoring_service.calculate_personalized_score(
            user_with_skills,
            "python_fastapi_job"
        )

        # Test scoring for different skill job
        design_job_score = await scoring_service.calculate_personalized_score(
            user_with_skills,
            "graphic_design_job"
        )

        # Python job should score higher due to skill matching
        assert python_job_score > design_job_score

    @pytest.mark.asyncio
    async def test_experience_level_matching(self, scoring_service):
        """Test experience level matching in personalized scoring"""
        # Create user with experience level preferences
        user_senior = User(
            user_id="senior_user",
            email="senior@example.com",
            search_history=[
                {
                    "job_id": "senior_role_001",
                    "interaction_type": "apply",
                    "duration": 500,
                    "timestamp": datetime.now() - timedelta(days=1),
                    "experience_level": "senior"
                },
                {
                    "job_id": "senior_role_002",
                    "interaction_type": "view",
                    "duration": 300,
                    "timestamp": datetime.now() - timedelta(days=2),
                    "experience_level": "senior"
                },
                {
                    "job_id": "senior_role_003",
                    "interaction_type": "save",
                    "duration": 200,
                    "timestamp": datetime.now() - timedelta(days=3),
                    "experience_level": "senior"
                },
                {
                    "job_id": "mid_role_001",
                    "interaction_type": "view",
                    "duration": 100,
                    "timestamp": datetime.now() - timedelta(days=4),
                    "experience_level": "mid"
                },
                {
                    "job_id": "senior_role_004",
                    "interaction_type": "apply",
                    "duration": 450,
                    "timestamp": datetime.now() - timedelta(days=5),
                    "experience_level": "senior"
                }
            ]
        )

        # Test scoring for matching experience level
        senior_job_score = await scoring_service.calculate_personalized_score(
            user_senior,
            "senior_level_position"
        )

        # Test scoring for junior level job
        junior_job_score = await scoring_service.calculate_personalized_score(
            user_senior,
            "junior_level_position"
        )

        # Senior job should score higher due to experience matching
        assert senior_job_score > junior_job_score

    @pytest.mark.asyncio
    async def test_preference_based_scoring(self, scoring_service):
        """Test user preference-based scoring algorithm"""
        # Create user with clear location and salary preferences
        user_with_prefs = User(
            user_id="pref_user",
            email="prefs@example.com",
            search_history=[
                {
                    "job_id": "tokyo_high_pay_001",
                    "interaction_type": "apply",
                    "duration": 600,
                    "timestamp": datetime.now() - timedelta(days=1),
                    "location": "Tokyo",
                    "salary_range": "high"
                },
                {
                    "job_id": "tokyo_high_pay_002",
                    "interaction_type": "save",
                    "duration": 400,
                    "timestamp": datetime.now() - timedelta(days=2),
                    "location": "Tokyo",
                    "salary_range": "high"
                },
                {
                    "job_id": "tokyo_mid_pay_001",
                    "interaction_type": "view",
                    "duration": 200,
                    "timestamp": datetime.now() - timedelta(days=3),
                    "location": "Tokyo",
                    "salary_range": "mid"
                },
                {
                    "job_id": "osaka_high_pay_001",
                    "interaction_type": "view",
                    "duration": 150,
                    "timestamp": datetime.now() - timedelta(days=4),
                    "location": "Osaka",
                    "salary_range": "high"
                },
                {
                    "job_id": "tokyo_high_pay_003",
                    "interaction_type": "apply",
                    "duration": 550,
                    "timestamp": datetime.now() - timedelta(days=5),
                    "location": "Tokyo",
                    "salary_range": "high"
                }
            ]
        )

        # Test scoring for preferred combination (Tokyo + High pay)
        preferred_job_score = await scoring_service.calculate_personalized_score(
            user_with_prefs,
            "tokyo_high_salary_job"
        )

        # Test scoring for non-preferred combination (Osaka + Low pay)
        non_preferred_job_score = await scoring_service.calculate_personalized_score(
            user_with_prefs,
            "osaka_low_salary_job"
        )

        # Preferred job should score significantly higher
        assert preferred_job_score > non_preferred_job_score

    @pytest.mark.asyncio
    async def test_collaborative_filtering_predictions(self, scoring_service):
        """Test that ALS collaborative filtering generates meaningful predictions"""
        # Create training data with multiple users
        training_history = [
            {
                "user_id": "user_001",
                "job_id": "job_001",
                "interaction_type": "apply",
                "rating": 5,
                "timestamp": datetime.now() - timedelta(days=1)
            },
            {
                "user_id": "user_001",
                "job_id": "job_002",
                "interaction_type": "view",
                "rating": 3,
                "timestamp": datetime.now() - timedelta(days=2)
            },
            {
                "user_id": "user_002",
                "job_id": "job_001",
                "interaction_type": "apply",
                "rating": 5,
                "timestamp": datetime.now() - timedelta(days=1)
            },
            {
                "user_id": "user_002",
                "job_id": "job_003",
                "interaction_type": "save",
                "rating": 4,
                "timestamp": datetime.now() - timedelta(days=3)
            }
        ]

        # Train model
        await scoring_service.train_model(training_history)

        # Test user with similar preferences to user_001
        similar_user = User(
            user_id="user_003",
            email="similar@example.com",
            search_history=[
                {
                    "job_id": "job_001",
                    "interaction_type": "apply",
                    "duration": 400,
                    "timestamp": datetime.now() - timedelta(days=1)
                }
            ]
        )

        # Should predict high score for job_002 (similar to user_001)
        predicted_score = await scoring_service.calculate_personalized_score(
            similar_user,
            "job_002"
        )

        # Should be higher than default due to collaborative filtering
        assert predicted_score > scoring_service.DEFAULT_SCORE

    def test_error_handling_invalid_input(self, scoring_service):
        """Test error handling for invalid inputs"""
        # Test with None user
        with pytest.raises((AttributeError, ValueError)):
            asyncio.run(scoring_service.calculate_personalized_score(None, "job_001"))

        # Test with invalid job_id
        user = User(user_id="test", email="test@example.com", search_history=[])
        score = asyncio.run(scoring_service.calculate_personalized_score(user, None))
        assert score == scoring_service.DEFAULT_SCORE

    @pytest.mark.asyncio
    async def test_performance_with_large_history(self, scoring_service):
        """Test performance with large user history"""
        # Create user with large history (1000 interactions)
        large_history = []
        for i in range(1000):
            large_history.append({
                "job_id": f"job_{i:04d}",
                "interaction_type": "view",
                "duration": 60,
                "timestamp": datetime.now() - timedelta(days=i % 30)
            })

        user_large_history = User(
            user_id="large_history_user",
            email="large@example.com",
            search_history=large_history
        )

        # Should handle large history without performance issues
        import time
        start_time = time.time()

        score = await scoring_service.calculate_personalized_score(
            user_large_history,
            "performance_test_job"
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within reasonable time (< 2 seconds)
        assert processing_time < 2.0
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


if __name__ == "__main__":
    # Run tests manually for validation
    print("Running T023 Personalized Scoring TDD Tests (RED PHASE)")
    print("These tests should FAIL initially - that's the point of TDD RED phase")

    # Simulate test execution
    service = PersonalizedScoringService()
    print(f"✓ Service initialized with ALS factors: {service.ALS_FACTORS}")
    print(f"✓ Default score setting: {service.DEFAULT_SCORE}")
    print(f"✓ Minimum history size: {service.MIN_HISTORY_SIZE}")

    print("\nTests created for:")
    print("- User preference-based scoring")
    print("- Historical interaction scoring")
    print("- Skill matching algorithms")
    print("- Experience level matching")
    print("- Collaborative filtering with ALS")
    print("- Performance testing")
    print("- Error handling")

    print("\nREADY FOR GREEN PHASE: Implementation to make tests pass")