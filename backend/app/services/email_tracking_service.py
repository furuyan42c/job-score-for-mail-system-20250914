"""
Email Tracking and Analytics Service - T033 Implementation

This service provides comprehensive email tracking capabilities including:
- Email delivery tracking
- Open rate monitoring
- Click tracking
- User engagement analytics
- A/B testing support
- Performance metrics

Author: Claude Code Assistant
Created: 2025-09-19
Task: T033 - Email Tracking and Analytics
"""

import asyncio
import json
import logging
import base64
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import urllib.parse

from app.core.database import get_session
from app.models.user import User

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"

class TrackingEventType(str, Enum):
    """Types of tracking events."""
    EMAIL_SENT = "email_sent"
    EMAIL_DELIVERED = "email_delivered"
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    JOB_VIEWED = "job_viewed"
    JOB_APPLIED = "job_applied"
    EMAIL_BOUNCED = "email_bounced"
    EMAIL_UNSUBSCRIBED = "email_unsubscribed"
    EMAIL_MARKED_SPAM = "email_marked_spam"

class LinkType(str, Enum):
    """Types of tracked links."""
    JOB_DETAIL = "job_detail"
    COMPANY_PAGE = "company_page"
    APPLY_BUTTON = "apply_button"
    UNSUBSCRIBE = "unsubscribe"
    PREFERENCES = "preferences"
    LOGO = "logo"
    FOOTER_LINK = "footer_link"
    SOCIAL_MEDIA = "social_media"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class EmailTrackingData:
    """Email tracking information."""
    tracking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    email_id: str = ""
    email_address: str = ""
    subject: str = ""
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    first_click_at: Optional[datetime] = None
    status: EmailStatus = EmailStatus.PENDING
    open_count: int = 0
    click_count: int = 0
    unique_clicks: int = 0
    user_agent: str = ""
    ip_address: str = ""
    location: str = ""
    device_type: str = ""
    email_client: str = ""
    template_id: str = ""
    campaign_id: str = ""
    a_b_test_variant: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrackingEvent:
    """Individual tracking event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tracking_id: str = ""
    event_type: TrackingEventType = TrackingEventType.EMAIL_SENT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_agent: str = ""
    ip_address: str = ""
    location: str = ""
    device_type: str = ""
    email_client: str = ""
    link_url: str = ""
    link_type: LinkType = LinkType.JOB_DETAIL
    job_id: str = ""
    section_id: str = ""
    position_in_email: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmailAnalytics:
    """Email campaign analytics summary."""
    campaign_id: str = ""
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    avg_time_to_open: Optional[timedelta] = None
    avg_time_to_click: Optional[timedelta] = None
    peak_activity_hour: int = 0
    top_clicked_jobs: List[Dict[str, Any]] = field(default_factory=list)
    device_breakdown: Dict[str, int] = field(default_factory=dict)
    client_breakdown: Dict[str, int] = field(default_factory=dict)
    location_breakdown: Dict[str, int] = field(default_factory=dict)

# ============================================================================
# EMAIL TRACKING SERVICE
# ============================================================================

class EmailTrackingService:
    """Service for email tracking and analytics."""

    def __init__(self):
        self.tracking_pixel_template = (
            '<img src="{base_url}/api/v1/email/track/open/{tracking_id}" '
            'width="1" height="1" style="display:none;" alt="" />'
        )

    async def create_email_tracking(
        self,
        user_id: str,
        email_address: str,
        subject: str,
        template_id: str = "",
        campaign_id: str = "",
        a_b_test_variant: str = "",
        metadata: Dict[str, Any] = None
    ) -> EmailTrackingData:
        """Create new email tracking record."""
        try:
            tracking_data = EmailTrackingData(
                user_id=user_id,
                email_id=str(uuid.uuid4()),
                email_address=email_address,
                subject=subject,
                template_id=template_id,
                campaign_id=campaign_id,
                a_b_test_variant=a_b_test_variant,
                metadata=metadata or {}
            )

            # Save to database
            await self._save_tracking_data(tracking_data)

            logger.info(f"Created email tracking {tracking_data.tracking_id} for user {user_id}")
            return tracking_data

        except Exception as e:
            logger.error(f"Error creating email tracking: {e}")
            raise

    async def add_tracking_to_email(
        self,
        email_html: str,
        tracking_id: str,
        base_url: str = "https://api.mailscore.example.com"
    ) -> str:
        """Add tracking pixel and link tracking to email HTML."""
        try:
            # Add tracking pixel for open tracking
            tracking_pixel = self.tracking_pixel_template.format(
                base_url=base_url,
                tracking_id=tracking_id
            )

            # Insert tracking pixel before closing body tag
            if "</body>" in email_html:
                email_html = email_html.replace("</body>", f"{tracking_pixel}</body>")
            else:
                email_html += tracking_pixel

            # Convert all links to tracked links
            email_html = await self._add_link_tracking(email_html, tracking_id, base_url)

            return email_html

        except Exception as e:
            logger.error(f"Error adding tracking to email: {e}")
            raise

    async def track_email_sent(
        self,
        tracking_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> bool:
        """Track email sent event."""
        return await self._record_tracking_event(
            tracking_id=tracking_id,
            event_type=TrackingEventType.EMAIL_SENT,
            user_agent=user_agent,
            ip_address=ip_address
        )

    async def track_email_delivered(
        self,
        tracking_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> bool:
        """Track email delivered event."""
        return await self._record_tracking_event(
            tracking_id=tracking_id,
            event_type=TrackingEventType.EMAIL_DELIVERED,
            user_agent=user_agent,
            ip_address=ip_address
        )

    async def track_email_open(
        self,
        tracking_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> bool:
        """Track email open event."""
        try:
            # Get existing tracking data
            tracking_data = await self._get_tracking_data(tracking_id)
            if not tracking_data:
                return False

            # Update tracking data
            tracking_data.open_count += 1
            if tracking_data.opened_at is None:
                tracking_data.opened_at = datetime.utcnow()
                tracking_data.status = EmailStatus.OPENED

            # Parse user agent for device/client info
            device_info = self._parse_user_agent(user_agent)
            tracking_data.user_agent = user_agent
            tracking_data.ip_address = ip_address
            tracking_data.device_type = device_info.get("device_type", "")
            tracking_data.email_client = device_info.get("email_client", "")

            # Save updated tracking data
            await self._save_tracking_data(tracking_data)

            # Record tracking event
            await self._record_tracking_event(
                tracking_id=tracking_id,
                event_type=TrackingEventType.EMAIL_OPENED,
                user_agent=user_agent,
                ip_address=ip_address,
                metadata=device_info
            )

            logger.info(f"Tracked email open for {tracking_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking email open: {e}")
            return False

    async def track_link_click(
        self,
        tracking_id: str,
        link_url: str,
        link_type: LinkType = LinkType.JOB_DETAIL,
        job_id: str = "",
        section_id: str = "",
        position: int = 0,
        user_agent: str = "",
        ip_address: str = ""
    ) -> str:
        """Track link click and return redirect URL."""
        try:
            # Get existing tracking data
            tracking_data = await self._get_tracking_data(tracking_id)
            if not tracking_data:
                return link_url

            # Update tracking data
            tracking_data.click_count += 1
            if tracking_data.first_click_at is None:
                tracking_data.first_click_at = datetime.utcnow()
                tracking_data.status = EmailStatus.CLICKED

            # Parse user agent for device/client info
            device_info = self._parse_user_agent(user_agent)

            # Save updated tracking data
            await self._save_tracking_data(tracking_data)

            # Record tracking event
            await self._record_tracking_event(
                tracking_id=tracking_id,
                event_type=TrackingEventType.LINK_CLICKED,
                user_agent=user_agent,
                ip_address=ip_address,
                link_url=link_url,
                link_type=link_type,
                job_id=job_id,
                section_id=section_id,
                position_in_email=position,
                metadata={**device_info, "original_url": link_url}
            )

            logger.info(f"Tracked link click for {tracking_id}: {link_url}")
            return link_url

        except Exception as e:
            logger.error(f"Error tracking link click: {e}")
            return link_url

    async def track_job_application(
        self,
        tracking_id: str,
        job_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> bool:
        """Track job application from email."""
        return await self._record_tracking_event(
            tracking_id=tracking_id,
            event_type=TrackingEventType.JOB_APPLIED,
            user_agent=user_agent,
            ip_address=ip_address,
            job_id=job_id,
            metadata={"conversion": True}
        )

    async def track_unsubscribe(
        self,
        tracking_id: str,
        user_agent: str = "",
        ip_address: str = ""
    ) -> bool:
        """Track email unsubscribe."""
        try:
            # Update tracking data status
            tracking_data = await self._get_tracking_data(tracking_id)
            if tracking_data:
                tracking_data.status = EmailStatus.UNSUBSCRIBED
                await self._save_tracking_data(tracking_data)

            return await self._record_tracking_event(
                tracking_id=tracking_id,
                event_type=TrackingEventType.EMAIL_UNSUBSCRIBED,
                user_agent=user_agent,
                ip_address=ip_address
            )

        except Exception as e:
            logger.error(f"Error tracking unsubscribe: {e}")
            return False

    async def get_email_analytics(
        self,
        campaign_id: str = "",
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: str = ""
    ) -> EmailAnalytics:
        """Get email analytics for campaign or user."""
        try:
            # Get tracking data from database
            tracking_data_list = await self._get_analytics_data(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )

            # Calculate analytics
            analytics = EmailAnalytics(campaign_id=campaign_id)

            if not tracking_data_list:
                return analytics

            # Basic counts
            analytics.total_sent = len(tracking_data_list)
            analytics.total_delivered = len([t for t in tracking_data_list if t.status in [EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED]])
            analytics.total_opened = len([t for t in tracking_data_list if t.opened_at is not None])
            analytics.total_clicked = len([t for t in tracking_data_list if t.click_count > 0])
            analytics.total_bounced = len([t for t in tracking_data_list if t.status == EmailStatus.BOUNCED])
            analytics.total_unsubscribed = len([t for t in tracking_data_list if t.status == EmailStatus.UNSUBSCRIBED])

            # Calculate rates
            if analytics.total_sent > 0:
                analytics.delivery_rate = analytics.total_delivered / analytics.total_sent
                analytics.bounce_rate = analytics.total_bounced / analytics.total_sent
                analytics.unsubscribe_rate = analytics.total_unsubscribed / analytics.total_sent

            if analytics.total_delivered > 0:
                analytics.open_rate = analytics.total_opened / analytics.total_delivered

            if analytics.total_opened > 0:
                analytics.click_rate = analytics.total_clicked / analytics.total_opened
                analytics.click_to_open_rate = analytics.total_clicked / analytics.total_opened

            # Device and client breakdown
            analytics.device_breakdown = {}
            analytics.client_breakdown = {}
            analytics.location_breakdown = {}

            for tracking in tracking_data_list:
                if tracking.device_type:
                    analytics.device_breakdown[tracking.device_type] = analytics.device_breakdown.get(tracking.device_type, 0) + 1
                if tracking.email_client:
                    analytics.client_breakdown[tracking.email_client] = analytics.client_breakdown.get(tracking.email_client, 0) + 1
                if tracking.location:
                    analytics.location_breakdown[tracking.location] = analytics.location_breakdown.get(tracking.location, 0) + 1

            # Get top clicked jobs from events
            analytics.top_clicked_jobs = await self._get_top_clicked_jobs(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"Generated analytics for campaign {campaign_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting email analytics: {e}")
            raise

    async def get_user_engagement_score(self, user_id: str, days: int = 30) -> float:
        """Calculate user engagement score based on email interactions."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get user's tracking data
            tracking_data_list = await self._get_analytics_data(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )

            if not tracking_data_list:
                return 0.0

            # Calculate engagement metrics
            total_emails = len(tracking_data_list)
            opened_emails = len([t for t in tracking_data_list if t.opened_at is not None])
            clicked_emails = len([t for t in tracking_data_list if t.click_count > 0])
            total_clicks = sum(t.click_count for t in tracking_data_list)

            # Engagement score calculation
            # Base score from open rate (0-40 points)
            open_score = (opened_emails / total_emails) * 40 if total_emails > 0 else 0

            # Click rate bonus (0-30 points)
            click_score = (clicked_emails / total_emails) * 30 if total_emails > 0 else 0

            # Multiple clicks bonus (0-20 points)
            multi_click_score = min((total_clicks - clicked_emails) / total_emails * 20, 20) if total_emails > 0 else 0

            # Recency bonus (0-10 points)
            recent_activity = len([t for t in tracking_data_list if t.opened_at and (datetime.utcnow() - t.opened_at).days <= 7])
            recency_score = (recent_activity / total_emails) * 10 if total_emails > 0 else 0

            engagement_score = open_score + click_score + multi_click_score + recency_score
            return min(engagement_score, 100.0)  # Cap at 100

        except Exception as e:
            logger.error(f"Error calculating engagement score for user {user_id}: {e}")
            return 0.0

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _add_link_tracking(self, email_html: str, tracking_id: str, base_url: str) -> str:
        """Add tracking to all links in email."""
        # Simple implementation - in production, use proper HTML parsing
        import re

        def replace_link(match):
            original_url = match.group(1)
            if original_url.startswith('mailto:') or original_url.startswith('#'):
                return match.group(0)

            # Create tracked URL
            tracked_url = f"{base_url}/api/v1/email/track/click/{tracking_id}?url={urllib.parse.quote(original_url)}"
            return f'href="{tracked_url}"'

        # Replace all href attributes
        tracked_html = re.sub(r'href="([^"]*)"', replace_link, email_html)
        return tracked_html

    def _parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Parse user agent to extract device and email client info."""
        # Simple implementation - in production, use proper user agent parsing library
        user_agent = user_agent.lower()

        device_type = "desktop"
        if any(mobile in user_agent for mobile in ["mobile", "android", "iphone", "ipad"]):
            device_type = "mobile"

        email_client = "unknown"
        if "gmail" in user_agent:
            email_client = "gmail"
        elif "outlook" in user_agent:
            email_client = "outlook"
        elif "apple" in user_agent or "mail" in user_agent:
            email_client = "apple_mail"
        elif "thunderbird" in user_agent:
            email_client = "thunderbird"

        return {
            "device_type": device_type,
            "email_client": email_client,
            "user_agent": user_agent
        }

    async def _record_tracking_event(
        self,
        tracking_id: str,
        event_type: TrackingEventType,
        user_agent: str = "",
        ip_address: str = "",
        link_url: str = "",
        link_type: LinkType = LinkType.JOB_DETAIL,
        job_id: str = "",
        section_id: str = "",
        position_in_email: int = 0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Record a tracking event."""
        try:
            device_info = self._parse_user_agent(user_agent)

            event = TrackingEvent(
                tracking_id=tracking_id,
                event_type=event_type,
                user_agent=user_agent,
                ip_address=ip_address,
                device_type=device_info.get("device_type", ""),
                email_client=device_info.get("email_client", ""),
                link_url=link_url,
                link_type=link_type,
                job_id=job_id,
                section_id=section_id,
                position_in_email=position_in_email,
                metadata=metadata or {}
            )

            # Save to database
            await self._save_tracking_event(event)
            return True

        except Exception as e:
            logger.error(f"Error recording tracking event: {e}")
            return False

    # ========================================================================
    # MOCK DATABASE OPERATIONS
    # ========================================================================

    async def _save_tracking_data(self, tracking_data: EmailTrackingData):
        """Save tracking data to database (mock implementation)."""
        # In real implementation, save to PostgreSQL/Supabase
        pass

    async def _get_tracking_data(self, tracking_id: str) -> Optional[EmailTrackingData]:
        """Get tracking data from database (mock implementation)."""
        # In real implementation, query from PostgreSQL/Supabase
        return None

    async def _save_tracking_event(self, event: TrackingEvent):
        """Save tracking event to database (mock implementation)."""
        # In real implementation, save to PostgreSQL/Supabase
        pass

    async def _get_analytics_data(
        self,
        campaign_id: str = "",
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: str = ""
    ) -> List[EmailTrackingData]:
        """Get analytics data from database (mock implementation)."""
        # In real implementation, query from PostgreSQL/Supabase
        return []

    async def _get_top_clicked_jobs(
        self,
        campaign_id: str = "",
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top clicked jobs (mock implementation)."""
        # In real implementation, query from PostgreSQL/Supabase
        return []

# ============================================================================
# SERVICE INSTANCE
# ============================================================================

email_tracking_service = EmailTrackingService()