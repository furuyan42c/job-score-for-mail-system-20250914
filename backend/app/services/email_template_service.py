"""
Email Template Customization Service - T032 Implementation

This service provides advanced email template customization capabilities,
allowing users to personalize email layouts, styles, and content sections.

Features:
- Template theme customization
- Section layout management
- Color scheme personalization
- Typography preferences
- Brand customization
- Template versioning

Author: Claude Code Assistant
Created: 2025-09-19
Task: T032 - Email Template Customization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from pathlib import Path
import jinja2
from jinja2 import Template, Environment, FileSystemLoader
import aiofiles

from app.core.database import get_session
from app.models.user import User
from app.schemas.email import EmailTemplateSettings, EmailTheme

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class EmailTheme(str, Enum):
    """Available email themes."""
    PROFESSIONAL = "professional"
    MODERN = "modern"
    MINIMAL = "minimal"
    COLORFUL = "colorful"
    DARK = "dark"
    CLASSIC = "classic"

class LayoutType(str, Enum):
    """Email layout types."""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    GRID = "grid"
    CARD_LAYOUT = "card_layout"
    TIMELINE = "timeline"

class SectionType(str, Enum):
    """Email section types."""
    HEADER = "header"
    HERO = "hero"
    EDITORIAL_PICKS = "editorial_picks"
    TOP_RECOMMENDATIONS = "top_recommendations"
    PERSONALIZED_PICKS = "personalized_picks"
    NEW_ARRIVALS = "new_arrivals"
    POPULAR_JOBS = "popular_jobs"
    YOU_MIGHT_LIKE = "you_might_like"
    FOOTER = "footer"

class ColorScheme(str, Enum):
    """Color scheme options."""
    BLUE_GRADIENT = "blue_gradient"
    GREEN_NATURE = "green_nature"
    PURPLE_TECH = "purple_tech"
    ORANGE_WARM = "orange_warm"
    RED_DYNAMIC = "red_dynamic"
    GRAY_MINIMAL = "gray_minimal"
    CUSTOM = "custom"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ColorPalette:
    """Color palette configuration."""
    primary: str
    secondary: str
    accent: str
    background: str
    text_primary: str
    text_secondary: str
    border: str
    success: str
    warning: str
    error: str

@dataclass
class Typography:
    """Typography configuration."""
    font_family: str = "Inter, system-ui, sans-serif"
    heading_font: str = "Inter, system-ui, sans-serif"
    font_size_small: str = "12px"
    font_size_base: str = "14px"
    font_size_large: str = "16px"
    font_size_xlarge: str = "18px"
    font_size_heading: str = "20px"
    line_height: str = "1.6"
    letter_spacing: str = "0"

@dataclass
class SectionSettings:
    """Individual section settings."""
    enabled: bool = True
    title: str = ""
    subtitle: str = ""
    max_items: int = 10
    show_images: bool = True
    show_company: bool = True
    show_salary: bool = True
    show_location: bool = True
    show_tags: bool = True
    custom_css: str = ""

@dataclass
class TemplateCustomization:
    """Complete template customization settings."""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = "Custom Template"
    theme: EmailTheme = EmailTheme.PROFESSIONAL
    layout: LayoutType = LayoutType.SINGLE_COLUMN
    color_scheme: ColorScheme = ColorScheme.BLUE_GRADIENT
    color_palette: ColorPalette = field(default_factory=lambda: ColorPalette(
        primary="#3B82F6",
        secondary="#6366F1",
        accent="#F59E0B",
        background="#F8FAFC",
        text_primary="#1F2937",
        text_secondary="#6B7280",
        border="#E5E7EB",
        success="#10B981",
        warning="#F59E0B",
        error="#EF4444"
    ))
    typography: Typography = field(default_factory=Typography)
    sections: Dict[str, SectionSettings] = field(default_factory=dict)
    custom_css: str = ""
    custom_header_html: str = ""
    custom_footer_html: str = ""
    logo_url: str = ""
    company_name: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    version: int = 1

# ============================================================================
# TEMPLATE SERVICE CLASS
# ============================================================================

class EmailTemplateCustomizationService:
    """Service for email template customization."""

    def __init__(self, template_dir: str = "app/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Default color palettes
        self.color_palettes = {
            ColorScheme.BLUE_GRADIENT: ColorPalette(
                primary="#3B82F6", secondary="#6366F1", accent="#F59E0B",
                background="#F8FAFC", text_primary="#1F2937", text_secondary="#6B7280",
                border="#E5E7EB", success="#10B981", warning="#F59E0B", error="#EF4444"
            ),
            ColorScheme.GREEN_NATURE: ColorPalette(
                primary="#059669", secondary="#047857", accent="#F59E0B",
                background="#F0FDF4", text_primary="#1F2937", text_secondary="#6B7280",
                border="#D1FAE5", success="#10B981", warning="#F59E0B", error="#EF4444"
            ),
            ColorScheme.PURPLE_TECH: ColorPalette(
                primary="#7C3AED", secondary="#5B21B6", accent="#F59E0B",
                background="#FAF5FF", text_primary="#1F2937", text_secondary="#6B7280",
                border="#E9D5FF", success="#10B981", warning="#F59E0B", error="#EF4444"
            ),
            ColorScheme.ORANGE_WARM: ColorPalette(
                primary="#EA580C", secondary="#C2410C", accent="#3B82F6",
                background="#FFF7ED", text_primary="#1F2937", text_secondary="#6B7280",
                border="#FED7AA", success="#10B981", warning="#F59E0B", error="#EF4444"
            ),
            ColorScheme.RED_DYNAMIC: ColorPalette(
                primary="#DC2626", secondary="#B91C1C", accent="#F59E0B",
                background="#FEF2F2", text_primary="#1F2937", text_secondary="#6B7280",
                border="#FECACA", success="#10B981", warning="#F59E0B", error="#EF4444"
            ),
            ColorScheme.GRAY_MINIMAL: ColorPalette(
                primary="#374151", secondary="#1F2937", accent="#6366F1",
                background="#F9FAFB", text_primary="#111827", text_secondary="#6B7280",
                border="#E5E7EB", success="#10B981", warning="#F59E0B", error="#EF4444"
            )
        }

        # Default section configurations
        self.default_sections = {
            SectionType.HEADER: SectionSettings(
                enabled=True, title="", subtitle="", max_items=0
            ),
            SectionType.EDITORIAL_PICKS: SectionSettings(
                enabled=True, title="✨ エディターズピック",
                subtitle="専門チームが厳選した特別な求人", max_items=5
            ),
            SectionType.TOP_RECOMMENDATIONS: SectionSettings(
                enabled=True, title="🎯 あなたへのおすすめ",
                subtitle="スキルと経験にマッチした求人", max_items=10
            ),
            SectionType.PERSONALIZED_PICKS: SectionSettings(
                enabled=True, title="💡 パーソナライズド求人",
                subtitle="過去の閲覧履歴に基づくおすすめ", max_items=8
            ),
            SectionType.NEW_ARRIVALS: SectionSettings(
                enabled=True, title="🆕 新着求人",
                subtitle="最近公開された求人", max_items=6
            ),
            SectionType.POPULAR_JOBS: SectionSettings(
                enabled=True, title="🔥 人気求人",
                subtitle="多くの人に注目されている求人", max_items=8
            ),
            SectionType.YOU_MIGHT_LIKE: SectionSettings(
                enabled=True, title="❤️ 気になる求人",
                subtitle="あなたの好みに合いそうな求人", max_items=6
            ),
            SectionType.FOOTER: SectionSettings(
                enabled=True, title="", subtitle="", max_items=0
            )
        }

    async def create_custom_template(
        self,
        user_id: str,
        customization: TemplateCustomization
    ) -> TemplateCustomization:
        """Create a new custom template."""
        try:
            customization.user_id = user_id
            customization.template_id = str(uuid.uuid4())
            customization.created_at = datetime.utcnow()
            customization.updated_at = datetime.utcnow()

            # Set default sections if not provided
            if not customization.sections:
                customization.sections = {
                    section_type.value: section_settings
                    for section_type, section_settings in self.default_sections.items()
                }

            # Set color palette based on scheme
            if customization.color_scheme != ColorScheme.CUSTOM:
                customization.color_palette = self.color_palettes[customization.color_scheme]

            # Save to database (mock implementation)
            await self._save_template_to_db(customization)

            logger.info(f"Created custom template {customization.template_id} for user {user_id}")
            return customization

        except Exception as e:
            logger.error(f"Error creating custom template: {e}")
            raise

    async def get_user_templates(self, user_id: str) -> List[TemplateCustomization]:
        """Get all templates for a user."""
        try:
            # Mock implementation - retrieve from database
            templates = await self._get_templates_from_db(user_id)
            return templates

        except Exception as e:
            logger.error(f"Error getting user templates: {e}")
            raise

    async def get_template(self, template_id: str, user_id: str) -> Optional[TemplateCustomization]:
        """Get a specific template."""
        try:
            template = await self._get_template_from_db(template_id, user_id)
            return template

        except Exception as e:
            logger.error(f"Error getting template {template_id}: {e}")
            raise

    async def update_template(
        self,
        template_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> TemplateCustomization:
        """Update an existing template."""
        try:
            template = await self.get_template(template_id, user_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Update fields
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            template.updated_at = datetime.utcnow()
            template.version += 1

            # Update color palette if scheme changed
            if 'color_scheme' in updates and template.color_scheme != ColorScheme.CUSTOM:
                template.color_palette = self.color_palettes[template.color_scheme]

            await self._save_template_to_db(template)

            logger.info(f"Updated template {template_id} for user {user_id}")
            return template

        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            raise

    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a template."""
        try:
            result = await self._delete_template_from_db(template_id, user_id)
            logger.info(f"Deleted template {template_id} for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            raise

    async def render_email_with_template(
        self,
        template_id: str,
        user_id: str,
        email_data: Dict[str, Any]
    ) -> str:
        """Render email HTML using custom template."""
        try:
            # Get template customization
            customization = await self.get_template(template_id, user_id)
            if not customization:
                raise ValueError(f"Template {template_id} not found")

            # Generate CSS from customization
            custom_css = self._generate_css(customization)

            # Prepare template variables
            template_vars = {
                **email_data,
                'custom_css': custom_css,
                'customization': customization,
                'color_palette': asdict(customization.color_palette),
                'typography': asdict(customization.typography),
                'sections': customization.sections,
                'company_name': customization.company_name or "JobMatch",
                'logo_url': customization.logo_url or "/static/logo.png"
            }

            # Load and render template
            template_file = f"custom_email_{customization.layout.value}.html"
            template = self.env.get_template(template_file)

            rendered_html = template.render(**template_vars)

            logger.info(f"Rendered email with template {template_id}")
            return rendered_html

        except Exception as e:
            logger.error(f"Error rendering email with template {template_id}: {e}")
            raise

    def _generate_css(self, customization: TemplateCustomization) -> str:
        """Generate CSS from customization settings."""
        palette = customization.color_palette
        typography = customization.typography

        css = f"""
        <style>
            :root {{
                --primary-color: {palette.primary};
                --secondary-color: {palette.secondary};
                --accent-color: {palette.accent};
                --background-color: {palette.background};
                --text-primary: {palette.text_primary};
                --text-secondary: {palette.text_secondary};
                --border-color: {palette.border};
                --success-color: {palette.success};
                --warning-color: {palette.warning};
                --error-color: {palette.error};

                --font-family: {typography.font_family};
                --heading-font: {typography.heading_font};
                --font-size-small: {typography.font_size_small};
                --font-size-base: {typography.font_size_base};
                --font-size-large: {typography.font_size_large};
                --font-size-xlarge: {typography.font_size_xlarge};
                --font-size-heading: {typography.font_size_heading};
                --line-height: {typography.line_height};
                --letter-spacing: {typography.letter_spacing};
            }}

            body {{
                font-family: var(--font-family);
                font-size: var(--font-size-base);
                line-height: var(--line-height);
                color: var(--text-primary);
                background-color: var(--background-color);
                letter-spacing: var(--letter-spacing);
            }}

            h1, h2, h3, h4, h5, h6 {{
                font-family: var(--heading-font);
                color: var(--text-primary);
            }}

            .email-container {{
                background-color: white;
                border: 1px solid var(--border-color);
            }}

            .section-header {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
            }}

            .job-item {{
                border-bottom: 1px solid var(--border-color);
            }}

            .job-title {{
                color: var(--text-primary);
                font-size: var(--font-size-large);
            }}

            .company-name {{
                color: var(--primary-color);
                font-size: var(--font-size-base);
            }}

            .job-details {{
                color: var(--text-secondary);
                font-size: var(--font-size-small);
            }}

            .match-score {{
                background-color: var(--accent-color);
                color: white;
                font-size: var(--font-size-small);
            }}

            .btn-primary {{
                background-color: var(--primary-color);
                color: white;
                border: none;
            }}

            .btn-secondary {{
                background-color: var(--secondary-color);
                color: white;
                border: none;
            }}

            {customization.custom_css}
        </style>
        """

        return css

    async def get_template_themes(self) -> List[Dict[str, Any]]:
        """Get available template themes."""
        themes = []
        for theme in EmailTheme:
            themes.append({
                "id": theme.value,
                "name": theme.value.replace("_", " ").title(),
                "description": f"{theme.value.replace('_', ' ').title()} email theme",
                "preview_url": f"/templates/previews/{theme.value}.png"
            })
        return themes

    async def get_color_schemes(self) -> List[Dict[str, Any]]:
        """Get available color schemes."""
        schemes = []
        for scheme, palette in self.color_palettes.items():
            schemes.append({
                "id": scheme.value,
                "name": scheme.value.replace("_", " ").title(),
                "colors": asdict(palette),
                "preview_url": f"/colors/previews/{scheme.value}.png"
            })
        return schemes

    async def preview_template(
        self,
        customization: TemplateCustomization,
        sample_data: Dict[str, Any]
    ) -> str:
        """Generate preview HTML for template customization."""
        try:
            # Generate preview with sample data
            preview_data = {
                **sample_data,
                'user_name': "田中 太郎",
                'total_jobs': 25,
                'preview_mode': True
            }

            # Generate CSS
            custom_css = self._generate_css(customization)

            template_vars = {
                **preview_data,
                'custom_css': custom_css,
                'customization': customization,
                'color_palette': asdict(customization.color_palette),
                'typography': asdict(customization.typography),
                'sections': customization.sections,
                'company_name': customization.company_name or "JobMatch",
                'logo_url': customization.logo_url or "/static/logo.png"
            }

            # Use preview template
            template = self.env.get_template("email_preview.html")
            rendered_html = template.render(**template_vars)

            return rendered_html

        except Exception as e:
            logger.error(f"Error generating template preview: {e}")
            raise

    # ========================================================================
    # MOCK DATABASE OPERATIONS
    # ========================================================================

    async def _save_template_to_db(self, template: TemplateCustomization):
        """Save template to database (mock implementation)."""
        # In real implementation, save to PostgreSQL/Supabase
        pass

    async def _get_templates_from_db(self, user_id: str) -> List[TemplateCustomization]:
        """Get templates from database (mock implementation)."""
        # In real implementation, query from PostgreSQL/Supabase
        return []

    async def _get_template_from_db(self, template_id: str, user_id: str) -> Optional[TemplateCustomization]:
        """Get template from database (mock implementation)."""
        # In real implementation, query from PostgreSQL/Supabase
        return None

    async def _delete_template_from_db(self, template_id: str, user_id: str) -> bool:
        """Delete template from database (mock implementation)."""
        # In real implementation, delete from PostgreSQL/Supabase
        return True

# ============================================================================
# SERVICE INSTANCE
# ============================================================================

email_template_service = EmailTemplateCustomizationService()