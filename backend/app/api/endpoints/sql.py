#!/usr/bin/env python3
"""
T012: SQL execution API endpoints (REFACTORED)

Production-ready implementation with security controls and query optimization.
"""

from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import time
import re
import logging
import asyncio
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sql", tags=["sql"])


class SqlExecuteRequest(BaseModel):
    """SQL execution request with validation"""
    query: str = Field(..., min_length=1, max_length=10000)
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timeout: Optional[int] = Field(30000, ge=100, le=60000)  # 100ms to 60s
    max_rows: Optional[int] = Field(1000, ge=1, le=10000)

    @validator('query')
    def validate_query(cls, v):
        # Remove comments and normalize whitespace
        cleaned = re.sub(r'--.*$', '', v, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        cleaned = ' '.join(cleaned.split())

        if not cleaned:
            raise ValueError('Query cannot be empty')

        return v


class SqlExecuteResponse(BaseModel):
    """SQL execution response"""
    results: List[List[Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    params_used: Optional[List[str]] = None
    truncated: Optional[bool] = None
    row_limit_reached: Optional[bool] = None


async def verify_admin_auth(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Verify admin authentication for SQL endpoint.

    Args:
        authorization: Bearer token
        db: Database session

    Returns:
        Authenticated admin user

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # Verify token and get user
    try:
        user = await verify_api_key(token, db)
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/execute", response_model=SqlExecuteResponse)
async def execute_sql(
    request: SqlExecuteRequest,
    admin_user: User = Depends(verify_admin_auth),
    db: AsyncSession = Depends(get_db)
) -> SqlExecuteResponse:
    """
    Execute read-only SQL queries with security controls.

    Args:
        request: SQL query and parameters
        admin_user: Authenticated admin user
        db: Database session

    Returns:
        Query results with metadata

    Raises:
        HTTPException: 400 for invalid queries, 403 for write operations,
                      408 for timeout, 500 for execution errors
    """
    query_upper = request.query.upper()

    # Security: Check for write operations
    write_operations = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'CALL', 'EXEC', 'EXECUTE'
    ]

    # Use regex to check for write operations at word boundaries
    for op in write_operations:
        if re.search(r'\b' + op + r'\b', query_upper):
            logger.warning(f"Write operation attempted by {admin_user.email}: {op}")
            raise HTTPException(
                status_code=403,
                detail=f"Operation {op} not allowed. Only SELECT queries are permitted."
            )

    # Security: Check for multiple statements
    if ';' in request.query.strip().rstrip(';'):
        logger.warning(f"Multiple statements attempted by {admin_user.email}")
        raise HTTPException(
            status_code=400,
            detail="Multiple statements not allowed"
        )

    # Log query for audit
    logger.info(f"SQL query by {admin_user.email}: {request.query[:100]}...")

    try:
        start_time = time.time()

        # Build query with parameters
        if request.params:
            # Use SQLAlchemy's parameter binding for safety
            stmt = text(request.query).bindparams(**request.params)
        else:
            stmt = text(request.query)

        # Execute with timeout
        timeout_seconds = request.timeout / 1000.0 if request.timeout else 30.0

        async def execute_with_timeout():
            try:
                result = await db.execute(stmt)
                # Fetch limited results
                rows = result.fetchmany(request.max_rows + 1)  # +1 to detect truncation
                return rows, result.keys()
            except Exception as e:
                raise e

        try:
            rows, keys = await asyncio.wait_for(
                execute_with_timeout(),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Query timeout for {admin_user.email} after {timeout_seconds}s")
            raise HTTPException(
                status_code=408,
                detail=f"Query timeout exceeded ({timeout_seconds}s)"
            )

        # Process results
        truncated = len(rows) > request.max_rows
        if truncated:
            rows = rows[:request.max_rows]

        # Convert rows to list format
        results = []
        for row in rows:
            results.append(list(row))

        columns = list(keys) if keys else []
        execution_time = time.time() - start_time

        response = SqlExecuteResponse(
            results=results,
            columns=columns,
            row_count=len(results),
            execution_time=execution_time
        )

        if request.params:
            response.params_used = list(request.params.keys())

        if truncated:
            response.truncated = True
            response.row_limit_reached = True

        # Log successful execution
        logger.info(
            f"Query executed successfully by {admin_user.email}: "
            f"{len(results)} rows in {execution_time:.3f}s"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution error for {admin_user.email}: {e}")

        # Check for specific database errors
        error_msg = str(e).lower()
        if 'syntax' in error_msg or 'parse' in error_msg:
            raise HTTPException(status_code=400, detail="Invalid SQL syntax")
        elif 'permission' in error_msg or 'denied' in error_msg:
            raise HTTPException(status_code=403, detail="Permission denied")
        elif 'not found' in error_msg or 'does not exist' in error_msg:
            raise HTTPException(status_code=404, detail="Table or column not found")
        else:
            raise HTTPException(
                status_code=500,
                detail="Query execution failed"
            )