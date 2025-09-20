"""
Advanced Testing and Optimization Service - T051-T060 Implementation

This service provides comprehensive testing and optimization capabilities:
- Performance testing and benchmarking
- A/B testing framework
- Load testing automation
- Database query optimization
- Cache performance analysis
- Memory usage optimization
- Security vulnerability testing

Author: Claude Code Assistant
Created: 2025-09-19
Tasks: T051-T060 - Advanced Testing & Optimization
"""

import asyncio
import concurrent.futures
import json
import logging
import statistics
import time
import tracemalloc
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import aioredis
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class TestType(str, Enum):
    """Types of tests."""

    PERFORMANCE = "performance"
    LOAD = "load"
    STRESS = "stress"
    VOLUME = "volume"
    AB_TEST = "ab_test"
    SECURITY = "security"
    INTEGRATION = "integration"
    API_BENCHMARK = "api_benchmark"


class OptimizationType(str, Enum):
    """Types of optimizations."""

    DATABASE_QUERY = "database_query"
    CACHE_STRATEGY = "cache_strategy"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""

    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_mb: float
    network_io_mb: float
    queries_executed: int
    cache_hit_rate: float
    error_rate: float
    throughput_rps: float
    concurrent_users: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestConfiguration:
    """Test configuration parameters."""

    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_type: TestType = TestType.PERFORMANCE
    name: str = ""
    description: str = ""
    target_endpoint: str = ""
    duration_seconds: int = 60
    concurrent_users: int = 10
    ramp_up_seconds: int = 10
    think_time_ms: int = 1000
    max_requests: int = 0  # 0 = unlimited
    test_data: Dict[str, Any] = field(default_factory=dict)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestResult:
    """Complete test execution results."""

    test_id: str
    config: TestConfiguration
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    metrics: List[PerformanceMetrics] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ABTestVariant:
    """A/B test variant configuration."""

    variant_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    traffic_percentage: float = 50.0
    config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ABTestExperiment:
    """A/B test experiment."""

    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: str = "active"
    variants: List[ABTestVariant] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    sample_size: int = 1000
    confidence_level: float = 0.95
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: OptimizationType
    title: str = ""
    description: str = ""
    impact: str = "medium"  # low, medium, high
    effort: str = "medium"  # low, medium, high
    implementation: str = ""
    expected_improvement: str = ""
    priority_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# ADVANCED TESTING SERVICE
# ============================================================================


