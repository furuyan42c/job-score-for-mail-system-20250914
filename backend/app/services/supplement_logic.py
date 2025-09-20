#!/usr/bin/env python3
"""
T026 GREEN PHASE: Minimal 40-item Supplement Logic Implementation
This is the minimal implementation to make tests pass.
"""

import logging
from typing import List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FallbackJob:
    """Simple fallback job for supplement logic."""
    job_id: str
    basic_score: float = 25.0
    title: str = "Fallback Job"
    company: str = "Fallback Company"
    location: str = "Unknown"

class MinimalJobSupplementService:
    """Minimal implementation for 40-item supplement logic - GREEN PHASE."""

    def __init__(self, target_count: int = 40):
        self.target_count = target_count

    async def ensure_minimum_items(self, jobs: List[Any], user: Any, target_count: int = None) -> List[Any]:
        """
        Ensure minimum number of items through supplementation.

        GREEN PHASE: Minimal implementation that makes tests pass.
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
                location=getattr(user, 'preferences', {}).get('location', 'Unknown')
            )

            result.append(fallback_job)
            existing_ids.add(fallback_id)
            fallback_counter += 1

        # Sort by score (highest first) to maintain priority ordering
        result.sort(key=lambda x: getattr(x, 'basic_score', 0), reverse=True)

        return result[:target]

# Update the test file to use the real implementation
class SupplementLogicService(MinimalJobSupplementService):
    """Alias for the main service."""
    pass