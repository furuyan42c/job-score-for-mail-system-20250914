"""
TDD Phase 2: GREEN - 契約テストをパスするための最小実装

このファイルは契約テスト（T007-T013）をパスするための
最小限のエンドポイント実装を含みます。
後のリファクタリングフェーズで実際のビジネスロジックに置き換えます。
"""

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
import re

from app.core.database import get_db
from app.services.job_import import JobImportService
from app.services.scoring import ScoringService
from app.services.matching import MatchingService
from app.services.email_generation import EmailGenerationService
from app.services.sql_executor import SQLExecutorService
from app.services.monitoring import MonitoringService

router = APIRouter()


# ============================================================================
# T007: POST /jobs/import - ジョブインポート
# ============================================================================

@router.post("/jobs/import", status_code=200)
async def import_jobs(
    file: UploadFile = File(..., description="CSVファイル"),
    mapping_config: Optional[str] = None,
    dry_run: bool = False,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T007 REFACTOR: 実際のCSVジョブインポート実装"""
    try:
        # ファイル形式バリデーション
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )

        # ファイルサイズ制限（10MB）
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size must be less than 10MB"
            )

        # 実際のインポート処理
        import_service = JobImportService(db)
        result = await import_service.import_from_csv(
            file_content=file_content,
            filename=file.filename,
            mapping_config=json.loads(mapping_config) if mapping_config else None,
            dry_run=dry_run
        )

        return {
            "imported": result.imported_count,
            "failed": result.failed_count,
            "message": result.message,
            "job_ids": result.job_ids,
            "batch_id": result.batch_id,
            "validation_errors": result.validation_errors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ============================================================================
# T008: POST /scoring/calculate - スコアリング計算
# ============================================================================

@router.post("/scoring/calculate", status_code=200)
async def calculate_scoring(
    user_id: int,
    job_ids: Optional[List[int]] = None,
    scoring_config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T008 REFACTOR: 実際のスコアリング計算実装"""
    try:
        # 入力バリデーション
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id must be positive"
            )

        if job_ids and len(job_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 1000 jobs can be processed at once"
            )

        # 実際のスコアリング処理
        scoring_service = ScoringService(db)
        scores = await scoring_service.calculate_user_job_scores(
            user_id=user_id,
            job_ids=job_ids,
            config=scoring_config or {}
        )

        return {
            "user_id": user_id,
            "scores": [
                {
                    "job_id": score.job_id,
                    "score": score.total_score,
                    "breakdown": score.score_breakdown,
                    "factors": score.scoring_factors
                }
                for score in scores
            ],
            "calculated_at": datetime.now().isoformat(),
            "scoring_version": scores[0].scoring_version if scores else "1.0"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring calculation failed: {str(e)}"
        )


# ============================================================================
# T009: POST /matching/generate - マッチング生成
# ============================================================================

@router.post("/matching/generate", status_code=200)
async def generate_matching(
    user_ids: List[int],
    matching_config: Optional[Dict[str, Any]] = None,
    async_processing: bool = True,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T009 REFACTOR: 実際のマッチング生成実装"""
    try:
        # 入力バリデーション
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_ids cannot be empty"
            )

        if len(user_ids) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 500 users can be processed at once"
            )

        # 実際のマッチング処理
        matching_service = MatchingService(db)

        if async_processing:
            # 非同期バッチ処理
            batch_result = await matching_service.create_matching_batch(
                user_ids=user_ids,
                config=matching_config or {}
            )

            return {
                "batch_id": batch_result.batch_id,
                "users_to_process": len(user_ids),
                "status": "pending",
                "created_at": batch_result.created_at.isoformat(),
                "estimated_completion": batch_result.estimated_completion.isoformat() if batch_result.estimated_completion else None
            }
        else:
            # 同期処理（小さなバッチ用）
            matching_results = await matching_service.generate_matches_sync(
                user_ids=user_ids,
                config=matching_config or {}
            )

            return {
                "batch_id": str(uuid.uuid4()),
                "users_processed": len(user_ids),
                "matches_generated": sum(len(result.matches) for result in matching_results),
                "status": "completed",
                "created_at": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching generation failed: {str(e)}"
        )


# ============================================================================
# T010: GET /matching/user/{user_id} - ユーザーマッチング取得
# ============================================================================

@router.get("/matching/user/{user_id}", status_code=200)
async def get_user_matching(
    user_id: int,
    limit: int = 40,
    min_score: Optional[float] = None,
    include_details: bool = False,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T010 REFACTOR: 実際のユーザーマッチング取得実装"""
    try:
        # 入力バリデーション
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id must be positive"
            )

        if limit <= 0 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 100"
            )

        # 実際のマッチング取得処理
        matching_service = MatchingService(db)
        user_matches = await matching_service.get_user_matches(
            user_id=user_id,
            limit=limit,
            min_score=min_score,
            include_job_details=include_details
        )

        if not user_matches:
            return {
                "user_id": user_id,
                "matches": [],
                "generated_at": None,
                "message": "No matches found for this user"
            }

        return {
            "user_id": user_id,
            "matches": [
                {
                    "job_id": match.job_id,
                    "score": match.matching_score,
                    "rank": match.rank,
                    "match_reasons": match.match_reasons,
                    "job_details": match.job_details if include_details else None
                }
                for match in user_matches.matches
            ],
            "generated_at": user_matches.generated_at.isoformat() if user_matches.generated_at else None,
            "total_matches": user_matches.total_count,
            "matching_version": user_matches.matching_version
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user matches: {str(e)}"
        )


