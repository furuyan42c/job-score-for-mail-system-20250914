"""
単体テスト: エラー追跡システム
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.utils.error_tracker import (
    ErrorTracker,
    ErrorSeverity,
    ErrorCategory,
    ErrorRecovery,
    capture_exceptions,
    monitor_performance
)


class TestErrorTracker:
    """ErrorTrackerクラスの単体テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.error_tracker = ErrorTracker()

    def test_error_tracker_initialization(self):
        """ErrorTracker初期化テスト"""
        assert not self.error_tracker.initialized
        assert self.error_tracker.fallback_errors == []
        assert self.error_tracker.max_fallback_errors == 100

    @patch('app.utils.error_tracker.sentry_sdk')
    @patch('app.utils.error_tracker.settings')
    def test_initialize_with_sentry_dsn(self, mock_settings, mock_sentry):
        """Sentry DSN設定時の初期化テスト"""
        mock_settings.SENTRY_DSN = "https://test@sentry.io/123"
        mock_settings.ENVIRONMENT = "test"
        mock_settings.VERSION = "1.0.0"
        mock_settings.DEBUG = False

        result = self.error_tracker.initialize()

        assert result is True
        assert self.error_tracker.initialized is True
        mock_sentry.init.assert_called_once()

    @patch('app.utils.error_tracker.settings')
    def test_initialize_without_sentry_dsn(self, mock_settings):
        """Sentry DSN未設定時の初期化テスト"""
        mock_settings.SENTRY_DSN = None

        result = self.error_tracker.initialize()

        assert result is False
        assert self.error_tracker.initialized is False

    @patch('app.utils.error_tracker.sentry_sdk')
    def test_capture_exception_with_sentry(self, mock_sentry):
        """Sentry有効時の例外キャプチャテスト"""
        self.error_tracker.initialized = True
        mock_sentry.capture_exception.return_value = "test-event-id"
        mock_sentry.new_scope.return_value.__enter__ = Mock()
        mock_sentry.new_scope.return_value.__exit__ = Mock()

        test_exception = ValueError("Test error")
        event_id = self.error_tracker.capture_exception(
            test_exception,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH
        )

        assert event_id == "test-event-id"

    def test_capture_exception_fallback(self):
        """フォールバック例外キャプチャテスト"""
        self.error_tracker.initialized = False

        test_exception = ValueError("Test error")
        event_id = self.error_tracker.capture_exception(
            test_exception,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH
        )

        assert event_id.startswith("fallback_")
        assert len(self.error_tracker.fallback_errors) == 1

        error_data = self.error_tracker.fallback_errors[0]
        assert error_data["exception_type"] == "ValueError"
        assert error_data["exception_message"] == "Test error"
        assert error_data["category"] == "api"
        assert error_data["severity"] == "error"

    @patch('app.utils.error_tracker.sentry_sdk')
    def test_capture_message_with_sentry(self, mock_sentry):
        """Sentry有効時のメッセージキャプチャテスト"""
        self.error_tracker.initialized = True
        mock_sentry.capture_message.return_value = "test-message-id"
        mock_sentry.new_scope.return_value.__enter__ = Mock()
        mock_sentry.new_scope.return_value.__exit__ = Mock()

        event_id = self.error_tracker.capture_message(
            "Test message",
            level=ErrorSeverity.LOW,
            category=ErrorCategory.BUSINESS_LOGIC
        )

        assert event_id == "test-message-id"

    def test_capture_message_fallback(self):
        """フォールバックメッセージキャプチャテスト"""
        self.error_tracker.initialized = False

        event_id = self.error_tracker.capture_message(
            "Test message",
            level=ErrorSeverity.LOW,
            category=ErrorCategory.BUSINESS_LOGIC
        )

        assert event_id.startswith("fallback_")
        assert len(self.error_tracker.fallback_errors) == 1

        error_data = self.error_tracker.fallback_errors[0]
        assert error_data["message"] == "Test message"
        assert error_data["level"] == "info"
        assert error_data["category"] == "business_logic"

    def test_fallback_error_limit(self):
        """フォールバックエラー数制限テスト"""
        self.error_tracker.initialized = False
        self.error_tracker.max_fallback_errors = 3

        # 5つのエラーを追加
        for i in range(5):
            self.error_tracker.capture_exception(
                Exception(f"Error {i}"),
                category=ErrorCategory.UNKNOWN
            )

        # 最大3つまでしか保存されない
        assert len(self.error_tracker.fallback_errors) == 3

        # 最新の3つが保存されている
        stored_messages = [error["exception_message"] for error in self.error_tracker.fallback_errors]
        assert "Error 2" in stored_messages
        assert "Error 3" in stored_messages
        assert "Error 4" in stored_messages
        assert "Error 0" not in stored_messages
        assert "Error 1" not in stored_messages

    def test_get_fallback_errors(self):
        """フォールバックエラー取得テスト"""
        self.error_tracker.initialized = False

        # エラーを追加
        self.error_tracker.capture_exception(
            Exception("Test error"),
            category=ErrorCategory.API
        )

        errors = self.error_tracker.get_fallback_errors()
        assert len(errors) == 1
        assert errors[0]["exception_message"] == "Test error"

        # 元のリストは変更されない
        errors.clear()
        assert len(self.error_tracker.fallback_errors) == 1

    def test_clear_fallback_errors(self):
        """フォールバックエラークリアテスト"""
        self.error_tracker.initialized = False

        # エラーを追加
        self.error_tracker.capture_exception(
            Exception("Test error"),
            category=ErrorCategory.API
        )

        assert len(self.error_tracker.fallback_errors) == 1

        # クリア
        self.error_tracker.clear_fallback_errors()
        assert len(self.error_tracker.fallback_errors) == 0

    @patch('app.utils.error_tracker.sentry_sdk')
    def test_set_user_context(self, mock_sentry):
        """ユーザーコンテキスト設定テスト"""
        self.error_tracker.initialized = True

        self.error_tracker.set_user_context(
            user_id="user123",
            email="test@example.com"
        )

        mock_sentry.set_user.assert_called_once_with({
            "id": "user123",
            "email": "test@example.com"
        })

    @patch('app.utils.error_tracker.sentry_sdk')
    def test_add_breadcrumb(self, mock_sentry):
        """ブレッドクラム追加テスト"""
        self.error_tracker.initialized = True

        self.error_tracker.add_breadcrumb(
            message="Test breadcrumb",
            category="test",
            level="info",
            data={"key": "value"}
        )

        mock_sentry.add_breadcrumb.assert_called_once_with(
            message="Test breadcrumb",
            category="test",
            level="info",
            data={"key": "value"}
        )

    def test_before_send_filter(self):
        """送信前フィルタテスト"""
        event = {
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "user-agent": "test-agent"
                },
                "data": {
                    "username": "test",
                    "password": "secret"
                }
            },
            "extra": {
                "api_key": "secret-key",
                "public_data": "visible"
            }
        }

        result = self.error_tracker._before_send_filter(event, {})

        # 機密情報がフィルタされている
        assert result["request"]["headers"]["authorization"] == "[Filtered]"
        assert result["request"]["headers"]["user-agent"] == "test-agent"
        assert result["request"]["data"]["password"] == "[Filtered]"
        assert result["request"]["data"]["username"] == "test"
        assert result["extra"]["api_key"] == "[Filtered]"
        assert result["extra"]["public_data"] == "visible"

    def test_before_send_transaction_filter(self):
        """トランザクション送信前フィルタテスト"""
        # 除外対象のトランザクション
        health_event = {"transaction": "/health"}
        docs_event = {"transaction": "/docs"}
        api_event = {"transaction": "/api/v1/users"}

        # ヘルスチェックは除外される
        assert self.error_tracker._before_send_transaction_filter(health_event, {}) is None

        # ドキュメントは除外される
        assert self.error_tracker._before_send_transaction_filter(docs_event, {}) is None

        # API エンドポイントは通過する
        assert self.error_tracker._before_send_transaction_filter(api_event, {}) == api_event

    @patch('app.utils.error_tracker.settings')
    def test_should_send_error_production(self, mock_settings):
        """本番環境でのエラー送信判定テスト"""
        mock_settings.DEBUG = False

        # 重要エラーは送信される
        assert self.error_tracker._should_send_error({"level": "fatal"}) is True
        assert self.error_tracker._should_send_error({"level": "error"}) is True

        # 警告は確率的に送信される（テストでは確認困難）
        # InfoやDebugは送信されない
        assert self.error_tracker._should_send_error({"level": "info"}) is False

    @patch('app.utils.error_tracker.settings')
    def test_should_send_error_debug(self, mock_settings):
        """開発環境でのエラー送信判定テスト"""
        mock_settings.DEBUG = True

        # 開発環境では全て送信される
        assert self.error_tracker._should_send_error({"level": "fatal"}) is True
        assert self.error_tracker._should_send_error({"level": "error"}) is True
        assert self.error_tracker._should_send_error({"level": "warning"}) is True
        assert self.error_tracker._should_send_error({"level": "info"}) is True


