"""
ユーザーアクション追跡APIエンドポイント

ユーザーの行動ログ記録、分析、バッチ処理などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date

from app.core.database import get_db
from app.models.common import BaseResponse, PaginatedResponse
from app.services.users import UserService

router = APIRouter()


# Request/Response Models
class ActionTrackRequest(BaseModel):
    """アクション追跡リクエスト"""
    user_id: int = Field(..., description="ユーザーID")
    action_type: str = Field(..., description="アクション種別")
    target_type: str = Field(..., description="対象種別（job, company, category等）")
    target_id: int = Field(..., description="対象ID")
    properties: Optional[Dict[str, Any]] = Field(None, description="追加プロパティ")
    timestamp: Optional[datetime] = Field(None, description="アクション発生時刻")
    session_id: Optional[str] = Field(None, description="セッションID")
    device_info: Optional[Dict[str, str]] = Field(None, description="デバイス情報")


class ActionResponse(BaseModel):
    """アクションレスポンス"""
    action_id: int
    user_id: int
    action_type: str
    target_type: str
    target_id: int
    properties: Optional[Dict[str, Any]]
    timestamp: datetime
    session_id: Optional[str]
    device_info: Optional[Dict[str, str]]


class BatchActionRequest(BaseModel):
    """バッチアクション追跡リクエスト"""
    actions: List[ActionTrackRequest] = Field(..., min_items=1, max_items=1000, description="アクションリスト")
    validate_users: bool = Field(True, description="ユーザー存在確認")
    ignore_duplicates: bool = Field(False, description="重複を無視")


class BatchActionResponse(BaseModel):
    """バッチアクション追跡レスポンス"""
    total_actions: int = Field(..., description="総アクション数")
    successful_count: int = Field(..., description="成功数")
    failed_count: int = Field(..., description="失敗数")
    errors: List[str] = Field(..., description="エラーリスト")
    processing_time: float = Field(..., description="処理時間（秒）")


class UserActionHistory(BaseModel):
    """ユーザーアクション履歴"""
    actions: List[ActionResponse]
    total_count: int
    page: int
    size: int
    user_summary: Dict[str, Any] = Field(..., description="ユーザーサマリー")


class ActionAnalytics(BaseModel):
    """アクション分析結果"""
    period_start: date
    period_end: date
    total_actions: int
    unique_users: int
    action_breakdown: Dict[str, int] = Field(..., description="アクション種別別集計")
    target_breakdown: Dict[str, int] = Field(..., description="対象種別別集計")
    hourly_distribution: List[Dict[str, Any]] = Field(..., description="時間別分布")
    popular_targets: List[Dict[str, Any]] = Field(..., description="人気対象")


@router.post("/track", response_model=BaseResponse)
async def track_action(
    action: ActionTrackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーアクション記録

    単一のユーザーアクションを記録します。
    """
    try:
        user_service = UserService(db)
        await user_service.track_action(action.dict())

        return BaseResponse(message="アクションが正常に記録されました")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アクション記録中にエラーが発生しました: {str(e)}"
        )


@router.post("/batch", response_model=BatchActionResponse)
async def track_batch_actions(
    batch_request: BatchActionRequest,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    バッチアクション記録

    複数のユーザーアクションを一括で記録します。
    """
    try:
        user_service = UserService(db)

        # 大量データの場合はバックグラウンド処理
        if len(batch_request.actions) > 100:
            # バックグラウンドタスクとして処理
            task_id = await user_service.start_batch_action_processing(
                actions=[action.dict() for action in batch_request.actions],
                validate_users=batch_request.validate_users,
                ignore_duplicates=batch_request.ignore_duplicates
            )

            background_tasks.add_task(
                user_service.process_batch_actions_async,
                task_id
            )

            return BatchActionResponse(
                total_actions=len(batch_request.actions),
                successful_count=0,
                failed_count=0,
                errors=[],
                processing_time=0.0
            )
        else:
            # 同期処理
            result = await user_service.track_batch_actions(
                actions=[action.dict() for action in batch_request.actions],
                validate_users=batch_request.validate_users,
                ignore_duplicates=batch_request.ignore_duplicates
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
            detail=f"バッチアクション記録中にエラーが発生しました: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=UserActionHistory)
async def get_user_actions(
    user_id: int = Path(..., description="ユーザーID"),
    action_types: Optional[str] = Query(None, description="アクション種別（カンマ区切り）"),
    target_types: Optional[str] = Query(None, description="対象種別（カンマ区切り）"),
    date_from: Optional[date] = Query(None, description="開始日"),
    date_to: Optional[date] = Query(None, description="終了日"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーアクション履歴取得

    指定されたユーザーのアクション履歴を取得します。
    """
    try:
        user_service = UserService(db)

        filters = {}
        if action_types:
            filters['action_types'] = action_types.split(',')
        if target_types:
            filters['target_types'] = target_types.split(',')
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to

        history = await user_service.get_user_action_history(
            user_id=user_id,
            filters=filters,
            page=page,
            size=size
        )

        if not history['actions']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された条件のアクション履歴が見つかりません"
            )

        return UserActionHistory(**history)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アクション履歴取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/analytics", response_model=ActionAnalytics)
