#!/usr/bin/env python3
"""
T020: BatchJob Model (REFACTORED)

Batch job management system with scheduling, retry logic, and performance tracking.
"""

from typing import Optional, Dict, Any, List, ClassVar
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum, select, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import enum
import logging

from app.core.database import Base

logger = logging.getLogger(__name__)


class JobStatus(str, enum.Enum):
    """Batch job status enumeration"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    RETRYING = 'retrying'


class JobType(str, enum.Enum):
    """Batch job type enumeration"""
    DATA_IMPORT = 'data_import'
    SCORE_CALCULATION = 'score_calculation'
    MATCHING = 'matching'
    EMAIL_GENERATION = 'email_generation'
    EMAIL_SENDING = 'email_sending'
    CLEANUP = 'cleanup'
    REPORT_GENERATION = 'report_generation'


class BatchJob(Base):
    """Batch job model"""
    
    __tablename__ = "batch_jobs"
    __table_args__ = (
        Index('idx_batch_job_status', 'status'),
        Index('idx_batch_job_type', 'job_type'),
        Index('idx_batch_job_scheduled', 'scheduled_at'),
        CheckConstraint('retry_count >= 0', name='check_retry_count_positive'),
        CheckConstraint('max_retries >= 0', name='check_max_retries_positive'),
        {'extend_existing': True}
    )
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration constants
    DEFAULT_MAX_RETRIES: ClassVar[int] = 3
    DEFAULT_TIMEOUT_SECONDS: ClassVar[int] = 3600  # 1 hour
    CLEANUP_DAYS_DEFAULT: ClassVar[int] = 30

    # Job details
    job_name = Column(String, nullable=False)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)

    # Timing
    scheduled_at = Column(DateTime(timezone=True), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=DEFAULT_MAX_RETRIES, nullable=False)
    
    # Job data
    parameters = Column(JSON, default={})
    result = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def start(self) -> None:
        """Start the job execution.

        Raises:
            RuntimeError: If job is not in a startable state
        """
        if self.status not in [JobStatus.PENDING, JobStatus.RETRYING]:
            raise RuntimeError(f"Cannot start job in status {self.status}")
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        logger.info(f"Started batch job {self.job_name} (ID: {self.id})")
    
    def complete(
        self,
        result: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark job as completed successfully.

        Args:
            result: Job execution results
            performance_metrics: Performance statistics
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result or {}
        if performance_metrics:
            # Add duration if not already present
            if 'duration_seconds' not in performance_metrics:
                performance_metrics['duration_seconds'] = self.get_duration()
            self.performance_metrics = performance_metrics
        logger.info(f"Completed batch job {self.job_name} (ID: {self.id})")
    
    def fail(self, error_message: str) -> None:
        """Mark job as failed with error message.

        Args:
            error_message: Description of failure
        """
        self.error_message = error_message
        self.retry_count = (self.retry_count or 0) + 1

        if self.should_retry():
            self.status = JobStatus.RETRYING
            logger.warning(f"Job {self.job_name} failed (attempt {self.retry_count}/{self.max_retries}): {error_message}")
        else:
            self.status = JobStatus.FAILED
            self.completed_at = datetime.utcnow()
            logger.error(f"Job {self.job_name} permanently failed after {self.retry_count} attempts: {error_message}")
    
    def retry(self):
        """Retry the job"""
        if self.retry_count < self.max_retries:
            self.status = JobStatus.RETRYING
    
    def cancel(self, reason: str = None):
        """Cancel the job"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        if reason:
            self.error_message = reason
    
    def should_retry(self) -> bool:
        """Check if job should be retried based on retry count and status.

        Returns:
            True if job can be retried
        """
        return (
            self.retry_count < self.max_retries and
            self.status in [JobStatus.FAILED, JobStatus.RETRYING]
        )
    
    def get_duration(self) -> float:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0
    
    @classmethod
    async def get_ready_jobs(cls, db_session: AsyncSession) -> List['BatchJob']:
        """Get jobs ready to run"""
        result = await db_session.execute(
            select(cls)
            .where(cls.status == JobStatus.PENDING)
            .where(cls.scheduled_at <= datetime.utcnow())
            .order_by(cls.scheduled_at)
        )
        return result.scalars().all()
    
    @classmethod
    async def get_job_history(cls, db_session, job_type: JobType = None, limit: int = 10):
        """Get job history"""
        query = select(cls).order_by(cls.created_at.desc()).limit(limit)
        
        if job_type:
            query = query.where(cls.job_type == job_type)
        
        result = await db_session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def cleanup_old_jobs(
        cls,
        db_session: AsyncSession,
        days_to_keep: int = CLEANUP_DAYS_DEFAULT
    ) -> int:
        """Clean up old completed/failed jobs"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = await db_session.execute(
            select(cls)
            .where(cls.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]))
            .where(cls.completed_at < cutoff_date)
        )
        
        old_jobs = result.scalars().all()
        count = len(old_jobs)
        
        for job in old_jobs:
            await db_session.delete(job)
        
        await db_session.commit()
        return count
    
    @classmethod
    async def can_start_new_job(cls, db_session, job_type: JobType, max_concurrent: int = 3) -> bool:
        """Check if a new job of given type can start"""
        result = await db_session.execute(
            select(func.count(cls.id))
            .where(cls.job_type == job_type)
            .where(cls.status == JobStatus.RUNNING)
        )
        
        running_count = result.scalar()
        return running_count < max_concurrent
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'job_name': self.job_name,
            'job_type': self.job_type.value if self.job_type else None,
            'status': self.status.value if self.status else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'parameters': self.parameters,
            'result': self.result,
            'performance_metrics': self.performance_metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
