"""
Advanced Matching Algorithms Service
T017-T020: Machine Learning-Based Job Recommendation System

This service implements sophisticated matching algorithms including:
- Collaborative filtering
- Content-based filtering
- Hybrid recommendation approaches
- Machine learning models for personalized job matching

Author: Claude Code Assistant
Created: 2025-09-19
Version: 1.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import math
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor

# ML/Data Science imports (would be sklearn, etc. in production)
# For now, implementing core algorithms from scratch
import random

from app.services.gpt5_integration import UserProfile, JobMatch

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class MatchingAlgorithm(Enum):
    """Available matching algorithms"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    ML_ENHANCED = "ml_enhanced"
    POPULARITY_BASED = "popularity_based"
    DEEP_LEARNING = "deep_learning"

class RecommendationType(Enum):
    """Types of recommendations"""
    PERSONAL = "personal"
    TRENDING = "trending"
    SIMILAR_USERS = "similar_users"
    LOCATION_BASED = "location_based"
    SKILL_MATCH = "skill_match"
    CAREER_GROWTH = "career_growth"

class MatchingQuality(Enum):
    """Quality levels for matching"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ULTRA = "ultra"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class UserInteraction:
    """User interaction with jobs"""
    user_id: int
    job_id: int
    interaction_type: str  # view, apply, save, share, reject
    timestamp: datetime
    interaction_strength: float = 1.0  # Weighted importance
    context_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserFeatures:
    """Extracted user features for ML"""
    user_id: int
    skills_vector: List[float]
    experience_level: float
    salary_expectation: float
    location_preferences: List[float]
    industry_preferences: List[float]
    job_type_preferences: List[float]
    activity_score: float
    career_stage: str
    last_active: datetime

@dataclass
class JobFeatures:
    """Extracted job features for ML"""
    job_id: int
    skills_required: List[float]
    experience_required: float
    salary_offered: float
    location_vector: List[float]
    industry_vector: List[float]
    job_type_vector: List[float]
    popularity_score: float
    freshness_score: float
    company_rating: float

@dataclass
class MatchingResult:
    """Result of matching algorithm"""
    user_id: int
    job_id: int
    match_score: float
    algorithm_used: MatchingAlgorithm
    confidence: float
    explanation: str
    feature_contributions: Dict[str, float]
    recommendation_type: RecommendationType

@dataclass
class RecommendationSet:
    """Set of recommendations for a user"""
    user_id: int
    recommendations: List[MatchingResult]
    algorithm_mix: Dict[MatchingAlgorithm, int]
    generated_at: datetime
    diversity_score: float
    coverage_score: float
    quality_metrics: Dict[str, float]

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

class FeatureExtractor:
    """Extract numerical features from user and job data"""

    def __init__(self):
        self.skill_vocabulary = set()
        self.location_vocabulary = set()
        self.industry_vocabulary = set()
        self.company_vocabulary = set()
        self._build_vocabularies()

    def _build_vocabularies(self):
        """Build vocabularies for feature encoding"""
        # This would typically be built from historical data
        self.skill_vocabulary = {
            "python", "java", "javascript", "react", "node.js", "sql", "aws",
            "machine learning", "data analysis", "project management", "agile",
            "marketing", "sales", "customer service", "accounting", "finance",
            "design", "ui/ux", "photoshop", "illustrator", "writing", "content"
        }

        self.location_vocabulary = {
            "tokyo", "osaka", "kyoto", "nagoya", "fukuoka", "sendai", "hiroshima",
            "sapporo", "yokohama", "kobe", "shibuya", "shinjuku", "ginza"
        }

        self.industry_vocabulary = {
            "technology", "finance", "healthcare", "education", "retail",
            "manufacturing", "consulting", "media", "gaming", "startup",
            "enterprise", "government", "non-profit", "entertainment"
        }

    def extract_user_features(
        self,
        user_profile: UserProfile,
        interaction_history: List[UserInteraction]
    ) -> UserFeatures:
        """Extract numerical features from user profile and interactions"""

        # Skills vector (one-hot encoding)
        skills_vector = self._encode_skills(
            user_profile.job_preferences.get("skills", [])
        )

        # Experience level (normalized 0-1)
        experience_level = self._normalize_experience(
            user_profile.job_preferences.get("experience_years", 0)
        )

        # Salary expectation (normalized)
        salary_expectation = self._normalize_salary(
            user_profile.salary_range.get("max", 0) if user_profile.salary_range else 0
        )

        # Location preferences
        location_preferences = self._encode_locations([user_profile.location] if user_profile.location else [])

        # Industry preferences
        industry_preferences = self._encode_industries(
            user_profile.job_preferences.get("industries", [])
        )

        # Job type preferences
        job_type_preferences = self._encode_job_types(
            user_profile.job_preferences.get("job_types", [])
        )

        # Activity score based on interactions
        activity_score = self._calculate_activity_score(interaction_history)

        # Career stage inference
        career_stage = self._infer_career_stage(user_profile, interaction_history)

        return UserFeatures(
            user_id=user_profile.user_id,
            skills_vector=skills_vector,
            experience_level=experience_level,
            salary_expectation=salary_expectation,
            location_preferences=location_preferences,
            industry_preferences=industry_preferences,
            job_type_preferences=job_type_preferences,
            activity_score=activity_score,
            career_stage=career_stage,
            last_active=user_profile.last_active or datetime.now()
        )

    def extract_job_features(
        self,
        job: JobMatch,
        popularity_data: Dict[str, Any] = None
    ) -> JobFeatures:
        """Extract numerical features from job data"""

        # Skills required vector
        skills_required = self._encode_skills(job.tags)

        # Experience required (normalized)
        experience_required = self._normalize_experience(
            popularity_data.get("experience_required", 3) if popularity_data else 3
        )

        # Salary offered (normalized)
        salary_offered = self._normalize_salary(
            self._extract_salary_number(job.salary) if job.salary else 0
        )

        # Location vector
        location_vector = self._encode_locations([job.location])

        # Industry vector (inferred from company or tags)
        industry_vector = self._encode_industries(job.tags[:3])

        # Job type vector (full-time, part-time, contract, etc.)
        job_type_vector = self._encode_job_types(job.tags[-2:])

        # Popularity score
        popularity_score = popularity_data.get("popularity_score", 0.5) if popularity_data else 0.5

        # Freshness score (based on how new the job is)
        freshness_score = self._calculate_freshness_score(job)

        # Company rating (would come from external data)
        company_rating = popularity_data.get("company_rating", 0.7) if popularity_data else 0.7

        return JobFeatures(
            job_id=job.job_id,
            skills_required=skills_required,
            experience_required=experience_required,
            salary_offered=salary_offered,
            location_vector=location_vector,
            industry_vector=industry_vector,
            job_type_vector=job_type_vector,
            popularity_score=popularity_score,
            freshness_score=freshness_score,
            company_rating=company_rating
        )

    def _encode_skills(self, skills: List[str]) -> List[float]:
        """Encode skills as binary vector"""
        vector = [0.0] * len(self.skill_vocabulary)
        skill_list = list(self.skill_vocabulary)

        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in self.skill_vocabulary:
                index = skill_list.index(skill_lower)
                vector[index] = 1.0

        return vector

    def _encode_locations(self, locations: List[str]) -> List[float]:
        """Encode locations as binary vector"""
        vector = [0.0] * len(self.location_vocabulary)
        location_list = list(self.location_vocabulary)

        for location in locations:
            location_lower = location.lower()
            # Fuzzy matching for location names
            for vocab_location in self.location_vocabulary:
                if vocab_location in location_lower or location_lower in vocab_location:
                    index = location_list.index(vocab_location)
                    vector[index] = 1.0

        return vector

    def _encode_industries(self, industries: List[str]) -> List[float]:
        """Encode industries as binary vector"""
        vector = [0.0] * len(self.industry_vocabulary)
        industry_list = list(self.industry_vocabulary)

        for industry in industries:
            industry_lower = industry.lower()
            # Fuzzy matching for industry names
            for vocab_industry in self.industry_vocabulary:
                if vocab_industry in industry_lower or industry_lower in vocab_industry:
                    index = industry_list.index(vocab_industry)
                    vector[index] = 1.0

        return vector

    def _encode_job_types(self, job_types: List[str]) -> List[float]:
        """Encode job types as vector"""
        # Simple job type encoding
        type_map = {
            "full_time": 0, "part_time": 1, "contract": 2,
            "freelance": 3, "internship": 4, "remote": 5
        }

        vector = [0.0] * len(type_map)

        for job_type in job_types:
            job_type_lower = job_type.lower()
            for type_key in type_map:
                if type_key.replace("_", "") in job_type_lower.replace(" ", ""):
                    vector[type_map[type_key]] = 1.0

        return vector

    def _normalize_experience(self, years: int) -> float:
        """Normalize experience years to 0-1 scale"""
        return min(years / 20.0, 1.0)  # Cap at 20 years

    def _normalize_salary(self, salary: float) -> float:
        """Normalize salary to 0-1 scale"""
        # Assuming max salary of 20M yen
        return min(salary / 20_000_000, 1.0)

    def _extract_salary_number(self, salary_str: str) -> float:
        """Extract numerical salary from string"""
        try:
            # Simple extraction logic
            import re
            numbers = re.findall(r'\d+', salary_str.replace(',', ''))
            if numbers:
                base_salary = float(numbers[0])
                # Handle different units (万, thousand, etc.)
                if '万' in salary_str:
                    base_salary *= 10000
                return base_salary
        except:
            pass
        return 0.0

    def _calculate_activity_score(self, interactions: List[UserInteraction]) -> float:
        """Calculate user activity score"""
        if not interactions:
            return 0.1

        # Weight recent interactions more heavily
        now = datetime.now()
        score = 0.0

        for interaction in interactions:
            days_ago = (now - interaction.timestamp).days
            recency_weight = max(0.1, 1.0 - (days_ago / 365))  # Decay over a year
            interaction_weight = {
                "apply": 3.0,
                "save": 2.0,
                "view": 1.0,
                "share": 2.5,
                "reject": 0.5
            }.get(interaction.interaction_type, 1.0)

            score += recency_weight * interaction_weight * interaction.interaction_strength

        # Normalize to 0-1 scale
        return min(score / 100.0, 1.0)

    def _infer_career_stage(
        self,
        user_profile: UserProfile,
        interactions: List[UserInteraction]
    ) -> str:
        """Infer user's career stage"""
        experience_years = user_profile.job_preferences.get("experience_years", 0)

        if experience_years <= 2:
            return "entry_level"
        elif experience_years <= 5:
            return "mid_level"
        elif experience_years <= 10:
            return "senior_level"
        else:
            return "executive_level"

    def _calculate_freshness_score(self, job: JobMatch) -> float:
        """Calculate job freshness score"""
        # Since we don't have posted date in JobMatch, use is_new flag
        if job.is_new:
            return 1.0
        else:
            return 0.5  # Default value

