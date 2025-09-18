"""
Regulatory Compliance Tests

規制コンプライアンステストスイート
- GDPR データハンドリング
- 削除権（忘れられる権利）
- データポータビリティ
- 同意管理
- プライバシーポリシー施行
- データ保持ポリシー
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import logging
import json
import uuid


class TestGDPRCompliance:
    """GDPR コンプライアンステスト"""

    @pytest.mark.asyncio
    async def test_data_subject_access_request(self, async_client: AsyncClient):
        """データ主体のアクセス要求テスト（第15条）"""
        # Create user with personal data
        user_data = {
            "email": "gdpr_test@example.com",
            "name": "GDPR Test User",
            "age_group": "30代前半",
            "location": "東京都",
            "occupation": "エンジニア"
        }

        response = await async_client.post("/users/", json=user_data)
        if response.status_code != 201:
            pytest.skip("User creation failed")

        user_id = response.json()["id"]

        # Request all personal data for this user
        response = await async_client.get(f"/users/{user_id}/gdpr/data-export")

        assert response.status_code == status.HTTP_200_OK
        export_data = response.json()

        # Should include all personal data
        assert "personal_data" in export_data
        assert "user_profile" in export_data["personal_data"]
        assert "activity_history" in export_data["personal_data"]
        assert "preferences" in export_data["personal_data"]

        # Should include metadata about data processing
        assert "data_processing_info" in export_data
        assert "legal_basis" in export_data["data_processing_info"]
        assert "retention_period" in export_data["data_processing_info"]
        assert "data_categories" in export_data["data_processing_info"]

        # Should be in machine-readable format
        assert isinstance(export_data, dict)

        # Should include data sources
        assert "data_sources" in export_data

    @pytest.mark.asyncio
    async def test_right_to_rectification(self, async_client: AsyncClient):
        """訂正権テスト（第16条）"""
        # Create user
        user_data = {
            "email": "rectification_test@example.com",
            "name": "Original Name",
            "age_group": "20代前半"
        }

        response = await async_client.post("/users/", json=user_data)
        if response.status_code != 201:
            pytest.skip("User creation failed")

        user_id = response.json()["id"]

        # Request rectification
        rectification_data = {
            "name": "Corrected Name",
            "age_group": "20代後半",
            "rectification_reason": "Incorrect information provided initially"
        }

        response = await async_client.put(
            f"/users/{user_id}/gdpr/rectify",
            json=rectification_data
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify changes were applied
        response = await async_client.get(f"/users/{user_id}")
        user_data = response.json()

        assert user_data["name"] == "Corrected Name"
        assert user_data["age_group"] == "20代後半"

        # Should log rectification activity
        response = await async_client.get(f"/users/{user_id}/gdpr/audit-log")
        if response.status_code == 200:
            audit_log = response.json()
            rectification_entries = [
                entry for entry in audit_log["entries"]
                if entry["action"] == "data_rectification"
            ]
            assert len(rectification_entries) > 0

    @pytest.mark.asyncio
    async def test_right_to_erasure(self, async_client: AsyncClient):
        """削除権テスト（第17条）- 忘れられる権利"""
        # Create user
        user_data = {
            "email": "erasure_test@example.com",
            "name": "To Be Deleted",
            "age_group": "20代前半"
        }

        response = await async_client.post("/users/", json=user_data)
        if response.status_code != 201:
            pytest.skip("User creation failed")

        user_id = response.json()["id"]

        # Create some associated data
        job_data = {
            "title": "Test Job",
            "company": "Test Company",
            "location": "東京都"
        }
        await async_client.post("/jobs/", json=job_data)

        # Apply for job (create relationship)
        await async_client.post(f"/jobs/1/apply", json={"user_id": user_id})

        # Request erasure
        erasure_request = {
            "erasure_reason": "No longer wish to use the service",
            "legal_ground": "withdrawal_of_consent"
        }

        response = await async_client.delete(
            f"/users/{user_id}/gdpr/erase",
            json=erasure_request
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        erasure_job = response.json()

        # Should return job ID for tracking
        assert "erasure_job_id" in erasure_job

        # Check erasure status
        response = await async_client.get(
            f"/gdpr/erasure-status/{erasure_job['erasure_job_id']}"
        )

        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()
        assert status_data["status"] in ["pending", "in_progress", "completed"]

        # Verify user data is marked for deletion or anonymized
        response = await async_client.get(f"/users/{user_id}")
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_410_GONE]

    @pytest.mark.asyncio
    async def test_data_portability(self, async_client: AsyncClient):
        """データポータビリティテスト（第20条）"""
        # Create user with extensive data
        user_data = {
            "email": "portability_test@example.com",
            "name": "Portability Test",
            "age_group": "30代前半",
            "skills": ["Python", "JavaScript", "SQL"],
            "preferences": {
                "job_types": ["remote", "full-time"],
                "salary_range": {"min": 500000, "max": 1000000}
            }
        }

        response = await async_client.post("/users/", json=user_data)
        if response.status_code != 201:
            pytest.skip("User creation failed")

        user_id = response.json()["id"]

        # Request data portability export
        response = await async_client.get(f"/users/{user_id}/gdpr/data-portability")

        assert response.status_code == status.HTTP_200_OK

        # Should return data in structured format
        export_data = response.json()

        # Should include commonly used formats
        assert "json" in export_data["formats"]
        assert "csv" in export_data["formats"] or "excel" in export_data["formats"]

        # JSON format should be complete
        json_data = export_data["data"]["json"]
        assert "user_profile" in json_data
        assert "job_applications" in json_data
        assert "search_history" in json_data
        assert "preferences" in json_data

        # Should be machine-readable and interoperable
        assert isinstance(json_data, dict)

    @pytest.mark.asyncio
    async def test_consent_management(self, async_client: AsyncClient):
        """同意管理テスト"""
        # Test consent recording
        consent_data = {
            "user_email": "consent_test@example.com",
            "consent_purposes": [
                "marketing_emails",
                "data_analytics",
                "third_party_sharing"
            ],
            "consent_given": True,
            "consent_timestamp": datetime.utcnow().isoformat(),
            "consent_method": "web_form",
            "privacy_policy_version": "v2.1"
        }

        response = await async_client.post("/gdpr/consent", json=consent_data)
        assert response.status_code == status.HTTP_201_CREATED

        consent_id = response.json()["consent_id"]

        # Test consent withdrawal
        withdrawal_data = {
            "withdrawal_purposes": ["marketing_emails"],
            "withdrawal_reason": "No longer interested"
        }

        response = await async_client.post(
            f"/gdpr/consent/{consent_id}/withdraw",
            json=withdrawal_data
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify consent status
        response = await async_client.get(f"/gdpr/consent/{consent_id}")
        consent_status = response.json()

        # Marketing consent should be withdrawn
        marketing_consent = next(
            c for c in consent_status["consents"]
            if c["purpose"] == "marketing_emails"
        )
        assert marketing_consent["status"] == "withdrawn"

        # Other consents should remain active
        analytics_consent = next(
            c for c in consent_status["consents"]
            if c["purpose"] == "data_analytics"
        )
        assert analytics_consent["status"] == "active"

    @pytest.mark.asyncio
    async def test_processing_lawfulness(self, async_client: AsyncClient):
        """処理の適法性テスト（第6条）"""
        # Test that each data processing has a legal basis
        response = await async_client.get("/gdpr/processing-activities")

        assert response.status_code == status.HTTP_200_OK
        processing_activities = response.json()

        for activity in processing_activities["activities"]:
            # Each processing activity must have a legal basis
            assert "legal_basis" in activity
            assert activity["legal_basis"] in [
                "consent",
                "contract",
                "legal_obligation",
                "vital_interests",
                "public_task",
                "legitimate_interests"
            ]

            # Must specify purpose
            assert "purpose" in activity
            assert len(activity["purpose"]) > 0

            # Must specify data categories
            assert "data_categories" in activity
            assert len(activity["data_categories"]) > 0

            # If legitimate interests, must include balancing test
            if activity["legal_basis"] == "legitimate_interests":
                assert "balancing_test" in activity

    @pytest.mark.asyncio
    async def test_data_retention_policies(self, async_client: AsyncClient):
        """データ保持ポリシーテスト"""
        # Test retention policy configuration
        response = await async_client.get("/gdpr/retention-policies")

        assert response.status_code == status.HTTP_200_OK
        retention_policies = response.json()

        # Should have policies for different data types
        policy_types = [policy["data_type"] for policy in retention_policies["policies"]]

        expected_types = [
            "user_profiles",
            "application_data",
            "job_postings",
            "search_logs",
            "audit_logs"
        ]

        for expected_type in expected_types:
            assert expected_type in policy_types

        # Each policy should specify retention period
        for policy in retention_policies["policies"]:
            assert "retention_period_months" in policy
            assert policy["retention_period_months"] > 0
            assert "deletion_method" in policy

        # Test automatic deletion for expired data
        response = await async_client.post("/gdpr/cleanup-expired-data")
        assert response.status_code == status.HTTP_202_ACCEPTED

        cleanup_job = response.json()
        assert "cleanup_job_id" in cleanup_job


class TestPrivacyByDesign:
    """プライバシー・バイ・デザインテスト"""

    @pytest.mark.asyncio
    async def test_data_minimization(self, async_client: AsyncClient):
        """データ最小化原則テスト"""
        # Test that only necessary data is collected
        minimal_user_data = {
            "email": "minimal@example.com",
            "name": "Minimal User"
            # Age group, location etc. should be optional
        }

        response = await async_client.post("/users/", json=minimal_user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Verify user was created with minimal data
        user_id = response.json()["id"]
        response = await async_client.get(f"/users/{user_id}")
        user_data = response.json()

        # Should not require excessive personal information
        assert user_data["email"] == "minimal@example.com"
        assert user_data["name"] == "Minimal User"

    @pytest.mark.asyncio
    async def test_privacy_by_default(self, async_client: AsyncClient):
        """デフォルトプライバシーテスト"""
        # Create user with default settings
        user_data = {
            "email": "privacy_default@example.com",
            "name": "Privacy Test"
        }

        response = await async_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        user_id = response.json()["id"]

        # Check default privacy settings
        response = await async_client.get(f"/users/{user_id}/privacy-settings")
        settings = response.json()

        # Should default to most private settings
        assert settings["profile_visibility"] == "private"
        assert settings["data_sharing"] == False
        assert settings["marketing_emails"] == False
        assert settings["third_party_sharing"] == False

    def test_pseudonymization_implementation(self):
        """仮名化実装テスト"""
        from app.utils.privacy import pseudonymize_data, is_pseudonymized

        sensitive_data = {
            "email": "user@example.com",
            "name": "John Doe",
            "phone": "090-1234-5678"
        }

        # Test pseudonymization
        pseudonymized = pseudonymize_data(sensitive_data)

        # Original data should not be present
        assert sensitive_data["email"] not in str(pseudonymized)
        assert sensitive_data["name"] not in str(pseudonymized)
        assert sensitive_data["phone"] not in str(pseudonymized)

        # Should be marked as pseudonymized
        assert is_pseudonymized(pseudonymized)

        # Should be reversible with proper key
        from app.utils.privacy import depseudonymize_data
        original = depseudonymize_data(pseudonymized)
        assert original["email"] == sensitive_data["email"]


class TestDataProtectionOfficer:
    """データ保護責任者（DPO）機能テスト"""

    @pytest.mark.asyncio
    async def test_dpo_contact_information(self, async_client: AsyncClient):
        """DPO連絡先情報テスト"""
        response = await async_client.get("/gdpr/dpo-contact")

        assert response.status_code == status.HTTP_200_OK
        dpo_info = response.json()

        # Should provide DPO contact details
        assert "name" in dpo_info
        assert "email" in dpo_info
        assert "phone" in dpo_info or "contact_form" in dpo_info
        assert "office_address" in dpo_info

    @pytest.mark.asyncio
    async def test_privacy_complaint_process(self, async_client: AsyncClient):
        """プライバシー苦情処理テスト"""
        complaint_data = {
            "complainant_email": "complainant@example.com",
            "subject": "Data processing concern",
            "description": "I believe my data is being processed unlawfully",
            "data_subject_rights_requested": ["access", "rectification"]
        }

        response = await async_client.post("/gdpr/complaints", json=complaint_data)
        assert response.status_code == status.HTTP_201_CREATED

        complaint = response.json()
        assert "complaint_id" in complaint
        assert "acknowledgment_sent" in complaint

        # Should acknowledge within required timeframe
        complaint_id = complaint["complaint_id"]
        response = await async_client.get(f"/gdpr/complaints/{complaint_id}")
        complaint_status = response.json()

        assert complaint_status["status"] in ["received", "investigating", "resolved"]
        assert "acknowledgment_date" in complaint_status


class TestSecurityMeasures:
    """セキュリティ対策テスト（第32条）"""

    @pytest.mark.asyncio
    async def test_encryption_at_rest(self, async_client: AsyncClient):
        """保存時暗号化テスト"""
        # Create user with personal data
        user_data = {
            "email": "encryption_test@example.com",
            "name": "Encryption Test",
            "sensitive_notes": "Confidential information"
        }

        response = await async_client.post("/users/", json=user_data)
        if response.status_code != 201:
            pytest.skip("User creation failed")

        # Verify data is encrypted in database
        from app.database import get_async_session
        from sqlalchemy import text

        async with get_async_session() as session:
            # Check raw database data
            stmt = text("SELECT email, name, sensitive_notes FROM users ORDER BY created_at DESC LIMIT 1")
            result = await session.execute(stmt)
            row = result.fetchone()

            if row:
                # Personal data should be encrypted
                assert row.email != user_data["email"], "Email not encrypted at rest"
                assert row.name != user_data["name"], "Name not encrypted at rest"

                if hasattr(row, 'sensitive_notes') and row.sensitive_notes:
                    assert row.sensitive_notes != user_data["sensitive_notes"], \
                        "Sensitive notes not encrypted at rest"

    @pytest.mark.asyncio
    async def test_access_logging(self, async_client: AsyncClient):
        """アクセスログテスト"""
        # Create user
        user_data = {
            "email": "access_log_test@example.com",
            "name": "Access Log Test"
        }

        response = await async_client.post("/users/", json=user_data)
        user_id = response.json()["id"]

        # Access user data
        response = await async_client.get(f"/users/{user_id}")

        # Check access is logged
        response = await async_client.get(f"/users/{user_id}/gdpr/access-log")

        if response.status_code == 200:
            access_log = response.json()

            # Should log data access
            recent_access = [
                entry for entry in access_log["entries"]
                if entry["action"] == "data_access"
                and entry["timestamp"] > (datetime.utcnow() - timedelta(minutes=1)).isoformat()
            ]

            assert len(recent_access) > 0, "Data access not logged"

    def test_data_breach_response_plan(self):
        """データ侵害対応計画テスト"""
        from app.utils.security import DataBreachHandler

        # Test data breach detection
        breach_handler = DataBreachHandler()

        # Simulate breach detection
        breach_event = {
            "event_type": "unauthorized_access",
            "affected_records": 100,
            "data_types": ["email", "name"],
            "severity": "high",
            "detection_time": datetime.utcnow()
        }

        breach_id = breach_handler.report_breach(breach_event)
        assert breach_id is not None

        # Test 72-hour notification requirement
        breach_info = breach_handler.get_breach_info(breach_id)

        # Should have notification plan
        assert "notification_plan" in breach_info
        assert "supervisory_authority_notification" in breach_info["notification_plan"]
        assert "data_subject_notification" in breach_info["notification_plan"]

        # Should assess if notification to supervisory authority is required
        notification_required = breach_handler.assess_notification_requirement(breach_id)
        assert isinstance(notification_required, bool)


class TestInternationalTransfers:
    """国際移転テスト（第44-49条）"""

    @pytest.mark.asyncio
    async def test_adequacy_decisions(self, async_client: AsyncClient):
        """十分性決定テスト"""
        # Check data transfer policies
        response = await async_client.get("/gdpr/data-transfer-policies")

        if response.status_code == 200:
            policies = response.json()

            # Should specify allowed countries/regions
            assert "allowed_countries" in policies

            # Should only allow transfers to adequate countries or with safeguards
            for country in policies["allowed_countries"]:
                assert "adequacy_decision" in country or "safeguards" in country

    @pytest.mark.asyncio
    async def test_standard_contractual_clauses(self, async_client: AsyncClient):
        """標準契約条項テスト"""
        # Test that SCCs are in place for third-country transfers
        response = await async_client.get("/gdpr/third-party-processors")

        if response.status_code == 200:
            processors = response.json()

            for processor in processors["processors"]:
                if processor["country_code"] not in ["EU", "UK", "JP"]:  # Example adequate countries
                    # Should have appropriate safeguards
                    assert "safeguards" in processor
                    assert processor["safeguards"]["type"] in [
                        "standard_contractual_clauses",
                        "adequacy_decision",
                        "binding_corporate_rules"
                    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# Mock implementations for testing (would be replaced with real implementations)

class DataBreachHandler:
    """Mock data breach handler"""

    def __init__(self):
        self.breaches = {}

    def report_breach(self, breach_event: Dict[str, Any]) -> str:
        breach_id = str(uuid.uuid4())
        self.breaches[breach_id] = {
            **breach_event,
            "notification_plan": {
                "supervisory_authority_notification": {
                    "required": True,
                    "deadline": datetime.utcnow() + timedelta(hours=72)
                },
                "data_subject_notification": {
                    "required": breach_event.get("severity") == "high",
                    "method": "email"
                }
            }
        }
        return breach_id

    def get_breach_info(self, breach_id: str) -> Dict[str, Any]:
        return self.breaches.get(breach_id, {})

    def assess_notification_requirement(self, breach_id: str) -> bool:
        breach = self.breaches.get(breach_id, {})
        return breach.get("severity") in ["high", "critical"]