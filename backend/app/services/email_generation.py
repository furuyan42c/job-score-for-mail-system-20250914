"""
Email Generation Service - T011 REFACTOR Implementation

Handles personalized email generation for users based on their job matches.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models import User, Job, Matching
from app.services.matching_service import MatchingService

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Email generation result container"""
    email_id: str
    subject: str
    body_html: str
    body_text: str
    status: str
    created_at: datetime
    job_count: int
    personalization_data: Dict[str, Any]
    preview_url: Optional[str] = None


class EmailGenerationService:
    """Service for generating personalized emails for users"""

    # Email templates
    TEMPLATES = {
        "default": {
            "subject": "【{user_name}様】おすすめのお仕事 {job_count}件",
            "html_header": """
                <html>
                <body style="font-family: 'Helvetica', sans-serif; line-height: 1.6;">
                    <h2>こんにちは、{user_name}様</h2>
                    <p>あなたにぴったりのお仕事を{job_count}件ご紹介します。</p>
                    <hr/>
            """,
            "html_job_template": """
                <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                    <h3>{title}</h3>
                    <p><strong>企業:</strong> {company}</p>
                    <p><strong>報酬:</strong> {fee:,}円</p>
                    <p><strong>マッチ度:</strong> {score:.1f}%</p>
                    <p>{description}</p>
                    <a href="{job_url}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">詳細を見る</a>
                </div>
            """,
            "html_footer": """
                    <hr/>
                    <p style="color: #666; font-size: 12px;">
                        このメールは自動生成されました。<br/>
                        配信停止をご希望の場合は、<a href="{unsubscribe_url}">こちら</a>をクリックしてください。
                    </p>
                </body>
                </html>
            """
        },
        "weekly_digest": {
            "subject": "【週刊】{user_name}様の今週のお仕事情報",
            "html_header": """
                <html>
                <body>
                    <h2>今週のおすすめ案件</h2>
                    <p>{user_name}様に最適な案件を厳選しました。</p>
            """
        }
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.matching_service = MatchingService(db)

    async def generate_user_email(
        self,
        user_id: int,
        template_id: str = "default",
        config: Optional[Dict[str, Any]] = None,
        preview_only: bool = False
    ) -> EmailResult:
        """
        Generate personalized email for a user

        Args:
            user_id: Target user ID
            template_id: Email template to use
            config: Additional configuration
            preview_only: Generate preview without sending

        Returns:
            EmailResult with generated email content
        """
        try:
            config = config or {}

            # Get user information
            user = await self._get_user(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Get user's top job matches
            limit = config.get("job_limit", 10)
            min_score = config.get("min_score", 60.0)

            matches = await self._get_user_matches(user_id, limit, min_score)

            # Get template
            template = self.TEMPLATES.get(template_id, self.TEMPLATES["default"])

            # Generate email content
            email_content = await self._generate_email_content(
                user=user,
                matches=matches,
                template=template,
                config=config
            )

            # Create email record
            email_id = str(uuid.uuid4())

            # Generate preview URL if needed
            preview_url = None
            if preview_only:
                preview_url = f"/email/preview/{email_id}"

            return EmailResult(
                email_id=email_id,
                subject=email_content["subject"],
                body_html=email_content["html"],
                body_text=email_content["text"],
                status="preview" if preview_only else "generated",
                created_at=datetime.now(),
                job_count=len(matches),
                personalization_data={
                    "user_name": user.name,
                    "user_id": user_id,
                    "template_id": template_id,
                    "job_ids": [m["job_id"] for m in matches]
                },
                preview_url=preview_url
            )

        except Exception as e:
            logger.error(f"Email generation failed for user {user_id}: {e}")
            raise

    async def _get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_user_matches(
        self,
        user_id: int,
        limit: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Get user's job matches"""
        # Get matches from matching service or database
        query = select(
            Matching.job_id,
            Matching.score,
            Job.title,
            Job.company,
            Job.fee,
            Job.description
        ).join(
            Job, Matching.job_id == Job.id
        ).where(
            and_(
                Matching.user_id == user_id,
                Matching.score >= min_score
            )
        ).order_by(
            Matching.score.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        rows = result.fetchall()

        matches = []
        for row in rows:
            matches.append({
                "job_id": row.job_id,
                "score": row.score,
                "title": row.title,
                "company": row.company,
                "fee": row.fee,
                "description": row.description[:200] + "..." if len(row.description) > 200 else row.description
            })

        return matches

    async def _generate_email_content(
        self,
        user: User,
        matches: List[Dict[str, Any]],
        template: Dict[str, str],
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate email content from template and data"""

        # Prepare template variables
        template_vars = {
            "user_name": user.name,
            "job_count": len(matches),
            "unsubscribe_url": config.get("unsubscribe_url", "#")
        }

        # Generate subject
        subject = template["subject"].format(**template_vars)

        # Generate HTML body
        html_parts = [template.get("html_header", "").format(**template_vars)]

        job_template = template.get("html_job_template", "")
        for match in matches:
            job_vars = {
                **match,
                "job_url": config.get("job_base_url", "/jobs/") + str(match["job_id"])
            }
            html_parts.append(job_template.format(**job_vars))

        html_parts.append(template.get("html_footer", "").format(**template_vars))
        html_body = "".join(html_parts)

        # Generate plain text version
        text_body = self._html_to_text(html_body)

        return {
            "subject": subject,
            "html": html_body,
            "text": text_body
        }

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text