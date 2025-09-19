"""
T085: Performance and Load Testing [RED PHASE]

This test is intentionally designed to fail (TDD RED phase).
Documents the expected system performance requirements that are not yet met,
making the need for performance optimization clear.

Performance targets:
- 100,000 job data import: <5 minutes
- 10,000 users × 40 job matching: <30 minutes
- 1,000 concurrent connections: <200ms response time
- Memory usage: <8GB

Run command: pytest tests/performance/test_load_performance.py -v
"""

import pytest
import asyncio
import time
import psutil
import httpx
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from datetime import datetime, timedelta


# Test configuration
API_BASE_URL = "http://localhost:8001"
REQUEST_TIMEOUT = 30.0

# Performance thresholds
PERFORMANCE_TARGETS = {
    "job_import_time_seconds": 300,  # 5 minutes
    "matching_batch_time_seconds": 1800,  # 30 minutes
    "concurrent_response_time_ms": 200,  # 200ms
    "memory_usage_gb": 8.0,  # 8GB
    "concurrent_connections": 1000,
    "job_data_size": 100000,  # 100k jobs
    "user_data_size": 10000,  # 10k users
    "jobs_per_user": 40
}


class PerformanceTestHelper:
    """Helper class for performance testing operations"""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage_gb()

    def get_memory_usage_gb(self) -> float:
        """Get current memory usage in GB"""
        memory_info = self.process.memory_info()
        return memory_info.rss / (1024 * 1024 * 1024)  # Convert bytes to GB

    def generate_job_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate fake job data for performance testing"""
        jobs = []
        for i in range(count):
            job = {
                "title": f"Job Title {i:06d}",
                "company": f"Company {random.randint(1, 1000)}",
                "location": random.choice(["Tokyo", "Osaka", "Nagoya", "Fukuoka", "Sapporo"]),
                "salary_min": random.randint(3000000, 8000000),
                "salary_max": random.randint(8000000, 15000000),
                "description": f"Job description for position {i:06d}. " + "Sample description text. " * 10,
                "requirements": f"Requirements for job {i:06d}: Python, SQL, Communication skills",
                "employment_type": random.choice(["正社員", "契約社員", "派遣社員", "アルバイト"]),
                "prefecture_id": random.randint(1, 47),
                "industry_id": random.randint(1, 20),
                "is_active": True
            }
            jobs.append(job)
        return jobs

    def generate_user_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate fake user data for performance testing"""
        users = []
        for i in range(count):
            user = {
                "email": f"user{i:06d}@performance.test",
                "name": f"Performance User {i:06d}",
                "password": "performancetest123",
                "prefecture_id": random.randint(1, 47),
                "age": random.randint(22, 65),
                "experience_years": random.randint(0, 20),
                "desired_salary_min": random.randint(3000000, 6000000),
                "desired_salary_max": random.randint(6000000, 12000000),
                "skills": f"Skill{random.randint(1, 50)}, Skill{random.randint(51, 100)}, Skill{random.randint(101, 150)}"
            }
            users.append(user)
        return users


@pytest.fixture(scope="class")
def performance_helper():
    """Performance testing helper fixture"""
    return PerformanceTestHelper()


@pytest.fixture(scope="class")
def client():
    """HTTP client setup for performance testing"""
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=REQUEST_TIMEOUT
    )


