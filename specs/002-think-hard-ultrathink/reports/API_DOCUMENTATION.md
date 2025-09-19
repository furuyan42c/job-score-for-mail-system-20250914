# 📡 API Documentation - Mail Score System

> **Status**: Complete | **Version**: v2.0.0 | **API Version**: v1 | **Updated**: September 19, 2025

## 📋 Overview

Complete REST API documentation for the Mail Score System. All **74 tasks (100%) implemented** with comprehensive endpoint coverage, authentication, and real-time features.

**Base URL**: `https://api.mailscore.com/api/v1` (Production)
**Base URL**: `http://localhost:8000/api/v1` (Development)

**Interactive Documentation**:
- Swagger UI: `https://api.mailscore.com/docs`
- ReDoc: `https://api.mailscore.com/redoc`

## 🔑 Authentication

### JWT Token Authentication
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "user",
    "is_active": true
  }
}
```

### Token Usage
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 👤 User Management (T014-T016)

### User Registration
```http
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "secure_password123",
  "full_name": "John Doe",
  "phone": "+81-90-1234-5678",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "address": {
    "prefecture": "Tokyo",
    "city": "Shibuya",
    "address_line": "1-1-1 Example St"
  }
}
```

### Get User Profile
```http
GET /users/me
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+81-90-1234-5678",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "address": {
    "prefecture": "Tokyo",
    "city": "Shibuya",
    "address_line": "1-1-1 Example St",
    "postal_code": "150-0001"
  },
  "preferences": {
    "preferred_job_types": ["part_time", "dispatch"],
    "preferred_industries": ["retail", "food_service"],
    "max_commute_time": 30,
    "min_hourly_wage": 1000,
    "availability": {
      "monday": ["09:00", "17:00"],
      "tuesday": ["09:00", "17:00"]
    }
  },
  "is_active": true,
  "created_at": "2025-09-19T10:00:00Z",
  "updated_at": "2025-09-19T10:30:00Z"
}
```

### Update User Profile
```http
PUT /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Smith",
  "phone": "+81-90-1234-5679",
  "preferences": {
    "preferred_job_types": ["part_time"],
    "max_commute_time": 45,
    "min_hourly_wage": 1200
  }
}
```

### User Preferences
```http
GET /users/me/preferences
PUT /users/me/preferences
Authorization: Bearer {token}
```

## 💼 Job Management (T005-T013)

### List Jobs
```http
GET /jobs?page=1&limit=20&prefecture=Tokyo&job_type=part_time&min_wage=1000
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `prefecture` (string): Filter by prefecture
- `city` (string): Filter by city
- `job_type` (enum): `part_time`, `full_time`, `dispatch`, `contract`
- `industry` (string): Filter by industry
- `min_wage` (int): Minimum hourly wage
- `max_wage` (int): Maximum hourly wage
- `keywords` (string): Search keywords
- `sort` (enum): `created_at`, `wage`, `distance`, `score`
- `order` (enum): `asc`, `desc`

**Response:**
```json
{
  "items": [
    {
      "id": "job-123e4567-e89b-12d3-a456-426614174000",
      "title": "コンビニスタッフ募集",
      "company_name": "ファミリーマート",
      "description": "レジ業務、商品陳列、清掃等",
      "job_type": "part_time",
      "industry": "retail",
      "location": {
        "prefecture": "Tokyo",
        "city": "Shibuya",
        "address": "1-2-3 Example Street",
        "nearest_station": "Shibuya Station",
        "walking_minutes": 5
      },
      "salary": {
        "type": "hourly",
        "amount": 1200,
        "currency": "JPY"
      },
      "work_hours": {
        "start_time": "09:00",
        "end_time": "17:00",
        "break_time": 60,
        "available_shifts": ["morning", "afternoon", "evening"]
      },
      "requirements": {
        "age_min": 18,
        "age_max": 65,
        "experience_required": false,
        "skills": ["customer_service"],
        "languages": ["japanese"]
      },
      "benefits": [
        "社会保険完備",
        "交通費支給",
        "制服貸与"
      ],
      "posted_at": "2025-09-19T08:00:00Z",
      "expires_at": "2025-10-19T23:59:59Z",
      "is_active": true,
      "application_count": 15,
      "view_count": 123
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 20,
  "pages": 63
}
```

