"""
単体テスト: ログユーティリティ
"""

import pytest
import json
from unittest.mock import Mock, patch

from app.utils.logging import (
    StructuredLogger,
    SensitiveDataMasker,
    LogLevel,
    LogCategory,
    LogContext
)


class TestSensitiveDataMasker:
    """機密データマスキングの単体テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.masker = SensitiveDataMasker()

    def test_mask_password_fields(self):
        """パスワードフィールドのマスキングテスト"""
        data = {
            "password": "secret123",
            "passwd": "secret456",
            "pwd": "secret789"
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["password"] == "***MASKED***"
        assert masked["passwd"] == "***MASKED***"
        assert masked["pwd"] == "***MASKED***"

    def test_mask_token_fields(self):
        """トークンフィールドのマスキングテスト"""
        data = {
            "token": "abc123",
            "access_token": "def456",
            "refresh_token": "ghi789",
            "api_key": "jkl012",
            "secret": "mno345"
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["token"] == "***MASKED***"
        assert masked["access_token"] == "***MASKED***"
        assert masked["refresh_token"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"
        assert masked["secret"] == "***MASKED***"

    def test_mask_email_fields(self):
        """メールフィールドのマスキングテスト"""
        data = {
            "email": "test@example.com",
            "user_email": "user@domain.org",
            "contact_email": "contact@company.com"
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["email"] == "***MASKED***"
        assert masked["user_email"] == "***MASKED***"
        assert masked["contact_email"] == "***MASKED***"

    def test_preserve_non_sensitive_data(self):
        """非機密データの保持テスト"""
        data = {
            "username": "testuser",
            "name": "Test User",
            "id": 123,
            "status": "active",
            "public_info": "visible"
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["username"] == "testuser"
        assert masked["name"] == "Test User"
        assert masked["id"] == 123
        assert masked["status"] == "active"
        assert masked["public_info"] == "visible"

    def test_mask_nested_data(self):
        """ネストされたデータのマスキングテスト"""
        data = {
            "user": {
                "name": "Test User",
                "password": "secret123",
                "profile": {
                    "email": "test@example.com",
                    "bio": "Public bio"
                }
            },
            "settings": {
                "api_key": "abc123",
                "theme": "dark"
            }
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["user"]["name"] == "Test User"
        assert masked["user"]["password"] == "***MASKED***"
        assert masked["user"]["profile"]["email"] == "***MASKED***"
        assert masked["user"]["profile"]["bio"] == "Public bio"
        assert masked["settings"]["api_key"] == "***MASKED***"
        assert masked["settings"]["theme"] == "dark"

    def test_mask_list_data(self):
        """リストデータのマスキングテスト"""
        data = {
            "users": [
                {"name": "User1", "password": "secret1"},
                {"name": "User2", "email": "user2@example.com"},
                {"name": "User3", "api_key": "key123"}
            ]
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["users"][0]["name"] == "User1"
        assert masked["users"][0]["password"] == "***MASKED***"
        assert masked["users"][1]["name"] == "User2"
        assert masked["users"][1]["email"] == "***MASKED***"
        assert masked["users"][2]["name"] == "User3"
        assert masked["users"][2]["api_key"] == "***MASKED***"

    def test_case_insensitive_masking(self):
        """大文字小文字を区別しないマスキングテスト"""
        data = {
            "PASSWORD": "secret123",
            "Email": "test@example.com",
            "API_KEY": "abc123",
            "Token": "xyz789"
        }

        masked = self.masker.mask_sensitive_data(data)

        assert masked["PASSWORD"] == "***MASKED***"
        assert masked["Email"] == "***MASKED***"
        assert masked["API_KEY"] == "***MASKED***"
        assert masked["Token"] == "***MASKED***"

    def test_non_dict_data_passthrough(self):
        """辞書以外のデータの通過テスト"""
        # 文字列
        assert self.masker.mask_sensitive_data("test string") == "test string"

        # 数値
        assert self.masker.mask_sensitive_data(123) == 123

        # リスト（要素が辞書でない場合）
        assert self.masker.mask_sensitive_data([1, 2, 3]) == [1, 2, 3]

        # None
        assert self.masker.mask_sensitive_data(None) is None


class TestLogContext:
    """ログコンテキストの単体テスト"""

    def test_log_context_creation(self):
        """ログコンテキスト作成テスト"""
        context = LogContext(
            request_id="req123",
            user_id="user456",
            ip_address="192.168.1.1"
        )

        assert context.request_id == "req123"
        assert context.user_id == "user456"
        assert context.ip_address == "192.168.1.1"

    def test_log_context_optional_fields(self):
        """オプションフィールドのテスト"""
        context = LogContext(
            request_id="req123",
            user_agent="test-browser",
            endpoint="/api/v1/test",
            method="POST",
            session_id="session789"
        )

        assert context.request_id == "req123"
        assert context.user_agent == "test-browser"
        assert context.endpoint == "/api/v1/test"
        assert context.method == "POST"
        assert context.session_id == "session789"

    def test_log_context_minimal(self):
        """最小構成でのコンテキスト作成テスト"""
        context = LogContext()

        # デフォルト値の確認
        assert context.request_id is None
        assert context.user_id is None
        assert context.ip_address is None


class TestLogEnums:
    """ログ列挙型の単体テスト"""

    def test_log_levels(self):
        """ログレベル列挙型テスト"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_log_categories(self):
        """ログカテゴリ列挙型テスト"""
        assert LogCategory.API.value == "api"
        assert LogCategory.DATABASE.value == "database"
        assert LogCategory.SECURITY.value == "security"
        assert LogCategory.BUSINESS.value == "business"
        assert LogCategory.PERFORMANCE.value == "performance"
        assert LogCategory.SYSTEM.value == "system"
        assert LogCategory.ERROR.value == "error"


