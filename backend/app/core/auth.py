"""
Authentication logic for user management
Handles user authentication, token validation, and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_token, is_token_expired
from app.core.database import get_db
from app.models.database import User


security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise AuthenticationError("Invalid token")

    # Check if token is expired
    if is_token_expired(token):
        raise AuthenticationError("Token expired")

    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Fetch user from database
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise AuthenticationError("User not found")

    # Check if user is active
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (convenience function)

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user object

    Raises:
        AuthenticationError: If user is not active
    """
    if not current_user.is_active:
        raise AuthenticationError("User account is disabled")
    return current_user


def require_role(required_role: str):
    """
    Decorator factory for role-based access control

    Args:
        required_role: Required role name

    Returns:
        Dependency function for FastAPI endpoints
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not hasattr(current_user, 'role') or current_user.role != required_role:
            raise AuthorizationError(f"Role '{required_role}' required")
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role

    Args:
        current_user: Current authenticated user

    Returns:
        User object if admin

    Raises:
        AuthorizationError: If user is not admin
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise AuthorizationError("Admin role required")
    return current_user


def require_self_or_admin(user_id: int):
    """
    Require user to be accessing their own data or be admin

    Args:
        user_id: Target user ID

    Returns:
        Dependency function for FastAPI endpoints
    """
    def access_checker(current_user: User = Depends(get_current_user)) -> User:
        is_self = current_user.user_id == user_id
        is_admin = hasattr(current_user, 'role') and current_user.role == 'admin'

        if not (is_self or is_admin):
            raise AuthorizationError("Access denied: can only access own data")

        return current_user
    return access_checker


class TokenBlacklist:
    """In-memory token blacklist for logout functionality"""

    def __init__(self):
        self._blacklisted_tokens = set()

    def add_token(self, token: str):
        """Add token to blacklist"""
        self._blacklisted_tokens.add(token)

    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in self._blacklisted_tokens

    def clear_expired_tokens(self):
        """Clear expired tokens from blacklist (periodic cleanup)"""
        # In production, this would be more sophisticated
        # For now, we keep all blacklisted tokens
        pass


# Global token blacklist instance
token_blacklist = TokenBlacklist()


async def get_current_user_with_blacklist_check(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user with blacklist token check

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        AuthenticationError: If token is blacklisted or invalid
    """
    token = credentials.credentials

    # Check if token is blacklisted
    if token_blacklist.is_blacklisted(token):
        raise AuthenticationError("Token has been revoked")

    # Use regular authentication
    return await get_current_user(credentials, db)


def validate_token_type(token: str, expected_type: str = "access") -> bool:
    """
    Validate token type (access vs refresh)

    Args:
        token: JWT token to validate
        expected_type: Expected token type

    Returns:
        True if token type matches, False otherwise
    """
    payload = verify_token(token)
    if not payload:
        return False

    token_type = payload.get("type", "access")
    return token_type == expected_type


def extract_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from JWT token

    Args:
        token: JWT token

    Returns:
        User ID if valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if user_id:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None

    return None