### Get Job Details
```http
GET /jobs/{job_id}
Authorization: Bearer {token}
```

### Create Job (Admin/Employer)
```http
POST /jobs
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "title": "新しいアルバイト求人",
  "company_name": "株式会社Example",
  "description": "詳細な仕事内容の説明",
  "job_type": "part_time",
  "industry": "food_service",
  "location": {
    "prefecture": "Tokyo",
    "city": "Shinjuku",
    "address": "1-1-1 Shinjuku Street",
    "nearest_station": "Shinjuku Station",
    "walking_minutes": 3
  },
  "salary": {
    "type": "hourly",
    "amount": 1300,
    "currency": "JPY"
  },
  "work_hours": {
    "start_time": "10:00",
    "end_time": "18:00",
    "break_time": 60
  },
  "requirements": {
    "age_min": 18,
    "experience_required": false
  },
  "expires_at": "2025-11-19T23:59:59Z"
}
```

### Update Job
```http
PUT /jobs/{job_id}
Authorization: Bearer {admin_token}
```

### Delete Job
```http
DELETE /jobs/{job_id}
Authorization: Bearer {admin_token}
```

## 🎯 Matching & Scoring (T021-T026)

### Get Job Matches for User
```http
GET /matching/jobs?user_id={user_id}&limit=40
Authorization: Bearer {token}
```

**Response:**
```json
{
  "matches": [
    {
      "job_id": "job-123",
      "job": {
        "title": "コンビニスタッフ",
        "company_name": "ファミリーマート",
        "location": {
          "prefecture": "Tokyo",
          "city": "Shibuya"
        },
        "salary": {
          "amount": 1200,
          "type": "hourly"
        }
      },
      "scores": {
        "total_score": 85.5,
        "basic_score": 75.0,
        "seo_score": 10.0,
        "personalized_score": 0.5,
        "breakdown": {
          "location_match": 90,
          "salary_match": 85,
          "job_type_match": 100,
          "schedule_match": 70,
          "skill_match": 60,
          "experience_match": 80
        }
      },
      "match_reasons": [
        "勤務地が希望エリア内",
        "時給が希望額以上",
        "希望職種と一致",
        "勤務時間が適合"
      ],
      "distance_km": 2.5,
      "commute_time_minutes": 15,
      "compatibility_percentage": 85,
      "recommended_rank": 1
    }
  ],
  "total_matches": 40,
  "algorithm_version": "v2.1",
  "generated_at": "2025-09-19T10:00:00Z"
}
```

### Get User Matches for Job
```http
GET /matching/users?job_id={job_id}&limit=50
Authorization: Bearer {admin_token}
```

### Calculate Job Score
```http
POST /scoring/calculate
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user-123",
  "job_id": "job-456",
  "scoring_type": "all"
}
```

**Response:**
```json
{
  "user_id": "user-123",
  "job_id": "job-456",
  "scores": {
    "basic_score": 78.5,
    "seo_score": 12.0,
    "personalized_score": 1.2,
    "total_score": 91.7
  },
  "factors": {
    "location_distance_km": 1.8,
    "salary_ratio": 1.15,
    "job_type_match": true,
    "industry_preference": true,
    "schedule_compatibility": 0.85,
    "skill_overlap": 0.7
  },
  "calculated_at": "2025-09-19T10:00:00Z"
}
```

### Bulk Scoring
```http
POST /scoring/bulk
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_ids": ["user-1", "user-2", "user-3"],
  "job_ids": ["job-1", "job-2"],
  "scoring_type": "basic"
}
```

## 📧 Email Management (T027-T033)