# ============================================================================
# T011: POST /email/generate - メール生成
# ============================================================================

@router.post("/email/generate", status_code=200)
async def generate_email(
    user_id: int,
    template_id: str = "default",
    email_config: Optional[Dict[str, Any]] = None,
    preview_mode: bool = False,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T011 REFACTOR: 実際のメール生成実装"""
    try:
        # 入力バリデーション
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id must be positive"
            )

        # 実際のメール生成処理
        email_service = EmailGenerationService(db)
        email_result = await email_service.generate_user_email(
            user_id=user_id,
            template_id=template_id,
            config=email_config or {},
            preview_only=preview_mode
        )

        return {
            "email_id": email_result.email_id,
            "user_id": user_id,
            "template_id": template_id,
            "subject": email_result.subject,
            "body": email_result.body_html,
            "plain_text": email_result.body_text,
            "status": email_result.status,
            "created_at": email_result.created_at.isoformat(),
            "job_count": email_result.job_count,
            "personalization_data": email_result.personalization_data,
            "preview_url": email_result.preview_url if preview_mode else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {str(e)}"
        )


# ============================================================================
# T012: POST /sql/execute - SQL実行（読み取り専用）
# ============================================================================

@router.post("/sql/execute", status_code=200)
async def execute_sql(
    query: str,
    max_rows: int = 1000,
    timeout_seconds: int = 30,
    explain_plan: bool = False,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T012 REFACTOR: 実際のSQL実行実装（読み取り専用強化）"""
    try:
        # 入力バリデーション
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )

        if len(query) > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query too long (max 10,000 characters)"
            )

        # 実際のSQL実行処理
        sql_service = SQLExecutorService(db)

        # セキュリティチェック（より厳密）
        security_check = sql_service.validate_read_only_query(query)
        if not security_check.is_safe:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Query contains unsafe operations: {security_check.violations}"
            )

        # クエリ実行
        execution_result = await sql_service.execute_read_only_query(
            query=query,
            max_rows=max_rows,
            timeout_seconds=timeout_seconds,
            include_explain=explain_plan
        )

        return {
            "columns": execution_result.columns,
            "rows": execution_result.rows,
            "row_count": execution_result.row_count,
            "execution_time": execution_result.execution_time_ms / 1000,
            "status": "success",
            "query_hash": execution_result.query_hash,
            "explain_plan": execution_result.explain_plan if explain_plan else None,
            "warnings": execution_result.warnings
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL execution failed: {str(e)}"
        )


# ============================================================================
# T013: GET /monitoring/metrics - モニタリングメトリクス
# ============================================================================

@router.get("/monitoring/metrics", status_code=200)
async def get_monitoring_metrics(
    metric_groups: Optional[List[str]] = None,
    time_range: Optional[str] = "1h",
    include_history: bool = False,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """T013 REFACTOR: 実際のモニタリングメトリクス実装"""
    try:
        # 実際のモニタリング処理
        monitoring_service = MonitoringService(db)

        # デフォルトメトリクスグループ
        if not metric_groups:
            metric_groups = ["system", "database", "application", "batch_jobs"]

        # メトリクス収集
        metrics_data = await monitoring_service.collect_metrics(
            groups=metric_groups,
            time_range=time_range,
            include_historical=include_history
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "collection_time_ms": metrics_data.collection_time_ms,
            "time_range": time_range
        }

        # グループ別メトリクス追加
        if "system" in metric_groups:
            result["system"] = {
                "cpu_usage": metrics_data.system_metrics.cpu_usage_percent,
                "memory_usage": metrics_data.system_metrics.memory_usage_percent,
                "disk_usage": metrics_data.system_metrics.disk_usage_percent,
                "load_average": metrics_data.system_metrics.load_average,
                "uptime_seconds": metrics_data.system_metrics.uptime_seconds
            }

        if "database" in metric_groups:
            result["database"] = {
                "active_connections": metrics_data.db_metrics.active_connections,
                "max_connections": metrics_data.db_metrics.max_connections,
                "active_queries": metrics_data.db_metrics.active_queries,
                "slow_queries": metrics_data.db_metrics.slow_queries_count,
                "avg_response_time_ms": metrics_data.db_metrics.avg_response_time_ms,
                "deadlocks": metrics_data.db_metrics.deadlocks_count
            }

        if "application" in metric_groups:
            result["application"] = {
                "requests_per_minute": metrics_data.app_metrics.requests_per_minute,
                "error_rate": metrics_data.app_metrics.error_rate,
                "avg_response_time_ms": metrics_data.app_metrics.avg_response_time_ms,
                "active_sessions": metrics_data.app_metrics.active_sessions,
                "cache_hit_rate": metrics_data.app_metrics.cache_hit_rate
            }

        if "batch_jobs" in metric_groups:
            result["batch_jobs"] = {
                "running": metrics_data.batch_metrics.running_jobs,
                "pending": metrics_data.batch_metrics.pending_jobs,
                "completed_today": metrics_data.batch_metrics.completed_today,
                "failed_today": metrics_data.batch_metrics.failed_today,
                "avg_duration_minutes": metrics_data.batch_metrics.avg_duration_minutes,
                "queue_length": metrics_data.batch_metrics.queue_length
            }

        if include_history:
            result["history"] = metrics_data.historical_data

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )