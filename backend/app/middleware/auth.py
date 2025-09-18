"""
Authentication Middleware
認証ミドルウェア

JWT ベースのAPI認証ミドルウェア
- Bearer トークン認証
- ロールベースアクセス制御 (RBAC)
- パスベースの認証制御
- セッション管理
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Set, Dict, Any
import time
import logging
from functools import wraps

from app.utils.jwt import JWTManager, TokenBlacklist
from app.utils.security import timing_safe_compare


logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """認証ミドルウェアクラス"""

    def __init__(self):
        self.security = HTTPBearer(auto_error=False)

        # 認証不要パス（パターンマッチング対応）
        self.public_paths: Set[str] = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/system-info",
        }

        # 認証不要パスのプレフィックス
        self.public_prefixes: List[str] = [
            "/auth/",  # 認証関連エンドポイント
            "/static/",  # 静的ファイル
        ]

        # 管理者専用パス
        self.admin_paths: Set[str] = {
            "/admin/",
            "/system-info",
        }

        # 管理者専用プレフィックス
        self.admin_prefixes: List[str] = [
            "/admin/",
            "/api/v1/admin/",
        ]

    def is_public_path(self, path: str) -> bool:
        """
        パブリックパス（認証不要）かチェック

        Args:
            path: リクエストパス

        Returns:
            bool: パブリックパスかどうか
        """
        # 完全一致チェック
        if path in self.public_paths:
            return True

        # プレフィックスマッチチェック
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True

        return False

    def is_admin_path(self, path: str) -> bool:
        """
        管理者専用パスかチェック

        Args:
            path: リクエストパス

        Returns:
            bool: 管理者専用パスかどうか
        """
        # 完全一致チェック
        if path in self.admin_paths:
            return True

        # プレフィックスマッチチェック
        for prefix in self.admin_prefixes:
            if path.startswith(prefix):
                return True

        return False

    async def authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        リクエストを認証

        Args:
            request: FastAPI リクエストオブジェクト

        Returns:
            Optional[Dict[str, Any]]: 認証されたユーザー情報（未認証時はNone）

        Raises:
            HTTPException: 認証失敗時
        """
        path = request.url.path

        # パブリックパスは認証スキップ
        if self.is_public_path(path):
            return None

        # Authorizationヘッダー取得
        credentials: HTTPAuthorizationCredentials = await self.security(request)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # JWT トークン検証
        try:
            payload = JWTManager.verify_token(credentials.credentials)

            # ブラックリストチェック
            jti = payload.get("jti")
            if jti and TokenBlacklist.is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 管理者パスのアクセス制御
            if self.is_admin_path(path):
                await self._check_admin_access(payload)

            # リクエストにユーザー情報を追加
            request.state.user = payload
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.user_permissions = payload.get("permissions", [])

            return payload

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _check_admin_access(self, payload: Dict[str, Any]) -> None:
        """
        管理者アクセス権限をチェック

        Args:
            payload: JWT ペイロード

        Raises:
            HTTPException: 権限不足時
        """
        user_scope = payload.get("scope", "")
        user_permissions = payload.get("permissions", [])

        # 管理者権限チェック
        if user_scope != "admin" and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges for admin access"
            )


class AuthenticationDependency:
    """認証依存関数クラス"""

    def __init__(self):
        self.auth_middleware = AuthenticationMiddleware()

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """
        認証必須エンドポイント用依存関数

        Args:
            request: リクエストオブジェクト

        Returns:
            Dict[str, Any]: 認証されたユーザー情報

        Raises:
            HTTPException: 認証失敗時
        """
        user_info = await self.auth_middleware.authenticate_request(request)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_info


