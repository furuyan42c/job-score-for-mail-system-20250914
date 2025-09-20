#!/usr/bin/env python3
"""
Batch Execution Model - Minimal GREEN Phase Implementation
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import Base


class BatchExecution(Base):
    """Model for tracking batch execution status and metrics"""

    __tablename__ = "batch_executions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(255), unique=True, index=True, nullable=False)
    batch_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BatchExecution(batch_id='{self.batch_id}', status='{self.status}')>"