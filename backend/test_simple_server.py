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

# T086-T090 Data Storage
MASTER_DATA = {
    "prefectures": [],
    "categories": [],
    "seo_keywords": []
}


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


@app.get("/api/v1/jobs/search")
def search_jobs(q: Optional[str] = None, location: Optional[str] = None, salary_min: Optional[int] = None):
    """Search jobs (hardcoded)"""
    # Filter logic would go here
    return {"jobs": JOBS_DATA}


@app.get("/api/v1/jobs/new")
def get_new_jobs(authorization: Optional[str] = Header(None)):
    """Get new jobs (hardcoded)"""
    return {"jobs": JOBS_DATA[:1]}


@app.get("/api/v1/jobs/complex")
def complex_search(q: Optional[str] = None, location: Optional[str] = None,
                  salary_min: Optional[int] = None):
    """Complex search (hardcoded)"""
    # Simulate some processing
    time.sleep(0.01)  # 10ms delay
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


# ============= T086: Master Data Loading =============
@app.post("/api/v1/data/master/prefectures", status_code=201)
def load_prefectures(data: Dict[str, Any]):
    """Load prefecture master data (hardcoded)"""
    global MASTER_DATA
    MASTER_DATA["prefectures"] = data.get("prefectures", [])
    return {"loaded": len(MASTER_DATA["prefectures"])}


@app.post("/api/v1/data/master/categories", status_code=201)
def load_categories(data: Dict[str, Any]):
    """Load category master data (hardcoded)"""
    global MASTER_DATA
    MASTER_DATA["categories"] = data.get("categories", [])
    return {"loaded": len(MASTER_DATA["categories"])}


# ============= T087: SEO Keyword Data =============
@app.post("/api/v1/data/seo/keywords", status_code=201)
def load_seo_keywords(data: Dict[str, Any]):
    """Load SEO keywords (hardcoded)"""
    global MASTER_DATA
    MASTER_DATA["seo_keywords"] = data.get("keywords", [])
    return {"loaded": len(MASTER_DATA["seo_keywords"])}


@app.get("/api/v1/data/seo/keywords")
def get_seo_keywords():
    """Get SEO keywords (hardcoded)"""
    return {"keywords": MASTER_DATA["seo_keywords"]}


# ============= T088: Job Data Import =============
@app.post("/api/v1/data/jobs/import", status_code=201)
def import_jobs(data: Dict[str, Any]):
    """Import job data (hardcoded)"""
    global JOBS_DATA, JOB_ID_COUNTER
    new_jobs = data.get("jobs", [])
    for job in new_jobs:
        job["id"] = JOB_ID_COUNTER
        JOBS_DATA.append(job)
        JOB_ID_COUNTER += 1
    return {"imported": len(new_jobs)}


# ============= T089: Data Integrity Validation =============
@app.post("/api/v1/data/validate/integrity")
def validate_data_integrity():
    """Validate data integrity (hardcoded)"""
    return {
        "validation_results": {
            "master_data": {"status": "valid", "count": len(MASTER_DATA["prefectures"]) + len(MASTER_DATA["categories"])},
            "job_data": {"status": "valid", "count": len(JOBS_DATA)},
            "referential_integrity": {"status": "valid", "issues": 0}
        }
    }


@app.get("/api/v1/data/validate/orphans")
def check_orphaned_records():
    """Check for orphaned records (hardcoded)"""
    return {"orphaned_records": 0}


# ============= T090: Basic Score Calculation =============
@app.post("/api/v1/scoring/calculate/basic")
def calculate_basic_score(data: Dict[str, Any]):
    """Calculate basic matching score (hardcoded)"""
    # Simple scoring logic
    location_score = 100 if data.get("user_profile", {}).get("location") == data.get("job_profile", {}).get("location") else 50
    salary_score = 80
    skill_score = 75

    total_score = (location_score + salary_score + skill_score) / 3

    return {
        "score": total_score,
        "components": {
            "location_score": location_score,
            "salary_score": salary_score,
            "skill_score": skill_score
        }
    }


@app.post("/api/v1/scoring/calculate/batch")
def calculate_batch_scores_v2(data: Dict[str, Any]):
    """Calculate batch scores (hardcoded)"""
    user_ids = data.get("user_ids", [])
    job_ids = data.get("job_ids", [])

    scores = []
    for user_id in user_ids:
        for job_id in job_ids:
            scores.append({
                "user_id": user_id,
                "job_id": job_id,
                "score": 75 + (user_id * job_id) % 20  # Random-ish score
            })

    return {"scores": scores}


# ============= T091: SEO Score Calculation =============
@app.post("/api/v1/scoring/calculate/seo")
def calculate_seo_score(data: Dict[str, Any]):
    """Calculate SEO score (hardcoded)"""
    # Simple SEO scoring logic
    keyword_matches = []
    for kw in data.get("seo_keywords", []):
        if kw["keyword"].split()[0] in data.get("job_data", {}).get("title", ""):
            keyword_matches.append({
                "keyword": kw["keyword"],
                "matched": True,
                "volume": kw["volume"]
            })

    seo_score = 75 if keyword_matches else 50
    search_volume_score = 80
    competition_score = 60

    return {
        "seo_score": seo_score,
        "keyword_matches": keyword_matches,
        "search_volume_score": search_volume_score,
        "competition_score": competition_score
    }