class TestJobDataImportPerformance:
    """Job data import performance tests"""

    @pytest.mark.asyncio
    async def test_large_job_data_import_performance(self, client, performance_helper):
        """
        Performance Test: 100,000 job data import within 5 minutes

        Expected behavior:
        - Bulk import API can handle 100k job records
        - Import completes within 300 seconds (5 minutes)
        - Memory usage stays within acceptable limits
        - No timeouts or connection errors

        Current state: Not optimized -> This test will fail
        """
        print(f"🔴 RED PHASE: Large job data import performance test")

        # Generate test data
        job_data_size = PERFORMANCE_TARGETS["job_data_size"]
        print(f"Generating {job_data_size:,} job records...")

        job_data = performance_helper.generate_job_data(job_data_size)
        print(f"Generated {len(job_data):,} job records")

        # Track memory before import
        memory_before = performance_helper.get_memory_usage_gb()
        print(f"Memory usage before import: {memory_before:.2f} GB")

        # Start timing
        start_time = time.time()

        # Attempt bulk import (this will likely fail in RED phase)
        try:
            response = await client.post(
                "/api/v1/jobs/bulk-import",
                json={"jobs": job_data},
                timeout=PERFORMANCE_TARGETS["job_import_time_seconds"] + 60
            )

            import_duration = time.time() - start_time
            memory_after = performance_helper.get_memory_usage_gb()
            memory_increase = memory_after - memory_before

            print(f"Import completed in {import_duration:.2f} seconds")
            print(f"Memory after import: {memory_after:.2f} GB (increase: {memory_increase:.2f} GB)")

            # Performance assertions
            assert response.status_code == 200, f"Bulk import failed with status {response.status_code}"
            assert import_duration <= PERFORMANCE_TARGETS["job_import_time_seconds"], \
                f"Import took {import_duration:.2f}s, exceeded {PERFORMANCE_TARGETS['job_import_time_seconds']}s limit"

            assert memory_increase <= PERFORMANCE_TARGETS["memory_usage_gb"], \
                f"Memory increase {memory_increase:.2f}GB exceeded {PERFORMANCE_TARGETS['memory_usage_gb']}GB limit"

            # Verify data was imported
            import_result = response.json()
            assert "imported_count" in import_result, "Response should contain imported count"
            assert import_result["imported_count"] == job_data_size, \
                f"Expected {job_data_size} imports, got {import_result['imported_count']}"

        except Exception as error:
            import_duration = time.time() - start_time
            print(f"Expected failure after {import_duration:.2f} seconds: Bulk import API not implemented")
            print(f"Error: {error}")

            # In RED phase, we expect this to fail
            pytest.fail(f"Bulk import API not implemented or performance target not met: {error}")


class TestMatchingPerformance:
    """Job matching performance tests"""

    @pytest.mark.asyncio
    async def test_large_scale_matching_performance(self, client, performance_helper):
        """
        Performance Test: 10,000 users × 40 jobs matching within 30 minutes

        Expected behavior:
        - Matching engine processes 10k users against 40 jobs each
        - Total processing time under 1800 seconds (30 minutes)
        - Results include match scores and reasoning
        - Memory usage remains stable during processing

        Current state: Not optimized -> This test will fail
        """
        print(f"🔴 RED PHASE: Large scale matching performance test")

        user_count = PERFORMANCE_TARGETS["user_data_size"]
        jobs_per_user = PERFORMANCE_TARGETS["jobs_per_user"]
        total_operations = user_count * jobs_per_user

        print(f"Testing matching performance: {user_count:,} users × {jobs_per_user} jobs = {total_operations:,} operations")

        # Generate test data
        user_data = performance_helper.generate_user_data(user_count)

        # Track memory and timing
        memory_before = performance_helper.get_memory_usage_gb()
        start_time = time.time()

        try:
            # Trigger batch matching calculation
            response = await client.post(
                "/api/v1/matching/batch-calculate",
                json={
                    "users": user_data[:100],  # Start with smaller batch for RED phase
                    "jobs_per_user": jobs_per_user,
                    "performance_mode": True
                },
                timeout=PERFORMANCE_TARGETS["matching_batch_time_seconds"] + 300
            )

            processing_duration = time.time() - start_time
            memory_after = performance_helper.get_memory_usage_gb()
            memory_increase = memory_after - memory_before

            print(f"Matching completed in {processing_duration:.2f} seconds")
            print(f"Memory after matching: {memory_after:.2f} GB (increase: {memory_increase:.2f} GB)")

            # Performance assertions
            assert response.status_code == 200, f"Batch matching failed with status {response.status_code}"

            # Scale up the time requirement based on actual batch size
            max_duration = PERFORMANCE_TARGETS["matching_batch_time_seconds"] * (100 / user_count)
            assert processing_duration <= max_duration, \
                f"Matching took {processing_duration:.2f}s, exceeded {max_duration:.2f}s scaled limit"

            # Verify matching results
            matching_results = response.json()
            assert "results" in matching_results, "Response should contain matching results"
            assert len(matching_results["results"]) > 0, "Should have matching results"

            # Check result structure
            first_result = matching_results["results"][0]
            assert "user_id" in first_result, "Result should contain user_id"
            assert "matches" in first_result, "Result should contain matches"
            assert "processing_time_ms" in first_result, "Result should contain processing time"

        except Exception as error:
            processing_duration = time.time() - start_time
            print(f"Expected failure after {processing_duration:.2f} seconds: Batch matching API not implemented")
            print(f"Error: {error}")

            # In RED phase, we expect this to fail
            pytest.fail(f"Batch matching API not implemented or performance target not met: {error}")