async def get_action_analytics(
    date_from: date = Query(..., description="分析開始日"),
    date_to: date = Query(..., description="分析終了日"),
    action_types: Optional[str] = Query(None, description="対象アクション種別（カンマ区切り）"),
    user_groups: Optional[str] = Query(None, description="ユーザーグループ（カンマ区切り）"),
    include_hourly: bool = Query(True, description="時間別分析を含める"),
    include_popular: bool = Query(True, description="人気対象分析を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    アクション分析

    指定期間のユーザーアクション分析を実行します。
    """
    try:
        user_service = UserService(db)

        filters = {}
        if action_types:
            filters['action_types'] = action_types.split(',')
        if user_groups:
            filters['user_groups'] = user_groups.split(',')

        analytics = await user_service.get_action_analytics(
            date_from=date_from,
            date_to=date_to,
            filters=filters,
            include_hourly=include_hourly,
            include_popular=include_popular
        )

        return ActionAnalytics(**analytics)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アクション分析中にエラーが発生しました: {str(e)}"
        )


@router.get("/heatmap/{user_id}")
async def get_user_action_heatmap(
    user_id: int = Path(..., description="ユーザーID"),
    date_from: date = Query(..., description="開始日"),
    date_to: date = Query(..., description="終了日"),
    granularity: str = Query("hour", description="時間粒度（hour, day, week）"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーアクションヒートマップ

    ユーザーのアクションパターンをヒートマップ形式で取得します。
    """
    try:
        user_service = UserService(db)
        heatmap = await user_service.get_user_action_heatmap(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            granularity=granularity
        )

        return heatmap

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ヒートマップ取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/funnel")
async def get_action_funnel(
    funnel_steps: str = Query(..., description="ファネルステップ（カンマ区切り）"),
    date_from: date = Query(..., description="開始日"),
    date_to: date = Query(..., description="終了日"),
    user_cohort: Optional[str] = Query(None, description="ユーザーコホート"),
    db: AsyncSession = Depends(get_db)
):
    """
    アクションファネル分析

    指定されたステップでのコンバージョンファネルを分析します。
    """
    try:
        user_service = UserService(db)

        steps = funnel_steps.split(',')
        if len(steps) < 2:
            raise ValueError("ファネルには最低2つのステップが必要です")

        funnel = await user_service.get_action_funnel(
            steps=steps,
            date_from=date_from,
            date_to=date_to,
            user_cohort=user_cohort
        )

        return funnel

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ファネル分析中にエラーが発生しました: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session_actions(
    session_id: str = Path(..., description="セッションID"),
    include_user_info: bool = Query(False, description="ユーザー情報を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    セッションアクション取得

    指定されたセッションIDの全アクションを取得します。
    """
    try:
        user_service = UserService(db)
        session_actions = await user_service.get_session_actions(
            session_id=session_id,
            include_user_info=include_user_info
        )

        if not session_actions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたセッションが見つかりません"
            )

        return session_actions

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セッション情報取得中にエラーが発生しました: {str(e)}"
        )


@router.delete("/cleanup", response_model=BaseResponse)
async def cleanup_old_actions(
    days_to_keep: int = Query(90, ge=1, le=365, description="保持日数"),
    action_types: Optional[str] = Query(None, description="対象アクション種別（カンマ区切り）"),
    dry_run: bool = Query(True, description="実行せずに対象件数のみ表示"),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    古いアクションデータクリーンアップ

    指定された期間より古いアクションデータを削除します。
    """
    try:
        user_service = UserService(db)

        target_types = None
        if action_types:
            target_types = action_types.split(',')

        if dry_run:
            # 対象件数を返す
            count = await user_service.count_old_actions(
                days_to_keep=days_to_keep,
                action_types=target_types
            )
            return BaseResponse(
                message=f"クリーンアップ対象: {count}件のアクション"
            )
        else:
            # バックグラウンドでクリーンアップ実行
            background_tasks.add_task(
                user_service.cleanup_old_actions,
                days_to_keep,
                target_types
            )

            return BaseResponse(
                message="古いアクションデータのクリーンアップを開始しました"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"クリーンアップ処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/trends")
async def get_action_trends(
    metric: str = Query("total_actions", description="トレンド指標"),
    period: str = Query("daily", description="期間（hourly, daily, weekly）"),
    days: int = Query(30, ge=1, le=365, description="対象日数"),
    action_types: Optional[str] = Query(None, description="対象アクション種別（カンマ区切り）"),
    db: AsyncSession = Depends(get_db)
):
    """
    アクショントレンド取得

    指定された期間でのアクショントレンドを取得します。
    """
    try:
        user_service = UserService(db)

        target_types = None
        if action_types:
            target_types = action_types.split(',')

        trends = await user_service.get_action_trends(
            metric=metric,
            period=period,
            days=days,
            action_types=target_types
        )

        return trends

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"トレンド取得中にエラーが発生しました: {str(e)}"
        )