#!/usr/bin/env python3
"""
T013: Contract Test for GET /monitoring/metrics (RED Phase)

Tests API contract for monitoring metrics endpoint including:
- Request validation
- Response schema
- Metric types
- Time ranges
"""

import pytest
from httpx import AsyncClient
from app.main import app
import json


class TestMonitoringMetricsContract:
    """Contract tests for GET /monitoring/metrics endpoint"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, client: AsyncClient):
        """Test successful metrics retrieval"""
        response = await client.get("/monitoring/metrics")

        assert response.status_code == 200
        data = response.json()

        # Verify response schema
        assert "system" in data
        assert "application" in data
        assert "database" in data
        assert "timestamp" in data

        # System metrics
        system = data["system"]
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "disk_usage" in system
        assert 0 <= system["cpu_percent"] <= 100
        assert 0 <= system["memory_percent"] <= 100

        # Application metrics
        app_metrics = data["application"]
        assert "request_count" in app_metrics
        assert "error_count" in app_metrics
        assert "avg_response_time" in app_metrics
        assert "active_users" in app_metrics

        # Database metrics
        db = data["database"]
        assert "connection_count" in db
        assert "query_count" in db
        assert "avg_query_time" in db
        assert "pool_size" in db

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range(self, client: AsyncClient):
        """Test metrics with time range filter"""
        params = {
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-02T00:00:00Z",
            "interval": "1h"
        }

        response = await client.get("/monitoring/metrics", params=params)

        assert response.status_code == 200
        data = response.json()

        # Should return time series data
        assert "time_series" in data
        assert isinstance(data["time_series"], list)

        if len(data["time_series"]) > 0:
            point = data["time_series"][0]
            assert "timestamp" in point
            assert "metrics" in point

    @pytest.mark.asyncio
    async def test_get_metrics_by_type(self, client: AsyncClient):
        """Test metrics filtered by type"""
        # Test system metrics only
        response = await client.get("/monitoring/metrics", params={"type": "system"})
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "application" not in data or data["application"] == {}

        # Test application metrics only
        response = await client.get("/monitoring/metrics", params={"type": "application"})
        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        assert "system" not in data or data["system"] == {}

        # Test database metrics only
        response = await client.get("/monitoring/metrics", params={"type": "database"})
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "system" not in data or data["system"] == {}

    @pytest.mark.asyncio
    async def test_get_metrics_business_metrics(self, client: AsyncClient):
        """Test business metrics"""
        response = await client.get("/monitoring/metrics", params={"type": "business"})

        assert response.status_code == 200
        data = response.json()

        business = data.get("business", {})
        # Business metrics should include
        assert "total_users" in business or "users" in data
        assert "total_jobs" in business or "jobs" in data
        assert "matches_generated" in business or "matches" in data
        assert "emails_sent" in business or "emails" in data
        assert "avg_match_score" in business or "scores" in data

    @pytest.mark.asyncio
    async def test_get_metrics_aggregation(self, client: AsyncClient):
        """Test metrics aggregation"""
        params = {
            "aggregation": "avg",
            "group_by": "hour",
            "metric": "response_time"
        }

        response = await client.get("/monitoring/metrics", params=params)

        assert response.status_code == 200
        data = response.json()

        if "aggregated" in data:
            assert isinstance(data["aggregated"], list)
            if len(data["aggregated"]) > 0:
                point = data["aggregated"][0]
                assert "time_bucket" in point
                assert "value" in point

    @pytest.mark.asyncio
    async def test_get_metrics_alerts(self, client: AsyncClient):
        """Test metrics with alert thresholds"""
        response = await client.get("/monitoring/metrics", params={"include_alerts": "true"})

        assert response.status_code == 200
        data = response.json()

        if "alerts" in data:
            assert isinstance(data["alerts"], list)
            for alert in data["alerts"]:
                assert "metric" in alert
                assert "threshold" in alert
                assert "current_value" in alert
                assert "status" in alert
                assert alert["status"] in ["ok", "warning", "critical"]

    @pytest.mark.asyncio
    async def test_get_metrics_invalid_time_range(self, client: AsyncClient):
        """Test invalid time range"""
        params = {
            "start_time": "2025-01-02T00:00:00Z",
            "end_time": "2025-01-01T00:00:00Z"  # End before start
        }

        response = await client.get("/monitoring/metrics", params=params)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "time" in data["detail"].lower() or "range" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_metrics_invalid_type(self, client: AsyncClient):
        """Test invalid metric type"""
        response = await client.get("/monitoring/metrics", params={"type": "invalid_type"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_metrics_health_check(self, client: AsyncClient):
        """Test health check metrics"""
        response = await client.get("/monitoring/metrics/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "checks" in data

        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks or "cache" in checks
        assert "disk_space" in checks
        assert "memory" in checks

        for check_name, check_data in checks.items():
            assert "status" in check_data
            assert "message" in check_data or "details" in check_data

    @pytest.mark.asyncio
    async def test_get_metrics_export_format(self, client: AsyncClient):
        """Test metrics export in different formats"""
        # Test Prometheus format
        response = await client.get("/monitoring/metrics", params={"format": "prometheus"})

        if response.status_code == 200:
            # Prometheus format should be text/plain
            assert "text/plain" in response.headers.get("content-type", "")
            content = response.text
            assert "# HELP" in content or "# TYPE" in content

        # Test JSON format (default)
        response = await client.get("/monitoring/metrics", params={"format": "json"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_metrics_rate_limiting(self, client: AsyncClient):
        """Test rate limiting on metrics endpoint"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await client.get("/monitoring/metrics")
            responses.append(response.status_code)

        # Should not rate limit monitoring endpoint (or have high limit)
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 8  # Allow at least 8 successful requests

    @pytest.mark.asyncio
    async def test_get_metrics_response_time(self, client: AsyncClient):
        """Test response time SLA"""
        import time

        start = time.time()
        response = await client.get("/monitoring/metrics")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Metrics should be fast (under 1 second)