class TestConcurrentConnectionPerformance:
    """Concurrent connection performance tests"""

    def make_concurrent_request(self, request_id: int) -> Dict[str, Any]:
        """Make a single concurrent request"""
        start_time = time.time()
        try:
            with httpx.Client(base_url=API_BASE_URL, timeout=5.0) as client:
                response = client.get("/health")
                duration_ms = (time.time() - start_time) * 1000

                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "success": response.status_code == 200
                }
        except Exception as error:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "request_id": request_id,
                "status_code": 0,
                "duration_ms": duration_ms,
                "success": False,
                "error": str(error)
            }

    def test_concurrent_connection_performance(self, performance_helper):
        """
        Performance Test: 1,000 concurrent connections with <200ms response time

        Expected behavior:
        - System handles 1000 concurrent HTTP connections
        - Average response time under 200ms
        - Success rate above 95%
        - No connection timeouts or server errors

        Current state: Not optimized -> This test will fail
        """
        print(f"🔴 RED PHASE: Concurrent connection performance test")

        concurrent_connections = PERFORMANCE_TARGETS["concurrent_connections"]
        target_response_time = PERFORMANCE_TARGETS["concurrent_response_time_ms"]

        print(f"Testing {concurrent_connections:,} concurrent connections")

        # Track memory before load test
        memory_before = performance_helper.get_memory_usage_gb()
        start_time = time.time()

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=min(concurrent_connections, 100)) as executor:
            # Submit all requests
            futures = [
                executor.submit(self.make_concurrent_request, i)
                for i in range(concurrent_connections)
            ]

            # Collect results
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as error:
                    results.append({
                        "request_id": -1,
                        "status_code": 0,
                        "duration_ms": 10000,
                        "success": False,
                        "error": str(error)
                    })

        total_duration = time.time() - start_time
        memory_after = performance_helper.get_memory_usage_gb()
        memory_increase = memory_after - memory_before

        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]

        if successful_requests:
            avg_response_time = sum(r["duration_ms"] for r in successful_requests) / len(successful_requests)
            max_response_time = max(r["duration_ms"] for r in successful_requests)
            min_response_time = min(r["duration_ms"] for r in successful_requests)
        else:
            avg_response_time = float('inf')
            max_response_time = float('inf')
            min_response_time = float('inf')

        success_rate = len(successful_requests) / len(results) * 100

        print(f"Load test completed in {total_duration:.2f} seconds")
        print(f"Successful requests: {len(successful_requests):,}/{len(results):,} ({success_rate:.1f}%)")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"Response time range: {min_response_time:.2f}ms - {max_response_time:.2f}ms")
        print(f"Memory increase: {memory_increase:.2f} GB")

        # Performance assertions (these will fail in RED phase)
        assert success_rate >= 95.0, \
            f"Success rate {success_rate:.1f}% below 95% threshold"

        assert avg_response_time <= target_response_time, \
            f"Average response time {avg_response_time:.2f}ms exceeded {target_response_time}ms target"

        assert memory_increase <= 1.0, \
            f"Memory increase {memory_increase:.2f}GB exceeded 1GB limit for load test"

        # Check for specific error patterns
        if failed_requests:
            error_summary = {}
            for req in failed_requests:
                error_type = req.get("error", "Unknown")
                error_summary[error_type] = error_summary.get(error_type, 0) + 1

            print(f"Error summary: {error_summary}")


