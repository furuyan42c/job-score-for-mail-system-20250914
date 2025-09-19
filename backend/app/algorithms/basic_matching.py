"""
Basic Skills-Based Matching Algorithm (T017)
Implements fundamental job matching based on skills overlap and basic criteria
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class MatchCriteria(str, Enum):
    """Matching criteria types"""
    SKILLS = "skills"
    LOCATION = "location"
    SALARY = "salary"
    EXPERIENCE = "experience"
    CATEGORY = "category"


@dataclass
class JobData:
    """Job data structure for matching"""
    job_id: int
    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    category: str
    location: str
    prefecture_code: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    experience_required: Optional[str]
    employment_type: str
    description: str


@dataclass
class UserProfile:
    """User profile structure for matching"""
    user_id: int
    skills: List[str]
    preferred_categories: List[str]
    preferred_location: str
    prefecture_code: str
    salary_min: Optional[int]
    max_commute_distance: int
    experience_level: Optional[str]
    job_types: List[str]


@dataclass
class MatchScore:
    """Match score breakdown"""
    total_score: int
    skills_score: int
    location_score: int
    salary_score: int
    category_score: int
    experience_score: int
    details: Dict[str, Any]


class BasicMatchingAlgorithm:
    """
    Basic skills-based matching algorithm

    Calculates job match scores based on:
    - Skills overlap (required and preferred)
    - Location proximity
    - Salary compatibility
    - Category match
    - Experience level match
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize algorithm with optional custom weights

        Args:
            weights: Custom weights for different criteria
        """
        self.default_weights = {
            "skills": 0.4,      # 40% - Most important
            "location": 0.2,    # 20%
            "salary": 0.2,      # 20%
            "category": 0.1,    # 10%
            "experience": 0.1   # 10%
        }
        self.weights = weights or self.default_weights

        # Validate weights sum to 1.0
        if abs(sum(self.weights.values()) - 1.0) > 0.01:
            logger.warning(f"Weights do not sum to 1.0: {sum(self.weights.values())}")

    def calculate_match_score(self, user: UserProfile, job: JobData) -> MatchScore:
        """
        Calculate overall match score between user and job

        Args:
            user: User profile
            job: Job data

        Returns:
            MatchScore with breakdown and total score
        """
        try:
            # Calculate individual scores
            skills_score = self._calculate_skills_score(user, job)
            location_score = self._calculate_location_score(user, job)
            salary_score = self._calculate_salary_score(user, job)
            category_score = self._calculate_category_score(user, job)
            experience_score = self._calculate_experience_score(user, job)

            # Calculate weighted total
            total_score = (
                skills_score * self.weights["skills"] +
                location_score * self.weights["location"] +
                salary_score * self.weights["salary"] +
                category_score * self.weights["category"] +
                experience_score * self.weights["experience"]
            )

            # Ensure score is in range 0-100
            total_score = max(0, min(100, int(total_score)))

            return MatchScore(
                total_score=total_score,
                skills_score=skills_score,
                location_score=location_score,
                salary_score=salary_score,
                category_score=category_score,
                experience_score=experience_score,
                details={
                    "algorithm": "basic_matching",
                    "version": "1.0",
                    "weights": self.weights,
                    "user_id": user.user_id,
                    "job_id": job.job_id
                }
            )

        except Exception as e:
            logger.error(f"Error calculating match score for user {user.user_id}, job {job.job_id}: {e}")
            return MatchScore(
                total_score=0,
                skills_score=0,
                location_score=0,
                salary_score=0,
                category_score=0,
                experience_score=0,
                details={"error": str(e)}
            )

    def _calculate_skills_score(self, user: UserProfile, job: JobData) -> int:
        """
        Calculate skills match score

        Considers both required and preferred skills with different weights
        """
        if not user.skills:
            return 0

        user_skills_lower = [skill.lower().strip() for skill in user.skills]
        required_skills_lower = [skill.lower().strip() for skill in job.required_skills]
        preferred_skills_lower = [skill.lower().strip() for skill in job.preferred_skills]

        # Required skills match (70% of skills score)
        required_matches = len(set(user_skills_lower) & set(required_skills_lower))
        required_total = len(required_skills_lower) if required_skills_lower else 1
        required_score = (required_matches / required_total) * 70

        # Preferred skills match (30% of skills score)
        preferred_matches = len(set(user_skills_lower) & set(preferred_skills_lower))
        preferred_total = len(preferred_skills_lower) if preferred_skills_lower else 1
        preferred_score = (preferred_matches / preferred_total) * 30

        total_skills_score = required_score + preferred_score
        return min(100, int(total_skills_score))

    def _calculate_location_score(self, user: UserProfile, job: JobData) -> int:
        """
        Calculate location match score

        Based on prefecture match and commute distance preferences
        """
        # Exact prefecture match gets high score
        if user.prefecture_code == job.prefecture_code:
            return 100

        # Adjacent prefectures get medium score
        # (In production, this would use actual geographic data)
        adjacent_prefs = self._get_adjacent_prefectures(user.prefecture_code)
        if job.prefecture_code in adjacent_prefs:
            return 60

        # Remote work or flexible location
        if "remote" in job.employment_type.lower() or "在宅" in job.employment_type:
            return 80

        # Distant locations get low score
        return 20

    def _calculate_salary_score(self, user: UserProfile, job: JobData) -> int:
        """
        Calculate salary compatibility score
        """
        # If no salary requirements from user, give neutral score
        if not user.salary_min:
            return 70

        # If job doesn't specify salary, give lower score
        if not job.salary_max:
            return 50

        # Check if job salary meets user minimum
        if job.salary_max >= user.salary_min:
            # Calculate how much above minimum (bonus points)
            excess_ratio = (job.salary_max - user.salary_min) / user.salary_min
            bonus = min(30, excess_ratio * 20)  # Up to 30 bonus points
            return min(100, 70 + int(bonus))
        else:
            # Job salary below user minimum
            shortfall_ratio = (user.salary_min - job.salary_max) / user.salary_min
            penalty = shortfall_ratio * 50
            return max(0, int(50 - penalty))

    def _calculate_category_score(self, user: UserProfile, job: JobData) -> int:
        """
        Calculate job category match score
        """
        if not user.preferred_categories:
            return 70  # Neutral score if no preferences

        # Direct category match
        if job.category in user.preferred_categories:
            return 100

        # Related category matching (basic implementation)
        related_categories = self._get_related_categories(job.category)
        for user_cat in user.preferred_categories:
            if user_cat in related_categories:
                return 70

        return 30  # Low score for unrelated categories

    def _calculate_experience_score(self, user: UserProfile, job: JobData) -> int:
        """
        Calculate experience level match score
        """
        if not user.experience_level or not job.experience_required:
            return 70  # Neutral score if no data

        experience_levels = {
            "entry": 1,
            "junior": 2,
            "mid": 3,
            "senior": 4,
            "expert": 5
        }

        user_level = experience_levels.get(user.experience_level.lower(), 3)
        job_level = experience_levels.get(job.experience_required.lower(), 3)

        # Perfect match
        if user_level == job_level:
            return 100

        # User has more experience than required (overqualified)
        if user_level > job_level:
            diff = user_level - job_level
            return max(60, 100 - (diff * 15))  # Slight penalty for overqualification

        # User has less experience than required
        if user_level < job_level:
            diff = job_level - user_level
            return max(20, 80 - (diff * 20))  # Penalty for underqualification

        return 70

    def _get_adjacent_prefectures(self, pref_code: str) -> List[str]:
        """
        Get adjacent prefecture codes (simplified implementation)
        """
        # Simplified mapping - in production would use geographic data
        adjacent_map = {
            "13": ["12", "14", "19", "22"],  # Tokyo
            "14": ["13", "12", "15"],        # Kanagawa
            "12": ["13", "14", "11", "20"],  # Chiba
            # Add more mappings as needed
        }
        return adjacent_map.get(pref_code, [])

    def _get_related_categories(self, category: str) -> List[str]:
        """
        Get related job categories (simplified implementation)
        """
        # Simplified category relationships
        related_map = {
            "IT": ["Software", "Engineering", "Tech"],
            "Finance": ["Banking", "Insurance", "Accounting"],
            "Sales": ["Marketing", "Business Development"],
            # Add more relationships as needed
        }
        return related_map.get(category, [])

    def batch_calculate_scores(self, user: UserProfile, jobs: List[JobData]) -> List[Tuple[int, MatchScore]]:
        """
        Calculate scores for multiple jobs for a user

        Args:
            user: User profile
            jobs: List of job data

        Returns:
            List of tuples (job_id, match_score) sorted by score descending
        """
        results = []

        for job in jobs:
            try:
                score = self.calculate_match_score(user, job)
                results.append((job.job_id, score))
            except Exception as e:
                logger.error(f"Error processing job {job.job_id}: {e}")
                continue

        # Sort by total score descending
        results.sort(key=lambda x: x[1].total_score, reverse=True)
        return results

    def get_top_matches(self, user: UserProfile, jobs: List[JobData], limit: int = 10) -> List[Tuple[int, MatchScore]]:
        """
        Get top N matches for a user

        Args:
            user: User profile
            jobs: List of job data
            limit: Maximum number of matches to return

        Returns:
            Top matches sorted by score
        """
        all_scores = self.batch_calculate_scores(user, jobs)
        return all_scores[:limit]

    def filter_by_minimum_score(self, scores: List[Tuple[int, MatchScore]], min_score: int = 50) -> List[Tuple[int, MatchScore]]:
        """
        Filter matches by minimum score threshold

        Args:
            scores: List of (job_id, match_score) tuples
            min_score: Minimum score threshold

        Returns:
            Filtered list of matches
        """
        return [(job_id, score) for job_id, score in scores if score.total_score >= min_score]