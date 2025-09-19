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


class LogAggregator:
    """Log aggregation service for centralized logging"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("aggregator")
        self.aggregated_logs: List[Dict[str, Any]] = []
        self.aggregation_window = 60  # seconds
        self.last_flush = time.time()

    async def aggregate_log(self, level: str, message: str, **kwargs):
        """Aggregate log entry for batch processing"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
            **kwargs
        }

        self.aggregated_logs.append(log_entry)

        # Auto-flush if window exceeded
        if time.time() - self.last_flush >= self.aggregation_window:
            await self.flush_logs()

    async def flush_logs(self):
        """Flush aggregated logs to external systems"""
        if not self.aggregated_logs:
            return

        try:
            # Group logs by level for efficient processing
            logs_by_level = defaultdict(list)
            for log in self.aggregated_logs:
                logs_by_level[log["level"]].append(log)

            # Send to external systems (mock implementation)
            for level, logs in logs_by_level.items():
                await self._send_to_external_system(level, logs)

            self.logger.info(f"Flushed {len(self.aggregated_logs)} aggregated logs")

        except Exception as e:
            self.logger.error(f"Failed to flush aggregated logs: {str(e)}", exc_info=True)

        finally:
            self.aggregated_logs.clear()
            self.last_flush = time.time()

    async def _send_to_external_system(self, level: str, logs: List[Dict[str, Any]]):
        """Send logs to external aggregation system (ELK, Splunk, etc.)"""
        # Mock implementation - in production this would send to actual log aggregators
        if level in ["ERROR", "CRITICAL"]:
            # High priority logs - send immediately to alerting system
            pass
        else:
            # Standard logs - batch to aggregation system
            pass

