"""
スコアリング関連APIエンドポイント

ユーザーと求人のマッチングスコア計算、ランキング、分析などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.common import BaseResponse, PaginatedResponse
from app.services.scoring import ScoringService

router = APIRouter()


# Request/Response Models
class ScoreCalculationRequest(BaseModel):
    """単一スコア計算リクエスト"""
    user_id: int = Field(..., description="ユーザーID")
    job_id: int = Field(..., description="求人ID")
    include_explanation: bool = Field(False, description="説明を含める")
    score_version: Optional[str] = Field(None, description="スコアリングバージョン")


class ScoreCalculationResponse(BaseModel):
    """スコア計算レスポンス"""
    user_id: int
    job_id: int
    composite_score: float = Field(..., ge=0, le=100, description="総合スコア")
    component_scores: Dict[str, float] = Field(..., description="構成要素スコア")
    explanation: Optional[str] = Field(None, description="スコア説明")
    calculated_at: str = Field(..., description="計算日時")


class BatchScoreRequest(BaseModel):
    """バッチスコア計算リクエスト"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000, description="ユーザーIDリスト")
    job_ids: List[int] = Field(..., min_items=1, max_items=1000, description="求人IDリスト")
    include_explanation: bool = Field(False, description="説明を含める")
    score_version: Optional[str] = Field(None, description="スコアリングバージョン")
    async_processing: bool = Field(False, description="非同期処理")


class BatchScoreResponse(BaseModel):
    """バッチスコア計算レスポンス"""
    batch_id: Optional[str] = Field(None, description="バッチID（非同期の場合）")
    total_combinations: int = Field(..., description="総組み合わせ数")
    completed_count: int = Field(..., description="完了数")
    scores: List[ScoreCalculationResponse] = Field(..., description="スコア結果")
    processing_time: float = Field(..., description="処理時間（秒）")


class UserScoresResponse(BaseModel):
    """ユーザースコア一覧レスポンス"""
    user_id: int
    total_scores: int = Field(..., description="総スコア数")
    top_scores: List[ScoreCalculationResponse] = Field(..., description="トップスコア")
    average_score: float = Field(..., description="平均スコア")
    updated_at: str = Field(..., description="最終更新日時")


class ScoreRankingItem(BaseModel):
    """スコアランキング項目"""
    user_id: int
    job_id: int
    composite_score: float
    rank: int = Field(..., description="順位")
    user_name: Optional[str] = Field(None, description="ユーザー名")
    job_title: Optional[str] = Field(None, description="求人タイトル")


class ScoreRankingsResponse(BaseModel):
    """スコアランキングレスポンス"""
    rankings: List[ScoreRankingItem]
    total_count: int
    generated_at: str = Field(..., description="生成日時")


@router.post("/calculate", response_model=ScoreCalculationResponse)
async def calculate_single_score(
    request: ScoreCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    単一ペアスコア計算

    指定されたユーザーと求人のペアのマッチングスコアを計算します。
    """
    try:
        scoring_service = ScoringService(db)
        score = await scoring_service.calculate_single_score(
            user_id=request.user_id,
            job_id=request.job_id,
            include_explanation=request.include_explanation,
            score_version=request.score_version
        )

        if not score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーまたは求人が見つかりません"
            )

        return score

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スコア計算中にエラーが発生しました: {str(e)}"
        )


@router.post("/batch", response_model=BatchScoreResponse)
async def calculate_batch_scores(
    request: BatchScoreRequest,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    バッチスコア計算

    複数のユーザーと求人の組み合わせのスコアを一括計算します。
    """
    try:
        scoring_service = ScoringService(db)

        # 大量データの場合は非同期処理
        if request.async_processing or len(request.user_ids) * len(request.job_ids) > 10000:
            batch_result = await scoring_service.start_batch_calculation(
                user_ids=request.user_ids,
                job_ids=request.job_ids,
                include_explanation=request.include_explanation,
                score_version=request.score_version
            )

            # バックグラウンドで処理を開始
            background_tasks.add_task(
                scoring_service.process_batch_async,
                batch_result["batch_id"]
            )

            return batch_result
        else:
            # 同期処理
            batch_result = await scoring_service.calculate_batch_scores(
                user_ids=request.user_ids,
                job_ids=request.job_ids,
                include_explanation=request.include_explanation,
                score_version=request.score_version
            )

            return batch_result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチスコア計算中にエラーが発生しました: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=UserScoresResponse)
