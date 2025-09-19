#!/usr/bin/env python3
"""
簡易サーバー起動テスト
T080 GREEN Phase - 最小実装でテストをパス
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Test Server")


# Pydantic models
class Job(BaseModel):
    id: int
    title: str
    company: str
    description: Optional[str] = None


class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Hardcoded data for GREEN phase
JOBS_DATA = [
    {"id": 1, "title": "Backend Developer", "company": "Tech Corp", "description": "Python developer needed"},
    {"id": 2, "title": "Frontend Developer", "company": "Web Inc", "description": "React developer needed"},
]

USERS_DATA = []
USER_ID_COUNTER = 1


@app.get("/")
def read_root():
    return {"message": "Backend is running"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Backend server is operational"
    }


@app.get("/api/v1/jobs")
def get_jobs_list():
    """求人一覧取得（ハードコード実装）"""
    return {
        "jobs": JOBS_DATA
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job_detail(job_id: int):
    """求人詳細取得（ハードコード実装）"""
    for job in JOBS_DATA:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/v1/users/register", status_code=201)
def register_user(user: UserRegister):
    """ユーザー登録（ハードコード実装）"""
    global USER_ID_COUNTER
    new_user = {
        "id": USER_ID_COUNTER,
        "email": user.email,
        "name": user.name
    }
    USERS_DATA.append(new_user)
    USER_ID_COUNTER += 1
    return new_user


@app.post("/api/v1/users/login")
def login_user(credentials: LoginRequest):
    """ユーザーログイン（ハードコード実装）"""
    # ハードコードで成功を返す
    return {
        "access_token": "fake_token_123456789",
        "token_type": "bearer"
    }

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8000")
    print("📋 Available endpoints:")
    print("   GET / - Root endpoint")
    print("   GET /health - Health check")
    uvicorn.run(app, host="0.0.0.0", port=8000)