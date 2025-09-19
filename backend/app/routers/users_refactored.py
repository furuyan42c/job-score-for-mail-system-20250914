"""
User management router - Production Ready (T014-T016 REFACTOR)
Implements secure user registration, authentication, and profile management
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_active_user, require_self_or_admin
from app.services.user_service import UserService
from app.models.database import User
from app.schemas.users import (
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    AccountDeletionRequest,
    AccountDeletionResponse,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    EmailUpdateResponse,
    ProfileImageResponse
)

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service instance"""
    return UserService(db)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRegistrationResponse)
async def register_user(
    user_data: UserRegistrationRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user with secure password hashing

    - **email**: Valid email address (must be unique)
    - **password**: Strong password (8+ chars, uppercase, lowercase, digit, special char)
    - **name**: Full name
    - **pref_cd**: Prefecture code (01-47)
    - Optional fields: birth_year, gender, phone, job_search_status, etc.
    """
    try:
        user = await user_service.register_user(user_data)

        return UserRegistrationResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            pref_cd=user.pref_cd,
            birth_year=user.birth_year,
            gender=user.gender,
            phone=user.phone,
            job_search_status=user.job_search_status,
            preferred_industries=user.preferred_industries or [],
            skills=user.skills or [],
            created_at=user.created_at
        )
    except Exception as e:
        # Re-raise HTTP exceptions, wrap others
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user's profile

    Returns detailed user profile information including preferences and statistics.
    """
    user_with_profile = await user_service.get_user_profile(current_user.user_id)
    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    return UserProfileResponse(
        user_id=user_with_profile.user_id,
        email=user_with_profile.email,
        name=user_with_profile.name,
        pref_cd=user_with_profile.pref_cd,
        birth_year=user_with_profile.birth_year,
        gender=user_with_profile.gender,
        phone=user_with_profile.phone,
        job_search_status=user_with_profile.job_search_status,
        preferred_industries=user_with_profile.preferred_industries or [],
        skills=user_with_profile.skills or [],
        created_at=user_with_profile.created_at,
        updated_at=user_with_profile.updated_at
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    update_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's profile

    Updates user profile with provided data. Email changes require separate verification.
    """
    # Handle email update separately (requires verification)
    if update_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email updates must be done through separate endpoint for security"
        )

    try:
        updated_user = await user_service.update_user_profile(
            current_user.user_id,
            update_data
        )

        return UserProfileResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            name=updated_user.name,
            pref_cd=updated_user.pref_cd,
            birth_year=updated_user.birth_year,
            gender=updated_user.gender,
            phone=updated_user.phone,
            job_search_status=updated_user.job_search_status,
            preferred_industries=updated_user.preferred_industries or [],
            skills=updated_user.skills or [],
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.patch("/me", response_model=UserProfileResponse)
async def partial_update_user_profile(
    update_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Partially update current user's profile

    Only updates fields that are provided in the request body.
    """
    return await update_user_profile(update_data, current_user, user_service)


@router.post("/me/change-password", response_model=PasswordChangeResponse)
async def change_user_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change user password

    Requires current password for verification. New password must meet strength requirements.
    """
    try:
        result = await user_service.change_password(
            current_user.user_id,
            password_data.current_password,
            password_data.new_password
        )

        return PasswordChangeResponse(message=result["message"])
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.delete("/me", response_model=AccountDeletionResponse)
async def delete_user_account(
    deletion_data: AccountDeletionRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user account (soft delete)

    Requires password confirmation and explicit confirmation text.
    Account is deactivated but data is retained for analytics.
    """
    try:
        result = await user_service.delete_user_account(
            current_user.user_id,
            deletion_data.password
        )

        return AccountDeletionResponse(message=result["message"])
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed"
        )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user preferences and notification settings
    """
    from app.models.database import UserPreferences

    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.user_id
    ).first()

    if not preferences:
        # Return default preferences
        return UserPreferencesResponse(
            email_notifications={
                "job_alerts": True,
                "newsletter": False,
                "system_updates": True
            },
            job_alert_frequency="weekly",
            preferred_job_types=["full_time"],
            salary_range={"min": 0, "max": 10000000},
            commute_time_max=60
        )

    return UserPreferencesResponse(
        email_notifications=preferences.email_notifications or {
            "job_alerts": True,
            "newsletter": False,
            "system_updates": True
        },
        job_alert_frequency=preferences.job_alert_frequency or "weekly",
        preferred_job_types=preferences.preferred_job_types or ["full_time"],
        salary_range={
            "min": preferences.preferred_salary_min or 0,
            "max": preferences.preferred_salary_max or 10000000
        },
        commute_time_max=preferences.commute_time_max or 60
    )


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences and notification settings
    """
    from app.models.database import UserPreferences

    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.user_id
    ).first()

    if not preferences:
        # Create new preferences
        preferences = UserPreferences(
            user_id=current_user.user_id,
            email_notifications=preferences_data.email_notifications or {
                "job_alerts": True,
                "newsletter": False,
                "system_updates": True
            },
            job_alert_frequency=preferences_data.job_alert_frequency or "weekly",
            preferred_job_types=preferences_data.preferred_job_types or ["full_time"],
            preferred_salary_min=preferences_data.salary_range.get("min") if preferences_data.salary_range else None,
            preferred_salary_max=preferences_data.salary_range.get("max") if preferences_data.salary_range else None,
            commute_time_max=preferences_data.commute_time_max or 60
        )
        db.add(preferences)
    else:
        # Update existing preferences
        if preferences_data.email_notifications is not None:
            preferences.email_notifications = preferences_data.email_notifications
        if preferences_data.job_alert_frequency is not None:
            preferences.job_alert_frequency = preferences_data.job_alert_frequency
        if preferences_data.preferred_job_types is not None:
            preferences.preferred_job_types = preferences_data.preferred_job_types
        if preferences_data.salary_range is not None:
            preferences.preferred_salary_min = preferences_data.salary_range.get("min")
            preferences.preferred_salary_max = preferences_data.salary_range.get("max")
        if preferences_data.commute_time_max is not None:
            preferences.commute_time_max = preferences_data.commute_time_max

    db.commit()
    db.refresh(preferences)

    return UserPreferencesResponse(
        email_notifications=preferences.email_notifications,
        job_alert_frequency=preferences.job_alert_frequency,
        preferred_job_types=preferences.preferred_job_types,
        salary_range={
            "min": preferences.preferred_salary_min or 0,
            "max": preferences.preferred_salary_max or 10000000
        },
        commute_time_max=preferences.commute_time_max
    )