### Generate Email Content
```http
POST /emails/generate
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "template_type": "job_recommendation",
  "user_id": "user-123",
  "job_matches": ["job-456", "job-789"],
  "personalization_level": "high"
}
```

**Response:**
```json
{
  "email_id": "email-123e4567",
  "recipient": {
    "user_id": "user-123",
    "email": "user@example.com",
    "name": "田中太郎"
  },
  "content": {
    "subject": "田中さんにピッタリの新着求人3件をご紹介！",
    "html_body": "<html><body>...",
    "text_body": "田中さん\n\n今回は特にあなたにピッタリの求人をご紹介します...",
    "preview_text": "時給1300円〜、駅チカ3分の好条件求人あり"
  },
  "metadata": {
    "template_version": "v2.1",
    "personalization_score": 0.92,
    "generated_at": "2025-09-19T10:00:00Z",
    "job_count": 3,
    "estimated_open_rate": 0.28
  }
}
```

### Send Email
```http
POST /emails/send
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email_id": "email-123e4567",
  "send_immediately": false,
  "scheduled_at": "2025-09-19T14:00:00Z"
}
```

### Email Templates
```http
GET /emails/templates
POST /emails/templates
PUT /emails/templates/{template_id}
DELETE /emails/templates/{template_id}
Authorization: Bearer {admin_token}
```

### Email Preview
```http
GET /emails/{email_id}/preview?format=html
Authorization: Bearer {admin_token}
```

### Email Status
```http
GET /emails/{email_id}/status
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "email_id": "email-123e4567",
  "status": "delivered",
  "sent_at": "2025-09-19T14:00:00Z",
  "delivered_at": "2025-09-19T14:00:15Z",
  "opened_at": "2025-09-19T15:30:22Z",
  "clicked_at": "2025-09-19T15:31:05Z",
  "tracking": {
    "opens": 1,
    "clicks": 2,
    "bounced": false,
    "complained": false
  }
}
```

## 📊 Analytics & KPI (T040-T045)

### Dashboard Overview
```http
GET /analytics/dashboard
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "period": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-19"
  },
  "metrics": {
    "total_users": 8540,
    "new_users_period": 245,
    "total_jobs": 12350,
    "new_jobs_period": 156,
    "total_matches": 45230,
    "matches_period": 2341,
    "emails_sent_period": 1820,
    "email_open_rate": 0.284,
    "email_click_rate": 0.089,
    "application_rate": 0.067
  },
  "trends": {
    "user_growth": 0.029,
    "job_growth": 0.013,
    "match_rate_improvement": 0.045,
    "email_performance": 0.012
  },
  "top_performing": {
    "industries": [
      {"name": "retail", "match_rate": 0.78},
      {"name": "food_service", "match_rate": 0.71}
    ],
    "prefectures": [
      {"name": "Tokyo", "user_count": 3420},
      {"name": "Osaka", "user_count": 1850}
    ]
  }
}
```

### User Analytics
```http
GET /analytics/users?period=30d&group_by=prefecture
Authorization: Bearer {admin_token}
```

### Job Analytics
```http
GET /analytics/jobs?period=7d&group_by=industry
Authorization: Bearer {admin_token}
```

### Matching Analytics
```http
GET /analytics/matching?period=1d&include_scores=true
Authorization: Bearer {admin_token}
```

### Email Analytics
```http
GET /analytics/emails?period=30d&template_id=template-123
Authorization: Bearer {admin_token}
```

## 🔍 Search & Filtering

### Advanced Job Search
```http
POST /search/jobs
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": {
    "keywords": "コンビニ スタッフ",
    "location": {
      "prefecture": "Tokyo",
      "city": "Shibuya",
      "radius_km": 5
    },
    "salary": {
      "min": 1000,
      "max": 2000,
      "type": "hourly"
    },
    "job_types": ["part_time", "dispatch"],
    "industries": ["retail", "food_service"],
    "schedule": {
      "days": ["monday", "tuesday", "wednesday"],
      "start_time": "09:00",
      "end_time": "17:00"
    },
    "requirements": {
      "experience_required": false,
      "age_max": 30
    }
  },
  "sort": {
    "field": "score",
    "order": "desc"
  },
  "page": 1,
  "limit": 20
}
```

