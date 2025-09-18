"""
Error Tracking and Monitoring
エラー追跡・監視システム

Sentry統合によるエラー監視
- エラー自動キャプチャ
- パフォーマンス監視
- ユーザーコンテキスト追加
- エラー分析・アラート
- リカバリ機能
"""

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    # モックオブジェクトを作成
    class MockSentry:
        @staticmethod
        def init(**kwargs):
            pass
        @staticmethod
        def capture_exception(exception):
            return None
        @staticmethod
        def capture_message(message, level=None):
            return None
        @staticmethod
        def set_user(user_data):
            pass
        @staticmethod
        def add_breadcrumb(**kwargs):
            pass
        @staticmethod
        def set_tag(key, value):
            pass
        @staticmethod
        def new_scope():
            return MockScope()
        @staticmethod
        def start_transaction(**kwargs):
            return MockTransaction()

    class MockScope:
        def __init__(self):
            self.level = None
            self.user = None
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_tag(self, key, value):
            pass
        def set_extra(self, key, value):
            pass

    class MockTransaction:
        def __init__(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_status(self, status):
            pass

    sentry_sdk = MockSentry()
import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from contextlib import asynccontextmanager
import time
import json
from datetime import datetime
from enum import Enum

from app.core.config import settings
import logging


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """エラー重要度"""
    LOW = "info"
    MEDIUM = "warning"
    HIGH = "error"
    CRITICAL = "fatal"


class ErrorCategory(Enum):
    """エラーカテゴリ"""
    API = "api"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UNKNOWN = "unknown"


class ErrorTracker:
    """Sentryベースのエラー追跡システム"""

    def __init__(self):
        self.initialized = False
        self.fallback_errors: List[Dict[str, Any]] = []
        self.max_fallback_errors = 100

    def initialize(self) -> bool:
        """Sentry初期化"""
        try:
            if not SENTRY_AVAILABLE:
                logger.warning("Sentry SDK not available, using fallback error tracking")
                return False

            if not settings.SENTRY_DSN:
                logger.warning("SENTRY_DSN not configured, error tracking disabled")
                return False

            # Sentryの統合設定
            integrations = [
                FastApiIntegration(auto_enable=True),
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ]

            # Sentry初期化
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=integrations,
                traces_sample_rate=0.1,  # パフォーマンストレース
                profiles_sample_rate=0.1,  # プロファイリング
                environment=settings.ENVIRONMENT,
                release=settings.VERSION,
                debug=settings.DEBUG,
                send_default_pii=False,  # 個人情報送信無効
                attach_stacktrace=True,
                max_breadcrumbs=50,
                before_send=self._before_send_filter,
                before_send_transaction=self._before_send_transaction_filter
            )

            # グローバルタグ設定
            sentry_sdk.set_tag("service", "job-matching-system")
            sentry_sdk.set_tag("component", "backend")

            self.initialized = True
            logger.info("Sentry error tracking initialized successfully")

            # 初期化確認のためのテストイベント
            self.capture_message(
                "Sentry initialization completed",
                level=ErrorSeverity.LOW,
                category=ErrorCategory.UNKNOWN
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False

    def _before_send_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """送信前フィルタ（機密情報除去）"""
        try:
            # 機密情報をフィルタ
            if 'request' in event:
                self._sanitize_request_data(event['request'])

            if 'extra' in event:
                self._sanitize_extra_data(event['extra'])

            # エラーレート制限
            if not self._should_send_error(event):
                return None

            return event

        except Exception as e:
            logger.error(f"Error in before_send filter: {e}")
            return event

    def _before_send_transaction_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """トランザクション送信前フィルタ"""
        try:
            # 不要なトランザクションを除外
            transaction_name = event.get('transaction', '')

            # ヘルスチェックなどを除外
            exclude_patterns = ['/health', '/docs', '/favicon.ico', '/openapi.json']
            if any(pattern in transaction_name for pattern in exclude_patterns):
                return None

            return event

        except Exception as e:
            logger.error(f"Error in transaction filter: {e}")
            return event

    def _sanitize_request_data(self, request_data: Dict[str, Any]):
        """リクエストデータの機密情報除去"""
        sensitive_fields = ['password', 'token', 'api_key', 'secret', 'authorization']

        for field in sensitive_fields:
            if field in request_data.get('headers', {}):
                request_data['headers'][field] = '[Filtered]'

            if field in request_data.get('data', {}):
                request_data['data'][field] = '[Filtered]'

    def _sanitize_extra_data(self, extra_data: Dict[str, Any]):
        """追加データの機密情報除去"""
        sensitive_keys = ['password', 'email', 'token', 'key']

        def sanitize_dict(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        data[key] = '[Filtered]'
                    elif isinstance(value, dict):
                        sanitize_dict(value)

        sanitize_dict(extra_data)

    def _should_send_error(self, event: Dict[str, Any]) -> bool:
        """エラー送信判定（レート制限）"""
        # 開発環境では全て送信
        if settings.DEBUG:
            return True

        # 本番環境では重要度によって制限
        level = event.get('level', 'error')
        if level in ['fatal', 'error']:
            return True
        elif level == 'warning':
            # 警告は10%の確率で送信
            import random
            return random.random() < 0.1
        else:
            return False

    def capture_exception(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        user_context: Optional[Dict[str, Any]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """例外キャプチャ"""
        try:
            if not self.initialized:
                return self._fallback_capture_exception(exception, category, severity, extra_context)

            # コンテキスト設定
            with sentry_sdk.new_scope() as scope:
                # カテゴリとレベル
                scope.set_tag("error_category", category.value)
                scope.level = severity.value

                # ユーザーコンテキスト
                if user_context:
                    scope.user = user_context

                # 追加コンテキスト
                if extra_context:
                    for key, value in extra_context.items():
                        scope.set_extra(key, value)

                # タグ
                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                # 例外送信
                event_id = sentry_sdk.capture_exception(exception)

                # ローカルログにも記録
                logger.error(
                    f"Exception captured: {type(exception).__name__}: {str(exception)}",
                    extra={
                        "sentry_event_id": event_id,
                        "error_category": category.value,
                        "severity": severity.value
                    }
                )

                return event_id

        except Exception as e:
            logger.error(f"Failed to capture exception with Sentry: {e}")
            return self._fallback_capture_exception(exception, category, severity, extra_context)

    def capture_message(
        self,
        message: str,
        level: ErrorSeverity = ErrorSeverity.LOW,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        extra_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """メッセージキャプチャ"""
        try:
            if not self.initialized:
                return self._fallback_capture_message(message, level, category, extra_context)

            with sentry_sdk.new_scope() as scope:
                scope.set_tag("message_category", category.value)
                scope.level = level.value

                if extra_context:
                    for key, value in extra_context.items():
                        scope.set_extra(key, value)

                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                event_id = sentry_sdk.capture_message(message, level.value)

                return event_id

        except Exception as e:
            logger.error(f"Failed to capture message with Sentry: {e}")
            return self._fallback_capture_message(message, level, category, extra_context)

    def _fallback_capture_exception(
        self,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """フォールバック例外キャプチャ"""
        fallback_id = f"fallback_{int(time.time() * 1000)}"

        error_data = {
            "id": fallback_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "exception",
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc(),
            "category": category.value,
            "severity": severity.value,
            "extra_context": extra_context or {}
        }

        self._store_fallback_error(error_data)

        # ローカルログ
        logger.error(
            f"Fallback exception capture: {type(exception).__name__}: {str(exception)}",
            extra={"fallback_id": fallback_id, "category": category.value}
        )

        return fallback_id

    def _fallback_capture_message(
        self,
        message: str,
        level: ErrorSeverity,
        category: ErrorCategory,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """フォールバックメッセージキャプチャ"""
        fallback_id = f"fallback_{int(time.time() * 1000)}"

        error_data = {
            "id": fallback_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "message",
            "message": message,
            "level": level.value,
            "category": category.value,
            "extra_context": extra_context or {}
        }

        self._store_fallback_error(error_data)

        return fallback_id

    def _store_fallback_error(self, error_data: Dict[str, Any]):
        """フォールバックエラー保存"""
        self.fallback_errors.append(error_data)

        # 最大数を超えた場合は古いものを削除
        if len(self.fallback_errors) > self.max_fallback_errors:
            self.fallback_errors.pop(0)

    def get_fallback_errors(self) -> List[Dict[str, Any]]:
        """フォールバックエラー取得"""
        return self.fallback_errors.copy()

    def clear_fallback_errors(self):
        """フォールバックエラークリア"""
        self.fallback_errors.clear()

    def set_user_context(self, user_id: str, email: Optional[str] = None, **kwargs):
        """ユーザーコンテキスト設定"""
        if self.initialized:
            sentry_sdk.set_user({
                "id": user_id,
                "email": email,
                **kwargs
            })

    def add_breadcrumb(self, message: str, category: str = "custom", level: str = "info", data: Optional[Dict] = None):
        """ブレッドクラム追加"""
        if self.initialized:
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {}
            )

    @asynccontextmanager
    async def capture_performance(self, operation_name: str, **kwargs):
        """パフォーマンス測定"""
        start_time = time.time()

        if self.initialized:
            with sentry_sdk.start_transaction(op="task", name=operation_name) as transaction:
                try:
                    yield transaction
                except Exception as e:
                    transaction.set_status("internal_error")
                    raise
        else:
            try:
                yield None
            finally:
                duration = time.time() - start_time
                logger.info(f"Performance: {operation_name} took {duration:.3f}s")


def capture_exceptions(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.HIGH,
    reraise: bool = True
):
    """例外キャプチャデコレータ"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_tracker.capture_exception(
                    e,
                    category=category,
                    severity=severity,
                    extra_context={
                        "function": func.__name__,
                        "module": func.__module__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                if reraise:
                    raise
                return None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker.capture_exception(
                    e,
                    category=category,
                    severity=severity,
                    extra_context={
                        "function": func.__name__,
                        "module": func.__module__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                if reraise:
                    raise
                return None

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_performance(operation_name: Optional[str] = None):
    """パフォーマンス監視デコレータ"""
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with error_tracker.capture_performance(op_name):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import asyncio
            async def _async_func():
                async with error_tracker.capture_performance(op_name):
                    return func(*args, **kwargs)

            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_async_func())
            except RuntimeError:
                # イベントループが実行されていない場合
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class ErrorRecovery:
    """エラーリカバリ機能"""

    @staticmethod
    async def retry_with_exponential_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: tuple = (Exception,)
    ):
        """指数バックオフでリトライ"""
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()

            except exceptions as e:
                if attempt == max_retries:
                    error_tracker.capture_exception(
                        e,
                        category=ErrorCategory.UNKNOWN,
                        severity=ErrorSeverity.HIGH,
                        extra_context={
                            "retry_attempt": attempt,
                            "max_retries": max_retries,
                            "function": func.__name__ if hasattr(func, '__name__') else str(func)
                        }
                    )
                    raise

                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Retrying {func.__name__} after {delay}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)

    @staticmethod
    def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
        """サーキットブレーカーパターン"""
        class CircuitBreaker:
            def __init__(self):
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def __call__(self, func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._call_with_circuit_breaker(func, args, kwargs)

                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(self._call_with_circuit_breaker(func, args, kwargs))
                    except RuntimeError:
                        return self._sync_call_with_circuit_breaker(func, args, kwargs)

                if asyncio.iscoroutinefunction(func):
                    return async_wrapper
                else:
                    return sync_wrapper

            async def _call_with_circuit_breaker(self, func, args, kwargs):
                if self.state == "OPEN":
                    if time.time() - self.last_failure_time > recovery_timeout:
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    if self.state == "HALF_OPEN":
                        self.state = "CLOSED"
                        self.failure_count = 0

                    return result

                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= failure_threshold:
                        self.state = "OPEN"

                    error_tracker.capture_exception(
                        e,
                        category=ErrorCategory.EXTERNAL_SERVICE,
                        severity=ErrorSeverity.MEDIUM,
                        extra_context={
                            "circuit_breaker_state": self.state,
                            "failure_count": self.failure_count
                        }
                    )
                    raise

            def _sync_call_with_circuit_breaker(self, func, args, kwargs):
                # 同期版の実装（簡略化）
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.failure_count += 1
                    error_tracker.capture_exception(e, category=ErrorCategory.EXTERNAL_SERVICE)
                    raise

        return CircuitBreaker()


# グローバルインスタンス
error_tracker = ErrorTracker()


# 便利な関数
def init_error_tracking() -> bool:
    """エラー追跡初期化"""
    return error_tracker.initialize()


def capture_exception(exception: Exception, **kwargs) -> Optional[str]:
    """例外キャプチャ（グローバル関数）"""
    return error_tracker.capture_exception(exception, **kwargs)


def capture_message(message: str, **kwargs) -> Optional[str]:
    """メッセージキャプチャ（グローバル関数）"""
    return error_tracker.capture_message(message, **kwargs)


def set_user_context(user_id: str, **kwargs):
    """ユーザーコンテキスト設定（グローバル関数）"""
    return error_tracker.set_user_context(user_id, **kwargs)


def add_breadcrumb(message: str, **kwargs):
    """ブレッドクラム追加（グローバル関数）"""
    return error_tracker.add_breadcrumb(message, **kwargs)