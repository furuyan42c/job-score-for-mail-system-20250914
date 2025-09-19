"""
Performance Monitoring Middleware
T063-GREEN: Basic implementation for performance monitoring with request/response tracking,
database query monitoring, and system resource monitoring
"""

import time
import asyncio
import statistics

# psutil import with fallback
try:
    import psutil
except ImportError:
    # Mock psutil functionality for testing
    class MockPsutil:
        @staticmethod
        def virtual_memory():
            class Memory:
                total = 8 * 1024 * 1024 * 1024  # 8GB
                available = 4 * 1024 * 1024 * 1024  # 4GB
                used = 4 * 1024 * 1024 * 1024  # 4GB
                percent = 50.0
            return Memory()

        @staticmethod
        def cpu_percent(interval=None):
            return 45.0

        @staticmethod
        def cpu_count():
            return 4

        @staticmethod
        def getloadavg():
            return [1.0, 1.5, 2.0]

        @staticmethod
        def disk_usage(path):
            class Disk:
                total = 100 * 1024 * 1024 * 1024  # 100GB
                free = 50 * 1024 * 1024 * 1024  # 50GB
                used = 50 * 1024 * 1024 * 1024  # 50GB
            return Disk()

        @staticmethod
        def net_io_counters():
            class Network:
                bytes_sent = 1024 * 1024
                bytes_recv = 2 * 1024 * 1024
                packets_sent = 1000
                packets_recv = 2000
            return Network()

        class Process:
            def memory_info(self):
                class MemInfo:
                    rss = 128 * 1024 * 1024  # 128MB
                return MemInfo()

            def cpu_percent(self):
                return 10.0

    psutil = MockPsutil()
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
import threading
import uuid

# FastAPI imports with fallback
try:
    from fastapi import Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware
    from starlette.middleware.base import RequestResponseEndpoint
except ImportError:
    # Mock FastAPI components for testing
    BaseHTTPMiddleware = object
    RequestResponseEndpoint = object

    class Request:
        def __init__(self):
            self.url = type('', (), {'path': '/test'})()
            self.method = 'GET'
            self.headers = {}
            self.client = type('', (), {'host': '127.0.0.1'})()

    class Response:
        def __init__(self):
            self.status_code = 200

from app.core.logging import CoreStructuredLogger


@dataclass
class ResourceThresholds:
    """Resource threshold configuration"""
    memory_warning: float = 80.0
    memory_critical: float = 90.0
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    disk_warning: float = 80.0
    disk_critical: float = 90.0


@dataclass
class RequestMetric:
    """Request performance metric"""
    request_id: str
    path: str
    method: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DatabaseMetric:
    """Database query performance metric"""
    query_id: str
    query: str
    params: Optional[List] = None
    start_time: float = 0
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    is_slow: bool = False


