#!/usr/bin/env python3
"""
T011: Contract Test for POST /email/generate (RED Phase)

Tests API contract for email generation endpoint including:
- Request validation
- Response schema
- Template processing
- Error handling
"""

import pytest
from httpx import AsyncClient
from app.main import app
import json


class TestEmailGenerateContract:
    """Contract tests for POST /email/generate endpoint"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_generate_email_success(self, client: AsyncClient):
        """Test successful email generation"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "weekly_digest",
            "job_ids": ["job1", "job2", "job3"],
            "personalization": {
                "user_name": "Test User",
                "preferences": {"location": "Tokyo"}
            }
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response schema
        assert "email_id" in data
        assert "subject" in data
        assert "body" in data
        assert "template_used" in data
        assert "generated_at" in data
        assert "sections" in data
        assert isinstance(data["sections"], list)

    @pytest.mark.asyncio
    async def test_generate_email_with_sections(self, client: AsyncClient):
        """Test email generation with custom sections"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "custom",
            "sections": [
                {"type": "header", "content": "Welcome!"},
                {"type": "job_list", "job_ids": ["job1", "job2"]},
                {"type": "cta", "button_text": "Apply Now", "url": "https://example.com"},
                {"type": "footer", "content": "Unsubscribe"}
            ]
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sections"]) == 4
        assert data["sections"][0]["type"] == "header"

    @pytest.mark.asyncio
    async def test_generate_email_invalid_template(self, client: AsyncClient):
        """Test email generation with invalid template"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "nonexistent_template"
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "template" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_generate_email_missing_user(self, client: AsyncClient):
        """Test email generation with missing user"""
        request_data = {
            "template_type": "weekly_digest"  # Missing user_id
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_generate_email_validation(self, client: AsyncClient):
        """Test request validation"""
        request_data = {
            "user_id": "",  # Empty user_id
            "template_type": "weekly_digest",
            "job_ids": "not_a_list"  # Should be a list
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    @pytest.mark.asyncio
    async def test_generate_email_large_payload(self, client: AsyncClient):
        """Test email generation with large job list"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "weekly_digest",
            "job_ids": [f"job_{i}" for i in range(100)]  # 100 jobs
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        # Should either succeed or return 413 (payload too large)
        assert response.status_code in [200, 413]

    @pytest.mark.asyncio
    async def test_generate_email_preview_mode(self, client: AsyncClient):
        """Test email preview generation"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "weekly_digest",
            "preview_mode": True,
            "job_ids": ["job1"]
        }
        
        response = await client.post("/email/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "preview" in data or "is_preview" in data
        assert "email_id" not in data or data.get("email_id") is None

    @pytest.mark.asyncio
    async def test_generate_email_idempotency(self, client: AsyncClient):
        """Test idempotency with request ID"""
        request_data = {
            "user_id": "test_user_123",
            "template_type": "weekly_digest",
            "job_ids": ["job1"]
        }
        
        headers = {"X-Request-ID": "unique-request-123"}
        
        # First request
        response1 = await client.post("/email/generate", json=request_data, headers=headers)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Duplicate request with same ID
        response2 = await client.post("/email/generate", json=request_data, headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return same email_id
        assert data1.get("email_id") == data2.get("email_id")

    @pytest.mark.asyncio
    async def test_generate_email_response_time(self, client: AsyncClient):
        """Test response time SLA"""
        import time
        
        request_data = {
            "user_id": "test_user_123",
            "template_type": "weekly_digest",
            "job_ids": ["job1", "job2"]
        }
        
        start = time.time()
        response = await client.post("/email/generate", json=request_data)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0  # Response should be under 3 seconds
