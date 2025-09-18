"""
Rate Limiting Middleware
レート制限ミドルウェア

APIレート制限機能
- スライディングウィンドウベースのレート制限
- IPベースとユーザーベースの制限
- 異なるエンドポイントごとの制限設定
- DDoS攻撃防止
- 管理機能付き
"""

import time
import asyncio
import hashlib
from typing import Dict, Optional, List, Tuple, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import logging
import json
from enum import Enum

from app.core.config import settings


logger = logging.getLogger(__name__)


class LimitType(Enum):
    """制限タイプ"""
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


@dataclass
class RateLimit:
    """レート制限設定"""
    requests: int  # 許可するリクエスト数
    window: int    # 時間窓（秒）
    burst: int = 0  # バースト許可数（0は無制限）


@dataclass
class RequestRecord:
    """リクエスト記録"""
    timestamp: float
    endpoint: str
    method: str
    status_code: int = 0
    response_time: float = 0.0


class SlidingWindowCounter:
    """スライディングウィンドウカウンター"""

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self.lock = asyncio.Lock()

    async def add_request(self, timestamp: Optional[float] = None) -> None:
        """リクエストを記録"""
        if timestamp is None:
            timestamp = time.time()

        async with self.lock:
            self.requests.append(timestamp)
            await self._cleanup_old_requests(timestamp)

    async def get_count(self, current_time: Optional[float] = None) -> int:
        """現在のリクエスト数を取得"""
        if current_time is None:
            current_time = time.time()

        async with self.lock:
            await self._cleanup_old_requests(current_time)
            return len(self.requests)

    async def _cleanup_old_requests(self, current_time: float) -> None:
        """古いリクエスト記録を削除"""
        cutoff_time = current_time - self.window_seconds
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()

    async def reset(self) -> None:
        """カウンターをリセット"""
        async with self.lock:
            self.requests.clear()


