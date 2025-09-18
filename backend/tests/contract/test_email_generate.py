"""
Contract test for POST /email/generate endpoint
Testing email generation according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestEmailGenerateContract:
    """Contract tests for email generation endpoint"""

    def test_generate_email_with_gpt5(self, client: TestClient):
        """Test generating email with GPT-5 nano"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1,
                "use_gpt5": True
            }
        )

        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "user_id" in data
        assert "subject" in data
        assert "html_body" in data
        assert "plain_body" in data
        assert "generated_at" in data
        assert "sections" in data

        # Verify field types
        assert data["user_id"] == 1
        assert isinstance(data["subject"], str)
        assert isinstance(data["html_body"], str)
        assert isinstance(data["plain_body"], str)
        assert isinstance(data["sections"], list)

    def test_generate_email_without_gpt5(self, client: TestClient):
        """Test generating email without GPT-5"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1,
                "use_gpt5": False
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "user_id" in data
        assert "subject" in data
        assert "html_body" in data
        assert "plain_body" in data

    def test_generate_email_default_gpt5(self, client: TestClient):
        """Test generating email with default GPT-5 setting (true)"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "user_id" in data
        assert "subject" in data
        # Default should use GPT-5

    def test_generate_email_sections_structure(self, client: TestClient):
        """Test email sections structure"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        assert response.status_code == 200

        data = response.json()
        sections = data["sections"]
        assert isinstance(sections, list)

        # Check each section structure
        for section in sections:
            assert "section_type" in section
            assert "title" in section
            assert "jobs" in section

            # Verify types
            assert isinstance(section["section_type"], str)
            assert isinstance(section["title"], str)
            assert isinstance(section["jobs"], list)

            # Check job structure in section
            for job in section["jobs"]:
                assert "job_id" in job
                assert "application_name" in job

    def test_generate_email_html_content(self, client: TestClient):
        """Test HTML body content structure"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        assert response.status_code == 200

        data = response.json()
        html_body = data["html_body"]

        # Check that it's valid HTML-like content
        assert isinstance(html_body, str)
        assert len(html_body) > 0

        # Could contain basic HTML tags
        # Note: Actual validation would require HTML parser

    def test_generate_email_plain_content(self, client: TestClient):
        """Test plain text body content"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        assert response.status_code == 200

        data = response.json()
        plain_body = data["plain_body"]

        # Check plain text content
        assert isinstance(plain_body, str)
        assert len(plain_body) > 0

        # Should not contain HTML tags
        assert "<html>" not in plain_body.lower()
        assert "<body>" not in plain_body.lower()

    def test_generate_email_missing_user_id(self, client: TestClient):
        """Test generating email without user_id"""
        response = client.post(
            "/api/v1/email/generate",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_generate_email_invalid_user_id(self, client: TestClient):
        """Test with invalid user ID format"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": "not_a_number"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_email_nonexistent_user(self, client: TestClient):
        """Test generating email for non-existent user"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 999999
            }
        )

        # Could be 200 with empty sections or 404
        assert response.status_code in [200, 404]

    def test_generate_email_timestamp_format(self, client: TestClient):
        """Test generated_at timestamp format"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Verify timestamp format
            assert "generated_at" in data

            # Should be ISO format datetime string
            from datetime import datetime
            try:
                datetime.fromisoformat(data["generated_at"].replace('Z', '+00:00'))
            except ValueError:
                pytest.fail("generated_at is not in valid ISO format")

    def test_generate_email_subject_content(self, client: TestClient):
        """Test email subject content"""
        response = client.post(
            "/api/v1/email/generate",
            json={
                "user_id": 1
            }
        )

        if response.status_code == 200:
            data = response.json()
            subject = data["subject"]

            # Subject should be non-empty and reasonable length
            assert len(subject) > 0
            assert len(subject) < 200  # Reasonable email subject length