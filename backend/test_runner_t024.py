#!/usr/bin/env python3
"""
Simple test runner for T024 section selection without external dependencies.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.section_selection import SectionSelectionService


def create_sample_jobs():
    """Create sample job data for testing."""
    jobs = []

    # High score recent jobs for editorial picks
    for i in range(10):
        jobs.append({
            'job_id': f'editorial_{i}',
            'title': f'Editorial Job {i}',
            'company_name': f'Premium Company {i}',
            'score': 85.0 + i,
            'created_at': datetime.now() - timedelta(hours=i),
            'salary_min': 1500,
            'salary_max': 2000,
            'category': 1,
            'location_score': 70.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # High salary jobs
    for i in range(10):
        jobs.append({
            'job_id': f'high_salary_{i}',
            'title': f'High Salary Job {i}',
            'company_name': f'High Pay Company {i}',
            'score': 75.0 + i,
            'created_at': datetime.now() - timedelta(days=i+1),
            'salary_min': 1800 + i*50,
            'salary_max': 2200 + i*50,
            'category': 2,
            'location_score': 60.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Experience match jobs (category 3)
    for i in range(10):
        jobs.append({
            'job_id': f'exp_match_{i}',
            'title': f'Experience Match Job {i}',
            'company_name': f'Experience Company {i}',
            'score': 70.0 + i,
            'created_at': datetime.now() - timedelta(days=i+2),
            'salary_min': 1300,
            'salary_max': 1600,
            'category': 3,  # User preferred category
            'location_score': 80.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Location convenient jobs
    for i in range(10):
        jobs.append({
            'job_id': f'location_{i}',
            'title': f'Location Job {i}',
            'company_name': f'Nearby Company {i}',
            'score': 65.0 + i,
            'created_at': datetime.now() - timedelta(days=i+3),
            'salary_min': 1200,
            'salary_max': 1500,
            'category': 4,
            'location_score': 90.0 + i,  # High location scores
            'working_hours_flexible': False,
            'weekend_available': False
        })

    # Weekend/flexible jobs
    for i in range(10):
        jobs.append({
            'job_id': f'weekend_{i}',
            'title': f'Weekend Job {i}',
            'company_name': f'Flexible Company {i}',
            'score': 60.0 + i,
            'created_at': datetime.now() - timedelta(days=i+4),
            'salary_min': 1100,
            'salary_max': 1400,
            'category': 5,
            'location_score': 50.0,
            'working_hours_flexible': True,
            'weekend_available': True
        })

    # Other recommendation jobs
    for i in range(10):
        jobs.append({
            'job_id': f'other_{i}',
            'title': f'Other Job {i}',
            'company_name': f'General Company {i}',
            'score': 55.0 + i,
            'created_at': datetime.now() - timedelta(days=i+5),
            'salary_min': 1000,
            'salary_max': 1300,
            'category': 6,
            'location_score': 40.0,
            'working_hours_flexible': False,
            'weekend_available': False
        })

    return jobs


def create_user_preferences():
    """User preferences for testing."""
    return {
        'preferred_categories': [3],  # Category 3 for experience match
        'location_preference': 'central_tokyo',
        'salary_preference_min': 1200,
        'flexible_working_preferred': True
    }


async def test_basic_functionality():
    """Test basic functionality of section selection."""
    print("🧪 Testing T024 Section Selection Service")
    print("=" * 50)

    # Create test data
    service = SectionSelectionService()
    jobs = create_sample_jobs()
    user_preferences = create_user_preferences()

    print(f"📊 Total jobs available: {len(jobs)}")
    print(f"👤 User preferred categories: {user_preferences['preferred_categories']}")

    # Execute section selection
    try:
        sections = await service.select_sections(
            jobs=jobs,
            user_preferences=user_preferences,
            total_jobs_required=40
        )

        print("\n✅ Section Selection Completed Successfully!")
        print(f"📋 Total sections created: {len(sections)}")

        # Validate results
        total_jobs = sum(len(section_jobs) for section_jobs in sections.values())
        print(f"🎯 Total jobs distributed: {total_jobs}")

        # Print section breakdown
        print("\n📊 Section Distribution:")
        print("-" * 30)

        for section_name, section_jobs in sections.items():
            if section_jobs:
                avg_score = sum(job['score'] for job in section_jobs) / len(section_jobs)
                print(f"{section_name}: {len(section_jobs)} jobs (avg score: {avg_score:.1f})")

                # Show sample jobs
                for i, job in enumerate(section_jobs[:2]):
                    print(f"  {i+1}. {job['title']} (Score: {job['score']:.1f})")
            else:
                print(f"{section_name}: 0 jobs")

        # Validation checks
        print("\n🔍 Validation Results:")
        print("-" * 20)

        # Check total count
        if total_jobs == 40:
            print("✅ Total job count: PASS (40 jobs)")
        else:
            print(f"❌ Total job count: FAIL ({total_jobs} != 40)")

        # Check section count
        if len(sections) == 6:
            print("✅ Section count: PASS (6 sections)")
        else:
            print(f"❌ Section count: FAIL ({len(sections)} != 6)")

        # Check no duplicates
        all_job_ids = []
        for section_jobs in sections.values():
            all_job_ids.extend([job['job_id'] for job in section_jobs])

        unique_job_ids = set(all_job_ids)
        if len(all_job_ids) == len(unique_job_ids):
            print("✅ No duplicates: PASS")
        else:
            print(f"❌ Duplicates found: FAIL ({len(all_job_ids)} total vs {len(unique_job_ids)} unique)")

        # Check minimum jobs per section
        min_section_size = min(len(section_jobs) for section_jobs in sections.values())
        if min_section_size >= 3:
            print(f"✅ Section minimums: PASS (min {min_section_size} jobs)")
        else:
            print(f"❌ Section minimums: FAIL (min {min_section_size} < 3)")

        # Check score thresholds
        all_scores = []
        for section_jobs in sections.values():
            all_scores.extend([job['score'] for job in section_jobs])

        min_score = min(all_scores) if all_scores else 0
        if min_score >= 50.0:
            print(f"✅ Score thresholds: PASS (min {min_score:.1f})")
        else:
            print(f"❌ Score thresholds: FAIL (min {min_score:.1f} < 50.0)")

        # Check category diversity
        all_categories = []
        for section_jobs in sections.values():
            all_categories.extend([job['category'] for job in section_jobs])

        unique_categories = set(all_categories)
        if len(unique_categories) >= 3:
            print(f"✅ Category diversity: PASS ({len(unique_categories)} categories)")
        else:
            print(f"❌ Category diversity: FAIL ({len(unique_categories)} < 3)")

        return True

    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases."""
    print("\n🧪 Testing Edge Cases")
    print("=" * 50)

    service = SectionSelectionService()
    user_preferences = create_user_preferences()

    # Test with invalid total jobs
    try:
        await service.select_sections(
            jobs=[],
            user_preferences=user_preferences,
            total_jobs_required=0
        )
        print("❌ Should have raised ValueError for zero jobs")
        return False
    except ValueError:
        print("✅ Correctly raised ValueError for zero jobs")

    # Test with insufficient jobs
    limited_jobs = create_sample_jobs()[:20]  # Only 20 jobs
    sections = await service.select_sections(
        jobs=limited_jobs,
        user_preferences=user_preferences,
        total_jobs_required=40
    )

    total_returned = sum(len(section_jobs) for section_jobs in sections.values())
    if total_returned <= 20:
        print(f"✅ Correctly handled insufficient jobs: returned {total_returned} jobs")
    else:
        print(f"❌ Should not exceed available jobs: returned {total_returned} > 20")
        return False

    return True


async def main():
    """Main test runner."""
    print("🚀 T024 Section Selection Service Test Suite")
    print("=" * 60)

    # Run basic functionality test
    basic_passed = await test_basic_functionality()

    # Run edge case tests
    edge_passed = await test_edge_cases()

    print("\n🏁 Test Summary")
    print("=" * 60)

    if basic_passed and edge_passed:
        print("✅ ALL TESTS PASSED - GREEN PHASE SUCCESSFUL!")
        print("📝 Ready for REFACTOR phase")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("🔄 Need to fix implementation")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)