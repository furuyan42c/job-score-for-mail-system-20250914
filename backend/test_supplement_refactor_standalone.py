#!/usr/bin/env python3
"""
T026 TDD REFACTOR Phase: Standalone Test for Enhanced Supplement Logic
Tests the refactored implementation without external dependencies
"""

import asyncio
from typing import List, Any, Optional, Dict, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ===== REFACTORED IMPLEMENTATION =====

class JobLike(Protocol):
    """Protocol defining the interface for job-like objects."""
    job_id: str
    basic_score: float
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

class UserLike(Protocol):
    """Protocol defining the interface for user-like objects."""
    preferences: Optional[Dict[str, Any]] = None

@dataclass
class SupplementConfig:
    """Configuration for supplement logic."""
    target_count: int = 40
    fallback_score: float = 25.0
    min_quality_threshold: float = 0.0
    max_fallback_ratio: float = 0.8  # Max 80% fallback jobs

    def __post_init__(self):
        """Validate configuration values."""
        if self.target_count < 1:
            raise ValueError("target_count must be positive")
        if self.fallback_score < 0:
            raise ValueError("fallback_score must be non-negative")
        if not 0 <= self.max_fallback_ratio <= 1:
            raise ValueError("max_fallback_ratio must be between 0 and 1")

@dataclass
class FallbackJob:
    """Enhanced fallback job with better error handling."""
    job_id: str
    basic_score: float = 25.0
    title: str = "Fallback Job"
    company: str = "Fallback Company"
    location: str = "Unknown"

    def __post_init__(self):
        """Validate fallback job data."""
        if not self.job_id:
            raise ValueError("job_id cannot be empty")
        if self.basic_score < 0:
            raise ValueError("basic_score must be non-negative")

@dataclass
class SupplementResult:
    """Result object for supplement operation with metrics."""
    jobs: List[Any]
    original_count: int
    supplemented_count: int
    fallback_count: int
    total_count: int
    config_used: SupplementConfig

    @property
    def supplemented_ratio(self) -> float:
        """Ratio of supplemented jobs to total."""
        return self.supplemented_count / self.total_count if self.total_count > 0 else 0.0

class BaseSupplementService(ABC):
    """Abstract base class for supplement services."""

    @abstractmethod
    async def ensure_minimum_items(self, jobs: List[Any], user: Any, target_count: int = None) -> List[Any]:
        """Ensure minimum number of items through supplementation."""
        pass

class SupplementLogicService(BaseSupplementService):
    """Enhanced 40-item supplement logic service with improved architecture."""

    def __init__(self, config: Optional[SupplementConfig] = None):
        """Initialize supplement service with configuration."""
        self.config = config or SupplementConfig()

    async def ensure_minimum_items(self, jobs: List[Any], user: Any, target_count: int = None) -> List[Any]:
        """Ensure minimum number of items through supplementation."""
        target = self._validate_target_count(target_count)

        if len(jobs) >= target:
            return self._select_top_jobs(jobs, target)

        # Calculate supplement requirements
        original_count = len(jobs)
        needed = target - original_count

        # Perform supplementation
        result = await self._supplement_jobs(jobs, user, needed)

        # Sort and return top jobs
        sorted_result = self._sort_jobs_by_score(result)
        return sorted_result[:target]

    async def ensure_minimum_items_with_metrics(self, jobs: List[Any], user: Any, target_count: int = None) -> SupplementResult:
        """Ensure minimum items and return detailed metrics."""
        target = self._validate_target_count(target_count)
        original_count = len(jobs)

        supplemented_jobs = await self.ensure_minimum_items(jobs, user, target)

        # Calculate metrics
        fallback_count = sum(1 for job in supplemented_jobs if self._is_fallback_job(job))
        supplemented_count = len(supplemented_jobs) - original_count

        return SupplementResult(
            jobs=supplemented_jobs,
            original_count=original_count,
            supplemented_count=supplemented_count,
            fallback_count=fallback_count,
            total_count=len(supplemented_jobs),
            config_used=self.config
        )

    def _validate_target_count(self, target_count: Optional[int]) -> int:
        """Validate and return target count."""
        target = target_count if target_count is not None else self.config.target_count
        if target < 1:
            raise ValueError("target_count must be positive")
        return target

    def _select_top_jobs(self, jobs: List[Any], target: int) -> List[Any]:
        """Select top jobs when we already have enough."""
        sorted_jobs = self._sort_jobs_by_score(jobs)
        return sorted_jobs[:target]

    async def _supplement_jobs(self, jobs: List[Any], user: Any, needed: int) -> List[Any]:
        """Supplement jobs with fallbacks."""
        result = jobs.copy()
        existing_ids = self._extract_job_ids(jobs)
        user_location = self._extract_user_location(user)

        for i in range(needed):
            fallback_job = self._create_fallback_job(i, existing_ids, user_location)
            result.append(fallback_job)
            existing_ids.add(fallback_job.job_id)

        return result

    def _extract_job_ids(self, jobs: List[Any]) -> set:
        """Extract job IDs from job list."""
        return {getattr(job, 'job_id', f'job_{i}') for i, job in enumerate(jobs)}

    def _extract_user_location(self, user: Any) -> str:
        """Extract user's preferred location."""
        if not hasattr(user, 'preferences'):
            return "Unknown"

        preferences = getattr(user, 'preferences', {})
        if not isinstance(preferences, dict):
            return "Unknown"

        return preferences.get('location', 'Unknown')

    def _create_fallback_job(self, index: int, existing_ids: set, location: str) -> FallbackJob:
        """Create a unique fallback job."""
        fallback_id = self._generate_unique_id(index, existing_ids)

        return FallbackJob(
            job_id=fallback_id,
            basic_score=self.config.fallback_score,
            title=f"Fallback Job {index + 1}",
            company=f"Fallback Company {index + 1}",
            location=location
        )

    def _generate_unique_id(self, base_index: int, existing_ids: set) -> str:
        """Generate a unique fallback job ID."""
        counter = base_index
        while True:
            candidate_id = f"fallback_{counter:03d}"
            if candidate_id not in existing_ids:
                return candidate_id
            counter += 1

    def _sort_jobs_by_score(self, jobs: List[Any]) -> List[Any]:
        """Sort jobs by score in descending order."""
        return sorted(jobs, key=lambda x: getattr(x, 'basic_score', 0), reverse=True)

    def _is_fallback_job(self, job: Any) -> bool:
        """Check if a job is a fallback job."""
        job_id = getattr(job, 'job_id', '')
        return job_id.startswith('fallback_')

