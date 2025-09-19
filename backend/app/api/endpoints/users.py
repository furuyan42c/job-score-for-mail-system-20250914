"""
T008: Users CRUD Endpoints - GREEN Phase Implementation
Minimal implementation following TDD principles
"""
from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

router = APIRouter()

# In-memory storage for TDD GREEN phase
_users_storage: Dict[int, Dict[str, Any]] = {}
_next_user_id = 1


# Minimal Pydantic models for Users
class UserCreateRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    name: str = Field(..., min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=16, le=100)
    location: Optional[str] = Field(None, max_length=100)
    skills: Optional[List[str]] = None

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('有効なメールアドレスを入力してください')
        return v.lower().strip()


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=16, le=100)
    location: Optional[str] = Field(None, max_length=100)
    skills: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    age: Optional[int] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    created_at: str
    updated_at: str
    status: str = "active"


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# =============================================================================
# T008: Users CRUD Endpoints
# =============================================================================

@router.post("/create", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreateRequest) -> UserResponse:
    """T008: Create a new user"""
    global _next_user_id

    # Check if email already exists
    for user in _users_storage.values():
        if user.get("email") == user_data.email and user.get("status") != "deleted":
            raise HTTPException(
                status_code=400,
                detail="このメールアドレスは既に使用されています"
            )

    user_id = _next_user_id
    _next_user_id += 1

    current_time = datetime.utcnow().isoformat()

    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name.strip(),
        "age": user_data.age,
        "location": user_data.location,
        "skills": user_data.skills or [],
        "created_at": current_time,
        "updated_at": current_time,
        "status": "active"
    }

    _users_storage[user_id] = user
    return UserResponse(**user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int = Path(..., gt=0)) -> UserResponse:
    """T008: Get user by ID"""
    if user_id not in _users_storage:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")

    user = _users_storage[user_id]
    if user.get("status") == "deleted":
        raise HTTPException(status_code=404, detail="ユーザーは削除されています")

    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int = Path(..., gt=0),
    user_data: UserUpdateRequest = ...
) -> UserResponse:
    """T008: Update user by ID"""
    if user_id not in _users_storage:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")

    user = _users_storage[user_id].copy()
    if user.get("status") == "deleted":
        raise HTTPException(status_code=404, detail="削除されたユーザーは更新できません")

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        user[field] = value

    user["updated_at"] = datetime.utcnow().isoformat()
    _users_storage[user_id] = user

    return UserResponse(**user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int = Path(..., gt=0)) -> None:
    """T008: Delete user by ID"""
    if user_id not in _users_storage:
        raise HTTPException(status_code=404, detail=f"ユーザーID {user_id} が見つかりません")

    user = _users_storage[user_id]
    if user.get("status") == "deleted":
        raise HTTPException(status_code=404, detail="ユーザーは既に削除されています")

    user["status"] = "deleted"
    user["deleted_at"] = datetime.utcnow().isoformat()
    user["updated_at"] = datetime.utcnow().isoformat()
    _users_storage[user_id] = user


@router.get("", response_model=UserListResponse)
async def list_users(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str = Query(default="active")
) -> UserListResponse:
    """T008: List users with pagination"""
    filtered_users = [
        user for user in _users_storage.values()
        if user.get("status", "active") == status
    ]

    total = len(filtered_users)
    sorted_users = sorted(filtered_users, key=lambda x: x.get("updated_at", ""), reverse=True)

    start = offset
    end = offset + limit
    paginated_users = sorted_users[start:end]

    page = (offset // limit) + 1
    has_next = end < total
    has_prev = offset > 0

    return UserListResponse(
        users=[UserResponse(**user) for user in paginated_users],
        total=total,
        page=page,
        per_page=limit,
        has_next=has_next,
        has_prev=has_prev
    )