"""
Core Structured Logging System
T061-GREEN: Basic implementation for structured logging with JSON format and correlation IDs
"""

import json
import logging
import time
import uuid
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum
import re


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogConfiguration:
    """Log configuration from environment"""
    level: str
    format: str
    environment: str
    enable_correlation: bool = True
    enable_performance_mode: bool = False
    batch_size: int = 100
    flush_interval: float = 1.0

    @classmethod
    def from_environment(cls) -> 'LogConfiguration':
        """Create configuration from environment variables"""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', 'json'),
            environment=os.getenv('ENVIRONMENT', 'development'),
            enable_correlation=os.getenv('LOG_ENABLE_CORRELATION', 'true').lower() == 'true',
            enable_performance_mode=os.getenv('LOG_PERFORMANCE_MODE', 'false').lower() == 'true',
            batch_size=int(os.getenv('LOG_BATCH_SIZE', '100')),
            flush_interval=float(os.getenv('LOG_FLUSH_INTERVAL', '1.0'))
        )


class CorrelationManager:
    """Manages correlation IDs for request tracing"""

    def __init__(self):
        self._local = threading.local()

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())

    def get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from thread local"""
        return getattr(self._local, 'correlation_id', None)

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID in thread local"""
        self._local.correlation_id = correlation_id

    @contextmanager
    def correlation_context(self, correlation_id: str):
        """Context manager for correlation ID"""
        old_id = self.get_current_correlation_id()
        self.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            if old_id:
                self.set_correlation_id(old_id)
            else:
                self._local.correlation_id = None


class SensitiveDataFilter:
    """Filter sensitive data from logs"""

    SENSITIVE_PATTERNS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'api_key',
        'access_token', 'refresh_token', 'jwt', 'auth', 'authorization',
        'credit_card', 'card_number', 'ssn', 'social_security'
    }

    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b')

    @classmethod
    def filter_sensitive_data(cls, data: Any) -> Any:
        """Filter sensitive data from log data"""
        if isinstance(data, dict):
            return {key: cls._filter_value(key, value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.filter_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            return cls._filter_string_patterns(data)
        else:
            return data

    @classmethod
    def _filter_value(cls, key: str, value: Any) -> Any:
        """Filter value based on key name"""
        if isinstance(key, str) and any(pattern in key.lower() for pattern in cls.SENSITIVE_PATTERNS):
            return "***MASKED***"
        return cls.filter_sensitive_data(value)

    @classmethod
    def _filter_string_patterns(cls, text: str) -> str:
        """Filter sensitive patterns in strings"""
        # Email addresses
        text = cls.EMAIL_PATTERN.sub("***@***.***", text)
        # Phone numbers
        text = cls.PHONE_PATTERN.sub("***-***-****", text)
        # Credit card numbers
        text = cls.CREDIT_CARD_PATTERN.sub("**** **** **** ****", text)
        return text


class LogFormatter(logging.Formatter):
    """Log formatter with environment-based formatting"""

    def __init__(self, environment: str = "development", correlation_manager: Optional[CorrelationManager] = None):
        super().__init__()
        self.environment = environment
        self.correlation_manager = correlation_manager or CorrelationManager()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record based on environment"""
        if self.environment == "production":
            return self._format_json(record)
        else:
            return self._format_human_readable(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as JSON for production"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": getattr(record, 'module', 'unknown'),
            "function": getattr(record, 'funcName', 'unknown'),
            "line": getattr(record, 'lineno', 0),
            "correlation_id": self.correlation_manager.get_current_correlation_id()
        }

        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'levelname', 'levelno', 'pathname', 'filename',
                              'module', 'lineno', 'funcName', 'created', 'msecs',
                              'relativeCreated', 'thread', 'threadName', 'processName',
                              'process', 'getMessage', 'msg', 'args']:
                    log_data[key] = SensitiveDataFilter.filter_sensitive_data(value)

        # Filter sensitive data
        log_data = SensitiveDataFilter.filter_sensitive_data(log_data)

        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _format_human_readable(self, record: logging.LogRecord) -> str:
        """Format as human-readable for development"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        correlation_id = self.correlation_manager.get_current_correlation_id()
        correlation_part = f" [{correlation_id[:8]}]" if correlation_id else ""

        return f"[{timestamp}] {record.levelname:<8} {record.name}{correlation_part}: {record.getMessage()}"


class LogLevelManager:
    """Manages dynamic log level adjustments"""

    def __init__(self):
        self._levels: Dict[str, str] = {}

    def set_level(self, logger_name: str, level: str):
        """Set log level for specific logger"""
        self._levels[logger_name] = level
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))

    def get_level(self, logger_name: str) -> str:
        """Get log level for specific logger"""
        return self._levels.get(logger_name, "INFO")