class RequestTrackingMiddleware:
    """Enhanced request tracking with correlation IDs"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("request_tracking")

    async def track_request(self, request, call_next):
        """Track request with enhanced context"""
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        with self.logger.correlation_manager.correlation_context(correlation_id):
            start_time = time.time()

            # Enhanced request logging
            request_data = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_length": request.headers.get("content-length"),
                "correlation_id": correlation_id
            }

            # Filter sensitive headers
            sensitive_headers = {"authorization", "cookie", "x-api-key"}
            request_data["headers"] = {
                k: "***MASKED***" if k.lower() in sensitive_headers else v
                for k, v in request_data["headers"].items()
            }

            self.logger.info("Request started", extra=request_data)

            try:
                response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000

                # Enhanced response logging
                response_data = {
                    **request_data,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_size": response.headers.get("content-length"),
                    "cache_status": response.headers.get("x-cache-status")
                }

                if response.status_code >= 400:
                    self.logger.warning("Request failed", extra=response_data)
                else:
                    self.logger.info("Request completed", extra=response_data)

                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id

                return response

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_data = {
                    **request_data,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms
                }
                self.logger.error("Request error", extra=error_data, exc_info=True)
                raise

class PerformanceLogger:
    """Performance monitoring logger"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("performance")
        self.performance_data = defaultdict(list)

    @contextmanager
    def track_operation(self, operation_name: str, **context):
        """Context manager for tracking operation performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield

        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory

            perf_data = {
                "operation": operation_name,
                "duration_ms": duration_ms,
                "memory_start_mb": start_memory,
                "memory_end_mb": end_memory,
                "memory_delta_mb": memory_delta,
                "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
                **context
            }

            # Store for aggregation
            self.performance_data[operation_name].append(perf_data)

            # Log based on performance thresholds
            if duration_ms > 5000:  # Slow operation
                self.logger.warning("Slow operation detected", extra=perf_data)
            elif duration_ms > 1000:  # Moderate performance
                self.logger.info("Operation completed", extra=perf_data)
            else:
                self.logger.debug("Fast operation", extra=perf_data)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def get_performance_summary(self, operation_name: str = None) -> Dict[str, Any]:
        """Get performance summary for operations"""
        if operation_name:
            data = self.performance_data.get(operation_name, [])
        else:
            data = []
            for op_data in self.performance_data.values():
                data.extend(op_data)

        if not data:
            return {}

        durations = [item["duration_ms"] for item in data]
        memory_deltas = [item["memory_delta_mb"] for item in data]

        return {
            "operation_count": len(data),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_memory_delta_mb": sum(memory_deltas) / len(memory_deltas),
            "total_operations": len(data),
            "operations_per_second": len(data) / (max(durations) / 1000) if durations else 0
        }

class SecurityAuditLogger:
    """Security-focused audit logging"""

    def __init__(self, logger: Optional[CoreStructuredLogger] = None):
        self.logger = logger or CoreStructuredLogger("security_audit")

    async def log_authentication_attempt(
        self,
        user_identifier: str,
        success: bool,
        method: str,
        ip_address: str,
        user_agent: str = None,
        **context
    ):
        """Log authentication attempts"""
        audit_data = {
            "event_type": "authentication_attempt",
            "user_identifier": user_identifier,
            "success": success,
            "auth_method": method,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
            **context
        }

        if success:
            self.logger.info("Authentication successful", extra=audit_data)
        else:
            self.logger.warning("Authentication failed", extra=audit_data)

    async def log_authorization_check(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        **context
    ):
        """Log authorization checks"""
        audit_data = {
            "event_type": "authorization_check",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "granted": granted,
            "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
            **context
        }

        if granted:
            self.logger.info("Authorization granted", extra=audit_data)
        else:
            self.logger.warning("Authorization denied", extra=audit_data)

    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        record_count: int = None,
        **context
    ):
        """Log data access operations"""
        audit_data = {
            "event_type": "data_access",
            "user_id": user_id,
            "data_type": data_type,
            "operation": operation,
            "record_count": record_count,
            "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
            **context
        }

        self.logger.info("Data access", extra=audit_data)

    async def log_security_incident(
        self,
        incident_type: str,
        severity: str,
        description: str,
        affected_user: str = None,
        **context
    ):
        """Log security incidents"""
        incident_data = {
            "event_type": "security_incident",
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "affected_user": affected_user,
            "correlation_id": self.logger.correlation_manager.get_current_correlation_id(),
            **context
        }

        if severity in ["high", "critical"]:
            self.logger.critical("Security incident", extra=incident_data)
        else:
            self.logger.error("Security incident", extra=incident_data)

def setup_comprehensive_logging(app, config: Optional[LogConfiguration] = None):
    """Setup comprehensive logging for FastAPI application"""
    config = config or LogConfiguration.from_environment()

    # Create loggers
    app_logger = CoreStructuredLogger("app", config)
    request_logger = CoreStructuredLogger("requests", config)
    performance_logger = PerformanceLogger(CoreStructuredLogger("performance", config))
    security_logger = SecurityAuditLogger(CoreStructuredLogger("security", config))
    log_aggregator = LogAggregator(CoreStructuredLogger("aggregator", config))

    # Setup request tracking middleware
    request_middleware = RequestTrackingMiddleware(request_logger)

    @app.middleware("http")
    async def logging_middleware(request, call_next):
        return await request_middleware.track_request(request, call_next)

    # Store loggers in app state for access
    app.state.loggers = {
        "app": app_logger,
        "requests": request_logger,
        "performance": performance_logger,
        "security": security_logger,
        "aggregator": log_aggregator
    }

    # Setup periodic log flushing
    @app.on_event("startup")
    async def setup_log_flushing():
        async def periodic_flush():
            while True:
                await asyncio.sleep(60)  # Flush every minute
                try:
                    await log_aggregator.flush_logs()
                except Exception as e:
                    app_logger.error(f"Log flushing failed: {str(e)}")

        # Start background task
        asyncio.create_task(periodic_flush())

    @app.on_event("shutdown")
    async def final_log_flush():
        await log_aggregator.flush_logs()

# Global logger instance
default_logger = CoreStructuredLogger("app")

# Utility functions for easy access
def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return default_logger.correlation_manager.get_current_correlation_id()

def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    default_logger.correlation_manager.set_correlation_id(correlation_id)

def get_performance_logger() -> PerformanceLogger:
    """Get global performance logger"""
    return PerformanceLogger()

def get_security_logger() -> SecurityAuditLogger:
    """Get global security audit logger"""
    return SecurityAuditLogger()