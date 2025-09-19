"""
Advanced Monitoring and Logging Service - T060-T062 Implementation

This service provides comprehensive monitoring and logging capabilities:
- Real-time metrics collection
- Advanced log aggregation and analysis
- Alert management and notifications
- Performance monitoring
- Health checks and status monitoring
- Custom dashboards and reports

Author: Claude Code Assistant
Created: 2025-09-19
Tasks: T060-T062 - Advanced Monitoring & Logging
"""

import asyncio
import logging
import json
import time
import psutil
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import aioredis
from contextlib import asynccontextmanager

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Metric:
    """A single metric measurement."""
    name: str
    value: float
    type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""
    description: str = ""

@dataclass
class LogEntry:
    """A structured log entry."""
    message: str
    level: LogLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    logger: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0
    user_id: str = ""
    request_id: str = ""
    session_id: str = ""
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None

@dataclass
class Alert:
    """An alert configuration and state."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    condition: str = ""  # e.g., "cpu_usage > 80"
    severity: AlertSeverity = AlertSeverity.MEDIUM
    status: AlertStatus = AlertStatus.ACTIVE
    threshold: float = 0.0
    metric_name: str = ""
    evaluation_window_minutes: int = 5
    notification_channels: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    suppressed_until: Optional[datetime] = None

@dataclass
class HealthCheck:
    """Health check configuration and result."""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    check_type: str = "http"  # http, database, redis, custom
    target: str = ""
    timeout_seconds: int = 30
    interval_seconds: int = 60
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    response_time_ms: float = 0.0
    error_message: str = ""
    consecutive_failures: int = 0
    max_failures: int = 3

@dataclass
class SystemMetrics:
    """System-level metrics snapshot."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_usage_percent: float = 0.0
    disk_usage_gb: float = 0.0
    disk_usage_percent: float = 0.0
    network_io_mb: float = 0.0
    disk_io_mb: float = 0.0
    active_connections: int = 0
    request_rate_per_second: float = 0.0
    error_rate_percent: float = 0.0
    avg_response_time_ms: float = 0.0

# ============================================================================
# MONITORING SERVICE
# ============================================================================

