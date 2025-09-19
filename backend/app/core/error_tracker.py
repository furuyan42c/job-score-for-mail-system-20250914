"""
Core Error Tracking System
T062-GREEN: Basic implementation for error tracking with capture, reporting, and alerting
"""

import json
import time
import hashlib
import uuid
import sys
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
import threading
# Email imports for notifications (optional)
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Email functionality will be limited if not available
    pass

from app.core.logging import CoreStructuredLogger


@dataclass
class ErrorData:
    """Error data structure"""
    id: str
    exception_type: str
    message: str
    timestamp: datetime
    fingerprint: str
    stack_trace: List[str]
    context: Dict[str, Any]
    severity: str
    count: int = 1


class ErrorTracker:
    """Core error tracking functionality"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {
            "enable_capture": True,
            "enable_reporting": True,
            "aggregation_window": 300,
            "alert_thresholds": {
                "error_rate": 10,
                "critical_errors": 5
            }
        }
        self.logger = CoreStructuredLogger("error_tracker")
        self._errors: Dict[str, ErrorData] = {}
        self._fingerprint_to_id: Dict[str, str] = {}
        self._lock = threading.Lock()

    def is_enabled(self) -> bool:
        """Check if error tracking is enabled"""
        return self.config.get("enable_capture", True)

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ) -> str:
        """Capture exception with context"""
        if not self.is_enabled():
            return ""

        # Generate error fingerprint
        fingerprint = self.get_error_fingerprint(exception)

        with self._lock:
            # Check if we've seen this error before
            if fingerprint in self._fingerprint_to_id:
                error_id = self._fingerprint_to_id[fingerprint]
                self._errors[error_id].count += 1
                self._errors[error_id].timestamp = datetime.now(timezone.utc)
                return error_id

            # New error
            error_id = str(uuid.uuid4())
            error_data = ErrorData(
                id=error_id,
                exception_type=type(exception).__name__,
                message=str(exception),
                timestamp=datetime.now(timezone.utc),
                fingerprint=fingerprint,
                stack_trace=traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ),
                context=context or {},
                severity=severity
            )

            self._errors[error_id] = error_data
            self._fingerprint_to_id[fingerprint] = error_id

            # Log the error
            self.logger.error(
                f"Exception captured: {error_data.exception_type}",
                extra={
                    "error_id": error_id,
                    "exception_type": error_data.exception_type,
                    "message": error_data.message,
                    "severity": severity,
                    "context": context
                }
            )

            return error_id

    def get_error_fingerprint(self, exception: Exception) -> str:
        """Generate fingerprint for error deduplication"""
        # Use exception type, message, and first few stack frames
        fingerprint_data = {
            "type": type(exception).__name__,
            "message": str(exception),
            "stack": traceback.format_tb(exception.__traceback__)[:3]  # First 3 frames
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def get_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored error"""
        with self._lock:
            error_data = self._errors.get(error_id)
            if error_data:
                return asdict(error_data)
            return None

    def search_errors(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search and filter errors"""
        with self._lock:
            results = []
            for error_data in self._errors.values():
                if self._matches_filters(error_data, filters):
                    results.append(asdict(error_data))
            return results

    def _matches_filters(self, error_data: ErrorData, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if error matches filters"""
        if not filters:
            return True

        for key, value in filters.items():
            if key == "exception_type" and error_data.exception_type != value:
                return False
            elif key == "severity" and error_data.severity != value:
                return False
            elif key == "time_range":
                # Implement time range filtering
                pass

        return True


class ErrorReporter:
    """Error reporting functionality"""

    def __init__(self, error_tracker: Optional[ErrorTracker] = None):
        self.error_tracker = error_tracker
        self.logger = CoreStructuredLogger("error_reporter")
        self._scheduled_jobs: Dict[str, Dict] = {}

    def generate_report(self, errors: List[Dict[str, Any]], time_range: str) -> Dict[str, Any]:
        """Generate comprehensive error report"""
        total_errors = sum(error.get("count", 1) for error in errors)
        unique_errors = len(errors)

        # Group by exception type
        by_type = defaultdict(int)
        for error in errors:
            by_type[error["exception_type"]] += error.get("count", 1)

        # Group by severity
        by_severity = defaultdict(int)
        for error in errors:
            by_severity[error["severity"]] += error.get("count", 1)

        return {
            "summary": {
                "total_errors": total_errors,
                "unique_errors": unique_errors,
                "time_range": time_range,
                "generated_at": datetime.now(timezone.utc).isoformat()
            },
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "errors": errors
        }

    def format_error(self, error: Dict[str, Any], format: str = "json") -> str:
        """Format error for different output formats"""
        if format == "json":
            return json.dumps(error, indent=2, default=str)

        elif format == "html":
            return f"""
            <html>
            <body>
                <h2>Error Report</h2>
                <p><strong>Type:</strong> {error['exception_type']}</p>
                <p><strong>Message:</strong> {error['message']}</p>
                <p><strong>Timestamp:</strong> {error['timestamp']}</p>
                <p><strong>ID:</strong> {error['id']}</p>
                <h3>Stack Trace</h3>
                <pre>{''.join(error.get('stack_trace', []))}</pre>
            </body>
            </html>
            """

        elif format == "text":
            stack_trace = ''.join(error.get('stack_trace', []))
            return f"""
Error Report
============
Type: {error['exception_type']}
Message: {error['message']}
Timestamp: {error['timestamp']}
ID: {error['id']}

Stack Trace:
{stack_trace}
            """

        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_scheduler(self) -> 'ReportScheduler':
        """Get report scheduler"""
        return ReportScheduler(self)


class ReportScheduler:
    """Report scheduling functionality"""

    def __init__(self, reporter: ErrorReporter):
        self.reporter = reporter
        self._jobs: Dict[str, Dict] = {}

    def schedule_report(
        self,
        interval: str,
        recipients: List[str],
        format: str = "html"
    ) -> str:
        """Schedule periodic report"""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "interval": interval,
            "recipients": recipients,
            "format": format,
            "created_at": datetime.now(timezone.utc),
            "active": True
        }
        return job_id

    def is_job_scheduled(self, job_id: str) -> bool:
        """Check if job is scheduled"""
        return job_id in self._jobs and self._jobs[job_id]["active"]

    def cancel_report(self, job_id: str):
        """Cancel scheduled report"""
        if job_id in self._jobs:
            self._jobs[job_id]["active"] = False


