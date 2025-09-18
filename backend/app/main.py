"""
FastAPI メインアプリケーション

バイト求人マッチングシステムのエントリーポイント
- RESTful APIエンドポイント
- 認証・認可
- エラーハンドリング
- CORS設定
"""

from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import asyncio
from typing import Callable

from app.core.config import settings
from app.core.database import init_db, close_db, ConnectionPoolStats
from app.dependencies import (
    get_request_id,
    log_request_performance,
    health_check_dependencies,
    close_redis
)
from app.utils.error_tracker import init_error_tracking, error_tracker, ErrorCategory, ErrorSeverity
from app.utils.openapi import custom_openapi
from app.routers import jobs, users, matching, analytics, batch, scores, actions, health, tdd_endpoints, sql_routes, auth, rate_limit_admin


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理（高並行性対応）"""
    # 起動時処理
    logger.info("Starting job matching system...")

    try:
        # エラー追跡初期化（最初に実行）
        error_tracking_enabled = init_error_tracking()
        if error_tracking_enabled:
            logger.info("Error tracking with Sentry initialized")
        else:
            logger.warning("Error tracking disabled (SENTRY_DSN not configured)")

        # データベース初期化
        await init_db()
        logger.info("Database connection initialized")

        # システム状態確認
        health = await health_check_dependencies()
        logger.info(f"System health check: {health}")

        # 接続プール状態ログ
        pool_stats = ConnectionPoolStats.get_pool_stats()
        logger.info(f"Database pool initialized: {pool_stats}")

    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        # エラー追跡にも送信
        error_tracker.capture_exception(
            e,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.CRITICAL,
            extra_context={"phase": "application_startup"}
        )
        raise

    yield

    # 終了時処理
    logger.info("Shutting down job matching system...")

    try:
        # 接続を優雅にクローズ
        await close_redis()
        logger.info("Redis connection closed")

        await close_db()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# FastAPIアプリケーション作成
app = FastAPI(
    title="バイト求人マッチングシステム API",
    description="""
    ## 機能概要

    * **求人管理**: 10万件規模の求人データ管理
    * **ユーザー管理**: 1万人規模のユーザープロファイル
    * **マッチング**: AIベースのスコアリングシステム
    * **バッチ処理**: 大規模データ処理とメール配信
    * **分析**: リアルタイム分析とKPIダッシュボード
    * **セキュリティ**: JWT認証、レート制限、構造化ログ
    * **監視**: Sentryエラー追跡、パフォーマンスモニタリング

    ## 技術スタック

    * FastAPI + PostgreSQL (Supabase)
    * Pydantic データバリデーション
    * SQLAlchemy ORM
    * Redis キャッシュ
    * Celery バッチ処理
    * Sentry エラー追跡

    ## セキュリティ

    * JWT Bearer認証
    * レート制限（IP/User/Endpoint別）
    * SQLインジェクション防止
    * 機密データマスキング

    ## APIバージョニング

    現在のバージョン: v1.0.0
    ベースURL: `/api/v1`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True
    }
)

# ミドルウェア設定（高並行性対応）
# Gzip圧縮（パフォーマンス向上）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# OpenAPIカスタムタグ定義
tags_metadata = [
    {
        "name": "authentication",
        "description": "認証・認可関連のエンドポイント",
        "externalDocs": {
            "description": "JWT認証の詳細",
            "url": "https://jwt.io/introduction",
        },
    },
    {
        "name": "jobs",
        "description": "求人データ管理API",
    },
    {
        "name": "users",
        "description": "ユーザー管理API",
    },
    {
        "name": "matching",
        "description": "AIマッチングエンジンAPI",
    },
    {
        "name": "batch",
        "description": "バッチ処理管理API",
    },
    {
        "name": "scores",
        "description": "スコアリングエンジンAPI",
    },
    {
        "name": "analytics",
        "description": "分析・レポートAPI",
    },
    {
        "name": "monitoring",
        "description": "システム監視・ヘルスチェック",
    },
    {
        "name": "admin",
        "description": "管理者用API",
    },
]

# タグメタデータをアプリに追加
app.openapi_tags = tags_metadata

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 本番環境での信頼済みホスト制限
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# 認証ミドルウェア
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.logging import request_logging_middleware

