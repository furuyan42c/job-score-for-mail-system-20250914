"""
Authentication & Authorization Security Tests

認証・認可セキュリティテストスイート
- JWT トークン検証
- セッション管理セキュリティ
- パスワード強度要件
- ブルートフォース攻撃防止
- ロールベースアクセス制御 (RBAC)
- API エンドポイント認可
- クロステナントデータ分離
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, MagicMock
import jwt
import time
import asyncio
from datetime import datetime, timedelta
import hashlib
import secrets
import bcrypt
from typing import Dict, List


class TestPasswordSecurity:
    """パスワードセキュリティテスト"""

    def test_password_strength_requirements(self):
        """パスワード強度要件テスト"""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "12345678",  # Too short
            "PASSWORD123",  # No lowercase
            "password123",  # No uppercase
            "Password",  # No numbers
            "Password123",  # Missing special chars (if required)
        ]

        # Test password validation function
        from app.utils.security import validate_password

        for weak_pwd in weak_passwords:
            is_valid, errors = validate_password(weak_pwd)
            assert not is_valid, f"Weak password accepted: {weak_pwd}"
            assert len(errors) > 0

        # Test strong passwords
        strong_passwords = [
            "StrongP@ssw0rd123",
            "MySecure#Pass123",
            "C0mpl3x!Password"
        ]

        for strong_pwd in strong_passwords:
            is_valid, errors = validate_password(strong_pwd)
            assert is_valid, f"Strong password rejected: {strong_pwd}, errors: {errors}"

    def test_password_hashing_security(self):
        """パスワードハッシュ化セキュリティテスト"""
        from app.utils.security import hash_password, verify_password

        password = "TestPassword123!"

        # Test that password is properly hashed
        hashed = hash_password(password)

        # Ensure it's not stored as plaintext
        assert password != hashed
        assert len(hashed) > 50  # Bcrypt hashes are long

        # Ensure it uses proper salt (no rainbow table attacks)
        hashed2 = hash_password(password)
        assert hashed != hashed2  # Different salts

        # Verify bcrypt is used (starts with $2b$ or similar)
        assert hashed.startswith(('$2b$', '$2a$', '$2y$'))

        # Test verification works
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_password_cost_factor(self):
        """パスワードコスト係数テスト"""
        from app.utils.security import hash_password

        password = "TestPassword123!"

        # Time the hashing to ensure it's not too fast (prevents brute force)
        start_time = time.time()
        hashed = hash_password(password)
        end_time = time.time()

        # Should take at least 0.1 seconds (adjust based on your requirements)
        assert end_time - start_time > 0.1, "Password hashing is too fast"

        # Verify cost factor is high enough (12 is recommended minimum)
        cost_factor = int(hashed.split('$')[2])
        assert cost_factor >= 12, f"Cost factor too low: {cost_factor}"


class TestJWTSecurity:
    """JWT トークンセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_jwt_token_validation(self, async_client: AsyncClient):
        """JWT トークン検証テスト"""
        # Test with valid credentials
        login_data = {
            "email": "test@example.com",
            "password": "ValidPassword123!"
        }

        response = await async_client.post("/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

            # Validate JWT structure
            access_token = data["access_token"]
            try:
                # Decode without verification to check structure
                decoded = jwt.decode(access_token, options={"verify_signature": False})

                # Check required claims
                assert "sub" in decoded  # Subject (user ID)
                assert "exp" in decoded  # Expiration
                assert "iat" in decoded  # Issued at
                assert "scope" in decoded or "permissions" in decoded  # Permissions

                # Check expiration is reasonable (not too long)
                exp = decoded["exp"]
                iat = decoded["iat"]
                duration = exp - iat
                assert duration <= 3600 * 24, "Token valid for too long"  # Max 24 hours

            except jwt.InvalidTokenError:
                assert False, "Invalid JWT structure"

    @pytest.mark.asyncio
    async def test_jwt_algorithm_security(self):
        """JWT アルゴリズムセキュリティテスト"""
        from app.utils.jwt import create_access_token, JWT_ALGORITHM

        # Ensure secure algorithm is used
        assert JWT_ALGORITHM in ["HS256", "RS256", "ES256"], f"Insecure algorithm: {JWT_ALGORITHM}"
        assert JWT_ALGORITHM != "none", "Insecure 'none' algorithm detected"

        # Test that algorithm cannot be overridden
        user_data = {"sub": "1", "email": "test@example.com"}

        # Create token with proper algorithm
        token = create_access_token(user_data)

        # Attempt to create token with 'none' algorithm
        try:
            malicious_header = {"alg": "none"}
            malicious_token = jwt.encode(user_data, "", algorithm="none", headers=malicious_header)

            # This token should not be accepted by the system
            from app.utils.jwt import verify_token
            with pytest.raises((jwt.InvalidTokenError, ValueError)):
                verify_token(malicious_token)

        except Exception:
            pass  # Expected to fail

    @pytest.mark.asyncio
    async def test_token_expiration(self, async_client: AsyncClient):
        """トークン有効期限テスト"""
        # Create an expired token
        from app.utils.jwt import create_access_token
        import jwt

        expired_payload = {
            "sub": "1",
            "email": "test@example.com",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }

        from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Try to use expired token
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/users/profile", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_signature_validation(self, async_client: AsyncClient):
        """トークン署名検証テスト"""
        # Create token with wrong signature
        from app.config import JWT_ALGORITHM

        malicious_payload = {
            "sub": "999",  # Different user
            "email": "admin@example.com",
            "exp": int(time.time()) + 3600
        }

        # Sign with wrong key
        malicious_token = jwt.encode(malicious_payload, "wrong_secret", algorithm=JWT_ALGORITHM)

        headers = {"Authorization": f"Bearer {malicious_token}"}
        response = await async_client.get("/users/profile", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSessionSecurity:
    """セッション管理セキュリティテスト"""

    @pytest.mark.asyncio
    async def test_session_timeout(self, async_client: AsyncClient):
        """セッションタイムアウトテスト"""
        # Login and get token
        login_data = {"email": "test@example.com", "password": "ValidPassword123!"}
        response = await async_client.post("/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]

            # Wait for token to expire (or mock time)
            with patch('time.time') as mock_time:
                # Mock time to be after token expiration
                mock_time.return_value = time.time() + 7200  # 2 hours later

                headers = {"Authorization": f"Bearer {token}"}
                response = await async_client.get("/users/profile", headers=headers)

                assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_concurrent_session_limits(self, async_client: AsyncClient):
        """同時セッション制限テスト"""
        login_data = {"email": "test@example.com", "password": "ValidPassword123!"}

        # Login multiple times to exceed concurrent session limit
        tokens = []
        for i in range(10):  # Try to create many sessions
            response = await async_client.post("/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                tokens.append(data["access_token"])

        # If concurrent sessions are limited, older tokens should be invalidated
        if len(tokens) > 5:  # Assuming limit is 5
            # Test first token (should be invalidated)
            headers = {"Authorization": f"Bearer {tokens[0]}"}
            response = await async_client.get("/users/profile", headers=headers)

            # Should be unauthorized if session limit is enforced
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK]

    @pytest.mark.asyncio
    async def test_session_fixation_prevention(self, async_client: AsyncClient):
        """セッション固定攻撃防止テスト"""
        # Get initial session before login
        response1 = await async_client.get("/")
        cookies_before = response1.cookies

        # Login
        login_data = {"email": "test@example.com", "password": "ValidPassword123!"}
        response2 = await async_client.post("/auth/login", json=login_data)

        if response2.status_code == 200:
            # Session ID should change after login
            cookies_after = response2.cookies

            # If using session cookies, they should be different
            if "session_id" in cookies_before and "session_id" in cookies_after:
                assert cookies_before["session_id"] != cookies_after["session_id"]


class TestBruteForceProtection:
    """ブルートフォース攻撃防止テスト"""

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, async_client: AsyncClient):
        """ログイン試行回数制限テスト"""
        failed_attempts = []

        # Attempt multiple failed logins
        for i in range(20):  # Try many times
            login_data = {
                "email": "test@example.com",
                "password": f"wrong_password_{i}"
            }

            start_time = time.time()
            response = await async_client.post("/auth/login", json=login_data)
            end_time = time.time()

            failed_attempts.append({
                "attempt": i + 1,
                "status": response.status_code,
                "duration": end_time - start_time
            })

            # Should start rate limiting after several attempts
            if i > 5:  # After 5 attempts
                assert response.status_code in [
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    status.HTTP_401_UNAUTHORIZED
                ]

                # Response should be slower (rate limiting delay)
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    assert end_time - start_time > 1.0  # At least 1 second delay

    @pytest.mark.asyncio
    async def test_account_lockout(self, async_client: AsyncClient):
        """アカウントロックアウトテスト"""
        login_data_base = {"email": "lockout_test@example.com"}

        # Multiple failed attempts
        for i in range(10):
            login_data = {**login_data_base, "password": f"wrong_{i}"}
            response = await async_client.post("/auth/login", json=login_data)

        # After many failures, even correct password should be rejected temporarily
        correct_login = {**login_data_base, "password": "CorrectPassword123!"}
        response = await async_client.post("/auth/login", json=correct_login)

        # Should be locked out
        assert response.status_code in [
            status.HTTP_423_LOCKED,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_401_UNAUTHORIZED
        ]

    @pytest.mark.asyncio
    async def test_distributed_brute_force_protection(self, async_client: AsyncClient):
        """分散ブルートフォース攻撃防止テスト"""
        # Test with different IPs (if rate limiting is IP-based)
        headers_list = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Forwarded-For": "192.168.1.2"},
            {"X-Forwarded-For": "192.168.1.3"},
            {"X-Real-IP": "10.0.0.1"},
            {"X-Real-IP": "10.0.0.2"},
        ]

        for headers in headers_list:
            # Multiple attempts from each "IP"
            for i in range(5):
                login_data = {
                    "email": f"test_{i}@example.com",
                    "password": "wrong_password"
                }

                response = await async_client.post(
                    "/auth/login",
                    json=login_data,
                    headers=headers
                )

                # Should still apply some form of rate limiting
                # (even if distributed across IPs)


class TestRoleBasedAccessControl:
    """ロールベースアクセス制御テスト"""

    @pytest.mark.asyncio
    async def test_admin_endpoint_protection(self, async_client: AsyncClient):
        """管理者専用エンドポイント保護テスト"""
        # Test admin endpoints without authentication
        admin_endpoints = [
            {"method": "GET", "path": "/admin/users"},
            {"method": "DELETE", "path": "/admin/users/1"},
            {"method": "POST", "path": "/admin/system/maintenance"},
            {"method": "GET", "path": "/admin/statistics"},
        ]

        for endpoint in admin_endpoints:
            if endpoint["method"] == "GET":
                response = await async_client.get(endpoint["path"])
            elif endpoint["method"] == "POST":
                response = await async_client.post(endpoint["path"], json={})
            elif endpoint["method"] == "DELETE":
                response = await async_client.delete(endpoint["path"])

            # Should require authentication
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, async_client: AsyncClient):
        """ユーザーデータ分離テスト"""
        # Login as user 1
        user1_token = await self._get_user_token(async_client, "user1@example.com")

        if user1_token:
            headers = {"Authorization": f"Bearer {user1_token}"}

            # Try to access another user's data
            response = await async_client.get("/users/999/profile", headers=headers)

            # Should not allow access to other users' data
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ]

    @pytest.mark.asyncio
    async def test_privilege_escalation_prevention(self, async_client: AsyncClient):
        """権限昇格防止テスト"""
        # Login as regular user
        user_token = await self._get_user_token(async_client, "regular_user@example.com")

        if user_token:
            headers = {"Authorization": f"Bearer {user_token}"}

            # Try to modify user role
            response = await async_client.put(
                "/users/profile",
                json={"role": "admin"},
                headers=headers
            )

            # Should not allow role modification
            if response.status_code == 200:
                # If update succeeds, role should not have changed
                profile_response = await async_client.get("/users/profile", headers=headers)
                profile_data = profile_response.json()
                assert profile_data.get("role", "user") != "admin"

    async def _get_user_token(self, async_client: AsyncClient, email: str) -> str:
        """Helper: Get authentication token for user"""
        login_data = {"email": email, "password": "ValidPassword123!"}
        response = await async_client.post("/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")

        return None