class BatchLogger:
    """Batch logger for high-volume scenarios"""

    def __init__(self, logger: logging.Logger, batch_size: int = 100, flush_interval: float = 1.0):
        self.logger = logger
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        self._total_logged = 0

    def add_log_entry(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Add log entry to batch"""
        entry = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extra": extra or {}
        }
        self._batch.append(entry)

        # Auto-flush if batch is full or time interval exceeded
        if (len(self._batch) >= self.batch_size or
            time.time() - self._last_flush >= self.flush_interval):
            self.flush()

    def flush(self):
        """Flush batch to logger"""
        if not self._batch:
            return

        # Log all entries in batch
        for entry in self._batch:
            log_level = getattr(logging, entry["level"])
            self.logger.log(log_level, entry["message"], extra=entry["extra"])

        self._total_logged += len(self._batch)
        self._batch.clear()
        self._last_flush = time.time()

    def get_pending_count(self) -> int:
        """Get number of pending log entries"""
        return len(self._batch)

    def get_total_logged(self) -> int:
        """Get total number of logged entries"""
        return self._total_logged


class CoreStructuredLogger:
    """Core structured logger with correlation support"""

    def __init__(self, name: str, config: Optional[LogConfiguration] = None):
        self.name = name
        self.config = config or LogConfiguration.from_environment()
        self.correlation_manager = CorrelationManager()
        self.level_manager = LogLevelManager()

        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.config.level))

        # Setup formatter
        self.formatter = LogFormatter(
            environment=self.config.environment,
            correlation_manager=self.correlation_manager
        )

        # Setup handler
        handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        self.logger.addHandler(handler)

        self._performance_mode = self.config.enable_performance_mode

    def set_performance_mode(self, enabled: bool):
        """Enable/disable performance mode"""
        self._performance_mode = enabled

    def create_batch_logger(self, batch_size: Optional[int] = None, flush_interval: Optional[float] = None) -> BatchLogger:
        """Create batch logger for high-volume scenarios"""
        return BatchLogger(
            self.logger,
            batch_size or self.config.batch_size,
            flush_interval or self.config.flush_interval
        )

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        if exc_info:
            kwargs['exc_info'] = True
            # Add exception details for JSON format
            import traceback
            import sys
            if sys.exc_info()[0] is not None:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                kwargs['exception'] = {
                    'type': exc_type.__name__ if exc_type else None,
                    'message': str(exc_value) if exc_value else None,
                    'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else None
                }
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method"""
        # Filter sensitive data from kwargs
        extra = SensitiveDataFilter.filter_sensitive_data(kwargs)

        # Performance mode: simplified logging
        if self._performance_mode:
            extra = {k: v for k, v in extra.items() if k in ['correlation_id', 'user_id', 'request_id']}

        self.logger.log(level, message, extra=extra)


class DatabaseQueryLogger:
    """Database query logger with performance tracking"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("database")

    @contextmanager
    def log_query(self, query: str, params: Optional[List] = None):
        """Context manager for logging database queries"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            # Mask sensitive data in query
            masked_query = SensitiveDataFilter._filter_string_patterns(query)

            self.logger.info("Database query executed", extra={
                "category": "database",
                "query": masked_query,
                "duration_ms": duration_ms,
                "params_count": len(params) if params else 0
            })


class ErrorAggregator:
    """Error aggregation and alerting"""

    def __init__(self, threshold: int = 5, time_window: int = 60):
        self.threshold = threshold
        self.time_window = time_window
        self._error_counts: Dict[str, List[float]] = {}

    def record_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """Record an error occurrence"""
        current_time = time.time()

        if error_type not in self._error_counts:
            self._error_counts[error_type] = []

        # Add current error
        self._error_counts[error_type].append(current_time)

        # Clean old errors outside time window
        cutoff_time = current_time - self.time_window
        self._error_counts[error_type] = [
            t for t in self._error_counts[error_type]
            if t > cutoff_time
        ]

    def get_triggered_alerts(self) -> List[Dict[str, Any]]:
        """Get triggered alerts based on thresholds"""
        alerts = []
        current_time = time.time()

        for error_type, timestamps in self._error_counts.items():
            # Clean old entries
            cutoff_time = current_time - self.time_window
            recent_errors = [t for t in timestamps if t > cutoff_time]

            if len(recent_errors) >= self.threshold:
                alerts.append({
                    "error_type": error_type,
                    "count": len(recent_errors),
                    "threshold": self.threshold,
                    "time_window": self.time_window,
                    "last_occurrence": max(recent_errors)
                })

        return alerts


class MetricsLogger:
    """Logger for metrics collection"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("metrics")
        self._collected_metrics: List[Dict[str, Any]] = []

    def record_counter(self, name: str, value: int, tags: Optional[Dict[str, str]] = None):
        """Record a counter metric"""
        metric = {
            "type": "counter",
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time()
        }
        self._collected_metrics.append(metric)
        self.logger.info(f"Counter metric: {name}={value}", extra=metric)

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        metric = {
            "type": "histogram",
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time()
        }
        self._collected_metrics.append(metric)
        self.logger.info(f"Histogram metric: {name}={value}", extra=metric)

    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric"""
        metric = {
            "type": "gauge",
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time()
        }
        self._collected_metrics.append(metric)
        self.logger.info(f"Gauge metric: {name}={value}", extra=metric)

    def get_collected_metrics(self) -> List[Dict[str, Any]]:
        """Get all collected metrics"""
        return self._collected_metrics.copy()


def setup_fastapi_logging(app):
    """Setup FastAPI logging integration"""
    from fastapi import Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware

    class LoggingMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, logger: Optional[CoreStructuredLogger] = None):
            super().__init__(app)
            self.logger = logger or CoreStructuredLogger("fastapi")

        async def dispatch(self, request: Request, call_next):
            # Generate correlation ID for request
            correlation_id = self.logger.correlation_manager.generate_correlation_id()

            with self.logger.correlation_manager.correlation_context(correlation_id):
                start_time = time.time()

                # Log request
                self.logger.info("Request started", extra={
                    "method": request.method,
                    "url": str(request.url),
                    "correlation_id": correlation_id
                })

                response = await call_next(request)

                # Log response
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info("Request completed", extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id
                })

                return response

    app.add_middleware(LoggingMiddleware)


# Global logger instance
default_logger = CoreStructuredLogger("app")