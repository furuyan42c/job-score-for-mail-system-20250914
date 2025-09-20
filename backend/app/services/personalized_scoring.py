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

    # Score combination weights
    SCORE_WEIGHTS = {
        "model_prediction": 0.4,
        "user_preferences": 0.3,
        "skill_matching": 0.2,
        "experience_matching": 0.1
    }

    # Performance and caching settings
    MAX_HISTORY_ANALYSIS = 1000  # Maximum history records to analyze
    CACHE_TTL_SECONDS = 3600     # Cache time-to-live
    PERFORMANCE_WARNING_THRESHOLD = 2.0  # Seconds

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
        """
        Calculate score based on user preferences (location, salary, etc.)

        Args:
            user: User with search history
            job_id: Job identifier to score

        Returns:
            Preference-based score between 0-100
        """
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Configuration for preference scoring
            INTERACTION_WEIGHTS = {"apply": 5, "save": 3, "view": 1}
            PREFERENCE_WEIGHTS = {
                "location": {"tokyo": 20, "osaka": 10, "kyoto": 15},
                "salary": {"high": 15, "medium": 10, "low": 5}
            }

            # Analyze preferences from search history
            location_prefs = Counter()
            salary_prefs = Counter()

            for record in user.search_history:
                weight = INTERACTION_WEIGHTS.get(record.get("interaction_type", "view"), 1)

                if "location" in record:
                    location_prefs[record["location"]] += weight
                if "salary_range" in record:
                    salary_prefs[record["salary_range"]] += weight

            # Calculate preference-based score
            score = self.DEFAULT_SCORE

            # Location preference matching
            job_location = self._extract_location_from_job_id(job_id)
            if job_location and location_prefs.get(job_location.title(), 0) > 0:
                location_boost = PREFERENCE_WEIGHTS["location"].get(job_location, 5)
                preference_strength = min(location_prefs[job_location.title()] / 10, 1.0)
                score += location_boost * preference_strength

            # Salary preference matching
            job_salary_level = self._extract_salary_level_from_job_id(job_id)
            if job_salary_level and salary_prefs.get(job_salary_level, 0) > 0:
                salary_boost = PREFERENCE_WEIGHTS["salary"].get(job_salary_level, 5)
                preference_strength = min(salary_prefs[job_salary_level] / 10, 1.0)
                score += salary_boost * preference_strength

            return min(100.0, max(0.0, score))

        except Exception as e:
            logger.error("Error calculating preference score for user %s, job %s: %s",
                        getattr(user, 'user_id', 'unknown'), job_id, e)
            return self.DEFAULT_SCORE

    def _extract_location_from_job_id(self, job_id: str) -> Optional[str]:
        """Extract location information from job_id"""
        job_lower = job_id.lower()
        for location in ["tokyo", "osaka", "kyoto", "nagoya", "fukuoka"]:
            if location in job_lower:
                return location
        return None

    def _extract_salary_level_from_job_id(self, job_id: str) -> Optional[str]:
        """Extract salary level information from job_id"""
        job_lower = job_id.lower()
        if "high" in job_lower:
            return "high"
        elif "medium" in job_lower or "mid" in job_lower:
            return "medium"
        elif "low" in job_lower:
            return "low"
        return None

    async def _calculate_skill_matching_score(self, user: User, job_id: str) -> float:
        """
        Calculate score based on skill matching

        Args:
            user: User with search history containing skills
            job_id: Job identifier to analyze for skill requirements

        Returns:
            Skill matching score between 0-100
        """
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Configuration for skill scoring
            SKILL_CATEGORIES = {
                "programming": {
                    "python": 25, "javascript": 20, "java": 22, "go": 18,
                    "typescript": 20, "rust": 15, "php": 18, "ruby": 16
                },
                "frameworks": {
                    "fastapi": 20, "django": 18, "react": 20, "vue": 18,
                    "angular": 17, "flask": 15, "spring": 19, "express": 16
                },
                "databases": {
                    "postgresql": 18, "mysql": 16, "mongodb": 15, "redis": 12,
                    "elasticsearch": 14, "sqlite": 10
                },
                "design": {
                    "photoshop": 15, "figma": 18, "sketch": 16, "ui": 20,
                    "ux": 22, "design": 15, "adobe": 14
                },
                "devops": {
                    "docker": 18, "kubernetes": 20, "aws": 19, "gcp": 17,
                    "terraform": 16, "jenkins": 14
                }
            }

            # Analyze user skill preferences
            skill_counts = Counter()
            interaction_weights = {"apply": 3, "save": 2, "view": 1}

            for record in user.search_history:
                weight = interaction_weights.get(record.get("interaction_type", "view"), 1)
                if "skills" in record and isinstance(record["skills"], list):
                    for skill in record["skills"]:
                        skill_counts[skill.lower()] += weight

            # Extract skills from job_id
            job_skills = self._extract_skills_from_job_id(job_id)

            if not job_skills:
                return self.DEFAULT_SCORE

            # Calculate skill matching score
            total_score = 0
            matched_skills = 0

            for job_skill in job_skills:
                if job_skill in skill_counts:
                    # Find skill category and base score
                    skill_score = self._get_skill_base_score(job_skill, SKILL_CATEGORIES)

                    # Apply user preference strength
                    user_skill_strength = min(skill_counts[job_skill] / 5.0, 1.0)
                    adjusted_score = skill_score * user_skill_strength

                    total_score += adjusted_score
                    matched_skills += 1

            # Calculate final score
            if matched_skills == 0:
                return self.DEFAULT_SCORE

            # Average the matched skills and add to base score
            average_skill_score = total_score / matched_skills
            final_score = self.DEFAULT_SCORE + (average_skill_score * 0.8)

            return min(100.0, max(0.0, final_score))

        except Exception as e:
            logger.error("Error calculating skill matching score for user %s, job %s: %s",
                        getattr(user, 'user_id', 'unknown'), job_id, e)
            return self.DEFAULT_SCORE

    def _extract_skills_from_job_id(self, job_id: str) -> List[str]:
        """Extract skill keywords from job_id"""
        job_lower = job_id.lower()
        potential_skills = [
            "python", "javascript", "java", "go", "typescript", "rust", "php", "ruby",
            "fastapi", "django", "react", "vue", "angular", "flask", "spring", "express",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
            "photoshop", "figma", "sketch", "ui", "ux", "design", "adobe",
            "docker", "kubernetes", "aws", "gcp", "terraform", "jenkins"
        ]

        found_skills = []
        for skill in potential_skills:
            if skill in job_lower:
                found_skills.append(skill)

        return found_skills

    def _get_skill_base_score(self, skill: str, skill_categories: Dict) -> int:
        """Get base score for a skill from categories"""
        for category, skills in skill_categories.items():
            if skill in skills:
                return skills[skill]
        return 10  # Default score for unclassified skills

    async def _calculate_experience_matching_score(self, user: User, job_id: str) -> float:
        """
        Calculate score based on experience level matching

        Args:
            user: User with search history containing experience preferences
            job_id: Job identifier to analyze for experience requirements

        Returns:
            Experience matching score between 0-100
        """
        try:
            if not user.search_history:
                return self.DEFAULT_SCORE

            # Configuration for experience level scoring
            EXPERIENCE_LEVELS = {
                "entry": {"weight": 10, "aliases": ["entry", "intern", "graduate", "new"]},
                "junior": {"weight": 15, "aliases": ["junior", "jr", "1-2", "beginner"]},
                "mid": {"weight": 18, "aliases": ["mid", "middle", "intermediate", "3-5"]},
                "senior": {"weight": 20, "aliases": ["senior", "sr", "lead", "5+", "expert"]},
                "principal": {"weight": 22, "aliases": ["principal", "staff", "architect", "10+"]}
            }

            INTERACTION_WEIGHTS = {"apply": 3, "save": 2, "view": 1}

            # Analyze user experience preferences
            experience_counts = Counter()

            for record in user.search_history:
                weight = INTERACTION_WEIGHTS.get(record.get("interaction_type", "view"), 1)
                if "experience_level" in record:
                    exp_level = record["experience_level"].lower()
                    # Normalize experience levels
                    normalized_level = self._normalize_experience_level(exp_level, EXPERIENCE_LEVELS)
                    if normalized_level:
                        experience_counts[normalized_level] += weight

            # Extract experience requirements from job_id
            job_experience_level = self._extract_experience_from_job_id(job_id, EXPERIENCE_LEVELS)

            if not job_experience_level:
                return self.DEFAULT_SCORE

            # Calculate experience matching score
            if job_experience_level in experience_counts:
                base_score = EXPERIENCE_LEVELS[job_experience_level]["weight"]
                user_preference_strength = min(experience_counts[job_experience_level] / 5.0, 1.0)
                experience_bonus = base_score * user_preference_strength

                final_score = self.DEFAULT_SCORE + experience_bonus
                return min(100.0, max(0.0, final_score))

            return self.DEFAULT_SCORE

        except Exception as e:
            logger.error("Error calculating experience matching score for user %s, job %s: %s",
                        getattr(user, 'user_id', 'unknown'), job_id, e)
            return self.DEFAULT_SCORE

    def _normalize_experience_level(self, exp_level: str, experience_levels: Dict) -> Optional[str]:
        """Normalize experience level to standard categories"""
        for level, config in experience_levels.items():
            if exp_level in config["aliases"]:
                return level
        return None

    def _extract_experience_from_job_id(self, job_id: str, experience_levels: Dict) -> Optional[str]:
        """Extract experience level from job_id"""
        job_lower = job_id.lower()

        for level, config in experience_levels.items():
            for alias in config["aliases"]:
                if alias in job_lower:
                    return level

        return None

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
