#!/usr/bin/env python3
"""
T020: BatchJob Model Tests (RED Phase)

Tests for the BatchJob model including:
- Batch job scheduling and execution
- Job status tracking
- Error handling and retries
- Performance metrics
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.batch_job import BatchJob, JobStatus, JobType
from app.models.base import Base
from app.core.database import get_db


class TestBatchJobModel:
    """Test suite for BatchJob model"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        async for session in get_db():
            yield session
            await session.rollback()

    def test_batch_job_model_exists(self):
        """Test that BatchJob model is defined"""
        assert BatchJob is not None
        assert hasattr(BatchJob, '__tablename__')
        assert BatchJob.__tablename__ == 'batch_jobs'

    def test_batch_job_fields(self):
        """Test that BatchJob model has all required fields"""
        required_fields = [
            'id', 'job_name', 'job_type', 'status',
            'scheduled_at', 'started_at', 'completed_at',
            'error_message', 'retry_count', 'max_retries',
            'parameters', 'result', 'performance_metrics',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert hasattr(BatchJob, field), f"BatchJob model missing field: {field}"

    def test_job_status_enum(self):
        """Test JobStatus enum values"""
        assert JobStatus.PENDING == 'pending'
        assert JobStatus.RUNNING == 'running'
        assert JobStatus.COMPLETED == 'completed'
        assert JobStatus.FAILED == 'failed'
        assert JobStatus.CANCELLED == 'cancelled'
        assert JobStatus.RETRYING == 'retrying'

    def test_job_type_enum(self):
        """Test JobType enum values"""
        assert JobType.DATA_IMPORT == 'data_import'
        assert JobType.SCORE_CALCULATION == 'score_calculation'
        assert JobType.MATCHING == 'matching'
        assert JobType.EMAIL_GENERATION == 'email_generation'
        assert JobType.EMAIL_SENDING == 'email_sending'
        assert JobType.CLEANUP == 'cleanup'
        assert JobType.REPORT_GENERATION == 'report_generation'

    @pytest.mark.asyncio
    async def test_create_batch_job(self, db_session: AsyncSession):
        """Test creating a batch job"""
        job = BatchJob(
            job_name="Daily Import",
            job_type=JobType.DATA_IMPORT,
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            parameters={"source": "api", "limit": 1000}
        )
        
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        
        assert job.id is not None
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 0
        assert job.max_retries == 3  # Default value

    @pytest.mark.asyncio
    async def test_batch_job_execution(self, db_session: AsyncSession):
        """Test batch job execution lifecycle"""
        job = BatchJob(
            job_name="Test Execution",
            job_type=JobType.SCORE_CALCULATION,
            scheduled_at=datetime.utcnow()
        )
        
        db_session.add(job)
        await db_session.commit()
        
        # Start job
        job.start()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        
        # Complete job
        job.complete(result={"processed": 100, "duration": 5.2})
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result["processed"] == 100
        
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_batch_job_failure(self, db_session: AsyncSession):
        """Test batch job failure handling"""
        job = BatchJob(
            job_name="Test Failure",
            job_type=JobType.MATCHING,
            max_retries=2
        )
        
        db_session.add(job)
        await db_session.commit()
        
        # Start and fail job
        job.start()
        job.fail(error_message="Connection timeout")
        
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Connection timeout"
        assert job.retry_count == 1
        
        # Retry job
        job.retry()
        assert job.status == JobStatus.RETRYING
        assert job.retry_count == 1
        
        # Fail again
        job.fail(error_message="Connection refused")
        assert job.retry_count == 2
        
        # Max retries reached
        job.fail(error_message="Final failure")
        assert job.status == JobStatus.FAILED
        assert job.should_retry() is False
        
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_batch_job_cancellation(self, db_session: AsyncSession):
        """Test batch job cancellation"""
        job = BatchJob(
            job_name="Test Cancel",
            job_type=JobType.EMAIL_GENERATION
        )
        
        db_session.add(job)
        await db_session.commit()
        
        # Start job
        job.start()
        assert job.status == JobStatus.RUNNING
        
        # Cancel job
        job.cancel(reason="User requested cancellation")
        assert job.status == JobStatus.CANCELLED
        assert "User requested" in job.error_message
        assert job.completed_at is not None
        
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_batch_job_scheduling(self, db_session: AsyncSession):
        """Test batch job scheduling"""
        # Create jobs scheduled at different times
        now = datetime.utcnow()
        jobs = [
            BatchJob(
                job_name="Job 1",
                job_type=JobType.DATA_IMPORT,
                scheduled_at=now + timedelta(hours=1)
            ),
            BatchJob(
                job_name="Job 2",
                job_type=JobType.SCORE_CALCULATION,
                scheduled_at=now + timedelta(minutes=30)
            ),
            BatchJob(
                job_name="Job 3",
                job_type=JobType.MATCHING,
                scheduled_at=now - timedelta(minutes=10)  # Past due
            ),
        ]
        
        for job in jobs:
            db_session.add(job)
        await db_session.commit()
        
        # Get jobs ready to run
        ready_jobs = await BatchJob.get_ready_jobs(db_session)
        
        assert len(ready_jobs) == 1
        assert ready_jobs[0].job_name == "Job 3"  # Past due job

    @pytest.mark.asyncio
    async def test_batch_job_performance_metrics(self, db_session: AsyncSession):
        """Test performance metrics tracking"""
        job = BatchJob(
            job_name="Performance Test",
            job_type=JobType.MATCHING
        )
        
        db_session.add(job)
        await db_session.commit()
        
        # Start job
        job.start()
        
        # Simulate processing and track metrics
        metrics = {
            "items_processed": 1000,
            "duration_seconds": 45.3,
            "memory_mb": 256,
            "cpu_percent": 75.5,
            "items_per_second": 22.1
        }
        
        job.complete(performance_metrics=metrics)
        
        assert job.performance_metrics["items_processed"] == 1000
        assert job.performance_metrics["duration_seconds"] == 45.3
        assert job.get_duration() > 0
        
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_batch_job_history(self, db_session: AsyncSession):
        """Test batch job history tracking"""
        # Create multiple runs of same job type
        for i in range(5):
            job = BatchJob(
                job_name=f"Daily Import Run {i+1}",
                job_type=JobType.DATA_IMPORT,
                status=JobStatus.COMPLETED if i < 4 else JobStatus.FAILED
            )
            db_session.add(job)
        
        await db_session.commit()
        
        # Get job history
        history = await BatchJob.get_job_history(
            db_session,
            job_type=JobType.DATA_IMPORT,
            limit=10
        )
        
        assert len(history) == 5
        assert sum(1 for j in history if j.status == JobStatus.COMPLETED) == 4
        assert sum(1 for j in history if j.status == JobStatus.FAILED) == 1

    @pytest.mark.asyncio
    async def test_batch_job_cleanup(self, db_session: AsyncSession):
        """Test old batch job cleanup"""
        now = datetime.utcnow()
        
        # Create old jobs
        old_jobs = [
            BatchJob(
                job_name="Old Job 1",
                job_type=JobType.CLEANUP,
                status=JobStatus.COMPLETED,
                completed_at=now - timedelta(days=35)  # Over 30 days old
            ),
            BatchJob(
                job_name="Old Job 2",
                job_type=JobType.CLEANUP,
                status=JobStatus.FAILED,
                completed_at=now - timedelta(days=40)
            ),
            BatchJob(
                job_name="Recent Job",
                job_type=JobType.CLEANUP,
                status=JobStatus.COMPLETED,
                completed_at=now - timedelta(days=5)  # Recent
            ),
        ]
        
        for job in old_jobs:
            db_session.add(job)
        await db_session.commit()
        
        # Cleanup old jobs
        deleted_count = await BatchJob.cleanup_old_jobs(
            db_session,
            days_to_keep=30
        )
        
        assert deleted_count == 2  # Two old jobs deleted
        
        # Verify only recent job remains
        result = await db_session.execute(
            select(BatchJob).where(BatchJob.job_type == JobType.CLEANUP)
        )
        remaining = result.scalars().all()
        
        assert len(remaining) == 1
        assert remaining[0].job_name == "Recent Job"

    @pytest.mark.asyncio
    async def test_concurrent_job_limit(self, db_session: AsyncSession):
        """Test concurrent job execution limits"""
        # Create multiple running jobs
        for i in range(3):
            job = BatchJob(
                job_name=f"Concurrent {i+1}",
                job_type=JobType.MATCHING,
                status=JobStatus.RUNNING
            )
            db_session.add(job)
        
        await db_session.commit()
        
        # Check if can start new job
        can_start = await BatchJob.can_start_new_job(
            db_session,
            job_type=JobType.MATCHING,
            max_concurrent=3
        )
        
        assert can_start is False  # Already at limit
        
        # Complete one job
        result = await db_session.execute(
            select(BatchJob)
            .where(BatchJob.status == JobStatus.RUNNING)
            .limit(1)
        )
        job_to_complete = result.scalar_one()
        job_to_complete.complete()
        await db_session.commit()
        
        # Now should be able to start
        can_start = await BatchJob.can_start_new_job(
            db_session,
            job_type=JobType.MATCHING,
            max_concurrent=3
        )
        
        assert can_start is True

    def test_batch_job_serialization(self):
        """Test batch job serialization to dict"""
        job = BatchJob(
            job_name="Serialize Test",
            job_type=JobType.EMAIL_SENDING,
            status=JobStatus.COMPLETED,
            parameters={"recipients": 100},
            result={"sent": 95, "failed": 5},
            performance_metrics={"duration": 10.5}
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['job_name'] == "Serialize Test"
        assert job_dict['job_type'] == 'email_sending'
        assert job_dict['status'] == 'completed'
        assert job_dict['parameters']['recipients'] == 100
        assert job_dict['result']['sent'] == 95
        assert 'created_at' in job_dict