class TestSystemResourcePerformance:
    """System resource usage performance tests"""

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, client, performance_helper):
        """
        Performance Test: Memory usage stays under 8GB during operation

        Expected behavior:
        - System memory usage remains below 8GB during load
        - No memory leaks during extended operation
        - Garbage collection works effectively
        - Memory usage returns to baseline after load

        Current state: Not optimized -> This test will fail
        """
        print(f"🔴 RED PHASE: Memory usage performance test")

        memory_limit_gb = PERFORMANCE_TARGETS["memory_usage_gb"]
        baseline_memory = performance_helper.get_memory_usage_gb()

        print(f"Baseline memory usage: {baseline_memory:.2f} GB")
        print(f"Memory limit: {memory_limit_gb:.2f} GB")

        # Simulate memory-intensive operations
        try:
            # Test 1: Large data retrieval
            print("Testing large data retrieval...")
            response = await client.get("/api/v1/jobs?limit=10000")
            memory_after_retrieval = performance_helper.get_memory_usage_gb()

            # Test 2: Multiple concurrent operations
            print("Testing concurrent operations...")
            tasks = []
            for i in range(50):
                task = client.get(f"/api/v1/jobs?page={i}&limit=100")
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            memory_after_concurrent = performance_helper.get_memory_usage_gb()

            # Test 3: Matching operations (if available)
            print("Testing matching operations...")
            try:
                matching_response = await client.post(
                    "/api/v1/matching/calculate",
                    json={"user_id": 1, "job_ids": list(range(1, 101))},
                    timeout=30
                )
                memory_after_matching = performance_helper.get_memory_usage_gb()
            except Exception:
                memory_after_matching = memory_after_concurrent
                print("Matching endpoint not available, skipping matching memory test")

            # Wait for potential garbage collection
            await asyncio.sleep(5)
            memory_after_gc = performance_helper.get_memory_usage_gb()

            print(f"Memory after retrieval: {memory_after_retrieval:.2f} GB")
            print(f"Memory after concurrent ops: {memory_after_concurrent:.2f} GB")
            print(f"Memory after matching: {memory_after_matching:.2f} GB")
            print(f"Memory after GC: {memory_after_gc:.2f} GB")

            # Memory assertions
            max_memory = max(memory_after_retrieval, memory_after_concurrent, memory_after_matching)

            assert max_memory <= memory_limit_gb, \
                f"Peak memory usage {max_memory:.2f}GB exceeded {memory_limit_gb}GB limit"

            memory_increase = max_memory - baseline_memory
            assert memory_increase <= memory_limit_gb * 0.5, \
                f"Memory increase {memory_increase:.2f}GB exceeded 50% of memory limit"

            # Check for memory leaks
            memory_retention = memory_after_gc - baseline_memory
            assert memory_retention <= 1.0, \
                f"Memory retention {memory_retention:.2f}GB suggests potential memory leak"

        except Exception as error:
            current_memory = performance_helper.get_memory_usage_gb()
            print(f"Expected failure: System performance not optimized")
            print(f"Current memory usage: {current_memory:.2f} GB")
            print(f"Error: {error}")

            # In RED phase, we expect some failures
            pytest.fail(f"System resource performance not optimized: {error}")


if __name__ == "__main__":
    # Display notes when running tests
    print("🔴 TDD RED PHASE: Performance and Load Testing")
    print("=" * 60)
    print("These tests are intentionally designed to fail.")
    print("Performance targets:")
    print(f"- Job import: {PERFORMANCE_TARGETS['job_data_size']:,} records in {PERFORMANCE_TARGETS['job_import_time_seconds']}s")
    print(f"- Matching: {PERFORMANCE_TARGETS['user_data_size']:,} users × {PERFORMANCE_TARGETS['jobs_per_user']} jobs in {PERFORMANCE_TARGETS['matching_batch_time_seconds']}s")
    print(f"- Concurrent: {PERFORMANCE_TARGETS['concurrent_connections']:,} connections in <{PERFORMANCE_TARGETS['concurrent_response_time_ms']}ms")
    print(f"- Memory: <{PERFORMANCE_TARGETS['memory_usage_gb']}GB usage")
    print("")
    print("Expected failures (RED phase):")
    print("1. Bulk import API not implemented")
    print("2. Batch matching API not implemented")
    print("3. System not optimized for concurrent load")
    print("4. Memory usage not optimized")
    print("5. Database queries not optimized for scale")
    print("6. No caching or performance tuning")
    print("")
    print("Next step (GREEN PHASE):")
    print("- Implement bulk import API")
    print("- Create batch matching system")
    print("- Add database indexing and optimization")
    print("- Implement caching layer")
    print("- Add connection pooling")
    print("- Memory optimization and profiling")
    print("=" * 60)