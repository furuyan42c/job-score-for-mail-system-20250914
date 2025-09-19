#!/usr/bin/env python3
"""
T010: Contract Test for GET /matching/user/{id} (RED Phase)

Tests API contract for user matching endpoint including:
- Request validation
- Response schema
- Status codes
- Error handling
"""

import pytest
from httpx import AsyncClient
from app.main import app
import json


class TestMatchingUserContract:
    """Contract tests for GET /matching/user/{id} endpoint"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_get_user_matches_success(self, client: AsyncClient):
        """Test successful user match retrieval"""
        user_id = "test_user_123"
        response = await client.get(f"/matching/user/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response schema
        assert "user_id" in data
        assert "matches" in data
        assert isinstance(data["matches"], list)
        
        if len(data["matches"]) > 0:
            match = data["matches"][0]
            assert "job_id" in match
            assert "match_score" in match
            assert "job_details" in match
            assert 0 <= match["match_score"] <= 100

    @pytest.mark.asyncio
    async def test_get_user_matches_with_filters(self, client: AsyncClient):
        """Test user matches with query parameters"""
        user_id = "test_user_123"
        params = {
            "min_score": 70,
            "max_score": 100,
            "limit": 10,
            "offset": 0,
            "sort_by": "score_desc"
        }
        
        response = await client.get(f"/matching/user/{user_id}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify filtered results
        for match in data["matches"]:
            assert match["match_score"] >= 70
            assert match["match_score"] <= 100

    @pytest.mark.asyncio
    async def test_get_user_matches_not_found(self, client: AsyncClient):
        """Test user not found error"""
        user_id = "nonexistent_user"
        response = await client.get(f"/matching/user/{user_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "user" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_matches_invalid_params(self, client: AsyncClient):
        """Test validation of query parameters"""
        user_id = "test_user_123"
        params = {
            "min_score": -10,  # Invalid: negative score
            "limit": "invalid"  # Invalid: not an integer
        }
        
        response = await client.get(f"/matching/user/{user_id}", params=params)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_matches_pagination(self, client: AsyncClient):
        """Test pagination in user matches"""
        user_id = "test_user_123"
        
        # First page
        response1 = await client.get(
            f"/matching/user/{user_id}",
            params={"limit": 5, "offset": 0}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second page
        response2 = await client.get(
            f"/matching/user/{user_id}",
            params={"limit": 5, "offset": 5}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pagination metadata
        assert "total_count" in data1
        assert "has_more" in data1
        assert "limit" in data1
        assert "offset" in data1

    @pytest.mark.asyncio
    async def test_get_user_matches_response_time(self, client: AsyncClient):
        """Test response time SLA"""
        import time
        
        user_id = "test_user_123"
        start = time.time()
        response = await client.get(f"/matching/user/{user_id}")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0  # Response should be under 2 seconds

    @pytest.mark.asyncio
    async def test_get_user_matches_content_type(self, client: AsyncClient):
        """Test response content type"""
        user_id = "test_user_123"
        response = await client.get(f"/matching/user/{user_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_user_matches_auth_required(self, client: AsyncClient):
        """Test authentication requirement"""
        user_id = "test_user_123"
        
        # Without auth header
        response = await client.get(f"/matching/user/{user_id}")
        
        # Should require authentication
        assert response.status_code in [401, 403]
        
        # With auth header
        headers = {"Authorization": "Bearer test_token"}
        response = await client.get(f"/matching/user/{user_id}", headers=headers)
        
        # Should allow with valid auth
        assert response.status_code in [200, 404]  # 404 if user doesn't exist
