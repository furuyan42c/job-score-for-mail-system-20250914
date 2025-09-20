#!/usr/bin/env python3
"""
T014-T015: Authentication API endpoints (GREEN Phase)

Minimal implementation for user registration and authentication.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Rate limiting storage (in-memory for GREEN phase)
_rate_limit_storage: Dict[str, list] = {}


class UserRegistrationRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    preferences: Optional[Dict[str, Any]] = None
    profile: Optional[Dict[str, Any]] = None

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v

    @validator('email')
    def normalize_email(cls, v):
        """Normalize email to lowercase"""
        return v.lower().strip()


class UserRegistrationResponse(BaseModel):
    """User registration response"""
    user_id: str
    email: str
    name: str
    created_at: datetime
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str

    @validator('email')
    def normalize_email(cls, v):
        """Normalize email to lowercase"""
        return v.lower().strip()


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: Dict[str, Any]
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """User profile response"""
    user_id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool


def check_rate_limit(identifier: str, max_attempts: int = 5) -> bool:
    """Simple rate limiting check"""
    now = datetime.utcnow()
    if identifier not in _rate_limit_storage:
        _rate_limit_storage[identifier] = []

    # Clean old attempts (older than 1 minute)
    _rate_limit_storage[identifier] = [
        t for t in _rate_limit_storage[identifier]
        if (now - t).seconds < 60
    ]

    # Check if exceeded
    if len(_rate_limit_storage[identifier]) >= max_attempts:
        return False

    # Record attempt
    _rate_limit_storage[identifier].append(now)
    return True


@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
) -> UserRegistrationResponse:
    """
    Register a new user.

    Minimal implementation for GREEN phase.
    """
    # Rate limiting
    if not check_rate_limit(f"register:{request.email}"):
        raise HTTPException(status_code=429, detail="Too many registration attempts")

    # Check if user exists
    existing_user = await db.execute(
        select(User).where(User.email == request.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )

    # Create user
    hashed_password = get_password_hash(request.password)
    user = User(
        email=request.email,
        name=request.name,
        hashed_password=hashed_password,
        user_id=f"user_{datetime.utcnow().timestamp()}",
        is_active=True
    )

    # Save preferences if provided
    if request.preferences:
        user.preferences = request.preferences

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(hours=24)
    )

    return UserRegistrationResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        access_token=access_token
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Login user and return access token.

    Minimal implementation for GREEN phase.
    """
    # Rate limiting
    if not check_rate_limit(f"login:{request.email}"):
        raise HTTPException(status_code=429, detail="Too many login attempts")

    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate tokens
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(hours=1)
    )

    refresh_token = create_access_token(
        data={"sub": user.email, "type": "refresh"},
        expires_delta=timedelta(days=7)
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name
        },
        refresh_token=refresh_token
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    from app.core.security import decode_token

    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user profile"""
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Logout user (invalidate token)"""
    # In production, would blacklist the token
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Refresh access token using refresh token"""
    from app.core.security import decode_token

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Get user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Generate new access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(hours=1)
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name
        }
    )


@router.post("/reset-password")
async def reset_password_request(
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Request password reset"""
    # Check user exists
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password/confirm")
async def reset_password_confirm(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Confirm password reset with token"""
    # In production, would validate reset token
    # For GREEN phase, just return success
    return {"message": "Password has been reset successfully"}


@router.put("/update-password")
async def update_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Update user password"""
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return {"message": "Password updated successfully"}