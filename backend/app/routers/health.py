"""
ヘルスチェック・監視関連APIエンドポイント

システムヘルス、メトリクス、パフォーマンス監視などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import psutil
import platform
import asyncio
import time

from app.core.database import get_db, ConnectionPoolStats
from app.core.config import settings
from app.dependencies import health_check_dependencies

router = APIRouter()


# Response Models
class HealthStatus(BaseModel):
    """基本ヘルスステータス"""
    status: str = Field(..., description="全体ステータス（healthy/degraded/unhealthy）")
    timestamp: datetime = Field(..., description="チェック時刻")
    version: str = Field(..., description="アプリケーションバージョン")
    uptime: float = Field(..., description="稼働時間（秒）")


class ServiceHealth(BaseModel):
    """サービス別ヘルス"""
    status: str = Field(..., description="サービスステータス")
    response_time: Optional[float] = Field(None, description="レスポンス時間（ミリ秒）")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    last_check: datetime = Field(..., description="最終チェック時刻")


class DetailedHealthResponse(BaseModel):
    """詳細ヘルスレスポンス"""
    overall: HealthStatus
    services: Dict[str, ServiceHealth] = Field(..., description="サービス別ステータス")
    database: Dict[str, Any] = Field(..., description="データベース情報")
    system: Dict[str, Any] = Field(..., description="システム情報")
    performance: Dict[str, Any] = Field(..., description="パフォーマンス情報")


class MetricsResponse(BaseModel):
    """メトリクス情報"""
    timestamp: datetime
    application: Dict[str, Any] = Field(..., description="アプリケーションメトリクス")
    system: Dict[str, Any] = Field(..., description="システムメトリクス")
    database: Dict[str, Any] = Field(..., description="データベースメトリクス")
    custom: Dict[str, Any] = Field(..., description="カスタムメトリクス")


class AlertRule(BaseModel):
    """アラートルール"""
    name: str = Field(..., description="ルール名")
    metric: str = Field(..., description="監視メトリクス")
    operator: str = Field(..., description="比較演算子")
    threshold: float = Field(..., description="閾値")
    enabled: bool = Field(True, description="有効フラグ")


class AlertStatus(BaseModel):
    """アラートステータス"""
    rule_name: str
    status: str = Field(..., description="アラート状態（ok/warning/critical）")
    current_value: float = Field(..., description="現在値")
    threshold: float = Field(..., description="閾値")
    message: str = Field(..., description="アラートメッセージ")
    triggered_at: Optional[datetime] = Field(None, description="アラート発生時刻")


# アプリケーション開始時刻（グローバル変数）
app_start_time = time.time()


@router.get("/", response_model=HealthStatus)
async def basic_health_check():
    """
    基本ヘルスチェック

    アプリケーションの基本的な稼働状況を確認します。
    """
    try:
        uptime = time.time() - app_start_time

        return HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime=uptime
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ヘルスチェック中にエラーが発生しました: {str(e)}"
        )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    include_system: bool = Query(True, description="システム情報を含める"),
    include_performance: bool = Query(True, description="パフォーマンス情報を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    詳細ヘルスチェック

    システム全体の詳細な稼働状況を確認します。
    """
    try:
        start_time = time.time()

        # 基本情報
        uptime = time.time() - app_start_time
        overall = HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime=uptime
        )

        # サービス別チェック
        services = {}

        # データベースチェック
        db_start = time.time()
        try:
            result = await db.execute("SELECT 1")
            await result.fetchone()
            db_response_time = (time.time() - db_start) * 1000
            services["database"] = ServiceHealth(
                status="healthy",
                response_time=db_response_time,
                last_check=datetime.utcnow()
            )
        except Exception as e:
            services["database"] = ServiceHealth(
                status="unhealthy",
                error_message=str(e),
                last_check=datetime.utcnow()
            )
            overall.status = "degraded"

        # Redis/キャッシュチェック（実装予定）
        services["cache"] = ServiceHealth(
            status="healthy",
            response_time=1.0,
            last_check=datetime.utcnow()
        )

        # データベース詳細情報
        pool_stats = ConnectionPoolStats.get_pool_stats()
        database_info = {
            "pool_stats": pool_stats,
            "connection_status": "connected",
            "pool_utilization": pool_stats.get("utilization", 0)
        }

        # システム情報
        system_info = {}
        if include_system:
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                system_info = {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "used": disk.used,
                        "percent": (disk.used / disk.total) * 100
                    }
                }
            except Exception as e:
                system_info = {"error": f"システム情報取得エラー: {str(e)}"}

        # パフォーマンス情報
        performance_info = {}
        if include_performance:
            response_time = (time.time() - start_time) * 1000
            performance_info = {
                "health_check_response_time": response_time,
                "database_pool_utilization": pool_stats.get("utilization", 0),
                "memory_usage_percent": psutil.virtual_memory().percent if include_system else None,
                "cpu_usage_percent": psutil.cpu_percent() if include_system else None,
                "uptime_hours": uptime / 3600
            }

        # 全体ステータス判定
        unhealthy_services = [name for name, service in services.items() if service.status == "unhealthy"]
        if unhealthy_services:
            overall.status = "unhealthy" if len(unhealthy_services) > 1 else "degraded"

        return DetailedHealthResponse(
            overall=overall,
            services=services,
            database=database_info,
            system=system_info,
            performance=performance_info
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"詳細ヘルスチェック中にエラーが発生しました: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    include_system: bool = Query(True, description="システムメトリクスを含める"),
    include_custom: bool = Query(True, description="カスタムメトリクスを含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    システムメトリクス取得

    パフォーマンス監視用のメトリクス情報を取得します。
    """
    try:
        timestamp = datetime.utcnow()

        # アプリケーションメトリクス
        uptime = time.time() - app_start_time
        pool_stats = ConnectionPoolStats.get_pool_stats()

        application_metrics = {
            "uptime_seconds": uptime,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "database_pool": pool_stats,
            "settings": {
                "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
                "api_rate_limit": settings.API_RATE_LIMIT,
                "slow_query_threshold": settings.SLOW_QUERY_THRESHOLD
            }
        }

        # システムメトリクス
        system_metrics = {}
        if include_system:
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                cpu_times = psutil.cpu_times()

                system_metrics = {
                    "cpu": {
                        "count": psutil.cpu_count(),
                        "percent": psutil.cpu_percent(interval=1),
                        "times": {
                            "user": cpu_times.user,
                            "system": cpu_times.system,
                            "idle": cpu_times.idle
                        }
                    },
                    "memory": {
                        "total_bytes": memory.total,
                        "available_bytes": memory.available,
                        "used_bytes": memory.used,
                        "percent": memory.percent,
                        "cached_bytes": getattr(memory, 'cached', 0),
                        "buffers_bytes": getattr(memory, 'buffers', 0)
                    },
                    "disk": {
                        "total_bytes": disk.total,
                        "free_bytes": disk.free,
                        "used_bytes": disk.used,
                        "percent": (disk.used / disk.total) * 100
                    },
                    "network": _get_network_stats(),
                    "processes": len(psutil.pids())
                }
            except Exception as e:
                system_metrics = {"error": f"システムメトリクス取得エラー: {str(e)}"}

        # データベースメトリクス
        database_metrics = {
            "pool_stats": pool_stats,
            "connection_count": pool_stats.get("checked_out", 0),
            "pool_utilization_percent": pool_stats.get("utilization", 0)
        }

        # カスタムメトリクス（アプリケーション固有）
        custom_metrics = {}
        if include_custom:
            custom_metrics = {
                "job_processing": {
                    "total_jobs": await _get_job_count(db),
                    "active_jobs": await _get_active_job_count(db),
                },
                "user_activity": {
                    "total_users": await _get_user_count(db),
                    "active_users_24h": await _get_active_user_count(db),
                },
                "matching": {
                    "scores_calculated_today": await _get_scores_calculated_today(db),
                    "recommendations_generated_today": await _get_recommendations_today(db),
                }
            }

        return MetricsResponse(
            timestamp=timestamp,
            application=application_metrics,
            system=system_metrics,
            database=database_metrics,
            custom=custom_metrics
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メトリクス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/alerts")
async def get_alert_status(
    db: AsyncSession = Depends(get_db)
):
    """
    アラートステータス取得

    設定されたアラートルールの現在のステータスを取得します。
    """
    try:
        # アラートルール定義
        alert_rules = [
            AlertRule(
                name="high_memory_usage",
                metric="memory_percent",
                operator="gt",
                threshold=80.0
            ),
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_percent",
                operator="gt",
                threshold=90.0
            ),
            AlertRule(
                name="high_db_pool_usage",
                metric="db_pool_utilization",
                operator="gt",
                threshold=85.0
            ),
            AlertRule(
                name="slow_response_time",
                metric="avg_response_time",
                operator="gt",
                threshold=1000.0  # 1秒
            )
        ]

        alerts = []

        # 現在のシステム状態を取得
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            pool_stats = ConnectionPoolStats.get_pool_stats()
            db_pool_utilization = pool_stats.get("utilization", 0)

            current_values = {
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "db_pool_utilization": db_pool_utilization,
                "avg_response_time": 500.0  # 仮の値（実際は計測が必要）
            }

            # 各ルールをチェック
            for rule in alert_rules:
                if not rule.enabled:
                    continue

                current_value = current_values.get(rule.metric, 0)

                # アラート状態判定
                alert_status = "ok"
                message = f"{rule.metric}: {current_value:.2f}"
                triggered_at = None

                if rule.operator == "gt" and current_value > rule.threshold:
                    alert_status = "critical" if current_value > rule.threshold * 1.2 else "warning"
                    message = f"{rule.metric} is {current_value:.2f} (threshold: {rule.threshold})"
                    triggered_at = datetime.utcnow()
                elif rule.operator == "lt" and current_value < rule.threshold:
                    alert_status = "critical" if current_value < rule.threshold * 0.8 else "warning"
                    message = f"{rule.metric} is {current_value:.2f} (threshold: {rule.threshold})"
                    triggered_at = datetime.utcnow()

                alerts.append(AlertStatus(
                    rule_name=rule.name,
                    status=alert_status,
                    current_value=current_value,
                    threshold=rule.threshold,
                    message=message,
                    triggered_at=triggered_at
                ))

        except Exception as e:
            # システム情報取得に失敗した場合
            alerts.append(AlertStatus(
                rule_name="system_monitoring_error",
                status="critical",
                current_value=0,
                threshold=0,
                message=f"システム監視エラー: {str(e)}",
                triggered_at=datetime.utcnow()
            ))

        return {
            "timestamp": datetime.utcnow(),
            "total_rules": len(alert_rules),
            "active_alerts": len([a for a in alerts if a.status != "ok"]),
            "alerts": alerts
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アラートステータス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
):
    """
    レディネスチェック

    アプリケーションがリクエストを受け付ける準備ができているかチェックします。
    """
    try:
        # データベース接続チェック
        result = await db.execute("SELECT 1")
        await result.fetchone()

        # 必要な設定値チェック
        required_settings = [
            "DATABASE_URL",
            "APP_NAME",
            "ENVIRONMENT"
        ]

        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)

        if missing_settings:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"必要な設定が不足しています: {', '.join(missing_settings)}"
            )

        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "checks": {
                "database": "ok",
                "configuration": "ok"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"レディネスチェック失敗: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """
    ライブネスチェック

    アプリケーションプロセスが生きているかチェックします。
    """
    try:
        # シンプルなプロセス稼働チェック
        uptime = time.time() - app_start_time

        return {
            "status": "alive",
            "timestamp": datetime.utcnow(),
            "uptime": uptime,
            "pid": psutil.Process().pid
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ライブネスチェック失敗: {str(e)}"
        )


# ヘルパー関数
def _get_network_stats():
    """ネットワーク統計情報を取得"""
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout
        }
    except:
        return {}


async def _get_job_count(db: AsyncSession) -> int:
    """求人総数を取得"""
    try:
        result = await db.execute("SELECT COUNT(*) FROM jobs")
        count = await result.scalar()
        return count or 0
    except:
        return 0


async def _get_active_job_count(db: AsyncSession) -> int:
    """有効求人数を取得"""
    try:
        result = await db.execute("SELECT COUNT(*) FROM jobs WHERE is_active = true")
        count = await result.scalar()
        return count or 0
    except:
        return 0


async def _get_user_count(db: AsyncSession) -> int:
    """ユーザー総数を取得"""
    try:
        result = await db.execute("SELECT COUNT(*) FROM users")
        count = await result.scalar()
        return count or 0
    except:
        return 0


async def _get_active_user_count(db: AsyncSession) -> int:
    """24時間以内にアクティブなユーザー数を取得"""
    try:
        result = await db.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        count = await result.scalar()
        return count or 0
    except:
        return 0


async def _get_scores_calculated_today(db: AsyncSession) -> int:
    """今日計算されたスコア数を取得"""
    try:
        result = await db.execute("""
            SELECT COUNT(*)
            FROM matching_results
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        count = await result.scalar()
        return count or 0
    except:
        return 0


async def _get_recommendations_today(db: AsyncSession) -> int:
    """今日生成された推薦数を取得"""
    try:
        result = await db.execute("""
            SELECT COUNT(*)
            FROM user_recommendations
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        count = await result.scalar()
        return count or 0
    except:
        return 0