"""
T009-T013: Additional API Endpoints - TDD Implementation
- T009: CSV Import endpoint
- T010: Scoring endpoint
- T011: Matching endpoint
- T012: Email sending endpoint
- T013: Batch operations endpoint
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import csv
import io

router = APIRouter()

# In-memory storage for all endpoints
_csv_imports: Dict[int, Dict[str, Any]] = {}
_scores: Dict[int, Dict[str, Any]] = {}
_matches: Dict[int, Dict[str, Any]] = {}
_emails: Dict[int, Dict[str, Any]] = {}
_batch_operations: Dict[int, Dict[str, Any]] = {}
_next_import_id = 1
_next_score_id = 1
_next_match_id = 1
_next_email_id = 1
_next_batch_id = 1


# =============================================================================
# T009: CSV Import Endpoint Models and Functions
# =============================================================================

class CSVImportResponse(BaseModel):
    import_id: int
    filename: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    status: str
    created_at: str


@router.post("/csv/import", response_model=CSVImportResponse)
async def import_csv(file: UploadFile = File(...)):
    """T009: Import CSV file and process data"""
    global _next_import_id

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")

    try:
        content = await file.read()
        csv_data = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        rows = list(csv_reader)
        total_rows = len(rows)
        processed_rows = total_rows  # Simplified for TDD
        failed_rows = 0

        import_id = _next_import_id
        _next_import_id += 1

        import_record = {
            "import_id": import_id,
            "filename": file.filename,
            "total_rows": total_rows,
            "processed_rows": processed_rows,
            "failed_rows": failed_rows,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "data": rows[:100]  # Store first 100 rows for demo
        }

        _csv_imports[import_id] = import_record
        return CSVImportResponse(**import_record)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV処理中にエラーが発生しました: {str(e)}")


@router.get("/csv/import/{import_id}", response_model=CSVImportResponse)
async def get_csv_import_status(import_id: int):
    """T009: Get CSV import status"""
    if import_id not in _csv_imports:
        raise HTTPException(status_code=404, detail="インポートが見つかりません")

    import_record = _csv_imports[import_id]
    return CSVImportResponse(**import_record)


# =============================================================================
# T010: Scoring Endpoint Models and Functions
# =============================================================================

class ScoreRequest(BaseModel):
    user_id: int
    job_id: int
    criteria: Optional[Dict[str, Any]] = None


class ScoreResponse(BaseModel):
    score_id: int
    user_id: int
    job_id: int
    score: float
    breakdown: Dict[str, float]
    created_at: str


@router.post("/scoring/calculate", response_model=ScoreResponse)
async def calculate_score(score_request: ScoreRequest):
    """T010: Calculate job matching score"""
    global _next_score_id

    # Simplified scoring algorithm for TDD
    base_score = 75.0
    breakdown = {
        "location_match": 20.0,
        "salary_match": 25.0,
        "skills_match": 15.0,
        "experience_match": 15.0
    }

    total_score = sum(breakdown.values())

    score_id = _next_score_id
    _next_score_id += 1

    score_record = {
        "score_id": score_id,
        "user_id": score_request.user_id,
        "job_id": score_request.job_id,
        "score": total_score,
        "breakdown": breakdown,
        "created_at": datetime.utcnow().isoformat()
    }

    _scores[score_id] = score_record
    return ScoreResponse(**score_record)


@router.get("/scoring/{score_id}", response_model=ScoreResponse)
async def get_score(score_id: int):
    """T010: Get scoring result"""
    if score_id not in _scores:
        raise HTTPException(status_code=404, detail="スコアが見つかりません")

    return ScoreResponse(**_scores[score_id])


# =============================================================================
# T011: Matching Endpoint Models and Functions
# =============================================================================

class MatchRequest(BaseModel):
    user_id: int
    max_results: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=50.0, ge=0.0, le=100.0)


class MatchResult(BaseModel):
    job_id: int
    score: float
    ranking: int


class MatchResponse(BaseModel):
    match_id: int
    user_id: int
    matches: List[MatchResult]
    total_matches: int
    created_at: str


@router.post("/matching/find", response_model=MatchResponse)
async def find_matches(match_request: MatchRequest):
    """T011: Find job matches for user"""
    global _next_match_id

    # Mock matching results for TDD
    mock_matches = [
        MatchResult(job_id=1, score=85.5, ranking=1),
        MatchResult(job_id=2, score=78.2, ranking=2),
        MatchResult(job_id=3, score=72.0, ranking=3),
    ]

    # Filter by min_score
    filtered_matches = [m for m in mock_matches if m.score >= match_request.min_score]

    # Limit results
    limited_matches = filtered_matches[:match_request.max_results]

    match_id = _next_match_id
    _next_match_id += 1

    match_record = {
        "match_id": match_id,
        "user_id": match_request.user_id,
        "matches": [m.model_dump() for m in limited_matches],
        "total_matches": len(limited_matches),
        "created_at": datetime.utcnow().isoformat()
    }

    _matches[match_id] = match_record
    return MatchResponse(**match_record)


@router.get("/matching/{match_id}", response_model=MatchResponse)
async def get_match_results(match_id: int):
    """T011: Get matching results"""
    if match_id not in _matches:
        raise HTTPException(status_code=404, detail="マッチング結果が見つかりません")

    return MatchResponse(**_matches[match_id])


# =============================================================================
# T012: Email Sending Endpoint Models and Functions
# =============================================================================

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    template: str
    data: Optional[Dict[str, Any]] = None


class EmailResponse(BaseModel):
    email_id: int
    to_email: str
    subject: str
    status: str
    sent_at: Optional[str] = None
    created_at: str


@router.post("/email/send", response_model=EmailResponse)
async def send_email(email_request: EmailRequest):
    """T012: Send email with template"""
    global _next_email_id

    # Validate email format (basic validation)
    if '@' not in email_request.to_email:
        raise HTTPException(status_code=400, detail="有効なメールアドレスを入力してください")

    email_id = _next_email_id
    _next_email_id += 1

    # Mock email sending for TDD
    email_record = {
        "email_id": email_id,
        "to_email": email_request.to_email,
        "subject": email_request.subject,
        "template": email_request.template,
        "data": email_request.data or {},
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }

    _emails[email_id] = email_record
    return EmailResponse(**email_record)


@router.get("/email/{email_id}", response_model=EmailResponse)
async def get_email_status(email_id: int):
    """T012: Get email sending status"""
    if email_id not in _emails:
        raise HTTPException(status_code=404, detail="メールが見つかりません")

    return EmailResponse(**_emails[email_id])


# =============================================================================
# T013: Batch Operations Endpoint Models and Functions
# =============================================================================

class BatchOperationRequest(BaseModel):
    operation_type: str = Field(..., description="バッチ操作タイプ")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_count: Optional[int] = None


class BatchOperationResponse(BaseModel):
    batch_id: int
    operation_type: str
    status: str
    processed_count: int
    total_count: int
    progress_percent: float
    started_at: str
    completed_at: Optional[str] = None


@router.post("/batch/start", response_model=BatchOperationResponse)
async def start_batch_operation(batch_request: BatchOperationRequest):
    """T013: Start batch operation"""
    global _next_batch_id

    valid_operations = ["score_calculation", "email_sending", "data_cleanup", "report_generation"]
    if batch_request.operation_type not in valid_operations:
        raise HTTPException(
            status_code=400,
            detail=f"無効な操作タイプです。有効な値: {valid_operations}"
        )

    batch_id = _next_batch_id
    _next_batch_id += 1

    # Mock batch operation for TDD
    total_count = batch_request.target_count or 100
    processed_count = total_count  # Simplified - instant completion
    progress_percent = 100.0

    batch_record = {
        "batch_id": batch_id,
        "operation_type": batch_request.operation_type,
        "status": "completed",
        "processed_count": processed_count,
        "total_count": total_count,
        "progress_percent": progress_percent,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "parameters": batch_request.parameters
    }

    _batch_operations[batch_id] = batch_record
    return BatchOperationResponse(**batch_record)


@router.get("/batch/{batch_id}", response_model=BatchOperationResponse)
async def get_batch_status(batch_id: int):
    """T013: Get batch operation status"""
    if batch_id not in _batch_operations:
        raise HTTPException(status_code=404, detail="バッチ操作が見つかりません")

    return BatchOperationResponse(**_batch_operations[batch_id])


@router.get("/batch", response_model=List[BatchOperationResponse])
async def list_batch_operations(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """T013: List batch operations"""
    all_batches = list(_batch_operations.values())
    sorted_batches = sorted(all_batches, key=lambda x: x.get("started_at", ""), reverse=True)

    start = offset
    end = offset + limit
    paginated_batches = sorted_batches[start:end]

    return [BatchOperationResponse(**batch) for batch in paginated_batches]