### Saved Searches
```http
GET /search/saved
POST /search/saved
PUT /search/saved/{search_id}
DELETE /search/saved/{search_id}
Authorization: Bearer {token}
```

### Search Suggestions
```http
GET /search/suggestions?q=コンビ&type=keywords
Authorization: Bearer {token}
```

## 📱 Real-time Features (T069-T071)

### WebSocket Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.mailscore.com/ws');

// Authentication
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));

// Subscribe to user notifications
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'user_notifications',
  user_id: 'user-123'
}));
```

### WebSocket Events
```json
// New job match notification
{
  "type": "new_match",
  "data": {
    "job_id": "job-456",
    "score": 89.5,
    "title": "コンビニスタッフ募集",
    "company": "ファミリーマート",
    "location": "東京都渋谷区"
  },
  "timestamp": "2025-09-19T10:00:00Z"
}

// Job status update
{
  "type": "job_status_update",
  "data": {
    "job_id": "job-456",
    "status": "filled",
    "message": "この求人の募集は終了しました"
  },
  "timestamp": "2025-09-19T10:00:00Z"
}

// Email delivery status
{
  "type": "email_status",
  "data": {
    "email_id": "email-123",
    "status": "delivered",
    "recipient": "user@example.com"
  },
  "timestamp": "2025-09-19T10:00:00Z"
}
```

### Push Notifications
```http
POST /notifications/send
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "user_id": "user-123",
  "type": "job_match",
  "title": "新しい求人マッチ",
  "body": "あなたにピッタリの求人が見つかりました",
  "data": {
    "job_id": "job-456",
    "action": "view_job"
  },
  "schedule_at": "2025-09-19T14:00:00Z"
}
```

## 🔐 Admin Endpoints

### User Management
```http
GET /admin/users?page=1&limit=50&status=active
POST /admin/users/{user_id}/deactivate
POST /admin/users/{user_id}/activate
PUT /admin/users/{user_id}/role
Authorization: Bearer {admin_token}
```

### Job Management
```http
GET /admin/jobs?status=pending&company=example
POST /admin/jobs/{job_id}/approve
POST /admin/jobs/{job_id}/reject
PUT /admin/jobs/{job_id}/priority
Authorization: Bearer {admin_token}
```

### System Administration
```http
GET /admin/system/health
GET /admin/system/metrics
POST /admin/system/maintenance
GET /admin/system/logs?level=error&limit=100
Authorization: Bearer {admin_token}
```

## 📈 Batch Operations

### Bulk Email Generation
```http
POST /batch/emails/generate
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "campaign_name": "Weekly Job Recommendations",
  "template_type": "job_recommendation",
  "target_users": {
    "criteria": {
      "is_active": true,
      "last_login_days": 7,
      "has_preferences": true
    },
    "exclude_recently_emailed": true
  },
  "job_selection": {
    "max_jobs_per_user": 5,
    "min_score_threshold": 70,
    "include_new_jobs_only": false
  },
  "schedule": {
    "send_at": "2025-09-20T09:00:00Z",
    "timezone": "Asia/Tokyo"
  }
}
```

### Batch Matching
```http
POST /batch/matching/recalculate
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "scope": "all_active_users",
  "job_filters": {
    "posted_since": "2025-09-18T00:00:00Z",
    "is_active": true
  },
  "scoring_type": "all",
  "chunk_size": 100
}
```

## ⚡ Performance & Caching

### Cache Management
```http
GET /cache/stats
DELETE /cache/clear?pattern=user:*
POST /cache/warm?entity=jobs
Authorization: Bearer {admin_token}
```

### Performance Metrics
```http
GET /metrics/performance?endpoint=/jobs&period=1h
Authorization: Bearer {admin_token}
```

## 🔍 SQL Execution (T039)

### Execute SQL Query
```http
POST /sql/execute
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "query": "SELECT COUNT(*) as total_users FROM users WHERE is_active = true",
  "read_only": true,
  "timeout_seconds": 30
}
```

**Response:**
```json
{
  "query_id": "query-123e4567",
  "results": [
    {"total_users": 8540}
  ],
  "execution_time_ms": 45,
  "rows_affected": 1,
  "columns": ["total_users"],
  "executed_at": "2025-09-19T10:00:00Z"
}
```

## 📊 Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1695123600
X-RateLimit-Window: 3600
```