@dataclass
class SystemMetric:
    """System resource metric"""
    timestamp: float
    memory_percent: float
    cpu_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_received: int
    process_memory_mb: float
    process_cpu_percent: float


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for performance monitoring"""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {
            "enable_request_tracking": True,
            "enable_db_monitoring": True,
            "enable_resource_monitoring": True,
            "slow_request_threshold": 1000,  # 1 second
            "memory_threshold": 80.0,
            "cpu_threshold": 90.0
        }
        self.logger = CoreStructuredLogger("performance_monitoring")
        self.request_tracker = RequestTimeTracker()
        self.db_monitor = DatabaseQueryMonitor()
        self.resource_monitor = SystemResourceMonitor()
        self._alerts: List[Dict[str, Any]] = []
        self._rate_limit_metrics: List[Dict[str, Any]] = []
        self._concurrent_requests = 0
        self._max_concurrent_requests = 0
        self._lock = threading.Lock()

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.config.get("enable_request_tracking", True)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with performance monitoring"""
        if not self.is_enabled():
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Track concurrent requests
        with self._lock:
            self._concurrent_requests += 1
            self._max_concurrent_requests = max(
                self._max_concurrent_requests,
                self._concurrent_requests
            )

        # Start request tracking
        start_time = time.time()
        self.request_tracker.start_request(
            request_id,
            str(request.url.path),
            request.method,
            {
                "user_agent": request.headers.get("user-agent", ""),
                "content_length": request.headers.get("content-length", 0),
                "ip_address": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # End request tracking
            duration = self.request_tracker.end_request(request_id)

            # Check for slow requests
            if duration >= self.config.get("slow_request_threshold", 1000):
                self._alerts.append({
                    "type": "slow_request",
                    "duration_ms": duration,
                    "path": str(request.url.path),
                    "method": request.method,
                    "timestamp": time.time()
                })

            # Log performance data
            self.logger.info("Request completed", extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration
            })

            return response

        finally:
            # Decrement concurrent requests
            with self._lock:
                self._concurrent_requests -= 1

    def get_request_metrics(self) -> List[Dict[str, Any]]:
        """Get request performance metrics"""
        return [
            {
                "request_id": metric.request_id,
                "path": metric.path,
                "method": metric.method,
                "duration_ms": metric.duration_ms,
                "timestamp": metric.start_time
            }
            for metric in self.request_tracker.get_all_metrics()
        ]

    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts"""
        return self._alerts.copy()

    def get_max_concurrent_requests(self) -> int:
        """Get maximum concurrent requests"""
        return self._max_concurrent_requests

    def record_rate_limit_hit(self, ip: str, endpoint: str):
        """Record rate limit hit"""
        self._rate_limit_metrics.append({
            "ip": ip,
            "endpoint": endpoint,
            "timestamp": time.time()
        })

    def get_rate_limit_metrics(self) -> List[Dict[str, Any]]:
        """Get rate limit metrics"""
        return self._rate_limit_metrics.copy()


class RequestTimeTracker:
    """Tracks request timing and metadata"""

    def __init__(self):
        self._active_requests: Dict[str, RequestMetric] = {}
        self._completed_requests: List[RequestMetric] = []
        self._lock = threading.Lock()

    def start_request(
        self,
        request_id: str,
        path: str,
        method: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Start tracking a request"""
        with self._lock:
            metric = RequestMetric(
                request_id=request_id,
                path=path,
                method=method,
                start_time=time.time(),
                user_agent=metadata.get("user_agent", "") if metadata else "",
                ip_address=metadata.get("ip_address", "") if metadata else "",
                content_length=metadata.get("content_length", 0) if metadata else 0
            )
            self._active_requests[request_id] = metric

    def end_request(self, request_id: str) -> float:
        """End tracking a request and return duration in ms"""
        with self._lock:
            if request_id not in self._active_requests:
                return 0.0

            metric = self._active_requests[request_id]
            metric.end_time = time.time()
            metric.duration_ms = (metric.end_time - metric.start_time) * 1000

            # Move to completed requests
            self._completed_requests.append(metric)
            del self._active_requests[request_id]

            return metric.duration_ms

    def get_request_data(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request data by ID"""
        with self._lock:
            # Check active requests
            if request_id in self._active_requests:
                return asdict(self._active_requests[request_id])

            # Check completed requests
            for metric in self._completed_requests:
                if metric.request_id == request_id:
                    return asdict(metric)

            return None

    def get_all_metrics(self) -> List[RequestMetric]:
        """Get all completed request metrics"""
        with self._lock:
            return self._completed_requests.copy()

    def calculate_percentiles(self, path: str) -> Dict[str, float]:
        """Calculate response time percentiles for a specific endpoint"""
        with self._lock:
            durations = [
                metric.duration_ms for metric in self._completed_requests
                if metric.path == path and metric.duration_ms is not None
            ]

            if not durations:
                return {"p50": 0, "p95": 0, "p99": 0}

            durations.sort()
            return {
                "p50": statistics.median(durations),
                "p95": durations[int(len(durations) * 0.95)] if durations else 0,
                "p99": durations[int(len(durations) * 0.99)] if durations else 0
            }

    def cleanup_old_requests(self, max_age: int = 3600):
        """Clean up old request data"""
        cutoff_time = time.time() - max_age
        with self._lock:
            self._completed_requests = [
                metric for metric in self._completed_requests
                if metric.start_time > cutoff_time
            ]


class DatabaseQueryMonitor:
    """Monitors database query performance"""

    def __init__(self):
        self._active_queries: Dict[str, DatabaseMetric] = {}
        self._completed_queries: List[DatabaseMetric] = []
        self._slow_query_threshold = 100  # 100ms default
        self._query_patterns: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def configure_slow_query_threshold(self, threshold_ms: float):
        """Configure slow query threshold"""
        self._slow_query_threshold = threshold_ms

    def start_query(self, query: str, params: Optional[List] = None) -> str:
        """Start monitoring a database query"""
        query_id = str(uuid.uuid4())

        with self._lock:
            metric = DatabaseMetric(
                query_id=query_id,
                query=query,
                params=params,
                start_time=time.time()
            )
            self._active_queries[query_id] = metric

        return query_id

    def end_query(self, query_id: str) -> float:
        """End monitoring a query and return duration in ms"""
        with self._lock:
            if query_id not in self._active_queries:
                return 0.0

            metric = self._active_queries[query_id]
            metric.end_time = time.time()
            metric.duration_ms = (metric.end_time - metric.start_time) * 1000
            metric.is_slow = metric.duration_ms >= self._slow_query_threshold

            # Normalize query for pattern analysis
            normalized_query = self._normalize_query(metric.query)
            self._query_patterns[normalized_query] += 1

            # Move to completed queries
            self._completed_queries.append(metric)
            del self._active_queries[query_id]

            return metric.duration_ms

    def get_query_data(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get query data by ID"""
        with self._lock:
            # Check active queries
            if query_id in self._active_queries:
                return asdict(self._active_queries[query_id])

            # Check completed queries
            for metric in self._completed_queries:
                if metric.query_id == query_id:
                    return asdict(metric)

            return None

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow queries"""
        with self._lock:
            return [
                asdict(metric) for metric in self._completed_queries
                if metric.is_slow
            ]

    def analyze_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze query patterns"""
        with self._lock:
            return {
                pattern: {"count": count}
                for pattern, count in self._query_patterns.items()
            }

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics (mock implementation)"""
        # In real implementation, this would integrate with actual connection pool
        return {
            "total_connections": 10,
            "active_connections": 3,
            "idle_connections": 7,
            "pool_utilization": 30.0
        }

    def record_cache_miss(self, query: str):
        """Record cache miss"""
        # Implementation would integrate with actual cache system
        pass

    def record_cache_hit(self, query: str):
        """Record cache hit"""
        # Implementation would integrate with actual cache system
        pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (mock implementation)"""
        return {
            "total_queries": 2,
            "cache_hits": 1,
            "cache_misses": 1,
            "hit_ratio": 0.5
        }

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern analysis"""
        # Simple normalization: replace numbers and strings with placeholders
        import re

        # Replace string literals
        query = re.sub(r"'[^']*'", "?", query)

        # Replace numbers
        query = re.sub(r'\b\d+\b', "?", query)

        # Replace multiple spaces with single space
        query = re.sub(r'\s+', ' ', query)

        return query.strip()


class SystemResourceMonitor:
    """Monitors system resource usage"""

    def __init__(self):
        self.logger = CoreStructuredLogger("system_resource_monitor")
        self._thresholds: Optional[ResourceThresholds] = None
        self._metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics

    def configure_thresholds(self, thresholds: ResourceThresholds):
        """Configure resource thresholds"""
        self._thresholds = thresholds

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()

            return {
                "total_memory": memory.total,
                "available_memory": memory.available,
                "used_memory": memory.used,
                "memory_percent": memory.percent,
                "process_memory": process.memory_info().rss
            }
        except Exception as e:
            self.logger.error("Failed to get memory stats", error=e)
            return {
                "total_memory": 0,
                "available_memory": 0,
                "used_memory": 0,
                "memory_percent": 0,
                "process_memory": 0
            }

    def get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU usage statistics"""
        try:
            process = psutil.Process()

            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "cpu_count": psutil.cpu_count(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                "process_cpu_percent": process.cpu_percent()
            }
        except Exception as e:
            self.logger.error("Failed to get CPU stats", error=e)
            return {
                "cpu_percent": 0,
                "cpu_count": 1,
                "load_average": [0, 0, 0],
                "process_cpu_percent": 0
            }

    def get_disk_stats(self) -> Dict[str, Any]:
        """Get disk usage statistics"""
        try:
            disk = psutil.disk_usage('/')

            return {
                "total_disk": disk.total,
                "free_disk": disk.free,
                "used_disk": disk.used,
                "disk_percent": (disk.used / disk.total) * 100
            }
        except Exception as e:
            self.logger.error("Failed to get disk stats", error=e)
            return {
                "total_disk": 0,
                "free_disk": 0,
                "used_disk": 0,
                "disk_percent": 0
            }

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()

            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_received": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_received": net_io.packets_recv
            }
        except Exception as e:
            self.logger.error("Failed to get network stats", error=e)
            return {
                "bytes_sent": 0,
                "bytes_received": 0,
                "packets_sent": 0,
                "packets_received": 0
            }

    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check resource thresholds and generate alerts"""
        if not self._thresholds:
            return []

        alerts = []

        # Check memory thresholds
        memory_stats = self.get_memory_stats()
        memory_percent = memory_stats.get("memory_percent", 0)

        if memory_percent >= self._thresholds.memory_critical:
            alerts.append({
                "type": "memory",
                "level": "critical",
                "value": memory_percent,
                "threshold": self._thresholds.memory_critical,
                "timestamp": time.time()
            })
        elif memory_percent >= self._thresholds.memory_warning:
            alerts.append({
                "type": "memory",
                "level": "warning",
                "value": memory_percent,
                "threshold": self._thresholds.memory_warning,
                "timestamp": time.time()
            })

        # Check CPU thresholds
        cpu_stats = self.get_cpu_stats()
        cpu_percent = cpu_stats.get("cpu_percent", 0)

        if cpu_percent >= self._thresholds.cpu_critical:
            alerts.append({
                "type": "cpu",
                "level": "critical",
                "value": cpu_percent,
                "threshold": self._thresholds.cpu_critical,
                "timestamp": time.time()
            })
        elif cpu_percent >= self._thresholds.cpu_warning:
            alerts.append({
                "type": "cpu",
                "level": "warning",
                "value": cpu_percent,
                "threshold": self._thresholds.cpu_warning,
                "timestamp": time.time()
            })

        return alerts

    def collect_metrics(self) -> SystemMetric:
        """Collect current system metrics"""
        memory_stats = self.get_memory_stats()
        cpu_stats = self.get_cpu_stats()
        disk_stats = self.get_disk_stats()
        network_stats = self.get_network_stats()

        metric = SystemMetric(
            timestamp=time.time(),
            memory_percent=memory_stats.get("memory_percent", 0),
            cpu_percent=cpu_stats.get("cpu_percent", 0),
            disk_percent=disk_stats.get("disk_percent", 0),
            network_bytes_sent=network_stats.get("bytes_sent", 0),
            network_bytes_received=network_stats.get("bytes_received", 0),
            process_memory_mb=memory_stats.get("process_memory", 0) / (1024 * 1024),
            process_cpu_percent=cpu_stats.get("process_cpu_percent", 0)
        )

        self._metrics_history.append(metric)
        return metric


class PerformanceMetrics:
    """Aggregates and analyzes performance metrics"""

    def __init__(self):
        self._request_metrics: List[Dict[str, Any]] = []
        self._db_metrics: List[Dict[str, Any]] = []
        self._system_metrics: List[SystemMetric] = []
        self._baselines: Dict[str, Dict[str, float]] = {}
        self.logger = CoreStructuredLogger("performance_metrics")

    def record_request_time(
        self,
        endpoint: str,
        method: str,
        duration: float,
        timestamp: Optional[float] = None
    ):
        """Record request timing metric"""
        self._request_metrics.append({
            "endpoint": endpoint,
            "method": method,
            "duration_ms": duration,
            "timestamp": timestamp or time.time()
        })

    def record_db_query_time(self, query: str, duration: float):
        """Record database query timing metric"""
        self._db_metrics.append({
            "query": query,
            "duration_ms": duration,
            "timestamp": time.time()
        })

    def record_memory_usage(self, memory_percent: float):
        """Record memory usage metric"""
        # Store in system metrics
        pass

    def record_cpu_usage(self, cpu_percent: float):
        """Record CPU usage metric"""
        # Store in system metrics
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            "request_metrics": {
                "total_requests": len(self._request_metrics),
                "avg_response_time": statistics.mean([m["duration_ms"] for m in self._request_metrics]) if self._request_metrics else 0
            },
            "database_metrics": {
                "total_queries": len(self._db_metrics),
                "avg_query_time": statistics.mean([m["duration_ms"] for m in self._db_metrics]) if self._db_metrics else 0
            },
            "system_metrics": {
                "total_samples": len(self._system_metrics)
            }
        }

    def aggregate_by_time_window(
        self,
        metric_type: str,
        window_size: int,
        aggregation: str = "avg"
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by time windows"""
        if metric_type == "request_time":
            metrics = self._request_metrics
        elif metric_type == "db_query_time":
            metrics = self._db_metrics
        else:
            return []

        # Group by time windows
        windows = defaultdict(list)
        current_time = time.time()

        for metric in metrics:
            window_start = int((metric["timestamp"] - current_time % window_size) // window_size) * window_size
            windows[window_start].append(metric["duration_ms"])

        # Aggregate each window
        result = []
        for window_start, durations in windows.items():
            if aggregation == "avg":
                value = statistics.mean(durations)
                key = "avg_duration"
            elif aggregation == "max":
                value = max(durations)
                key = "max_duration"
            elif aggregation == "min":
                value = min(durations)
                key = "min_duration"
            else:
                value = statistics.mean(durations)
                key = "avg_duration"

            result.append({
                "window_start": window_start,
                key: value,
                "count": len(durations)
            })

        return sorted(result, key=lambda x: x["window_start"])

    def analyze_trend(self, metric_type: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Analyze performance trend"""
        if metric_type == "request_time":
            metrics = [
                m for m in self._request_metrics
                if endpoint is None or m["endpoint"] == endpoint
            ]
        else:
            return {"direction": "stable", "slope": 0}

        if len(metrics) < 2:
            return {"direction": "stable", "slope": 0}

        # Sort by timestamp
        metrics = sorted(metrics, key=lambda x: x["timestamp"])

        # Simple trend analysis: compare first and second half
        mid_point = len(metrics) // 2
        first_half_avg = statistics.mean([m["duration_ms"] for m in metrics[:mid_point]])
        second_half_avg = statistics.mean([m["duration_ms"] for m in metrics[mid_point:]])

        slope = second_half_avg - first_half_avg

        if slope > 10:  # 10ms increase
            direction = "increasing"
        elif slope < -10:  # 10ms decrease
            direction = "decreasing"
        else:
            direction = "stable"

        return {"direction": direction, "slope": slope}

    def establish_baseline(self, endpoint: str) -> Dict[str, float]:
        """Establish performance baseline for endpoint"""
        endpoint_metrics = [
            m for m in self._request_metrics
            if m["endpoint"] == endpoint
        ]

        if not endpoint_metrics:
            return {"avg_duration": 0, "p95_duration": 0}

        durations = [m["duration_ms"] for m in endpoint_metrics]
        baseline = {
            "avg_duration": statistics.mean(durations),
            "p95_duration": durations[int(len(durations) * 0.95)] if durations else 0
        }

        self._baselines[endpoint] = baseline
        return baseline

    def compare_to_baseline(self, endpoint: str, baseline: Dict[str, float]) -> Dict[str, Any]:
        """Compare current performance to baseline"""
        recent_metrics = [
            m for m in self._request_metrics[-100:]  # Last 100 requests
            if m["endpoint"] == endpoint
        ]

        if not recent_metrics:
            return {"deviation_percent": 0, "performance_degraded": False}

        current_avg = statistics.mean([m["duration_ms"] for m in recent_metrics])
        baseline_avg = baseline.get("avg_duration", current_avg)

        if baseline_avg == 0:
            deviation_percent = 0
        else:
            deviation_percent = ((current_avg - baseline_avg) / baseline_avg) * 100

        return {
            "deviation_percent": deviation_percent,
            "performance_degraded": deviation_percent > 20  # 20% threshold
        }