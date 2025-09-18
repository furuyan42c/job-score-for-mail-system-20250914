"""
Security Utilities
セキュリティユーティリティ

パスワードハッシュ化、検証、強度チェックなどのセキュリティ関連機能
- 高セキュリティなbcryptハッシュ化
- パスワード強度検証
- セキュアなランダム文字列生成
- タイミング攻撃耐性
"""

import bcrypt
import secrets
import re
import time
from typing import Tuple, List
from functools import wraps


class PasswordValidator:
    """パスワード強度検証クラス"""

    # パスワード要件設定
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_LOWERCASE = True
    REQUIRE_UPPERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, List[str]]:
        """
        パスワード強度を検証

        Args:
            password: 検証するパスワード

        Returns:
            Tuple[bool, List[str]]: (有効かどうか, エラーリスト)
        """
        errors = []

        if not password:
            errors.append("Password is required")
            return False, errors

        # 長さチェック
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")

        # 小文字チェック
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # 大文字チェック
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # 数字チェック
        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        # 特殊文字チェック
        if cls.REQUIRE_SPECIAL:
            special_pattern = f'[{re.escape(cls.SPECIAL_CHARACTERS)}]'
            if not re.search(special_pattern, password):
                errors.append("Password must contain at least one special character")

        # 一般的な脆弱パスワードチェック
        weak_patterns = [
            r'password',
            r'123456',
            r'qwerty',
            r'admin',
            r'letmein',
            r'welcome',
            r'monkey',
            r'dragon'
        ]

        password_lower = password.lower()
        for pattern in weak_patterns:
            if re.search(pattern, password_lower):
                errors.append("Password contains common weak patterns")
                break

        # 連続文字チェック
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password should not contain repeated characters")

        # シーケンシャル文字チェック（簡易版）
        sequential_patterns = ['123', 'abc', 'ABC', '321', 'cba', 'CBA']
        for pattern in sequential_patterns:
            if pattern in password:
                errors.append("Password should not contain sequential characters")
                break

        return len(errors) == 0, errors


class PasswordHasher:
    """高セキュリティパスワードハッシュ化クラス"""

    # bcryptコスト係数（12以上推奨、時間とセキュリティのバランス）
    COST_FACTOR = 12

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        パスワードをbcryptでハッシュ化

        Args:
            password: プレーンテキストパスワード

        Returns:
            str: ハッシュ化されたパスワード
        """
        # UTF-8エンコードしてハッシュ化
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=cls.COST_FACTOR)
        hashed = bcrypt.hashpw(password_bytes, salt)

        return hashed.decode('utf-8')

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """
        パスワードを検証（タイミング攻撃耐性あり）

        Args:
            password: プレーンテキストパスワード
            hashed_password: ハッシュ化されたパスワード

        Returns:
            bool: パスワードが一致するかどうか
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')

            # bcryptは内部でタイミング攻撃耐性を持つ
            return bcrypt.checkpw(password_bytes, hashed_bytes)

        except (ValueError, TypeError):
            # 不正な形式の場合は常にFalseを返す（一定時間待つ）
            time.sleep(0.1)  # タイミング攻撃対策
            return False

    @classmethod
    def needs_rehash(cls, hashed_password: str) -> bool:
        """
        ハッシュの再作成が必要かチェック

        Args:
            hashed_password: 既存のハッシュ

        Returns:
            bool: 再ハッシュが必要かどうか
        """
        try:
            # ハッシュからコスト係数を抽出
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_cost = int(parts[2])
                return current_cost < cls.COST_FACTOR
        except (ValueError, IndexError):
            pass

        return True  # 解析できない場合は再ハッシュ推奨


class SecureTokenGenerator:
    """セキュアなトークン生成クラス"""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        暗号学的に安全なランダムトークンを生成

        Args:
            length: トークン長（バイト）

        Returns:
            str: hex形式のトークン
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_url_safe_token(length: int = 32) -> str:
        """
        URL安全なランダムトークンを生成

        Args:
            length: トークン長（バイト）

        Returns:
            str: URL安全なトークン
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_token(length: int = 6) -> str:
        """
        数字のみのトークンを生成（OTPなど用）

        Args:
            length: 桁数

        Returns:
            str: 数字のみのトークン
        """
        return ''.join(secrets.choice('0123456789') for _ in range(length))


def timing_safe_compare(a: str, b: str) -> bool:
    """
    タイミング攻撃耐性のある文字列比較

    Args:
        a: 比較する文字列1
        b: 比較する文字列2

    Returns:
        bool: 文字列が一致するかどうか
    """
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def rate_limit_decorator(max_attempts: int = 5, time_window: int = 300):
    """
    レート制限デコレータ（簡易版）

    Args:
        max_attempts: 最大試行回数
        time_window: 時間窓（秒）
    """
    def decorator(func):
        # メモリベースの簡易レート制限（本番ではRedisなど使用）
        attempts = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            # IPアドレスまたは何らかの識別子を取得（簡易版）
            client_id = kwargs.get('client_id', 'unknown')
            current_time = time.time()

            # 古いエントリを削除
            attempts[client_id] = [
                timestamp for timestamp in attempts.get(client_id, [])
                if current_time - timestamp < time_window
            ]

            # 制限チェック
            if len(attempts.get(client_id, [])) >= max_attempts:
                raise Exception("Rate limit exceeded")

            # 新しい試行を記録
            if client_id not in attempts:
                attempts[client_id] = []
            attempts[client_id].append(current_time)

            return func(*args, **kwargs)

        return wrapper
    return decorator


# 便利関数エクスポート
def validate_password(password: str) -> Tuple[bool, List[str]]:
    """パスワード強度検証（便利関数）"""
    return PasswordValidator.validate_password(password)


def hash_password(password: str) -> str:
    """パスワードハッシュ化（便利関数）"""
    return PasswordHasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """パスワード検証（便利関数）"""
    return PasswordHasher.verify_password(password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """セキュアトークン生成（便利関数）"""
    return SecureTokenGenerator.generate_token(length)