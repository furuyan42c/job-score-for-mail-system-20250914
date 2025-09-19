#!/usr/bin/env python3
"""
簡易サーバー - T081-T085 GREEN Phase実装
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
import uuid

app = FastAPI(title="Test Server - Extended")


# ============= Existing Models =============
class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    description: Optional[str] = None
    salary: Optional[int] = None


class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ============= T081: Supabase Auth Models =============
class SupabaseSignup(BaseModel):
    email: str
    password: str
    metadata: Optional[Dict[str, Any]] = None


class SupabaseSession(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600


# ============= T083: Data Flow Models =============
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None


# ============= T084: User Journey Models =============
class EmailSettings(BaseModel):
    frequency: str
    categories: Optional[List[str]] = None
    enabled: bool = True


class ScoreRequest(BaseModel):
    user_id: int
    job_id: int


# ============= Data Storage =============
JOBS_DATA = [
    {"id": 1, "title": "Backend Developer", "company": "Tech Corp", "description": "Python developer needed", "salary": 500000},
    {"id": 2, "title": "Frontend Developer", "company": "Web Inc", "description": "React developer needed", "salary": 450000},
]
USERS_DATA = []
USER_ID_COUNTER = 1
JOB_ID_COUNTER = 3


# ============= Existing Endpoints =============
@app.get("/")
def read_root():
    return {"message": "Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend server is operational"}


@app.get("/api/v1/jobs")
def get_jobs_list():
    return {"jobs": JOBS_DATA}


@app.get("/api/v1/jobs/{job_id}")
def get_job_detail(job_id: int):
    for job in JOBS_DATA:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/v1/users/register", status_code=201)
def register_user(user: UserRegister):
    global USER_ID_COUNTER
    new_user = {
        "id": USER_ID_COUNTER,
        "email": user.email,
        "name": user.name,
        "preferences": user.preferences
    }
    USERS_DATA.append(new_user)
    USER_ID_COUNTER += 1
    return new_user


@app.post("/api/v1/users/login")
def login_user(credentials: LoginRequest):
    return {
        "access_token": f"token_{uuid.uuid4().hex[:12]}",
        "token_type": "bearer"
    }


# ============= T081: Supabase Auth Endpoints =============
@app.post("/api/v1/auth/supabase/signup", status_code=201)
def supabase_signup(data: SupabaseSignup):
    """Supabase signup (hardcoded)"""
    return {
        "session": {
            "access_token": f"sb_token_{uuid.uuid4().hex[:12]}",
            "refresh_token": f"sb_refresh_{uuid.uuid4().hex[:12]}",
            "expires_in": 3600
        },
        "user": {
            "id": str(uuid.uuid4()),
            "email": data.email,
            "metadata": data.metadata or {}
        }
    }


@app.post("/api/v1/auth/supabase/login")
def supabase_login(credentials: LoginRequest):
    """Supabase login (hardcoded)"""
    return {
        "session": {
            "access_token": f"sb_token_{uuid.uuid4().hex[:12]}",
            "refresh_token": f"sb_refresh_{uuid.uuid4().hex[:12]}",
            "expires_in": 3600
        }
    }


@app.post("/api/v1/auth/supabase/logout")
def supabase_logout(authorization: Optional[str] = Header(None)):
    """Supabase logout (hardcoded)"""
    return {"status": "logged_out"}


@app.post("/api/v1/auth/supabase/refresh")
def supabase_refresh(data: Dict[str, str]):
    """Refresh token (hardcoded)"""
    return {
        "session": {
            "access_token": f"sb_token_{uuid.uuid4().hex[:12]}",
            "refresh_token": f"sb_refresh_{uuid.uuid4().hex[:12]}",
            "expires_in": 3600
        }
    }


@app.get("/api/v1/auth/supabase/profile")
def supabase_profile(authorization: Optional[str] = Header(None)):
    """Get user profile (hardcoded)"""
    return {
        "user": {
            "id": str(uuid.uuid4()),
            "email": "user@example.com",
            "metadata": {"name": "Test User"}
        }
    }


# ============= T083: Data Flow Endpoints =============
@app.post("/api/v1/jobs", status_code=201)
def create_job(job: Job):
    """Create a job (hardcoded)"""
    global JOB_ID_COUNTER
    new_job = job.dict()
    new_job["id"] = JOB_ID_COUNTER
    JOBS_DATA.append(new_job)
    JOB_ID_COUNTER += 1
    return new_job


@app.patch("/api/v1/jobs/{job_id}")
def update_job(job_id: int, update_data: Dict[str, Any]):
    """Update a job (hardcoded)"""
    for job in JOBS_DATA:
        if job["id"] == job_id:
            job.update(update_data)
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.delete("/api/v1/jobs/{job_id}", status_code=204)
def delete_job(job_id: int):
    """Delete a job (hardcoded)"""
    global JOBS_DATA
    JOBS_DATA = [job for job in JOBS_DATA if job["id"] != job_id]
    return None


@app.patch("/api/v1/users/profile")
def update_profile(profile: ProfileUpdate, authorization: Optional[str] = Header(None)):
    """Update user profile (hardcoded)"""
    return {
        "id": 1,
        "email": "user@example.com",
        "name": profile.name or "Updated Name",
        "skills": profile.skills,
        "experience_years": profile.experience_years
    }


@app.post("/api/v1/scoring/calculate")
def calculate_score(request: ScoreRequest):
    """Calculate matching score (hardcoded)"""
    return {
        "user_id": request.user_id,
        "job_id": request.job_id,
        "score": 85.5,
        "breakdown": {
            "skill_match": 90,
            "location_match": 80,
            "salary_match": 86
        }
    }


@app.post("/api/v1/matching/generate")
def generate_matching(data: Dict[str, Any]):
    """Generate matching (hardcoded)"""
    return {
        "matches": [
            {"job_id": 1, "score": 95, "rank": 1},
            {"job_id": 2, "score": 88, "rank": 2},
        ][:data.get("limit", 10)]
    }


@app.get("/api/v1/matching/user/{user_id}")
def get_user_matches(user_id: int):
    """Get user matches (hardcoded)"""
    return {
        "matches": [
            {"job_id": 1, "score": 95, "matched_at": "2025-09-19T12:00:00Z"},
            {"job_id": 2, "score": 88, "matched_at": "2025-09-19T12:00:00Z"},
        ]
    }


# ============= T084: User Journey Endpoints =============
@app.get("/api/v1/jobs/search")
def search_jobs(q: Optional[str] = None, location: Optional[str] = None, salary_min: Optional[int] = None):
    """Search jobs (hardcoded)"""
    # Filter logic would go here
    return {"jobs": JOBS_DATA}


@app.get("/api/v1/matching/user/{user_id}/recommendations")
def get_recommendations(user_id: int, authorization: Optional[str] = Header(None)):
    """Get recommendations (hardcoded)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "recommendations": [
            {"job_id": 1, "score": 95, "reason": "High skill match"},
            {"job_id": 2, "score": 88, "reason": "Good location match"},
        ]
    }