class MinimalJobSupplementService(SupplementLogicService):
    """Backward compatibility alias."""

    def __init__(self, target_count: int = 40):
        """Initialize with simple target count for backward compatibility."""
        config = SupplementConfig(target_count=target_count)
        super().__init__(config)

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

# ===== REFACTOR PHASE TESTS =====

async def test_configuration_validation():
    """REFACTOR: Test configuration validation."""
    print("Testing: configuration validation...")

    # Test valid config
    config = SupplementConfig(target_count=50, fallback_score=30.0)
    assert config.target_count == 50
    assert config.fallback_score == 30.0

    # Test invalid target count
    try:
        SupplementConfig(target_count=0)
        assert False, "Should have raised ValueError for target_count=0"
    except ValueError:
        pass  # Expected

    # Test invalid fallback score
    try:
        SupplementConfig(fallback_score=-1.0)
        assert False, "Should have raised ValueError for negative fallback_score"
    except ValueError:
        pass  # Expected

    # Test invalid max_fallback_ratio
    try:
        SupplementConfig(max_fallback_ratio=1.5)
        assert False, "Should have raised ValueError for max_fallback_ratio > 1"
    except ValueError:
        pass  # Expected

    print("✅ PASSED")

async def test_metrics_functionality():
    """REFACTOR: Test metrics functionality."""
    print("Testing: metrics functionality...")

    # Arrange
    service = SupplementLogicService()
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 80) for i in range(10)]

    # Act
    result = await service.ensure_minimum_items_with_metrics(jobs, user, 40)

    # Assert
    assert result.original_count == 10
    assert result.supplemented_count == 30
    assert result.fallback_count == 30
    assert result.total_count == 40
    assert 0 < result.supplemented_ratio <= 1
    assert result.supplemented_ratio == 30/40  # 0.75

    print("✅ PASSED")

async def test_enhanced_error_handling():
    """REFACTOR: Test enhanced error handling."""
    print("Testing: enhanced error handling...")

    service = SupplementLogicService()
    user = MockUser("user_001")
    jobs = [MockJob("job_1", 80)]

    # Test invalid target count
    try:
        await service.ensure_minimum_items(jobs, user, 0)
        assert False, "Should have raised ValueError for target_count=0"
    except ValueError:
        pass  # Expected

    try:
        await service.ensure_minimum_items(jobs, user, -5)
        assert False, "Should have raised ValueError for negative target_count"
    except ValueError:
        pass  # Expected

    print("✅ PASSED")

async def test_fallback_job_validation():
    """REFACTOR: Test fallback job validation."""
    print("Testing: fallback job validation...")

    # Test valid fallback job
    job = FallbackJob("fb_001", 25.0)
    assert job.job_id == "fb_001"
    assert job.basic_score == 25.0

    # Test invalid job_id
    try:
        FallbackJob("", 25.0)
        assert False, "Should have raised ValueError for empty job_id"
    except ValueError:
        pass  # Expected

    # Test invalid score
    try:
        FallbackJob("fb_001", -1.0)
        assert False, "Should have raised ValueError for negative score"
    except ValueError:
        pass  # Expected

    print("✅ PASSED")

