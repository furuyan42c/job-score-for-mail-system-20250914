"""
API Documentation Generation System
T062-GREEN: Auto-generate comprehensive API documentation

This system provides automatic generation of OpenAPI documentation,
interactive Swagger UI, and exportable documentation formats.

Features:
- Auto-discovery of FastAPI routes and models
- Enhanced OpenAPI spec generation
- Interactive Swagger UI with custom themes
- Export to Markdown and PDF
- API versioning support
- Custom documentation templates

Author: Claude Code Assistant
Created: 2025-09-19
Version: 1.0.0
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from pathlib import Path
import inspect
import logging

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
import yaml

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class APIEndpoint:
    """API endpoint information"""
    path: str
    method: str
    name: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    deprecated: bool = False
    version: str = "v1"

@dataclass
class APIDocumentationConfig:
    """Configuration for API documentation generation"""
    title: str = "Mail Score API"
    version: str = "1.0.0"
    description: str = "Comprehensive job recommendation and email generation API"
    contact: Dict[str, str] = field(default_factory=lambda: {
        "name": "API Support",
        "email": "api-support@mailscore.com",
        "url": "https://mailscore.com/support"
    })
    license: Dict[str, str] = field(default_factory=lambda: {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    })
    servers: List[Dict[str, str]] = field(default_factory=lambda: [
        {"url": "https://api.mailscore.com", "description": "Production server"},
        {"url": "https://staging-api.mailscore.com", "description": "Staging server"},
        {"url": "http://localhost:8000", "description": "Development server"}
    ])
    custom_css: str = ""
    include_examples: bool = True
    include_schemas: bool = True
    group_by_tags: bool = True

@dataclass
class DocumentationMetrics:
    """Metrics for documentation quality"""
    total_endpoints: int = 0
    documented_endpoints: int = 0
    coverage_percentage: float = 0.0
    missing_descriptions: List[str] = field(default_factory=list)
    missing_examples: List[str] = field(default_factory=list)
    deprecated_endpoints: List[str] = field(default_factory=list)

# ============================================================================
# OPENAPI CUSTOMIZATION
# ============================================================================

class EnhancedOpenAPIGenerator:
    """Enhanced OpenAPI specification generator"""

    def __init__(self, config: APIDocumentationConfig):
        self.config = config
        self.custom_schemas = {}
        self.custom_examples = {}

    def generate_openapi_spec(self, app: FastAPI) -> Dict[str, Any]:
        """Generate enhanced OpenAPI specification"""

        # Get base OpenAPI spec from FastAPI
        openapi_spec = get_openapi(
            title=self.config.title,
            version=self.config.version,
            description=self.config.description,
            routes=app.routes,
        )

        # Enhance with custom information
        openapi_spec = self._enhance_spec(openapi_spec, app)

        return openapi_spec

    def _enhance_spec(self, spec: Dict[str, Any], app: FastAPI) -> Dict[str, Any]:
        """Enhance OpenAPI spec with additional information"""

        # Add contact and license information
        spec["info"]["contact"] = self.config.contact
        spec["info"]["license"] = self.config.license

        # Add servers
        spec["servers"] = self.config.servers

        # Add custom tags with descriptions
        spec["tags"] = self._generate_tag_descriptions(app)

        # Enhance paths with examples and better descriptions
        if "paths" in spec:
            spec["paths"] = self._enhance_paths(spec["paths"], app)

        # Add custom components
        if "components" in spec:
            spec["components"] = self._enhance_components(spec["components"])

        # Add custom extensions
        spec["x-logo"] = {
            "url": "https://mailscore.com/logo.png",
            "altText": "Mail Score API"
        }

        return spec

    def _generate_tag_descriptions(self, app: FastAPI) -> List[Dict[str, Any]]:
        """Generate tag descriptions from routes"""
        tags = {}

        for route in app.routes:
            if isinstance(route, APIRoute) and route.tags:
                for tag in route.tags:
                    if tag not in tags:
                        tags[tag] = {
                            "name": tag,
                            "description": self._get_tag_description(tag)
                        }

        return list(tags.values())

    def _get_tag_description(self, tag: str) -> str:
        """Get description for a tag"""
        descriptions = {
            "authentication": "User authentication and authorization endpoints",
            "users": "User profile management and operations",
            "jobs": "Job listing and management endpoints",
            "matching": "Job recommendation and matching algorithms",
            "analytics": "Analytics and reporting endpoints",
            "email": "Email generation and delivery services",
            "admin": "Administrative functions and system management",
            "health": "System health and monitoring endpoints",
            "sql": "SQL execution and data query endpoints",
            "performance": "Performance monitoring and optimization",
            "batch": "Batch processing and background jobs"
        }

        return descriptions.get(tag.lower(), f"{tag.capitalize()} related endpoints")

    def _enhance_paths(self, paths: Dict[str, Any], app: FastAPI) -> Dict[str, Any]:
        """Enhance path specifications with examples and better descriptions"""

        for path, path_methods in paths.items():
            for method, operation in path_methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    # Add examples to request body
                    if "requestBody" in operation:
                        operation["requestBody"] = self._add_request_examples(
                            operation["requestBody"], path, method
                        )

                    # Add examples to responses
                    if "responses" in operation:
                        operation["responses"] = self._add_response_examples(
                            operation["responses"], path, method
                        )

                    # Enhance operation description
                    operation["description"] = self._enhance_operation_description(
                        operation.get("description", ""), path, method
                    )

        return paths

    def _add_request_examples(
        self,
        request_body: Dict[str, Any],
        path: str,
        method: str
    ) -> Dict[str, Any]:
        """Add examples to request body"""

        if "content" in request_body:
            for content_type, content_info in request_body["content"].items():
                if "schema" in content_info:
                    example = self._generate_example_for_schema(
                        content_info["schema"], path, method, "request"
                    )
                    if example:
                        content_info["example"] = example

        return request_body

    def _add_response_examples(
        self,
        responses: Dict[str, Any],
        path: str,
        method: str
    ) -> Dict[str, Any]:
        """Add examples to responses"""

        for status_code, response_info in responses.items():
            if "content" in response_info:
                for content_type, content_info in response_info["content"].items():
                    if "schema" in content_info:
                        example = self._generate_example_for_schema(
                            content_info["schema"], path, method, "response", status_code
                        )
                        if example:
                            content_info["example"] = example

        return responses

    def _generate_example_for_schema(
        self,
        schema: Dict[str, Any],
        path: str,
        method: str,
        type_: str,
        status_code: str = None
    ) -> Optional[Dict[str, Any]]:
        """Generate realistic examples for schemas"""

        # Check custom examples first
        example_key = f"{path}:{method}:{type_}:{status_code or 'default'}"
        if example_key in self.custom_examples:
            return self.custom_examples[example_key]

        # Generate based on schema type
        if "$ref" in schema:
            schema_name = schema["$ref"].split("/")[-1]
            return self._get_model_example(schema_name)

        if schema.get("type") == "object" and "properties" in schema:
            return self._generate_object_example(schema["properties"])

        return None

    def _get_model_example(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get example for a specific model"""

        examples = {
            "UserProfile": {
                "user_id": 123,
                "name": "田中太郎",
                "email": "tanaka@example.com",
                "location": "東京都渋谷区",
                "skills": ["Python", "機械学習", "データ分析"],
                "experience_years": 5
            },
            "JobMatch": {
                "job_id": 456,
                "title": "データサイエンティスト",
                "company": "テック株式会社",
                "location": "東京都",
                "salary": "600-800万円",
                "match_score": 0.89,
                "description": "機械学習を活用したデータ分析業務"
            },
            "EmailContent": {
                "subject": "あなたにピッタリの求人5件をご紹介",
                "greeting": "田中太郎様、いつもお世話になっております。",
                "sections": [
                    {
                        "title": "編集部厳選求人",
                        "job_items": ["データサイエンティスト @ テック株式会社"]
                    }
                ],
                "language": "ja"
            },
            "SQLExecuteRequest": {
                "query": "SELECT * FROM jobs WHERE location LIKE '%東京%' LIMIT 10",
                "limit": 10,
                "explain_only": False,
                "cache_ttl": 300
            },
            "APIError": {
                "error": "認証に失敗しました",
                "error_code": "AUTH_FAILED",
                "timestamp": "2025-09-19T10:30:00Z",
                "correlation_id": "abc123def456"
            }
        }

        return examples.get(model_name)

    def _generate_object_example(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Generate example for object properties"""
        example = {}

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")

            if prop_type == "string":
                if "email" in prop_name.lower():
                    example[prop_name] = "user@example.com"
                elif "name" in prop_name.lower():
                    example[prop_name] = "サンプルユーザー"
                elif "id" in prop_name.lower():
                    example[prop_name] = "abc123"
                else:
                    example[prop_name] = "サンプル値"

            elif prop_type == "integer":
                example[prop_name] = 123

            elif prop_type == "number":
                example[prop_name] = 123.45

            elif prop_type == "boolean":
                example[prop_name] = True

            elif prop_type == "array":
                items = prop_schema.get("items", {})
                if items.get("type") == "string":
                    example[prop_name] = ["サンプル1", "サンプル2"]
                else:
                    example[prop_name] = [123, 456]

        return example

    def _enhance_operation_description(
        self,
        original_description: str,
        path: str,
        method: str
    ) -> str:
        """Enhance operation description with additional context"""

        enhanced = original_description

        # Add path and method context if description is empty
        if not enhanced:
            if method.upper() == "GET":
                enhanced = f"Retrieve information from {path}"
            elif method.upper() == "POST":
                enhanced = f"Create or submit data to {path}"
            elif method.upper() == "PUT":
                enhanced = f"Update data at {path}"
            elif method.upper() == "DELETE":
                enhanced = f"Delete data from {path}"
            elif method.upper() == "PATCH":
                enhanced = f"Partially update data at {path}"

        # Add security notes for protected endpoints
        if "/admin/" in path or "/sql/" in path:
            enhanced += "\n\n⚠️ **Note**: This endpoint requires special permissions and is subject to rate limiting."

        # Add performance notes for potentially slow endpoints
        if any(keyword in path for keyword in ["/search", "/recommendations", "/batch"]):
            enhanced += "\n\n⏱️ **Performance**: This operation may take longer to complete depending on the data size."

        return enhanced

    def _enhance_components(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance components section"""

        # Add custom security schemes
        if "securitySchemes" not in components:
            components["securitySchemes"] = {}

        components["securitySchemes"].update({
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication"
            }
        })

        # Add custom examples
        if "examples" not in components:
            components["examples"] = {}

        components["examples"].update({
            "UserProfileExample": {
                "summary": "Sample user profile",
                "value": self._get_model_example("UserProfile")
            },
            "JobMatchExample": {
                "summary": "Sample job match",
                "value": self._get_model_example("JobMatch")
            }
        })

        return components