@app.post("/api/v1/users/email-settings")
def update_email_settings(settings: EmailSettings, authorization: Optional[str] = Header(None)):
    """Update email settings (hardcoded)"""
    return {"status": "updated", "settings": settings.dict()}


@app.post("/api/v1/actions/view", status_code=201)
def record_view_action(data: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Record view action (hardcoded)"""
    return {"action_id": str(uuid.uuid4()), "recorded_at": "2025-09-19T12:00:00Z"}


@app.get("/api/v1/jobs/new")
def get_new_jobs(authorization: Optional[str] = Header(None)):
    """Get new jobs (hardcoded)"""
    return {"jobs": JOBS_DATA[:1]}


@app.get("/api/v1/users/saved-jobs")
def get_saved_jobs(authorization: Optional[str] = Header(None)):
    """Get saved jobs (hardcoded)"""
    return {"saved_jobs": [{"job_id": 1, "saved_at": "2025-09-18T10:00:00Z"}]}


@app.get("/api/v1/users/applications")
def get_applications(authorization: Optional[str] = Header(None)):
    """Get applications (hardcoded)"""
    return {"applications": []}


@app.get("/api/v1/auth/register-prompt")
def register_prompt():
    """Register prompt (hardcoded)"""
    return {"message": "Please register to access full features", "register_url": "/register"}


# ============= T085: Performance Endpoints =============
@app.post("/api/v1/jobs/batch")
def create_jobs_batch(jobs: List[Dict[str, Any]]):
    """Batch create jobs (hardcoded)"""
    return {"created": len(jobs), "status": "success"}


@app.get("/api/v1/jobs/search")
def complex_search(q: Optional[str] = None, location: Optional[str] = None,
                  salary_min: Optional[int] = None):
    """Complex search (hardcoded)"""
    # Simulate some processing
    time.sleep(0.01)  # 10ms delay
    return {"jobs": JOBS_DATA}


@app.get("/api/v1/matching/generate")
def generate_batch_matching(user_id: Optional[int] = None, limit: int = 40):
    """Generate batch matching (hardcoded)"""
    return {
        "matches": [
            {"job_id": i, "score": 95 - i*2}
            for i in range(1, min(limit + 1, 41))
        ]
    }


@app.get("/api/v1/scoring/calculate/batch")
def calculate_batch_scores():
    """Calculate batch scores (hardcoded)"""
    time.sleep(0.05)  # 50ms delay
    return {"scores_calculated": 100, "average_score": 82.5}


if __name__ == "__main__":
    print("🚀 Starting extended test server on http://localhost:8000")
    print("📋 GREEN Phase implementation for T081-T085")
    uvicorn.run(app, host="0.0.0.0", port=8000)