auth_middleware = AuthenticationMiddleware()

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next: Callable):
    """レート制限ミドルウェア（認証前に実行）"""
    start_time = time.time()

    # レート制限チェック
    rate_limit_response = await rate_limit_middleware.check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response

    # リクエスト処理
    response = await call_next(request)

    # レスポンス時間記録
    response_time = time.time() - start_time

    # レート制限ヘッダー追加
    await rate_limit_middleware.add_response_headers(response, request)

    # リクエスト記録（統計用）
    client_ip = rate_limit_middleware._get_client_ip(request)
    user_id = getattr(request.state, 'user_id', None)

    from app.middleware.rate_limit import RequestRecord
    record = RequestRecord(
        timestamp=start_time,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        response_time=response_time
    )

    key = f"ip:{client_ip}" if not user_id else f"user:{user_id}"
    await rate_limit_middleware.storage.add_request_record(key, record)

    return response


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next: Callable):
    """構造化ログミドルウェア（リクエスト/レスポンス/セキュリティイベント）"""
    return await request_logging_middleware.log_request_response(request, call_next)


@app.middleware("http")
async def authentication_middleware(request: Request, call_next: Callable):
    """認証ミドルウェア（全リクエストに適用）"""
    try:
        # 認証チェック（認証不要パスは自動でスキップされる）
        await auth_middleware.authenticate_request(request)

        # 認証成功時にエラー追跡のユーザーコンテキスト設定
        if hasattr(request.state, 'user_id') and request.state.user_id:
            error_tracker.set_user_context(
                user_id=request.state.user_id,
                email=getattr(request.state, 'user_email', None)
            )

    except HTTPException as auth_error:
        # 認証エラーをエラー追跡に記録
        error_tracker.capture_exception(
            auth_error,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            extra_context={
                "path": request.url.path,
                "method": request.method,
                "status_code": auth_error.status_code
            }
        )

        # 認証エラーの場合、パブリックパス以外はエラーを返す
        if not auth_middleware.is_public_path(request.url.path):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=auth_error.status_code,
                content={"detail": auth_error.detail},
                headers=auth_error.headers or {}
            )

    # 認証通過または認証不要の場合は次のミドルウェアへ
    response = await call_next(request)
    return response


# リクエストトラッキング・パフォーマンス監視ミドルウェア
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next: Callable):
    """リクエストトラッキングとパフォーマンス監視（高並行性対応）"""
    # リクエストID生成
    request_id = await get_request_id(request)

    # エラー追跡用ブレッドクラム追加
    error_tracker.add_breadcrumb(
        message=f"Request started: {request.method} {request.url.path}",
        category="request",
        level="info",
        data={
            "method": request.method,
            "path": request.url.path,
            "request_id": request_id
        }
    )

    start_time = time.time()

    try:
        # レスポンス処理
        response = await call_next(request)

        # 処理時間計測
        process_time = time.time() - start_time

        # レスポンスヘッダー追加
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        # パフォーマンス監視ログ
        if process_time > settings.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow request: {request.method} {request.url} "
                f"took {process_time:.2f}s [Request ID: {request_id}]"
            )

            # 遅いリクエストをエラー追跡に記録
            error_tracker.capture_message(
                f"Slow request detected: {request.method} {request.url.path}",
                level=ErrorSeverity.MEDIUM,
                category=ErrorCategory.PERFORMANCE,
                extra_context={
                    "duration_ms": process_time * 1000,
                    "threshold_ms": settings.SLOW_QUERY_THRESHOLD * 1000,
                    "request_id": request_id
                },
                tags={
                    "endpoint": request.url.path,
                    "method": request.method
                }
            )

        # レスポンス完了ブレッドクラム
        error_tracker.add_breadcrumb(
            message=f"Request completed: {response.status_code}",
            category="response",
            level="info",
            data={
                "status_code": response.status_code,
                "duration_ms": process_time * 1000,
                "request_id": request_id
            }
        )

        # 統計情報（非同期で記録）
        asyncio.create_task(_log_request_stats(request, response, process_time))

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # エラーブレッドクラム追加
        error_tracker.add_breadcrumb(
            message=f"Request failed: {type(e).__name__}",
            category="error",
            level="error",
            data={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": process_time * 1000,
                "request_id": request_id
            }
        )

        logger.error(
            f"Request failed: {request.method} {request.url} "
            f"after {process_time:.2f}s [Request ID: {request_id}] - {str(e)}"
        )
        raise


async def _log_request_stats(request: Request, response, process_time: float):
    """リクエスト統計情報を非同期でログ記録"""
    try:
        # 接続プール使用率監視
        pool_stats = ConnectionPoolStats.get_pool_stats()
        if pool_stats["utilization"] > 80:  # 80%以上で警告
            logger.warning(f"High database connection pool utilization: {pool_stats}")

        # デバッグモードでは詳細ログ
        if settings.DEBUG:
            logger.debug(
                f"Request stats - Method: {request.method}, "
                f"URL: {request.url}, Time: {process_time:.3f}s, "
                f"Status: {response.status_code}, Pool: {pool_stats['utilization']:.1f}%"
            )

    except Exception as e:
        logger.error(f"Failed to log request stats: {e}")


# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """グローバル例外処理"""
    request_id = getattr(request.state, "request_id", None)

    # エラー追跡にキャプチャ
    user_context = {}
    if hasattr(request.state, 'user_id') and request.state.user_id:
        user_context = {"id": request.state.user_id}

    event_id = error_tracker.capture_exception(
        exc,
        category=ErrorCategory.API,
        severity=ErrorSeverity.HIGH,
        user_context=user_context if user_context else None,
        extra_context={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "phase": "request_processing"
        },
        tags={
            "endpoint": request.url.path,
            "method": request.method
        }
    )

    # ローカルログ
    logger.error(f"Global exception: {exc}", exc_info=True, extra={
        "request_id": request_id,
        "sentry_event_id": event_id
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "内部サーバーエラーが発生しました",
            "detail": str(exc) if settings.DEBUG else "サーバーエラー",
            "request_id": request_id,
            "event_id": event_id if settings.DEBUG else None
        }
    )


# ヘルスチェックエンドポイント（詳細版）
@app.get("/health", tags=["monitoring"])
async def health_check():
    """アプリケーションヘルスチェック（高並行性対応）"""
    health_data = await health_check_dependencies()

    # 接続プール状態も追加
    pool_stats = ConnectionPoolStats.get_pool_stats()

    return {
        "status": "healthy" if all(
            status != "unhealthy" for status in [
                health_data.get("database", "unknown"),
                health_data.get("redis", "unknown")
            ]
        ) else "unhealthy",
        "version": "1.0.0",
        "timestamp": health_data["timestamp"],
        "services": {
            "database": health_data.get("database", "unknown"),
            "redis": health_data.get("redis", "unknown")
        },
        "database_pool": pool_stats,
        "performance": {
            "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
            "rate_limit": settings.API_RATE_LIMIT,
            "slow_query_threshold": settings.SLOW_QUERY_THRESHOLD
        }
    }

# 詳細システム情報エンドポイント
@app.get("/system-info", tags=["monitoring"])
async def system_info():
    """システム詳細情報（管理者用）"""
    import psutil
    import platform

    # システム情報収集
    pool_stats = ConnectionPoolStats.get_pool_stats()

    return {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent
        },
        "application": {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "database": {
            "pool_stats": pool_stats,
            "pool_config": {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE
            }
        },
        "performance": {
            "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
            "api_rate_limit": settings.API_RATE_LIMIT,
            "slow_query_threshold": settings.SLOW_QUERY_THRESHOLD,
            "workers": settings.UVICORN_WORKERS,
            "worker_connections": settings.UVICORN_WORKER_CONNECTIONS
        }
    }


# APIエンドポイントルーター登録
# 認証関連エンドポイント（認証不要パスとして設定済み）
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

app.include_router(
    jobs.router,
    prefix="/api/v1/jobs",
    tags=["jobs"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    matching.router,
    prefix="/api/v1/matching",
    tags=["matching"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

app.include_router(
    batch.router,
    prefix="/api/v1/batch",
    tags=["batch"]
)

app.include_router(
    scores.router,
    prefix="/api/v1/scores",
    tags=["scores"]
)

app.include_router(
    actions.router,
    prefix="/api/v1/actions",
    tags=["actions"]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["health", "monitoring"]
)

app.include_router(
    rate_limit_admin.router,
    prefix="/admin/rate-limit",
    tags=["admin", "rate-limiting"]
)

app.include_router(
    sql_routes.router,
    prefix="/api/v1/sql",
    tags=["sql", "administration"]
)

# TDD Phase 2: GREEN - 契約テスト用エンドポイント（最小実装）
# これらは後でリファクタリングフェーズで適切な場所に移動する
app.include_router(
    tdd_endpoints.router,
    prefix="/api/v1",
    tags=["tdd_endpoints"]
)


# ルートエンドポイント
@app.get("/", tags=["root"])
async def root():
    """API情報"""
    return {
        "message": "バイト求人マッチングシステム API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# カスタムOpenAPIスキーマを適用
def get_custom_openapi():
    return custom_openapi(app)

app.openapi = get_custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        # 高並行性設定
        workers=settings.UVICORN_WORKERS if not settings.DEBUG else 1,
        worker_connections=settings.UVICORN_WORKER_CONNECTIONS,
        backlog=settings.UVICORN_BACKLOG,
        limit_concurrency=settings.MAX_CONCURRENT_REQUESTS,
        timeout_keep_alive=settings.KEEP_ALIVE_TIMEOUT,
        timeout_graceful_shutdown=30,
        # パフォーマンス最適化
        loop="uvloop",  # Unix系でのパフォーマンス向上
        http="httptools",  # HTTPパフォーマンス向上
        access_log=settings.DEBUG,
        use_colors=settings.DEBUG
    )