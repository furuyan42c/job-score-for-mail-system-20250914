"""
Structured Logging System
構造化ログシステム

構造化ログ機能とログ管理
- JSON構造化ログ
- ログレベル管理
- セキュリティログ
- パフォーマンスログ
- ログ集約と分析
- 機密情報マスキング
"""

import logging
import json
import time
import traceback
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import inspect
from pathlib import Path

from app.core.config import settings


class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """ログカテゴリ"""
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    API = "api"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    ERROR = "error"


@dataclass
class LogContext:
    """ログコンテキスト"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class StructuredLogEntry:
    """構造化ログエントリ"""
    timestamp: str
    level: str
    category: str
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    context: LogContext
    data: Dict[str, Any]
    duration_ms: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None


class SensitiveDataMasker:
    """機密データマスキング"""

    SENSITIVE_PATTERNS = {
        "password", "passwd", "pwd", "secret", "token", "key", "api_key",
        "access_token", "refresh_token", "jwt", "auth", "authorization",
        "credit_card", "card_number", "ssn", "social_security",
        "email", "phone", "address", "zip_code", "postal_code"
    }

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'

    @classmethod
    def mask_sensitive_data(cls, data: Any) -> Any:
        """機密データをマスキング"""
        if isinstance(data, dict):
            return {key: cls._mask_value(key, value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            return cls._mask_string_patterns(data)
        else:
            return data

    @classmethod
    def _mask_value(cls, key: str, value: Any) -> Any:
        """キーに基づく値のマスキング"""
        if isinstance(key, str) and any(pattern in key.lower() for pattern in cls.SENSITIVE_PATTERNS):
            if isinstance(value, str) and len(value) > 0:
                if len(value) <= 4:
                    return "*" * len(value)
                else:
                    return value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                return "***MASKED***"

        return cls.mask_sensitive_data(value)

    @classmethod
    def _mask_string_patterns(cls, text: str) -> str:
        """文字列内のパターンをマスキング"""
        import re

        # メールアドレス
        text = re.sub(cls.EMAIL_PATTERN, lambda m: cls._mask_email(m.group()), text)

        # 電話番号
        text = re.sub(cls.PHONE_PATTERN, "***-***-****", text)

        # クレジットカード番号
        text = re.sub(cls.CREDIT_CARD_PATTERN, "**** **** **** ****", text)

        return text

    @staticmethod
    def _mask_email(email: str) -> str:
        """メールアドレスをマスキング"""
        if '@' in email:
            local, domain = email.split('@', 1)
            if len(local) <= 2:
                return f"***@{domain}"
            else:
                return f"{local[0]}***{local[-1]}@{domain}"
        return "***@***.***"


class StructuredLogger:
    """構造化ログ管理クラス"""

    def __init__(self, name: str = __name__):
        self.name = name
        self.logger = logging.getLogger(name)
        self.context = LogContext()

        # フォーマッター設定
        self._setup_formatters()

    def _setup_formatters(self):
        """ログフォーマッターを設定"""
        # JSON フォーマッター
        json_formatter = StructuredJSONFormatter()

        # ハンドラー設定
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

        # ファイルハンドラー（本番環境用）
        if not settings.DEBUG:
            file_handler = logging.FileHandler("app.log")
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

    def set_context(self, **kwargs) -> 'StructuredLogger':
        """ログコンテキストを設定"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        return self

    def with_context(self, **kwargs) -> 'StructuredLogger':
        """新しいコンテキストで新しいロガーインスタンスを作成"""
        new_logger = StructuredLogger(self.name)
        new_logger.context = LogContext(**{**asdict(self.context), **kwargs})
        return new_logger

    def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Exception] = None
    ):
        """構造化ログ出力"""
        frame = inspect.currentframe().f_back
        module = frame.f_globals.get('__name__', 'unknown')
        function = frame.f_code.co_name
        line_number = frame.f_lineno

        # 機密データマスキング
        if data:
            data = SensitiveDataMasker.mask_sensitive_data(data)

        # エラー詳細
        error_details = None
        if error:
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc() if settings.DEBUG else None
            }

        # ログエントリ作成
        log_entry = StructuredLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            category=category.value,
            message=message,
            logger_name=self.name,
            module=module,
            function=function,
            line_number=line_number,
            context=self.context,
            data=data or {},
            duration_ms=duration_ms,
            error_details=error_details
        )

        # 標準ログ出力
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, log_entry)

    def debug(self, category: LogCategory, message: str, **kwargs):
        """デバッグログ"""
        self.log(LogLevel.DEBUG, category, message, **kwargs)

    def info(self, category: LogCategory, message: str, **kwargs):
        """情報ログ"""
        self.log(LogLevel.INFO, category, message, **kwargs)

    def warning(self, category: LogCategory, message: str, **kwargs):
        """警告ログ"""
        self.log(LogLevel.WARNING, category, message, **kwargs)

    def error(self, category: LogCategory, message: str, error: Optional[Exception] = None, **kwargs):
        """エラーログ"""
        self.log(LogLevel.ERROR, category, message, error=error, **kwargs)

    def critical(self, category: LogCategory, message: str, error: Optional[Exception] = None, **kwargs):
        """致命的エラーログ"""
        self.log(LogLevel.CRITICAL, category, message, error=error, **kwargs)

    # カテゴリ別便利メソッド
    def security(self, level: LogLevel, message: str, **kwargs):
        """セキュリティログ"""
        self.log(level, LogCategory.SECURITY, message, **kwargs)

    def performance(self, message: str, duration_ms: float, **kwargs):
        """パフォーマンスログ"""
        self.log(LogLevel.INFO, LogCategory.PERFORMANCE, message, duration_ms=duration_ms, **kwargs)

    def api_request(self, method: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
        """APIリクエストログ"""
        data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            **kwargs
        }
        self.log(LogLevel.INFO, LogCategory.API, f"{method} {endpoint} - {status_code}",
                data=data, duration_ms=duration_ms)

    def database_query(self, query: str, duration_ms: float, **kwargs):
        """データベースクエリログ"""
        # クエリの機密部分をマスキング
        masked_query = SensitiveDataMasker._mask_string_patterns(query)
        data = {"query": masked_query, **kwargs}
        self.log(LogLevel.INFO, LogCategory.DATABASE, "Database query executed",
                data=data, duration_ms=duration_ms)

    def auth_event(self, event_type: str, user_id: Optional[str] = None, **kwargs):
        """認証イベントログ"""
        data = {"event_type": event_type, "user_id": user_id, **kwargs}
        self.log(LogLevel.INFO, LogCategory.AUTHENTICATION, f"Authentication event: {event_type}", data=data)