class ErrorAggregation:
    """Error aggregation and analysis"""

    def __init__(self):
        self._error_records: List[Dict[str, Any]] = []
        self.logger = CoreStructuredLogger("error_aggregation")

    def record_error(self, timestamp: float, error_type: str, **kwargs):
        """Record error for aggregation"""
        self._error_records.append({
            "timestamp": timestamp,
            "error_type": error_type,
            **kwargs
        })

    def calculate_error_rate(self, time_window: int, error_type: Optional[str] = None) -> float:
        """Calculate error rate over time window"""
        current_time = time.time()
        cutoff_time = current_time - time_window

        relevant_errors = [
            record for record in self._error_records
            if record["timestamp"] > cutoff_time and
            (error_type is None or record["error_type"] == error_type)
        ]

        return len(relevant_errors)

    def analyze_trend(self, error_type: str, time_window: int) -> Dict[str, Any]:
        """Analyze error trend over time"""
        current_time = time.time()
        cutoff_time = current_time - time_window

        relevant_errors = [
            record for record in self._error_records
            if record["timestamp"] > cutoff_time and record["error_type"] == error_type
        ]

        if len(relevant_errors) < 2:
            return {"direction": "stable", "slope": 0}

        # Simple trend analysis: compare first and second half
        mid_time = cutoff_time + (time_window / 2)
        first_half = [r for r in relevant_errors if r["timestamp"] < mid_time]
        second_half = [r for r in relevant_errors if r["timestamp"] >= mid_time]

        first_rate = len(first_half) / (time_window / 2)
        second_rate = len(second_half) / (time_window / 2)

        slope = second_rate - first_rate

        if slope > 0.1:
            direction = "increasing"
        elif slope < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"

        return {"direction": direction, "slope": slope}

    def detect_correlations(self, time_window: int) -> List[Dict[str, Any]]:
        """Detect correlations between error types"""
        current_time = time.time()
        cutoff_time = current_time - time_window

        relevant_errors = [
            record for record in self._error_records
            if record["timestamp"] > cutoff_time
        ]

        # Group by type
        by_type = defaultdict(list)
        for error in relevant_errors:
            by_type[error["error_type"]].append(error["timestamp"])

        correlations = []
        types = list(by_type.keys())

        # Simple correlation detection: errors occurring close in time
        for i, type1 in enumerate(types):
            for type2 in types[i+1:]:
                correlation_score = self._calculate_correlation(
                    by_type[type1], by_type[type2]
                )

                if correlation_score > 0.5:  # Threshold for correlation
                    correlations.append({
                        "error_type_1": type1,
                        "error_type_2": type2,
                        "correlation_score": correlation_score
                    })

        return correlations

    def _calculate_correlation(self, timestamps1: List[float], timestamps2: List[float]) -> float:
        """Calculate correlation between two error types"""
        # Simple correlation: how often errors occur within 30 seconds of each other
        correlation_count = 0
        total_pairs = 0

        for ts1 in timestamps1:
            for ts2 in timestamps2:
                total_pairs += 1
                if abs(ts1 - ts2) <= 30:  # Within 30 seconds
                    correlation_count += 1

        return correlation_count / total_pairs if total_pairs > 0 else 0