class TokenBucket:
    """トークンバケットアルゴリズム実装"""

    def __init__(self, capacity: int, refill_rate: int, refill_period: int = 1):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # 補充レート（回/期間）
        self.refill_period = refill_period  # 補充期間（秒）
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """トークンを消費（成功時True）"""
        async with self.lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def _refill(self) -> None:
        """トークンを補充"""
        current_time = time.time()
        time_passed = current_time - self.last_refill

        if time_passed >= self.refill_period:
            periods_passed = int(time_passed // self.refill_period)
            tokens_to_add = periods_passed * self.refill_rate

            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = current_time

    async def get_tokens(self) -> int:
        """現在のトークン数を取得"""
        async with self.lock:
            await self._refill()
            return self.tokens


class RateLimitStorage:
    """レート制限データストレージ（メモリベース）"""

    def __init__(self):
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.request_history: Dict[str, List[RequestRecord]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}  # IP: ブロック終了時刻
        self.whitelist_ips: set = set()
        self.lock = asyncio.Lock()

    async def get_sliding_window(self, key: str, window_seconds: int) -> SlidingWindowCounter:
        """スライディングウィンドウカウンターを取得"""
        async with self.lock:
            if key not in self.sliding_windows:
                self.sliding_windows[key] = SlidingWindowCounter(window_seconds)
            return self.sliding_windows[key]

    async def get_token_bucket(self, key: str, capacity: int, refill_rate: int) -> TokenBucket:
        """トークンバケットを取得"""
        async with self.lock:
            if key not in self.token_buckets:
                self.token_buckets[key] = TokenBucket(capacity, refill_rate)
            return self.token_buckets[key]

    async def is_ip_blocked(self, ip: str) -> bool:
        """IPがブロックされているかチェック"""
        if ip in self.whitelist_ips:
            return False

        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                # ブロック期間終了
                del self.blocked_ips[ip]

        return False

    async def block_ip(self, ip: str, duration_seconds: int) -> None:
        """IPを一時ブロック"""
        if ip not in self.whitelist_ips:
            self.blocked_ips[ip] = time.time() + duration_seconds
            logger.warning(f"IP {ip} blocked for {duration_seconds} seconds")

    async def add_to_whitelist(self, ip: str) -> None:
        """IPをホワイトリストに追加"""
        self.whitelist_ips.add(ip)

    async def remove_from_whitelist(self, ip: str) -> None:
        """IPをホワイトリストから削除"""
        self.whitelist_ips.discard(ip)

    async def add_request_record(self, key: str, record: RequestRecord) -> None:
        """リクエスト記録を追加"""
        async with self.lock:
            self.request_history[key].append(record)

            # 古い記録を削除（最新1000件まで保持）
            if len(self.request_history[key]) > 1000:
                self.request_history[key] = self.request_history[key][-1000:]

    async def get_request_stats(self, key: str, minutes: int = 60) -> Dict[str, Any]:
        """リクエスト統計を取得"""
        cutoff_time = time.time() - (minutes * 60)
        recent_requests = [
            r for r in self.request_history.get(key, [])
            if r.timestamp > cutoff_time
        ]

        if not recent_requests:
            return {
                "total_requests": 0,
                "avg_response_time": 0,
                "status_codes": {},
                "endpoints": {}
            }

        status_codes = defaultdict(int)
        endpoints = defaultdict(int)
        total_response_time = 0

        for request in recent_requests:
            status_codes[str(request.status_code)] += 1
            endpoints[request.endpoint] += 1
            total_response_time += request.response_time

        return {
            "total_requests": len(recent_requests),
            "avg_response_time": total_response_time / len(recent_requests),
            "status_codes": dict(status_codes),
            "endpoints": dict(endpoints)
        }

    async def cleanup_old_data(self, max_age_hours: int = 24) -> None:
        """古いデータをクリーンアップ"""
        cutoff_time = time.time() - (max_age_hours * 3600)

        async with self.lock:
            # 古いリクエスト履歴を削除
            for key in list(self.request_history.keys()):
                self.request_history[key] = [
                    r for r in self.request_history[key]
                    if r.timestamp > cutoff_time
                ]
                if not self.request_history[key]:
                    del self.request_history[key]

            # 期限切れのIPブロックを削除
            current_time = time.time()
            expired_blocks = [
                ip for ip, expiry in self.blocked_ips.items()
                if current_time >= expiry
            ]
            for ip in expired_blocks:
                del self.blocked_ips[ip]


class RateLimitMiddleware:
    """レート制限ミドルウェア"""

    def __init__(self):
        self.storage = RateLimitStorage()

        # デフォルト制限設定
        self.default_limits = {
            LimitType.GLOBAL: RateLimit(requests=10000, window=60),  # 全体で10,000req/分
            LimitType.PER_IP: RateLimit(requests=1000, window=60),   # IP当たり1,000req/分
            LimitType.PER_USER: RateLimit(requests=5000, window=60), # ユーザー当たり5,000req/分
        }

        # エンドポイント固有の制限
        self.endpoint_limits = {
            "/auth/login": RateLimit(requests=10, window=60),      # ログイン試行制限
            "/auth/register": RateLimit(requests=5, window=300),   # 登録制限
            "/auth/reset-password": RateLimit(requests=3, window=600),  # パスワードリセット
            "/api/v1/sql/execute": RateLimit(requests=100, window=60),  # SQL実行制限
        }

        # 管理者・特権ユーザーの制限緩和
        self.privileged_limits = {
            LimitType.PER_USER: RateLimit(requests=50000, window=60),  # 50,000req/分
        }

        # DDoS検知設定
        self.ddos_threshold = 100  # 秒間リクエスト数
        self.ddos_block_duration = 300  # 5分間ブロック

    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """レート制限をチェック"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # IPブロックチェック
        if await self.storage.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return self._create_rate_limit_response(
                "IP address is temporarily blocked",
                retry_after=300
            )

        # ユーザー情報取得
        user_id = getattr(request.state, 'user_id', None)
        user_role = getattr(request.state, 'user', {}).get('scope', 'user')

        # 制限キー生成
        keys = self._generate_limit_keys(request, client_ip, user_id)

        # 各制限レベルをチェック
        for limit_type, key in keys.items():
            if await self._is_rate_limited(key, limit_type, request.url.path, user_role):
                # リクエスト記録
                record = RequestRecord(
                    timestamp=current_time,
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=429
                )
                await self.storage.add_request_record(key, record)

                return self._create_rate_limit_response(
                    f"Rate limit exceeded for {limit_type.value}",
                    retry_after=self._get_retry_after(limit_type)
                )

        # DDoS検知
        if await self._detect_ddos(client_ip):
            await self.storage.block_ip(client_ip, self.ddos_block_duration)
            return self._create_rate_limit_response(
                "Suspicious activity detected. IP temporarily blocked.",
                retry_after=self.ddos_block_duration
            )

        # 制限内の場合、カウンターを更新
        await self._update_counters(keys, current_time, request)

        return None  # 制限内

    async def _is_rate_limited(
        self, key: str, limit_type: LimitType, endpoint: str, user_role: str
    ) -> bool:
        """レート制限チェック"""
        # 制限設定取得
        if endpoint in self.endpoint_limits:
            limit_config = self.endpoint_limits[endpoint]
        elif user_role == 'admin' and limit_type in self.privileged_limits:
            limit_config = self.privileged_limits[limit_type]
        else:
            limit_config = self.default_limits.get(limit_type)

        if not limit_config:
            return False

        # スライディングウィンドウチェック
        counter = await self.storage.get_sliding_window(key, limit_config.window)
        current_count = await counter.get_count()

        return current_count >= limit_config.requests

    async def _update_counters(self, keys: Dict[LimitType, str], timestamp: float, request: Request) -> None:
        """カウンターを更新"""
        for limit_type, key in keys.items():
            # 制限設定取得
            limit_config = None
            if request.url.path in self.endpoint_limits:
                limit_config = self.endpoint_limits[request.url.path]
            else:
                limit_config = self.default_limits.get(limit_type)

            if limit_config:
                counter = await self.storage.get_sliding_window(key, limit_config.window)
                await counter.add_request(timestamp)

    async def _detect_ddos(self, client_ip: str) -> bool:
        """DDoS攻撃を検知"""
        key = f"ddos:{client_ip}"
        counter = await self.storage.get_sliding_window(key, 1)  # 1秒間のウィンドウ
        current_count = await counter.get_count()

        if current_count >= self.ddos_threshold:
            logger.critical(f"Potential DDoS attack detected from IP: {client_ip}")
            return True

        await counter.add_request()
        return False

    def _generate_limit_keys(self, request: Request, client_ip: str, user_id: Optional[str]) -> Dict[LimitType, str]:
        """制限キーを生成"""
        keys = {
            LimitType.GLOBAL: "global",
            LimitType.PER_IP: f"ip:{client_ip}",
            LimitType.PER_ENDPOINT: f"endpoint:{request.url.path}"
        }

        if user_id:
            keys[LimitType.PER_USER] = f"user:{user_id}"

        return keys

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

    def _create_rate_limit_response(self, message: str, retry_after: int = 60) -> JSONResponse:
        """レート制限レスポンスを作成"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": message,
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.default_limits[LimitType.PER_IP].requests),
                "X-RateLimit-Window": str(self.default_limits[LimitType.PER_IP].window),
            }
        )

    def _get_retry_after(self, limit_type: LimitType) -> int:
        """リトライ時間を取得"""
        limit_config = self.default_limits.get(limit_type)
        return limit_config.window if limit_config else 60

    async def get_rate_limit_status(self, request: Request) -> Dict[str, Any]:
        """現在のレート制限状態を取得"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        keys = self._generate_limit_keys(request, client_ip, user_id)

        status = {}
        for limit_type, key in keys.items():
            limit_config = self.default_limits.get(limit_type)
            if limit_config:
                counter = await self.storage.get_sliding_window(key, limit_config.window)
                current_count = await counter.get_count()

                status[limit_type.value] = {
                    "limit": limit_config.requests,
                    "window": limit_config.window,
                    "current": current_count,
                    "remaining": max(0, limit_config.requests - current_count),
                    "reset_time": time.time() + limit_config.window
                }

        return status

    async def add_response_headers(self, response: Response, request: Request) -> None:
        """レスポンスにレート制限ヘッダーを追加"""
        try:
            status = await self.get_rate_limit_status(request)

            # IP制限情報をヘッダーに追加
            if LimitType.PER_IP.value in status:
                ip_status = status[LimitType.PER_IP.value]
                response.headers["X-RateLimit-Limit"] = str(ip_status["limit"])
                response.headers["X-RateLimit-Remaining"] = str(ip_status["remaining"])
                response.headers["X-RateLimit-Reset"] = str(int(ip_status["reset_time"]))

        except Exception as e:
            logger.error(f"Failed to add rate limit headers: {e}")

    async def whitelist_ip(self, ip: str) -> None:
        """IPをホワイトリストに追加"""
        await self.storage.add_to_whitelist(ip)
        logger.info(f"IP {ip} added to whitelist")

    async def blacklist_ip(self, ip: str, duration_seconds: int = 3600) -> None:
        """IPをブラックリストに追加"""
        await self.storage.block_ip(ip, duration_seconds)
        logger.info(f"IP {ip} added to blacklist for {duration_seconds} seconds")

    async def get_statistics(self, minutes: int = 60) -> Dict[str, Any]:
        """レート制限統計を取得"""
        stats = {
            "blocked_ips": len(self.storage.blocked_ips),
            "whitelisted_ips": len(self.storage.whitelist_ips),
            "active_windows": len(self.storage.sliding_windows),
            "request_history_keys": len(self.storage.request_history)
        }

        # グローバル統計
        global_stats = await self.storage.get_request_stats("global", minutes)
        stats["global"] = global_stats

        return stats

    async def cleanup(self) -> None:
        """定期クリーンアップ実行"""
        await self.storage.cleanup_old_data()
        logger.info("Rate limit data cleanup completed")


# グローバルインスタンス
rate_limit_middleware = RateLimitMiddleware()


# 定期クリーンアップタスク
async def periodic_cleanup():
    """定期クリーンアップタスク"""
    while True:
        try:
            await asyncio.sleep(3600)  # 1時間ごと
            await rate_limit_middleware.cleanup()
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")


# デコレータ関数
def rate_limit(requests: int, window: int = 60):
    """レート制限デコレータ"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # リクエストオブジェクトを見つける
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                # カスタム制限チェック
                client_ip = rate_limit_middleware._get_client_ip(request)
                key = f"custom:{func.__name__}:{client_ip}"

                counter = await rate_limit_middleware.storage.get_sliding_window(key, window)
                current_count = await counter.get_count()

                if current_count >= requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: {requests} requests per {window} seconds"
                    )

                await counter.add_request()

            return await func(*args, **kwargs)
        return wrapper
    return decorator