async def get_user_scores(
    user_id: int = Path(..., description="ユーザーID"),
    limit: int = Query(20, ge=1, le=100, description="トップスコア件数"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="最小スコア"),
    job_categories: Optional[str] = Query(None, description="職種カテゴリ（カンマ区切り）"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーのスコア一覧取得

    指定されたユーザーの求人マッチングスコア一覧を取得します。
    """
    try:
        scoring_service = ScoringService(db)

        filters = {}
        if min_score is not None:
            filters['min_score'] = min_score
        if job_categories:
            filters['job_categories'] = job_categories.split(',')

        scores = await scoring_service.get_user_scores(
            user_id=user_id,
            limit=limit,
            filters=filters
        )

        if not scores:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーのスコアが見つかりません"
            )

        return scores

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザースコア取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/rankings", response_model=ScoreRankingsResponse)
async def get_score_rankings(
    ranking_type: str = Query("composite", description="ランキング種別"),
    period: str = Query("daily", description="期間（daily, weekly, monthly）"),
    limit: int = Query(100, ge=1, le=1000, description="ランキング件数"),
    category_filter: Optional[str] = Query(None, description="カテゴリフィルター"),
    user_group: Optional[str] = Query(None, description="ユーザーグループ"),
    db: AsyncSession = Depends(get_db)
):
    """
    スコアランキング取得

    各種条件でのスコアランキングを取得します。
    """
    try:
        scoring_service = ScoringService(db)

        filters = {}
        if category_filter:
            filters['category'] = category_filter
        if user_group:
            filters['user_group'] = user_group

        rankings = await scoring_service.get_score_rankings(
            ranking_type=ranking_type,
            period=period,
            limit=limit,
            filters=filters
        )

        return rankings

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ランキング取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str = Path(..., description="バッチID"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチ処理状況取得

    非同期で実行中のバッチ処理の状況を取得します。
    """
    try:
        scoring_service = ScoringService(db)
        status_info = await scoring_service.get_batch_status(batch_id)

        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチが見つかりません"
            )

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチ状況取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/batch/{batch_id}/results", response_model=BatchScoreResponse)
async def get_batch_results(
    batch_id: str = Path(..., description="バッチID"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """
    バッチ処理結果取得

    完了したバッチ処理の結果を取得します。
    """
    try:
        scoring_service = ScoringService(db)
        results = await scoring_service.get_batch_results(
            batch_id=batch_id,
            page=page,
            size=size
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたバッチの結果が見つかりません"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"バッチ結果取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/recalculate/user/{user_id}", response_model=BaseResponse)
async def recalculate_user_scores(
    user_id: int = Path(..., description="ユーザーID"),
    force: bool = Query(False, description="強制再計算"),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    ユーザースコア再計算

    指定されたユーザーの全スコアを再計算します。
    """
    try:
        scoring_service = ScoringService(db)

        # バックグラウンドで再計算を実行
        background_tasks.add_task(
            scoring_service.recalculate_user_scores,
            user_id,
            force
        )

        return BaseResponse(message="ユーザースコアの再計算を開始しました")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スコア再計算開始中にエラーが発生しました: {str(e)}"
        )


@router.get("/statistics")
async def get_scoring_statistics(
    period_days: int = Query(30, ge=1, le=365, description="統計期間（日）"),
    breakdown_by: str = Query("category", description="分析軸"),
    db: AsyncSession = Depends(get_db)
):
    """
    スコアリング統計情報取得

    スコアリングシステムの統計情報を取得します。
    """
    try:
        scoring_service = ScoringService(db)
        statistics = await scoring_service.get_scoring_statistics(
            period_days=period_days,
            breakdown_by=breakdown_by
        )

        return statistics

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計情報取得中にエラーが発生しました: {str(e)}"
        )


@router.delete("/cache/clear", response_model=BaseResponse)
async def clear_score_cache(
    cache_type: str = Query("all", description="キャッシュ種別"),
    user_ids: Optional[str] = Query(None, description="対象ユーザーID（カンマ区切り）"),
    db: AsyncSession = Depends(get_db)
):
    """
    スコアキャッシュクリア

    スコアリングキャッシュをクリアします。
    """
    try:
        scoring_service = ScoringService(db)

        target_user_ids = None
        if user_ids:
            target_user_ids = [int(x) for x in user_ids.split(',')]

        await scoring_service.clear_score_cache(
            cache_type=cache_type,
            user_ids=target_user_ids
        )

        return BaseResponse(message="スコアキャッシュが正常にクリアされました")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"キャッシュクリア中にエラーが発生しました: {str(e)}"
        )