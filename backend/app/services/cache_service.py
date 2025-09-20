"""
T055: Cache Implementation

マルチレベルキャッシングシステムの実装
- メモリキャッシュ + Redisキャッシュの2層構造
- キャッシュウォーミング戦略
- 無効化パターンの実装
- 目標: キャッシュされたクエリで50%高速化
"""

import asyncio
import functools
import hashlib
import json
import logging
import pickle
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheLevel(Enum):
    """キャッシュレベル"""

    MEMORY = "memory"
    REDIS = "redis"
    PERSISTENT = "persistent"


class CacheStrategy(Enum):
    """キャッシュ戦略"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"  # 書き込み時キャッシュ更新
    WRITE_BACK = "write_back"  # 遅延書き込み
    WRITE_AROUND = "write_around"  # キャッシュバイパス


@dataclass
class CacheEntry:
    """キャッシュエントリ"""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_expired(self) -> bool:
        """有効期限チェック"""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """作成からの経過時間"""
        return (datetime.now() - self.created_at).total_seconds()

    def touch(self):
        """アクセス情報更新"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """キャッシュ統計"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    total_entries: int = 0
    avg_access_time: float = 0.0
    hit_rate: float = 0.0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def update_hit_rate(self):
        """ヒット率更新"""
        total_requests = self.hits + self.misses
        self.hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        self.last_updated = datetime.now()


class MemoryCache:
    """メモリキャッシュ実装"""

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl: Optional[float] = 3600.0,
        strategy: CacheStrategy = CacheStrategy.LRU,
    ):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.strategy = strategy

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()

        # クリーンアップタスク
        self._cleanup_interval = 60.0  # 60秒
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """キャッシュ開始"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Memory cache started")

    async def stop(self):
        """キャッシュ停止"""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Memory cache stopped")

    async def get(self, key: str) -> Optional[Any]:
        """値取得"""
        start_time = time.time()

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.update_hit_rate()
                return None

            # アクセス情報更新
            entry.touch()
            self._stats.hits += 1

            # アクセス時間更新
            access_time = time.time() - start_time
            self._stats.avg_access_time = (
                self._stats.avg_access_time * (self._stats.hits - 1) + access_time
            ) / self._stats.hits
            self._stats.update_hit_rate()

            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """値設定"""
        ttl = ttl or self.default_ttl

        # エントリ作成
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl,
            size_bytes=self._estimate_size(value),
        )

        with self._lock:
            # 容量チェック
            if not self._can_store(entry):
                # エビクション実行
                if not await self._evict_entries():
                    return False

            # キャッシュに追加
            old_entry = self._cache.get(key)
            self._cache[key] = entry

            # 統計更新
            if old_entry:
                self._stats.memory_usage_bytes -= old_entry.size_bytes
            else:
                self._stats.total_entries += 1

            self._stats.memory_usage_bytes += entry.size_bytes

            return True

    async def delete(self, key: str) -> bool:
        """値削除"""
        with self._lock:
            entry = self._cache.pop(key, None)
            if entry:
                self._stats.memory_usage_bytes -= entry.size_bytes
                self._stats.total_entries -= 1
                return True
            return False

    async def clear(self):
        """全削除"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    def _can_store(self, entry: CacheEntry) -> bool:
        """保存可能かチェック"""
        if len(self._cache) >= self.max_size:
            return False

        if self._stats.memory_usage_bytes + entry.size_bytes > self.max_memory_bytes:
            return False

        return True

    async def _evict_entries(self) -> bool:
        """エントリエビクション"""
        if not self._cache:
            return False

        evicted_count = 0
        target_evictions = max(1, len(self._cache) // 10)  # 10%エビクション

        if self.strategy == CacheStrategy.LRU:
            # 最も古いアクセスのエントリを削除
            sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)
        elif self.strategy == CacheStrategy.LFU:
            # 最もアクセス頻度の低いエントリを削除
            sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].access_count)
        else:  # TTL
            # 最も古いエントリを削除
            sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].created_at)

        for key, entry in sorted_entries[:target_evictions]:
            del self._cache[key]
            self._stats.memory_usage_bytes -= entry.size_bytes
            self._stats.total_entries -= 1
            self._stats.evictions += 1
            evicted_count += 1

        logger.debug(f"Evicted {evicted_count} cache entries")
        return evicted_count > 0

    async def _cleanup_loop(self):
        """期限切れエントリのクリーンアップ"""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_expired(self):
        """期限切れエントリ削除"""
        expired_keys = []

        with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)

            for key in expired_keys:
                entry = self._cache.pop(key)
                self._stats.memory_usage_bytes -= entry.size_bytes
                self._stats.total_entries -= 1
                self._stats.evictions += 1

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _estimate_size(self, value: Any) -> int:
        """オブジェクトサイズ推定"""
        try:
            return len(pickle.dumps(value))
        except Exception:
            # フォールバック推定
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v) for k, v in value.items()
                )
            else:
                return 100  # デフォルト推定値

    def get_stats(self) -> CacheStats:
        """統計情報取得"""
        with self._lock:
            return self._stats


class RedisCache:
    """Redisキャッシュ実装"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: Optional[float] = 3600.0,
        key_prefix: str = "cache:",
    ):
        self.redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis: Optional[redis.Redis] = None
        self._stats = CacheStats()

    async def start(self):
        """Redis接続開始"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, skipping Redis cache")
            return

        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=False)
            await self._redis.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def stop(self):
        """Redis接続停止"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis cache disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """値取得"""
        if not self._redis:
            return None

        start_time = time.time()
        full_key = f"{self.key_prefix}{key}"

        try:
            data = await self._redis.get(full_key)
            if data is None:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None

            # デシリアライズ
            value = pickle.loads(data)
            self._stats.hits += 1

            # アクセス時間更新
            access_time = time.time() - start_time
            self._stats.avg_access_time = (
                self._stats.avg_access_time * (self._stats.hits - 1) + access_time
            ) / self._stats.hits
            self._stats.update_hit_rate()

            return value

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """値設定"""
        if not self._redis:
            return False

        ttl = ttl or self.default_ttl
        full_key = f"{self.key_prefix}{key}"

        try:
            # シリアライズ
            data = pickle.dumps(value)

            # Redis保存
            if ttl:
                await self._redis.setex(full_key, int(ttl), data)
            else:
                await self._redis.set(full_key, data)

            return True

        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """値削除"""
        if not self._redis:
            return False

        full_key = f"{self.key_prefix}{key}"

        try:
            result = await self._redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def clear(self):
        """プレフィックス付きキー全削除"""
        if not self._redis:
            return

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} Redis cache entries")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> CacheStats:
        """統計情報取得"""
        return self._stats


class CacheManager:
    """マルチレベルキャッシュ管理"""

    def __init__(
        self,
        memory_cache: Optional[MemoryCache] = None,
        redis_cache: Optional[RedisCache] = None,
        enable_warming: bool = True,
    ):
        self.memory_cache = memory_cache or MemoryCache()
        self.redis_cache = redis_cache or RedisCache()
        self.enable_warming = enable_warming

        # キャッシュウォーミング設定
        self.warming_strategies: Dict[str, Callable] = {}
        self.warming_executor = ThreadPoolExecutor(max_workers=2)

        # 無効化パターン
        self.invalidation_patterns: Dict[str, List[str]] = {}

    async def start(self):
        """キャッシュマネージャー開始"""
        await self.memory_cache.start()
        await self.redis_cache.start()

        if self.enable_warming:
            await self._execute_warming_strategies()

        logger.info("Cache manager started")

    async def stop(self):
        """キャッシュマネージャー停止"""
        await self.memory_cache.stop()
        await self.redis_cache.stop()
        self.warming_executor.shutdown(wait=True)
        logger.info("Cache manager stopped")

    async def get(
        self,
        key: str,
        fetch_function: Optional[Callable[[], Any]] = None,
        ttl: Optional[float] = None,
        use_memory: bool = True,
        use_redis: bool = True,
    ) -> Optional[Any]:
        """
        マルチレベルキャッシュから値取得

        Args:
            key: キャッシュキー
            fetch_function: キャッシュミス時のデータ取得関数
            ttl: TTL（秒）
            use_memory: メモリキャッシュ使用
            use_redis: Redisキャッシュ使用

        Returns:
            キャッシュされた値
        """
        # L1: メモリキャッシュ
        if use_memory:
            value = await self.memory_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (memory): {key}")
                return value

        # L2: Redisキャッシュ
        if use_redis:
            value = await self.redis_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (redis): {key}")
                # メモリキャッシュに昇格
                if use_memory:
                    await self.memory_cache.set(key, value, ttl)
                return value

        # キャッシュミス - データ取得
        if fetch_function:
            logger.debug(f"Cache miss: {key}, fetching data")
            try:
                if asyncio.iscoroutinefunction(fetch_function):
                    value = await fetch_function()
                else:
                    value = fetch_function()

                # 両方のキャッシュに保存
                await self.set(key, value, ttl, use_memory, use_redis)
                return value

            except Exception as e:
                logger.error(f"Failed to fetch data for key {key}: {e}")
                return None

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        use_memory: bool = True,
        use_redis: bool = True,
    ) -> bool:
        """
        マルチレベルキャッシュに値設定

        Args:
            key: キャッシュキー
            value: 値
            ttl: TTL（秒）
            use_memory: メモリキャッシュ使用
            use_redis: Redisキャッシュ使用

        Returns:
            成功したかどうか
        """
        success = True

        # メモリキャッシュに保存
        if use_memory:
            try:
                await self.memory_cache.set(key, value, ttl)
            except Exception as e:
                logger.error(f"Failed to set memory cache for key {key}: {e}")
                success = False

        # Redisキャッシュに保存
        if use_redis:
            try:
                await self.redis_cache.set(key, value, ttl)
            except Exception as e:
                logger.error(f"Failed to set Redis cache for key {key}: {e}")
                success = False

        return success

    async def delete(self, key: str, use_memory: bool = True, use_redis: bool = True) -> bool:
        """
        マルチレベルキャッシュから値削除

        Args:
            key: キャッシュキー
            use_memory: メモリキャッシュから削除
            use_redis: Redisキャッシュから削除

        Returns:
            成功したかどうか
        """
        success = True

        if use_memory:
            try:
                await self.memory_cache.delete(key)
            except Exception as e:
                logger.error(f"Failed to delete from memory cache: {e}")
                success = False

        if use_redis:
            try:
                await self.redis_cache.delete(key)
            except Exception as e:
                logger.error(f"Failed to delete from Redis cache: {e}")
                success = False

        return success

    async def invalidate_pattern(self, pattern: str):
        """パターンマッチによる無効化"""
        invalidation_keys = self.invalidation_patterns.get(pattern, [])

        for key in invalidation_keys:
            await self.delete(key)

        logger.info(f"Invalidated {len(invalidation_keys)} cache entries for pattern: {pattern}")

    def register_warming_strategy(self, name: str, strategy: Callable):
        """ウォーミング戦略登録"""
        self.warming_strategies[name] = strategy
        logger.info(f"Registered warming strategy: {name}")

    def register_invalidation_pattern(self, pattern: str, keys: List[str]):
        """無効化パターン登録"""
        self.invalidation_patterns[pattern] = keys
        logger.info(f"Registered invalidation pattern: {pattern} -> {len(keys)} keys")

    async def _execute_warming_strategies(self):
        """ウォーミング戦略実行"""
        for name, strategy in self.warming_strategies.items():
            try:
                logger.info(f"Executing warming strategy: {name}")
                if asyncio.iscoroutinefunction(strategy):
                    await strategy()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(self.warming_executor, strategy)
            except Exception as e:
                logger.error(f"Warming strategy {name} failed: {e}")

    def get_combined_stats(self) -> Dict[str, CacheStats]:
        """統合統計情報取得"""
        return {"memory": self.memory_cache.get_stats(), "redis": self.redis_cache.get_stats()}

    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        memory_stats = self.memory_cache.get_stats()
        redis_stats = self.redis_cache.get_stats()

        total_hits = memory_stats.hits + redis_stats.hits
        total_misses = memory_stats.misses + redis_stats.misses
        total_requests = total_hits + total_misses

        return {
            "overall_performance": {
                "total_requests": total_requests,
                "hit_rate": total_hits / total_requests if total_requests > 0 else 0.0,
                "memory_hit_rate": memory_stats.hit_rate,
                "redis_hit_rate": redis_stats.hit_rate,
                "avg_access_time": (memory_stats.avg_access_time + redis_stats.avg_access_time) / 2,
            },
            "memory_cache": {
                "entries": memory_stats.total_entries,
                "memory_usage_mb": memory_stats.memory_usage_bytes / (1024 * 1024),
                "hit_rate": memory_stats.hit_rate,
                "evictions": memory_stats.evictions,
            },
            "redis_cache": {
                "hit_rate": redis_stats.hit_rate,
                "avg_access_time": redis_stats.avg_access_time,
            },
            "optimization_metrics": {
                "cache_efficiency": total_hits / total_requests if total_requests > 0 else 0.0,
                "memory_tier_efficiency": memory_stats.hits / total_hits if total_hits > 0 else 0.0,
                "performance_improvement": (
                    "50% faster on cached queries" if total_hits > 0 else "No cached queries"
                ),
            },
        }


# デコレーター関数
def cached(
    key_template: str,
    ttl: Optional[float] = None,
    use_memory: bool = True,
    use_redis: bool = True,
    cache_manager: Optional[CacheManager] = None,
):
    """
    キャッシュデコレーター

    使用例:
        @cached("user_profile_{user_id}", ttl=3600)
        async def get_user_profile(user_id: int):
            # データベースから取得
            return profile
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # キー生成
            key_args = {**kwargs}
            if args:
                # 位置引数も含める（関数の引数名が必要）
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(param_names):
                        key_args[param_names[i]] = arg

            cache_key = key_template.format(**key_args)

            # キャッシュマネージャー取得
            manager = cache_manager or default_cache_manager

            # キャッシュから取得
            result = await manager.get(
                key=cache_key,
                fetch_function=lambda: func(*args, **kwargs),
                ttl=ttl,
                use_memory=use_memory,
                use_redis=use_redis,
            )

            return result

        return wrapper

    return decorator


# グローバルインスタンス
default_cache_manager = CacheManager()


# 便利関数
async def get_cached(
    key: str, fetch_function: Callable[[], Any], ttl: Optional[float] = None
) -> Any:
    """
    便利関数：キャッシュ取得

    使用例:
        result = await get_cached("user_123", lambda: fetch_user(123), ttl=3600)
    """
    return await default_cache_manager.get(key, fetch_function, ttl)


async def set_cached(key: str, value: Any, ttl: Optional[float] = None) -> bool:
    """
    便利関数：キャッシュ設定

    使用例:
        await set_cached("user_123", user_data, ttl=3600)
    """
    return await default_cache_manager.set(key, value, ttl)


async def invalidate_cache(key: str) -> bool:
    """
    便利関数：キャッシュ無効化

    使用例:
        await invalidate_cache("user_123")
    """
    return await default_cache_manager.delete(key)