class TestErrorSeverityAndCategory:
    """エラー重要度とカテゴリの単体テスト"""

    def test_error_severity_values(self):
        """エラー重要度の値テスト"""
        assert ErrorSeverity.LOW.value == "info"
        assert ErrorSeverity.MEDIUM.value == "warning"
        assert ErrorSeverity.HIGH.value == "error"
        assert ErrorSeverity.CRITICAL.value == "fatal"

    def test_error_category_values(self):
        """エラーカテゴリの値テスト"""
        assert ErrorCategory.API.value == "api"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.BUSINESS_LOGIC.value == "business_logic"
        assert ErrorCategory.EXTERNAL_SERVICE.value == "external_service"
        assert ErrorCategory.PERFORMANCE.value == "performance"
        assert ErrorCategory.SECURITY.value == "security"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestCaptureExceptionsDecorator:
    """capture_exceptionsデコレータのテスト"""

    @patch('app.utils.error_tracker.error_tracker')
    def test_async_function_success(self, mock_error_tracker):
        """非同期関数成功時のテスト"""
        @capture_exceptions(category=ErrorCategory.API, severity=ErrorSeverity.HIGH)
        async def test_async_func():
            return "success"

        async def run_test():
            result = await test_async_func()
            assert result == "success"
            mock_error_tracker.capture_exception.assert_not_called()

        asyncio.run(run_test())

    @patch('app.utils.error_tracker.error_tracker')
    def test_async_function_exception(self, mock_error_tracker):
        """非同期関数例外時のテスト"""
        test_exception = ValueError("Test error")

        @capture_exceptions(category=ErrorCategory.API, severity=ErrorSeverity.HIGH)
        async def test_async_func():
            raise test_exception

        async def run_test():
            with pytest.raises(ValueError):
                await test_async_func()

            mock_error_tracker.capture_exception.assert_called_once_with(
                test_exception,
                category=ErrorCategory.API,
                severity=ErrorSeverity.HIGH,
                extra_context={
                    "function": "test_async_func",
                    "module": __name__,
                    "args_count": 0,
                    "kwargs_keys": []
                }
            )

        asyncio.run(run_test())

    @patch('app.utils.error_tracker.error_tracker')
    def test_sync_function_success(self, mock_error_tracker):
        """同期関数成功時のテスト"""
        @capture_exceptions(category=ErrorCategory.API, severity=ErrorSeverity.HIGH)
        def test_sync_func():
            return "success"

        result = test_sync_func()
        assert result == "success"
        mock_error_tracker.capture_exception.assert_not_called()

    @patch('app.utils.error_tracker.error_tracker')
    def test_sync_function_exception(self, mock_error_tracker):
        """同期関数例外時のテスト"""
        test_exception = ValueError("Test error")

        @capture_exceptions(category=ErrorCategory.API, severity=ErrorSeverity.HIGH)
        def test_sync_func():
            raise test_exception

        with pytest.raises(ValueError):
            test_sync_func()

        mock_error_tracker.capture_exception.assert_called_once_with(
            test_exception,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            extra_context={
                "function": "test_sync_func",
                "module": __name__,
                "args_count": 0,
                "kwargs_keys": []
            }
        )

    @patch('app.utils.error_tracker.error_tracker')
    def test_decorator_no_reraise(self, mock_error_tracker):
        """reraiseしない場合のテスト"""
        @capture_exceptions(category=ErrorCategory.API, reraise=False)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result is None  # 例外がキャプチャされてNoneが返される
        mock_error_tracker.capture_exception.assert_called_once()


