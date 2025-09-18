"""
JWT Utilities
JWT トークンユーティリティ

JWT トークンの生成、検証、管理機能
- セキュアなJWT実装
- トークン有効期限管理
- 自動リフレッシュ機能
- セッション管理
"""

import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, status

from app.core.config import settings


class JWTManager:
    """JWT トークン管理クラス"""

    # アルゴリズム設定（セキュア）
    JWT_ALGORITHM = "HS256"

    # トークン有効期限
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # 必須クレーム
    REQUIRED_CLAIMS = ["sub", "exp", "iat", "jti"]

    @classmethod
    def create_access_token(cls, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        アクセストークンを作成

        Args:
            data: トークンに含めるデータ
            expires_delta: 有効期限（デフォルトは30分）

        Returns:
            str: JWT アクセストークン
        """
        to_encode = data.copy()

        # 有効期限設定
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 必須クレームを追加
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": cls._generate_jti(),  # JWT ID（トークン無効化用）
            "type": "access"
        })

        # スコープ/権限設定
        if "scope" not in to_encode and "permissions" not in to_encode:
            to_encode["scope"] = "user"

        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def create_refresh_token(cls, data: Dict[str, Any]) -> str:
        """
        リフレッシュトークンを作成

        Args:
            data: トークンに含めるデータ

        Returns:
            str: JWT リフレッシュトークン
        """
        to_encode = data.copy()

        # 有効期限設定（長期）
        expire = datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": cls._generate_jti(),
            "type": "refresh"
        })

        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        JWT トークンを検証

        Args:
            token: 検証するトークン

        Returns:
            Dict[str, Any]: デコードされたペイロード

        Raises:
            HTTPException: トークン検証失敗時
        """
        try:
            # トークンデコード
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[cls.JWT_ALGORITHM],
                options={"require": cls.REQUIRED_CLAIMS}
            )

            # 基本検証
            cls._validate_token_payload(payload)

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Dict[str, str]:
        """
        リフレッシュトークンから新しいアクセストークンを生成

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            Dict[str, str]: 新しいアクセストークンとリフレッシュトークン

        Raises:
            HTTPException: トークン検証失敗時
        """
        try:
            # リフレッシュトークンを検証
            payload = cls.verify_token(refresh_token)

            # リフレッシュトークンかチェック
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            # 新しいトークン生成用データ
            token_data = {
                "sub": payload["sub"],
                "email": payload.get("email"),
                "scope": payload.get("scope", "user"),
                "permissions": payload.get("permissions", [])
            }

            # 新しいアクセストークンを生成
            new_access_token = cls.create_access_token(token_data)

            # 新しいリフレッシュトークンも生成（セキュリティ向上）
            new_refresh_token = cls.create_refresh_token(token_data)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}"
            )

    @classmethod
    def decode_token_without_verification(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        検証なしでトークンをデコード（デバッグ用）

        Args:
            token: デコードするトークン

        Returns:
            Dict[str, Any]: デコードされたペイロード（検証なし）
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None

    @classmethod
    def get_token_expiry(cls, token: str) -> Optional[datetime]:
        """
        トークンの有効期限を取得

        Args:
            token: チェックするトークン

        Returns:
            datetime: 有効期限（取得失敗時はNone）
        """
        try:
            payload = cls.decode_token_without_verification(token)
            if payload and "exp" in payload:
                return datetime.utcfromtimestamp(payload["exp"])
        except Exception:
            pass

        return None

    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        """
        トークンが期限切れかチェック

        Args:
            token: チェックするトークン

        Returns:
            bool: 期限切れかどうか
        """
        expiry = cls.get_token_expiry(token)
        if expiry:
            return datetime.utcnow() > expiry
        return True  # 有効期限が取得できない場合は期限切れとみなす

    @staticmethod
    def _generate_jti() -> str:
        """JWT IDを生成"""
        from app.utils.security import SecureTokenGenerator
        return SecureTokenGenerator.generate_token(16)

    @staticmethod
    def _validate_token_payload(payload: Dict[str, Any]) -> None:
        """
        トークンペイロードの追加検証

        Args:
            payload: 検証するペイロード

        Raises:
            HTTPException: 検証失敗時
        """
        # 必須フィールドチェック
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject"
            )

        # トークンタイプチェック（オプション）
        token_type = payload.get("type")
        if token_type and token_type not in ["access", "refresh"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # 発行時刻の妥当性チェック
        iat = payload.get("iat")
        if iat:
            # 未来の時刻で発行されたトークンは無効
            if iat > time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token issued in the future"
                )

            # あまりに古いトークン（24時間以上前）は疑わしい
            if time.time() - iat > 86400:  # 24時間
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token too old"
                )


class TokenBlacklist:
    """
    トークンブラックリスト管理
    （実装は簡易版、本番ではRedisなど使用）
    """

    _blacklisted_tokens = set()

    @classmethod
    def add_token(cls, jti: str) -> None:
        """
        トークンをブラックリストに追加

        Args:
            jti: JWT ID
        """
        cls._blacklisted_tokens.add(jti)

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """
        トークンがブラックリストに含まれているかチェック

        Args:
            jti: JWT ID

        Returns:
            bool: ブラックリストに含まれているか
        """
        return jti in cls._blacklisted_tokens

    @classmethod
    def remove_expired_tokens(cls) -> None:
        """
        期限切れトークンをブラックリストから削除
        （定期的に実行すべき）
        """
        # 実装は省略（実際には有効期限を追跡して削除）
        pass


# 便利関数
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """アクセストークン作成（便利関数）"""
    return JWTManager.create_access_token(data, expires_delta)


def verify_token(token: str) -> Dict[str, Any]:
    """トークン検証（便利関数）"""
    return JWTManager.verify_token(token)


def create_tokens_for_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    ユーザー用のアクセス・リフレッシュトークンペアを作成

    Args:
        user_data: ユーザーデータ

    Returns:
        Dict[str, str]: トークンペア
    """
    access_token = JWTManager.create_access_token(user_data)
    refresh_token = JWTManager.create_refresh_token(user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# セキュリティ定数
JWT_ALGORITHM = JWTManager.JWT_ALGORITHM