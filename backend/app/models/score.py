#!/usr/bin/env python3
"""
T018: Score Model (REFACTORED)

Comprehensive scoring system for jobs with multiple scoring components.
"""

import enum
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import and_, func

from app.core.database import Base

logger = logging.getLogger(__name__)


class ScoreType(str, enum.Enum):
    """Score type enumeration"""

    BASE = "base"
    SEO = "seo"
    MATCH = "match"
    COMBINED = "combined"


class Score(Base):
    """Score model for scores table"""

    __tablename__ = "scores"
    __table_args__ = (
        Index("idx_score_job_user", "job_id", "user_id"),
        Index("idx_score_type", "score_type"),
        Index("idx_score_calculated", "calculated_at"),
        CheckConstraint("total_score >= 0 AND total_score <= 100", name="check_total_score_range"),
        {"extend_existing": True},
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    job_id = Column(Integer, ForeignKey("jobs.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Score type
    score_type = Column(SQLEnum(ScoreType))

    # Score components
    base_score = Column(Float, default=0.0)
    salary_score = Column(Float, default=0.0)
    location_score = Column(Float, default=0.0)
    company_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    seo_score = Column(Float, default=0.0)
    match_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)

    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    job = relationship("Job", back_populates="scores")
    user = relationship("User")

    # Default scoring weights
    DEFAULT_WEIGHTS = {
        "base": 0.3,
        "seo": 0.2,
        "match": 0.3,
        "salary": 0.1,
        "location": 0.05,
        "company": 0.05,
    }

    SCORE_MIN = 0.0
    SCORE_MAX = 100.0

    def calculate_total_score(self, weights: Optional[Dict[str, float]] = None) -> None:
        """Calculate weighted total score from components.

        Args:
            weights: Optional custom weights for score components
        """
        if weights is None:
            weights = self.DEFAULT_WEIGHTS

        # Normalize weights to sum to 1.0
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            normalized_weights = {k: v / weight_sum for k, v in weights.items()}
        else:
            normalized_weights = weights

        # Calculate weighted score
        self.total_score = sum(
            [
                (self.base_score or 0) * normalized_weights.get("base", 0),
                (self.seo_score or 0) * normalized_weights.get("seo", 0),
                (self.match_score or 0) * normalized_weights.get("match", 0),
                (self.salary_score or 0) * normalized_weights.get("salary", 0),
                (self.location_score or 0) * normalized_weights.get("location", 0),
                (self.company_score or 0) * normalized_weights.get("company", 0),
            ]
        )

        self.total_score = round(min(self.SCORE_MAX, max(self.SCORE_MIN, self.total_score)), 2)

    @validates(
        "base_score",
        "salary_score",
        "location_score",
        "company_score",
        "freshness_score",
        "completeness_score",
        "seo_score",
        "match_score",
        "total_score",
    )
    def validate_score_range(self, key: str, score: Optional[float]) -> Optional[float]:
        """Validate that scores are in valid range.

        Args:
            key: Field name
            score: Score value to validate

        Returns:
            Validated score value

        Raises:
            ValueError: If score is outside valid range
        """
        if score is not None:
            if score < self.SCORE_MIN or score > self.SCORE_MAX:
                raise ValueError(
                    f"Score {key} must be between {self.SCORE_MIN} and {self.SCORE_MAX}, got {score}"
                )
        return score

    @classmethod
    async def get_latest_scores(
        cls, db_session: AsyncSession, job_ids: List[int], score_type: ScoreType
    ) -> Dict[int, float]:
        """Get latest scores for given jobs"""
        from sqlalchemy import and_, select
        from sqlalchemy.sql import func

        # Subquery to get latest score for each job
        subquery = (
            select(cls.job_id, func.max(cls.calculated_at).label("max_calculated_at"))
            .where(and_(cls.job_id.in_(job_ids), cls.score_type == score_type))
            .group_by(cls.job_id)
            .subquery()
        )

        # Main query to get the scores
        result = await db_session.execute(
            select(cls).join(
                subquery,
                and_(
                    cls.job_id == subquery.c.job_id,
                    cls.calculated_at == subquery.c.max_calculated_at,
                ),
            )
        )

        scores = result.scalars().all()

        # Return as dict mapping job_id to score
        return {
            score.job_id: score.base_score if score_type == ScoreType.BASE else score.total_score
            for score in scores
        }

    @classmethod
    async def get_score_statistics(
        cls, db_session: AsyncSession, job_id: Optional[int] = None
    ) -> Dict[str, float]:
        """Get score statistics"""
        from sqlalchemy import func, select

        query = select(
            func.count(cls.id).label("count"),
            func.avg(cls.total_score).label("average"),
            func.min(cls.total_score).label("min"),
            func.max(cls.total_score).label("max"),
        )

        if job_id:
            query = query.where(cls.job_id == job_id)

        result = await db_session.execute(query)
        row = result.first()

        return {
            "count": row.count or 0,
            "average": float(row.average or 0),
            "min": float(row.min or 0),
            "max": float(row.max or 0),
        }

    def to_dict(self, include_components: bool = True) -> Dict[str, Any]:
        """Convert score to dictionary representation.

        Args:
            include_components: Whether to include all score components

        Returns:
            Dictionary representation of score
        """
        data = {
            "id": self.id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "score_type": self.score_type.value if self.score_type else None,
            "base_score": self.base_score,
            "salary_score": self.salary_score,
            "location_score": self.location_score,
            "company_score": self.company_score,
            "freshness_score": self.freshness_score,
            "completeness_score": self.completeness_score,
            "seo_score": self.seo_score,
            "match_score": self.match_score,
            "total_score": self.total_score,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