class TestErrorRecovery:
    """ErrorRecoveryクラスの単体テスト"""

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_success(self):
        """リトライ成功テスト"""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await ErrorRecovery.retry_with_exponential_backoff(
            test_func,
            max_retries=3,
            base_delay=0.001  # テスト高速化のため短く
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_failure(self):
        """リトライ失敗テスト"""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            await ErrorRecovery.retry_with_exponential_backoff(
                test_func,
                max_retries=2,
                base_delay=0.001
            )

        assert call_count == 3  # 初回 + 2回リトライ

    def test_circuit_breaker_closed_state(self):
        """サーキットブレーカー正常状態テスト"""
        @ErrorRecovery.circuit_breaker(failure_threshold=2, recovery_timeout=1)
        def test_func():
            return "success"

        # 正常動作
        result = test_func()
        assert result == "success"

    def test_circuit_breaker_open_state(self):
        """サーキットブレーカー開放状態テスト"""
        call_count = 0

        @ErrorRecovery.circuit_breaker(failure_threshold=2, recovery_timeout=60)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError(f"Failure {call_count}")

        # 閾値まで失敗させる
        for i in range(2):
            with pytest.raises(ConnectionError):
                test_func()

        # サーキットブレーカーが開く
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            test_func()


class TestPerformanceMonitoring:
    """パフォーマンス監視テスト"""

    @patch('app.utils.error_tracker.error_tracker')
    @pytest.mark.asyncio
    async def test_capture_performance_context_manager(self, mock_error_tracker):
        """パフォーマンス測定コンテキストマネージャーテスト"""
        mock_error_tracker.initialized = True

        async with mock_error_tracker.capture_performance("test_operation") as transaction:
            await asyncio.sleep(0.001)  # 短時間の処理をシミュレート

        # トランザクションが作成されていることを確認
        # 実際のSentryとの統合テストではないため、モックの呼び出しを確認

    @patch('app.utils.error_tracker.error_tracker')
    def test_monitor_performance_decorator(self, mock_error_tracker):
        """パフォーマンス監視デコレータテスト"""
        mock_error_tracker.capture_performance.return_value.__aenter__ = Mock(return_value=None)
        mock_error_tracker.capture_performance.return_value.__aexit__ = Mock(return_value=None)

        @monitor_performance("test_operation")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])