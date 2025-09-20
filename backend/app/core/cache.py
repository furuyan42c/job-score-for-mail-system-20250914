"""
キャッシュ管理モジュール

Redisベースのキャッシュ管理機能を提供
開発環境では簡易的なインメモリキャッシュにフォールバック
"""

import asyncio
import json
import logging
import pickle
from datetime import timedelta
from functools import wraps
from hashlib import md5
from typing import Any, Optional, Union

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redisインポートを試みる
try:
    import redis.asyncio as aioredis
    from redis.exceptions import RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using in-memory cache fallback.")


class InMemoryCache:
    """簡易的なインメモリキャッシュ（開発環境用）"""

    def __init__(self):
        self._cache = {}
        self._ttls = {}

    async def get(self, key: str) -> Optional[bytes]:
        """キャッシュから値を取得"""
        if key in self._cache:
            return self._cache[key]
        return None

    async def set(self, key: str, value: bytes, ex: Optional[int] = None) -> bool:
        """キャッシュに値を設定"""
        self._cache[key] = value
        if ex:
            # TTL管理（簡易実装）
            self._ttls[key] = ex
        return True

    async def delete(self, *keys: str) -> int:
        """キャッシュから削除"""
        deleted = 0
        for key in keys:
            if key in self._cache:
                del self._cache[key]
                if key in self._ttls:
                    del self._ttls[key]
                deleted += 1
        return deleted

    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        return key in self._cache

    async def expire(self, key: str, seconds: int) -> bool:
        """TTL設定"""
        if key in self._cache:
            self._ttls[key] = seconds
            return True
        return False

    async def close(self):
        """接続クローズ（インメモリでは何もしない）"""
        pass

    async def flushdb(self):
        """全データクリア"""
        self._cache.clear()
        self._ttls.clear()


class CacheManager:
    """キャッシュマネージャー"""

    def __init__(self):
        self.redis_client: Optional[Union[aioredis.Redis, InMemoryCache]] = None
        self._initialized = False

    async def initialize(self):
        """キャッシュ初期化"""
        if self._initialized:
            return

        try:
            if REDIS_AVAILABLE and not settings.database_url_async.startswith("sqlite"):
                # Redis使用
                self.redis_client = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False,
                    max_connections=50,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPINTVL
                        2: 3,  # TCP_KEEPCNT
                        3: 5,  # TCP_KEEPIDLE
                    },
                )
                # 接続確認
                await self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            else:
                # インメモリキャッシュ使用
                self.redis_client = InMemoryCache()
                logger.info("In-memory cache initialized (Redis not available)")

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            # フォールバック
            self.redis_client = InMemoryCache()
            self._initialized = True

    async def get(self, key: str, default: Any = None) -> Any:
        """キャッシュから値を取得"""
        if not self._initialized:
            await self.initialize()

        try:
            value = await self.redis_client.get(key)
            if value is None:
                return default

            # デシリアライズ
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # JSON以外の場合はpickleを試す
                try:
                    return pickle.loads(value)
                except:
                    return value.decode() if isinstance(value, bytes) else value

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """キャッシュに値を設定"""
        if not self._initialized:
            await self.initialize()

        try:
            # シリアライズ
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value).encode()
            elif isinstance(value, str):
                serialized = value.encode()
            elif isinstance(value, bytes):
                serialized = value
            else:
                serialized = pickle.dumps(value)

            # TTL設定
            ttl = ttl or settings.CACHE_TTL

            return await self.redis_client.set(key, serialized, ex=ttl)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """キャッシュから削除"""
        if not self._initialized:
            await self.initialize()

        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        if not self._initialized:
            await self.initialize()

        try:
            return await self.redis_client.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """パターンに一致するキーを削除"""
        if not self._initialized:
            await self.initialize()

        try:
            if isinstance(self.redis_client, InMemoryCache):
                # インメモリキャッシュの場合
                keys_to_delete = [
                    k for k in self.redis_client._cache.keys() if pattern.replace("*", "") in k
                ]
                return await self.redis_client.delete(*keys_to_delete)
            else:
                # Redisの場合
                cursor = 0
                deleted = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        deleted += await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
                return deleted

        except Exception as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return 0

    async def close(self):
        """接続クローズ"""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """キャッシュキー生成"""
        parts = [prefix]
        parts.extend(str(arg) for arg in args)
        parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(parts)

    async def get_or_set(self, key: str, func: callable, ttl: Optional[int] = None) -> Any:
        """キャッシュから取得、なければ関数実行して設定"""
        value = await self.get(key)
        if value is not None:
            return value

        # 非同期関数の場合
        if asyncio.iscoroutinefunction(func):
            value = await func()
        else:
            value = func()

        await self.set(key, value, ttl)
        return value


def cached(prefix: str, ttl: Optional[int] = None, key_builder: Optional[callable] = None):
    """キャッシュデコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キー生成
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # デフォルトのキー生成
                key_parts = [prefix, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # キャッシュから取得
            value = await cache_manager.get(cache_key)
            if value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return value

            # 関数実行
            logger.debug(f"Cache miss for key: {cache_key}")
            value = await func(*args, **kwargs)

            # キャッシュに設定
            await cache_manager.set(cache_key, value, ttl)

            return value

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """キャッシュ無効化デコレータ"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 関数実行
            result = await func(*args, **kwargs)

            # キャッシュクリア
            await cache_manager.clear_pattern(pattern)

            return result

        return wrapper

    return decorator


# シングルトンインスタンス
cache_manager = CacheManager()


# キャッシュキープレフィックス定数
class CacheKeys:
    """キャッシュキープレフィックス"""

    # ユーザー関連
    USER_PROFILE = "user:profile"
    USER_SESSION = "user:session"
    USER_PREFERENCES = "user:preferences"

    # 求人関連
    JOB_DETAIL = "job:detail"
    JOB_LIST = "job:list"
    JOB_SEARCH = "job:search"
    JOB_RECOMMENDATIONS = "job:recommendations"

    # スコアリング関連
    SCORE_BASIC = "score:basic"
    SCORE_SEO = "score:seo"
    SCORE_PERSONALIZED = "score:personalized"
    SCORE_TOTAL = "score:total"

    # マッチング関連
    MATCHING_RESULT = "matching:result"
    MATCHING_SECTIONS = "matching:sections"

    # 統計関連
    STATS_DAILY = "stats:daily"
    STATS_USER = "stats:user"
    STATS_JOB = "stats:job"

    # システム関連
    SYSTEM_CONFIG = "system:config"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_METRICS = "system:metrics"


__all__ = ["cache_manager", "CacheManager", "CacheKeys", "cached", "invalidate_cache"]
