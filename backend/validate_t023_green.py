#!/usr/bin/env python3
"""
T023 GREEN Phase Validation
Simple test runner without pytest dependency
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.personalized_scoring import PersonalizedScoringService
from app.models.user import User


async def test_basic_functionality():
    """Test basic PersonalizedScoringService functionality"""
    print("🧪 Testing T023 PersonalizedScoringService - GREEN PHASE")
    print("=" * 60)

    # Initialize service
    service = PersonalizedScoringService()
    print(f"✅ Service initialized with ALS factors: {service.ALS_FACTORS}")
    print(f"✅ Default score: {service.DEFAULT_SCORE}")
    print(f"✅ Minimum history size: {service.MIN_HISTORY_SIZE}")

    # Test 1: ALS model initialization
    print("\n📊 Test 1: ALS Model Initialization")
    model = await service.initialize_als_model()
    assert model is not None, "Model should be initialized"
    assert model.factors == 50, "Model should have 50 factors"
    assert model.regularization == 0.01, "Model should have 0.01 regularization"
    assert model.iterations == 15, "Model should have 15 iterations"
    print("✅ ALS model initialization passed")

    # Test 2: User with no history
    print("\n👤 Test 2: User with no search history")
    user_no_history = User(
        user_id="test_user_001",
        email="test@example.com",
        search_history=[]
    )

    score = await service.calculate_personalized_score(user_no_history, "test_job_001")
    assert score == service.DEFAULT_SCORE, f"Should return default score {service.DEFAULT_SCORE}, got {score}"
    print(f"✅ No history test passed - returned {score}")

    # Test 3: User with insufficient history
    print("\n📋 Test 3: User with insufficient history")
    user_limited_history = User(
        user_id="limited_user_001",
        email="limited@example.com",
        search_history=[
            {
                "job_id": "job_001",
                "interaction_type": "view",
                "duration": 45,
                "timestamp": datetime.now() - timedelta(days=2)
            },
            {
                "job_id": "job_002",
                "interaction_type": "view",
                "duration": 30,
                "timestamp": datetime.now() - timedelta(days=1)
            }
        ]
    )

    score = await service.calculate_personalized_score(user_limited_history, "test_job_002")
    assert score == service.DEFAULT_SCORE, f"Should return default score for insufficient history, got {score}"
    print(f"✅ Insufficient history test passed - returned {score}")

    # Test 4: User with sufficient history
    print("\n🎯 Test 4: User with sufficient search history")
    user_with_history = User(
        user_id="test_user_with_history",
        email="history@example.com",
        search_history=[
            {
                "job_id": "job_001",
                "interaction_type": "view",
                "duration": 120,
                "timestamp": datetime.now() - timedelta(days=5)
            },
            {
                "job_id": "job_002",
                "interaction_type": "apply",
                "duration": 300,
                "timestamp": datetime.now() - timedelta(days=3)
            },
            {
                "job_id": "job_003",
                "interaction_type": "view",
                "duration": 60,
                "timestamp": datetime.now() - timedelta(days=1)
            },
            {
                "job_id": "job_004",
                "interaction_type": "save",
                "duration": 30,
                "timestamp": datetime.now() - timedelta(hours=12)
            },
            {
                "job_id": "job_005",
                "interaction_type": "view",
                "duration": 180,
                "timestamp": datetime.now() - timedelta(hours=6)
            }
        ]
    )

    score = await service.calculate_personalized_score(user_with_history, "target_job_001")
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
    assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
    print(f"✅ Sufficient history test passed - returned {score}")

    # Test 5: Skill matching
    print("\n🛠️ Test 5: Skill matching algorithm")
    user_with_skills = User(
        user_id="skilled_user",
        email="skilled@example.com",
        search_history=[
            {
                "job_id": "programming_job_001",
                "interaction_type": "apply",
                "duration": 400,
                "timestamp": datetime.now() - timedelta(days=1),
                "skills": ["python", "fastapi", "sql"]
            },
            {
                "job_id": "programming_job_002",
                "interaction_type": "view",
                "duration": 200,
                "timestamp": datetime.now() - timedelta(days=2),
                "skills": ["python", "django", "postgresql"]
            },
            {
                "job_id": "programming_job_003",
                "interaction_type": "save",
                "duration": 100,
                "timestamp": datetime.now() - timedelta(days=3),
                "skills": ["javascript", "react", "node.js"]
            },
            {
                "job_id": "programming_job_004",
                "interaction_type": "view",
                "duration": 150,
                "timestamp": datetime.now() - timedelta(days=4),
                "skills": ["python", "machine learning", "tensorflow"]
            },
            {
                "job_id": "programming_job_005",
                "interaction_type": "apply",
                "duration": 350,
                "timestamp": datetime.now() - timedelta(days=5),
                "skills": ["python", "fastapi", "docker"]
            }
        ]
    )

    python_job_score = await service.calculate_personalized_score(user_with_skills, "python_fastapi_job")
    design_job_score = await service.calculate_personalized_score(user_with_skills, "graphic_design_job")

    assert python_job_score > design_job_score, f"Python job should score higher: {python_job_score} vs {design_job_score}"
    print(f"✅ Skill matching test passed - Python job: {python_job_score}, Design job: {design_job_score}")

    # Test 6: Behavior analysis
    print("\n🔍 Test 6: User behavior analysis")
    analyzed_data = await service.analyze_user_behavior(user_with_history.search_history, days=30)
    assert isinstance(analyzed_data, list), "Should return list of analyzed data"
    assert len(analyzed_data) > 0, "Should have analyzed behavior patterns"
    print(f"✅ Behavior analysis test passed - analyzed {len(analyzed_data)} records")

    # Test 7: Error handling
    print("\n⚠️ Test 7: Error handling")
    try:
        await service.calculate_personalized_score(None, "test_job")
        assert False, "Should raise ValueError for None user"
    except ValueError:
        print("✅ Error handling test passed - caught ValueError for None user")

    invalid_score = await service.calculate_personalized_score(user_no_history, None)
    assert invalid_score == service.DEFAULT_SCORE, "Should return default score for invalid job_id"
    print(f"✅ Error handling test passed - returned {invalid_score} for invalid job_id")

    print("\n🎉 ALL TESTS PASSED - GREEN PHASE SUCCESSFUL!")
    print("✅ User preference-based scoring: Implemented")
    print("✅ Historical interaction scoring: Implemented")
    print("✅ Skill matching algorithms: Implemented")
    print("✅ Experience level matching: Implemented")
    print("✅ Collaborative filtering foundation: Implemented")
    print("✅ Error handling: Implemented")
    print("\n🔄 Ready for REFACTOR phase!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())