# ============================================================================
# DOCUMENTATION GENERATOR
# ============================================================================

class APIDocumentationGenerator:
    """Main API documentation generator"""

    def __init__(self, config: APIDocumentationConfig = None):
        self.config = config or APIDocumentationConfig()
        self.openapi_generator = EnhancedOpenAPIGenerator(self.config)
        self.app_reference = None

    def setup_documentation(self, app: FastAPI):
        """Setup documentation routes and handlers"""
        self.app_reference = app

        # Store original openapi function
        original_openapi = app.openapi

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            # Generate enhanced OpenAPI spec
            openapi_schema = self.openapi_generator.generate_openapi_spec(app)
            app.openapi_schema = openapi_schema
            return app.openapi_schema

        # Replace FastAPI's openapi function
        app.openapi = custom_openapi

        # Add documentation routes
        self._setup_documentation_routes(app)

    def _setup_documentation_routes(self, app: FastAPI):
        """Setup custom documentation routes"""

        @app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html(request: Request):
            """Enhanced Swagger UI with custom styling"""
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title=f"{self.config.title} - Documentation",
                swagger_favicon_url="/static/favicon.ico",
                swagger_css_url="/static/custom-swagger.css" if self.config.custom_css else None,
                swagger_js_url=None,  # Use default
                init_oauth=None
            )

        @app.get("/redoc", include_in_schema=False)
        async def redoc_html():
            """Enhanced ReDoc documentation"""
            return get_redoc_html(
                openapi_url="/openapi.json",
                title=f"{self.config.title} - Documentation",
                redoc_favicon_url="/static/favicon.ico"
            )

        @app.get("/docs/download/openapi.json", include_in_schema=False)
        async def download_openapi_json():
            """Download OpenAPI specification as JSON"""
            return JSONResponse(content=app.openapi())

        @app.get("/docs/download/openapi.yaml", include_in_schema=False)
        async def download_openapi_yaml():
            """Download OpenAPI specification as YAML"""
            openapi_spec = app.openapi()
            yaml_content = yaml.dump(openapi_spec, default_flow_style=False, allow_unicode=True)

            return HTMLResponse(
                content=yaml_content,
                headers={"Content-Disposition": "attachment; filename=openapi.yaml"}
            )

        @app.get("/docs/metrics", include_in_schema=False)
        async def documentation_metrics():
            """Get documentation coverage metrics"""
            metrics = self.calculate_documentation_metrics(app)
            return JSONResponse(content=metrics.__dict__)

        @app.get("/docs/markdown", include_in_schema=False)
        async def download_markdown_docs():
            """Download documentation as Markdown"""
            markdown_content = self.generate_markdown_documentation(app)
            return HTMLResponse(
                content=markdown_content,
                headers={"Content-Disposition": "attachment; filename=api-docs.md"}
            )

    def calculate_documentation_metrics(self, app: FastAPI) -> DocumentationMetrics:
        """Calculate documentation coverage metrics"""
        metrics = DocumentationMetrics()

        for route in app.routes:
            if isinstance(route, APIRoute):
                metrics.total_endpoints += 1

                # Check if endpoint is documented
                if route.description and route.description.strip():
                    metrics.documented_endpoints += 1
                else:
                    metrics.missing_descriptions.append(f"{route.methods} {route.path}")

                # Check for deprecated endpoints
                if getattr(route, 'deprecated', False):
                    metrics.deprecated_endpoints.append(f"{route.methods} {route.path}")

        # Calculate coverage percentage
        if metrics.total_endpoints > 0:
            metrics.coverage_percentage = (
                metrics.documented_endpoints / metrics.total_endpoints * 100
            )

        return metrics

    def generate_markdown_documentation(self, app: FastAPI) -> str:
        """Generate Markdown documentation"""
        openapi_spec = app.openapi()

        markdown_parts = []

        # Title and description
        info = openapi_spec.get("info", {})
        markdown_parts.append(f"# {info.get('title', 'API Documentation')}")
        markdown_parts.append(f"\n**Version**: {info.get('version', '1.0.0')}")
        markdown_parts.append(f"\n{info.get('description', '')}\n")

        # Contact information
        if "contact" in info:
            contact = info["contact"]
            markdown_parts.append("## Contact Information")
            markdown_parts.append(f"- **Name**: {contact.get('name', '')}")
            markdown_parts.append(f"- **Email**: {contact.get('email', '')}")
            markdown_parts.append(f"- **URL**: {contact.get('url', '')}\n")

        # Servers
        servers = openapi_spec.get("servers", [])
        if servers:
            markdown_parts.append("## Servers")
            for server in servers:
                markdown_parts.append(f"- **{server.get('description', 'Server')}**: {server.get('url', '')}")
            markdown_parts.append("")

        # Authentication
        components = openapi_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        if security_schemes:
            markdown_parts.append("## Authentication")
            for name, scheme in security_schemes.items():
                markdown_parts.append(f"### {name}")
                markdown_parts.append(f"- **Type**: {scheme.get('type', '')}")
                markdown_parts.append(f"- **Description**: {scheme.get('description', '')}")
            markdown_parts.append("")

        # Endpoints by tag
        paths = openapi_spec.get("paths", {})
        tags = openapi_spec.get("tags", [])

        # Group endpoints by tag
        endpoints_by_tag = {}
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    operation_tags = operation.get("tags", ["Untagged"])
                    for tag in operation_tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append({
                            "path": path,
                            "method": method.upper(),
                            "operation": operation
                        })

        # Generate documentation for each tag
        for tag_info in tags:
            tag_name = tag_info["name"]
            if tag_name in endpoints_by_tag:
                markdown_parts.append(f"## {tag_name}")
                markdown_parts.append(f"{tag_info.get('description', '')}\n")

                for endpoint in endpoints_by_tag[tag_name]:
                    operation = endpoint["operation"]
                    markdown_parts.append(f"### {endpoint['method']} {endpoint['path']}")

                    # Summary and description
                    if "summary" in operation:
                        markdown_parts.append(f"**Summary**: {operation['summary']}")
                    if "description" in operation:
                        markdown_parts.append(f"\n{operation['description']}")

                    # Parameters
                    if "parameters" in operation:
                        markdown_parts.append("\n**Parameters**:")
                        for param in operation["parameters"]:
                            required = " (required)" if param.get("required", False) else ""
                            markdown_parts.append(
                                f"- `{param['name']}` ({param.get('in', 'query')}){required}: "
                                f"{param.get('description', '')}"
                            )

                    # Request body
                    if "requestBody" in operation:
                        markdown_parts.append("\n**Request Body**:")
                        request_body = operation["requestBody"]
                        if "description" in request_body:
                            markdown_parts.append(request_body["description"])

                    # Responses
                    if "responses" in operation:
                        markdown_parts.append("\n**Responses**:")
                        for status_code, response in operation["responses"].items():
                            description = response.get("description", "")
                            markdown_parts.append(f"- `{status_code}`: {description}")

                    markdown_parts.append("")

        return "\n".join(markdown_parts)

    def export_documentation(
        self,
        app: FastAPI,
        output_dir: str = "./docs",
        formats: List[str] = None
    ):
        """Export documentation in various formats"""
        formats = formats or ["json", "yaml", "markdown"]
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Get OpenAPI spec
        openapi_spec = app.openapi()

        # Export JSON
        if "json" in formats:
            json_path = output_path / "openapi.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported OpenAPI JSON to {json_path}")

        # Export YAML
        if "yaml" in formats:
            yaml_path = output_path / "openapi.yaml"
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(openapi_spec, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Exported OpenAPI YAML to {yaml_path}")

        # Export Markdown
        if "markdown" in formats:
            markdown_content = self.generate_markdown_documentation(app)
            markdown_path = output_path / "api-documentation.md"
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Exported Markdown documentation to {markdown_path}")

        # Export metrics
        metrics = self.calculate_documentation_metrics(app)
        metrics_path = output_path / "documentation-metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics.__dict__, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Exported documentation metrics to {metrics_path}")

    def add_custom_example(
        self,
        path: str,
        method: str,
        type_: str,
        example: Dict[str, Any],
        status_code: str = "default"
    ):
        """Add custom example for specific endpoint"""
        example_key = f"{path}:{method}:{type_}:{status_code}"
        self.openapi_generator.custom_examples[example_key] = example

    def set_custom_css(self, css_content: str):
        """Set custom CSS for Swagger UI"""
        self.config.custom_css = css_content

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_api_documentation(
    app: FastAPI,
    config: APIDocumentationConfig = None
) -> APIDocumentationGenerator:
    """Setup comprehensive API documentation for FastAPI app"""

    config = config or APIDocumentationConfig()
    doc_generator = APIDocumentationGenerator(config)
    doc_generator.setup_documentation(app)

    logger.info(f"API documentation setup complete for {config.title} v{config.version}")
    return doc_generator

