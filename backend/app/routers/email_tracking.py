"""
Email Tracking API Routes - T032/T033 Implementation

This module provides API endpoints for email template customization and tracking.

Endpoints:
- Template customization
- Email tracking pixels
- Link click tracking
- Analytics reporting

Author: Claude Code Assistant
Created: 2025-09-19
Tasks: T032, T033 - Email Templates & Tracking
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
import io
import base64

from app.core.auth import get_current_user
from app.models.user import User
from app.services.email_template_service import (
    email_template_service,
    TemplateCustomization,
    EmailTheme,
    LayoutType,
    ColorScheme
)
from app.services.email_tracking_service import (
    email_tracking_service,
    EmailTrackingData,
    EmailAnalytics,
    TrackingEventType,
    LinkType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email", tags=["Email Templates & Tracking"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TemplateCustomizationRequest(BaseModel):
    """Request model for template customization."""
    name: str = Field(..., description="Template name")
    theme: EmailTheme = Field(EmailTheme.PROFESSIONAL, description="Template theme")
    layout: LayoutType = Field(LayoutType.SINGLE_COLUMN, description="Layout type")
    color_scheme: ColorScheme = Field(ColorScheme.BLUE_GRADIENT, description="Color scheme")
    custom_css: str = Field("", description="Custom CSS")
    custom_header_html: str = Field("", description="Custom header HTML")
    custom_footer_html: str = Field("", description="Custom footer HTML")
    logo_url: str = Field("", description="Logo URL")
    company_name: str = Field("", description="Company name")
    sections: Dict[str, Any] = Field(default_factory=dict, description="Section settings")

class TemplateCustomizationResponse(BaseModel):
    """Response model for template customization."""
    template_id: str
    name: str
    theme: str
    layout: str
    color_scheme: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    version: int

class EmailTrackingRequest(BaseModel):
    """Request model for email tracking creation."""
    email_address: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    template_id: str = Field("", description="Template ID")
    campaign_id: str = Field("", description="Campaign ID")
    a_b_test_variant: str = Field("", description="A/B test variant")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class EmailTrackingResponse(BaseModel):
    """Response model for email tracking."""
    tracking_id: str
    email_id: str
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    first_click_at: Optional[datetime]
    open_count: int
    click_count: int

class EmailAnalyticsResponse(BaseModel):
    """Response model for email analytics."""
    campaign_id: str
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    click_to_open_rate: float
    top_clicked_jobs: List[Dict[str, Any]]
    device_breakdown: Dict[str, int]
    client_breakdown: Dict[str, int]

# ============================================================================
# TEMPLATE CUSTOMIZATION ENDPOINTS
# ============================================================================

@router.post("/templates", response_model=TemplateCustomizationResponse)
async def create_custom_template(
    request: TemplateCustomizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new custom email template."""
    try:
        # Create template customization object
        customization = TemplateCustomization(
            user_id=str(current_user.id),
            name=request.name,
            theme=request.theme,
            layout=request.layout,
            color_scheme=request.color_scheme,
            custom_css=request.custom_css,
            custom_header_html=request.custom_header_html,
            custom_footer_html=request.custom_footer_html,
            logo_url=request.logo_url,
            company_name=request.company_name,
            sections=request.sections
        )

        # Create template
        created_template = await email_template_service.create_custom_template(
            user_id=str(current_user.id),
            customization=customization
        )

        return TemplateCustomizationResponse(
            template_id=created_template.template_id,
            name=created_template.name,
            theme=created_template.theme.value,
            layout=created_template.layout.value,
            color_scheme=created_template.color_scheme.value,
            created_at=created_template.created_at,
            updated_at=created_template.updated_at,
            is_active=created_template.is_active,
            version=created_template.version
        )

    except Exception as e:
        logger.error(f"Error creating custom template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.get("/templates", response_model=List[TemplateCustomizationResponse])
async def get_user_templates(
    current_user: User = Depends(get_current_user)
):
    """Get all templates for the current user."""
    try:
        templates = await email_template_service.get_user_templates(str(current_user.id))

        return [
            TemplateCustomizationResponse(
                template_id=template.template_id,
                name=template.name,
                theme=template.theme.value,
                layout=template.layout.value,
                color_scheme=template.color_scheme.value,
                created_at=template.created_at,
                updated_at=template.updated_at,
                is_active=template.is_active,
                version=template.version
            )
            for template in templates
        ]

    except Exception as e:
        logger.error(f"Error getting user templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")

@router.get("/templates/{template_id}", response_model=TemplateCustomizationResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific template."""
    try:
        template = await email_template_service.get_template(template_id, str(current_user.id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return TemplateCustomizationResponse(
            template_id=template.template_id,
            name=template.name,
            theme=template.theme.value,
            layout=template.layout.value,
            color_scheme=template.color_scheme.value,
            created_at=template.created_at,
            updated_at=template.updated_at,
            is_active=template.is_active,
            version=template.version
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")

@router.put("/templates/{template_id}", response_model=TemplateCustomizationResponse)
async def update_template(
    template_id: str,
    request: TemplateCustomizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing template."""
    try:
        updates = request.dict(exclude_unset=True)

        updated_template = await email_template_service.update_template(
            template_id=template_id,
            user_id=str(current_user.id),
            updates=updates
        )

        return TemplateCustomizationResponse(
            template_id=updated_template.template_id,
            name=updated_template.name,
            theme=updated_template.theme.value,
            layout=updated_template.layout.value,
            color_scheme=updated_template.color_scheme.value,
            created_at=updated_template.created_at,
            updated_at=updated_template.updated_at,
            is_active=updated_template.is_active,
            version=updated_template.version
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update template")

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a template."""
    try:
        success = await email_template_service.delete_template(template_id, str(current_user.id))

        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete template")

@router.get("/templates/themes")
async def get_template_themes():
    """Get available template themes."""
    try:
        themes = await email_template_service.get_template_themes()
        return {"themes": themes}

    except Exception as e:
        logger.error(f"Error getting template themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get themes")

@router.get("/templates/color-schemes")
async def get_color_schemes():
    """Get available color schemes."""
    try:
        schemes = await email_template_service.get_color_schemes()
        return {"color_schemes": schemes}

    except Exception as e:
        logger.error(f"Error getting color schemes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get color schemes")

@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    sample_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Generate preview HTML for a template."""
    try:
        template = await email_template_service.get_template(template_id, str(current_user.id))

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        preview_html = await email_template_service.preview_template(template, sample_data)

        return {"preview_html": preview_html}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating template preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview")

# ============================================================================
# EMAIL TRACKING ENDPOINTS
# ============================================================================

@router.post("/tracking", response_model=EmailTrackingResponse)
async def create_email_tracking(
    request: EmailTrackingRequest,
    current_user: User = Depends(get_current_user)
):
    """Create email tracking for a new email."""
    try:
        tracking_data = await email_tracking_service.create_email_tracking(
            user_id=str(current_user.id),
            email_address=request.email_address,
            subject=request.subject,
            template_id=request.template_id,
            campaign_id=request.campaign_id,
            a_b_test_variant=request.a_b_test_variant,
            metadata=request.metadata
        )

        return EmailTrackingResponse(
            tracking_id=tracking_data.tracking_id,
            email_id=tracking_data.email_id,
            status=tracking_data.status.value,
            sent_at=tracking_data.sent_at,
            delivered_at=tracking_data.delivered_at,
            opened_at=tracking_data.opened_at,
            first_click_at=tracking_data.first_click_at,
            open_count=tracking_data.open_count,
            click_count=tracking_data.click_count
        )

    except Exception as e:
        logger.error(f"Error creating email tracking: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tracking")

@router.get("/track/open/{tracking_id}")
async def track_email_open(
    tracking_id: str,
    request: Request,
    response: Response
):
    """Track email open via tracking pixel."""
    try:
        # Get user agent and IP
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        # Track the open
        await email_tracking_service.track_email_open(
            tracking_id=tracking_id,
            user_agent=user_agent,
            ip_address=ip_address
        )

        # Return 1x1 transparent pixel
        pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

        response.headers["Content-Type"] = "image/png"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return StreamingResponse(io.BytesIO(pixel_data), media_type="image/png")

    except Exception as e:
        logger.error(f"Error tracking email open: {e}")
        # Return pixel even on error
        pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
        return StreamingResponse(io.BytesIO(pixel_data), media_type="image/png")

@router.get("/track/click/{tracking_id}")
async def track_link_click(
    tracking_id: str,
    url: str = Query(..., description="Original URL to redirect to"),
    job_id: str = Query("", description="Job ID if applicable"),
    section: str = Query("", description="Email section"),
    position: int = Query(0, description="Position in email"),
    request: Request = None
):
    """Track link click and redirect to original URL."""
    try:
        # Get user agent and IP
        user_agent = request.headers.get("user-agent", "") if request else ""
        ip_address = request.client.host if request and request.client else ""

        # Determine link type based on URL
        link_type = LinkType.JOB_DETAIL
        if "company" in url.lower():
            link_type = LinkType.COMPANY_PAGE
        elif "apply" in url.lower():
            link_type = LinkType.APPLY_BUTTON
        elif "unsubscribe" in url.lower():
            link_type = LinkType.UNSUBSCRIBE

        # Track the click
        redirect_url = await email_tracking_service.track_link_click(
            tracking_id=tracking_id,
            link_url=url,
            link_type=link_type,
            job_id=job_id,
            section_id=section,
            position=position,
            user_agent=user_agent,
            ip_address=ip_address
        )

        # Redirect to original URL
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        logger.error(f"Error tracking link click: {e}")
        # Redirect to original URL even on error
        return RedirectResponse(url=url, status_code=302)

@router.get("/tracking/{tracking_id}", response_model=EmailTrackingResponse)
async def get_email_tracking(
    tracking_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get tracking information for an email."""
    try:
        tracking_data = await email_tracking_service._get_tracking_data(tracking_id)

        if not tracking_data:
            raise HTTPException(status_code=404, detail="Tracking data not found")

        return EmailTrackingResponse(
            tracking_id=tracking_data.tracking_id,
            email_id=tracking_data.email_id,
            status=tracking_data.status.value,
            sent_at=tracking_data.sent_at,
            delivered_at=tracking_data.delivered_at,
            opened_at=tracking_data.opened_at,
            first_click_at=tracking_data.first_click_at,
            open_count=tracking_data.open_count,
            click_count=tracking_data.click_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracking data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tracking data")

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/campaign/{campaign_id}", response_model=EmailAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific campaign."""
    try:
        analytics = await email_tracking_service.get_email_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )

        return EmailAnalyticsResponse(
            campaign_id=analytics.campaign_id,
            total_sent=analytics.total_sent,
            total_delivered=analytics.total_delivered,
            total_opened=analytics.total_opened,
            total_clicked=analytics.total_clicked,
            delivery_rate=analytics.delivery_rate,
            open_rate=analytics.open_rate,
            click_rate=analytics.click_rate,
            click_to_open_rate=analytics.click_to_open_rate,
            top_clicked_jobs=analytics.top_clicked_jobs,
            device_breakdown=analytics.device_breakdown,
            client_breakdown=analytics.client_breakdown
        )

    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/analytics/user/{user_id}/engagement")
async def get_user_engagement_score(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get user engagement score."""
    try:
        # Check if current user can access this data
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        engagement_score = await email_tracking_service.get_user_engagement_score(
            user_id=user_id,
            days=days
        )

        return {
            "user_id": user_id,
            "engagement_score": engagement_score,
            "analysis_period_days": days,
            "score_interpretation": {
                "0-25": "Low engagement",
                "26-50": "Medium engagement",
                "51-75": "High engagement",
                "76-100": "Very high engagement"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user engagement score: {e}")
        raise HTTPException(status_code=500, detail="Failed to get engagement score")

@router.post("/tracking/{tracking_id}/unsubscribe")
async def track_unsubscribe(
    tracking_id: str,
    request: Request
):
    """Track email unsubscribe."""
    try:
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        success = await email_tracking_service.track_unsubscribe(
            tracking_id=tracking_id,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return {"success": success, "message": "Unsubscribe tracked"}

    except Exception as e:
        logger.error(f"Error tracking unsubscribe: {e}")
        raise HTTPException(status_code=500, detail="Failed to track unsubscribe")

@router.post("/tracking/{tracking_id}/job-applied")
async def track_job_application(
    tracking_id: str,
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Track job application from email."""
    try:
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        success = await email_tracking_service.track_job_application(
            tracking_id=tracking_id,
            job_id=job_id,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return {"success": success, "message": "Job application tracked"}

    except Exception as e:
        logger.error(f"Error tracking job application: {e}")
        raise HTTPException(status_code=500, detail="Failed to track application")