class AdvancedMonitoringService:
    """Service for advanced monitoring and logging."""

    def __init__(self):
        self.metrics_buffer: List[Metric] = []
        self.log_buffer: List[LogEntry] = []
        self.alerts: Dict[str, Alert] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metric_aggregations: Dict[str, List[float]] = {}
        self.notification_handlers: Dict[str, Callable] = {}

        # Configure structured logging
        self.logger = structlog.get_logger()

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False

    async def start_monitoring(self):
        """Start the monitoring service."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Advanced monitoring service started")

    async def stop_monitoring(self):
        """Stop the monitoring service."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Advanced monitoring service stopped")

    # ========================================================================
    # METRICS COLLECTION
    # ========================================================================

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Dict[str, str] = None,
        unit: str = "",
        description: str = ""
    ):
        """Record a metric measurement."""
        metric = Metric(
            name=name,
            value=value,
            type=metric_type,
            tags=tags or {},
            unit=unit,
            description=description
        )

        self.metrics_buffer.append(metric)

        # Update aggregations for alert evaluation
        if name not in self.metric_aggregations:
            self.metric_aggregations[name] = []

        self.metric_aggregations[name].append(value)

        # Keep only recent values (last 100)
        if len(self.metric_aggregations[name]) > 100:
            self.metric_aggregations[name] = self.metric_aggregations[name][-100:]

        # Check alerts
        await self._evaluate_alerts(name, value)

    async def record_counter(self, name: str, increment: float = 1.0, tags: Dict[str, str] = None):
        """Record a counter metric."""
        await self.record_metric(name, increment, MetricType.COUNTER, tags)

    async def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer metric."""
        await self.record_metric(name, duration_ms, MetricType.TIMER, tags, "ms")

    @asynccontextmanager
    async def timer_context(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            await self.record_timer(name, duration_ms, tags)

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_mb = memory.used / 1024 / 1024
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_gb = disk.used / 1024 / 1024 / 1024
        disk_percent = (disk.used / disk.total) * 100

        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            network_io_mb = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024
        except:
            network_io_mb = 0

        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024
        except:
            disk_io_mb = 0

        # Network connections
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0

        metrics = SystemMetrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_mb,
            memory_usage_percent=memory_percent,
            disk_usage_gb=disk_gb,
            disk_usage_percent=disk_percent,
            network_io_mb=network_io_mb,
            disk_io_mb=disk_io_mb,
            active_connections=connections
        )

        # Record as individual metrics
        await self.record_metric("system.cpu_usage", cpu_percent, MetricType.GAUGE, unit="%")
        await self.record_metric("system.memory_usage", memory_mb, MetricType.GAUGE, unit="MB")
        await self.record_metric("system.disk_usage", disk_gb, MetricType.GAUGE, unit="GB")
        await self.record_metric("system.network_io", network_io_mb, MetricType.GAUGE, unit="MB")
        await self.record_metric("system.connections", connections, MetricType.GAUGE)

        return metrics

    async def get_metric_aggregation(
        self,
        metric_name: str,
        aggregation_type: str = "avg",
        window_minutes: int = 5
    ) -> Optional[float]:
        """Get aggregated metric value over a time window."""
        values = self.metric_aggregations.get(metric_name, [])
        if not values:
            return None

        # For simplicity, use all recent values
        # In production, filter by time window
        if aggregation_type == "avg":
            return sum(values) / len(values)
        elif aggregation_type == "max":
            return max(values)
        elif aggregation_type == "min":
            return min(values)
        elif aggregation_type == "sum":
            return sum(values)
        elif aggregation_type == "count":
            return len(values)
        else:
            return None

    # ========================================================================
    # LOGGING
    # ========================================================================

    async def log_structured(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        logger_name: str = "",
        user_id: str = "",
        request_id: str = "",
        session_id: str = "",
        extra_fields: Dict[str, Any] = None,
        exception: Exception = None
    ):
        """Log a structured message."""
        import inspect

        # Get caller information
        frame = inspect.currentframe().f_back
        module = frame.f_globals.get("__name__", "")
        function = frame.f_code.co_name
        line_number = frame.f_lineno

        log_entry = LogEntry(
            message=message,
            level=level,
            logger=logger_name,
            module=module,
            function=function,
            line_number=line_number,
            user_id=user_id,
            request_id=request_id,
            session_id=session_id,
            extra_fields=extra_fields or {},
            exception=str(exception) if exception else None,
            stack_trace=traceback.format_exc() if exception else None
        )

        self.log_buffer.append(log_entry)

        # Also log to standard logger
        standard_logger = logging.getLogger(logger_name)
        log_method = getattr(standard_logger, level.value)

        if exception:
            log_method(f"{message} - Exception: {exception}", exc_info=True)
        else:
            log_method(message)

        # Check for error-based alerts
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            await self._check_error_rate_alerts()

    async def query_logs(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        level: LogLevel = None,
        logger: str = "",
        user_id: str = "",
        search_text: str = "",
        limit: int = 100
    ) -> List[LogEntry]:
        """Query logs with filters."""
        filtered_logs = self.log_buffer.copy()

        # Apply filters
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]

        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]

        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if logger:
            filtered_logs = [log for log in filtered_logs if logger.lower() in log.logger.lower()]

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        if search_text:
            filtered_logs = [
                log for log in filtered_logs
                if search_text.lower() in log.message.lower()
            ]

        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        return filtered_logs[:limit]

    async def get_log_statistics(
        self,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get log statistics for the specified time window."""
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_logs = [log for log in self.log_buffer if log.timestamp >= since]

        stats = {
            "total_logs": len(recent_logs),
            "by_level": {},
            "by_logger": {},
            "error_rate": 0.0,
            "top_errors": [],
            "time_window_minutes": window_minutes
        }

        # Count by level
        for level in LogLevel:
            count = len([log for log in recent_logs if log.level == level])
            stats["by_level"][level.value] = count

        # Count by logger
        loggers = {}
        for log in recent_logs:
            loggers[log.logger] = loggers.get(log.logger, 0) + 1
        stats["by_logger"] = loggers

        # Error rate
        error_logs = len([log for log in recent_logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]])
        stats["error_rate"] = (error_logs / len(recent_logs) * 100) if recent_logs else 0

        # Top errors
        error_messages = {}
        for log in recent_logs:
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_messages[log.message] = error_messages.get(log.message, 0) + 1

        stats["top_errors"] = sorted(
            [{"message": msg, "count": count} for msg, count in error_messages.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        return stats

    # ========================================================================
    # ALERTS
    # ========================================================================

    async def create_alert(
        self,
        name: str,
        description: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        evaluation_window_minutes: int = 5,
        notification_channels: List[str] = None
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            name=name,
            description=description,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            evaluation_window_minutes=evaluation_window_minutes,
            notification_channels=notification_channels or []
        )

        self.alerts[alert.alert_id] = alert
        self.logger.info(f"Created alert: {name} ({alert.alert_id})")

        return alert

    async def _evaluate_alerts(self, metric_name: str, current_value: float):
        """Evaluate alerts for a specific metric."""
        for alert in self.alerts.values():
            if alert.metric_name != metric_name or alert.status != AlertStatus.ACTIVE:
                continue

            # Check if alert is suppressed
            if alert.suppressed_until and datetime.utcnow() < alert.suppressed_until:
                continue

            # Evaluate condition
            triggered = await self._evaluate_alert_condition(alert, current_value)

            if triggered:
                await self._trigger_alert(alert)

    async def _evaluate_alert_condition(self, alert: Alert, current_value: float) -> bool:
        """Evaluate if an alert condition is met."""
        condition = alert.condition.lower()

        if ">" in condition:
            return current_value > alert.threshold
        elif "<" in condition:
            return current_value < alert.threshold
        elif "=" in condition:
            return abs(current_value - alert.threshold) < 0.001  # Floating point comparison
        elif "avg" in condition:
            # Average over evaluation window
            avg_value = await self.get_metric_aggregation(
                alert.metric_name,
                "avg",
                alert.evaluation_window_minutes
            )
            if avg_value is None:
                return False

            if ">" in condition:
                return avg_value > alert.threshold
            elif "<" in condition:
                return avg_value < alert.threshold

        return False

    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert."""
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1

        alert_data = {
            "alert_id": alert.alert_id,
            "name": alert.name,
            "description": alert.description,
            "severity": alert.severity.value,
            "metric_name": alert.metric_name,
            "threshold": alert.threshold,
            "triggered_at": alert.last_triggered.isoformat(),
            "trigger_count": alert.trigger_count
        }

        # Send notifications
        for channel in alert.notification_channels:
            await self._send_notification(channel, alert_data)

        # Log alert
        await self.log_structured(
            f"Alert triggered: {alert.name}",
            LogLevel.WARNING,
            "alert_system",
            extra_fields=alert_data
        )

    async def _send_notification(self, channel: str, alert_data: Dict[str, Any]):
        """Send alert notification to a channel."""
        handler = self.notification_handlers.get(channel)
        if handler:
            try:
                await handler(alert_data)
            except Exception as e:
                self.logger.error(f"Failed to send notification to {channel}: {e}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "") -> bool:
        """Acknowledge an alert."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        await self.log_structured(
            f"Alert acknowledged: {alert.name}",
            LogLevel.INFO,
            "alert_system",
            extra_fields={"alert_id": alert_id, "acknowledged_by": acknowledged_by}
        )

        return True

    async def resolve_alert(self, alert_id: str, resolved_by: str = "") -> bool:
        """Resolve an alert."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.RESOLVED
        await self.log_structured(
            f"Alert resolved: {alert.name}",
            LogLevel.INFO,
            "alert_system",
            extra_fields={"alert_id": alert_id, "resolved_by": resolved_by}
        )

        return True

    async def suppress_alert(
        self,
        alert_id: str,
        duration_minutes: int,
        suppressed_by: str = ""
    ) -> bool:
        """Suppress an alert for a specified duration."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.suppressed_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        await self.log_structured(
            f"Alert suppressed: {alert.name} for {duration_minutes} minutes",
            LogLevel.INFO,
            "alert_system",
            extra_fields={
                "alert_id": alert_id,
                "suppressed_by": suppressed_by,
                "duration_minutes": duration_minutes
            }
        )

        return True

    async def _check_error_rate_alerts(self):
        """Check for error rate based alerts."""
        # Calculate current error rate
        window_minutes = 5
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_logs = [log for log in self.log_buffer if log.timestamp >= since]

        if not recent_logs:
            return

        error_logs = [log for log in recent_logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        error_rate = (len(error_logs) / len(recent_logs)) * 100

        # Record as metric for alert evaluation
        await self.record_metric("application.error_rate", error_rate, MetricType.GAUGE, unit="%")

    # ========================================================================
    # HEALTH CHECKS
    # ========================================================================

    async def register_health_check(
        self,
        name: str,
        description: str,
        check_type: str,
        target: str,
        timeout_seconds: int = 30,
        interval_seconds: int = 60,
        max_failures: int = 3
    ) -> HealthCheck:
        """Register a new health check."""
        health_check = HealthCheck(
            name=name,
            description=description,
            check_type=check_type,
            target=target,
            timeout_seconds=timeout_seconds,
            interval_seconds=interval_seconds,
            max_failures=max_failures
        )

        self.health_checks[health_check.check_id] = health_check
        self.logger.info(f"Registered health check: {name} ({health_check.check_id})")

        return health_check

    async def run_health_check(self, check_id: str) -> bool:
        """Run a specific health check."""
        health_check = self.health_checks.get(check_id)
        if not health_check:
            return False

        start_time = time.time()

        try:
            # Run the appropriate check
            if health_check.check_type == "http":
                success = await self._check_http_health(health_check.target, health_check.timeout_seconds)
            elif health_check.check_type == "database":
                success = await self._check_database_health(health_check.target)
            elif health_check.check_type == "redis":
                success = await self._check_redis_health(health_check.target)
            else:
                success = await self._check_custom_health(health_check.target)

            response_time = (time.time() - start_time) * 1000

            # Update health check status
            health_check.last_check = datetime.utcnow()
            health_check.response_time_ms = response_time

            if success:
                health_check.status = HealthStatus.HEALTHY
                health_check.last_success = datetime.utcnow()
                health_check.consecutive_failures = 0
                health_check.error_message = ""
            else:
                health_check.consecutive_failures += 1
                if health_check.consecutive_failures >= health_check.max_failures:
                    health_check.status = HealthStatus.UNHEALTHY
                else:
                    health_check.status = HealthStatus.DEGRADED

            # Record metrics
            await self.record_metric(
                f"health_check.{health_check.name}.response_time",
                response_time,
                MetricType.TIMER,
                {"check_type": health_check.check_type}
            )

            await self.record_metric(
                f"health_check.{health_check.name}.success",
                1 if success else 0,
                MetricType.GAUGE,
                {"check_type": health_check.check_type}
            )

            return success

        except Exception as e:
            health_check.consecutive_failures += 1
            health_check.status = HealthStatus.UNHEALTHY
            health_check.error_message = str(e)
            health_check.last_check = datetime.utcnow()

            await self.log_structured(
                f"Health check failed: {health_check.name}",
                LogLevel.ERROR,
                "health_check",
                extra_fields={"check_id": check_id, "error": str(e)},
                exception=e
            )

            return False

    async def _check_http_health(self, url: str, timeout: int) -> bool:
        """Check HTTP endpoint health."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    return response.status < 400
        except:
            return False

    async def _check_database_health(self, connection_string: str) -> bool:
        """Check database health."""
        # Mock implementation - in real app, test actual database connection
        try:
            await asyncio.sleep(0.1)  # Simulate connection test
            return True
        except:
            return False

    async def _check_redis_health(self, connection_string: str) -> bool:
        """Check Redis health."""
        # Mock implementation - in real app, test actual Redis connection
        try:
            await asyncio.sleep(0.05)  # Simulate Redis ping
            return True
        except:
            return False

    async def _check_custom_health(self, target: str) -> bool:
        """Check custom health."""
        # Mock implementation - in real app, run custom health check logic
        return True

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        health_summary = {
            "overall_status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [],
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0
            }
        }

        # Collect all health check statuses
        for health_check in self.health_checks.values():
            check_info = {
                "name": health_check.name,
                "status": health_check.status.value,
                "last_check": health_check.last_check.isoformat() if health_check.last_check else None,
                "response_time_ms": health_check.response_time_ms,
                "consecutive_failures": health_check.consecutive_failures,
                "error_message": health_check.error_message
            }

            health_summary["checks"].append(check_info)
            health_summary["summary"][health_check.status.value] += 1

        # Determine overall status
        if health_summary["summary"]["unhealthy"] > 0:
            health_summary["overall_status"] = HealthStatus.UNHEALTHY.value
        elif health_summary["summary"]["degraded"] > 0:
            health_summary["overall_status"] = HealthStatus.DEGRADED.value

        return health_summary

    # ========================================================================
    # MONITORING LOOP
    # ========================================================================

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                # Collect system metrics
                await self.collect_system_metrics()

                # Run health checks
                for health_check in self.health_checks.values():
                    if self._should_run_health_check(health_check):
                        await self.run_health_check(health_check.check_id)

                # Cleanup old data
                await self._cleanup_old_data()

                # Wait for next iteration
                await asyncio.sleep(30)  # Run every 30 seconds

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)

    def _should_run_health_check(self, health_check: HealthCheck) -> bool:
        """Determine if a health check should be run."""
        if not health_check.last_check:
            return True

        elapsed = (datetime.utcnow() - health_check.last_check).total_seconds()
        return elapsed >= health_check.interval_seconds

    async def _cleanup_old_data(self):
        """Clean up old metrics and logs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        # Clean old metrics
        self.metrics_buffer = [
            metric for metric in self.metrics_buffer
            if metric.timestamp > cutoff_time
        ]

        # Clean old logs
        self.log_buffer = [
            log for log in self.log_buffer
            if log.timestamp > cutoff_time
        ]

    # ========================================================================
    # NOTIFICATION HANDLERS
    # ========================================================================

    def register_notification_handler(self, channel: str, handler: Callable):
        """Register a notification handler for a channel."""
        self.notification_handlers[channel] = handler

    async def default_email_handler(self, alert_data: Dict[str, Any]):
        """Default email notification handler."""
        # Mock email sending
        self.logger.info(f"Email notification sent for alert: {alert_data['name']}")

    async def default_slack_handler(self, alert_data: Dict[str, Any]):
        """Default Slack notification handler."""
        # Mock Slack notification
        self.logger.info(f"Slack notification sent for alert: {alert_data['name']}")

    async def default_webhook_handler(self, alert_data: Dict[str, Any]):
        """Default webhook notification handler."""
        # Mock webhook call
        self.logger.info(f"Webhook notification sent for alert: {alert_data['name']}")

# ============================================================================
# SERVICE INSTANCE
# ============================================================================

monitoring_service = AdvancedMonitoringService()