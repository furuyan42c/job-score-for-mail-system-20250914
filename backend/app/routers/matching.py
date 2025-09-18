"""
マッチング関連APIエンドポイント

求人とユーザーのマッチング処理、推薦システムなどのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.matching import (
    MatchingRequest, MatchingResult, MatchingBatchInfo, UserJobRecommendations,
    MatchingSearchRequest, MatchingAnalytics, RealtimeMatchingRequest,
    RealtimeMatchingResponse, ScoringConfiguration, ABTestConfig
)
from app.models.common import BaseResponse
from app.services.matching import MatchingService

router = APIRouter()


@router.post("/execute", response_model=MatchingBatchInfo)
async def execute_matching(
    request: MatchingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    マッチング実行

    指定された条件でユーザーと求人のマッチングを実行します。
    """
    try:
        matching_service = MatchingService(db)
        batch_info = await matching_service.execute_matching(request)
        return batch_info

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"マッチング実行中にエラーが発生しました: {str(e)}"
        )


@router.get("/realtime/{user_id}", response_model=RealtimeMatchingResponse)
async def realtime_matching(
    user_id: int = Path(..., description="ユーザーID"),
    max_results: int = Query(20, ge=1, le=100, description="最大結果数"),
    exclude_job_ids: Optional[str] = Query(None, description="除外求人ID（カンマ区切り）"),
    category_filters: Optional[str] = Query(None, description="カテゴリフィルター（カンマ区切り）"),
    include_explanations: bool = Query(False, description="説明を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    リアルタイムマッチング

    指定されたユーザーに対してリアルタイムで求人推薦を実行します。
    """
    try:
        request_data = RealtimeMatchingRequest(
            user_id=user_id,
            max_results=max_results,
            exclude_job_ids=[int(x) for x in exclude_job_ids.split(',')] if exclude_job_ids else [],
            category_filters=[int(x) for x in category_filters.split(',')] if category_filters else [],
            include_explanations=include_explanations
        )

        matching_service = MatchingService(db)
        response = await matching_service.realtime_matching(request_data)
        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"リアルタイムマッチング中にエラーが発生しました: {str(e)}"
        )


@router.get("/recommendations/{user_id}", response_model=UserJobRecommendations)
async def get_user_recommendations(
    user_id: int = Path(..., description="ユーザーID"),
    recommendation_date: Optional[str] = Query(None, description="推薦日（YYYY-MM-DD）"),
    include_sent: bool = Query(False, description="送信済みを含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー推薦取得

    指定されたユーザーの求人推薦を取得します。
    """
    try:
        matching_service = MatchingService(db)
        recommendations = await matching_service.get_user_recommendations(
            user_id=user_id,
            recommendation_date=recommendation_date,
            include_sent=include_sent
        )

        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された条件の推薦が見つかりません"
            )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推薦取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/batches/{batch_id}", response_model=MatchingBatchInfo)
async def get_batch_info(
    batch_id: int = Path(..., description="バッチID"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチ情報取得

    指定されたマッチングバッチの詳細情報を取得します。
    """
    try:
        matching_service = MatchingService(db)
        batch_info = await matching_service.get_batch_info(batch_id)

        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチが見つかりません"
            )

        return batch_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチ情報取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/results", response_model=List[MatchingResult])
async def search_matching_results(
    user_ids: Optional[str] = Query(None, description="ユーザーID（カンマ区切り）"),
    job_ids: Optional[str] = Query(None, description="求人ID（カンマ区切り）"),
    batch_ids: Optional[str] = Query(None, description="バッチID（カンマ区切り）"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="最小スコア"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="最大スコア"),
    batch_date_from: Optional[str] = Query(None, description="バッチ日付開始（YYYY-MM-DD）"),
    batch_date_to: Optional[str] = Query(None, description="バッチ日付終了（YYYY-MM-DD）"),
    sort_by: str = Query("composite_score", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """
    マッチング結果検索

    様々な条件でマッチング結果を検索します。
    """
    try:
        filters = {}
        if user_ids:
            filters['user_ids'] = [int(x) for x in user_ids.split(',')]
        if job_ids:
            filters['job_ids'] = [int(x) for x in job_ids.split(',')]
        if batch_ids:
            filters['batch_ids'] = [int(x) for x in batch_ids.split(',')]
        if min_score is not None:
            filters['min_score'] = min_score
        if max_score is not None:
            filters['max_score'] = max_score
        if batch_date_from:
            filters['batch_date_from'] = batch_date_from
        if batch_date_to:
            filters['batch_date_to'] = batch_date_to

        matching_service = MatchingService(db)
        results = await matching_service.search_results(
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
            detail=f"マッチング結果検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/analytics", response_model=MatchingAnalytics)
async def get_matching_analytics(
    period_days: int = Query(30, ge=1, le=365, description="分析期間（日）"),
    include_trends: bool = Query(True, description="トレンド分析を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    マッチング分析

    マッチングシステムの分析結果を取得します。
    """
    try:
        matching_service = MatchingService(db)
        analytics = await matching_service.get_analytics(period_days, include_trends)
        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/scoring-config", response_model=ScoringConfiguration)
async def get_scoring_configuration(
    version: Optional[str] = Query(None, description="設定バージョン"),
    db: AsyncSession = Depends(get_db)
):
    """
    スコアリング設定取得

    現在のスコアリング設定を取得します。
    """
    try:
        matching_service = MatchingService(db)
        config = await matching_service.get_scoring_config(version)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたスコアリング設定が見つかりません"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/scoring-config", response_model=ScoringConfiguration)
async def update_scoring_configuration(
    config: ScoringConfiguration,
    db: AsyncSession = Depends(get_db)
):
    """
    スコアリング設定更新

    スコアリング設定を更新します。
    """
    try:
        matching_service = MatchingService(db)
        updated_config = await matching_service.update_scoring_config(config)
        return updated_config

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


@router.post("/ab-test", response_model=ABTestConfig)
async def create_ab_test(
    test_config: ABTestConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    A/Bテスト作成

    新しいA/Bテストを作成します。
    """
    try:
        matching_service = MatchingService(db)
        created_test = await matching_service.create_ab_test(test_config)
        return created_test

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/Bテスト作成中にエラーが発生しました: {str(e)}"
        )


@router.post("/generate-daily-picks", response_model=BaseResponse)
async def generate_daily_picks(
    target_date: Optional[str] = Query(None, description="対象日（YYYY-MM-DD、未指定で今日）"),
    user_ids: Optional[str] = Query(None, description="対象ユーザーID（カンマ区切り）"),
    force_regenerate: bool = Query(False, description="強制再生成"),
    db: AsyncSession = Depends(get_db)
):
    """
    日次求人選定

    指定された日付の日次求人選定を実行します。
    """
    try:
        matching_service = MatchingService(db)
        await matching_service.generate_daily_picks(
            target_date=target_date,
            user_ids=[int(x) for x in user_ids.split(',')] if user_ids else None,
            force_regenerate=force_regenerate
        )

        return BaseResponse(message="日次求人選定が正常に実行されました")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"日次求人選定中にエラーが発生しました: {str(e)}"
        )