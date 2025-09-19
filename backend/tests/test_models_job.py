#!/usr/bin/env python3
"""
T016: Job Model Tests (RED Phase)

Tests for the Job model including:
- Model structure and fields
- Relationships with other models
- Data validation
- CRUD operations
- Business logic
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.core.database import Base, get_db


class TestJobModel:
    """Test suite for Job model"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        async for session in get_db():
            yield session
            await session.rollback()

    def test_job_model_exists(self):
        """Test that Job model is defined"""
        assert Job is not None
        assert hasattr(Job, '__tablename__')
        assert Job.__tablename__ == 'jobs'

    def test_job_model_fields(self):
        """Test that Job model has all required fields"""
        required_fields = [
            'id', 'job_id', 'company_id', 'company_name',
            'job_contents', 'job_contents_detail', 'salary',
            'min_salary', 'max_salary', 'area', 'area_address',
            'pref_cd', 'city_cd', 'station', 'hours',
            'employment_type', 'employment_type_cd', 'welfare',
            'requirement', 'appeal_point', 'image_url',
            'occupation_cd1', 'occupation_cd2', 'occupation_cd3',
            'min_age', 'max_age', 'start_at', 'end_at',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert hasattr(Job, field), f"Job model missing field: {field}"

    def test_job_model_relationships(self):
        """Test that Job model has proper relationships"""
        assert hasattr(Job, 'scores')
        assert hasattr(Job, 'user_matches')
        assert hasattr(Job, 'email_sections')

    @pytest.mark.asyncio
    async def test_create_job(self, db_session: AsyncSession):
        """Test creating a new job"""
        job = Job(
            job_id="TEST001",
            company_name="Test Company",
            job_contents="Software Engineer",
            job_contents_detail="Develop web applications",
            salary="300,000 - 500,000 yen",
            min_salary=300000,
            max_salary=500000,
            area="Tokyo",
            area_address="Shibuya-ku, Tokyo",
            pref_cd=13,
            city_cd=13113,
            employment_type="Full-time",
            employment_type_cd=1,
            hours="9:00-18:00",
            welfare="Health insurance, Paid leave",
            requirement="3+ years experience"
        )
        
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        
        assert job.id is not None
        assert job.job_id == "TEST001"
        assert job.company_name == "Test Company"

    @pytest.mark.asyncio
    async def test_job_validation(self, db_session: AsyncSession):
        """Test job data validation"""
        # Test invalid salary range
        with pytest.raises(ValueError, match="min_salary cannot be greater than max_salary"):
            job = Job(
                job_id="TEST002",
                company_name="Test Company",
                min_salary=500000,
                max_salary=300000  # Invalid: min > max
            )
            job.validate_salary_range()

        # Test invalid age range
        with pytest.raises(ValueError, match="min_age cannot be greater than max_age"):
            job = Job(
                job_id="TEST003",
                company_name="Test Company",
                min_age=50,
                max_age=30  # Invalid: min > max
            )
            job.validate_age_range()

    @pytest.mark.asyncio
    async def test_job_search(self, db_session: AsyncSession):
        """Test job search functionality"""
        # Create test jobs
        jobs = [
            Job(job_id="SEARCH001", company_name="Tech Corp", job_contents="Python Developer"),
            Job(job_id="SEARCH002", company_name="Web Inc", job_contents="Frontend Developer"),
            Job(job_id="SEARCH003", company_name="Data Ltd", job_contents="Data Scientist")
        ]
        
        for job in jobs:
            db_session.add(job)
        await db_session.commit()
        
        # Search for Python jobs
        result = await db_session.execute(
            select(Job).where(Job.job_contents.contains("Python"))
        )
        python_jobs = result.scalars().all()
        
        assert len(python_jobs) == 1
        assert python_jobs[0].job_id == "SEARCH001"

    @pytest.mark.asyncio
    async def test_job_update(self, db_session: AsyncSession):
        """Test updating job information"""
        # Create job
        job = Job(
            job_id="UPDATE001",
            company_name="Old Company",
            job_contents="Old Position"
        )
        db_session.add(job)
        await db_session.commit()
        
        # Update job
        job.company_name = "New Company"
        job.job_contents = "New Position"
        await db_session.commit()
        await db_session.refresh(job)
        
        assert job.company_name == "New Company"
        assert job.job_contents == "New Position"
        assert job.updated_at is not None

    @pytest.mark.asyncio
    async def test_job_delete(self, db_session: AsyncSession):
        """Test deleting a job"""
        # Create job
        job = Job(job_id="DELETE001", company_name="Delete Me")
        db_session.add(job)
        await db_session.commit()
        job_id = job.id
        
        # Delete job
        await db_session.delete(job)
        await db_session.commit()
        
        # Verify deletion
        result = await db_session.execute(
            select(Job).where(Job.id == job_id)
        )
        deleted_job = result.scalar_one_or_none()
        
        assert deleted_job is None

    def test_job_score_calculation(self):
        """Test job score calculation methods"""
        job = Job(
            min_salary=400000,
            max_salary=600000,
            pref_cd=13,  # Tokyo
            company_name="Top Company"
        )
        
        # Test base score calculation
        base_score = job.calculate_base_score()
        assert 0 <= base_score <= 100
        
        # Test location score
        location_score = job.calculate_location_score()
        assert location_score > 50  # Tokyo should have high score

    def test_job_serialization(self):
        """Test job serialization to dict"""
        job = Job(
            job_id="SERIAL001",
            company_name="Test Company",
            job_contents="Developer",
            min_salary=300000,
            max_salary=500000
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['job_id'] == "SERIAL001"
        assert job_dict['company_name'] == "Test Company"
        assert job_dict['min_salary'] == 300000
        assert job_dict['max_salary'] == 500000
        assert 'created_at' in job_dict
        assert 'updated_at' in job_dict
