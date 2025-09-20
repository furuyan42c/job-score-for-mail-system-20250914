#!/usr/bin/env python3
"""
Standalone test for T029 GREEN phase verification.
Tests the MatchingBatchService directly without pytest dependencies.
"""

import sys
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, '/Users/furuyanaoki/Project/new.mail.score/backend')

async def test_green_phase():
    """Test the GREEN phase implementation."""
    print("=== T029 GREEN PHASE TESTING ===")

    try:
        # Test 1: Import the service
        print("1. Testing import...")
        from app.services.matching_batch import MatchingBatchService
        print("   ✓ MatchingBatchService imported successfully")

        # Test 2: Initialize the service
        print("2. Testing initialization...")
        service = MatchingBatchService()
        print("   ✓ MatchingBatchService initialized successfully")

        # Test 3: Check service dependencies
        print("3. Testing service dependencies...")
        assert hasattr(service, 'section_service'), "Missing section_service"
        assert hasattr(service, 'duplicate_service'), "Missing duplicate_service"
        assert hasattr(service, 'supplement_service'), "Missing supplement_service"
        print("   ✓ All service dependencies present")

        # Test 4: Test basic batch processing
        print("4. Testing basic batch processing...")

        # Sample test data
        users = [
            {
                'user_id': 1,
                'preferences': {
                    'preferred_categories': ['IT'],
                    'location': 'Tokyo'
                }
            }
        ]

        jobs = [
            {
                'job_id': 'test_job_001',
                'endcl_cd': 'test_company_1',
                'application_name': 'Test Job',
                'category': 'IT',
                'score': 75,
                'salary_min': 3000,
                'location_score': 80,
                'created_at': datetime.now(),
                'working_hours_flexible': True
            }
        ]

        applications = []

        # Process batch
        results = await service.process_users_batch(users, jobs, applications)

        # Verify results structure
        assert 'users' in results, "Missing 'users' in results"
        assert 'total_users' in results, "Missing 'total_users' in results"
        assert 'successful_users' in results, "Missing 'successful_users' in results"
        assert 'failed_users' in results, "Missing 'failed_users' in results"
        assert 'processing_time' in results, "Missing 'processing_time' in results"
        assert 'metrics' in results, "Missing 'metrics' in results"

        print("   ✓ Batch processing completed successfully")
        print(f"     - Total users: {results['total_users']}")
        print(f"     - Successful users: {results['successful_users']}")
        print(f"     - Failed users: {results['failed_users']}")
        print(f"     - Processing time: {results['processing_time']:.3f}s")

        # Test 5: Test single user processing
        print("5. Testing single user processing...")
        user_result = await service.process_single_user(users[0], jobs, applications)

        assert 'sections' in user_result, "Missing 'sections' in user_result"
        assert 'total_jobs' in user_result, "Missing 'total_jobs' in user_result"
        assert 'processing_time' in user_result, "Missing 'processing_time' in user_result"

        print("   ✓ Single user processing completed successfully")
        print(f"     - Total jobs: {user_result['total_jobs']}")
        print(f"     - Sections: {list(user_result['sections'].keys())}")

        # Test 6: Test parallel processing
        print("6. Testing parallel processing...")
        parallel_results = await service.process_users_batch_parallel(
            users, jobs, applications, max_concurrent=2
        )

        assert 'users' in parallel_results, "Missing 'users' in parallel results"
        assert parallel_results['successful_users'] > 0, "No successful parallel processing"

        print("   ✓ Parallel processing completed successfully")
        print(f"     - Successful users: {parallel_results['successful_users']}")

        print("\n=== GREEN PHASE: ALL TESTS PASSED ✓ ===")
        return True

    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_green_phase())
    if success:
        print("\nGREEN PHASE VERIFICATION: SUCCESS")
        sys.exit(0)
    else:
        print("\nGREEN PHASE VERIFICATION: FAILED")
        sys.exit(1)