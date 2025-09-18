"""
Rate Limiting Administration Router
レート制限管理ルーター

レート制限の管理・監視・設定用APIエンドポイント
- レート制限統計情報
- IPホワイトリスト/ブラックリスト管理
- 制限設定の動的変更
- DDoS攻撃監視
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, IPvAnyAddress
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.middleware.auth import get_admin_user
from app.middleware.rate_limit import rate_limit_middleware, LimitType, RateLimit
from app.models.common import BaseResponse


logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic Models
class RateLimitStatus(BaseModel):
    """レート制限状態"""
    limit_type: str
    limit: int
    window: int
    current: int
    remaining: int
    reset_time: datetime


class IPManagementRequest(BaseModel):
    """IP管理リクエスト"""
    ip_address: str
    duration_seconds: Optional[int] = 3600
    reason: Optional[str] = ""


class RateLimitConfigRequest(BaseModel):
    """レート制限設定リクエスト"""
    limit_type: str
    requests: int
    window: int
    endpoint: Optional[str] = None


class StatisticsResponse(BaseModel):
    """統計レスポンス"""
    period_minutes: int
    total_requests: int
    blocked_requests: int
    avg_response_time: float
    top_endpoints: Dict[str, int]
    top_ips: Dict[str, int]
    status_codes: Dict[str, int]


@router.get("/status", response_model=List[RateLimitStatus], summary="レート制限状態取得")
async def get_rate_limit_status(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> List[RateLimitStatus]:
    """
    現在のレート制限状態を取得

    すべての制限タイプの現在の使用状況を表示します。
    """
    try:
        # モックリクエストを作成（統計目的）
        from fastapi import Request
        from unittest.mock import MagicMock

        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "admin"
        mock_request.state.user_id = admin_user.get("sub")

        status_data = await rate_limit_middleware.get_rate_limit_status(mock_request)

        result = []
        for limit_type, data in status_data.items():
            result.append(RateLimitStatus(
                limit_type=limit_type,
                limit=data["limit"],
                window=data["window"],
                current=data["current"],
                remaining=data["remaining"],
                reset_time=datetime.fromtimestamp(data["reset_time"])
            ))

        return result

    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )


@router.get("/statistics", response_model=StatisticsResponse, summary="レート制限統計取得")
async def get_rate_limit_statistics(
    minutes: int = Query(default=60, ge=1, le=1440, description="統計期間（分）"),
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> StatisticsResponse:
    """
    レート制限統計情報を取得

    指定期間のリクエスト統計、ブロック情報などを取得します。
    """
    try:
        stats = await rate_limit_middleware.get_statistics(minutes)

        # 追加統計計算
        global_stats = stats.get("global", {})

        return StatisticsResponse(
            period_minutes=minutes,
            total_requests=global_stats.get("total_requests", 0),
            blocked_requests=stats.get("blocked_ips", 0),
            avg_response_time=global_stats.get("avg_response_time", 0),
            top_endpoints=global_stats.get("endpoints", {}),
            top_ips={},  # プライバシー保護のため空
            status_codes=global_stats.get("status_codes", {})
        )

    except Exception as e:
        logger.error(f"Failed to get rate limit statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.post("/whitelist", response_model=BaseResponse, summary="IPホワイトリスト追加")
async def add_ip_to_whitelist(
    request: IPManagementRequest,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> BaseResponse:
    """
    IPアドレスをホワイトリストに追加

    指定されたIPアドレスはレート制限を受けません。
    """
    try:
        await rate_limit_middleware.whitelist_ip(request.ip_address)

        logger.info(
            f"Admin {admin_user.get('email')} added {request.ip_address} to whitelist. "
            f"Reason: {request.reason}"
        )

        return BaseResponse(
            message=f"IP address {request.ip_address} added to whitelist"
        )

    except Exception as e:
        logger.error(f"Failed to add IP to whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add IP to whitelist"
        )


@router.delete("/whitelist/{ip_address}", response_model=BaseResponse, summary="IPホワイトリスト削除")
async def remove_ip_from_whitelist(
    ip_address: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> BaseResponse:
    """
    IPアドレスをホワイトリストから削除

    指定されたIPアドレスは再びレート制限を受けるようになります。
    """
    try:
        await rate_limit_middleware.storage.remove_from_whitelist(ip_address)

        logger.info(
            f"Admin {admin_user.get('email')} removed {ip_address} from whitelist"
        )

        return BaseResponse(
            message=f"IP address {ip_address} removed from whitelist"
        )

    except Exception as e:
        logger.error(f"Failed to remove IP from whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove IP from whitelist"
        )


@router.post("/blacklist", response_model=BaseResponse, summary="IPブラックリスト追加")
async def add_ip_to_blacklist(
    request: IPManagementRequest,
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> BaseResponse:
    """
    IPアドレスをブラックリストに追加

    指定されたIPアドレスからのリクエストを一定時間ブロックします。
    """
    try:
        duration = request.duration_seconds or 3600
        await rate_limit_middleware.blacklist_ip(request.ip_address, duration)

        logger.info(
            f"Admin {admin_user.get('email')} blocked {request.ip_address} for {duration} seconds. "
            f"Reason: {request.reason}"
        )

        return BaseResponse(
            message=f"IP address {request.ip_address} blocked for {duration} seconds"
        )

    except Exception as e:
        logger.error(f"Failed to add IP to blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add IP to blacklist"
        )


@router.get("/blocked-ips", response_model=Dict[str, float], summary="ブロック中IP一覧")
async def get_blocked_ips(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, float]:
    """
    現在ブロック中のIPアドレス一覧を取得

    IPアドレスとブロック解除時刻のマッピングを返します。
    """
    try:
        blocked_ips = rate_limit_middleware.storage.blocked_ips.copy()

        # 時刻をISO形式に変換（フロントエンド表示用）
        result = {}
        for ip, expiry_timestamp in blocked_ips.items():
            result[ip] = expiry_timestamp

        return result

    except Exception as e:
        logger.error(f"Failed to get blocked IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blocked IPs"
        )


@router.get("/whitelisted-ips", response_model=List[str], summary="ホワイトリストIP一覧")
async def get_whitelisted_ips(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> List[str]:
    """
    現在ホワイトリストに登録されているIPアドレス一覧を取得
    """
    try:
        whitelisted_ips = list(rate_limit_middleware.storage.whitelist_ips)
        return whitelisted_ips

    except Exception as e:
        logger.error(f"Failed to get whitelisted IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve whitelisted IPs"
        )


@router.post("/reset-counters", response_model=BaseResponse, summary="カウンターリセット")
async def reset_rate_limit_counters(
    ip_address: Optional[str] = Query(None, description="リセット対象のIPアドレス（省略時は全体）"),
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> BaseResponse:
    """
    レート制限カウンターをリセット

    指定されたIPまたは全体のレート制限カウンターをリセットします。
    """
    try:
        if ip_address:
            # 特定IPのカウンターリセット
            keys_to_reset = [
                f"ip:{ip_address}",
                f"ddos:{ip_address}"
            ]

            for key in keys_to_reset:
                if key in rate_limit_middleware.storage.sliding_windows:
                    await rate_limit_middleware.storage.sliding_windows[key].reset()

            logger.info(
                f"Admin {admin_user.get('email')} reset rate limit counters for IP {ip_address}"
            )

            return BaseResponse(
                message=f"Rate limit counters reset for IP {ip_address}"
            )
        else:
            # 全体のカウンターリセット
            for counter in rate_limit_middleware.storage.sliding_windows.values():
                await counter.reset()

            logger.info(
                f"Admin {admin_user.get('email')} reset all rate limit counters"
            )

            return BaseResponse(
                message="All rate limit counters have been reset"
            )

    except Exception as e:
        logger.error(f"Failed to reset rate limit counters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset counters"
        )


@router.post("/cleanup", response_model=BaseResponse, summary="データクリーンアップ")
async def cleanup_rate_limit_data(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> BaseResponse:
    """
    古いレート制限データをクリーンアップ

    期限切れのブロック情報や古いリクエスト履歴を削除します。
    """
    try:
        await rate_limit_middleware.cleanup()

        logger.info(
            f"Admin {admin_user.get('email')} triggered rate limit data cleanup"
        )

        return BaseResponse(
            message="Rate limit data cleanup completed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to cleanup rate limit data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup data"
        )


@router.get("/config", response_model=Dict[str, Any], summary="レート制限設定取得")
async def get_rate_limit_config(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    現在のレート制限設定を取得

    デフォルト制限とエンドポイント固有の制限設定を返します。
    """
    try:
        config = {
            "default_limits": {
                limit_type.value: {
                    "requests": limit.requests,
                    "window": limit.window,
                    "burst": limit.burst
                }
                for limit_type, limit in rate_limit_middleware.default_limits.items()
            },
            "endpoint_limits": {
                endpoint: {
                    "requests": limit.requests,
                    "window": limit.window,
                    "burst": limit.burst
                }
                for endpoint, limit in rate_limit_middleware.endpoint_limits.items()
            },
            "ddos_threshold": rate_limit_middleware.ddos_threshold,
            "ddos_block_duration": rate_limit_middleware.ddos_block_duration
        }

        return config

    except Exception as e:
        logger.error(f"Failed to get rate limit config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )


@router.get("/health", response_model=Dict[str, Any], summary="レート制限システム健全性チェック")
async def get_rate_limit_health(
    admin_user: Dict[str, Any] = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    レート制限システムの健全性をチェック

    システムの状態、リソース使用状況、パフォーマンス指標を返します。
    """
    try:
        storage = rate_limit_middleware.storage

        health_data = {
            "status": "healthy",
            "storage": {
                "sliding_windows": len(storage.sliding_windows),
                "token_buckets": len(storage.token_buckets),
                "request_history_keys": len(storage.request_history),
                "blocked_ips": len(storage.blocked_ips),
                "whitelisted_ips": len(storage.whitelist_ips)
            },
            "performance": {
                "avg_check_time": 0,  # 実際の測定値に置き換え
                "memory_usage": 0,    # メモリ使用量
                "active_locks": 0     # アクティブなロック数
            },
            "alerts": []
        }

        # 健全性チェック
        if len(storage.blocked_ips) > 1000:
            health_data["alerts"].append("High number of blocked IPs detected")

        if len(storage.sliding_windows) > 10000:
            health_data["alerts"].append("High number of active rate limit windows")

        # アラートがある場合はステータス変更
        if health_data["alerts"]:
            health_data["status"] = "warning"

        return health_data

    except Exception as e:
        logger.error(f"Failed to get rate limit health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health information"
        )