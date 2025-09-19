"""
バッチ処理関連APIエンドポイント

バッチジョブの管理、メール生成、データインポートなどのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.batch import (
    BatchJob, BatchJobRequest, BatchJobSearchRequest, BatchJobProgress,
    EmailTemplate, EmailContent, EmailGenerationRequest, EmailQueue,
    EmailDeliveryStats, EmailCampaign, DataImportRequest, DataImportResult,
    ScheduledTask, BatchPerformanceMetrics, SystemMaintenanceRequest
)
from app.models.common import BaseResponse, PaginatedResponse
from app.services.batch import BatchService

router = APIRouter()


# ============================================================================
# TDD Phase 2: GREEN - 最小限の実装でテストをパス
# ============================================================================

@router.post("/trigger", status_code=202)
async def trigger_batch(
    batch_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    T005: バッチトリガー（TDD REFACTOR実装）

    実際のビジネスロジックでバッチジョブを作成・開始
    """
    import uuid
    from datetime import datetime

    try:
        # 入力バリデーション
        valid_batch_types = ["daily_matching", "email_generation", "data_import", "scoring"]
        if batch_type not in valid_batch_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid batch_type. Must be one of: {valid_batch_types}"
            )

        # バッチサービス経由で実際のジョブ作成
        batch_service = BatchService(db)
        batch_job = await batch_service.create_and_start_batch(
            batch_type=batch_type,
            initiated_by="system",  # TODO: 実際のユーザーIDに置換
            priority="normal"
        )

        return {
            "batch_id": batch_job.batch_id,
            "job_type": batch_job.job_type,
            "started_at": batch_job.started_at.isoformat() if batch_job.started_at else datetime.now().isoformat(),
            "status": batch_job.status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger batch: {str(e)}"
        )


@router.get("/status/{batch_id}")
async def get_batch_status(
    batch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    T006: バッチステータス取得（TDD REFACTOR実装）

    実際のデータベースからバッチステータスを取得
    """
    try:
        # バッチサービス経由で実際のステータス取得
        batch_service = BatchService(db)
        batch_job = await batch_service.get_batch_status(batch_id)

        if not batch_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch job with ID {batch_id} not found"
            )

        return {
            "batch_id": batch_job.batch_id,
            "status": batch_job.status,
            "progress": batch_job.progress_percentage or 0,
            "job_type": batch_job.job_type,
            "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None,
            "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None,
            "error_message": batch_job.error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )


# ============================================================================
# 既存のエンドポイント
# ============================================================================

@router.get("/jobs", response_model=PaginatedResponse)
async def search_batch_jobs(
    job_types: Optional[str] = Query(None, description="ジョブタイプ（カンマ区切り）"),
    statuses: Optional[str] = Query(None, description="ステータス（カンマ区切り）"),
    priorities: Optional[str] = Query(None, description="優先度（カンマ区切り）"),
    started_from: Optional[str] = Query(None, description="開始日時から（ISO形式）"),
    started_to: Optional[str] = Query(None, description="開始日時まで（ISO形式）"),
    initiated_by: Optional[str] = Query(None, description="実行者"),
    has_errors: Optional[bool] = Query(None, description="エラーあり"),
    sort_by: str = Query("started_at", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチジョブ検索

    様々な条件でバッチジョブを検索します。
    """
    try:
        filters = {}
        if job_types:
            filters['job_types'] = job_types.split(',')
        if statuses:
            filters['statuses'] = statuses.split(',')
        if priorities:
            filters['priorities'] = priorities.split(',')
        if started_from:
            filters['started_from'] = started_from
        if started_to:
            filters['started_to'] = started_to
        if initiated_by:
            filters['initiated_by'] = initiated_by
        if has_errors is not None:
            filters['has_errors'] = has_errors

        batch_service = BatchService(db)
        results = await batch_service.search_jobs(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        return results

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチジョブ検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/jobs/{batch_id}", response_model=BatchJob)
async def get_batch_job(
    batch_id: int = Path(..., description="バッチID"),
    include_logs: bool = Query(False, description="ログを含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチジョブ詳細取得

    指定されたバッチジョブの詳細情報を取得します。
    """
    try:
        batch_service = BatchService(db)
        job = await batch_service.get_job_by_id(batch_id, include_logs)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチジョブが見つかりません"
            )

        return job

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチジョブ取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/jobs", response_model=BatchJob)
async def create_batch_job(
    job_request: BatchJobRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    バッチジョブ作成

    新しいバッチジョブを作成・実行します。
    """
    try:
        batch_service = BatchService(db)
        job = await batch_service.create_job(job_request)
        return job

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチジョブ作成中にエラーが発生しました: {str(e)}"
        )


@router.post("/jobs/{batch_id}/cancel", response_model=BaseResponse)
async def cancel_batch_job(
    batch_id: int = Path(..., description="バッチID"),
    reason: Optional[str] = Query(None, description="キャンセル理由"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチジョブキャンセル

    実行中のバッチジョブをキャンセルします。
    """
    try:
        batch_service = BatchService(db)
        success = await batch_service.cancel_job(batch_id, reason)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチジョブが見つかりません"
            )

        return BaseResponse(message="バッチジョブが正常にキャンセルされました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチジョブキャンセル中にエラーが発生しました: {str(e)}"
        )


@router.get("/jobs/{batch_id}/progress", response_model=BatchJobProgress)
async def get_batch_job_progress(
    batch_id: int = Path(..., description="バッチID"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチジョブ進捗取得

    指定されたバッチジョブの進捗状況を取得します。
    """
    try:
        batch_service = BatchService(db)
        progress = await batch_service.get_job_progress(batch_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチジョブが見つかりません"
            )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"進捗取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/email/templates", response_model=List[EmailTemplate])
async def get_email_templates(
    category: Optional[str] = Query(None, description="カテゴリ"),
    is_active: bool = Query(True, description="有効なテンプレートのみ"),
    db: AsyncSession = Depends(get_db)
):
    """
    メールテンプレート一覧取得

    メールテンプレートの一覧を取得します。
    """
    try:
        batch_service = BatchService(db)
        templates = await batch_service.get_email_templates(category, is_active)
        return templates

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メールテンプレート取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/email/generate", response_model=BaseResponse)
async def generate_emails(
    request: EmailGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    メール生成

    指定された条件でユーザー向けメールを生成します。
    """
    try:
        batch_service = BatchService(db)
        job = await batch_service.generate_emails(request)

        if request.dry_run:
            return BaseResponse(
                message=f"メール生成テスト完了: 対象ユーザー数確認済み（実際の生成は行われていません）"
            )
        else:
            return BaseResponse(
                message=f"メール生成ジョブが開始されました (バッチID: {job.batch_id})"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メール生成中にエラーが発生しました: {str(e)}"
        )


@router.get("/email/queue", response_model=List[EmailQueue])
async def get_email_queue(
    status: Optional[str] = Query(None, description="配信ステータス"),
    scheduled_date: Optional[str] = Query(None, description="配信予定日（YYYY-MM-DD）"),
    user_ids: Optional[str] = Query(None, description="ユーザーID（カンマ区切り）"),
    limit: int = Query(100, ge=1, le=1000, description="最大件数"),
    db: AsyncSession = Depends(get_db)
):
    """
    メール配信キュー取得

    メール配信キューの状況を取得します。
    """
    try:
        filters = {}
        if status:
            filters['status'] = status
        if scheduled_date:
            filters['scheduled_date'] = scheduled_date
        if user_ids:
            filters['user_ids'] = [int(x) for x in user_ids.split(',')]

        batch_service = BatchService(db)
        queue = await batch_service.get_email_queue(filters, limit)
        return queue

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メール配信キュー取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/email/stats", response_model=EmailDeliveryStats)
async def get_email_delivery_stats(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    template_id: Optional[str] = Query(None, description="テンプレートID"),
    db: AsyncSession = Depends(get_db)
):
    """
    メール配信統計取得

    指定期間のメール配信統計を取得します。
    """
    try:
        batch_service = BatchService(db)
        stats = await batch_service.get_email_delivery_stats(
            period_start=period_start,
            period_end=period_end,
            template_id=template_id
        )
        return stats

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メール配信統計取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/data/import", response_model=DataImportResult)
async def import_data(
    file: UploadFile = File(...),
    import_type: str = Query(..., description="インポートタイプ"),
    mapping_config: str = Query(..., description="マッピング設定（JSON）"),
    duplicate_handling: str = Query("skip", description="重複処理方法"),
    dry_run: bool = Query(False, description="実行確認"),
    db: AsyncSession = Depends(get_db)
):
    """
    データインポート

    CSVファイルからデータをインポートします。
    """
    try:
        batch_service = BatchService(db)
        result = await batch_service.import_data(
            file=file,
            import_type=import_type,
            mapping_config=mapping_config,
            duplicate_handling=duplicate_handling,
            dry_run=dry_run
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データインポート中にエラーが発生しました: {str(e)}"
        )


@router.get("/scheduled-tasks", response_model=List[ScheduledTask])
async def get_scheduled_tasks(
    is_active: bool = Query(True, description="有効なタスクのみ"),
    task_type: Optional[str] = Query(None, description="タスクタイプ"),
    db: AsyncSession = Depends(get_db)
):
    """
    スケジュールタスク一覧取得

    定期実行タスクの一覧を取得します。
    """
    try:
        batch_service = BatchService(db)
        tasks = await batch_service.get_scheduled_tasks(is_active, task_type)
        return tasks

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スケジュールタスク取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/scheduled-tasks", response_model=ScheduledTask)
async def create_scheduled_task(
    task: ScheduledTask,
    db: AsyncSession = Depends(get_db)
):
    """
    スケジュールタスク作成

    新しい定期実行タスクを作成します。
    """
    try:
        batch_service = BatchService(db)
        created_task = await batch_service.create_scheduled_task(task)
        return created_task

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スケジュールタスク作成中にエラーが発生しました: {str(e)}"
        )


@router.get("/performance", response_model=BatchPerformanceMetrics)
async def get_batch_performance_metrics(
    period_days: int = Query(7, ge=1, le=90, description="分析期間（日）"),
    job_type: Optional[str] = Query(None, description="ジョブタイプ"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチパフォーマンス指標取得

    バッチシステムのパフォーマンス指標を取得します。
    """
    try:
        batch_service = BatchService(db)
        metrics = await batch_service.get_performance_metrics(period_days, job_type)
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"パフォーマンス指標取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/maintenance", response_model=BaseResponse)
async def schedule_maintenance(
    request: SystemMaintenanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    システムメンテナンス予約

    システムメンテナンスを予約します。
    """
    try:
        batch_service = BatchService(db)
        await batch_service.schedule_maintenance(request)
        return BaseResponse(message="システムメンテナンスが正常に予約されました")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メンテナンス予約中にエラーが発生しました: {str(e)}"
        )


@router.post("/cleanup", response_model=BaseResponse)
async def run_data_cleanup(
    cleanup_type: str = Query(..., description="クリーンアップタイプ"),
    days_to_keep: int = Query(90, ge=1, le=1825, description="保持日数"),
    dry_run: bool = Query(True, description="実行確認"),
    db: AsyncSession = Depends(get_db)
):
    """
    データクリーンアップ実行

    古いデータのクリーンアップを実行します。
    """
    try:
        batch_service = BatchService(db)
        result = await batch_service.run_data_cleanup(cleanup_type, days_to_keep, dry_run)

        if dry_run:
            return BaseResponse(
                message=f"クリーンアップ対象データ確認完了: {result.get('affected_records', 0)}件"
            )
        else:
            return BaseResponse(
                message=f"データクリーンアップ完了: {result.get('deleted_records', 0)}件削除"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データクリーンアップ中にエラーが発生しました: {str(e)}"
        )