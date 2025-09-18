"""
ユーザー関連APIエンドポイント

ユーザーの作成、更新、検索、プロファイル管理などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.users import (
    User, UserCreate, UserUpdate, UserListItem, UserSearchRequest,
    UserSearchResponse, UserAction, UserActionCreate, UserProfile,
    UserActivitySummary, UserEngagementMetrics, BulkUserOperation,
    BulkUserResult
)
from app.models.common import BaseResponse, ErrorResponse
from app.services.users import UserService

router = APIRouter()


@router.get("/", response_model=UserSearchResponse)
async def search_users(
    email: Optional[str] = Query(None, description="メールアドレス検索"),
    age_groups: Optional[str] = Query(None, description="年齢層（カンマ区切り）"),
    genders: Optional[str] = Query(None, description="性別（カンマ区切り）"),
    prefecture_codes: Optional[str] = Query(None, description="都道府県コード（カンマ区切り）"),
    is_active: Optional[bool] = Query(True, description="有効ユーザーのみ"),
    email_subscription: Optional[bool] = Query(None, description="メール配信希望"),
    has_recent_activity: Optional[bool] = Query(None, description="最近活動あり"),
    sort_by: str = Query("registration_date", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー検索"""
    try:
        filters = {}
        if email:
            filters['email'] = email
        if age_groups:
            filters['age_groups'] = age_groups.split(',')
        if genders:
            filters['genders'] = genders.split(',')
        if prefecture_codes:
            filters['prefecture_codes'] = prefecture_codes.split(',')
        if is_active is not None:
            filters['is_active'] = is_active
        if email_subscription is not None:
            filters['email_subscription'] = email_subscription
        if has_recent_activity is not None:
            filters['has_recent_activity'] = has_recent_activity

        user_service = UserService(db)
        result = await user_service.search_users(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int = Path(..., description="ユーザーID"),
    include_profile: bool = Query(False, description="プロファイル情報を含める"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー詳細取得"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id, include_profile)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー作成"""
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー作成中にエラーが発生しました: {str(e)}"
        )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """新規ユーザー登録"""
    try:
        user_service = UserService(db)
        user = await user_service.register_user(user_data)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー登録中にエラーが発生しました: {str(e)}"
        )


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int = Path(..., description="ユーザーID"),
    user_data: UserUpdate = ...,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー更新"""
    try:
        user_service = UserService(db)
        user = await user_service.update_user(user_id, user_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )

        return user

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー更新中にエラーが発生しました: {str(e)}"
        )


@router.post("/{user_id}/actions", response_model=BaseResponse)
async def record_user_action(
    user_id: int = Path(..., description="ユーザーID"),
    action_data: UserActionCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー行動記録"""
    try:
        # user_idの一致確認
        if action_data.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="パスのuser_idとリクエストボディのuser_idが一致しません"
            )

        user_service = UserService(db)
        await user_service.record_action(action_data)
        return BaseResponse(message="ユーザー行動が正常に記録されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"行動記録中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}/actions", response_model=List[UserAction])
async def get_user_actions(
    user_id: int = Path(..., description="ユーザーID"),
    action_types: Optional[str] = Query(None, description="アクション種別（カンマ区切り）"),
    days: int = Query(30, ge=1, le=365, description="取得日数"),
    limit: int = Query(100, ge=1, le=1000, description="最大件数"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー行動履歴取得"""
    try:
        user_service = UserService(db)
        actions = await user_service.get_user_actions(
            user_id=user_id,
            action_types=action_types.split(',') if action_types else None,
            days=days,
            limit=limit
        )
        return actions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"行動履歴取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(
    user_id: int = Path(..., description="ユーザーID"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザープロファイル取得"""
    try:
        user_service = UserService(db)
        profile = await user_service.get_user_profile(user_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザープロファイルが見つかりません"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}/activity-summary", response_model=UserActivitySummary)
async def get_user_activity_summary(
    user_id: int = Path(..., description="ユーザーID"),
    period_days: int = Query(30, ge=1, le=365, description="集計期間（日）"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー活動サマリー取得"""
    try:
        user_service = UserService(db)
        summary = await user_service.get_activity_summary(user_id, period_days)
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"活動サマリー取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}/engagement-metrics", response_model=UserEngagementMetrics)
async def get_user_engagement_metrics(
    user_id: int = Path(..., description="ユーザーID"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザーエンゲージメント指標取得"""
    try:
        user_service = UserService(db)
        metrics = await user_service.get_engagement_metrics(user_id)

        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エンゲージメント指標が見つかりません"
            )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エンゲージメント指標取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/bulk-operations", response_model=BulkUserResult)
async def bulk_user_operations(
    operation: BulkUserOperation,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー一括操作"""
    try:
        user_service = UserService(db)
        result = await user_service.bulk_operations(operation)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一括操作中にエラーが発生しました: {str(e)}"
        )


@router.post("/{user_id}/update-profile", response_model=BaseResponse)
async def update_user_profile(
    user_id: int = Path(..., description="ユーザーID"),
    force_recalculate: bool = Query(False, description="強制再計算"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザープロファイル更新"""
    try:
        user_service = UserService(db)
        success = await user_service.update_profile(user_id, force_recalculate)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )

        return BaseResponse(message="ユーザープロファイルが正常に更新されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル更新中にエラーが発生しました: {str(e)}"
        )


@router.put("/{user_id}/preferences", response_model=BaseResponse)
async def update_user_preferences(
    user_id: int = Path(..., description="ユーザーID"),
    preferences: dict = ...,
    db: AsyncSession = Depends(get_db)
):
    """ユーザー設定更新"""
    try:
        user_service = UserService(db)
        success = await user_service.update_preferences(user_id, preferences)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )

        return BaseResponse(message="ユーザー設定が正常に更新されました")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定更新中にエラーが発生しました: {str(e)}"
        )


@router.get("/{user_id}/history", response_model=List[UserAction])
async def get_user_history(
    user_id: int = Path(..., description="ユーザーID"),
    action_types: Optional[str] = Query(None, description="アクション種別（カンマ区切り）"),
    limit: int = Query(100, ge=1, le=1000, description="最大件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー行動履歴取得"""
    try:
        user_service = UserService(db)
        history = await user_service.get_user_history(
            user_id=user_id,
            action_types=action_types.split(',') if action_types else None,
            limit=limit,
            offset=offset
        )
        return history

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"履歴取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/stats/summary")
async def get_user_stats_summary(
    db: AsyncSession = Depends(get_db)
):
    """ユーザー統計サマリー"""
    try:
        user_service = UserService(db)
        stats = await user_service.get_stats_summary()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計取得中にエラーが発生しました: {str(e)}"
        )