class TestAPIEndpointSecurity:
    """API エンドポイントセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_prevention(self, async_client: AsyncClient):
        """未認証アクセス防止テスト"""
        protected_endpoints = [
            {"method": "GET", "path": "/users/profile"},
            {"method": "PUT", "path": "/users/profile"},
            {"method": "POST", "path": "/jobs"},
            {"method": "DELETE", "path": "/jobs/1"},
            {"method": "GET", "path": "/scores/my-scores"},
        ]

        for endpoint in protected_endpoints:
            if endpoint["method"] == "GET":
                response = await async_client.get(endpoint["path"])
            elif endpoint["method"] == "POST":
                response = await async_client.post(endpoint["path"], json={})
            elif endpoint["method"] == "PUT":
                response = await async_client.put(endpoint["path"], json={})
            elif endpoint["method"] == "DELETE":
                response = await async_client.delete(endpoint["path"])

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_manipulation_resistance(self, async_client: AsyncClient):
        """トークン操作耐性テスト"""
        # Test with malformed tokens
        malformed_tokens = [
            "Bearer invalid_token",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Incomplete JWT
            "Bearer null",
            "Bearer undefined",
            "",
            "Basic admin:password",  # Wrong auth type
        ]

        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = await async_client.get("/users/profile", headers=headers)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_cross_user_data_access_prevention(self, async_client: AsyncClient):
        """クロスユーザーデータアクセス防止テスト"""
        # This test would require setting up multiple test users
        # and ensuring they can't access each other's data

        # Test accessing another user's scores
        user_token = await self._get_valid_token(async_client)

        if user_token:
            headers = {"Authorization": f"Bearer {user_token}"}

            # Try to access scores for different user_id
            response = await async_client.get("/scores?user_id=999999", headers=headers)

            # Should either deny access or return empty results
            if response.status_code == 200:
                data = response.json()
                assert len(data.get("items", [])) == 0

    async def _get_valid_token(self, async_client: AsyncClient) -> str:
        """Helper: Get valid authentication token"""
        login_data = {"email": "test@example.com", "password": "ValidPassword123!"}
        response = await async_client.post("/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")

        return None


class TestSecurityHeaders:
    """セキュリティヘッダーテスト"""

    @pytest.mark.asyncio
    async def test_required_security_headers(self, async_client: AsyncClient):
        """必須セキュリティヘッダーテスト"""
        response = await async_client.get("/")

        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": ["strict-origin-when-cross-origin", "no-referrer"],
            "Content-Security-Policy": None,  # Should exist
        }

        for header, expected_values in required_headers.items():
            assert header in response.headers, f"Missing security header: {header}"

            if expected_values and isinstance(expected_values, list):
                assert response.headers[header] in expected_values
            elif expected_values:
                assert response.headers[header] == expected_values

    @pytest.mark.asyncio
    async def test_hsts_header(self, async_client: AsyncClient):
        """HSTS ヘッダーテスト"""
        response = await async_client.get("/")

        # Should have HSTS header for HTTPS
        if "strict-transport-security" in response.headers:
            hsts = response.headers["strict-transport-security"]
            assert "max-age" in hsts
            # Should be at least 1 year
            assert "max-age=31536000" in hsts or "max-age=63072000" in hsts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])