"""
Advanced Weighted Matching Algorithm (T018)
Implements sophisticated job matching with dynamic weights and machine learning features
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import math
import logging
from datetime import datetime, timedelta

from .basic_matching import BasicMatchingAlgorithm, JobData, UserProfile, MatchScore

logger = logging.getLogger(__name__)


class WeightingStrategy(str, Enum):
    """Weight adjustment strategies"""
    STATIC = "static"
    USER_HISTORY = "user_history"
    COLLABORATIVE = "collaborative"
    ADAPTIVE = "adaptive"


@dataclass
class UserBehaviorData:
    """User behavior data for weight adjustment"""
    user_id: int
    job_applications: List[int] = field(default_factory=list)
    job_clicks: List[int] = field(default_factory=list)
    job_views: List[int] = field(default_factory=list)
    feedback_history: Dict[int, str] = field(default_factory=dict)  # job_id -> feedback
    time_spent_by_job: Dict[int, int] = field(default_factory=dict)  # job_id -> seconds
    last_activity: Optional[datetime] = None


@dataclass
class JobInteractionData:
    """Job interaction aggregated data"""
    job_id: int
    total_views: int = 0
    total_clicks: int = 0
    total_applications: int = 0
    avg_time_spent: float = 0.0
    positive_feedback_ratio: float = 0.0
    conversion_rate: float = 0.0  # applications / views


class WeightedMatchingAlgorithm(BasicMatchingAlgorithm):
    """
    Advanced matching algorithm with dynamic weights

    Features:
    - Adaptive weights based on user behavior
    - Collaborative filtering signals
    - Temporal decay for preferences
    - Machine learning feature extraction
    """

    def __init__(self,
                 base_weights: Optional[Dict[str, float]] = None,
                 weighting_strategy: WeightingStrategy = WeightingStrategy.ADAPTIVE,
                 learning_rate: float = 0.1):
        """
        Initialize weighted matching algorithm

        Args:
            base_weights: Base weights for criteria
            weighting_strategy: Strategy for weight adjustment
            learning_rate: Learning rate for adaptive weights
        """
        super().__init__(base_weights)
        self.weighting_strategy = weighting_strategy
        self.learning_rate = learning_rate
        self.user_weights_cache: Dict[int, Dict[str, float]] = {}
        self.job_popularity_cache: Dict[int, float] = {}

    def calculate_weighted_score(self,
                                user: UserProfile,
                                job: JobData,
                                user_behavior: Optional[UserBehaviorData] = None,
                                job_interactions: Optional[JobInteractionData] = None) -> MatchScore:
        """
        Calculate match score with dynamic weights

        Args:
            user: User profile
            job: Job data
            user_behavior: User's historical behavior data
            job_interactions: Job's interaction statistics

        Returns:
            Enhanced match score with personalized weights
        """
        try:
            # Get personalized weights
            weights = self._get_personalized_weights(user, user_behavior)

            # Calculate base scores
            skills_score = self._calculate_enhanced_skills_score(user, job, user_behavior)
            location_score = self._calculate_location_score(user, job)
            salary_score = self._calculate_enhanced_salary_score(user, job, user_behavior)
            category_score = self._calculate_enhanced_category_score(user, job, user_behavior)
            experience_score = self._calculate_experience_score(user, job)

            # Apply popularity and social signals
            popularity_boost = self._calculate_popularity_boost(job, job_interactions)
            temporal_adjustment = self._calculate_temporal_adjustment(user_behavior)

            # Calculate weighted total
            base_score = (
                skills_score * weights["skills"] +
                location_score * weights["location"] +
                salary_score * weights["salary"] +
                category_score * weights["category"] +
                experience_score * weights["experience"]
            )

            # Apply boosts and adjustments
            final_score = base_score + popularity_boost + temporal_adjustment

            # Ensure score is in range 0-100
            final_score = max(0, min(100, int(final_score)))

            return MatchScore(
                total_score=final_score,
                skills_score=skills_score,
                location_score=location_score,
                salary_score=salary_score,
                category_score=category_score,
                experience_score=experience_score,
                details={
                    "algorithm": "weighted_matching",
                    "version": "2.0",
                    "base_weights": self.weights,
                    "personalized_weights": weights,
                    "popularity_boost": popularity_boost,
                    "temporal_adjustment": temporal_adjustment,
                    "base_score": base_score,
                    "weighting_strategy": self.weighting_strategy,
                    "user_id": user.user_id,
                    "job_id": job.job_id
                }
            )

        except Exception as e:
            logger.error(f"Error calculating weighted score for user {user.user_id}, job {job.job_id}: {e}")
            # Fallback to basic algorithm
            return super().calculate_match_score(user, job)

    def _get_personalized_weights(self,
                                 user: UserProfile,
                                 user_behavior: Optional[UserBehaviorData] = None) -> Dict[str, float]:
        """
        Get personalized weights based on user behavior
        """
        if self.weighting_strategy == WeightingStrategy.STATIC or not user_behavior:
            return self.weights.copy()

        # Check cache
        if user.user_id in self.user_weights_cache:
            return self.user_weights_cache[user.user_id]

        base_weights = self.weights.copy()

        if self.weighting_strategy == WeightingStrategy.USER_HISTORY:
            weights = self._adjust_weights_by_user_history(base_weights, user_behavior)
        elif self.weighting_strategy == WeightingStrategy.COLLABORATIVE:
            weights = self._adjust_weights_by_collaborative_filtering(base_weights, user, user_behavior)
        elif self.weighting_strategy == WeightingStrategy.ADAPTIVE:
            weights = self._adjust_weights_adaptively(base_weights, user, user_behavior)
        else:
            weights = base_weights

        # Cache for future use
        self.user_weights_cache[user.user_id] = weights
        return weights

    def _adjust_weights_by_user_history(self,
                                       base_weights: Dict[str, float],
                                       user_behavior: UserBehaviorData) -> Dict[str, float]:
        """
        Adjust weights based on user's historical behavior patterns
        """
        weights = base_weights.copy()

        # Analyze user's job interaction patterns
        if user_behavior.job_applications:
            # Users who apply frequently might value salary more
            application_rate = len(user_behavior.job_applications) / max(1, len(user_behavior.job_views))
            if application_rate > 0.1:  # High application rate
                weights["salary"] = min(0.5, weights["salary"] * 1.2)
                weights["skills"] = max(0.2, weights["skills"] * 0.9)

        # Analyze feedback patterns
        if user_behavior.feedback_history:
            positive_feedback = sum(1 for feedback in user_behavior.feedback_history.values()
                                   if feedback in ["interested", "applied"])
            total_feedback = len(user_behavior.feedback_history)

            if total_feedback > 5 and positive_feedback / total_feedback < 0.3:
                # User is picky, increase skills weight
                weights["skills"] = min(0.6, weights["skills"] * 1.3)
                weights["category"] = min(0.3, weights["category"] * 1.2)

        # Normalize weights
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    def _adjust_weights_by_collaborative_filtering(self,
                                                  base_weights: Dict[str, float],
                                                  user: UserProfile,
                                                  user_behavior: UserBehaviorData) -> Dict[str, float]:
        """
        Adjust weights based on similar users' behavior
        """
        # Simplified collaborative filtering
        # In production, this would use more sophisticated similarity metrics
        weights = base_weights.copy()

        # Find similar users based on skills and preferences
        similarity_boost = 0.1  # Placeholder for similarity-based adjustments

        # Users with similar skills might value skills differently
        if "Python" in user.skills or "JavaScript" in user.skills:
            weights["skills"] = min(0.6, weights["skills"] * (1 + similarity_boost))

        # Normalize weights
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    def _adjust_weights_adaptively(self,
                                  base_weights: Dict[str, float],
                                  user: UserProfile,
                                  user_behavior: UserBehaviorData) -> Dict[str, float]:
        """
        Adaptively adjust weights using reinforcement learning principles
        """
        weights = base_weights.copy()

        # Combine multiple adjustment strategies
        hist_weights = self._adjust_weights_by_user_history(base_weights, user_behavior)
        collab_weights = self._adjust_weights_by_collaborative_filtering(base_weights, user, user_behavior)

        # Weighted average of different strategies
        for key in weights:
            weights[key] = (
                0.4 * base_weights[key] +
                0.4 * hist_weights[key] +
                0.2 * collab_weights[key]
            )

        # Apply learning rate
        for key in weights:
            adjustment = (weights[key] - base_weights[key]) * self.learning_rate
            weights[key] = base_weights[key] + adjustment

        # Normalize weights
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    def _calculate_enhanced_skills_score(self,
                                       user: UserProfile,
                                       job: JobData,
                                       user_behavior: Optional[UserBehaviorData] = None) -> int:
        """
        Enhanced skills scoring with behavior-based adjustments
        """
        base_score = super()._calculate_skills_score(user, job)

        if not user_behavior:
            return base_score

        # Boost score for skills that user has applied to before
        applied_jobs_skills = self._get_skills_from_applied_jobs(user_behavior.job_applications)
        skill_familiarity_boost = 0

        for skill in job.required_skills + job.preferred_skills:
            if skill.lower() in [s.lower() for s in applied_jobs_skills]:
                skill_familiarity_boost += 5

        return min(100, base_score + skill_familiarity_boost)

    def _calculate_enhanced_salary_score(self,
                                       user: UserProfile,
                                       job: JobData,
                                       user_behavior: Optional[UserBehaviorData] = None) -> int:
        """
        Enhanced salary scoring considering user's application history
        """
        base_score = super()._calculate_salary_score(user, job)

        if not user_behavior or not user_behavior.job_applications:
            return base_score

        # Analyze user's salary acceptance patterns from applications
        avg_applied_salary = self._get_average_applied_salary(user_behavior.job_applications)

        if avg_applied_salary and job.salary_max:
            # Adjust score based on historical acceptance patterns
            if job.salary_max >= avg_applied_salary * 0.9:  # Within 90% of historical average
                return min(100, base_score + 10)
            elif job.salary_max < avg_applied_salary * 0.7:  # Significantly below average
                return max(0, base_score - 15)

        return base_score

    def _calculate_enhanced_category_score(self,
                                         user: UserProfile,
                                         job: JobData,
                                         user_behavior: Optional[UserBehaviorData] = None) -> int:
        """
        Enhanced category scoring with user preference learning
        """
        base_score = super()._calculate_category_score(user, job)

        if not user_behavior:
            return base_score

        # Learn from user's actual application categories
        applied_categories = self._get_categories_from_applied_jobs(user_behavior.job_applications)

        if job.category in applied_categories:
            # User has applied to this category before
            application_frequency = applied_categories.count(job.category)
            boost = min(20, application_frequency * 5)
            return min(100, base_score + boost)

        return base_score

    def _calculate_popularity_boost(self,
                                  job: JobData,
                                  job_interactions: Optional[JobInteractionData] = None) -> int:
        """
        Calculate popularity-based score boost
        """
        if not job_interactions:
            return 0

        # Jobs with high engagement get slight boost (but not too much to avoid echo chambers)
        conversion_rate = job_interactions.conversion_rate
        positive_feedback = job_interactions.positive_feedback_ratio

        # Balanced popularity boost (max 5 points)
        popularity_score = (conversion_rate * 3 + positive_feedback * 2) * 1.0
        return min(5, int(popularity_score))

    def _calculate_temporal_adjustment(self,
                                     user_behavior: Optional[UserBehaviorData] = None) -> int:
        """
        Calculate temporal adjustments based on recency and trends
        """
        if not user_behavior or not user_behavior.last_activity:
            return 0

        # Adjust based on user activity recency
        days_since_activity = (datetime.now() - user_behavior.last_activity).days

        if days_since_activity < 1:
            return 2  # Very recent activity, slight boost
        elif days_since_activity < 7:
            return 1  # Recent activity
        elif days_since_activity > 30:
            return -2  # Stale user, slight penalty

        return 0

    def _get_skills_from_applied_jobs(self, applied_job_ids: List[int]) -> List[str]:
        """
        Extract skills from jobs user has applied to (placeholder)
        """
        # In production, this would query the database for job skills
        return ["Python", "SQL", "JavaScript"]  # Placeholder

    def _get_average_applied_salary(self, applied_job_ids: List[int]) -> Optional[float]:
        """
        Calculate average salary of jobs user has applied to (placeholder)
        """
        # In production, this would query the database for job salaries
        return 5000000.0  # Placeholder - 5M yen

    def _get_categories_from_applied_jobs(self, applied_job_ids: List[int]) -> List[str]:
        """
        Extract categories from jobs user has applied to (placeholder)
        """
        # In production, this would query the database for job categories
        return ["IT", "Software", "Engineering"]  # Placeholder

    def update_user_weights(self,
                           user_id: int,
                           job_id: int,
                           feedback: str,
                           predicted_score: int,
                           actual_engagement: float):
        """
        Update user weights based on feedback (online learning)

        Args:
            user_id: User ID
            job_id: Job ID
            feedback: User feedback (interested, not_interested, applied)
            predicted_score: Score our algorithm predicted
            actual_engagement: Actual user engagement (0-1)
        """
        if user_id not in self.user_weights_cache:
            return

        weights = self.user_weights_cache[user_id]

        # Simple reinforcement learning update
        error = actual_engagement - (predicted_score / 100.0)

        # Adjust weights based on error
        for criterion in weights:
            # This is a simplified update rule
            # In production, would use more sophisticated RL algorithms
            if abs(error) > 0.3:  # Significant prediction error
                adjustment = error * self.learning_rate * 0.1
                weights[criterion] = max(0.05, min(0.8, weights[criterion] + adjustment))

        # Normalize weights
        total = sum(weights.values())
        self.user_weights_cache[user_id] = {k: v / total for k, v in weights.items()}

    def get_feature_importance(self, user_id: int) -> Dict[str, float]:
        """
        Get feature importance for a specific user

        Args:
            user_id: User ID

        Returns:
            Dictionary of feature importance scores
        """
        if user_id in self.user_weights_cache:
            return self.user_weights_cache[user_id].copy()
        return self.weights.copy()

    def clear_cache(self):
        """Clear all cached data"""
        self.user_weights_cache.clear()
        self.job_popularity_cache.clear()