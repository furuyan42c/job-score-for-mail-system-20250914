"""
T006: Jobs CRUD Endpoints - GREEN Phase Implementation
Minimal implementation to pass the RED phase tests
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# In-memory storage for TDD GREEN phase (will be replaced with database in REFACTOR)
_jobs_storage: Dict[int, Dict[str, Any]] = {}
_next_job_id = 1


# Minimal Pydantic models for TDD GREEN phase
class JobCreateRequest(BaseModel):
    title: str
    description: str
    company_name: str
    location: str
    salary_min: int
    salary_max: int
    salary_type: str
    employment_type: str
    features: Optional[Dict[str, Any]] = None


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_type: Optional[str] = None
    employment_type: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


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


# =============================================================================
# T006 GREEN: Minimal CRUD Endpoints
# =============================================================================

@router.post("/create", response_model=JobResponse, status_code=201)
async def create_job(job_data: JobCreateRequest) -> JobResponse:
    """
    T006 GREEN: Create a new job
    Minimal implementation for TDD
    """
    global _next_job_id

    job_id = _next_job_id
    _next_job_id += 1

    current_time = datetime.utcnow().isoformat()

    job = {
        "id": job_id,
        "title": job_data.title,
        "description": job_data.description,
        "company_name": job_data.company_name,
        "location": job_data.location,
        "salary_min": job_data.salary_min,
        "salary_max": job_data.salary_max,
        "salary_type": job_data.salary_type,
        "employment_type": job_data.employment_type,
        "features": job_data.features,
        "created_at": current_time,
        "updated_at": current_time
    }

    _jobs_storage[job_id] = job
    return JobResponse(**job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: int) -> JobResponse:
    """
    T006 GREEN: Get a job by ID
    Minimal implementation for TDD
    """
    if job_id not in _jobs_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found"
        )

    job = _jobs_storage[job_id]
    return JobResponse(**job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_data: JobUpdateRequest) -> JobResponse:
    """
    T006 GREEN: Update a job by ID
    Minimal implementation for TDD
    """
    if job_id not in _jobs_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found"
        )

    job = _jobs_storage[job_id].copy()

    # Update only provided fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        job[field] = value

    job["updated_at"] = datetime.utcnow().isoformat()

    _jobs_storage[job_id] = job
    return JobResponse(**job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: int) -> None:
    """
    T006 GREEN: Delete a job by ID
    Minimal implementation for TDD
    """
    if job_id not in _jobs_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found"
        )

    del _jobs_storage[job_id]


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> List[JobResponse]:
    """
    T006 GREEN: List all jobs with pagination
    Minimal implementation for TDD
    """
    all_jobs = list(_jobs_storage.values())

    # Apply pagination
    start = offset
    end = offset + limit
    paginated_jobs = all_jobs[start:end]

    return [JobResponse(**job) for job in paginated_jobs]