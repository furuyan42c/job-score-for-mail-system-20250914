#!/usr/bin/env python3
"""
T023: Personalized Scoring Tests (RED Phase)
Tests for implicit ALS collaborative filtering
"""

import pytest
import numpy as np
from app.services.personalized_scoring import PersonalizedScoringService
from app.models.user import User
from app.models.job import Job


class TestPersonalizedScoring:
    """Test suite for personalized scoring with ALS"""

    @pytest.fixture
    def scoring_service(self):
        """Create personalized scoring service"""
        return PersonalizedScoringService()

    @pytest.fixture
    def user_history(self):
        """Sample user action history"""
        return [
            {"job_id": "job_001", "action": "view", "timestamp": "2024-01-01"},
            {"job_id": "job_002", "action": "apply", "timestamp": "2024-01-02"},
            {"job_id": "job_003", "action": "view", "timestamp": "2024-01-03"}
        ]

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing"""
        return User(
            user_id="test_user_001",
            email="test@example.com",
            search_history=[]
        )

    @pytest.mark.asyncio
    async def test_als_model_initialization(self, scoring_service):
        """Test ALS model initialization with correct parameters"""
        model = await scoring_service.initialize_als_model()

        assert model.factors == 50
        assert model.regularization == 0.01
        assert model.iterations == 15

    @pytest.mark.asyncio
    async def test_user_behavior_analysis(self, scoring_service, user_history):
        """Test analysis of 360-day user action data"""
        behavior_matrix = await scoring_service.analyze_user_behavior(
            user_history,
            days=360
        )

        assert behavior_matrix is not None
        assert len(behavior_matrix) > 0

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, scoring_service, sample_user):
        """Test fallback when no user history available"""
        # User with no history
        score = await scoring_service.calculate_personalized_score(
            sample_user,
            job_id="new_job_001"
        )

        # Should return default/fallback score
        assert score >= 0
        assert score <= 100
        assert score == 50  # Default middle score

    @pytest.mark.asyncio
    async def test_als_scoring(self, scoring_service, sample_user, user_history):
        """Test ALS model scoring"""
        # Train model with history
        await scoring_service.train_model(user_history)

        # Get personalized score
        score = await scoring_service.calculate_personalized_score(
            sample_user,
            job_id="new_job_001"
        )

        assert score >= 0
        assert score <= 100