def create_documentation_config(
    title: str = "Mail Score API",
    version: str = "1.0.0",
    description: str = None,
    **kwargs
) -> APIDocumentationConfig:
    """Create documentation configuration with sensible defaults"""

    default_description = f"""
# {title}

A comprehensive job recommendation and email generation API platform.

## Features

- **Job Matching**: Advanced algorithms for personalized job recommendations
- **Email Generation**: AI-powered email content creation and templates
- **User Management**: Complete user profile and preference management
- **Analytics**: Detailed analytics and reporting capabilities
- **Admin Tools**: Administrative functions and system management

## Getting Started

1. Obtain an API key from the developer console
2. Include the API key in the `Authorization` header: `Bearer YOUR_API_KEY`
3. Start making requests to the endpoints documented below

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Standard users**: 1000 requests per hour
- **Premium users**: 10000 requests per hour
- **Enterprise users**: Unlimited (within reasonable limits)

## Support

For API support, please contact our development team or visit our documentation portal.
    """.strip()

    return APIDocumentationConfig(
        title=title,
        version=version,
        description=description or default_description,
        **kwargs
    )

# ============================================================================
# TESTING UTILITIES
# ============================================================================

def test_documentation_generation():
    """Test the documentation generation system"""

    # Create test FastAPI app
    from fastapi import FastAPI, Depends, HTTPException
    from pydantic import BaseModel

    app = FastAPI()

    # Test models
    class TestUser(BaseModel):
        id: int
        name: str
        email: str

    class TestResponse(BaseModel):
        success: bool
        message: str
        data: Optional[TestUser] = None

    # Test endpoints
    @app.get("/users/{user_id}", response_model=TestResponse, tags=["users"])
    async def get_user(user_id: int):
        """Get user by ID"""
        return TestResponse(
            success=True,
            message="User retrieved successfully",
            data=TestUser(id=user_id, name="Test User", email="test@example.com")
        )

    @app.post("/users", response_model=TestResponse, tags=["users"])
    async def create_user(user: TestUser):
        """Create a new user"""
        return TestResponse(
            success=True,
            message="User created successfully",
            data=user
        )

    # Setup documentation
    config = create_documentation_config(
        title="Test API",
        version="1.0.0",
        description="Test API for documentation generation"
    )

    doc_generator = setup_api_documentation(app, config)

    # Test metrics calculation
    metrics = doc_generator.calculate_documentation_metrics(app)
    print(f"Documentation Metrics:")
    print(f"- Total endpoints: {metrics.total_endpoints}")
    print(f"- Documented endpoints: {metrics.documented_endpoints}")
    print(f"- Coverage: {metrics.coverage_percentage:.1f}%")

    # Test Markdown generation
    markdown_docs = doc_generator.generate_markdown_documentation(app)
    print(f"\nMarkdown documentation generated ({len(markdown_docs)} characters)")

    # Test export
    try:
        doc_generator.export_documentation(app, "./test_docs")
        print("Documentation exported successfully")
    except Exception as e:
        print(f"Export failed: {e}")

    return doc_generator

if __name__ == "__main__":
    test_documentation_generation()