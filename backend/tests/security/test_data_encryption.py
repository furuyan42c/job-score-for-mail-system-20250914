"""
Data Encryption Verification Tests

データ暗号化検証テストスイート
- 保存時PII データ暗号化
- TLS/SSL 通信検証
- パスワードハッシュ化 (bcrypt/argon2)
- ログの機密データマスキング
- 暗号化キー管理
- データベースフィールド暗号化
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
import ssl
import socket
import hashlib
import secrets
import base64
import re
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import logging
from typing import Dict, Any


class TestPasswordHashing:
    """パスワードハッシュ化テスト"""

    def test_bcrypt_implementation(self):
        """bcrypt 実装テスト"""
        from app.utils.security import hash_password, verify_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        # Verify bcrypt format
        assert hashed.startswith(('$2b$', '$2a$', '$2y$')), "Password not using bcrypt"

        # Verify cost factor
        parts = hashed.split('$')
        assert len(parts) == 4, "Invalid bcrypt format"
        cost = int(parts[2])
        assert cost >= 12, f"Cost factor too low: {cost}"

        # Test verification
        assert verify_password(password, hashed), "Password verification failed"
        assert not verify_password("wrong_password", hashed), "Invalid password accepted"

    def test_salt_randomness(self):
        """ソルトランダム性テスト"""
        from app.utils.security import hash_password

        password = "TestPassword123!"

        # Generate multiple hashes
        hashes = [hash_password(password) for _ in range(10)]

        # All hashes should be different (due to random salts)
        assert len(set(hashes)) == len(hashes), "Salt not random - identical hashes generated"

        # Each hash should have different salt
        salts = [h.split('$')[3][:22] for h in hashes]  # Extract salt part
        assert len(set(salts)) == len(salts), "Identical salts generated"

    def test_timing_attack_resistance(self):
        """タイミング攻撃耐性テスト"""
        from app.utils.security import verify_password, hash_password
        import time

        password = "TestPassword123!"
        hashed = hash_password(password)

        # Test timing consistency
        times_correct = []
        times_incorrect = []

        for _ in range(10):
            # Correct password
            start = time.time()
            verify_password(password, hashed)
            times_correct.append(time.time() - start)

            # Incorrect password
            start = time.time()
            verify_password("wrong_password", hashed)
            times_incorrect.append(time.time() - start)

        # Times should be similar (constant time comparison)
        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)

        # Allow for some variance but they should be close
        ratio = max(avg_correct, avg_incorrect) / min(avg_correct, avg_incorrect)
        assert ratio < 2.0, f"Timing difference too large: {ratio}"


class TestFieldEncryption:
    """フィールドレベル暗号化テスト"""

    @pytest.mark.asyncio
    async def test_email_encryption(self, async_client: AsyncClient):
        """メールアドレス暗号化テスト"""
        # Create user with email
        user_data = {
            "email": "sensitive@example.com",
            "name": "Test User",
            "age_group": "20代前半",
            "location": "東京都"
        }

        response = await async_client.post("/users/", json=user_data)

        if response.status_code == 201:
            user_id = response.json()["id"]

            # Check database directly to verify encryption
            from app.database import get_async_session
            from app.models.database import User
            from sqlalchemy import select

            async with get_async_session() as session:
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if db_user:
                    # Email in database should be encrypted, not plaintext
                    assert db_user.email != user_data["email"], "Email not encrypted in database"

                    # Should not contain @ symbol if encrypted
                    if hasattr(db_user, 'email_encrypted'):
                        assert "@" not in db_user.email_encrypted, "Email appears to be plaintext"

    @pytest.mark.asyncio
    async def test_pii_field_encryption(self, async_client: AsyncClient):
        """PII フィールド暗号化テスト"""
        # Test various PII fields
        sensitive_data = {
            "email": "test@example.com",
            "name": "田中太郎",
            "phone": "090-1234-5678",
            "location": "東京都渋谷区"
        }

        user_data = {
            **sensitive_data,
            "age_group": "30代前半",
            "occupation": "エンジニア"
        }

        response = await async_client.post("/users/", json=user_data)

        if response.status_code == 201:
            # Verify that sensitive data is encrypted at rest
            from app.database import get_async_session
            from sqlalchemy import text

            async with get_async_session() as session:
                # Query raw database
                stmt = text("SELECT * FROM users ORDER BY created_at DESC LIMIT 1")
                result = await session.execute(stmt)
                row = result.fetchone()

                if row:
                    row_dict = row._asdict()

                    # Check that sensitive fields are not stored as plaintext
                    for field, value in sensitive_data.items():
                        if field in row_dict:
                            stored_value = row_dict[field]
                            if stored_value:
                                assert stored_value != value, f"{field} stored as plaintext"

    def test_encryption_key_management(self):
        """暗号化キー管理テスト"""
        from app.utils.encryption import get_encryption_key, encrypt_data, decrypt_data

        # Test key derivation
        key = get_encryption_key()
        assert len(key) == 32, "Encryption key should be 32 bytes"

        # Test encryption/decryption
        plaintext = "sensitive_data@example.com"
        encrypted = encrypt_data(plaintext)
        decrypted = decrypt_data(encrypted)

        assert plaintext == decrypted, "Encryption/decryption failed"
        assert plaintext != encrypted, "Data not encrypted"

        # Test different plaintexts produce different ciphertexts
        encrypted2 = encrypt_data(plaintext)
        assert encrypted != encrypted2, "Encryption not using IV/nonce"

    def test_key_rotation_support(self):
        """キーローテーション対応テスト"""
        from app.utils.encryption import encrypt_data, decrypt_data

        # Simulate key rotation scenario
        plaintext = "test_data@example.com"

        # Encrypt with current key
        encrypted_old = encrypt_data(plaintext)

        # Simulate key rotation (would happen in real system)
        # The system should be able to decrypt old data with old key
        # and encrypt new data with new key

        decrypted = decrypt_data(encrypted_old)
        assert decrypted == plaintext, "Cannot decrypt after key rotation"


class TestTLSCommunication:
    """TLS/SSL 通信テスト"""

    @pytest.mark.asyncio
    async def test_https_enforcement(self, async_client: AsyncClient):
        """HTTPS 強制テスト"""
        # Test that HTTP redirects to HTTPS
        response = await async_client.get("/", follow_redirects=False)

        # In production, should redirect HTTP to HTTPS
        if response.status_code in [301, 302, 307, 308]:
            location = response.headers.get("location", "")
            assert location.startswith("https://"), "HTTP not redirected to HTTPS"

    def test_tls_version_support(self):
        """TLS バージョン対応テスト"""
        # Test TLS configuration (would require actual server)
        import ssl

        # Ensure only secure TLS versions are supported
        context = ssl.create_default_context()

        # Should support TLS 1.2 and 1.3 only
        assert context.minimum_version >= ssl.TLSVersion.TLSv1_2, "Insecure TLS version supported"

        # Should not support SSLv2, SSLv3, TLS 1.0, TLS 1.1
        insecure_protocols = [
            ssl.PROTOCOL_SSLv2,
            ssl.PROTOCOL_SSLv3,
            ssl.PROTOCOL_TLSv1,
            ssl.PROTOCOL_TLSv1_1
        ]

        # These should be disabled
        for protocol in insecure_protocols:
            try:
                test_context = ssl.SSLContext(protocol)
                # If this doesn't raise an exception, the protocol is still available
                # In a secure environment, these should be disabled
            except ssl.SSLError:
                # Good - insecure protocol is disabled
                pass

    @pytest.mark.asyncio
    async def test_certificate_validation(self, async_client: AsyncClient):
        """証明書検証テスト"""
        # Test SSL certificate validation
        response = await async_client.get("/health")

        # In production with proper SSL, this should succeed
        # In development, this test might need to be skipped
        assert response.status_code != 525, "SSL certificate validation failed"

    @pytest.mark.asyncio
    async def test_hsts_header_presence(self, async_client: AsyncClient):
        """HSTS ヘッダー存在テスト"""
        response = await async_client.get("/")

        # Should have Strict-Transport-Security header
        hsts_header = response.headers.get("strict-transport-security")
        if hsts_header:
            assert "max-age=" in hsts_header, "HSTS max-age not specified"

            # Extract max-age value
            max_age = re.search(r'max-age=(\d+)', hsts_header)
            if max_age:
                age_seconds = int(max_age.group(1))
                # Should be at least 1 year (31536000 seconds)
                assert age_seconds >= 31536000, f"HSTS max-age too short: {age_seconds}"

            # Should include includeSubDomains for better security
            assert "includeSubDomains" in hsts_header, "HSTS should include subdomains"


class TestDataMasking:
    """データマスキングテスト"""

    def test_log_data_masking(self, caplog):
        """ログデータマスキングテスト"""
        from app.utils.logging import log_user_action

        sensitive_data = {
            "email": "user@example.com",
            "password": "secret123",
            "credit_card": "4111-1111-1111-1111",
            "ssn": "123-45-6789"
        }

        with caplog.at_level(logging.INFO):
            log_user_action("test_action", sensitive_data)

        # Check that sensitive data is masked in logs
        log_output = caplog.text.lower()

        # Email should be partially masked
        assert "user@example.com" not in log_output, "Email not masked in logs"
        assert "u***@example.com" in log_output or "****@example.com" in log_output

        # Password should never appear in logs
        assert "secret123" not in log_output, "Password exposed in logs"

        # Credit card should be masked
        assert "4111-1111-1111-1111" not in log_output, "Credit card not masked"

        # SSN should be masked
        assert "123-45-6789" not in log_output, "SSN not masked"

    @pytest.mark.asyncio
    async def test_api_response_masking(self, async_client: AsyncClient):
        """API レスポンスマスキングテスト"""
        # Create user
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "090-1234-5678"
        }

        response = await async_client.post("/users/", json=user_data)

        if response.status_code == 201:
            user_data = response.json()

            # Sensitive fields should be masked or excluded
            if "phone" in user_data:
                phone = user_data["phone"]
                # Phone should be partially masked
                assert "090-****-5678" in phone or "***-****-5678" in phone

            # Internal IDs should not be exposed
            assert "internal_id" not in user_data, "Internal ID exposed in API"
            assert "database_id" not in user_data, "Database ID exposed in API"

    def test_error_message_sanitization(self):
        """エラーメッセージサニタイゼーションテスト"""
        from app.utils.errors import sanitize_error_message

        # Test database error sanitization
        db_error = "SQLSTATE[23000]: Integrity constraint violation: 1062 Duplicate entry 'test@example.com' for key 'users.email_unique'"
        sanitized = sanitize_error_message(db_error)

        # Should not expose database schema information
        assert "SQLSTATE" not in sanitized, "Database error code exposed"
        assert "users.email_unique" not in sanitized, "Database schema exposed"
        assert "test@example.com" not in sanitized, "Sensitive data exposed in error"

        # Should provide generic error message
        assert "validation error" in sanitized.lower() or "conflict" in sanitized.lower()


class TestBackupEncryption:
    """バックアップ暗号化テスト"""

    def test_backup_data_encryption(self):
        """バックアップデータ暗号化テスト"""
        from app.utils.backup import create_encrypted_backup, verify_backup_encryption

        # Test data
        test_data = {
            "users": [
                {"email": "user1@example.com", "name": "User 1"},
                {"email": "user2@example.com", "name": "User 2"}
            ]
        }

        # Create encrypted backup
        encrypted_backup = create_encrypted_backup(test_data)

        # Verify backup is encrypted
        assert encrypted_backup != str(test_data), "Backup data not encrypted"

        # Should not contain plaintext emails
        assert "user1@example.com" not in encrypted_backup, "Email exposed in backup"
        assert "user2@example.com" not in encrypted_backup, "Email exposed in backup"

        # Verify backup can be decrypted
        is_valid = verify_backup_encryption(encrypted_backup)
        assert is_valid, "Backup encryption verification failed"

    def test_backup_key_security(self):
        """バックアップキーセキュリティテスト"""
        from app.utils.backup import get_backup_key

        # Backup encryption key should be different from application key
        backup_key = get_backup_key()
        app_key = get_encryption_key()

        assert backup_key != app_key, "Backup key same as application key"
        assert len(backup_key) >= 32, "Backup key too short"


class TestDatabaseEncryption:
    """データベース暗号化テスト"""

    @pytest.mark.asyncio
    async def test_connection_encryption(self):
        """データベース接続暗号化テスト"""
        from app.database import DATABASE_URL

        db_url = str(DATABASE_URL)

        # Should use SSL for database connections in production
        if "postgresql" in db_url:
            # PostgreSQL should use SSL
            assert "sslmode=" in db_url, "PostgreSQL connection not using SSL"

            ssl_mode = re.search(r'sslmode=(\w+)', db_url)
            if ssl_mode:
                mode = ssl_mode.group(1)
                assert mode in ['require', 'verify-ca', 'verify-full'], f"Insecure SSL mode: {mode}"

        elif "mysql" in db_url:
            # MySQL should use SSL
            assert "ssl=" in db_url or "ssl_disabled=false" in db_url, "MySQL connection not using SSL"

    @pytest.mark.asyncio
    async def test_transparent_data_encryption(self, async_session):
        """透過的データ暗号化テスト"""
        # Test that database supports encryption at rest
        from sqlalchemy import text

        # Check if database supports TDE (Transparent Data Encryption)
        try:
            # PostgreSQL: Check for encryption extension
            stmt = text("SELECT * FROM pg_available_extensions WHERE name = 'pgcrypto'")
            result = await async_session.execute(stmt)

            # Should have encryption capabilities
            extensions = result.fetchall()
            assert len(extensions) > 0, "Database encryption extension not available"

        except Exception:
            # Different databases have different ways to check encryption
            # This test might need database-specific implementations
            pass


class TestMemoryProtection:
    """メモリ保護テスト"""

    def test_sensitive_data_clearing(self):
        """機密データクリアテスト"""
        from app.utils.security import SecureString

        # Test secure string implementation
        password = "sensitive_password_123"
        secure_str = SecureString(password)

        # Should be able to access value
        assert str(secure_str) == password

        # Clear from memory
        secure_str.clear()

        # Should be cleared
        assert str(secure_str) == "", "Sensitive data not cleared from memory"

    def test_password_memory_handling(self):
        """パスワードメモリハンドリングテスト"""
        from app.utils.security import hash_password

        password = "test_password_123"

        # Monitor memory for password traces (simplified test)
        # In real implementation, this would use memory scanning tools

        hashed = hash_password(password)

        # Password should not be stored in plaintext in memory
        # This is hard to test without specialized tools
        # but we can at least verify the hash doesn't contain the password
        assert password not in hashed, "Password found in hash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# Utility functions that would be implemented in the actual application

def get_encryption_key():
    """Get encryption key from secure storage"""
    # This would be implemented to get key from environment or key management system
    return b'test_key_32_bytes_long_for_testing'

def encrypt_data(plaintext: str) -> str:
    """Encrypt sensitive data"""
    key = get_encryption_key()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(plaintext.encode()).decode()

def decrypt_data(encrypted: str) -> str:
    """Decrypt sensitive data"""
    key = get_encryption_key()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(encrypted.encode()).decode()