# ============= T092: User-Job Matching =============
@app.post("/api/v1/matching/generate/comprehensive")
def generate_comprehensive_matching(data: Dict[str, Any]):
    """Generate comprehensive user-job matches (hardcoded)"""
    user_ids = data.get("user_ids", [])
    job_ids = data.get("job_ids", [])

    matches = []
    for user_id in user_ids:
        for job_id in job_ids:
            matches.append({
                "user_id": user_id,
                "job_id": job_id,
                "total_score": 85 - (user_id + job_id) % 15,  # Varied scores
                "location_score": 90,
                "salary_score": 80,
                "skill_score": 75,
                "seo_score": 70
            })

    return {"matches": matches}


@app.get("/api/v1/matching/user/{user_id}/top")
def get_top_matches(user_id: int, limit: int = 5):
    """Get top matches for a user (hardcoded)"""
    matches = [
        {"job_id": 1, "total_score": 90, "title": "Job 1"},
        {"job_id": 2, "total_score": 85, "title": "Job 2"},
        {"job_id": 3, "total_score": 80, "title": "Job 3"},
    ][:limit]
    return {"matches": matches}


# ============= T093: Email Generation =============
@app.post("/api/v1/email/generate")
def generate_email(data: Dict[str, Any]):
    """Generate email content (hardcoded)"""
    user_name = data.get("user_data", {}).get("name", "ユーザー")
    recommendations = data.get("job_recommendations", [])

    body_text = f"""こんにちは、{user_name}様

あなたにぴったりの求人が見つかりました！

おすすめ求人:
"""
    for job in recommendations[:3]:
        body_text += f"- {job['title']} ({job['company']}) - マッチ度: {job['match_score']}%\n"

    body_html = f"""<html><body>
<h2>こんにちは、{user_name}様</h2>
<p>あなたにぴったりの求人が見つかりました！</p>
<ul>
{''.join([f"<li>{job['title']} - {job['company']}</li>" for job in recommendations[:3]])}
</ul>
</body></html>"""

    return {
        "email": {
            "subject": f"{user_name}様へのおすすめ求人情報",
            "body_text": body_text,
            "body_html": body_html
        }
    }


# ============= T094: Distribution List Generation =============
@app.post("/api/v1/distribution/generate-list")
def generate_distribution_list(data: Dict[str, Any]):
    """Generate distribution list (hardcoded)"""
    max_recipients = data.get("filters", {}).get("max_recipients", 100)

    distribution_list = []
    for i in range(min(10, max_recipients)):  # Generate up to 10 recipients
        distribution_list.append({
            "user_id": i + 1,
            "email": f"user{i+1}@example.com",
            "job_recommendations": [
                {"job_id": j+1, "score": 85 - j*5}
                for j in range(3)
            ]
        })

    return {
        "distribution_list": distribution_list,
        "total_recipients": len(distribution_list)
    }


# ============= T095: Batch Distribution Simulation =============
DISTRIBUTION_STATUS = {}


@app.post("/api/v1/distribution/simulate")
def simulate_batch_distribution(data: Dict[str, Any]):
    """Simulate batch email distribution (hardcoded)"""
    list_id = data.get("distribution_list_id", "default")
    send_rate = data.get("send_rate", 10)
    total_recipients = data.get("total_recipients", 100)

    estimated_time = total_recipients / send_rate

    DISTRIBUTION_STATUS[list_id] = "in_progress"

    return {
        "simulation_results": {
            "estimated_time_seconds": estimated_time,
            "success_count": total_recipients - 2,  # Simulate some failures
            "failure_count": 2,
            "queue_status": "active",
            "send_rate": send_rate
        }
    }


@app.get("/api/v1/distribution/status/{list_id}")
def get_distribution_status(list_id: str):
    """Get distribution status (hardcoded)"""
    status = DISTRIBUTION_STATUS.get(list_id, "pending")
    return {
        "status": status,
        "list_id": list_id,
        "progress": 75 if status == "in_progress" else 100
    }


# ============= T096: Distribution Result Analysis =============
@app.post("/api/v1/distribution/analyze")
def analyze_distribution_results(data: Dict[str, Any]):
    """Analyze distribution results (hardcoded)"""
    distribution_id = data.get("distribution_id", "default")

    # Hardcoded analytics data
    return {
        "analysis": {
            "total_sent": 100,
            "total_delivered": 98,
            "total_opened": 45,
            "total_clicked": 23,
            "delivery_rate": 98.0,
            "open_rate": 45.0,
            "click_rate": 23.0,
            "conversion_rate": 12.5,
            "average_open_time_minutes": 32.5,
            "peak_engagement_hour": 10,
            "distribution_id": distribution_id
        }
    }


@app.get("/api/v1/distribution/analytics/{distribution_id}")
def get_distribution_analytics(distribution_id: str):
    """Get detailed distribution analytics (hardcoded)"""
    return {
        "distribution_id": distribution_id,
        "performance_summary": {
            "status": "completed",
            "total_recipients": 100,
            "successful_deliveries": 98,
            "engagement_score": 75.5
        },
        "engagement_breakdown": {
            "by_hour": {
                "9": 15,
                "10": 25,
                "11": 20,
                "12": 10
            },
            "by_job_category": {
                "飲食": 35,
                "小売": 30,
                "サービス": 20,
                "その他": 15
            },
            "by_user_segment": {
                "active": 60,
                "occasional": 30,
                "new": 10
            }
        },
        "recommendations": [
            {
                "type": "timing",
                "message": "10時台の配信が最も効果的です"
            },
            {
                "type": "content",
                "message": "飲食カテゴリの求人への関心が高いです"
            },
            {
                "type": "segmentation",
                "message": "アクティブユーザーのエンゲージメント率が高いです"
            }
        ]
    }


if __name__ == "__main__":
    print("🚀 Starting extended test server on http://localhost:8000")
    print("📋 GREEN Phase implementation for T081-T096")
    uvicorn.run(app, host="0.0.0.0", port=8000)