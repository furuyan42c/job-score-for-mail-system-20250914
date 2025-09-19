"""
認証サービス - T081 Supabase Auth統合のリファクタリング実装
"""
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta


class AuthService:
    """認証関連のビジネスロジックを管理"""

    def __init__(self):
        self.sessions = {}  # セッション管理（インメモリ）
        self.users = {}     # ユーザー情報（インメモリ）

    def signup(self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ユーザー登録処理
        実際の実装では、Supabase APIを呼び出す
        """
        user_id = str(uuid.uuid4())
        access_token = f"sb_token_{uuid.uuid4().hex[:12]}"
        refresh_token = f"sb_refresh_{uuid.uuid4().hex[:12]}"

        # ユーザー情報を保存
        self.users[user_id] = {
            "id": user_id,
            "email": email,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        # セッション情報を保存
        self.sessions[access_token] = {
            "user_id": user_id,
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }

        return {
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600
            },
            "user": self.users[user_id]
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        ログイン処理
        実際の実装では、認証チェックを行う
        """
        # 簡易実装：メールアドレスから既存ユーザーを検索
        user = None
        for uid, udata in self.users.items():
            if udata["email"] == email:
                user = udata
                break

        if not user:
            # 新規ユーザーとして作成
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": email,
                "metadata": {},
                "created_at": datetime.now().isoformat()
            }
            self.users[user_id] = user

        access_token = f"sb_token_{uuid.uuid4().hex[:12]}"
        refresh_token = f"sb_refresh_{uuid.uuid4().hex[:12]}"

        self.sessions[access_token] = {
            "user_id": user["id"],
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }

        return {
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600
            }
        }

    def logout(self, token: Optional[str] = None) -> Dict[str, Any]:
        """ログアウト処理"""
        if token and token in self.sessions:
            del self.sessions[token]

        return {"status": "logged_out"}

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """トークンリフレッシュ処理"""
        # 簡易実装：新しいトークンを発行
        access_token = f"sb_token_{uuid.uuid4().hex[:12]}"
        new_refresh = f"sb_refresh_{uuid.uuid4().hex[:12]}"

        return {
            "session": {
                "access_token": access_token,
                "refresh_token": new_refresh,
                "expires_in": 3600
            }
        }

    def get_profile(self, token: Optional[str] = None) -> Dict[str, Any]:
        """ユーザープロファイル取得"""
        if token and token in self.sessions:
            user_id = self.sessions[token]["user_id"]
            if user_id in self.users:
                return {"user": self.users[user_id]}

        # デフォルトユーザー
        return {
            "user": {
                "id": str(uuid.uuid4()),
                "email": "user@example.com",
                "metadata": {"name": "Test User"}
            }
        }


# シングルトンインスタンス
auth_service = AuthService()