class StructuredJSONFormatter(logging.Formatter):
    """JSON構造化ログフォーマッター"""

    def format(self, record) -> str:
        """ログレコードをJSON形式でフォーマット"""
        if isinstance(record.msg, StructuredLogEntry):
            log_entry = record.msg
            return json.dumps({
                "timestamp": log_entry.timestamp,
                "level": log_entry.level,
                "category": log_entry.category,
                "message": log_entry.message,
                "logger": log_entry.logger_name,
                "module": log_entry.module,
                "function": log_entry.function,
                "line": log_entry.line_number,
                "context": asdict(log_entry.context),
                "data": log_entry.data,
                "duration_ms": log_entry.duration_ms,
                "error": log_entry.error_details
            }, ensure_ascii=False, default=str)
        else:
            # 従来のログメッセージの場合
            return json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "category": "system",
                "message": record.getMessage(),
                "logger": record.name,
                "module": record.module if hasattr(record, 'module') else 'unknown',
                "function": record.funcName if hasattr(record, 'funcName') else 'unknown',
                "line": record.lineno if hasattr(record, 'lineno') else 0
            }, ensure_ascii=False)


class PerformanceLogger:
    """パフォーマンス測定ログ"""

    def __init__(self, logger: StructuredLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type:
                self.logger.error(
                    LogCategory.PERFORMANCE,
                    f"Operation failed: {self.operation_name}",
                    error=exc_val,
                    duration_ms=duration_ms
                )
            else:
                self.logger.performance(
                    f"Operation completed: {self.operation_name}",
                    duration_ms=duration_ms
                )

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type:
                self.logger.error(
                    LogCategory.PERFORMANCE,
                    f"Operation failed: {self.operation_name}",
                    error=exc_val,
                    duration_ms=duration_ms
                )
            else:
                self.logger.performance(
                    f"Operation completed: {self.operation_name}",
                    duration_ms=duration_ms
                )


def log_execution_time(category: LogCategory = LogCategory.PERFORMANCE):
    """実行時間ログデコレータ"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.performance(
                    f"Function executed: {func.__name__}",
                    duration_ms=duration_ms,
                    data={"args_count": len(args), "kwargs_count": len(kwargs)}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    category,
                    f"Function failed: {func.__name__}",
                    error=e,
                    duration_ms=duration_ms
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.performance(
                    f"Function executed: {func.__name__}",
                    duration_ms=duration_ms,
                    data={"args_count": len(args), "kwargs_count": len(kwargs)}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    category,
                    f"Function failed: {func.__name__}",
                    error=e,
                    duration_ms=duration_ms
                )
                raise

        # 非同期関数かチェック
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_security_event(event_type: str, severity: LogLevel = LogLevel.WARNING):
    """セキュリティイベントログデコレータ"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            # リクエストオブジェクトを探す
            request = None
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'url'):
                    request = arg
                    break

            context_data = {}
            if request:
                context_data = {
                    "ip_address": request.client.host if request.client else "unknown",
                    "endpoint": str(request.url),
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "unknown")
                }

            try:
                result = await func(*args, **kwargs)
                logger.security(
                    LogLevel.INFO,
                    f"Security event: {event_type} - Success",
                    data=context_data
                )
                return result
            except Exception as e:
                logger.security(
                    severity,
                    f"Security event: {event_type} - Failed: {str(e)}",
                    error=e,
                    data=context_data
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            try:
                result = func(*args, **kwargs)
                logger.security(LogLevel.INFO, f"Security event: {event_type} - Success")
                return result
            except Exception as e:
                logger.security(severity, f"Security event: {event_type} - Failed: {str(e)}", error=e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class LoggerManager:
    """ログ管理クラス"""

    _loggers: Dict[str, StructuredLogger] = {}

    @classmethod
    def get_logger(cls, name: str) -> StructuredLogger:
        """ロガーインスタンスを取得"""
        if name not in cls._loggers:
            cls._loggers[name] = StructuredLogger(name)
        return cls._loggers[name]

    @classmethod
    def configure_root_logger(cls):
        """ルートロガーを設定"""
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format=settings.LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 不要なログを抑制
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)

    @classmethod
    def setup_log_rotation(cls):
        """ログローテーション設定"""
        from logging.handlers import RotatingFileHandler

        # 本番環境でのログローテーション
        if not settings.DEBUG:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # アプリケーションログ
            app_handler = RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            app_handler.setFormatter(StructuredJSONFormatter())

            # セキュリティログ
            security_handler = RotatingFileHandler(
                log_dir / "security.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            security_handler.setFormatter(StructuredJSONFormatter())

            # パフォーマンスログ
            performance_handler = RotatingFileHandler(
                log_dir / "performance.log",
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=3
            )
            performance_handler.setFormatter(StructuredJSONFormatter())

            logging.getLogger().addHandler(app_handler)
            logging.getLogger("security").addHandler(security_handler)
            logging.getLogger("performance").addHandler(performance_handler)


# 便利関数
def get_logger(name: str = None) -> StructuredLogger:
    """ロガーを取得"""
    if name is None:
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'app')
    return LoggerManager.get_logger(name)


def performance_log(operation_name: str) -> PerformanceLogger:
    """パフォーマンス測定ログ"""
    frame = inspect.currentframe().f_back
    logger_name = frame.f_globals.get('__name__', 'app')
    logger = get_logger(logger_name)
    return PerformanceLogger(logger, operation_name)


# 初期化
LoggerManager.configure_root_logger()
if not settings.DEBUG:
    LoggerManager.setup_log_rotation()