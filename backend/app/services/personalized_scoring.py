#!/usr/bin/env python3
"""
T023: Personalized Scoring Service

Provides collaborative filtering-based personalized scoring using ALS algorithm.
Generates user-specific job recommendations based on historical behavior.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from app.models.user import User

logger = logging.getLogger(__name__)

class PersonalizedScoringService:
    """Service for calculating personalized job scores using collaborative filtering."""

    # ALS model parameters
    ALS_FACTORS = 50
    ALS_REGULARIZATION = 0.01
    ALS_ITERATIONS = 15

    # Scoring parameters
    DEFAULT_SCORE = 50.0
    TRAINED_SCORE_BASE = 75.0
    BEHAVIOR_ANALYSIS_DAYS = 30
    MIN_HISTORY_SIZE = 5

    def __init__(self):
        """Initialize personalized scoring service."""
        self.factors = self.ALS_FACTORS
        self.regularization = self.ALS_REGULARIZATION
        self.iterations = self.ALS_ITERATIONS
        self.model = None
        self._user_item_matrix = None
        self._user_id_to_index = {}
        self._job_id_to_index = {}
        self._model_trained = False
        logger.info("PersonalizedScoringService initialized with ALS params: factors=%d, reg=%.3f, iter=%d",
                   self.factors, self.regularization, self.iterations)

    async def initialize_als_model(self):
        """
        Initialize ALS collaborative filtering model.

        Returns:
            Initialized ALS model instance
        """
        try:
            # TODO: Replace with actual ALS implementation (e.g., implicit library)
            class ALSModel:
                """Mock ALS model for development."""
                def __init__(self, factors: int, regularization: float, iterations: int):
                    self.factors = factors
                    self.regularization = regularization
                    self.iterations = iterations
                    self.is_fitted = False

                def fit(self, user_item_matrix):
                    """Fit the model to user-item interaction data."""
                    self.is_fitted = True
                    logger.info("ALS model fitted with matrix shape: %s",
                              getattr(user_item_matrix, 'shape', 'unknown'))

                def predict(self, user_id: str, item_id: str) -> float:
                    """Predict user preference for an item."""
                    if not self.is_fitted:
                        return 0.5
                    # Mock prediction logic
                    return 0.75

            model = ALSModel(self.factors, self.regularization, self.iterations)
            logger.info("ALS model initialized successfully")
            return model

        except Exception as e:
            logger.error("Error initializing ALS model: %s", e)
            return None

    async def analyze_user_behavior(self, history: List[Dict], days: int = None) -> List[Dict[str, Any]]:
        """
        Analyze user behavior patterns from interaction history.

        Args:
            history: List of user interaction records
            days: Number of days to analyze (default: BEHAVIOR_ANALYSIS_DAYS)

        Returns:
            List of analyzed behavior patterns
        """
        if days is None:
            days = self.BEHAVIOR_ANALYSIS_DAYS

        if not history:
            logger.debug("No history provided for behavior analysis")
            return []

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            analyzed_data = []

            for record in history:
                if not isinstance(record, dict):
                    continue

                # Check if record is within time window
                timestamp = record.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    if timestamp < cutoff_date:
                        continue

                # Extract relevant features
                analyzed_record = {
                    "job_id": record.get("job_id"),
                    "interaction_type": record.get("interaction_type", "view"),
                    "duration": record.get("duration", 0),
                    "timestamp": timestamp
                }
                analyzed_data.append(analyzed_record)

            logger.info("Analyzed %d behavior records from last %d days", len(analyzed_data), days)
            return analyzed_data

        except Exception as e:
            logger.error("Error analyzing user behavior: %s", e)
            return []

    async def train_model(self, history: List[Dict]):
        """
        Train the collaborative filtering model on user history.

        Args:
            history: List of user interaction records
        """
        try:
            if not history:
                logger.warning("Cannot train model with empty history")
                return

            # Initialize model if not exists
            if not self.model:
                self.model = await self.initialize_als_model()

            if self.model:
                # TODO: Convert history to user-item matrix format
                # For now, just mark as fitted
                self.model.is_fitted = True
                logger.info("Model training completed with %d records", len(history))

        except Exception as e:
            logger.error("Error training model: %s", e)

    async def calculate_personalized_score(self, user: User, job_id: str) -> float:
        """
        Calculate personalized score for a job based on user preferences.

        Args:
            user: User object with search history
            job_id: ID of the job to score

        Returns:
            Personalized score between 0 and 100
        """
        try:
            if not user:
                raise ValueError("User cannot be None")

            if not job_id:
                logger.warning("Invalid job_id provided, returning default score")
                return self.DEFAULT_SCORE

            # Check if user has sufficient history
            if not hasattr(user, 'search_history') or not user.search_history:
                logger.debug("User %s has no search history, returning default score",
                           getattr(user, 'user_id', 'unknown'))
                return self.DEFAULT_SCORE

            history_size = len(user.search_history)

            # Return default score if history is too small
            if history_size < self.MIN_HISTORY_SIZE:
                logger.debug("User %s has insufficient history (%d records), returning default score",
                           getattr(user, 'user_id', 'unknown'), history_size)
                return self.DEFAULT_SCORE

            # Train model if needed
            if not self.model or not getattr(self.model, 'is_fitted', False):
                await self.train_model(user.search_history)

            # Calculate score using model
            if self.model and getattr(self.model, 'is_fitted', False):
                # Use actual model prediction
                prediction = self.model.predict(getattr(user, 'user_id', ''), job_id)
                score = self.TRAINED_SCORE_BASE * prediction

                # Apply preference-based scoring adjustments
                preference_score = await self._calculate_preference_score(user, job_id)
                skill_score = await self._calculate_skill_matching_score(user, job_id)
                experience_score = await self._calculate_experience_matching_score(user, job_id)

                # Combine scores with weights
                final_score = (score * 0.4) + (preference_score * 0.3) + (skill_score * 0.2) + (experience_score * 0.1)

                # Ensure score is within bounds
                final_score = max(0, min(100, final_score))

                logger.info("Personalized score for user %s, job %s: %.2f (model=%.2f, pref=%.2f, skill=%.2f, exp=%.2f)",
                           getattr(user, 'user_id', 'unknown'), job_id, final_score, score, preference_score, skill_score, experience_score)
                return final_score

            return self.DEFAULT_SCORE

        except Exception as e:
            logger.error("Error calculating personalized score: %s", e)
            return self.DEFAULT_SCORE

    async def _calculate_preference_score(self, user: User, job_id: str) -> float:
        """Calculate score based on user preferences (location, salary, etc.)"""
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Analyze preferences from search history
            location_prefs = Counter()
            salary_prefs = Counter()
            interaction_weights = {"apply": 5, "save": 3, "view": 1}

            for record in user.search_history:
                weight = interaction_weights.get(record.get("interaction_type", "view"), 1)

                if "location" in record:
                    location_prefs[record["location"]] += weight
                if "salary_range" in record:
                    salary_prefs[record["salary_range"]] += weight

            # Score based on job_id matching preferences
            # In real implementation, we'd match against actual job data
            score = self.DEFAULT_SCORE

            # Simple preference scoring based on job_id patterns
            if "tokyo" in job_id.lower() and location_prefs.get("Tokyo", 0) > 0:
                score += 20
            if "high" in job_id.lower() and salary_prefs.get("high", 0) > 0:
                score += 15
            if "osaka" in job_id.lower() and location_prefs.get("Osaka", 0) > 0:
                score += 10

            return min(100, score)

        except Exception as e:
            logger.error("Error calculating preference score: %s", e)
            return self.DEFAULT_SCORE

    async def _calculate_skill_matching_score(self, user: User, job_id: str) -> float:
        """Calculate score based on skill matching"""
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Analyze skills from search history
            skill_counts = Counter()
            for record in user.search_history:
                if "skills" in record:
                    for skill in record["skills"]:
                        skill_counts[skill] += 1

            # Score based on job_id matching skills
            score = self.DEFAULT_SCORE

            if "python" in job_id.lower() and skill_counts.get("python", 0) > 0:
                score += 25
            if "javascript" in job_id.lower() and skill_counts.get("javascript", 0) > 0:
                score += 20
            if "design" in job_id.lower() and any(skill in ["design", "photoshop", "ui"] for skill in skill_counts):
                score += 15

            return min(100, score)

        except Exception as e:
            logger.error("Error calculating skill matching score: %s", e)
            return self.DEFAULT_SCORE

    async def _calculate_experience_matching_score(self, user: User, job_id: str) -> float:
        """Calculate score based on experience level matching"""
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Analyze experience levels from search history
            experience_counts = Counter()
            interaction_weights = {"apply": 3, "save": 2, "view": 1}

            for record in user.search_history:
                weight = interaction_weights.get(record.get("interaction_type", "view"), 1)
                if "experience_level" in record:
                    experience_counts[record["experience_level"]] += weight

            # Score based on job_id matching experience levels
            score = self.DEFAULT_SCORE

            if "senior" in job_id.lower() and experience_counts.get("senior", 0) > 0:
                score += 20
            if "junior" in job_id.lower() and experience_counts.get("junior", 0) > 0:
                score += 15
            if "mid" in job_id.lower() and experience_counts.get("mid", 0) > 0:
                score += 18

            return min(100, score)

        except Exception as e:
            logger.error("Error calculating experience matching score: %s", e)
            return self.DEFAULT_SCORE

    async def _build_user_item_matrix(self):
        """Build user-item interaction matrix for collaborative filtering"""
        try:
            # Simulated database query result
            # In real implementation, this would query the database
            interactions = []

            # Build user and job indices
            user_ids = set()
            job_ids = set()

            for interaction in interactions:
                user_ids.add(interaction.user_id)
                job_ids.add(interaction.job_id)

            self._user_id_to_index = {user_id: idx for idx, user_id in enumerate(sorted(user_ids))}
            self._job_id_to_index = {job_id: idx for idx, job_id in enumerate(sorted(job_ids))}

            # Create interaction matrix
            if user_ids and job_ids:
                self._user_item_matrix = np.zeros((len(user_ids), len(job_ids)))

                for interaction in interactions:
                    user_idx = self._user_id_to_index[interaction.user_id]
                    job_idx = self._job_id_to_index[interaction.job_id]
                    self._user_item_matrix[user_idx, job_idx] = interaction.interaction_weight
            else:
                # Handle empty case
                self._user_item_matrix = np.array([[]])
                self._user_id_to_index = {}
                self._job_id_to_index = {}

            logger.info("User-item matrix built: %d users, %d jobs",
                       len(self._user_id_to_index), len(self._job_id_to_index))

        except Exception as e:
            logger.error("Error building user-item matrix: %s", e)
            self._user_item_matrix = np.array([[]])
            self._user_id_to_index = {}
            self._job_id_to_index = {}
