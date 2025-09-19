#!/usr/bin/env python3
"""
T020: BatchJob Model (GREEN Phase)

Minimal implementation to pass tests
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum, select
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

from app.core.database import Base


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
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Job details
    job_name = Column(String)
    job_type = Column(SQLEnum(JobType))
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Job data
    parameters = Column(JSON, default={})
    result = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def start(self):
        """Start the job"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: dict = None, performance_metrics: dict = None):
        """Complete the job"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result
        if performance_metrics:
            self.performance_metrics = performance_metrics
    
    def fail(self, error_message: str):
        """Mark job as failed"""
        self.error_message = error_message
        self.retry_count += 1
        
        if self.retry_count <= self.max_retries:
            self.status = JobStatus.FAILED
        else:
            self.status = JobStatus.FAILED
    
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
        """Check if job should be retried"""
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED
    
    def get_duration(self) -> float:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0
    
    @classmethod
    async def get_ready_jobs(cls, db_session):
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
    async def cleanup_old_jobs(cls, db_session, days_to_keep: int = 30):
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
