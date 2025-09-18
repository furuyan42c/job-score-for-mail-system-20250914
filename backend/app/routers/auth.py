"""
Authentication Router
認証ルーター

ユーザー認証関連のAPIエンドポイント
- ログイン/ログアウト
- トークンリフレッシュ
- パスワードリセット
- セッション管理
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.utils.jwt import JWTManager, create_tokens_for_user
from app.utils.security import verify_password, hash_password, validate_password, generate_secure_token
from app.middleware.auth import get_current_user, get_current_user_optional, session_manager
from app.models.common import BaseResponse


logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic モデル
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30分
    user_info: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class SessionInfo(BaseModel):
    token_jti: str
    user_agent: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    is_current: bool


# ログイン試行回数制限（簡易版）
login_attempts = {}


@router.post("/login", response_model=LoginResponse, summary="ユーザーログイン")
async def login(
    request: Request,
    credentials: LoginRequest
) -> LoginResponse:
    """
    ユーザーログイン

    JWT トークンペアを発行してユーザー認証を行います。
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # レート制限チェック（簡易版）
    attempt_key = f"{credentials.email}:{client_ip}"
    current_attempts = login_attempts.get(attempt_key, [])

    # 最近5分以内の試行回数をチェック
    import time
    recent_attempts = [t for t in current_attempts if time.time() - t < 300]  # 5分

    if len(recent_attempts) >= 5:
        logger.warning(f"Too many login attempts for {credentials.email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    try:
        # データベースからユーザー情報を取得（仮実装）
        user = await get_user_by_email(credentials.email)

        if not user:
            # ユーザーが存在しない場合もパスワード検証のような時間をかける（タイミング攻撃対策）
            hash_password("dummy_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # パスワード検証
        if not verify_password(credentials.password, user["hashed_password"]):
            # 失敗した試行を記録
            login_attempts[attempt_key] = recent_attempts + [time.time()]

            logger.warning(f"Failed login attempt for {credentials.email} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # アカウントが無効化されていないかチェック
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account has been disabled"
            )

        # JWT トークンデータ準備
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "scope": user.get("role", "user"),
            "permissions": user.get("permissions", [])
        }

        # トークンペア生成
        tokens = create_tokens_for_user(token_data)

        # セッション管理
        payload = JWTManager.decode_token_without_verification(tokens["access_token"])
        if payload:
            session_manager.create_session(
                user_id=str(user["id"]),
                token_jti=payload.get("jti", ""),
                user_agent=user_agent,
                ip_address=client_ip
            )

        # 成功時は試行回数をリセット
        if attempt_key in login_attempts:
            del login_attempts[attempt_key]

        # ユーザー情報（パスワード除外）
        user_info = {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True),
            "last_login": datetime.utcnow().isoformat()
        }

        logger.info(f"Successful login for user {user['email']} from {client_ip}")

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user_info=user_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {credentials.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post("/refresh", response_model=Dict[str, str], summary="トークンリフレッシュ")
async def refresh_token(
    request: RefreshTokenRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Dict[str, str]:
    """
    リフレッシュトークンから新しいアクセストークンを生成

    有効期限切れ近いアクセストークンを新しいものに更新します。
    """
    try:
        # リフレッシュトークンから新しいトークンペアを生成
        new_tokens = JWTManager.refresh_access_token(request.refresh_token)

        # セッション管理更新
        payload = JWTManager.decode_token_without_verification(new_tokens["access_token"])
        if payload and current_user:
            session_manager.update_session_activity(
                user_id=current_user.get("sub", ""),
                token_jti=payload.get("jti", "")
            )

        logger.info(f"Token refreshed for user {current_user.get('email', 'unknown') if current_user else 'unknown'}")

        return new_tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=BaseResponse, summary="ユーザーログアウト")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> BaseResponse:
    """
    ユーザーログアウト

    現在のセッションを無効化してトークンをブラックリストに追加します。
    """
    try:
        user_id = current_user.get("sub", "")
        token_jti = current_user.get("jti", "")

        # セッション無効化
        if user_id and token_jti:
            session_manager.revoke_session(user_id, token_jti)

        logger.info(f"User {current_user.get('email', 'unknown')} logged out")

        return BaseResponse(message="Successfully logged out")

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all", response_model=BaseResponse, summary="全セッションログアウト")
async def logout_all_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> BaseResponse:
    """
    すべてのセッションからログアウト

    ユーザーのすべてのアクティブセッションを無効化します。
    """
    try:
        user_id = current_user.get("sub", "")

        if user_id:
            session_manager.revoke_all_sessions(user_id)

        logger.info(f"All sessions revoked for user {current_user.get('email', 'unknown')}")

        return BaseResponse(message="All sessions logged out successfully")

    except Exception as e:
        logger.error(f"Logout all sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout all sessions failed"
        )


@router.get("/me", response_model=Dict[str, Any], summary="ユーザー情報取得")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    現在認証されているユーザーの情報を取得

    JWT トークンから取得したユーザー情報を返します。
    """
    try:
        user_id = current_user.get("sub", "")
        user = await get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # パスワード以外の情報を返す
        user_info = {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "role": user.get("role", "user"),
            "permissions": user.get("permissions", []),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at", ""),
            "last_login": user.get("last_login", "")
        }

        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.get("/sessions", response_model=List[SessionInfo], summary="アクティブセッション一覧")
async def get_active_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[SessionInfo]:
    """
    ユーザーのアクティブセッション一覧を取得

    現在ログイン中のデバイス・ブラウザ一覧を表示します。
    """
    try:
        user_id = current_user.get("sub", "")
        current_jti = current_user.get("jti", "")

        sessions = session_manager.get_user_sessions(user_id)

        session_list = []
        for session in sessions:
            session_info = SessionInfo(
                token_jti=session["token_jti"],
                user_agent=session.get("user_agent", ""),
                ip_address=session.get("ip_address", ""),
                created_at=datetime.fromtimestamp(session["created_at"]),
                last_activity=datetime.fromtimestamp(session["last_activity"]),
                is_current=session["token_jti"] == current_jti
            )
            session_list.append(session_info)

        return session_list

    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.post("/change-password", response_model=BaseResponse, summary="パスワード変更")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> BaseResponse:
    """
    ユーザーパスワード変更

    現在のパスワードを確認してから新しいパスワードに変更します。
    """
    try:
        user_id = current_user.get("sub", "")
        user = await get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # 現在のパスワード検証
        if not verify_password(request.current_password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # 新しいパスワード強度チェック
        is_valid, errors = validate_password(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(errors)}"
            )

        # 現在のパスワードと同じでないかチェック
        if verify_password(request.new_password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # パスワードをハッシュ化してデータベース更新
        new_hashed_password = hash_password(request.new_password)
        await update_user_password(user_id, new_hashed_password)

        # パスワード変更後はすべてのセッションを無効化（セキュリティのため）
        session_manager.revoke_all_sessions(user_id)

        logger.info(f"Password changed for user {current_user.get('email', 'unknown')}")

        return BaseResponse(
            message="Password changed successfully. Please log in again with your new password."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/reset-password", response_model=BaseResponse, summary="パスワードリセット")
async def request_password_reset(
    request: PasswordResetRequest
) -> BaseResponse:
    """
    パスワードリセット要求

    メールアドレスにパスワードリセットリンクを送信します。
    """
    try:
        user = await get_user_by_email(request.email)

        # ユーザーが存在しない場合でも同じレスポンスを返す（セキュリティのため）
        if user:
            # リセットトークン生成
            reset_token = generate_secure_token(32)

            # トークンをデータベースに保存（有効期限付き）
            await save_password_reset_token(user["id"], reset_token)

            # パスワードリセットメールを送信
            await send_password_reset_email(user["email"], reset_token)

            logger.info(f"Password reset requested for {request.email}")

        return BaseResponse(
            message="If the email exists in our system, you will receive a password reset link."
        )

    except Exception as e:
        logger.error(f"Password reset error: {e}")
        # セキュリティのため、エラー詳細は返さない
        return BaseResponse(
            message="If the email exists in our system, you will receive a password reset link."
        )


# データベース操作関数（仮実装）
async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """メールアドレスでユーザーを取得（仮実装）"""
    # 実際の実装ではデータベースクエリを使用
    if email == "test@example.com":
        return {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": hash_password("ValidPassword123!"),  # テスト用
            "role": "user",
            "permissions": [],
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": None
        }
    return None


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """ユーザーIDでユーザーを取得（仮実装）"""
    if user_id == "1":
        return {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": hash_password("ValidPassword123!"),
            "role": "user",
            "permissions": [],
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": None
        }
    return None


async def update_user_password(user_id: str, hashed_password: str) -> None:
    """ユーザーパスワードを更新（仮実装）"""
    # 実際の実装ではデータベース更新を行う
    logger.info(f"Password updated for user ID: {user_id}")


async def save_password_reset_token(user_id: int, token: str) -> None:
    """パスワードリセットトークンを保存（仮実装）"""
    # 実際の実装ではデータベースに保存（有効期限付き）
    logger.info(f"Password reset token saved for user ID: {user_id}")


async def send_password_reset_email(email: str, token: str) -> None:
    """パスワードリセットメールを送信（仮実装）"""
    # 実際の実装ではメール送信サービスを使用
    logger.info(f"Password reset email sent to: {email}")