### Rate Limit Tiers
- **Public endpoints**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Premium users**: 5000 requests/hour
- **Admin users**: 10000 requests/hour

## ❌ Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力データに問題があります",
    "details": [
      {
        "field": "email",
        "message": "有効なメールアドレスを入力してください"
      }
    ],
    "request_id": "req-123e4567",
    "timestamp": "2025-09-19T10:00:00Z"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

### Common Error Codes
- `INVALID_TOKEN` - JWT token is invalid or expired
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `VALIDATION_ERROR` - Request data validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED` - Request rate limit exceeded
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable

## 🔧 API Versioning

### Version Header
```http
Accept: application/vnd.mailscore.v2+json
API-Version: v2
```

### Deprecation Notice
```http
Deprecation: true
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Link: </api/v2/users>; rel="successor-version"
```

## 📱 Mobile SDK Support

### iOS SDK
```swift
import MailScoreSDK

let client = MailScoreClient(apiKey: "your-api-key")
client.authenticate(email: "user@example.com", password: "password") { result in
    // Handle authentication result
}
```

### Android SDK
```kotlin
val client = MailScoreClient("your-api-key")
client.authenticate("user@example.com", "password") { result ->
    // Handle authentication result
}
```

## 🧪 Testing Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-19T10:00:00Z",
  "version": "v2.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "email": "healthy",
    "storage": "healthy"
  },
  "uptime_seconds": 1234567
}
```

### API Status
```http
GET /status
```

### Test Data
```http
POST /test/seed-data
DELETE /test/clear-data
Authorization: Bearer {test_token}
```

---

## 📚 Integration Examples

### Python Integration
```python
import requests

class MailScoreAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def get_job_matches(self, user_id, limit=20):
        response = requests.get(
            f'{self.base_url}/matching/jobs',
            params={'user_id': user_id, 'limit': limit},
            headers=self.headers
        )
        return response.json()

    def create_job(self, job_data):
        response = requests.post(
            f'{self.base_url}/jobs',
            json=job_data,
            headers=self.headers
        )
        return response.json()

# Usage
api = MailScoreAPI('https://api.mailscore.com/api/v1', 'your-token')
matches = api.get_job_matches('user-123')
```

### JavaScript Integration
```javascript
class MailScoreAPI {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  async getJobMatches(userId, limit = 20) {
    const response = await fetch(
      `${this.baseUrl}/matching/jobs?user_id=${userId}&limit=${limit}`,
      { headers: this.headers }
    );
    return await response.json();
  }

  async createJob(jobData) {
    const response = await fetch(`${this.baseUrl}/jobs`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(jobData)
    });
    return await response.json();
  }
}

// Usage
const api = new MailScoreAPI('https://api.mailscore.com/api/v1', 'your-token');
const matches = await api.getJobMatches('user-123');
```

---

## 📞 Support

### API Support
- **Documentation**: https://api.mailscore.com/docs
- **Status Page**: https://status.mailscore.com
- **Support Email**: api-support@mailscore.com
- **Discord**: https://discord.gg/mailscore

### SLA & Availability
- **Uptime**: 99.9% guaranteed
- **Response Time**: <100ms average
- **Support Response**: <24 hours

---

*This API documentation covers all 74 implemented features with comprehensive examples and integration guides.*
*Last updated: September 19, 2025 | API Version: v2.0.0*