class AlertThresholds:
    """Alert threshold management"""

    def __init__(self):
        self._thresholds: Dict[str, Dict[str, float]] = {}
        self._suppression: Dict[str, float] = {}  # metric -> last_alert_time
        self.logger = CoreStructuredLogger("alert_thresholds")

    def configure(self, thresholds: Dict[str, Dict[str, float]]):
        """Configure alert thresholds"""
        self._thresholds = thresholds

    def get_configuration(self) -> Dict[str, Dict[str, float]]:
        """Get current threshold configuration"""
        return self._thresholds.copy()

    def evaluate_threshold(
        self,
        metric: str,
        value: float,
        suppress_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Evaluate threshold and trigger alerts"""
        if metric not in self._thresholds:
            return {"triggered": False, "reason": "No threshold configured"}

        thresholds = self._thresholds[metric]
        current_time = time.time()

        # Check suppression
        if suppress_duration and metric in self._suppression:
            last_alert = self._suppression[metric]
            if current_time - last_alert < suppress_duration:
                return {
                    "triggered": False,
                    "suppressed": True,
                    "suppression_remaining": suppress_duration - (current_time - last_alert)
                }

        # Evaluate thresholds
        alert_level = None
        if value >= thresholds.get("critical", float('inf')):
            alert_level = "critical"
        elif value >= thresholds.get("warning", float('inf')):
            alert_level = "warning"

        if alert_level:
            # Record alert time for suppression
            if suppress_duration:
                self._suppression[metric] = current_time

            return {
                "triggered": True,
                "level": alert_level,
                "metric": metric,
                "value": value,
                "threshold": thresholds[alert_level],
                "timestamp": current_time
            }

        return {"triggered": False}


class ExceptionHandler:
    """Exception handler integration"""

    def __init__(self, error_tracker: Optional[ErrorTracker] = None):
        self.error_tracker = error_tracker or ErrorTracker()
        self._original_handler = None
        self._captured_exceptions: List[Dict[str, Any]] = []

    def get_current_handler(self):
        """Get current exception handler"""
        return sys.excepthook

    def register_global_handler(self):
        """Register global exception handler"""
        self._original_handler = sys.excepthook
        sys.excepthook = self._exception_hook

    def restore_handler(self, handler):
        """Restore original exception handler"""
        sys.excepthook = handler

    def _exception_hook(self, exc_type, exc_value, exc_traceback):
        """Custom exception hook"""
        # Capture exception
        self.error_tracker.capture_exception(exc_value)

        # Call original handler
        if self._original_handler:
            self._original_handler(exc_type, exc_value, exc_traceback)

    @contextmanager
    def capture_exceptions(self):
        """Context manager for exception capture"""
        captured = ExceptionCapture()
        yield captured

    def capture(self, func: Callable) -> Callable:
        """Decorator for exception capture"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_id = self.error_tracker.capture_exception(e)
                self._captured_exceptions.append({
                    "exception_type": type(e).__name__,
                    "message": str(e),
                    "error_id": error_id,
                    "timestamp": datetime.now(timezone.utc)
                })
                return None
        return wrapper

    def get_last_captured(self) -> Optional[Dict[str, Any]]:
        """Get last captured exception"""
        return self._captured_exceptions[-1] if self._captured_exceptions else None


class ExceptionCapture:
    """Exception capture context manager"""

    def __init__(self):
        self._captured: List[Dict[str, Any]] = []

    def get_captured_exceptions(self) -> List[Dict[str, Any]]:
        """Get captured exceptions"""
        return self._captured.copy()


class ErrorNotifier:
    """Error notification system"""

    def __init__(self):
        self._channels: Dict[str, Dict[str, Any]] = {}
        self._rate_limits: Dict[str, deque] = defaultdict(deque)
        self._rate_limit_config = {"max_notifications": 10, "time_window": 300}
        self.logger = CoreStructuredLogger("error_notifier")

    def configure_channels(self, channels: Dict[str, Dict[str, Any]]):
        """Configure notification channels"""
        self._channels = channels

    def get_channel_configuration(self) -> Dict[str, Dict[str, Any]]:
        """Get channel configuration"""
        return self._channels.copy()

    def configure_rate_limit(self, max_notifications: int, time_window: int):
        """Configure rate limiting"""
        self._rate_limit_config = {
            "max_notifications": max_notifications,
            "time_window": time_window
        }

    def send_notification(
        self,
        channel: str,
        error_data: Dict[str, Any],
        template: str = "default"
    ) -> Dict[str, Any]:
        """Send notification through specified channel"""
        # Check rate limiting
        if self._is_rate_limited(channel):
            return {
                "success": False,
                "rate_limited": True,
                "message": "Rate limit exceeded"
            }

        # Record notification for rate limiting
        self._record_notification(channel)

        channel_config = self._channels.get(channel, {})
        if not channel_config.get("enabled", False):
            return {
                "success": False,
                "message": f"Channel {channel} not enabled"
            }

        try:
            if channel == "email":
                return self._send_email(error_data, channel_config, template)
            elif channel == "slack":
                return self._send_slack(error_data, channel_config, template)
            elif channel == "webhook":
                return self._send_webhook(error_data, channel_config, template)
            else:
                return {
                    "success": False,
                    "message": f"Unknown channel: {channel}"
                }
        except Exception as e:
            self.logger.error(f"Failed to send notification via {channel}", error=e)
            return {
                "success": False,
                "error": str(e)
            }

    def _is_rate_limited(self, channel: str) -> bool:
        """Check if channel is rate limited"""
        current_time = time.time()
        cutoff_time = current_time - self._rate_limit_config["time_window"]

        # Clean old entries
        while (self._rate_limits[channel] and
               self._rate_limits[channel][0] < cutoff_time):
            self._rate_limits[channel].popleft()

        return len(self._rate_limits[channel]) >= self._rate_limit_config["max_notifications"]

    def _record_notification(self, channel: str):
        """Record notification for rate limiting"""
        self._rate_limits[channel].append(time.time())

    def _send_email(self, error_data: Dict[str, Any], config: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Send email notification (mock implementation)"""
        # Mock implementation - would integrate with actual SMTP
        self.logger.info(f"Sending email notification to {config.get('recipients', [])}")
        return {"success": True, "channel": "email"}

    def _send_slack(self, error_data: Dict[str, Any], config: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Send Slack notification (mock implementation)"""
        # Mock implementation - would integrate with Slack API
        self.logger.info(f"Sending Slack notification to {config.get('channel', '#alerts')}")
        return {"success": True, "channel": "slack"}

    def _send_webhook(self, error_data: Dict[str, Any], config: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Send webhook notification (mock implementation)"""
        # Mock implementation - would make HTTP request
        self.logger.info(f"Sending webhook notification to {config.get('url', '')}")
        return {"success": True, "channel": "webhook"}


# Global error tracker instance
default_error_tracker = ErrorTracker()