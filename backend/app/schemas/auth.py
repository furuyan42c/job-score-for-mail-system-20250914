"""
Authentication schemas for TDD GREEN phase
Minimal Pydantic models for authentication endpoints
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, Optional


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=1800, description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str = Field(..., description="New JWT access token")
    expires_in: int = Field(default=1800, description="Token expiration time in seconds")


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = Field(..., description="Logout confirmation message")


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[int] = Field(None, description="User ID if token is valid")
    expires_at: Optional[str] = Field(None, description="Token expiration time")


class AuthErrorResponse(BaseModel):
    """Authentication error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")


class RateLimitErrorResponse(BaseModel):
    """Rate limit error response schema"""
    detail: str = Field(..., description="Rate limit error message")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")