class OptionalAuthenticationDependency:
    """オプショナル認証依存関数クラス"""

    def __init__(self):
        self.auth_middleware = AuthenticationMiddleware()

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        認証オプショナルエンドポイント用依存関数

        Args:
            request: リクエストオブジェクト

        Returns:
            Optional[Dict[str, Any]]: 認証されたユーザー情報（未認証時はNone）
        """
        try:
            return await self.auth_middleware.authenticate_request(request)
        except HTTPException:
            return None


class AdminAuthenticationDependency:
    """管理者認証依存関数クラス"""

    def __init__(self):
        self.auth_middleware = AuthenticationMiddleware()

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """
        管理者専用エンドポイント用依存関数

        Args:
            request: リクエストオブジェクト

        Returns:
            Dict[str, Any]: 認証された管理者情報

        Raises:
            HTTPException: 認証失敗または権限不足時
        """
        user_info = await self.auth_middleware.authenticate_request(request)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 管理者権限チェック
        user_scope = user_info.get("scope", "")
        user_permissions = user_info.get("permissions", [])

        if user_scope != "admin" and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        return user_info


# 依存関数インスタンス（シングルトン）
get_current_user = AuthenticationDependency()
get_current_user_optional = OptionalAuthenticationDependency()
get_admin_user = AdminAuthenticationDependency()


def require_permissions(permissions: List[str]):
    """
    特定の権限を要求するデコレータ

    Args:
        permissions: 必要な権限リスト

    Returns:
        デコレータ関数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエストオブジェクトを取得
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # kwargsからRequestを探す
                request = kwargs.get('request')

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in decorator context"
                )

            # ユーザー権限チェック
            user_permissions = getattr(request.state, 'user_permissions', [])

            # 必要な権限がすべて含まれているかチェック
            missing_permissions = [p for p in permissions if p not in user_permissions]

            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {missing_permissions}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """
    特定のロールを要求するデコレータ

    Args:
        role: 必要なロール

    Returns:
        デコレータ関数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエストオブジェクトを取得
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get('request')

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in decorator context"
                )

            # ユーザーロールチェック
            user_info = getattr(request.state, 'user', {})
            user_scope = user_info.get('scope', '')

            if not timing_safe_compare(user_scope, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class SessionManager:
    """セッション管理クラス"""

    def __init__(self):
        # メモリベースの簡易実装（本番ではRedisなど使用）
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_id: str, token_jti: str, user_agent: str = "", ip_address: str = "") -> None:
        """
        新しいセッションを作成

        Args:
            user_id: ユーザーID
            token_jti: JWT ID
            user_agent: ユーザーエージェント
            ip_address: IPアドレス
        """
        session_data = {
            "user_id": user_id,
            "token_jti": token_jti,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "created_at": time.time(),
            "last_activity": time.time()
        }

        # ユーザーごとの複数セッション管理
        if user_id not in self._active_sessions:
            self._active_sessions[user_id] = {}

        self._active_sessions[user_id][token_jti] = session_data

    def update_session_activity(self, user_id: str, token_jti: str) -> None:
        """
        セッションの最終活動時刻を更新

        Args:
            user_id: ユーザーID
            token_jti: JWT ID
        """
        if user_id in self._active_sessions and token_jti in self._active_sessions[user_id]:
            self._active_sessions[user_id][token_jti]["last_activity"] = time.time()

    def revoke_session(self, user_id: str, token_jti: str) -> None:
        """
        特定のセッションを無効化

        Args:
            user_id: ユーザーID
            token_jti: JWT ID
        """
        if user_id in self._active_sessions and token_jti in self._active_sessions[user_id]:
            del self._active_sessions[user_id][token_jti]
            TokenBlacklist.add_token(token_jti)

    def revoke_all_sessions(self, user_id: str) -> None:
        """
        ユーザーのすべてのセッションを無効化

        Args:
            user_id: ユーザーID
        """
        if user_id in self._active_sessions:
            # すべてのトークンをブラックリストに追加
            for token_jti in self._active_sessions[user_id]:
                TokenBlacklist.add_token(token_jti)

            # セッション削除
            del self._active_sessions[user_id]

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        ユーザーのアクティブセッション一覧を取得

        Args:
            user_id: ユーザーID

        Returns:
            List[Dict[str, Any]]: セッション一覧
        """
        if user_id in self._active_sessions:
            return list(self._active_sessions[user_id].values())
        return []

    def cleanup_expired_sessions(self, max_inactive_minutes: int = 60) -> None:
        """
        非アクティブなセッションをクリーンアップ

        Args:
            max_inactive_minutes: 最大非アクティブ時間（分）
        """
        current_time = time.time()
        max_inactive_seconds = max_inactive_minutes * 60

        for user_id in list(self._active_sessions.keys()):
            sessions_to_remove = []

            for token_jti, session_data in self._active_sessions[user_id].items():
                if current_time - session_data["last_activity"] > max_inactive_seconds:
                    sessions_to_remove.append(token_jti)

            for token_jti in sessions_to_remove:
                self.revoke_session(user_id, token_jti)

            # ユーザーのセッションがすべてなくなった場合、ユーザーエントリも削除
            if not self._active_sessions[user_id]:
                del self._active_sessions[user_id]


# グローバルセッションマネージャー
session_manager = SessionManager()