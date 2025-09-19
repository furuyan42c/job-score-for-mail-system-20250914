"""
User service for managing user operations
Handles user registration, authentication, profile management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, validate_password_strength
from app.core.auth import token_blacklist
from app.models.database import User, UserProfile
from app.schemas.users import UserRegistrationRequest, UserProfileUpdateRequest


class UserService:
    """Service class for user management operations"""

    def __init__(self, db: Session):
        self.db = db

    async def register_user(self, user_data: UserRegistrationRequest) -> User:
        """
        Register a new user with secure password hashing

        Args:
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Validate password strength
        password_validation = validate_password_strength(user_data.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user object
        user = User(
            email=user_data.email.lower(),
            password_hash=hashed_password,
            name=user_data.name,
            pref_cd=user_data.pref_cd,
            birth_year=user_data.birth_year,
            gender=user_data.gender,
            phone=user_data.phone,
            job_search_status=user_data.job_search_status,
            preferred_industries=user_data.preferred_industries or [],
            skills=user_data.skills or [],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # Create user profile
            profile = UserProfile(
                user_id=user.user_id,
                preference_scores={},
                category_interests={},
                location_preference_radius=10,
                preferred_areas=[],
                application_count=0,
                click_count=0,
                latent_factors=[],
                created_at=datetime.utcnow()
            )

            self.db.add(profile)
            self.db.commit()

            return user

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login_date = datetime.utcnow()
        self.db.commit()

        return user

    async def create_user_tokens(self, user: User) -> Dict[str, Any]:
        """
        Create access and refresh tokens for user

        Args:
            user: User object

        Returns:
            Dictionary with tokens and user info
        """
        # Create token data
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "name": user.name
        }

        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name
            }
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Create new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new access token

        Raises:
            HTTPException: If refresh token is invalid
        """
        from app.core.auth import validate_token_type, extract_user_id_from_token

        # Validate token type
        if not validate_token_type(refresh_token, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Extract user ID
        user_id = extract_user_id_from_token(refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "name": user.name
        }

        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "expires_in": 3600
        }

    async def logout_user(self, access_token: str) -> Dict[str, str]:
        """
        Logout user by blacklisting token

        Args:
            access_token: User's access token

        Returns:
            Success message
        """
        # Add token to blacklist
        token_blacklist.add_token(access_token)

        return {"message": "Successfully logged out"}

    async def get_user_profile(self, user_id: int) -> Optional[User]:
        """
        Get user profile by ID

        Args:
            user_id: User ID

        Returns:
            User object with profile data
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None

        # Load profile data
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        user.profile = profile

        return user

    async def update_user_profile(self, user_id: int, update_data: UserProfileUpdateRequest) -> User:
        """
        Update user profile

        Args:
            user_id: User ID
            update_data: Profile update data

        Returns:
            Updated user object

        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.pref_cd is not None:
            user.pref_cd = update_data.pref_cd
        if update_data.birth_year is not None:
            user.birth_year = update_data.birth_year
        if update_data.gender is not None:
            user.gender = update_data.gender
        if update_data.phone is not None:
            user.phone = update_data.phone
        if update_data.job_search_status is not None:
            user.job_search_status = update_data.job_search_status
        if update_data.preferred_industries is not None:
            user.preferred_industries = update_data.preferred_industries
        if update_data.skills is not None:
            user.skills = update_data.skills

        user.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, str]:
        """
        Change user password

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Success message

        Raises:
            HTTPException: If current password is wrong or new password is invalid
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect current password"
            )

        # Validate new password
        password_validation = validate_password_strength(new_password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "New password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )

        # Update password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()

        self.db.commit()

        return {"message": "Password changed successfully"}

    async def delete_user_account(self, user_id: int, password: str) -> Dict[str, str]:
        """
        Delete user account (soft delete)

        Args:
            user_id: User ID
            password: User password for confirmation

        Returns:
            Success message

        Raises:
            HTTPException: If password is wrong
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        # Soft delete (deactivate)
        user.is_active = False
        user.updated_at = datetime.utcnow()

        self.db.commit()

        return {"message": "Account has been successfully deleted"}

    async def search_users(self, filters: Dict[str, Any], page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        Search users with filters

        Args:
            filters: Search filters
            page: Page number
            size: Page size

        Returns:
            Dictionary with users and pagination info
        """
        query = self.db.query(User)

        # Apply filters
        if filters.get("email"):
            query = query.filter(User.email.ilike(f"%{filters['email']}%"))

        if filters.get("is_active") is not None:
            query = query.filter(User.is_active == filters["is_active"])

        if filters.get("prefecture_codes"):
            query = query.filter(User.pref_cd.in_(filters["prefecture_codes"]))

        # Pagination
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()

        return {
            "items": users,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }