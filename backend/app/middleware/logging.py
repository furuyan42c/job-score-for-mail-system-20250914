"""
Logging Middleware
ログミドルウェア

リクエスト/レスポンスログとコンテキスト管理
- リクエストトラッキング
- レスポンス時間測定
- エラーログ
- セキュリティイベントログ
- パフォーマンス監視
"""

import time
import uuid
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from app.utils.logging import get_logger, LogCategory, LogLevel, LogContext
from app.core.config import settings


class RequestLoggingMiddleware:
    """リクエストログミドルウェア"""

    def __init__(self):
        self.logger = get_logger(__name__)

        # ログ除外パス
        self.exclude_paths = {
            "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"
        }

        # 機密パラメータ（ログから除外）
        self.sensitive_params = {
            "password", "passwd", "pwd", "secret", "token", "key",
            "api_key", "access_token", "refresh_token", "authorization"
        }

    async def log_request_response(self, request: Request, call_next: Callable) -> Response:
        """リクエスト/レスポンスをログ"""
        # リクエストID生成
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 基本情報取得
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # ログコンテキスト設定
        context = LogContext(
            request_id=request_id,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint=path,
            method=method,
            user_id=getattr(request.state, 'user_id', None),
            session_id=getattr(request.state, 'session_id', None)
        )

        logger = self.logger.with_context(**context.__dict__)

        # 除外パスチェック
        if path in self.exclude_paths:
            return await call_next(request)

        # リクエスト開始ログ
        start_time = time.time()

        try:
            # リクエストボディを読み取り（サイズ制限あり）
            request_body = await self._get_request_body(request)

            # リクエストログ
            await self._log_request_start(logger, request, request_body)

            # リクエスト処理
            response = await call_next(request)

            # 処理時間計算
            process_time = (time.time() - start_time) * 1000

            # レスポンスログ
            await self._log_request_complete(
                logger, request, response, process_time, request_body
            )

            # レスポンスヘッダーに情報追加
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}"

            return response

        except Exception as e:
            # エラーログ
            process_time = (time.time() - start_time) * 1000
            await self._log_request_error(logger, request, e, process_time)

            # エラーレスポンス作成
            if settings.DEBUG:
                error_detail = str(e)
            else:
                error_detail = "Internal server error"

            error_response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": error_detail,
                    "request_id": request_id
                }
            )
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Process-Time"] = f"{process_time:.2f}"

            return error_response

    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """リクエストボディを安全に取得"""
        try:
            # ボディサイズ制限（1MB）
            max_body_size = 1024 * 1024

            if request.headers.get("content-length"):
                content_length = int(request.headers["content-length"])
                if content_length > max_body_size:
                    return {"error": "Request body too large for logging"}

            # JSONボディの場合のみログ
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body_bytes = await request.body()
                if len(body_bytes) > max_body_size:
                    return {"error": "Request body too large for logging"}

                if body_bytes:
                    body = json.loads(body_bytes.decode('utf-8'))
                    return self._mask_sensitive_data(body)

        except Exception as e:
            return {"error": f"Failed to parse request body: {str(e)}"}

        return None

    def _mask_sensitive_data(self, data: Any) -> Any:
        """機密データをマスキング"""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if isinstance(key, str) and key.lower() in self.sensitive_params:
                    masked_data[key] = "***MASKED***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    async def _log_request_start(
        self, logger, request: Request, request_body: Optional[Dict[str, Any]]
    ):
        """リクエスト開始ログ"""
        # クエリパラメータをマスキング
        query_params = dict(request.query_params)
        masked_params = self._mask_sensitive_data(query_params)

        logger.api_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=0,  # 開始時点
            duration_ms=0,
            data={
                "phase": "request_start",
                "url": str(request.url),
                "query_params": masked_params,
                "headers": dict(request.headers),
                "body": request_body,
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
        )

    async def _log_request_complete(
        self,
        logger,
        request: Request,
        response: Response,
        process_time: float,
        request_body: Optional[Dict[str, Any]]
    ):
        """リクエスト完了ログ"""
        # レスポンス情報取得
        status_code = response.status_code
        response_size = response.headers.get("content-length", "unknown")

        # ログレベル決定
        if status_code >= 500:
            log_level = LogLevel.ERROR
        elif status_code >= 400:
            log_level = LogLevel.WARNING
        else:
            log_level = LogLevel.INFO

        # パフォーマンス警告
        performance_warning = process_time > settings.SLOW_QUERY_THRESHOLD * 1000

        data = {
            "phase": "request_complete",
            "status_code": status_code,
            "response_size": response_size,
            "performance_warning": performance_warning,
            "user_id": getattr(request.state, 'user_id', None),
            "rate_limited": status_code == 429,
            "authentication_failed": status_code == 401,
            "authorization_failed": status_code == 403
        }

        logger.log(
            log_level,
            LogCategory.API,
            f"{request.method} {request.url.path} - {status_code}",
            data=data,
            duration_ms=process_time
        )

        # パフォーマンス警告
        if performance_warning:
            logger.warning(
                LogCategory.PERFORMANCE,
                f"Slow request detected: {request.method} {request.url.path}",
                data={
                    "duration_ms": process_time,
                    "threshold_ms": settings.SLOW_QUERY_THRESHOLD * 1000
                }
            )

        # セキュリティイベント
        if status_code in [401, 403, 429]:
            await self._log_security_event(logger, request, status_code)

    async def _log_request_error(
        self,
        logger,
        request: Request,
        error: Exception,
        process_time: float
    ):
        """リクエストエラーログ"""
        logger.error(
            LogCategory.ERROR,
            f"Request failed: {request.method} {request.url.path}",
            error=error,
            data={
                "phase": "request_error",
                "error_type": type(error).__name__,
                "user_id": getattr(request.state, 'user_id', None)
            },
            duration_ms=process_time
        )

    async def _log_security_event(self, logger, request: Request, status_code: int):
        """セキュリティイベントログ"""
        event_types = {
            401: "authentication_failed",
            403: "authorization_failed",
            429: "rate_limit_exceeded"
        }

        event_type = event_types.get(status_code, "unknown_security_event")

        logger.security(
            LogLevel.WARNING,
            f"Security event: {event_type}",
            data={
                "event_type": event_type,
                "status_code": status_code,
                "endpoint": request.url.path,
                "method": request.method,
                "user_id": getattr(request.state, 'user_id', None)
            }
        )

    def _get_client_ip(self, request: Request) -> str:
        """クライアントIPアドレスを取得"""
        # プロキシ経由の場合を考慮
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class DatabaseLoggingMixin:
    """データベースログミックスイン"""

    def __init__(self):
        self.db_logger = get_logger("database")

    async def log_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        error: Optional[Exception] = None
    ):
        """データベースクエリをログ"""
        # クエリの機密部分をマスキング
        masked_query = self._mask_query(query)
        masked_params = self._mask_sensitive_data(params) if params else None

        data = {
            "query": masked_query,
            "params": masked_params,
            "row_count": row_count
        }

        if error:
            self.db_logger.error(
                LogCategory.DATABASE,
                "Database query failed",
                error=error,
                data=data,
                duration_ms=duration_ms
            )
        else:
            level = LogLevel.WARNING if duration_ms and duration_ms > 1000 else LogLevel.INFO
            self.db_logger.log(
                level,
                LogCategory.DATABASE,
                "Database query executed",
                data=data,
                duration_ms=duration_ms
            )

    def _mask_query(self, query: str) -> str:
        """SQLクエリの機密部分をマスキング"""
        import re

        # パスワード関連のクエリをマスキング
        query = re.sub(
            r"(password\s*=\s*['\"])[^'\"]*(['\"])",
            r"\1***MASKED***\2",
            query,
            flags=re.IGNORECASE
        )

        # メールアドレスをマスキング
        query = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "***@***.***",
            query
        )

        return query

    def _mask_sensitive_data(self, data: Any) -> Any:
        """機密データをマスキング"""
        if isinstance(data, dict):
            masked_data = {}
            sensitive_keys = {"password", "email", "token", "secret", "key"}
            for key, value in data.items():
                if isinstance(key, str) and key.lower() in sensitive_keys:
                    masked_data[key] = "***MASKED***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data


