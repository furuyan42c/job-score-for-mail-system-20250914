"""
OpenAPI Documentation Utilities
OpenAPIドキュメント生成ユーティリティ

APIドキュメントの自動生成と拡張
- レスポンス例の追加
- エラーコードドキュメント
- 認証スキーマ
- カスタムOpenAPIスキーマ生成
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# セキュリティスキーマ
bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="JWT Bearer認証。ヘッダーに `Authorization: Bearer <token>` を含める必要があります。",
    bearerFormat="JWT",
    auto_error=True
)


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """カスタムOpenAPIスキーマ生成"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # セキュリティスキーマの追加
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT認証トークン。`/auth/login` エンドポイントから取得できます。"
        }
    }

    # グローバルセキュリティ設定
    openapi_schema["security"] = [{"bearerAuth": []}]

    # サーバー情報の追加
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "ローカル開発サーバー"
        },
        {
            "url": "https://api.job-matching.example.com",
            "description": "本番サーバー"
        }
    ]

    # 外部ドキュメントの追加
    openapi_schema["externalDocs"] = {
        "description": "プロジェクト仕様書",
        "url": "https://github.com/your-org/job-matching-system/docs"
    }

    # レスポンス例の追加
    add_response_examples(openapi_schema)

    # エラーレスポンスの標準化
    add_error_responses(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def add_response_examples(openapi_schema: Dict[str, Any]):
    """レスポンス例の追加"""

    # 共通レスポンス例
    examples = {
        "SuccessResponse": {
            "description": "成功レスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {},
                        "message": "操作が正常に完了しました"
                    }
                }
            }
        },
        "ErrorResponse": {
            "description": "エラーレスポンス",
            "content": {
                "application/json": {
                    "example": {
                        "error": "エラータイプ",
                        "detail": "エラーの詳細説明",
                        "request_id": "req-123456"
                    }
                }
            }
        }
    }

    # コンポーネントに例を追加
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}

    openapi_schema["components"]["examples"].update(examples)


def add_error_responses(openapi_schema: Dict[str, Any]):
    """標準エラーレスポンスの追加"""

    error_responses = {
        "400": {
            "description": "Bad Request - リクエストが不正です",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "validation_error"},
                            "detail": {"type": "string", "example": "入力データが不正です"},
                            "errors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {"type": "string"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - 認証が必要です",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "unauthorized"},
                            "detail": {"type": "string", "example": "認証トークンが無効または期限切れです"}
                        }
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden - アクセス権限がありません",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "forbidden"},
                            "detail": {"type": "string", "example": "このリソースへのアクセス権限がありません"}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Not Found - リソースが見つかりません",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "not_found"},
                            "detail": {"type": "string", "example": "指定されたリソースが見つかりません"}
                        }
                    }
                }
            }
        },
        "429": {
            "description": "Too Many Requests - レート制限に達しました",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "rate_limit_exceeded"},
                            "detail": {"type": "string", "example": "レート制限に達しました。しばらくしてから再試行してください"},
                            "retry_after": {"type": "integer", "example": 60}
                        }
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error - サーバー内部エラー",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "internal_server_error"},
                            "detail": {"type": "string", "example": "内部サーバーエラーが発生しました"},
                            "request_id": {"type": "string", "example": "req-123456"}
                        }
                    }
                }
            }
        }
    }

    # コンポーネントにレスポンスを追加
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    if "responses" not in openapi_schema["components"]:
        openapi_schema["components"]["responses"] = {}

    openapi_schema["components"]["responses"].update(error_responses)


class APIDocumentation:
    """APIドキュメンテーションヘルパー"""

    @staticmethod
    def endpoint_summary(
        summary: str,
        description: str,
        response_description: str = "成功レスポンス",
        tags: List[str] = None,
        deprecated: bool = False
    ) -> Dict[str, Any]:
        """エンドポイントのドキュメント情報を生成"""
        doc = {
            "summary": summary,
            "description": description,
            "response_description": response_description,
            "deprecated": deprecated
        }
        if tags:
            doc["tags"] = tags
        return doc

    @staticmethod
    def response_examples() -> Dict[str, Any]:
        """レスポンス例のセット"""
        return {
            200: {
                "description": "成功",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "data": {},
                            "message": "リクエストが正常に処理されました"
                        }
                    }
                }
            },
            400: {"$ref": "#/components/responses/400"},
            401: {"$ref": "#/components/responses/401"},
            403: {"$ref": "#/components/responses/403"},
            404: {"$ref": "#/components/responses/404"},
            429: {"$ref": "#/components/responses/429"},
            500: {"$ref": "#/components/responses/500"}
        }


# API情報メタデータ
API_INFO = {
    "title": "バイト求人マッチングシステム API",
    "version": "1.0.0",
    "contact": {
        "name": "開発チーム",
        "email": "dev-team@example.com",
        "url": "https://github.com/your-org/job-matching-system"
    },
    "license": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
}


# 使用例のドキュメント
USAGE_EXAMPLES = {
    "authentication": {
        "login": {
            "curl": """
                curl -X POST "http://localhost:8000/auth/login" \\
                     -H "Content-Type: application/json" \\
                     -d '{"email": "user@example.com", "password": "password123"}'
            """,
            "python": """
                import requests

                response = requests.post(
                    "http://localhost:8000/auth/login",
                    json={"email": "user@example.com", "password": "password123"}
                )
                token = response.json()["access_token"]
            """
        },
        "authenticated_request": {
            "curl": """
                curl -X GET "http://localhost:8000/api/v1/users/me" \\
                     -H "Authorization: Bearer YOUR_JWT_TOKEN"
            """,
            "python": """
                import requests

                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(
                    "http://localhost:8000/api/v1/users/me",
                    headers=headers
                )
            """
        }
    },
    "batch_processing": {
        "trigger": {
            "curl": """
                curl -X POST "http://localhost:8000/api/v1/batch/trigger" \\
                     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
                     -H "Content-Type: application/json" \\
                     -d '{"batch_type": "daily_matching"}'
            """
        }
    }
}