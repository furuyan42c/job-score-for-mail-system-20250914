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


# =============================================================================
# T006: Jobs CRUD Endpoints - GREEN Phase Implementation
# Minimal TDD implementation
# =============================================================================

from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel

# In-memory storage for TDD GREEN phase (will be replaced with database in REFACTOR)
_jobs_storage: Dict[int, Dict[str, Any]] = {}
_next_job_id = 1


# T006 REFACTOR: Enhanced Pydantic models with validation
from pydantic import Field, validator
from enum import Enum

class SalaryTypeEnum(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class EmploymentTypeEnum(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="求人タイトル")
    description: str = Field(..., min_length=10, max_length=2000, description="求人詳細")
    company_name: str = Field(..., min_length=1, max_length=100, description="会社名")
    location: str = Field(..., min_length=1, max_length=200, description="勤務地")
    salary_min: int = Field(..., ge=0, le=10000, description="最低時給（円）")
    salary_max: int = Field(..., ge=0, le=10000, description="最高時給（円）")
    salary_type: SalaryTypeEnum = Field(..., description="給与タイプ")
    employment_type: EmploymentTypeEnum = Field(..., description="雇用形態")
    features: Optional[Dict[str, Any]] = Field(None, description="求人特徴")

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if 'salary_min' in values and v < values['salary_min']:
            raise ValueError('最高給与は最低給与以上である必要があります')
        return v

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('タイトルは空にできません')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('詳細は空にできません')
        return v.strip()


class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    salary_min: Optional[int] = Field(None, ge=0, le=10000)
    salary_max: Optional[int] = Field(None, ge=0, le=10000)
    salary_type: Optional[SalaryTypeEnum] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    features: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('タイトルは空にできません')
        return v.strip() if v else v

    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('詳細は空にできません')
        return v.strip() if v else v


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    company_name: str
    location: str
    salary_min: int
    salary_max: int
    salary_type: str
    employment_type: str
    features: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


@router.post("/create",
    response_model=JobResponse,
    status_code=201,
    summary="新しい求人を作成",
    description="求人情報を作成します。バリデーション済みのデータが必要です。")
async def create_job(job_data: JobCreateRequest) -> JobResponse:
    """
    T006 REFACTOR: Create a new job with enhanced validation and error handling

    Args:
        job_data: 求人作成データ（バリデーション済み）

    Returns:
        作成された求人情報

    Raises:
        HTTPException: バリデーションエラーまたは作成失敗時
    """
    try:
        global _next_job_id

        # Additional business logic validation
        if job_data.salary_min > job_data.salary_max:
            raise HTTPException(
                status_code=400,
                detail="最低給与は最高給与以下である必要があります"
            )

        job_id = _next_job_id
        _next_job_id += 1

        current_time = datetime.utcnow().isoformat()

        # Enhanced job data with normalized values
        job = {
            "id": job_id,
            "title": job_data.title.strip(),
            "description": job_data.description.strip(),
            "company_name": job_data.company_name.strip(),
            "location": job_data.location.strip(),
            "salary_min": job_data.salary_min,
            "salary_max": job_data.salary_max,
            "salary_type": job_data.salary_type.value,
            "employment_type": job_data.employment_type.value,
            "features": job_data.features or {},
            "created_at": current_time,
            "updated_at": current_time,
            "status": "active"  # Default status
        }

        _jobs_storage[job_id] = job

        # Log successful creation (would be proper logging in production)
        print(f"✅ Job created successfully: ID {job_id}, Title: {job_data.title}")

        return JobResponse(**job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"求人作成中にエラーが発生しました: {str(e)}"
        )


@router.get("/job/{job_id}",
    response_model=JobResponse,
    summary="求人詳細を取得",
    description="指定されたIDの求人詳細を取得します。")
async def get_job_by_id(
    job_id: int = Path(..., gt=0, description="求人ID")
) -> JobResponse:
    """
    T006 REFACTOR: Get a job by ID with enhanced validation and error handling

    Args:
        job_id: 求人ID（1以上の整数）

    Returns:
        求人詳細情報

    Raises:
        HTTPException: 求人が見つからない場合
    """
    try:
        if job_id not in _jobs_storage:
            raise HTTPException(
                status_code=404,
                detail=f"求人ID {job_id} が見つかりません"
            )

        job = _jobs_storage[job_id]

        # Check if job is still active (in production, would check status)
        if job.get("status") == "deleted":
            raise HTTPException(
                status_code=404,
                detail=f"求人ID {job_id} は削除されています"
            )

        return JobResponse(**job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"求人取得中にエラーが発生しました: {str(e)}"
        )


@router.put("/job/{job_id}",
    response_model=JobResponse,
    summary="求人情報を更新",
    description="指定されたIDの求人情報を更新します。")
async def update_job(
    job_id: int = Path(..., gt=0, description="求人ID"),
    job_data: JobUpdateRequest = ...
) -> JobResponse:
    """T006 REFACTOR: Update a job by ID with enhanced validation"""
    try:
        if job_id not in _jobs_storage:
            raise HTTPException(
                status_code=404,
                detail=f"求人ID {job_id} が見つかりません"
            )

        current_job = _jobs_storage[job_id].copy()

        if current_job.get("status") == "deleted":
            raise HTTPException(
                status_code=404,
                detail=f"削除された求人は更新できません"
            )

        # Update only provided fields with enhanced validation
        update_data = job_data.model_dump(exclude_unset=True)

        # Convert enum values to strings
        if "salary_type" in update_data:
            update_data["salary_type"] = update_data["salary_type"].value
        if "employment_type" in update_data:
            update_data["employment_type"] = update_data["employment_type"].value

        for field, value in update_data.items():
            current_job[field] = value

        # Validate salary range after update
        if current_job["salary_min"] > current_job["salary_max"]:
            raise HTTPException(
                status_code=400,
                detail="最低給与は最高給与以下である必要があります"
            )

        current_job["updated_at"] = datetime.utcnow().isoformat()

        _jobs_storage[job_id] = current_job
        print(f"✅ Job updated successfully: ID {job_id}")

        return JobResponse(**current_job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"求人更新中にエラーが発生しました: {str(e)}"
        )


@router.delete("/job/{job_id}",
    status_code=204,
    summary="求人を削除",
    description="指定されたIDの求人を削除します。")
async def delete_job(
    job_id: int = Path(..., gt=0, description="求人ID")
) -> None:
    """T006 REFACTOR: Delete a job by ID with enhanced validation"""
    try:
        if job_id not in _jobs_storage:
            raise HTTPException(
                status_code=404,
                detail=f"求人ID {job_id} が見つかりません"
            )

        job = _jobs_storage[job_id]
        if job.get("status") == "deleted":
            raise HTTPException(
                status_code=404,
                detail=f"求人ID {job_id} は既に削除されています"
            )

        # Soft delete (mark as deleted instead of hard delete)
        job["status"] = "deleted"
        job["deleted_at"] = datetime.utcnow().isoformat()
        job["updated_at"] = datetime.utcnow().isoformat()

        _jobs_storage[job_id] = job
        print(f"✅ Job deleted successfully: ID {job_id}")

        # In production, would actually delete from storage
        # del _jobs_storage[job_id]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"求人削除中にエラーが発生しました: {str(e)}"
        )


@router.get("/list",
    response_model=JobListResponse,
    summary="求人一覧を取得",
    description="求人一覧をページネーション付きで取得します。")
async def list_jobs(
    limit: int = Query(default=10, ge=1, le=100, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="オフセット"),
    status: Optional[str] = Query(default="active", description="求人ステータス")
) -> JobListResponse:
    """T006 REFACTOR: List all jobs with enhanced pagination and filtering"""
    try:
        # Filter jobs by status
        filtered_jobs = [
            job for job in _jobs_storage.values()
            if job.get("status", "active") == status
        ]

        total = len(filtered_jobs)

        # Sort by updated_at (newest first)
        sorted_jobs = sorted(
            filtered_jobs,
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )

        # Apply pagination
        start = offset
        end = offset + limit
        paginated_jobs = sorted_jobs[start:end]

        # Calculate pagination info
        page = (offset // limit) + 1
        has_next = end < total
        has_prev = offset > 0

        return JobListResponse(
            jobs=[JobResponse(**job) for job in paginated_jobs],
            total=total,
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"求人一覧取得中にエラーが発生しました: {str(e)}"
        )