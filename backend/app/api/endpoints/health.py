"""
T005: Health Check Endpoint - GREEN Phase Implementation
Minimal implementation to pass the RED phase tests
"""
from fastapi import APIRouter
from datetime import datetime
import time
from typing import Dict, Any

router = APIRouter()

# Global start time for uptime calculation
_start_time = time.time()


@router.get("/check")
async def health_check() -> Dict[str, Any]:
    """
    T005 GREEN: Minimal health check endpoint
    Returns basic health status information
    """
    current_time = time.time()
    uptime = current_time - _start_time

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime": uptime
    }