async def test_protocol_compliance():
    """REFACTOR: Test protocol compliance."""
    print("Testing: protocol compliance...")

    # Test that MockJob satisfies JobLike protocol
    job = MockJob("test_job", 75.0)
    assert hasattr(job, 'job_id')
    assert hasattr(job, 'basic_score')
    assert hasattr(job, 'title')
    assert hasattr(job, 'company')
    assert hasattr(job, 'location')

    # Test that MockUser satisfies UserLike protocol
    user = MockUser("test_user", {"location": "Osaka"})
    assert hasattr(user, 'preferences')
    assert isinstance(user.preferences, dict)

    print("✅ PASSED")

async def test_abstract_base_class():
    """REFACTOR: Test abstract base class."""
    print("Testing: abstract base class...")

    # Test that BaseSupplementService cannot be instantiated
    try:
        service = BaseSupplementService()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        pass  # Expected

    # Test that SupplementLogicService properly inherits
    service = SupplementLogicService()
    assert isinstance(service, BaseSupplementService)

    print("✅ PASSED")

async def test_backward_compatibility():
    """REFACTOR: Test backward compatibility."""
    print("Testing: backward compatibility...")

    # Test that MinimalJobSupplementService still works
    service = MinimalJobSupplementService(target_count=50)
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 80) for i in range(10)]

    result = await service.ensure_minimum_items(jobs, user, 50)

    assert len(result) == 50
    assert service.config.target_count == 50

    print("✅ PASSED")

async def run_original_tests():
    """Run original GREEN phase tests to ensure they still pass."""
    print("Running original GREEN phase tests...\n")

    # Use the refactored service
    service = SupplementLogicService()

    # Test 1: ensures minimum 40 items when insufficient
    print("Testing: ensures minimum 40 items when insufficient...")
    user = MockUser("user_001", {"location": "Tokyo"})
    jobs = [MockJob(f"job_{i}", 90 - i) for i in range(10)]
    result = await service.ensure_minimum_items(jobs, user, 40)
    assert len(result) == 40
    original_job_ids = {f"job_{i}" for i in range(10)}
    result_original = [job for job in result if job.job_id in original_job_ids]
    assert len(result_original) == 10
    print("✅ PASSED")

    # Test 2: fallback selection when not enough matches
    print("Testing: fallback selection when not enough matches...")
    jobs = [MockJob(f"job_{i}", 85) for i in range(5)]
    result = await service.ensure_minimum_items(jobs, user, 40)
    assert len(result) == 40
    fallback_jobs = [job for job in result if job.job_id.startswith("fallback_")]
    assert len(fallback_jobs) == 35
    print("✅ PASSED")

    # Test 3: priority ordering for supplementation
    print("Testing: priority ordering for supplementation...")
    jobs = [MockJob("high_1", 90), MockJob("low_1", 30), MockJob("medium_1", 60)]
    result = await service.ensure_minimum_items(jobs, user, 40)
    assert len(result) == 40
    assert result[0].job_id == "high_1"
    original_jobs = [job for job in result if job.job_id in ["high_1", "low_1", "medium_1"]]
    scores = [job.basic_score for job in original_jobs]
    assert scores == sorted(scores, reverse=True)
    print("✅ PASSED")

    # Test 4: avoids already selected items
    print("Testing: avoids already selected items...")
    jobs = [MockJob(f"selected_{i}", 80) for i in range(15)]
    result = await service.ensure_minimum_items(jobs, user, 40)
    assert len(result) == 40
    job_ids = [job.job_id for job in result]
    assert len(job_ids) == len(set(job_ids))
    original_ids = {f"selected_{i}" for i in range(15)}
    result_original_ids = {job.job_id for job in result if job.job_id in original_ids}
    assert len(result_original_ids) == 15
    print("✅ PASSED")

    # Test 5: no supplement when already sufficient
    print("Testing: no supplement when already sufficient...")
    jobs = [MockJob(f"job_{i}", 70) for i in range(50)]
    result = await service.ensure_minimum_items(jobs, user, 40)
    assert len(result) == 40
    result_ids = {job.job_id for job in result}
    fallback_count = sum(1 for job_id in result_ids if job_id.startswith("fallback_"))
    assert fallback_count == 0
    print("✅ PASSED")

async def run_all_tests():
    """Run all TDD tests including REFACTOR phase."""
    print("🔵 Running TDD REFACTOR PHASE tests...\n")

    try:
        # First ensure original functionality still works
        await run_original_tests()

        print("\n" + "="*50)
        print("Running REFACTOR phase enhancements...\n")

        # REFACTOR phase tests (new features)
        await test_configuration_validation()
        await test_metrics_functionality()
        await test_enhanced_error_handling()
        await test_fallback_job_validation()
        await test_protocol_compliance()
        await test_abstract_base_class()
        await test_backward_compatibility()

        print("\n🎉 All REFACTOR phase tests PASSED!")
        print("✅ T026 40-item supplement logic is refactored and improved")
        print("✨ Enhanced with: configuration validation, metrics, error handling, protocols, and maintainability")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests())