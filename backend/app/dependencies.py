"""
FastAPI 依存性注入管理

共通の依存性を定義し、リクエスト処理を最適化
高並行性（10,000+同時接続）に対応
"""

import time
import uuid
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db, get_db_read_only

logger = logging.getLogger(__name__)

# セキュリティ設定
security = HTTPBearer()

# Redis接続（キャッシュ・レート制限用）
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Redis接続の依存性注入"""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
            retry_on_timeout=True,
            max_connections=200  # 高並行性対応
        )
    return redis_client


async def close_redis():
    """Redis接続クローズ"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# リクエストID生成・トラッキング
async def get_request_id(request: Request) -> str:
    """
    リクエストID生成・取得

    各リクエストにユニークなIDを付与してトラッキング
    """
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # リクエスト状態に保存
    request.state.request_id = request_id
    request.state.start_time = time.time()

    return request_id


# レート制限
class RateLimiter:
    """Redis を使用したレート制限"""

    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests or settings.API_RATE_LIMIT
        self.window_seconds = window_seconds

    async def __call__(
        self,
        request: Request,
        redis: aioredis.Redis = Depends(get_redis)
    ) -> None:
        """レート制限チェック"""
        # クライアントIPを取得
        client_ip = request.client.host
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            client_ip = forwarded_for.split(",")[0].strip()

        # レート制限キー
        key = f"rate_limit:{client_ip}"

        try:
            # 現在のリクエスト数を取得
            current = await redis.get(key)

            if current is None:
                # 初回リクエスト
                await redis.setex(key, self.window_seconds, 1)
            else:
                current_count = int(current)
                if current_count >= self.max_requests:
                    # レート制限に達している
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
                    )
                # カウンターを増加
                await redis.incr(key)

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Rate limiting error: {e}")
            # Redis エラーの場合はレート制限をスキップ


# 認証関連
class AuthManager:
    """認証管理"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークン生成"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """トークン検証"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_read_only),
    redis: aioredis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    現在のユーザー情報取得

    JWTトークンを検証してユーザー情報を返す
    """
    # トークン検証
    payload = AuthManager.verify_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Redis キャッシュからユーザー情報を取得（パフォーマンス最適化）
    cache_key = f"user:{user_id}"
    cached_user = await redis.get(cache_key)

    if cached_user:
        import json
        return json.loads(cached_user)

    # データベースからユーザー情報を取得
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT id, email, is_active, role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    user = result.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    user_data = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "role": user.role
    }

    # Redis にキャッシュ（5分間）
    import json
    await redis.setex(cache_key, 300, json.dumps(user_data))

    return user_data


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """管理者権限チェック"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# パフォーマンス監視
async def log_request_performance(request: Request) -> None:
    """リクエストパフォーマンスのログ出力"""
    if hasattr(request.state, "start_time"):
        duration = time.time() - request.state.start_time
        if duration > settings.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow request detected: {request.method} {request.url} "
                f"took {duration:.2f}s [Request ID: {getattr(request.state, 'request_id', 'unknown')}]"
            )


# ヘルスチェック依存性
async def health_check_dependencies() -> Dict[str, Any]:
    """システム依存性のヘルスチェック"""
    health_status = {
        "database": "unknown",
        "redis": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }

    # データベースチェック
    try:
        from app.core.database import check_database_health
        db_health = await check_database_health()
        health_status["database"] = db_health["status"]
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)

    # Redisチェック
    try:
        redis = await get_redis()
        await redis.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = "unhealthy"
        health_status["redis_error"] = str(e)

    return health_status


# 高並行性対応の最適化されたレート制限
rate_limit_normal = RateLimiter(max_requests=settings.API_RATE_LIMIT, window_seconds=60)
rate_limit_strict = RateLimiter(max_requests=100, window_seconds=60)  # 厳しい制限
rate_limit_auth = RateLimiter(max_requests=10, window_seconds=60)     # 認証系API


# 依存性のエクスポート
__all__ = [
    "get_db",
    "get_db_read_only",
    "get_redis",
    "get_request_id",
    "get_current_user",
    "get_admin_user",
    "rate_limit_normal",
    "rate_limit_strict",
    "rate_limit_auth",
    "health_check_dependencies",
    "log_request_performance",
    "AuthManager",
    "RateLimiter"
]