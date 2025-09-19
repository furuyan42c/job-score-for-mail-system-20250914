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