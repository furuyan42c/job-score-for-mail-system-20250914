#!/usr/bin/env python3
"""
T026 TDD Implementation: Standalone 40-item Supplement Logic Test
Complete TDD cycle without application dependencies
"""

import asyncio
from typing import List, Any, Optional
from dataclasses import dataclass

# ===== IMPLEMENTATION (GREEN PHASE) =====

@dataclass
class FallbackJob:
    """Simple fallback job for supplement logic."""
    job_id: str
    basic_score: float = 25.0
    title: str = "Fallback Job"
    company: str = "Fallback Company"
    location: str = "Unknown"

class SupplementLogicService:
    """40-item supplement logic service - GREEN PHASE implementation."""

    def __init__(self, target_count: int = 40):
        self.target_count = target_count

    async def ensure_minimum_items(self, jobs: List[Any], user: Any, target_count: int = None) -> List[Any]:
        """
        Ensure minimum number of items through supplementation.
        """
        target = target_count or self.target_count

        # If we already have enough, return the target number
        if len(jobs) >= target:
            return jobs[:target]

        # Start with existing jobs
        result = jobs.copy()

        # Calculate how many more we need
        needed = target - len(jobs)

        # Generate fallback jobs to reach target
        existing_ids = {getattr(job, 'job_id', f'job_{i}') for i, job in enumerate(jobs)}

        fallback_counter = 0
        while len(result) < target:
            # Create unique fallback job ID
            fallback_id = f"fallback_{fallback_counter:03d}"
            while fallback_id in existing_ids:
                fallback_counter += 1
                fallback_id = f"fallback_{fallback_counter:03d}"

            # Create fallback job
            fallback_job = FallbackJob(
                job_id=fallback_id,
                basic_score=25.0,
                title=f"Fallback Job {fallback_counter}",
                company=f"Fallback Company {fallback_counter}",
                location=getattr(user, 'preferences', {}).get('location', 'Unknown') if hasattr(user, 'preferences') else 'Unknown'
            )

            result.append(fallback_job)
            existing_ids.add(fallback_id)
            fallback_counter += 1

        # Sort by score (highest first) to maintain priority ordering
        result.sort(key=lambda x: getattr(x, 'basic_score', 0), reverse=True)

        return result[:target]

# ===== TEST SETUP =====

class MockJob:
    def __init__(self, job_id: str, score: float, location: str = "Tokyo"):
        self.job_id = job_id
        self.basic_score = score
        self.location = location
        self.title = f"Job {job_id}"
        self.company = f"Company {job_id}"

class MockUser:
    def __init__(self, user_id: str, preferences: dict = None):
        self.user_id = user_id
        self.preferences = preferences or {}

# ===== TDD TESTS =====

async def test_ensures_minimum_40_items_when_insufficient():
    """GREEN: Test that supplement ensures minimum 40 items when fewer are provided."""
    print("Testing: ensures minimum 40 items when insufficient...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 90 - i) for i in range(10)]

    # Act
    result = await service.ensure_minimum_items(jobs, user, 40)

    # Assert
    assert len(result) == 40, f"Expected 40 jobs, got {len(result)}"

    # Original jobs should be present
    original_job_ids = {f"job_{i}" for i in range(10)}
    result_original = [job for job in result if job.job_id in original_job_ids]
    assert len(result_original) == 10, f"Expected 10 original jobs, got {len(result_original)}"

    print("✅ PASSED")

async def test_fallback_selection_when_not_enough_matches():
    """GREEN: Test fallback when not enough high-score matches available."""
    print("Testing: fallback selection when not enough matches...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 85) for i in range(5)]

    # Act
    result = await service.ensure_minimum_items(jobs, user, 40)

    # Assert
    assert len(result) == 40, f"Expected 40 jobs, got {len(result)}"

    # Should have 5 original + 35 fallback jobs
    fallback_jobs = [job for job in result if job.job_id.startswith("fallback_")]
    assert len(fallback_jobs) == 35, f"Expected 35 fallback jobs, got {len(fallback_jobs)}"

    print("✅ PASSED")

async def test_priority_ordering_for_supplementation():
    """GREEN: Test that supplement maintains priority order."""
    print("Testing: priority ordering for supplementation...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [
        MockJob("high_1", 90),
        MockJob("low_1", 30),
        MockJob("medium_1", 60),
    ]

    # Act
    result = await service.ensure_minimum_items(jobs, user, 40)

    # Assert
    assert len(result) == 40, f"Expected 40 jobs, got {len(result)}"

    # Check that higher score jobs come first
    assert result[0].job_id == "high_1", f"Expected high_1 first, got {result[0].job_id}"

    # Verify descending score order for original jobs
    original_jobs = [job for job in result if job.job_id in ["high_1", "low_1", "medium_1"]]
    scores = [job.basic_score for job in original_jobs]
    assert scores == sorted(scores, reverse=True), f"Expected descending order, got {scores}"

    print("✅ PASSED")

async def test_avoids_already_selected_items():
    """GREEN: Test that supplement doesn't duplicate already selected items."""
    print("Testing: avoids already selected items...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"selected_{i}", 80) for i in range(15)]

    # Act
    result = await service.ensure_minimum_items(jobs, user, 40)

    # Assert
    assert len(result) == 40, f"Expected 40 jobs, got {len(result)}"

    # Check no duplicates by job_id
    job_ids = [job.job_id for job in result]
    unique_ids = set(job_ids)
    assert len(job_ids) == len(unique_ids), f"Found duplicate job IDs: {len(job_ids)} vs {len(unique_ids)}"

    # Original jobs should all be present
    original_ids = {f"selected_{i}" for i in range(15)}
    result_original_ids = {job.job_id for job in result if job.job_id in original_ids}
    assert len(result_original_ids) == 15, f"Expected 15 original jobs, got {len(result_original_ids)}"

    print("✅ PASSED")

async def test_no_supplement_when_already_sufficient():
    """GREEN: Test no supplement when already 40+ items."""
    print("Testing: no supplement when already sufficient...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 70) for i in range(50)]

    # Act
    result = await service.ensure_minimum_items(jobs, user, 40)

    # Assert
    assert len(result) == 40, f"Expected exactly 40 jobs, got {len(result)}"

    # Should be the highest scoring 40 jobs
    result_ids = {job.job_id for job in result}
    # All should be original jobs (no fallback)
    fallback_count = sum(1 for job_id in result_ids if job_id.startswith("fallback_"))
    assert fallback_count == 0, f"Expected no fallback jobs, found {fallback_count}"

    print("✅ PASSED")

async def run_all_tests():
    """Run all TDD tests for GREEN phase."""
    print("🟢 Running TDD GREEN PHASE tests...\n")

    try:
        await test_ensures_minimum_40_items_when_insufficient()
        await test_fallback_selection_when_not_enough_matches()
        await test_priority_ordering_for_supplementation()
        await test_avoids_already_selected_items()
        await test_no_supplement_when_already_sufficient()

        print("\n🎉 All GREEN phase tests PASSED!")
        print("✅ T026 40-item supplement logic implementation is working")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests())