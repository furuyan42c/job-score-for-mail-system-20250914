#!/usr/bin/env python3
"""
T018: Score Model (GREEN Phase)

Minimal implementation to pass tests
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ScoreType(str, enum.Enum):
    """Score type enumeration"""
    BASE = 'base'
    SEO = 'seo'
    MATCH = 'match'
    COMBINED = 'combined'


class Score(Base):
    """Score model for scores table"""
    
    __tablename__ = "scores"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    job_id = Column(Integer, ForeignKey('jobs.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
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
    
    def calculate_total_score(self, weights: dict = None):
        """Calculate weighted total score"""
        if not weights:
            weights = {
                'base': 0.4,
                'seo': 0.3,
                'match': 0.3
            }
        
        self.total_score = (
            self.base_score * weights.get('base', 0) +
            self.seo_score * weights.get('seo', 0) +
            self.match_score * weights.get('match', 0)
        )
    
    def validate_score_range(self):
        """Validate that scores are in valid range"""
        scores_to_check = [
            self.base_score, self.salary_score, self.location_score,
            self.company_score, self.freshness_score, self.completeness_score,
            self.seo_score, self.match_score, self.total_score
        ]
        
        for score in scores_to_check:
            if score is not None:
                if score < 0 or score > 100:
                    raise ValueError("Score must be between 0 and 100")
    
    @classmethod
    async def get_latest_scores(cls, db_session, job_ids: list, score_type: ScoreType):
        """Get latest scores for given jobs"""
        from sqlalchemy import select, and_
        from sqlalchemy.sql import func
        
        # Subquery to get latest score for each job
        subquery = (
            select(
                cls.job_id,
                func.max(cls.calculated_at).label('max_calculated_at')
            )
            .where(and_(
                cls.job_id.in_(job_ids),
                cls.score_type == score_type
            ))
            .group_by(cls.job_id)
            .subquery()
        )
        
        # Main query to get the scores
        result = await db_session.execute(
            select(cls)
            .join(
                subquery,
                and_(
                    cls.job_id == subquery.c.job_id,
                    cls.calculated_at == subquery.c.max_calculated_at
                )
            )
        )
        
        scores = result.scalars().all()
        
        # Return as dict mapping job_id to score
        return {
            score.job_id: score.base_score if score_type == ScoreType.BASE else score.total_score
            for score in scores
        }
    
    @classmethod
    async def get_score_statistics(cls, db_session, job_id: int = None):
        """Get score statistics"""
        from sqlalchemy import select, func
        
        query = select(
            func.count(cls.id).label('count'),
            func.avg(cls.total_score).label('average'),
            func.min(cls.total_score).label('min'),
            func.max(cls.total_score).label('max')
        )
        
        if job_id:
            query = query.where(cls.job_id == job_id)
        
        result = await db_session.execute(query)
        row = result.first()
        
        return {
            'count': row.count or 0,
            'average': float(row.average or 0),
            'min': float(row.min or 0),
            'max': float(row.max or 0)
        }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'score_type': self.score_type.value if self.score_type else None,
            'base_score': self.base_score,
            'salary_score': self.salary_score,
            'location_score': self.location_score,
            'company_score': self.company_score,
            'freshness_score': self.freshness_score,
            'completeness_score': self.completeness_score,
            'seo_score': self.seo_score,
            'match_score': self.match_score,
            'total_score': self.total_score,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
