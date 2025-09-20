#!/usr/bin/env python3
"""
Direct test of GREEN phase implementation for T028
This bypasses the app module system to test just the scoring batch service
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly without going through app module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'services'))

try:
    from scoring_batch import ScoringBatchService, BatchConfig, BatchResult

    async def test_green_phase():
        print("=== GREEN PHASE TESTING ===")

        # Test 1: Basic instantiation
        print("Test 1: Service instantiation...")
        config = BatchConfig()
        service = ScoringBatchService(config)
        print("✓ Service created successfully")

        # Test 2: Basic score calculation
        print("Test 2: Basic score calculation...")
        user_data = {'id': 1, 'skills': ['Python', 'Django'], 'location': 'Tokyo'}
        job_data = {'id': 1, 'required_skills': ['Python', 'FastAPI'], 'location': 'Tokyo'}

        basic_score = await service.calculate_basic_score(user_data, job_data)
        print(f"✓ Basic score: {basic_score}")
        assert 0 <= basic_score <= 1, f"Basic score {basic_score} not in range [0,1]"

        # Test 3: SEO score calculation
        print("Test 3: SEO score calculation...")
        user_seo_data = {'id': 1, 'profile_keywords': ['senior', 'python', 'developer'], 'profile_completeness': 0.8}
        job_seo_data = {'id': 1, 'seo_keywords': ['senior', 'python', 'engineer'], 'description_quality': 0.9}

        seo_score = await service.calculate_seo_score(user_seo_data, job_seo_data)
        print(f"✓ SEO score: {seo_score}")
        assert 0 <= seo_score <= 1, f"SEO score {seo_score} not in range [0,1]"

        # Test 4: Personalized score calculation
        print("Test 4: Personalized score calculation...")
        user_pref_data = {
            'id': 1,
            'preferences': {
                'remote_work': True,
                'salary_range': {'min': 5000000, 'max': 8000000},
                'company_size': 'startup'
            }
        }
        job_pref_data = {
            'id': 1,
            'remote_allowed': True,
            'salary_range': {'min': 6000000, 'max': 9000000},
            'company_size': 'startup'
        }

        personalized_score = await service.calculate_personalized_score(user_pref_data, job_pref_data)
        print(f"✓ Personalized score: {personalized_score}")
        assert 0 <= personalized_score <= 1, f"Personalized score {personalized_score} not in range [0,1]"

        # Test 5: Batch processing
        print("Test 5: Batch processing...")
        users = [
            {'id': i, 'skills': ['Python'], 'location': 'Tokyo'}
            for i in range(1, 4)
        ]
        jobs = [
            {'id': j, 'required_skills': ['Python'], 'location': 'Tokyo'}
            for j in range(1, 3)
        ]

        batch_results = await service.process_batch(users, jobs)
        print(f"✓ Batch processing returned {len(batch_results)} results")
        assert len(batch_results) == 6, f"Expected 6 results (3 users × 2 jobs), got {len(batch_results)}"

        # Test 6: Score persistence
        print("Test 6: Score persistence...")
        scores = [
            {
                'user_id': 1,
                'job_id': 1,
                'basic_score': 0.8,
                'seo_score': 0.7,
                'personalized_score': 0.9,
                'composite_score': 0.8
            }
        ]

        persist_result = await service.persist_scores(scores)
        print(f"✓ Score persistence success: {persist_result.success}")
        assert persist_result.success, "Score persistence should succeed"

        # Test 7: Incremental scoring
        print("Test 7: Incremental scoring...")
        from datetime import datetime, timedelta
        last_run_time = datetime.now() - timedelta(hours=24)

        incremental_result = await service.run_incremental_scoring(last_run_time)
        print(f"✓ Incremental scoring returned: {incremental_result}")
        assert 'processed_users' in incremental_result

        # Test 8: Performance metrics
        print("Test 8: Performance metrics...")
        metrics = await service.get_performance_metrics()
        print(f"✓ Performance metrics: {metrics}")
        expected_keys = ['scores_per_second', 'memory_usage', 'processing_time']
        for key in expected_keys:
            assert key in metrics, f"Missing key {key} in metrics"

        print("\n=== ALL GREEN PHASE TESTS PASSED ===")
        return True

    # Run the tests
    if __name__ == "__main__":
        result = asyncio.run(test_green_phase())
        print(f"Green phase test result: {result}")

except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()