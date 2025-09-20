#!/usr/bin/env python3
"""
Scheduled Job Model - Minimal GREEN Phase Implementation
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import Base


class ScheduledJob(Base):
    """Model for storing scheduled job configurations"""

    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    job_name = Column(String(255), nullable=False)
    job_function = Column(String(500), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # cron, interval, date
    trigger_config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    max_instances = Column(Integer, default=1)
    coalesce = Column(Boolean, default=True)
    dependencies = Column(JSON, nullable=True)  # Array of job IDs
    timeout_seconds = Column(Integer, nullable=True)
    priority = Column(Integer, default=5)
    next_run_time = Column(DateTime, nullable=True)
    last_run_time = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduledJob(job_id='{self.job_id}', enabled={self.enabled})>"
