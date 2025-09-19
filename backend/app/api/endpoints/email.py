#!/usr/bin/env python3
"""
T011: Email generation API endpoints (GREEN Phase)

Minimal implementation to pass contract tests.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/email", tags=["email"])


class EmailSection(BaseModel):
    """Email section"""
    type: str
    content: Optional[str] = None
    job_ids: Optional[List[str]] = None
    button_text: Optional[str] = None
    url: Optional[str] = None


class EmailGenerateRequest(BaseModel):
    """Email generation request"""
    user_id: str
    template_type: str
    job_ids: Optional[List[str]] = None
    sections: Optional[List[EmailSection]] = None
    personalization: Optional[Dict[str, Any]] = None
    preview_mode: Optional[bool] = False


class EmailGenerateResponse(BaseModel):
    """Email generation response"""
    email_id: Optional[str]
    subject: str
    body: str
    template_used: str
    generated_at: str
    sections: List[Dict[str, Any]]
    preview: Optional[bool] = None
    is_preview: Optional[bool] = None


# Store for idempotency (in-memory for GREEN phase)
_request_cache = {}


@router.post("/generate", response_model=EmailGenerateResponse)
async def generate_email(
    request: EmailGenerateRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
) -> EmailGenerateResponse:
    """
    Generate an email from template.

    Minimal implementation for GREEN phase.
    """
    # Check for idempotency
    if x_request_id and x_request_id in _request_cache:
        return _request_cache[x_request_id]

    # Validate template
    valid_templates = ["weekly_digest", "custom", "daily_digest", "job_alert"]
    if request.template_type not in valid_templates:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template type: {request.template_type}"
        )

    # Validate request
    if not request.user_id:
        raise HTTPException(status_code=422, detail="user_id is required")

    if request.job_ids and not isinstance(request.job_ids, list):
        raise HTTPException(status_code=422, detail=[{"loc": ["body", "job_ids"], "msg": "must be a list"}])

    # Generate sections
    sections = []
    if request.sections:
        for section in request.sections:
            sections.append({
                "type": section.type,
                "content": section.content,
                "job_ids": section.job_ids
            })
    else:
        # Default sections
        sections = [
            {"type": "header", "content": "Your Weekly Job Digest"},
            {"type": "job_list", "job_ids": request.job_ids or []},
            {"type": "footer", "content": "Unsubscribe"}
        ]

    # Generate response
    response = EmailGenerateResponse(
        email_id=None if request.preview_mode else str(uuid.uuid4()),
        subject=f"Your {request.template_type.replace('_', ' ').title()}",
        body=f"Email content for {request.user_id}",
        template_used=request.template_type,
        generated_at=datetime.utcnow().isoformat(),
        sections=sections
    )

    # Handle preview mode
    if request.preview_mode:
        response.is_preview = True

    # Cache for idempotency
    if x_request_id:
        _request_cache[x_request_id] = response

    return response