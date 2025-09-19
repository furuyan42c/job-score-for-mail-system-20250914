"""
Matching Service for Job Recommendation System (T017-T020)
Coordinates matching algorithms, filtering, sorting, and history tracking
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
import logging
from enum import Enum

from app.algorithms.basic_matching import BasicMatchingAlgorithm, JobData, UserProfile, MatchScore
from app.algorithms.weighted_matching import WeightedMatchingAlgorithm, UserBehaviorData, JobInteractionData
from app.models.database import User, MatchingScore, MatchHistory

logger = logging.getLogger(__name__)


class AlgorithmType(str, Enum):
    """Available matching algorithms"""
    BASIC = "basic"
    WEIGHTED = "weighted"
    HYBRID = "hybrid"


class SortOrder(str, Enum):
    """Sort order options"""
    SCORE_DESC = "score_desc"
    SCORE_ASC = "score_asc"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    SALARY_DESC = "salary_desc"
    SALARY_ASC = "salary_asc"


class MatchFilter:
    """Filter criteria for match results"""
    def __init__(self,
                 min_score: Optional[int] = None,
                 max_score: Optional[int] = None,
                 categories: Optional[List[str]] = None,
                 locations: Optional[List[str]] = None,
                 salary_min: Optional[int] = None,
                 salary_max: Optional[int] = None,
                 experience_levels: Optional[List[str]] = None,
                 exclude_applied: bool = True,
                 exclude_viewed: bool = False):
        self.min_score = min_score
        self.max_score = max_score
        self.categories = categories or []
        self.locations = locations or []
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.experience_levels = experience_levels or []
        self.exclude_applied = exclude_applied
        self.exclude_viewed = exclude_viewed


class MatchingService:
    """
    Service for job matching operations

    Handles:
    - Algorithm selection and execution
    - Result filtering and sorting
    - Match history tracking
    - Performance monitoring
    """

    def __init__(self, db: Session):
        self.db = db
        self.basic_algorithm = BasicMatchingAlgorithm()
        self.weighted_algorithm = WeightedMatchingAlgorithm()

    async def find_matches(self,
                          user_id: int,
                          algorithm: AlgorithmType = AlgorithmType.WEIGHTED,
                          limit: int = 50,
                          filters: Optional[MatchFilter] = None,
                          sort_order: SortOrder = SortOrder.SCORE_DESC) -> List[Dict[str, Any]]:
        """
        Find job matches for a user

        Args:
            user_id: User ID
            algorithm: Matching algorithm to use
            limit: Maximum number of results
            filters: Filter criteria
            sort_order: Sort order for results

        Returns:
            List of match results with scores and job details
        """
        try:
            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User {user_id} not found")

            # Get available jobs
            jobs = await self._get_available_jobs(user_id, filters)
            if not jobs:
                return []

            # Calculate matches using selected algorithm
            if algorithm == AlgorithmType.BASIC:
                matches = await self._calculate_basic_matches(user_profile, jobs)
            elif algorithm == AlgorithmType.WEIGHTED:
                matches = await self._calculate_weighted_matches(user_profile, jobs, user_id)
            elif algorithm == AlgorithmType.HYBRID:
                matches = await self._calculate_hybrid_matches(user_profile, jobs, user_id)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            # Apply filters
            if filters:
                matches = self._apply_filters(matches, filters)

            # Sort results
            matches = self._sort_matches(matches, sort_order)

            # Limit results
            matches = matches[:limit]

            # Store match history
            await self._store_match_history(user_id, matches, algorithm)

            # Convert to response format
            return [self._format_match_result(match, job_data)
                   for match, job_data in matches]

        except Exception as e:
            logger.error(f"Error finding matches for user {user_id}: {e}")
            raise

    async def get_match_history(self,
                               user_id: int,
                               limit: int = 100,
                               include_interactions: bool = True) -> List[Dict[str, Any]]:
        """
        Get user's match history

        Args:
            user_id: User ID
            limit: Maximum number of records
            include_interactions: Include interaction data

        Returns:
            List of historical matches with interaction data
        """
        try:
            query = self.db.query(MatchHistory).filter(
                MatchHistory.user_id == user_id
            ).order_by(desc(MatchHistory.matched_at)).limit(limit)

            history_records = query.all()

            results = []
            for record in history_records:
                result = {
                    "match_id": record.id,
                    "job_id": record.job_id,
                    "match_score": record.match_score,
                    "algorithm_used": record.algorithm_used,
                    "match_rank": record.match_rank,
                    "matched_at": record.matched_at.isoformat()
                }

                if include_interactions:
                    result.update({
                        "viewed": record.viewed,
                        "clicked": record.clicked,
                        "applied": record.applied,
                        "favorited": record.favorited,
                        "hidden": record.hidden,
                        "viewed_at": record.viewed_at.isoformat() if record.viewed_at else None,
                        "clicked_at": record.clicked_at.isoformat() if record.clicked_at else None,
                        "applied_at": record.applied_at.isoformat() if record.applied_at else None,
                        "favorited_at": record.favorited_at.isoformat() if record.favorited_at else None,
                        "user_feedback": record.user_feedback,
                        "feedback_reason": record.feedback_reason
                    })

                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error getting match history for user {user_id}: {e}")
            raise

    async def record_interaction(self,
                                user_id: int,
                                job_id: int,
                                interaction_type: str,
                                feedback: Optional[str] = None,
                                feedback_reason: Optional[str] = None) -> bool:
        """
        Record user interaction with a matched job

        Args:
            user_id: User ID
            job_id: Job ID
            interaction_type: Type of interaction (viewed, clicked, applied, favorited, hidden)
            feedback: User feedback (interested, not_interested, maybe)
            feedback_reason: Reason for feedback

        Returns:
            True if recorded successfully
        """
        try:
            # Find existing match history record
            match_record = self.db.query(MatchHistory).filter(
                and_(
                    MatchHistory.user_id == user_id,
                    MatchHistory.job_id == job_id
                )
            ).first()

            if not match_record:
                # Create new record if doesn't exist
                match_record = MatchHistory(
                    user_id=user_id,
                    job_id=job_id,
                    match_score=0,  # Will be updated when we have the score
                    algorithm_used="unknown",
                    matched_at=datetime.utcnow()
                )
                self.db.add(match_record)

            # Update interaction fields
            current_time = datetime.utcnow()

            if interaction_type == "viewed":
                match_record.viewed = True
                if not match_record.viewed_at:
                    match_record.viewed_at = current_time
            elif interaction_type == "clicked":
                match_record.clicked = True
                match_record.clicked_at = current_time
                # Auto-mark as viewed
                if not match_record.viewed:
                    match_record.viewed = True
                    match_record.viewed_at = current_time
            elif interaction_type == "applied":
                match_record.applied = True
                match_record.applied_at = current_time
                # Auto-mark as clicked and viewed
                if not match_record.clicked:
                    match_record.clicked = True
                    match_record.clicked_at = current_time
                if not match_record.viewed:
                    match_record.viewed = True
                    match_record.viewed_at = current_time
            elif interaction_type == "favorited":
                match_record.favorited = True
                match_record.favorited_at = current_time
            elif interaction_type == "hidden":
                match_record.hidden = True

            # Update feedback
            if feedback:
                match_record.user_feedback = feedback
            if feedback_reason:
                match_record.feedback_reason = feedback_reason

            match_record.updated_at = current_time

            self.db.commit()

            # Update algorithm weights based on feedback (for weighted algorithm)
            if feedback and hasattr(self.weighted_algorithm, 'update_user_weights'):
                engagement_score = self._calculate_engagement_score(interaction_type, feedback)
                self.weighted_algorithm.update_user_weights(
                    user_id, job_id, feedback, match_record.match_score, engagement_score
                )

            logger.info(f"Recorded {interaction_type} interaction for user {user_id}, job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
            self.db.rollback()
            return False

    async def get_recommendation_metrics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get recommendation performance metrics for a user

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Dictionary with performance metrics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Query match history for the period
            history = self.db.query(MatchHistory).filter(
                and_(
                    MatchHistory.user_id == user_id,
                    MatchHistory.matched_at >= since_date
                )
            ).all()

            if not history:
                return {
                    "total_matches": 0,
                    "metrics": {}
                }

            total_matches = len(history)
            viewed_count = sum(1 for h in history if h.viewed)
            clicked_count = sum(1 for h in history if h.clicked)
            applied_count = sum(1 for h in history if h.applied)
            favorited_count = sum(1 for h in history if h.favorited)

            # Calculate rates
            view_rate = viewed_count / total_matches if total_matches > 0 else 0
            click_through_rate = clicked_count / viewed_count if viewed_count > 0 else 0
            application_rate = applied_count / clicked_count if clicked_count > 0 else 0
            favorite_rate = favorited_count / viewed_count if viewed_count > 0 else 0

            # Feedback analysis
            positive_feedback = sum(1 for h in history if h.user_feedback == "interested")
            negative_feedback = sum(1 for h in history if h.user_feedback == "not_interested")
            total_feedback = positive_feedback + negative_feedback

            return {
                "period_days": days,
                "total_matches": total_matches,
                "interactions": {
                    "viewed": viewed_count,
                    "clicked": clicked_count,
                    "applied": applied_count,
                    "favorited": favorited_count
                },
                "rates": {
                    "view_rate": round(view_rate, 3),
                    "click_through_rate": round(click_through_rate, 3),
                    "application_rate": round(application_rate, 3),
                    "favorite_rate": round(favorite_rate, 3)
                },
                "feedback": {
                    "positive": positive_feedback,
                    "negative": negative_feedback,
                    "total": total_feedback,
                    "satisfaction_rate": round(positive_feedback / total_feedback, 3) if total_feedback > 0 else 0
                },
                "avg_match_score": round(sum(h.match_score for h in history) / total_matches, 1) if total_matches > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error calculating metrics for user {user_id}: {e}")
            raise

    # Private helper methods
    async def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile for matching"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None

        return UserProfile(
            user_id=user.user_id,
            skills=user.skills or [],
            preferred_categories=user.preferred_industries or [],
            preferred_location=user.pref_cd or "",
            prefecture_code=user.pref_cd or "",
            salary_min=None,  # Would get from preferences
            max_commute_distance=30,  # Default
            experience_level=None,  # Would determine from profile
            job_types=["full_time"]  # Default
        )

    async def _get_available_jobs(self, user_id: int, filters: Optional[MatchFilter]) -> List[JobData]:
        """Get available jobs for matching (placeholder)"""
        # In production, this would query the job database
        # For now, return mock data
        mock_jobs = [
            JobData(
                job_id=1,
                title="Python Developer",
                required_skills=["Python", "SQL"],
                preferred_skills=["FastAPI", "PostgreSQL"],
                category="IT",
                location="Tokyo",
                prefecture_code="13",
                salary_min=4000000,
                salary_max=6000000,
                experience_required="mid",
                employment_type="full_time",
                description="Python developer position"
            ),
            JobData(
                job_id=2,
                title="Data Scientist",
                required_skills=["Python", "Machine Learning"],
                preferred_skills=["TensorFlow", "Pandas"],
                category="IT",
                location="Osaka",
                prefecture_code="27",
                salary_min=5000000,
                salary_max=8000000,
                experience_required="senior",
                employment_type="full_time",
                description="Data scientist position"
            )
        ]
        return mock_jobs

    async def _calculate_basic_matches(self, user: UserProfile, jobs: List[JobData]) -> List[Tuple[MatchScore, JobData]]:
        """Calculate matches using basic algorithm"""
        results = []
        for job in jobs:
            score = self.basic_algorithm.calculate_match_score(user, job)
            results.append((score, job))
        return results

    async def _calculate_weighted_matches(self, user: UserProfile, jobs: List[JobData], user_id: int) -> List[Tuple[MatchScore, JobData]]:
        """Calculate matches using weighted algorithm"""
        # Get user behavior data
        user_behavior = await self._get_user_behavior_data(user_id)

        results = []
        for job in jobs:
            # Get job interaction data
            job_interactions = await self._get_job_interaction_data(job.job_id)

            score = self.weighted_algorithm.calculate_weighted_score(
                user, job, user_behavior, job_interactions
            )
            results.append((score, job))
        return results

    async def _calculate_hybrid_matches(self, user: UserProfile, jobs: List[JobData], user_id: int) -> List[Tuple[MatchScore, JobData]]:
        """Calculate matches using hybrid approach"""
        # Combine basic and weighted algorithms
        basic_matches = await self._calculate_basic_matches(user, jobs)
        weighted_matches = await self._calculate_weighted_matches(user, jobs, user_id)

        # Average the scores (simplified hybrid approach)
        results = []
        for (basic_score, job), (weighted_score, _) in zip(basic_matches, weighted_matches):
            hybrid_score = MatchScore(
                total_score=int((basic_score.total_score + weighted_score.total_score) / 2),
                skills_score=int((basic_score.skills_score + weighted_score.skills_score) / 2),
                location_score=int((basic_score.location_score + weighted_score.location_score) / 2),
                salary_score=int((basic_score.salary_score + weighted_score.salary_score) / 2),
                category_score=int((basic_score.category_score + weighted_score.category_score) / 2),
                experience_score=int((basic_score.experience_score + weighted_score.experience_score) / 2),
                details={"algorithm": "hybrid", "basic_score": basic_score.total_score, "weighted_score": weighted_score.total_score}
            )
            results.append((hybrid_score, job))

        return results

    async def _get_user_behavior_data(self, user_id: int) -> Optional[UserBehaviorData]:
        """Get user behavior data for weighted algorithm"""
        # Query match history for user behavior
        history = self.db.query(MatchHistory).filter(
            MatchHistory.user_id == user_id
        ).all()

        if not history:
            return None

        return UserBehaviorData(
            user_id=user_id,
            job_applications=[h.job_id for h in history if h.applied],
            job_clicks=[h.job_id for h in history if h.clicked],
            job_views=[h.job_id for h in history if h.viewed],
            feedback_history={h.job_id: h.user_feedback for h in history if h.user_feedback},
            last_activity=max(h.updated_at for h in history) if history else None
        )

    async def _get_job_interaction_data(self, job_id: int) -> Optional[JobInteractionData]:
        """Get job interaction statistics"""
        # Query interaction statistics for job
        interactions = self.db.query(MatchHistory).filter(
            MatchHistory.job_id == job_id
        ).all()

        if not interactions:
            return None

        total_views = sum(1 for i in interactions if i.viewed)
        total_clicks = sum(1 for i in interactions if i.clicked)
        total_applications = sum(1 for i in interactions if i.applied)
        positive_feedback = sum(1 for i in interactions if i.user_feedback == "interested")
        total_feedback = sum(1 for i in interactions if i.user_feedback)

        return JobInteractionData(
            job_id=job_id,
            total_views=total_views,
            total_clicks=total_clicks,
            total_applications=total_applications,
            conversion_rate=total_applications / total_views if total_views > 0 else 0,
            positive_feedback_ratio=positive_feedback / total_feedback if total_feedback > 0 else 0
        )

    def _apply_filters(self, matches: List[Tuple[MatchScore, JobData]], filters: MatchFilter) -> List[Tuple[MatchScore, JobData]]:
        """Apply filters to match results"""
        filtered = matches

        if filters.min_score is not None:
            filtered = [(score, job) for score, job in filtered if score.total_score >= filters.min_score]

        if filters.max_score is not None:
            filtered = [(score, job) for score, job in filtered if score.total_score <= filters.max_score]

        if filters.categories:
            filtered = [(score, job) for score, job in filtered if job.category in filters.categories]

        if filters.locations:
            filtered = [(score, job) for score, job in filtered if job.prefecture_code in filters.locations]

        if filters.salary_min is not None:
            filtered = [(score, job) for score, job in filtered
                       if job.salary_max and job.salary_max >= filters.salary_min]

        if filters.salary_max is not None:
            filtered = [(score, job) for score, job in filtered
                       if job.salary_min and job.salary_min <= filters.salary_max]

        return filtered

    def _sort_matches(self, matches: List[Tuple[MatchScore, JobData]], sort_order: SortOrder) -> List[Tuple[MatchScore, JobData]]:
        """Sort match results"""
        if sort_order == SortOrder.SCORE_DESC:
            return sorted(matches, key=lambda x: x[0].total_score, reverse=True)
        elif sort_order == SortOrder.SCORE_ASC:
            return sorted(matches, key=lambda x: x[0].total_score)
        elif sort_order == SortOrder.SALARY_DESC:
            return sorted(matches, key=lambda x: x[1].salary_max or 0, reverse=True)
        elif sort_order == SortOrder.SALARY_ASC:
            return sorted(matches, key=lambda x: x[1].salary_min or 0)
        else:
            return matches

    async def _store_match_history(self, user_id: int, matches: List[Tuple[MatchScore, JobData]], algorithm: AlgorithmType):
        """Store match results in history"""
        try:
            for rank, (score, job) in enumerate(matches, 1):
                # Check if record already exists
                existing = self.db.query(MatchHistory).filter(
                    and_(
                        MatchHistory.user_id == user_id,
                        MatchHistory.job_id == job.job_id
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.match_score = score.total_score
                    existing.algorithm_used = algorithm
                    existing.match_rank = rank
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    history_record = MatchHistory(
                        user_id=user_id,
                        job_id=job.job_id,
                        match_score=score.total_score,
                        algorithm_used=algorithm,
                        match_rank=rank,
                        matched_at=datetime.utcnow()
                    )
                    self.db.add(history_record)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error storing match history: {e}")
            self.db.rollback()

    def _format_match_result(self, match: Tuple[MatchScore, JobData], job_data: JobData) -> Dict[str, Any]:
        """Format match result for API response"""
        score, job = match
        return {
            "job_id": job.job_id,
            "title": job.title,
            "category": job.category,
            "location": job.location,
            "prefecture_code": job.prefecture_code,
            "salary_range": {
                "min": job.salary_min,
                "max": job.salary_max
            },
            "employment_type": job.employment_type,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "match_score": {
                "total": score.total_score,
                "breakdown": {
                    "skills": score.skills_score,
                    "location": score.location_score,
                    "salary": score.salary_score,
                    "category": score.category_score,
                    "experience": score.experience_score
                },
                "algorithm": score.details.get("algorithm", "unknown")
            }
        }

    def _calculate_engagement_score(self, interaction_type: str, feedback: str) -> float:
        """Calculate engagement score for algorithm learning"""
        base_scores = {
            "viewed": 0.1,
            "clicked": 0.3,
            "applied": 1.0,
            "favorited": 0.8,
            "hidden": -0.5
        }

        feedback_modifiers = {
            "interested": 0.3,
            "not_interested": -0.3,
            "maybe": 0.0
        }

        base_score = base_scores.get(interaction_type, 0.0)
        feedback_modifier = feedback_modifiers.get(feedback, 0.0)

        return max(0.0, min(1.0, base_score + feedback_modifier))