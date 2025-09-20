"""
Security utilities for user authentication
Implements secure password hashing using bcrypt and JWT token management
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


# Alias for compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in token

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify JWT token

    Args:
        token: JWT token to decode

    Returns:
        Token payload

    Raises:
        JWTError: If token is invalid
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# Alias for compatibility
def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token to verify

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired

    Args:
        token: JWT token to check

    Returns:
        True if token is expired, False otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if exp:
            return datetime.utcnow() > datetime.fromtimestamp(exp)
        return True
    except JWTError:
        return True


async def verify_api_key(token: str, db) -> Optional[Any]:
    """
    Verify API key and return associated user

    Args:
        token: API key token
        db: Database session

    Returns:
        User if valid, None otherwise
    """
    from sqlalchemy import select

    from app.models.user import User

    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            return None

        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except Exception:
        return None


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed results

    Args:
        password: Password to validate

    Returns:
        Dictionary with validation results
    """
    errors = []
    score = 0

    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    else:
        score += 1

    # Uppercase check
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    else:
        score += 1

    # Lowercase check
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    else:
        score += 1

    # Digit check
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    else:
        score += 1

    # Special character check
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")
    else:
        score += 1

    # Strength rating
    if score < 3:
        strength = "weak"
    elif score < 5:
        strength = "medium"
    else:
        strength = "strong"

    return {"valid": len(errors) == 0, "errors": errors, "score": score, "strength": strength}
