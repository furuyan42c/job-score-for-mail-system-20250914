"""
Authentication router - Production Ready (T015 REFACTOR)
Implements secure JWT-based authentication with rate limiting and security features
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import time
import logging

from app.core.database import get_db
from app.core.auth import get_current_user_with_blacklist_check, token_blacklist, extract_user_id_from_token
from app.services.user_service import UserService
from app.models.database import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    AuthErrorResponse,
    RateLimitErrorResponse
)

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Rate limiting for login attempts
LOGIN_ATTEMPTS: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes


def check_rate_limit(identifier: str) -> bool:
    """
    Check if identifier (IP or email) is rate limited

    Args:
        identifier: IP address or email to check

    Returns:
        True if rate limited, False otherwise
    """
    current_time = time.time()

    if identifier not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[identifier] = []

    # Clean old attempts
    LOGIN_ATTEMPTS[identifier] = [
        attempt_time for attempt_time in LOGIN_ATTEMPTS[identifier]
        if current_time - attempt_time < RATE_LIMIT_WINDOW
    ]

    return len(LOGIN_ATTEMPTS[identifier]) >= MAX_LOGIN_ATTEMPTS


def record_login_attempt(identifier: str):
    """
    Record a failed login attempt

    Args:
        identifier: IP address or email
    """
    if identifier not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[identifier] = []

    LOGIN_ATTEMPTS[identifier].append(time.time())


def clear_login_attempts(identifier: str):
    """
    Clear login attempts for identifier (on successful login)

    Args:
        identifier: IP address or email
    """
    if identifier in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[identifier] = []


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service instance"""
    return UserService(db)


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user and return access/refresh tokens

    **Rate Limiting**: 5 attempts per 5 minutes per email address

    - **email**: User email address
    - **password**: User password

    **Returns**: Access token, refresh token, and user information
    """
    email = login_data.email.lower()

    # Check rate limiting by email
    if check_rate_limit(email):
        logger.warning(f"Rate limit exceeded for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many failed attempts."
        )

    try:
        # Authenticate user
        user = await user_service.authenticate_user(email, login_data.password)
        if not user:
            # Record failed attempt
            record_login_attempt(email)
            logger.warning(f"Authentication failed for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_credentials"
            )

        # Clear failed attempts on successful login
        clear_login_attempts(email)

        # Create tokens
        tokens = await user_service.create_user_tokens(user)

        logger.info(f"User {user.user_id} logged in successfully")

        return LoginResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create new access token using refresh token

    - **refresh_token**: Valid refresh token

    **Returns**: New access token with expiration time
    """
    try:
        result = await user_service.refresh_access_token(refresh_data.refresh_token)
        return RefreshTokenResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service unavailable"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
):
    """
    Logout user by invalidating access token

    **Authentication Required**: Valid access token in Authorization header

    **Returns**: Logout confirmation message
    """
    try:
        result = await user_service.logout_user(credentials.credentials)

        # Extract user ID for logging
        user_id = extract_user_id_from_token(credentials.credentials)
        if user_id:
            logger.info(f"User {user_id} logged out successfully")

        return LogoutResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service unavailable"
        )


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user_with_blacklist_check)
):
    """
    Verify if current access token is valid

    **Authentication Required**: Valid access token in Authorization header

    **Returns**: User information if token is valid
    """
    return {
        "valid": True,
        "user": {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "is_active": current_user.is_active
        }
    }


@router.get("/me")
async def get_authenticated_user(
    current_user: User = Depends(get_current_user_with_blacklist_check)
):
    """
    Get current authenticated user information

    **Authentication Required**: Valid access token in Authorization header

    **Returns**: Current user profile information
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "email_verified": current_user.email_verified,
        "created_at": current_user.created_at,
        "last_login_date": current_user.last_login_date
    }


# Admin endpoints
@router.post("/admin/revoke-token")
async def revoke_user_token(
    data: Dict[str, str],
    current_user: User = Depends(get_current_user_with_blacklist_check)
):
    """
    Revoke user token (admin only)

    **Admin Only**: Requires admin role

    - **token**: Token to revoke
    """
    from app.core.auth import require_admin

    # Check admin role
    require_admin(current_user)

    token = data.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )

    # Add token to blacklist
    token_blacklist.add_token(token)

    logger.info(f"Admin {current_user.user_id} revoked token")

    return {"message": "Token revoked successfully"}


@router.get("/admin/login-attempts")
async def get_login_attempts(
    current_user: User = Depends(get_current_user_with_blacklist_check)
):
    """
    Get current login attempts (admin only)

    **Admin Only**: Requires admin role

    **Returns**: Current rate limiting state
    """
    from app.core.auth import require_admin

    # Check admin role
    require_admin(current_user)

    current_time = time.time()
    active_attempts = {}

    for identifier, attempts in LOGIN_ATTEMPTS.items():
        # Clean old attempts
        recent_attempts = [
            attempt for attempt in attempts
            if current_time - attempt < RATE_LIMIT_WINDOW
        ]
        if recent_attempts:
            active_attempts[identifier] = {
                "count": len(recent_attempts),
                "rate_limited": len(recent_attempts) >= MAX_LOGIN_ATTEMPTS,
                "last_attempt": datetime.fromtimestamp(max(recent_attempts)).isoformat()
            }

    return {
        "active_attempts": active_attempts,
        "rate_limit_config": {
            "max_attempts": MAX_LOGIN_ATTEMPTS,
            "window_seconds": RATE_LIMIT_WINDOW
        }
    }


@router.post("/admin/clear-rate-limit")
async def clear_rate_limit(
    data: Dict[str, str],
    current_user: User = Depends(get_current_user_with_blacklist_check)
):
    """
    Clear rate limit for identifier (admin only)

    **Admin Only**: Requires admin role

    - **identifier**: Email or IP to clear rate limit for
    """
    from app.core.auth import require_admin

    # Check admin role
    require_admin(current_user)

    identifier = data.get("identifier")
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier is required"
        )

    clear_login_attempts(identifier)

    logger.info(f"Admin {current_user.user_id} cleared rate limit for {identifier}")

    return {"message": f"Rate limit cleared for {identifier}"}