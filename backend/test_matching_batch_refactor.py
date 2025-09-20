#!/usr/bin/env python3
"""
Test for T029 REFACTOR phase verification.
Comprehensive testing of the refactored MatchingBatchService.
"""

import sys
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, '/Users/furuyanaoki/Project/new.mail.score/backend')

async def test_refactor_phase():
    """Test the REFACTOR phase implementation."""
    print("=== T029 REFACTOR PHASE TESTING ===")

    try:
        # Test 1: Import the service and configuration classes
        print("1. Testing enhanced imports...")
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'matching_batch',
            '/Users/furuyanaoki/Project/new.mail.score/backend/app/services/matching_batch.py'
        )
        matching_batch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(matching_batch_module)

        MatchingBatchService = matching_batch_module.MatchingBatchService
        BatchConfig = matching_batch_module.BatchConfig
        ProcessingStrategy = matching_batch_module.ProcessingStrategy
        ProcessingMetrics = matching_batch_module.ProcessingMetrics
        UserProcessingResult = matching_batch_module.UserProcessingResult

        print("   ✓ All enhanced classes imported successfully")

        # Test 2: Configuration validation
        print("2. Testing configuration validation...")
        config = BatchConfig(
            max_concurrent_users=5,
            max_processing_time_seconds=60,
            strategy=ProcessingStrategy.ADAPTIVE
        )

        try:
            invalid_config = BatchConfig(max_concurrent_users=0)
            print("   ✗ Should have failed with invalid config")
            return False
        except ValueError:
            print("   ✓ Configuration validation works")

        # Test 3: Service initialization with configuration
        print("3. Testing enhanced initialization...")
        service = MatchingBatchService(config)
        assert hasattr(service, 'config')
        assert hasattr(service, 'metrics')
        assert hasattr(service, '_performance_monitor')
        print("   ✓ Service initialized with enhanced features")

        # Test 4: Health check functionality
        print("4. Testing health check...")
        health_status = await service.health_check()
        assert 'status' in health_status
        assert 'services' in health_status
        assert 'config' in health_status
        assert 'timestamp' in health_status
        print(f"   ✓ Health check passed: {health_status['status']}")

        # Test 5: Enhanced batch processing
        print("5. Testing enhanced batch processing...")

        users = [
            {
                'user_id': 1,
                'preferences': {
                    'preferred_categories': ['IT'],
                    'location': 'Tokyo',
                    'salary_min': 3000
                }
            },
            {
                'user_id': 2,
                'preferences': {
                    'preferred_categories': ['Sales'],
                    'location': 'Osaka',
                    'salary_min': 2500
                }
            }
        ]

        jobs = [
            {
                'job_id': f'job_{i:03d}',
                'endcl_cd': f'company_{i % 10}',
                'application_name': f'Job Title {i}',
                'category': 'IT' if i % 2 == 0 else 'Sales',
                'score': 60 + i,
                'salary_min': 2500 + (i * 100),
                'location_score': 75,
                'created_at': datetime.now(),
                'working_hours_flexible': True
            }
            for i in range(50)
        ]

        applications = []

        # Test batch processing with configuration override
        override_config = BatchConfig(
            max_concurrent_users=2,
            strategy=ProcessingStrategy.PARALLEL
        )

        results = await service.process_users_batch(users, jobs, applications, override_config)

        # Verify enhanced results structure
        assert 'performance_metrics' in results
        assert 'users' in results
        assert 'metrics' in results

        performance_metrics = results['performance_metrics']
        assert hasattr(performance_metrics, 'total_users')
        assert hasattr(performance_metrics, 'successful_users')
        assert hasattr(performance_metrics, 'error_rate')

        print("   ✓ Enhanced batch processing completed")
        print(f"     - Total users: {performance_metrics.total_users}")
        print(f"     - Successful users: {performance_metrics.successful_users}")
        print(f"     - Error rate: {performance_metrics.error_rate:.3f}")
        print(f"     - Processing time: {performance_metrics.total_processing_time:.3f}s")

        # Test 6: Individual user processing with enhanced result
        print("6. Testing enhanced single user processing...")
        user_result = await service.process_single_user(users[0], jobs, applications)

        assert isinstance(user_result, UserProcessingResult)
        assert user_result.success
        assert user_result.user_id == 1
        assert user_result.sections is not None
        assert user_result.total_jobs > 0
        assert user_result.metrics is not None

        print("   ✓ Enhanced single user processing completed")
        print(f"     - User ID: {user_result.user_id}")
        print(f"     - Success: {user_result.success}")
        print(f"     - Total jobs: {user_result.total_jobs}")
        print(f"     - Processing time: {user_result.processing_time:.3f}s")

        # Test 7: Error handling and resilience
        print("7. Testing error handling...")

        # Test with invalid job data (empty jobs list to test graceful failure)
        try:
            await service.process_users_batch(users, [], applications)
            print("   ✗ Should have failed with empty jobs list")
            return False
        except ValueError as e:
            print("   ✓ Input validation works correctly")

        # Test individual user error handling by providing user with missing preferences
        problematic_user = {'user_id': 999}  # Valid structure but minimal data
        user_result = await service.process_single_user(problematic_user, jobs, applications)

        # Should handle gracefully - either succeed with defaults or fail gracefully
        print(f"   ✓ Individual user error handling: success={user_result.success}")
        if not user_result.success:
            print(f"     - Error handled: {user_result.error_message[:50]}...")
        else:
            print(f"     - Processed with defaults: {user_result.total_jobs} jobs")

        # Test 8: Performance metrics and monitoring
        print("8. Testing performance metrics...")

        metrics = service.get_performance_metrics()
        assert isinstance(metrics, ProcessingMetrics)

        # Reset metrics
        service.reset_metrics()
        new_metrics = service.get_performance_metrics()
        assert new_metrics.total_users == 0

        print("   ✓ Performance metrics and reset functionality work")

        # Test 9: Backward compatibility
        print("9. Testing backward compatibility...")

        legacy_results = await service.process_users_batch_parallel(
            users, jobs, applications, max_concurrent=3
        )

        assert 'users' in legacy_results
        assert legacy_results['successful_users'] > 0

        print("   ✓ Backward compatibility maintained")

        # Test 10: Configuration updates
        print("10. Testing configuration updates...")

        new_config = BatchConfig(
            max_concurrent_users=8,
            strategy=ProcessingStrategy.SEQUENTIAL
        )
        service.update_config(new_config)
        assert service.config.max_concurrent_users == 8
        assert service.config.strategy == ProcessingStrategy.SEQUENTIAL

        print("   ✓ Configuration updates work")

        print("\n=== REFACTOR PHASE: ALL TESTS PASSED ✓ ===")
        return True

    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_refactor_phase())
    if success:
        print("\nREFACTOR PHASE VERIFICATION: SUCCESS")
        sys.exit(0)
    else:
        print("\nREFACTOR PHASE VERIFICATION: FAILED")
        sys.exit(1)