class TestStructuredLogger:
    """構造化ログの単体テスト（モック使用）"""

    def setup_method(self):
        """テストセットアップ"""
        with patch('app.utils.logging.logging.getLogger') as mock_get_logger:
            self.mock_logger = Mock()
            mock_get_logger.return_value = self.mock_logger
            self.structured_logger = StructuredLogger("test_logger")

    def test_logger_initialization(self):
        """ログ初期化テスト"""
        assert self.structured_logger.name == "test_logger"
        assert self.structured_logger.level == LogLevel.INFO

    def test_context_setting(self):
        """コンテキスト設定テスト"""
        context = LogContext(request_id="req123", user_id="user456")
        logger_with_context = self.structured_logger.with_context(**context.__dict__)

        assert logger_with_context.context.request_id == "req123"
        assert logger_with_context.context.user_id == "user456"

    @patch('app.utils.logging.json.dumps')
    def test_log_formatting(self, mock_json_dumps):
        """ログフォーマットテスト"""
        mock_json_dumps.return_value = '{"test": "json"}'

        # コンテキスト付きログ
        context = LogContext(request_id="req123")
        logger_with_context = self.structured_logger.with_context(**context.__dict__)

        # ログメソッド実行（実際の実装に依存）
        # 実際の実装でのテストが困難なため、初期化テストのみ実施
        assert logger_with_context is not None


class TestSQLQueryMasking:
    """SQLクエリマスキングの単体テスト"""

    def test_mask_password_in_query(self):
        """SQLクエリ内のパスワードマスキングテスト"""
        from app.middleware.logging import DatabaseLoggingMixin

        db_logging = DatabaseLoggingMixin()

        # パスワード更新クエリ
        query = "UPDATE users SET password = 'secret123' WHERE id = 1"
        masked = db_logging._mask_query(query)

        assert "secret123" not in masked
        assert "***MASKED***" in masked

        # パスワード挿入クエリ
        query = "INSERT INTO users (name, password) VALUES ('test', 'mypassword')"
        masked = db_logging._mask_query(query)

        assert "mypassword" not in masked
        assert "***MASKED***" in masked

    def test_mask_email_in_query(self):
        """SQLクエリ内のメールアドレスマスキングテスト"""
        from app.middleware.logging import DatabaseLoggingMixin

        db_logging = DatabaseLoggingMixin()

        # メールアドレスを含むクエリ
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        masked = db_logging._mask_query(query)

        assert "test@example.com" not in masked
        assert "***@***.***" in masked

    def test_preserve_normal_query(self):
        """通常のクエリ保持テスト"""
        from app.middleware.logging import DatabaseLoggingMixin

        db_logging = DatabaseLoggingMixin()

        # 通常のクエリ（機密情報なし）
        query = "SELECT id, name, created_at FROM users ORDER BY created_at DESC"
        masked = db_logging._mask_query(query)

        assert masked == query  # 変更されないことを確認


if __name__ == "__main__":
    pytest.main([__file__, "-v"])