# ============================================================================
# MATCHING ALGORITHMS
# ============================================================================

class CollaborativeFilteringMatcher:
    """Collaborative filtering recommendation engine"""

    def __init__(self):
        self.user_item_matrix = None
        self.user_similarity_matrix = None
        self.item_similarity_matrix = None

    async def train(self, interactions: List[UserInteraction]):
        """Train collaborative filtering model"""
        logger.info("Training collaborative filtering model...")

        # Build user-item interaction matrix
        users = list(set(i.user_id for i in interactions))
        items = list(set(i.job_id for i in interactions))

        user_idx = {user: idx for idx, user in enumerate(users)}
        item_idx = {item: idx for idx, item in enumerate(items)}

        matrix = np.zeros((len(users), len(items)))

        for interaction in interactions:
            u_idx = user_idx[interaction.user_id]
            i_idx = item_idx[interaction.job_id]

            # Weight different interaction types
            weight = {
                "apply": 5.0,
                "save": 3.0,
                "view": 1.0,
                "share": 4.0,
                "reject": -2.0
            }.get(interaction.interaction_type, 1.0)

            matrix[u_idx, i_idx] += weight * interaction.interaction_strength

        self.user_item_matrix = matrix
        self.user_idx_map = user_idx
        self.item_idx_map = item_idx

        # Calculate user similarity (cosine similarity)
        self.user_similarity_matrix = self._calculate_cosine_similarity(matrix)

        # Calculate item similarity
        self.item_similarity_matrix = self._calculate_cosine_similarity(matrix.T)

        logger.info(f"Collaborative filtering model trained with {len(users)} users and {len(items)} items")

    def _calculate_cosine_similarity(self, matrix: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity matrix"""
        # Normalize vectors
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = matrix / norms

        # Calculate cosine similarity
        similarity = np.dot(normalized, normalized.T)
        return similarity

    async def predict_user_job_score(self, user_id: int, job_id: int) -> float:
        """Predict score for user-job pair"""
        if self.user_item_matrix is None:
            return 0.5  # Default score if not trained

        if user_id not in self.user_idx_map or job_id not in self.item_idx_map:
            return 0.5

        user_idx = self.user_idx_map[user_id]
        item_idx = self.item_idx_map[job_id]

        # User-based collaborative filtering
        user_similarities = self.user_similarity_matrix[user_idx]
        user_ratings = self.user_item_matrix[:, item_idx]

        # Find similar users who have interacted with this job
        similar_users_mask = (user_ratings != 0) & (user_similarities > 0.1)

        if not np.any(similar_users_mask):
            return 0.5

        # Weighted average of similar users' ratings
        weights = user_similarities[similar_users_mask]
        ratings = user_ratings[similar_users_mask]

        predicted_score = np.average(ratings, weights=weights)

        # Normalize to 0-1 scale
        return max(0.0, min(1.0, (predicted_score + 5) / 10))  # Assume range -5 to 5

class ContentBasedMatcher:
    """Content-based filtering using feature similarity"""

    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor

    async def calculate_match_score(
        self,
        user_features: UserFeatures,
        job_features: JobFeatures
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate match score between user and job features"""

        scores = {}

        # Skills match (most important)
        skills_similarity = self._cosine_similarity(
            user_features.skills_vector,
            job_features.skills_required
        )
        scores["skills"] = skills_similarity

        # Location match
        location_similarity = self._cosine_similarity(
            user_features.location_preferences,
            job_features.location_vector
        )
        scores["location"] = location_similarity

        # Industry match
        industry_similarity = self._cosine_similarity(
            user_features.industry_preferences,
            job_features.industry_vector
        )
        scores["industry"] = industry_similarity

        # Experience level match
        experience_diff = abs(user_features.experience_level - job_features.experience_required)
        experience_score = max(0.0, 1.0 - experience_diff)
        scores["experience"] = experience_score

        # Salary compatibility
        if user_features.salary_expectation > 0 and job_features.salary_offered > 0:
            salary_ratio = min(job_features.salary_offered / user_features.salary_expectation, 1.0)
            salary_score = max(0.0, salary_ratio)
        else:
            salary_score = 0.7  # Neutral score if salary info missing
        scores["salary"] = salary_score

        # Job type match
        job_type_similarity = self._cosine_similarity(
            user_features.job_type_preferences,
            job_features.job_type_vector
        )
        scores["job_type"] = job_type_similarity

        # Company quality (external factor)
        scores["company_quality"] = job_features.company_rating

        # Freshness bonus
        scores["freshness"] = job_features.freshness_score

        # Weighted combination
        weights = {
            "skills": 0.30,
            "location": 0.20,
            "industry": 0.15,
            "experience": 0.15,
            "salary": 0.10,
            "job_type": 0.05,
            "company_quality": 0.03,
            "freshness": 0.02
        }

        overall_score = sum(scores[feature] * weights[feature] for feature in scores)

        return overall_score, scores

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

class HybridMatcher:
    """Hybrid recommendation combining multiple algorithms"""

    def __init__(
        self,
        collaborative_matcher: CollaborativeFilteringMatcher,
        content_based_matcher: ContentBasedMatcher
    ):
        self.collaborative_matcher = collaborative_matcher
        self.content_based_matcher = content_based_matcher

    async def calculate_hybrid_score(
        self,
        user_id: int,
        user_features: UserFeatures,
        job_id: int,
        job_features: JobFeatures,
        user_popularity_score: float = 0.5
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate hybrid recommendation score"""

        # Get collaborative filtering score
        cf_score = await self.collaborative_matcher.predict_user_job_score(user_id, job_id)

        # Get content-based score
        cb_score, cb_features = await self.content_based_matcher.calculate_match_score(
            user_features, job_features
        )

        # Popularity-based score
        popularity_score = job_features.popularity_score

        # Dynamic weighting based on user activity
        activity_level = user_features.activity_score

        # More active users get more weight on collaborative filtering
        cf_weight = 0.3 + (activity_level * 0.3)  # 0.3 to 0.6
        cb_weight = 0.7 - (activity_level * 0.3)  # 0.4 to 0.7
        popularity_weight = 0.1

        # Ensure weights sum to 1
        total_weight = cf_weight + cb_weight + popularity_weight
        cf_weight /= total_weight
        cb_weight /= total_weight
        popularity_weight /= total_weight

        # Combine scores
        hybrid_score = (
            cf_score * cf_weight +
            cb_score * cb_weight +
            popularity_score * popularity_weight
        )

        # Add diversity bonus for career growth recommendations
        diversity_bonus = self._calculate_diversity_bonus(user_features, job_features)
        hybrid_score = min(1.0, hybrid_score + diversity_bonus)

        explanation_data = {
            "collaborative_score": cf_score,
            "content_based_score": cb_score,
            "popularity_score": popularity_score,
            "weights": {
                "collaborative": cf_weight,
                "content_based": cb_weight,
                "popularity": popularity_weight
            },
            "diversity_bonus": diversity_bonus,
            "feature_scores": cb_features
        }

        return hybrid_score, explanation_data

    def _calculate_diversity_bonus(
        self,
        user_features: UserFeatures,
        job_features: JobFeatures
    ) -> float:
        """Calculate bonus for diverse recommendations"""
        # Encourage career growth and skill expansion
        skill_expansion_potential = 0.0

        # Check if job requires skills user doesn't have
        user_skills = set(i for i, val in enumerate(user_features.skills_vector) if val > 0)
        job_skills = set(i for i, val in enumerate(job_features.skills_required) if val > 0)

        new_skills = job_skills - user_skills
        if new_skills:
            # Small bonus for learning new skills
            skill_expansion_potential = min(0.05, len(new_skills) * 0.01)

        return skill_expansion_potential

# ============================================================================
# MAIN MATCHING SERVICE
# ============================================================================

class AdvancedMatchingService:
    """
    Advanced job matching service with multiple ML algorithms

    Provides sophisticated job recommendations using:
    - Collaborative filtering
    - Content-based filtering
    - Hybrid approaches
    - Popularity-based recommendations
    - Diversity optimization
    """

    def __init__(self, quality_level: MatchingQuality = MatchingQuality.STANDARD):
        self.quality_level = quality_level
        self.feature_extractor = FeatureExtractor()
        self.collaborative_matcher = CollaborativeFilteringMatcher()
        self.content_based_matcher = ContentBasedMatcher(self.feature_extractor)
        self.hybrid_matcher = HybridMatcher(
            self.collaborative_matcher,
            self.content_based_matcher
        )

        self.is_trained = False
        self.training_stats = {}

        logger.info(f"AdvancedMatchingService initialized with quality level: {quality_level.value}")

    async def train_models(
        self,
        user_profiles: List[UserProfile],
        job_data: List[JobMatch],
        interaction_history: List[UserInteraction]
    ):
        """Train all matching models with historical data"""
        logger.info("Starting model training...")

        start_time = datetime.now()

        # Train collaborative filtering
        await self.collaborative_matcher.train(interaction_history)

        # Extract and cache features for future use
        self.user_features_cache = {}
        self.job_features_cache = {}

        # Process users
        for user_profile in user_profiles:
            user_interactions = [
                i for i in interaction_history
                if i.user_id == user_profile.user_id
            ]
            user_features = self.feature_extractor.extract_user_features(
                user_profile, user_interactions
            )
            self.user_features_cache[user_profile.user_id] = user_features

        # Process jobs
        for job in job_data:
            job_features = self.feature_extractor.extract_job_features(job)
            self.job_features_cache[job.job_id] = job_features

        training_time = (datetime.now() - start_time).total_seconds()

        self.training_stats = {
            "training_time_seconds": training_time,
            "users_processed": len(user_profiles),
            "jobs_processed": len(job_data),
            "interactions_processed": len(interaction_history),
            "trained_at": datetime.now()
        }

        self.is_trained = True

        logger.info(
            f"Model training completed in {training_time:.2f} seconds. "
            f"Processed {len(user_profiles)} users, {len(job_data)} jobs, "
            f"and {len(interaction_history)} interactions."
        )

    async def get_recommendations(
        self,
        user_profile: UserProfile,
        available_jobs: List[JobMatch],
        interaction_history: List[UserInteraction] = None,
        algorithm: MatchingAlgorithm = MatchingAlgorithm.HYBRID,
        num_recommendations: int = 40,
        diversify: bool = True
    ) -> RecommendationSet:
        """
        Get personalized job recommendations for a user

        Args:
            user_profile: User profile data
            available_jobs: List of available jobs to recommend from
            interaction_history: User's interaction history
            algorithm: Matching algorithm to use
            num_recommendations: Number of recommendations to return
            diversify: Whether to optimize for diversity

        Returns:
            RecommendationSet with personalized recommendations
        """
        start_time = datetime.now()

        logger.info(
            f"Generating recommendations for user {user_profile.user_id} "
            f"using {algorithm.value} algorithm"
        )

        # Extract user features
        user_interactions = interaction_history or []
        user_features = self.feature_extractor.extract_user_features(
            user_profile, user_interactions
        )

        # Score all available jobs
        scoring_tasks = []
        for job in available_jobs:
            task = self._score_job_for_user(
                user_profile.user_id,
                user_features,
                job,
                algorithm
            )
            scoring_tasks.append(task)

        # Execute scoring concurrently
        job_scores = await asyncio.gather(*scoring_tasks)

        # Create matching results
        matching_results = []
        for i, (job, (score, explanation_data)) in enumerate(zip(available_jobs, job_scores)):
            result = MatchingResult(
                user_id=user_profile.user_id,
                job_id=job.job_id,
                match_score=score,
                algorithm_used=algorithm,
                confidence=explanation_data.get("confidence", 0.7),
                explanation=self._generate_explanation(explanation_data, job),
                feature_contributions=explanation_data.get("feature_scores", {}),
                recommendation_type=self._determine_recommendation_type(explanation_data, job)
            )
            matching_results.append(result)

        # Sort by score
        matching_results.sort(key=lambda x: x.match_score, reverse=True)

        # Apply diversification if requested
        if diversify:
            matching_results = self._diversify_recommendations(matching_results, available_jobs)

        # Take top N recommendations
        final_recommendations = matching_results[:num_recommendations]

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(final_recommendations, available_jobs)

        generation_time = (datetime.now() - start_time).total_seconds()

        recommendation_set = RecommendationSet(
            user_id=user_profile.user_id,
            recommendations=final_recommendations,
            algorithm_mix={algorithm: len(final_recommendations)},
            generated_at=datetime.now(),
            diversity_score=quality_metrics["diversity_score"],
            coverage_score=quality_metrics["coverage_score"],
            quality_metrics=quality_metrics
        )

        logger.info(
            f"Generated {len(final_recommendations)} recommendations for user "
            f"{user_profile.user_id} in {generation_time:.2f} seconds"
        )

        return recommendation_set

    async def _score_job_for_user(
        self,
        user_id: int,
        user_features: UserFeatures,
        job: JobMatch,
        algorithm: MatchingAlgorithm
    ) -> Tuple[float, Dict[str, Any]]:
        """Score a single job for a user"""

        job_features = self.feature_extractor.extract_job_features(job)

        if algorithm == MatchingAlgorithm.CONTENT_BASED:
            score, feature_scores = await self.content_based_matcher.calculate_match_score(
                user_features, job_features
            )
            explanation_data = {
                "content_based_score": score,
                "feature_scores": feature_scores,
                "confidence": 0.8
            }

        elif algorithm == MatchingAlgorithm.COLLABORATIVE_FILTERING:
            score = await self.collaborative_matcher.predict_user_job_score(user_id, job.job_id)
            explanation_data = {
                "collaborative_score": score,
                "confidence": 0.7 if self.is_trained else 0.3
            }

        elif algorithm == MatchingAlgorithm.HYBRID:
            score, explanation_data = await self.hybrid_matcher.calculate_hybrid_score(
                user_id, user_features, job.job_id, job_features
            )
            explanation_data["confidence"] = 0.85 if self.is_trained else 0.6

        elif algorithm == MatchingAlgorithm.POPULARITY_BASED:
            score = job_features.popularity_score * 0.7 + job_features.freshness_score * 0.3
            explanation_data = {
                "popularity_score": job_features.popularity_score,
                "freshness_score": job_features.freshness_score,
                "confidence": 0.6
            }

        else:
            # Default to content-based
            score, feature_scores = await self.content_based_matcher.calculate_match_score(
                user_features, job_features
            )
            explanation_data = {
                "content_based_score": score,
                "feature_scores": feature_scores,
                "confidence": 0.8
            }

        return score, explanation_data

    def _generate_explanation(self, explanation_data: Dict[str, Any], job: JobMatch) -> str:
        """Generate human-readable explanation for the match"""

        explanations = []

        if "feature_scores" in explanation_data:
            feature_scores = explanation_data["feature_scores"]

            # Skills match
            if feature_scores.get("skills", 0) > 0.7:
                explanations.append("あなたのスキルと高い適合性があります")

            # Location match
            if feature_scores.get("location", 0) > 0.8:
                explanations.append("希望地域に近い勤務地です")

            # Industry match
            if feature_scores.get("industry", 0) > 0.7:
                explanations.append("ご希望の業界の求人です")

            # Experience match
            if feature_scores.get("experience", 0) > 0.8:
                explanations.append("あなたの経験レベルに適しています")

        # Collaborative filtering insights
        if explanation_data.get("collaborative_score", 0) > 0.7:
            explanations.append("類似のプロフィールの方に人気があります")

        # Popularity insights
        if explanation_data.get("popularity_score", 0) > 0.8:
            explanations.append("多くの方から注目されている求人です")

        if not explanations:
            explanations.append("バランスの取れたマッチングです")

        return "。".join(explanations) + "。"

    def _determine_recommendation_type(
        self,
        explanation_data: Dict[str, Any],
        job: JobMatch
    ) -> RecommendationType:
        """Determine the type of recommendation"""

        if job.is_popular:
            return RecommendationType.TRENDING

        if explanation_data.get("collaborative_score", 0) > 0.8:
            return RecommendationType.SIMILAR_USERS

        if explanation_data.get("feature_scores", {}).get("location", 0) > 0.8:
            return RecommendationType.LOCATION_BASED

        if explanation_data.get("feature_scores", {}).get("skills", 0) > 0.8:
            return RecommendationType.SKILL_MATCH

        if explanation_data.get("diversity_bonus", 0) > 0:
            return RecommendationType.CAREER_GROWTH

        return RecommendationType.PERSONAL

    def _diversify_recommendations(
        self,
        recommendations: List[MatchingResult],
        available_jobs: List[JobMatch]
    ) -> List[MatchingResult]:
        """Apply diversification to avoid echo chamber effect"""

        if len(recommendations) <= 10:
            return recommendations

        # Create job lookup
        job_lookup = {job.job_id: job for job in available_jobs}

        # Group by company to avoid over-representation
        company_groups = defaultdict(list)
        for rec in recommendations:
            job = job_lookup.get(rec.job_id)
            if job:
                company_groups[job.company].append(rec)

        # Limit recommendations per company
        diversified = []
        max_per_company = max(2, len(recommendations) // 10)  # At most 10% from same company

        for company, company_recs in company_groups.items():
            # Take top recommendations from each company
            company_recs.sort(key=lambda x: x.match_score, reverse=True)
            diversified.extend(company_recs[:max_per_company])

        # Sort again by score
        diversified.sort(key=lambda x: x.match_score, reverse=True)

        return diversified

    def _calculate_quality_metrics(
        self,
        recommendations: List[MatchingResult],
        available_jobs: List[JobMatch]
    ) -> Dict[str, float]:
        """Calculate quality metrics for the recommendation set"""

        if not recommendations:
            return {"diversity_score": 0.0, "coverage_score": 0.0}

        # Create job lookup
        job_lookup = {job.job_id: job for job in available_jobs}

        # Diversity metrics
        companies = set()
        locations = set()
        for rec in recommendations:
            job = job_lookup.get(rec.job_id)
            if job:
                companies.add(job.company)
                locations.add(job.location)

        diversity_score = min(1.0, (len(companies) + len(locations)) / len(recommendations))

        # Coverage score (how well we cover the score spectrum)
        scores = [rec.match_score for rec in recommendations]
        if len(scores) > 1:
            score_range = max(scores) - min(scores)
            coverage_score = min(1.0, score_range / 0.5)  # Normalize to 0.5 range
        else:
            coverage_score = 0.5

        # Average confidence
        avg_confidence = sum(rec.confidence for rec in recommendations) / len(recommendations)

        # Quality distribution
        high_quality = sum(1 for rec in recommendations if rec.match_score > 0.8)
        medium_quality = sum(1 for rec in recommendations if 0.6 <= rec.match_score <= 0.8)
        low_quality = len(recommendations) - high_quality - medium_quality

        return {
            "diversity_score": diversity_score,
            "coverage_score": coverage_score,
            "avg_confidence": avg_confidence,
            "high_quality_count": high_quality,
            "medium_quality_count": medium_quality,
            "low_quality_count": low_quality,
            "unique_companies": len(companies),
            "unique_locations": len(locations)
        }

    def get_training_stats(self) -> Dict[str, Any]:
        """Get model training statistics"""
        return self.training_stats.copy()

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance weights"""
        return {
            "skills": 0.30,
            "location": 0.20,
            "industry": 0.15,
            "experience": 0.15,
            "salary": 0.10,
            "job_type": 0.05,
            "company_quality": 0.03,
            "freshness": 0.02
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def create_advanced_matching_service(
    quality_level: MatchingQuality = MatchingQuality.STANDARD
) -> AdvancedMatchingService:
    """Create and configure an advanced matching service"""
    return AdvancedMatchingService(quality_level)

async def batch_generate_recommendations(
    matching_service: AdvancedMatchingService,
    user_profiles: List[UserProfile],
    available_jobs: List[JobMatch],
    algorithm: MatchingAlgorithm = MatchingAlgorithm.HYBRID
) -> List[RecommendationSet]:
    """Generate recommendations for multiple users concurrently"""

    tasks = [
        matching_service.get_recommendations(
            user_profile,
            available_jobs,
            algorithm=algorithm
        )
        for user_profile in user_profiles
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to generate recommendations for user {i}: {result}")
        else:
            valid_results.append(result)

    return valid_results

# ============================================================================
# TESTING UTILITIES
# ============================================================================

async def test_advanced_matching():
    """Test the advanced matching service with sample data"""

    # Create test service
    matching_service = await create_advanced_matching_service(MatchingQuality.PREMIUM)

    # Create test users
    test_users = [
        UserProfile(
            user_id=1,
            name="田中太郎",
            email="tanaka@example.com",
            preferred_language="ja",
            location="東京都渋谷区",
            job_preferences={
                "skills": ["Python", "機械学習", "データ分析"],
                "industries": ["IT", "金融"],
                "experience_years": 5
            },
            salary_range={"min": 6000000, "max": 8000000}
        ),
        UserProfile(
            user_id=2,
            name="佐藤花子",
            email="sato@example.com",
            preferred_language="ja",
            location="東京都新宿区",
            job_preferences={
                "skills": ["JavaScript", "React", "Node.js"],
                "industries": ["IT", "スタートアップ"],
                "experience_years": 3
            },
            salary_range={"min": 5000000, "max": 7000000}
        )
    ]

    # Create test jobs
    test_jobs = [
        JobMatch(
            job_id=1,
            title="データサイエンティスト",
            company="テックコーポ",
            location="東京都",
            salary="600-800万円",
            description="機械学習を活用したデータ分析",
            match_score=0.0,  # Will be calculated
            tags=["Python", "機械学習", "統計", "IT"],
            is_new=True,
            is_popular=True
        ),
        JobMatch(
            job_id=2,
            title="フロントエンドエンジニア",
            company="ウェブ株式会社",
            location="東京都新宿区",
            salary="500-700万円",
            description="Reactを使ったWebアプリケーション開発",
            match_score=0.0,
            tags=["JavaScript", "React", "CSS", "IT"],
            is_new=False,
            is_popular=True
        ),
        JobMatch(
            job_id=3,
            title="バックエンドエンジニア",
            company="サーバーシステムズ",
            location="東京都港区",
            salary="650-850万円",
            description="Node.jsを使ったAPI開発",
            match_score=0.0,
            tags=["Node.js", "API", "データベース", "IT"],
            is_new=True,
            is_popular=False
        )
    ]

    # Create test interactions
    test_interactions = [
        UserInteraction(
            user_id=1,
            job_id=1,
            interaction_type="view",
            timestamp=datetime.now() - timedelta(days=1),
            interaction_strength=1.0
        ),
        UserInteraction(
            user_id=1,
            job_id=1,
            interaction_type="save",
            timestamp=datetime.now() - timedelta(hours=12),
            interaction_strength=2.0
        ),
        UserInteraction(
            user_id=2,
            job_id=2,
            interaction_type="apply",
            timestamp=datetime.now() - timedelta(days=2),
            interaction_strength=3.0
        )
    ]

    # Train models
    await matching_service.train_models(test_users, test_jobs, test_interactions)

    # Test different algorithms
    algorithms = [
        MatchingAlgorithm.CONTENT_BASED,
        MatchingAlgorithm.COLLABORATIVE_FILTERING,
        MatchingAlgorithm.HYBRID
    ]

    for algorithm in algorithms:
        print(f"\n=== Testing {algorithm.value.upper()} ===")

        for user in test_users:
            recommendations = await matching_service.get_recommendations(
                user, test_jobs, test_interactions, algorithm=algorithm, num_recommendations=3
            )

            print(f"\nUser: {user.name}")
            print(f"Algorithm: {algorithm.value}")
            print(f"Generated: {len(recommendations.recommendations)} recommendations")
            print(f"Diversity Score: {recommendations.diversity_score:.2f}")

            for i, rec in enumerate(recommendations.recommendations, 1):
                job = next(j for j in test_jobs if j.job_id == rec.job_id)
                print(f"  {i}. {job.title} @ {job.company}")
                print(f"     Score: {rec.match_score:.3f}")
                print(f"     Type: {rec.recommendation_type.value}")
                print(f"     Explanation: {rec.explanation}")

    # Show training stats
    stats = matching_service.get_training_stats()
    print(f"\n=== Training Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_advanced_matching())