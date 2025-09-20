"""
Main API Router for T005-T013 TDD Endpoints
Consolidates all new API endpoints implemented following TDD principles
"""
from fastapi import APIRouter

# Import all endpoint routers
from app.api.endpoints.health import router as health_router
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.additional_endpoints import router as additional_router
from app.api.endpoints.matching import router as matching_router
from app.api.endpoints.email import router as email_router
from app.api.endpoints.sql import router as sql_router
from app.api.endpoints.monitoring import router as monitoring_router
from app.api.endpoints.auth import router as auth_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers with proper prefixes
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    jobs_router,
    prefix="/jobs",
    tags=["jobs"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    additional_router,
    prefix="",  # Additional endpoints have their own prefixes
    tags=["additional"]
)

# Include T010-T013 endpoints
api_router.include_router(
    matching_router,
    tags=["matching"]
)

api_router.include_router(
    email_router,
    tags=["email"]
)

api_router.include_router(
    sql_router,
    tags=["sql"]
)

api_router.include_router(
    monitoring_router,
    tags=["monitoring"]
)

api_router.include_router(
    auth_router,
    tags=["authentication"]
)