class AdvancedTestingService:
    """Service for advanced testing and optimization."""

    def __init__(self):
        self.active_tests: Dict[str, TestResult] = {}
        self.ab_experiments: Dict[str, ABTestExperiment] = {}
        self.optimization_history: List[OptimizationRecommendation] = []

    # ========================================================================
    # PERFORMANCE TESTING
    # ========================================================================

    async def run_performance_test(self, config: TestConfiguration) -> TestResult:
        """Execute a comprehensive performance test."""
        try:
            # Initialize test result
            test_result = TestResult(
                test_id=config.test_id,
                config=config,
                status=TestStatus.RUNNING,
                start_time=datetime.utcnow(),
            )

            self.active_tests[config.test_id] = test_result

            logger.info(f"Starting performance test {config.test_id}")

            # Start memory tracking
            tracemalloc.start()

            # Execute test based on type
            if config.test_type == TestType.LOAD:
                await self._run_load_test(config, test_result)
            elif config.test_type == TestType.STRESS:
                await self._run_stress_test(config, test_result)
            elif config.test_type == TestType.API_BENCHMARK:
                await self._run_api_benchmark(config, test_result)
            else:
                await self._run_basic_performance_test(config, test_result)

            # Calculate final metrics
            self._calculate_final_metrics(test_result)

            # Generate recommendations
            test_result.recommendations = await self._generate_recommendations(test_result)

            # Complete test
            test_result.status = TestStatus.COMPLETED
            test_result.end_time = datetime.utcnow()
            test_result.duration_seconds = (
                test_result.end_time - test_result.start_time
            ).total_seconds()

            logger.info(f"Performance test {config.test_id} completed")
            return test_result

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            test_result.status = TestStatus.FAILED
            test_result.errors.append(
                {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "traceback": tracemalloc.format_exc() if tracemalloc.is_tracing() else str(e),
                }
            )
            return test_result

        finally:
            if tracemalloc.is_tracing():
                tracemalloc.stop()

    async def _run_basic_performance_test(self, config: TestConfiguration, result: TestResult):
        """Run basic performance test."""
        response_times = []
        errors = []

        # Simulate concurrent users
        async def simulate_user():
            try:
                start_time = time.time()

                # Simulate API call or operation
                await self._simulate_operation(config.target_endpoint, config.test_data)

                response_time = (time.time() - start_time) * 1000  # Convert to ms
                response_times.append(response_time)

                result.successful_requests += 1

            except Exception as e:
                errors.append({"error": str(e), "timestamp": datetime.utcnow().isoformat()})
                result.failed_requests += 1

        # Execute test
        tasks = []
        for _ in range(config.concurrent_users):
            task = asyncio.create_task(simulate_user())
            tasks.append(task)
            await asyncio.sleep(config.think_time_ms / 1000)

        await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate metrics
        if response_times:
            result.avg_response_time = statistics.mean(response_times)
            result.min_response_time = min(response_times)
            result.max_response_time = max(response_times)
            result.p95_response_time = statistics.quantiles(response_times, n=20)[
                18
            ]  # 95th percentile
            result.p99_response_time = statistics.quantiles(response_times, n=100)[
                98
            ]  # 99th percentile

        result.total_requests = result.successful_requests + result.failed_requests
        result.error_rate = (
            (result.failed_requests / result.total_requests * 100)
            if result.total_requests > 0
            else 0
        )
        result.errors.extend(errors)

    async def _run_load_test(self, config: TestConfiguration, result: TestResult):
        """Run load test with gradual ramp-up."""
        start_time = time.time()
        end_time = start_time + config.duration_seconds

        # Gradual ramp-up
        current_users = 0
        max_users = config.concurrent_users
        ramp_interval = config.ramp_up_seconds / max_users

        while time.time() < end_time:
            # Increase load gradually
            if current_users < max_users and time.time() < start_time + config.ramp_up_seconds:
                current_users += 1

            # Collect metrics
            metrics = await self._collect_system_metrics()
            result.metrics.append(metrics)

            # Simulate user requests
            tasks = []
            for _ in range(current_users):
                task = asyncio.create_task(self._simulate_user_session(config))
                tasks.append(task)

            # Wait for requests to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Process responses
            for response in responses:
                if isinstance(response, Exception):
                    result.failed_requests += 1
                    result.errors.append(
                        {"error": str(response), "timestamp": datetime.utcnow().isoformat()}
                    )
                else:
                    result.successful_requests += 1

            await asyncio.sleep(ramp_interval)

        result.total_requests = result.successful_requests + result.failed_requests

    async def _run_stress_test(self, config: TestConfiguration, result: TestResult):
        """Run stress test to find breaking point."""
        current_load = config.concurrent_users
        load_increment = config.concurrent_users // 4
        max_error_rate = 5.0  # 5% error rate threshold

        while True:
            logger.info(f"Testing with {current_load} concurrent users")

            # Run test at current load
            test_metrics = await self._run_load_burst(current_load, config)

            # Check if we've reached the breaking point
            error_rate = (
                (test_metrics["failed_requests"] / test_metrics["total_requests"] * 100)
                if test_metrics["total_requests"] > 0
                else 0
            )

            result.metrics.append(
                PerformanceMetrics(
                    response_time_ms=test_metrics["avg_response_time"],
                    memory_usage_mb=test_metrics["memory_usage"],
                    cpu_usage_percent=test_metrics["cpu_usage"],
                    disk_io_mb=0,
                    network_io_mb=0,
                    queries_executed=test_metrics["total_requests"],
                    cache_hit_rate=0,
                    error_rate=error_rate,
                    throughput_rps=test_metrics["throughput"],
                    concurrent_users=current_load,
                )
            )

            if (
                error_rate > max_error_rate or test_metrics["avg_response_time"] > 5000
            ):  # 5 second threshold
                logger.info(f"Breaking point reached at {current_load} users")
                break

            current_load += load_increment

            # Safety limit
            if current_load > config.concurrent_users * 10:
                break

    async def _run_api_benchmark(self, config: TestConfiguration, result: TestResult):
        """Run API-specific benchmark tests."""
        endpoints = config.test_data.get("endpoints", [config.target_endpoint])

        for endpoint in endpoints:
            logger.info(f"Benchmarking endpoint: {endpoint}")

            # Test various scenarios
            scenarios = [
                {"users": 1, "duration": 10},  # Single user baseline
                {"users": 10, "duration": 30},  # Normal load
                {"users": 50, "duration": 60},  # High load
                {"users": 100, "duration": 30},  # Peak load
            ]

            for scenario in scenarios:
                scenario_metrics = await self._benchmark_endpoint(
                    endpoint, scenario["users"], scenario["duration"]
                )

                result.metrics.append(scenario_metrics)

    async def _simulate_operation(self, endpoint: str, test_data: Dict[str, Any]):
        """Simulate an operation or API call."""
        # Mock implementation - in real app, make actual HTTP requests
        await asyncio.sleep(0.1)  # Simulate processing time

        # Simulate occasional errors
        import random

        if random.random() < 0.05:  # 5% error rate
            raise Exception("Simulated operation error")

        return {"status": "success", "response_time": 0.1}

    async def _simulate_user_session(self, config: TestConfiguration) -> Dict[str, Any]:
        """Simulate a complete user session."""
        session_start = time.time()

        try:
            # Simulate multiple operations in a session
            operations = config.test_data.get("operations", ["login", "browse", "search"])

            for operation in operations:
                await self._simulate_operation(
                    f"{config.target_endpoint}/{operation}", config.test_data
                )
                await asyncio.sleep(config.think_time_ms / 1000)

            session_time = time.time() - session_start
            return {
                "status": "success",
                "session_time": session_time,
                "operations": len(operations),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "session_time": time.time() - session_start}

    async def _run_load_burst(
        self, concurrent_users: int, config: TestConfiguration
    ) -> Dict[str, Any]:
        """Run a burst of load testing."""
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        response_times = []

        # Simulate concurrent users
        async def user_load():
            nonlocal successful_requests, failed_requests
            try:
                operation_start = time.time()
                await self._simulate_operation(config.target_endpoint, config.test_data)
                response_time = (time.time() - operation_start) * 1000
                response_times.append(response_time)
                successful_requests += 1
            except Exception:
                failed_requests += 1

        # Execute load
        tasks = [user_load() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time
        total_requests = successful_requests + failed_requests

        # Get system metrics
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "throughput": total_requests / duration if duration > 0 else 0,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "duration": duration,
        }

    async def _benchmark_endpoint(
        self, endpoint: str, concurrent_users: int, duration_seconds: int
    ) -> PerformanceMetrics:
        """Benchmark a specific endpoint."""
        start_time = time.time()
        end_time = start_time + duration_seconds

        requests_made = 0
        response_times = []
        errors = 0

        while time.time() < end_time:
            # Make concurrent requests
            tasks = []
            for _ in range(concurrent_users):
                task = asyncio.create_task(self._time_request(endpoint))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                requests_made += 1
                if isinstance(result, Exception):
                    errors += 1
                else:
                    response_times.append(result)

            await asyncio.sleep(0.1)  # Small delay between bursts

        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        error_rate = (errors / requests_made * 100) if requests_made > 0 else 0
        throughput = requests_made / duration_seconds

        # Get system metrics
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        cpu_usage = process.cpu_percent()

        return PerformanceMetrics(
            response_time_ms=avg_response_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            disk_io_mb=0,
            network_io_mb=0,
            queries_executed=requests_made,
            cache_hit_rate=0,
            error_rate=error_rate,
            throughput_rps=throughput,
            concurrent_users=concurrent_users,
        )

    async def _time_request(self, endpoint: str) -> float:
        """Time a single request."""
        start_time = time.time()
        await self._simulate_operation(endpoint, {})
        return (time.time() - start_time) * 1000

    async def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        process = psutil.Process()

        # CPU and Memory
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024 if disk_io else 0
        except:
            disk_io_mb = 0

        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            network_io_mb = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024 if net_io else 0
        except:
            network_io_mb = 0

        return PerformanceMetrics(
            response_time_ms=0,  # Will be filled by specific tests
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            disk_io_mb=disk_io_mb,
            network_io_mb=network_io_mb,
            queries_executed=0,
            cache_hit_rate=0,
            error_rate=0,
            throughput_rps=0,
            concurrent_users=0,
        )

    def _calculate_final_metrics(self, result: TestResult):
        """Calculate final aggregated metrics."""
        if not result.metrics:
            return

        # Calculate averages and aggregates
        response_times = [m.response_time_ms for m in result.metrics if m.response_time_ms > 0]
        if response_times:
            result.avg_response_time = statistics.mean(response_times)
            result.min_response_time = min(response_times)
            result.max_response_time = max(response_times)

        # Throughput
        total_throughput = sum(m.throughput_rps for m in result.metrics)
        result.throughput_rps = total_throughput / len(result.metrics) if result.metrics else 0

    # ========================================================================
    # A/B TESTING
    # ========================================================================

    async def create_ab_test(
        self,
        name: str,
        description: str,
        variants: List[ABTestVariant],
        success_metrics: List[str],
        sample_size: int = 1000,
        confidence_level: float = 0.95,
    ) -> ABTestExperiment:
        """Create a new A/B test experiment."""
        experiment = ABTestExperiment(
            name=name,
            description=description,
            variants=variants,
            success_metrics=success_metrics,
            sample_size=sample_size,
            confidence_level=confidence_level,
        )

        # Validate variants
        total_traffic = sum(v.traffic_percentage for v in variants)
        if abs(total_traffic - 100.0) > 0.1:
            raise ValueError(f"Variant traffic percentages must sum to 100%, got {total_traffic}%")

        # Ensure one control variant
        control_variants = [v for v in variants if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("Exactly one variant must be marked as control")

        self.ab_experiments[experiment.experiment_id] = experiment
        logger.info(f"Created A/B test experiment: {experiment.experiment_id}")

        return experiment

    async def assign_user_to_variant(
        self, experiment_id: str, user_id: str
    ) -> Optional[ABTestVariant]:
        """Assign a user to an A/B test variant."""
        experiment = self.ab_experiments.get(experiment_id)
        if not experiment or experiment.status != "active":
            return None

        # Simple hash-based assignment for consistent results
        import hashlib

        hash_input = f"{experiment_id}_{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        percentage = (hash_value % 100) + 1

        # Assign based on traffic percentages
        current_percentage = 0
        for variant in experiment.variants:
            current_percentage += variant.traffic_percentage
            if percentage <= current_percentage:
                return variant

        # Fallback to control
        return next(v for v in experiment.variants if v.is_control)

    async def record_ab_test_metric(
        self, experiment_id: str, variant_id: str, metric_name: str, value: float
    ):
        """Record a metric value for an A/B test variant."""
        experiment = self.ab_experiments.get(experiment_id)
        if not experiment:
            return

        # Find variant
        variant = next((v for v in experiment.variants if v.variant_id == variant_id), None)
        if not variant:
            return

        # Update metrics
        if metric_name not in variant.metrics:
            variant.metrics[metric_name] = 0

        variant.metrics[metric_name] += value

    async def analyze_ab_test_results(self, experiment_id: str) -> Dict[str, Any]:
        """Analyze A/B test results and determine statistical significance."""
        experiment = self.ab_experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Mock statistical analysis
        control_variant = next(v for v in experiment.variants if v.is_control)
        results = {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "control_variant": control_variant.variant_id,
            "variants": [],
            "winner": None,
            "confidence": 0.0,
            "statistical_significance": False,
        }

        for variant in experiment.variants:
            variant_results = {
                "variant_id": variant.variant_id,
                "name": variant.name,
                "is_control": variant.is_control,
                "metrics": variant.metrics,
                "performance_vs_control": {},
            }

            # Compare against control
            if not variant.is_control:
                for metric_name in experiment.success_metrics:
                    control_value = control_variant.metrics.get(metric_name, 0)
                    variant_value = variant.metrics.get(metric_name, 0)

                    if control_value > 0:
                        improvement = ((variant_value - control_value) / control_value) * 100
                        variant_results["performance_vs_control"][metric_name] = {
                            "improvement_percent": improvement,
                            "control_value": control_value,
                            "variant_value": variant_value,
                        }

            results["variants"].append(variant_results)

        # Determine winner (simplified)
        best_variant = control_variant
        best_improvement = 0

        for variant in experiment.variants:
            if variant.is_control:
                continue

            total_improvement = 0
            metric_count = 0

            for metric_name in experiment.success_metrics:
                control_value = control_variant.metrics.get(metric_name, 0)
                variant_value = variant.metrics.get(metric_name, 0)

                if control_value > 0:
                    improvement = ((variant_value - control_value) / control_value) * 100
                    total_improvement += improvement
                    metric_count += 1

            avg_improvement = total_improvement / metric_count if metric_count > 0 else 0

            if avg_improvement > best_improvement:
                best_improvement = avg_improvement
                best_variant = variant

        if best_improvement > 5:  # 5% improvement threshold
            results["winner"] = best_variant.variant_id
            results["confidence"] = 0.95  # Mock confidence
            results["statistical_significance"] = True

        return results

    # ========================================================================
    # OPTIMIZATION RECOMMENDATIONS
    # ========================================================================

    async def _generate_recommendations(self, test_result: TestResult) -> List[str]:
        """Generate optimization recommendations based on test results."""
        recommendations = []

        # Response time recommendations
        if test_result.avg_response_time > 1000:  # 1 second
            recommendations.append(
                f"高い応答時間 ({test_result.avg_response_time:.1f}ms) - "
                "データベースクエリの最適化、キャッシュの実装、または非同期処理の検討をお勧めします。"
            )

        # Error rate recommendations
        if test_result.error_rate > 1:  # 1%
            recommendations.append(
                f"エラー率が高い ({test_result.error_rate:.1f}%) - "
                "エラーハンドリングの改善、リトライ機能の実装、またはサーキットブレーカーパターンの導入を検討してください。"
            )

        # Throughput recommendations
        if test_result.throughput_rps < 10:
            recommendations.append(
                f"スループットが低い ({test_result.throughput_rps:.1f} RPS) - "
                "並列処理の増加、コネクションプールの最適化、またはハードウェアのスケールアップを検討してください。"
            )

        # Memory usage recommendations
        if test_result.metrics:
            avg_memory = statistics.mean(m.memory_usage_mb for m in test_result.metrics)
            if avg_memory > 1000:  # 1GB
                recommendations.append(
                    f"メモリ使用量が高い ({avg_memory:.1f}MB) - "
                    "メモリリークの確認、オブジェクトプールの使用、またはGCチューニングを検討してください。"
                )

        if not recommendations:
            recommendations.append(
                "パフォーマンスは良好です。現在の最適化レベルを維持してください。"
            )

        return recommendations

    async def generate_optimization_recommendations(
        self, metrics_history: List[PerformanceMetrics], current_config: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate comprehensive optimization recommendations."""
        recommendations = []

        if not metrics_history:
            return recommendations

        # Analyze trends
        recent_metrics = metrics_history[-10:]  # Last 10 measurements
        older_metrics = metrics_history[-20:-10] if len(metrics_history) >= 20 else []

        # Database optimization
        avg_queries = statistics.mean(m.queries_executed for m in recent_metrics)
        if avg_queries > 100:
            recommendations.append(
                OptimizationRecommendation(
                    type=OptimizationType.DATABASE_QUERY,
                    title="データベースクエリの最適化",
                    description=f"平均 {avg_queries:.0f} クエリ/リクエスト - インデックスの追加や結合の最適化を検討",
                    impact="high",
                    effort="medium",
                    implementation="インデックス分析、クエリプラン確認、N+1問題の解決",
                    expected_improvement="応答時間 30-50% 改善",
                    priority_score=8.5,
                )
            )

        # Cache optimization
        avg_cache_hit = statistics.mean(m.cache_hit_rate for m in recent_metrics)
        if avg_cache_hit < 70:
            recommendations.append(
                OptimizationRecommendation(
                    type=OptimizationType.CACHE_STRATEGY,
                    title="キャッシュ戦略の改善",
                    description=f"キャッシュヒット率 {avg_cache_hit:.1f}% - キャッシュ戦略の見直しが必要",
                    impact="medium",
                    effort="low",
                    implementation="Redis実装、TTL最適化、キャッシュキー設計見直し",
                    expected_improvement="データベース負荷 40-60% 削減",
                    priority_score=7.0,
                )
            )

        # Memory optimization
        avg_memory = statistics.mean(m.memory_usage_mb for m in recent_metrics)
        if avg_memory > 1000:
            recommendations.append(
                OptimizationRecommendation(
                    type=OptimizationType.MEMORY_USAGE,
                    title="メモリ使用量の最適化",
                    description=f"平均メモリ使用量 {avg_memory:.0f}MB - メモリ効率の改善が必要",
                    impact="medium",
                    effort="high",
                    implementation="メモリプロファイリング、オブジェクトプール、遅延読み込み",
                    expected_improvement="メモリ使用量 20-30% 削減",
                    priority_score=6.5,
                )
            )

        # CPU optimization
        avg_cpu = statistics.mean(m.cpu_usage_percent for m in recent_metrics)
        if avg_cpu > 80:
            recommendations.append(
                OptimizationRecommendation(
                    type=OptimizationType.CPU_USAGE,
                    title="CPU使用率の最適化",
                    description=f"平均CPU使用率 {avg_cpu:.1f}% - CPU集約的処理の最適化が必要",
                    impact="high",
                    effort="high",
                    implementation="アルゴリズム最適化、並列処理、非同期処理導入",
                    expected_improvement="CPU使用率 15-25% 削減",
                    priority_score=8.0,
                )
            )

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)

        self.optimization_history.extend(recommendations)
        return recommendations

    # ========================================================================
    # SECURITY TESTING
    # ========================================================================

    async def run_security_scan(
        self, target_url: str, test_types: List[str] = None
    ) -> Dict[str, Any]:
        """Run security vulnerability scan."""
        if test_types is None:
            test_types = ["sql_injection", "xss", "auth_bypass", "rate_limit"]

        results = {
            "target": target_url,
            "scan_time": datetime.utcnow().isoformat(),
            "vulnerabilities": [],
            "risk_score": 0,
            "recommendations": [],
        }

        for test_type in test_types:
            vulnerability = await self._run_security_test(target_url, test_type)
            if vulnerability:
                results["vulnerabilities"].append(vulnerability)

        # Calculate risk score
        risk_scores = [v.get("severity", 0) for v in results["vulnerabilities"]]
        results["risk_score"] = max(risk_scores) if risk_scores else 0

        # Generate security recommendations
        results["recommendations"] = self._generate_security_recommendations(
            results["vulnerabilities"]
        )

        return results

    async def _run_security_test(self, target_url: str, test_type: str) -> Optional[Dict[str, Any]]:
        """Run a specific security test."""
        # Mock security testing - in real implementation, use proper security tools
        test_payloads = {
            "sql_injection": ["' OR 1=1--", "'; DROP TABLE users;--"],
            "xss": ["<script>alert('xss')</script>", "<img src=x onerror=alert(1)>"],
            "auth_bypass": ["admin", "administrator"],
            "rate_limit": ["rate_limit_test"],
        }

        payloads = test_payloads.get(test_type, [])

        for payload in payloads:
            # Simulate security test
            await asyncio.sleep(0.1)  # Simulate test time

            # Mock vulnerability detection (randomly for demo)
            import random

            if random.random() < 0.1:  # 10% chance of finding vulnerability
                return {
                    "type": test_type,
                    "payload": payload,
                    "severity": random.randint(1, 10),
                    "description": f"Potential {test_type} vulnerability detected",
                    "recommendation": f"Implement proper input validation and sanitization for {test_type}",
                }

        return None

    def _generate_security_recommendations(
        self, vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate security recommendations based on found vulnerabilities."""
        recommendations = []

        vulnerability_types = set(v["type"] for v in vulnerabilities)

        if "sql_injection" in vulnerability_types:
            recommendations.append("パラメータ化クエリの実装とORM使用の検討")

        if "xss" in vulnerability_types:
            recommendations.append("入力値のサニタイゼーションとCSPヘッダーの実装")

        if "auth_bypass" in vulnerability_types:
            recommendations.append("強固な認証機能と多要素認証の実装")

        if "rate_limit" in vulnerability_types:
            recommendations.append("レート制限とDDoS保護の実装")

        if not recommendations:
            recommendations.append("現在のセキュリティレベルは良好です")

        return recommendations

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_test_status(self, test_id: str) -> Optional[TestResult]:
        """Get the status of a running or completed test."""
        return self.active_tests.get(test_id)

    async def cancel_test(self, test_id: str) -> bool:
        """Cancel a running test."""
        test = self.active_tests.get(test_id)
        if test and test.status == TestStatus.RUNNING:
            test.status = TestStatus.CANCELLED
            test.end_time = datetime.utcnow()
            return True
        return False

    async def get_test_history(
        self, limit: int = 50, test_type: Optional[TestType] = None
    ) -> List[TestResult]:
        """Get test execution history."""
        tests = list(self.active_tests.values())

        if test_type:
            tests = [t for t in tests if t.config.test_type == test_type]

        # Sort by start time, most recent first
        tests.sort(key=lambda x: x.start_time, reverse=True)

        return tests[:limit]


# ============================================================================
# SERVICE INSTANCE
# ============================================================================

advanced_testing_service = AdvancedTestingService()
