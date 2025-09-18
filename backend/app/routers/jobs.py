"""
求人関連APIエンドポイント

求人の作成、更新、検索、詳細取得などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.jobs import (
    Job, JobCreate, JobUpdate, JobListItem, JobSearchRequest,
    JobSearchResponse, JobRecommendation, JobCompanyPopularity,
    JobKeywordAnalysis, BulkJobOperation, BulkJobResult
)
from app.models.common import BaseResponse, ErrorResponse, PaginatedResponse
from app.services.jobs import JobService

router = APIRouter()


@router.get("/", response_model=JobSearchResponse)
async def search_jobs(
    keyword: Optional[str] = Query(None, description="キーワード検索"),
    prefecture_codes: Optional[str] = Query(None, description="都道府県コード（カンマ区切り）"),
    city_codes: Optional[str] = Query(None, description="市区町村コード（カンマ区切り）"),
    occupation_codes: Optional[str] = Query(None, description="職種コード（カンマ区切り）"),
    feature_codes: Optional[str] = Query(None, description="特徴コード（カンマ区切り）"),
    min_salary: Optional[int] = Query(None, description="最低給与"),
    max_salary: Optional[int] = Query(None, description="最高給与"),
    salary_type: Optional[str] = Query(None, description="給与タイプ"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="最小スコア"),
    has_high_income: Optional[bool] = Query(None, description="高収入求人のみ"),
    is_active: Optional[bool] = Query(True, description="有効求人のみ"),
    sort_by: str = Query("posting_date", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序"),
    page: int = Query(1, ge=1, description="ページ番号"),
    size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人検索

    様々な条件で求人を検索します。
    """
    try:
        # 検索条件構築
        filters = {}
        if keyword:
            filters['keyword'] = keyword
        if prefecture_codes:
            filters['prefecture_codes'] = prefecture_codes.split(',')
        if city_codes:
            filters['city_codes'] = city_codes.split(',')
        if occupation_codes:
            filters['occupation_codes'] = [int(x) for x in occupation_codes.split(',')]
        if feature_codes:
            filters['feature_codes'] = feature_codes.split(',')
        if min_salary is not None:
            filters['min_salary'] = min_salary
        if max_salary is not None:
            filters['max_salary'] = max_salary
        if salary_type:
            filters['salary_type'] = salary_type
        if min_score is not None:
            filters['min_score'] = min_score
        if has_high_income is not None:
            filters['has_high_income'] = has_high_income
        if is_active is not None:
            filters['is_active'] = is_active

        job_service = JobService(db)
        result = await job_service.search_jobs(
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
            detail=f"求人検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/{job_id}", response_model=Job)
async def get_job(
    job_id: int = Path(..., description="求人ID"),
    include_scoring: bool = Query(False, description="スコアリング情報を含める"),
    include_stats: bool = Query(False, description="統計情報を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人詳細取得

    指定された求人IDの詳細情報を取得します。
    """
    try:
        job_service = JobService(db)
        job = await job_service.get_job_by_id(
            job_id=job_id,
            include_scoring=include_scoring,
            include_stats=include_stats
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return job

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    求人作成

    新しい求人を作成します。
    """
    try:
        job_service = JobService(db)
        job = await job_service.create_job(job_data)
        return job

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人作成中にエラーが発生しました: {str(e)}"
        )


@router.put("/{job_id}", response_model=Job)
async def update_job(
    job_id: int = Path(..., description="求人ID"),
    job_data: JobUpdate = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    求人更新

    指定された求人の情報を更新します。
    """
    try:
        job_service = JobService(db)
        job = await job_service.update_job(job_id, job_data)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return job

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
            detail=f"求人更新中にエラーが発生しました: {str(e)}"
        )


@router.delete("/{job_id}", response_model=BaseResponse)
async def delete_job(
    job_id: int = Path(..., description="求人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人削除

    指定された求人を削除（非活性化）します。
    """
    try:
        job_service = JobService(db)
        success = await job_service.delete_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return BaseResponse(message="求人が正常に削除されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人削除中にエラーが発生しました: {str(e)}"
        )


@router.post("/{job_id}/activate", response_model=BaseResponse)
async def activate_job(
    job_id: int = Path(..., description="求人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人有効化

    指定された求人を有効化します。
    """
    try:
        job_service = JobService(db)
        success = await job_service.activate_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return BaseResponse(message="求人が正常に有効化されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人有効化中にエラーが発生しました: {str(e)}"
        )


@router.post("/{job_id}/deactivate", response_model=BaseResponse)
async def deactivate_job(
    job_id: int = Path(..., description="求人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人無効化

    指定された求人を無効化します。
    """
    try:
        job_service = JobService(db)
        success = await job_service.deactivate_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return BaseResponse(message="求人が正常に無効化されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人無効化中にエラーが発生しました: {str(e)}"
        )


@router.get("/{job_id}/recommendations", response_model=List[JobRecommendation])
async def get_job_recommendations(
    job_id: int = Path(..., description="求人ID"),
    limit: int = Query(10, ge=1, le=50, description="最大件数"),
    db: AsyncSession = Depends(get_db)
):
    """
    類似求人推薦

    指定された求人に類似した他の求人を推薦します。
    """
    try:
        job_service = JobService(db)
        recommendations = await job_service.get_similar_jobs(job_id, limit)
        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人推薦取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{job_id}/keyword-analysis", response_model=JobKeywordAnalysis)
async def analyze_job_keywords(
    job_id: int = Path(..., description="求人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人キーワード分析

    指定された求人のキーワード分析を実行します。
    """
    try:
        job_service = JobService(db)
        analysis = await job_service.analyze_job_keywords(job_id)

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"キーワード分析中にエラーが発生しました: {str(e)}"
        )


@router.get("/companies/{endcl_cd}/popularity", response_model=JobCompanyPopularity)
async def get_company_popularity(
    endcl_cd: str = Path(..., description="エンドクライアントコード"),
    db: AsyncSession = Depends(get_db)
):
    """
    企業人気度取得

    指定された企業の人気度情報を取得します。
    """
    try:
        job_service = JobService(db)
        popularity = await job_service.get_company_popularity(endcl_cd)

        if not popularity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された企業が見つかりません"
            )

        return popularity

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"企業人気度取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/bulk-operations", response_model=BulkJobResult)
async def bulk_job_operations(
    operation: BulkJobOperation,
    db: AsyncSession = Depends(get_db)
):
    """
    求人一括操作

    複数の求人に対して一括操作を実行します。
    """
    try:
        job_service = JobService(db)
        result = await job_service.bulk_operations(operation)
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


@router.post("/{job_id}/recalculate-score", response_model=BaseResponse)
async def recalculate_job_score(
    job_id: int = Path(..., description="求人ID"),
    force: bool = Query(False, description="強制再計算"),
    db: AsyncSession = Depends(get_db)
):
    """
    求人スコア再計算

    指定された求人のスコアを再計算します。
    """
    try:
        job_service = JobService(db)
        success = await job_service.recalculate_score(job_id, force)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された求人が見つかりません"
            )

        return BaseResponse(message="求人スコアが正常に再計算されました")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スコア再計算中にエラーが発生しました: {str(e)}"
        )


@router.post("/search", response_model=JobSearchResponse)
async def advanced_job_search(
    search_request: JobSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    高度求人検索

    詳細な検索条件で求人を検索します。
    """
    try:
        job_service = JobService(db)
        result = await job_service.advanced_search(search_request)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/recommendations/{user_id}", response_model=List[JobRecommendation])
async def get_job_recommendations_for_user(
    user_id: int = Path(..., description="ユーザーID"),
    limit: int = Query(20, ge=1, le=100, description="最大件数"),
    exclude_applied: bool = Query(True, description="応募済み求人を除外"),
    include_explanations: bool = Query(False, description="推薦理由を含める"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー向け求人推薦

    指定されたユーザーに最適化された求人を推薦します。
    """
    try:
        job_service = JobService(db)
        recommendations = await job_service.get_user_recommendations(
            user_id=user_id,
            limit=limit,
            exclude_applied=exclude_applied,
            include_explanations=include_explanations
        )
        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求人推薦取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/stats/summary")
async def get_job_stats_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    求人統計サマリー

    求人全体の統計情報を取得します。
    """
    try:
        job_service = JobService(db)
        stats = await job_service.get_stats_summary()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計取得中にエラーが発生しました: {str(e)}"
        )