class ApplicationEventLogger:
    """アプリケーションイベントログ"""

    def __init__(self):
        self.logger = get_logger("application")

    async def log_startup_event(self, app_name: str, version: str):
        """アプリケーション起動ログ"""
        self.logger.info(
            LogCategory.SYSTEM,
            f"Application startup: {app_name} v{version}",
            data={
                "event_type": "application_startup",
                "app_name": app_name,
                "version": version,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            }
        )

    async def log_shutdown_event(self, app_name: str):
        """アプリケーション終了ログ"""
        self.logger.info(
            LogCategory.SYSTEM,
            f"Application shutdown: {app_name}",
            data={
                "event_type": "application_shutdown",
                "app_name": app_name
            }
        )

    async def log_health_check(self, status: str, details: Dict[str, Any]):
        """ヘルスチェックログ"""
        log_level = LogLevel.INFO if status == "healthy" else LogLevel.ERROR

        self.logger.log(
            log_level,
            LogCategory.SYSTEM,
            f"Health check: {status}",
            data={
                "event_type": "health_check",
                "status": status,
                "details": details
            }
        )

    async def log_business_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """ビジネスイベントログ"""
        self.logger.info(
            LogCategory.BUSINESS,
            description,
            data={
                "event_type": event_type,
                "user_id": user_id,
                **(data or {})
            }
        )


# グローバルインスタンス
request_logging_middleware = RequestLoggingMiddleware()
db_logging_mixin = DatabaseLoggingMixin()
app_event_logger = ApplicationEventLogger()


# 便利な装飾子
def log_function_call(category: LogCategory = LogCategory.SYSTEM):
    """関数呼び出しログ装飾子"""
    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.debug(
                    category,
                    f"Function executed: {func.__name__}",
                    data={
                        "function": func.__name__,
                        "module": func.__module__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    },
                    duration_ms=duration_ms
                )
                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    category,
                    f"Function failed: {func.__name__}",
                    error=e,
                    data={
                        "function": func.__name__,
                        "module": func.__module__
                    },
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

                logger.debug(
                    category,
                    f"Function executed: {func.__name__}",
                    data={
                        "function": func.__name__,
                        "module": func.__module__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    },
                    duration_ms=duration_ms
                )
                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    category,
                    f"Function failed: {func.__name__}",
                    error=e,
                    data={
                        "function": func.__name__,
                        "module": func.__module__
                    },
                    duration_ms=duration_ms
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator