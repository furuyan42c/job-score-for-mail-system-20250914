#!/usr/bin/env python3
"""
T010: Matching API endpoints (REFACTORED)

Production-ready implementation with database integration.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

from app.core.database import get_db
from app.models.score import Score, ScoreType
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["matching"])


class JobMatch(BaseModel):
    """Job match result with validation"""
    job_id: str = Field(..., description="Unique job identifier")
    match_score: float = Field(..., ge=0, le=100, description="Match score (0-100)")
    job_details: Dict[str, Any] = Field(default_factory=dict, description="Job details")


class UserMatchesResponse(BaseModel):
    """User matches response with pagination"""
    user_id: str = Field(..., description="User identifier")
    matches: List[JobMatch] = Field(default_factory=list, description="List of job matches")
    total_count: int = Field(..., ge=0, description="Total number of matches")
    has_more: bool = Field(..., description="More results available")
    limit: int = Field(..., ge=1, le=100, description="Results per page")
    offset: int = Field(..., ge=0, description="Pagination offset")


@router.get("/user/{user_id}", response_model=UserMatchesResponse)
async def get_user_matches(
    user_id: str = Path(..., description="User ID"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum match score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum match score"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: Optional[str] = Query("score_desc", regex="^(score_desc|score_asc|date_desc|date_asc)$"),
    db: AsyncSession = Depends(get_db)
) -> UserMatchesResponse:
    """
    Get job matches for a user with filtering and pagination.

    Args:
        user_id: User identifier
        min_score: Minimum match score filter
        max_score: Maximum match score filter
        limit: Number of results per page
        offset: Pagination offset
        sort_by: Sort order
        db: Database session

    Returns:
        UserMatchesResponse with matched jobs

    Raises:
        HTTPException: 404 if user not found
    """
    try:
        # Verify user exists
        user_query = select(User).where(User.user_id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Build query for matches
        query = select(Score, Job).join(
            Job, Score.job_id == Job.id
        ).where(
            and_(
                Score.user_id == user.id,
                Score.score_type == ScoreType.MATCH
            )
        )

        # Apply score filters
        if min_score is not None:
            query = query.where(Score.match_score >= min_score)
        if max_score is not None:
            query = query.where(Score.match_score <= max_score)

        # Apply sorting
        if sort_by == "score_desc":
            query = query.order_by(Score.match_score.desc())
        elif sort_by == "score_asc":
            query = query.order_by(Score.match_score.asc())
        elif sort_by == "date_desc":
            query = query.order_by(Score.calculated_at.desc())
        else:
            query = query.order_by(Score.calculated_at.asc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Format matches
        matches = [
            JobMatch(
                job_id=str(job.job_id),
                match_score=float(score.match_score or score.total_score),
                job_details={
                    "title": job.job_contents,
                    "company": job.company_name,
                    "location": job.area,
                    "salary": str(job.salary) if job.salary else None,
                    "employment_type": job.employment_type,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
            )
            for score, job in rows
        ]

        return UserMatchesResponse(
            user_id=user_id,
            matches=matches,
            total_count=total_count,
            has_more=(offset + len(matches)) < total_count,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching matches for user {user_id}: {e}")
        # Return empty results on error (fail gracefully)
        return UserMatchesResponse(
            user_id=user_id,
            matches=[],
            total_count=0,
            has_more=False,
            limit=limit,
            offset=offset
        )