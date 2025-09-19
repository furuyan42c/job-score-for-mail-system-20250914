#!/usr/bin/env python3
"""
T018: Score Model Tests (RED Phase)

Tests for the Score model including:
- Score calculation algorithms
- Score types and categories
- Score history tracking
- Relationships with jobs and users
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.score import Score, ScoreType
from app.models.job import Job
from app.models.user import User
from app.core.database import Base, get_db


class TestScoreModel:
    """Test suite for Score model"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        async for session in get_db():
            yield session
            await session.rollback()

    def test_score_model_exists(self):
        """Test that Score model is defined"""
        assert Score is not None
        assert hasattr(Score, '__tablename__')
        assert Score.__tablename__ == 'scores'

    def test_score_model_fields(self):
        """Test that Score model has all required fields"""
        required_fields = [
            'id', 'job_id', 'user_id', 'score_type',
            'base_score', 'salary_score', 'location_score',
            'company_score', 'freshness_score', 'completeness_score',
            'seo_score', 'match_score', 'total_score',
            'calculated_at', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert hasattr(Score, field), f"Score model missing field: {field}"

    def test_score_types_enum(self):
        """Test ScoreType enum values"""
        assert ScoreType.BASE == 'base'
        assert ScoreType.SEO == 'seo'
        assert ScoreType.MATCH == 'match'
        assert ScoreType.COMBINED == 'combined'

    def test_score_model_relationships(self):
        """Test that Score model has proper relationships"""
        assert hasattr(Score, 'job')
        assert hasattr(Score, 'user')

    @pytest.mark.asyncio
    async def test_create_base_score(self, db_session: AsyncSession):
        """Test creating a base score"""
        # Create job first
        job = Job(job_id="JOB001", company_name="Test Corp")
        db_session.add(job)
        await db_session.commit()
        
        score = Score(
            job_id=job.id,
            score_type=ScoreType.BASE,
            base_score=75.5,
            salary_score=80.0,
            location_score=70.0,
            company_score=65.0,
            freshness_score=85.0,
            completeness_score=77.5
        )
        
        db_session.add(score)
        await db_session.commit()
        await db_session.refresh(score)
        
        assert score.id is not None
        assert score.score_type == ScoreType.BASE
        assert score.base_score == 75.5
        assert score.calculated_at is not None

    @pytest.mark.asyncio
    async def test_create_match_score(self, db_session: AsyncSession):
        """Test creating a match score between user and job"""
        # Create job and user
        job = Job(job_id="JOB002", company_name="Match Corp")
        user = User(user_id="USER002", email="match@example.com", name="Match User")
        
        db_session.add(job)
        db_session.add(user)
        await db_session.commit()
        
        score = Score(
            job_id=job.id,
            user_id=user.id,
            score_type=ScoreType.MATCH,
            match_score=82.3,
            total_score=82.3
        )
        
        db_session.add(score)
        await db_session.commit()
        
        assert score.user_id == user.id
        assert score.match_score == 82.3

    @pytest.mark.asyncio
    async def test_calculate_total_score(self, db_session: AsyncSession):
        """Test total score calculation"""
        job = Job(job_id="JOB003", company_name="Total Corp")
        db_session.add(job)
        await db_session.commit()
        
        score = Score(
            job_id=job.id,
            score_type=ScoreType.COMBINED,
            base_score=70.0,
            seo_score=80.0,
            match_score=90.0
        )
        
        # Calculate weighted total
        score.calculate_total_score(weights={
            'base': 0.3,
            'seo': 0.2,
            'match': 0.5
        })
        
        expected_total = (70.0 * 0.3) + (80.0 * 0.2) + (90.0 * 0.5)
        assert abs(score.total_score - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_score_history_tracking(self, db_session: AsyncSession):
        """Test score history tracking"""
        job = Job(job_id="JOB004", company_name="History Corp")
        db_session.add(job)
        await db_session.commit()
        
        # Create initial score
        score1 = Score(
            job_id=job.id,
            score_type=ScoreType.BASE,
            base_score=60.0,
            total_score=60.0
        )
        db_session.add(score1)
        await db_session.commit()
        
        # Create updated score
        score2 = Score(
            job_id=job.id,
            score_type=ScoreType.BASE,
            base_score=75.0,
            total_score=75.0
        )
        db_session.add(score2)
        await db_session.commit()
        
        # Get score history
        result = await db_session.execute(
            select(Score)
            .where(Score.job_id == job.id)
            .where(Score.score_type == ScoreType.BASE)
            .order_by(Score.calculated_at.desc())
        )
        history = result.scalars().all()
        
        assert len(history) == 2
        assert history[0].base_score == 75.0  # Most recent
        assert history[1].base_score == 60.0

    @pytest.mark.asyncio
    async def test_score_validation(self, db_session: AsyncSession):
        """Test score validation rules"""
        job = Job(job_id="JOB005", company_name="Validate Corp")
        db_session.add(job)
        await db_session.commit()
        
        # Test invalid score range
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            score = Score(
                job_id=job.id,
                score_type=ScoreType.BASE,
                base_score=150.0  # Invalid: > 100
            )
            score.validate_score_range()

        # Test negative score
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            score = Score(
                job_id=job.id,
                score_type=ScoreType.BASE,
                base_score=-10.0  # Invalid: < 0
            )
            score.validate_score_range()

    @pytest.mark.asyncio
    async def test_get_latest_scores(self, db_session: AsyncSession):
        """Test getting latest scores for jobs"""
        # Create jobs
        job1 = Job(job_id="LATEST001", company_name="Latest1")
        job2 = Job(job_id="LATEST002", company_name="Latest2")
        
        db_session.add(job1)
        db_session.add(job2)
        await db_session.commit()
        
        # Create scores
        scores = [
            Score(job_id=job1.id, score_type=ScoreType.BASE, base_score=70.0),
            Score(job_id=job1.id, score_type=ScoreType.BASE, base_score=75.0),  # Latest for job1
            Score(job_id=job2.id, score_type=ScoreType.BASE, base_score=80.0),  # Latest for job2
        ]
        
        for score in scores:
            db_session.add(score)
            await db_session.commit()
        
        # Get latest scores
        latest_scores = await Score.get_latest_scores(
            db_session,
            job_ids=[job1.id, job2.id],
            score_type=ScoreType.BASE
        )
        
        assert len(latest_scores) == 2
        assert latest_scores[job1.id] == 75.0
        assert latest_scores[job2.id] == 80.0

    @pytest.mark.asyncio
    async def test_score_aggregation(self, db_session: AsyncSession):
        """Test score aggregation functions"""
        job = Job(job_id="AGG001", company_name="Aggregate Corp")
        db_session.add(job)
        await db_session.commit()
        
        # Create multiple scores
        scores = [
            Score(job_id=job.id, score_type=ScoreType.BASE, total_score=70.0),
            Score(job_id=job.id, score_type=ScoreType.SEO, total_score=80.0),
            Score(job_id=job.id, score_type=ScoreType.MATCH, total_score=90.0),
        ]
        
        for score in scores:
            db_session.add(score)
        await db_session.commit()
        
        # Test aggregation
        stats = await Score.get_score_statistics(
            db_session,
            job_id=job.id
        )
        
        assert stats['count'] == 3
        assert stats['average'] == 80.0
        assert stats['min'] == 70.0
        assert stats['max'] == 90.0

    def test_score_serialization(self):
        """Test score serialization to dict"""
        score = Score(
            job_id=1,
            user_id=2,
            score_type=ScoreType.MATCH,
            base_score=70.0,
            seo_score=80.0,
            match_score=85.0,
            total_score=78.3
        )
        
        score_dict = score.to_dict()
        
        assert score_dict['job_id'] == 1
        assert score_dict['user_id'] == 2
        assert score_dict['score_type'] == 'match'
        assert score_dict['total_score'] == 78.3
        assert 'calculated_at' in score_dict
