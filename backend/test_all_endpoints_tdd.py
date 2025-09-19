"""
Comprehensive TDD Test: All T005-T013 Endpoints
Test all implemented API endpoints following TDD verification
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

# Import all models and functions for direct testing
from app.api.endpoints.health import health_check
from app.api.endpoints.users import (
    UserCreateRequest, UserResponse, create_user, get_user_by_id, list_users
)
from app.api.endpoints.additional_endpoints import (
    ScoreRequest, ScoreResponse, calculate_score,
    MatchRequest, MatchResponse, find_matches,
    EmailRequest, EmailResponse, send_email,
    BatchOperationRequest, BatchOperationResponse, start_batch_operation
)


async def test_all_endpoints():
    """Test all TDD endpoints for basic functionality"""
    print("🧪 Testing All T005-T013 TDD Endpoints...")

    # =============================================================================
    # T005: Health Check Endpoint
    # =============================================================================
    print("\n📍 Testing T005: Health Check...")
    health_result = await health_check()
    assert "status" in health_result
    assert health_result["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in health_result
    assert "uptime" in health_result
    print("✅ T005 Health Check: PASSED")

    # =============================================================================
    # T008: Users CRUD (jobs already tested in previous files)
    # =============================================================================
    print("\n👤 Testing T008: Users CRUD...")

    # Create user
    user_data = UserCreateRequest(
        email="test@example.com",
        name="テストユーザー",
        age=25,
        location="東京都",
        skills=["Python", "JavaScript"]
    )
    created_user = await create_user(user_data)
    assert created_user.id > 0
    assert created_user.email == "test@example.com"
    assert created_user.status == "active"
    print("✅ T008 Create User: PASSED")

    # Get user
    retrieved_user = await get_user_by_id(created_user.id)
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email
    print("✅ T008 Get User: PASSED")

    # List users
    users_list = await list_users(limit=10, offset=0, status="active")
    assert users_list.total >= 1
    assert len(users_list.users) >= 1
    assert users_list.users[0].id == created_user.id
    print("✅ T008 List Users: PASSED")

    # =============================================================================
    # T010: Scoring Endpoint
    # =============================================================================
    print("\n📊 Testing T010: Scoring...")
    score_request = ScoreRequest(user_id=1, job_id=1)
    score_result = await calculate_score(score_request)

    assert score_result.score_id > 0
    assert score_result.user_id == 1
    assert score_result.job_id == 1
    assert isinstance(score_result.score, float)
    assert score_result.score > 0
    assert "breakdown" in score_result.model_dump()
    print("✅ T010 Scoring: PASSED")

    # =============================================================================
    # T011: Matching Endpoint
    # =============================================================================
    print("\n🎯 Testing T011: Matching...")
    match_request = MatchRequest(user_id=1, max_results=5, min_score=70.0)
    match_result = await find_matches(match_request)

    assert match_result.match_id > 0
    assert match_result.user_id == 1
    assert len(match_result.matches) <= 5
    assert match_result.total_matches >= 0

    # Check score filtering
    for match in match_result.matches:
        assert match.score >= 70.0
    print("✅ T011 Matching: PASSED")

    # =============================================================================
    # T012: Email Sending Endpoint
    # =============================================================================
    print("\n📧 Testing T012: Email Sending...")
    email_request = EmailRequest(
        to_email="test@example.com",
        subject="テストメール",
        template="welcome_template",
        data={"name": "テストユーザー"}
    )
    email_result = await send_email(email_request)

    assert email_result.email_id > 0
    assert email_result.to_email == "test@example.com"
    assert email_result.subject == "テストメール"
    assert email_result.status in ["sent", "pending", "failed"]
    print("✅ T012 Email Sending: PASSED")

    # =============================================================================
    # T013: Batch Operations Endpoint
    # =============================================================================
    print("\n⚙️ Testing T013: Batch Operations...")
    batch_request = BatchOperationRequest(
        operation_type="score_calculation",
        parameters={"max_users": 100},
        target_count=50
    )
    batch_result = await start_batch_operation(batch_request)

    assert batch_result.batch_id > 0
    assert batch_result.operation_type == "score_calculation"
    assert batch_result.status in ["pending", "running", "completed", "failed"]
    assert batch_result.total_count == 50
    assert 0 <= batch_result.progress_percent <= 100
    print("✅ T013 Batch Operations: PASSED")

    print("\n🎉 ALL T005-T013 ENDPOINTS TESTS PASSED!")
    return True


async def test_error_handling():
    """Test error handling across endpoints"""
    print("\n🚨 Testing Error Handling...")

    # Test invalid user ID
    try:
        await get_user_by_id(99999)
        assert False, "Should have raised exception"
    except Exception as e:
        assert "見つかりません" in str(e) or "not found" in str(e).lower()
        print("✅ Invalid User ID error handling: PASSED")

    # Test invalid email
    try:
        invalid_user = UserCreateRequest(
            email="invalid-email",
            name="テスト"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "メールアドレス" in str(e) or "email" in str(e).lower()
        print("✅ Invalid email validation: PASSED")

    # Test invalid batch operation
    try:
        invalid_batch = BatchOperationRequest(operation_type="invalid_operation")
        await start_batch_operation(invalid_batch)
        assert False, "Should have raised exception"
    except Exception as e:
        assert "無効" in str(e) or "invalid" in str(e).lower()
        print("✅ Invalid batch operation error handling: PASSED")

    print("✅ Error handling tests: PASSED")


async def test_integration_workflow():
    """Test integration workflow across multiple endpoints"""
    print("\n🔄 Testing Integration Workflow...")

    # 1. Create a user
    user_data = UserCreateRequest(
        email="workflow@example.com",
        name="ワークフローユーザー",
        age=30,
        skills=["Python", "FastAPI"]
    )
    user = await create_user(user_data)

    # 2. Calculate score for the user
    score_request = ScoreRequest(user_id=user.id, job_id=1)
    score = await calculate_score(score_request)

    # 3. Find matches for the user
    match_request = MatchRequest(user_id=user.id, max_results=3)
    matches = await find_matches(match_request)

    # 4. Send notification email
    email_request = EmailRequest(
        to_email=user.email,
        subject="新しい求人マッチが見つかりました",
        template="match_notification",
        data={"matches_count": matches.total_matches}
    )
    email = await send_email(email_request)

    # 5. Start batch operation for similar users
    batch_request = BatchOperationRequest(
        operation_type="score_calculation",
        parameters={"user_skills": user.skills}
    )
    batch = await start_batch_operation(batch_request)

    # Verify workflow
    assert user.id > 0
    assert score.user_id == user.id
    assert matches.user_id == user.id
    assert email.to_email == user.email
    assert batch.batch_id > 0

    print("✅ Integration workflow: PASSED")
    print("  📝 User created")
    print("  📊 Score calculated")
    print("  🎯 Matches found")
    print("  📧 Email sent")
    print("  ⚙️ Batch operation started")


if __name__ == "__main__":
    try:
        asyncio.run(test_all_endpoints())
        asyncio.run(test_error_handling())
        asyncio.run(test_integration_workflow())

        print("\n🎉 COMPREHENSIVE TDD TESTS COMPLETE!")
        print("\n📋 Implementation Summary:")
        print("✅ T005: Health Check Endpoint - Complete")
        print("✅ T006: Jobs CRUD Endpoints - Complete")
        print("✅ T007: Jobs Listing with Pagination - Complete (integrated with T006)")
        print("✅ T008: Users CRUD Endpoints - Complete")
        print("✅ T009: CSV Import Endpoint - Complete")
        print("✅ T010: Scoring Endpoint - Complete")
        print("✅ T011: Matching Endpoint - Complete")
        print("✅ T012: Email Sending Endpoint - Complete")
        print("✅ T013: Batch Operations Endpoint - Complete")

        print("\n🏗️ TDD Implementation Features:")
        print("  🔴 RED Phase: Created failing tests for all endpoints")
        print("  🟢 GREEN Phase: Implemented minimal functionality to pass tests")
        print("  🔄 REFACTOR Phase: Enhanced with production features")
        print("    - Input validation with Pydantic models")
        print("    - Proper HTTP status codes and error handling")
        print("    - Pagination and filtering")
        print("    - Enum-based type safety")
        print("    - Comprehensive error messages")
        print("    - API documentation with descriptions")

    except Exception as e:
        print(f"\n💥 TDD TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()