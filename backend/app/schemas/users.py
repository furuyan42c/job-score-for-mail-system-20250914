"""
User management schemas for TDD GREEN phase
Minimal Pydantic models for user registration and profile management
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserRegistrationRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., min_length=1, max_length=100, description="User full name")
    pref_cd: str = Field(..., description="Prefecture code (01-47)")
    birth_year: Optional[int] = Field(None, ge=1900, le=2024, description="Birth year")
    gender: Optional[str] = Field(None, pattern="^[MF]$", description="Gender (M/F)")
    phone: Optional[str] = Field(None, description="Phone number")
    job_search_status: Optional[str] = Field(
        None,
        pattern="^(active|passive|not_searching)$",
        description="Job search status"
    )
    preferred_industries: Optional[List[str]] = Field(default_factory=list, description="Preferred industries")
    skills: Optional[List[str]] = Field(default_factory=list, description="User skills")

    @validator('pref_cd')
    def validate_pref_cd(cls, v):
        """Validate prefecture code is between 01-47"""
        try:
            pref_num = int(v)
            if not (1 <= pref_num <= 47):
                raise ValueError("Prefecture code must be between 01 and 47")
        except ValueError:
            raise ValueError("Prefecture code must be a valid number")
        return v

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserRegistrationResponse(BaseModel):
    """User registration response schema"""
    user_id: int = Field(..., description="Created user ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    pref_cd: str = Field(..., description="Prefecture code")
    birth_year: Optional[int] = Field(None, description="Birth year")
    gender: Optional[str] = Field(None, description="Gender")
    phone: Optional[str] = Field(None, description="Phone number")
    job_search_status: Optional[str] = Field(None, description="Job search status")
    preferred_industries: Optional[List[str]] = Field(default_factory=list, description="Preferred industries")
    skills: Optional[List[str]] = Field(default_factory=list, description="Skills")
    created_at: datetime = Field(..., description="Creation timestamp")


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    pref_cd: str = Field(..., description="Prefecture code")
    birth_year: Optional[int] = Field(None, description="Birth year")
    gender: Optional[str] = Field(None, description="Gender")
    phone: Optional[str] = Field(None, description="Phone number")
    job_search_status: Optional[str] = Field(None, description="Job search status")
    preferred_industries: Optional[List[str]] = Field(default_factory=list, description="Preferred industries")
    skills: Optional[List[str]] = Field(default_factory=list, description="Skills")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserProfileUpdateRequest(BaseModel):
    """User profile update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User full name")
    pref_cd: Optional[str] = Field(None, description="Prefecture code (01-47)")
    birth_year: Optional[int] = Field(None, ge=1900, le=2024, description="Birth year")
    gender: Optional[str] = Field(None, pattern="^[MF]$", description="Gender (M/F)")
    phone: Optional[str] = Field(None, description="Phone number")
    job_search_status: Optional[str] = Field(
        None,
        pattern="^(active|passive|not_searching)$",
        description="Job search status"
    )
    preferred_industries: Optional[List[str]] = Field(None, description="Preferred industries")
    skills: Optional[List[str]] = Field(None, description="User skills")
    email: Optional[EmailStr] = Field(None, description="Email (requires verification)")


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class AccountDeletionRequest(BaseModel):
    """Account deletion request schema"""
    password: str = Field(..., description="Current password for confirmation")
    confirm: str = Field(..., description="Must be 'DELETE MY ACCOUNT'")

    @validator('confirm')
    def validate_confirmation(cls, v):
        """Validate deletion confirmation text"""
        if v != "DELETE MY ACCOUNT":
            raise ValueError("Must type 'DELETE MY ACCOUNT' to confirm")
        return v


class UserPreferencesResponse(BaseModel):
    """User preferences response schema"""
    email_notifications: Dict[str, bool] = Field(..., description="Email notification settings")
    job_alert_frequency: str = Field(..., description="Job alert frequency")
    preferred_job_types: List[str] = Field(..., description="Preferred job types")
    salary_range: Dict[str, int] = Field(..., description="Salary range preferences")
    commute_time_max: int = Field(..., description="Maximum commute time in minutes")


class UserPreferencesUpdateRequest(BaseModel):
    """User preferences update request schema"""
    email_notifications: Optional[Dict[str, bool]] = Field(None, description="Email notification settings")
    job_alert_frequency: Optional[str] = Field(
        None,
        pattern="^(daily|weekly|monthly)$",
        description="Job alert frequency"
    )
    preferred_job_types: Optional[List[str]] = Field(None, description="Preferred job types")
    salary_range: Optional[Dict[str, int]] = Field(None, description="Salary range preferences")
    commute_time_max: Optional[int] = Field(None, ge=0, le=180, description="Maximum commute time in minutes")


class EmailUpdateResponse(BaseModel):
    """Email update response schema"""
    message: str = Field(..., description="Update status message")
    verification_sent: bool = Field(..., description="Whether verification email was sent")


class PasswordChangeResponse(BaseModel):
    """Password change response schema"""
    message: str = Field(..., description="Success message")


class AccountDeletionResponse(BaseModel):
    """Account deletion response schema"""
    message: str = Field(..., description="Deletion confirmation message")


class ProfileImageResponse(BaseModel):
    """Profile image upload response schema"""
    profile_image_url: str = Field(..., description="URL of uploaded profile image")
    thumbnail_url: str = Field(..., description="URL of thumbnail image")