@router.post("/me/profile-image", response_model=ProfileImageResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload profile image

    Accepts image files (JPEG, PNG) up to 5MB.
    Returns URLs for full image and thumbnail.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are allowed"
        )

    # Validate file size (5MB limit)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )

    # In production, this would upload to cloud storage (S3, GCS, etc.)
    # For now, return mock URLs
    image_id = str(uuid.uuid4())

    return ProfileImageResponse(
        profile_image_url=f"https://storage.example.com/profiles/{current_user.user_id}/{image_id}.jpg",
        thumbnail_url=f"https://storage.example.com/profiles/{current_user.user_id}/{image_id}_thumb.jpg"
    )


# Admin endpoints for user management
@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int,
    current_user: User = Depends(require_self_or_admin(user_id)),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user profile by ID (admin or self access only)
    """
    user_with_profile = await user_service.get_user_profile(user_id)
    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfileResponse(
        user_id=user_with_profile.user_id,
        email=user_with_profile.email,
        name=user_with_profile.name,
        pref_cd=user_with_profile.pref_cd,
        birth_year=user_with_profile.birth_year,
        gender=user_with_profile.gender,
        phone=user_with_profile.phone,
        job_search_status=user_with_profile.job_search_status,
        preferred_industries=user_with_profile.preferred_industries or [],
        skills=user_with_profile.skills or [],
        created_at=user_with_profile.created_at,
        updated_at=user_with_profile.updated_at
    )