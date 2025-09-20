"""
T031 Email Generator Service - GREEN Phase (TDD)
メールテンプレート生成サービス（6セクション構造）

この実装は最小限のテストパス条件を満たします：
1. 6セクション構造のメールテンプレート生成
2. 動的コンテンツ挿入
3. HTML妥当性検証
4. 基本的なエラーハンドリング
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template, FileSystemLoader, Environment


class EmailValidationError(Exception):
    """メールバリデーションエラー"""
    pass


class EmailGenerator:
    """メールテンプレート生成サービス"""

    def __init__(self):
        self.template_path = "/Users/furuyanaoki/Project/new.mail.score/backend/templates"
        self.template_cache = {}
        self.generation_metrics = {
            "total_generated": 0,
            "generation_time_ms": [],
            "cache_hits": 0,
            "cache_misses": 0
        }

        # Jinja2環境の設定
        self.env = Environment(
            loader=FileSystemLoader(self.template_path),
            autoescape=True
        )

    def generate_email(self, user_data: Dict[str, Any], sections_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        6セクション構造でメールを生成する

        Args:
            user_data: ユーザー情報
            sections_data: 6セクション分のデータ

        Returns:
            Dict[str, Any]: 生成されたメール情報
        """
        start_time = time.time()

        try:
            # テンプレートの読み込み
            template = self._get_template("email_template.html")

            # テンプレート変数の準備
            template_vars = {
                "user_name": user_data.get("name", "ユーザー"),
                "greeting": "こんにちは",
                "user_email": user_data.get("email", ""),
                "sections": sections_data,
                "cta_url": "https://example.com/jobs",
                "unsubscribe_url": "https://example.com/unsubscribe"
            }

            # HTMLレンダリング
            html_content = template.render(template_vars)

            # メールサイズ計算
            email_size = self.calculate_email_size(html_content)

            # 生成メトリクスの更新
            generation_time = (time.time() - start_time) * 1000
            self._update_metrics(generation_time)

            return {
                "html_content": html_content,
                "template_vars": template_vars,
                "size_bytes": email_size,
                "generation_time_ms": generation_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise EmailValidationError(f"Email generation failed: {str(e)}")

    def insert_dynamic_content(self, template_vars: Dict[str, Any]) -> Dict[str, Any]:
        """
        動的コンテンツ挿入

        Args:
            template_vars: テンプレート変数

        Returns:
            Dict[str, Any]: 動的コンテンツ挿入結果
        """
        try:
            template = self._get_template("email_template.html")
            rendered_content = template.render(template_vars)

            return {
                "rendered_content": rendered_content,
                "variables_used": list(template_vars.keys()),
                "content_length": len(rendered_content),
                "insertion_success": True
            }

        except Exception as e:
            return {
                "error": str(e),
                "insertion_success": False
            }

    def validate_email_structure(self, email_data: Dict[str, Any]) -> bool:
        """
        メール構造の妥当性検証

        Args:
            email_data: 検証対象のメールデータ

        Returns:
            bool: 妥当性検証結果
        """
        if not isinstance(email_data, dict):
            raise EmailValidationError("Email data must be a dictionary")

        required_sections = [
            'editorial_picks', 'high_salary', 'nearby',
            'popular', 'new_jobs', 'recommended'
        ]

        # セクションデータが存在するかチェック
        sections = email_data.get('sections', {})
        if not isinstance(sections, dict):
            raise EmailValidationError("Sections must be a dictionary")

        missing_sections = []
        for section in required_sections:
            if section not in sections:
                missing_sections.append(section)

        if missing_sections:
            raise EmailValidationError(f"Missing required sections: {missing_sections}")

        return True

    def calculate_email_size(self, html_content: str) -> int:
        """
        メールサイズ計算

        Args:
            html_content: HTMLコンテンツ

        Returns:
            int: サイズ（バイト）
        """
        if not isinstance(html_content, str):
            raise EmailValidationError("HTML content must be a string")

        return len(html_content.encode('utf-8'))

    def get_generation_metrics(self) -> Dict[str, Any]:
        """
        メール生成パフォーマンスメトリクス取得

        Returns:
            Dict[str, Any]: メトリクス情報
        """
        avg_time = (
            sum(self.generation_metrics["generation_time_ms"]) /
            len(self.generation_metrics["generation_time_ms"])
        ) if self.generation_metrics["generation_time_ms"] else 0

        return {
            "total_generated": self.generation_metrics["total_generated"],
            "average_generation_time_ms": round(avg_time, 2),
            "cache_hits": self.generation_metrics["cache_hits"],
            "cache_misses": self.generation_metrics["cache_misses"],
            "cache_hit_ratio": (
                self.generation_metrics["cache_hits"] /
                max(1, self.generation_metrics["cache_hits"] + self.generation_metrics["cache_misses"])
            )
        }

    def get_template_cache_status(self) -> Dict[str, Any]:
        """
        テンプレートキャッシュ状態取得

        Returns:
            Dict[str, Any]: キャッシュ状態
        """
        return {
            "cached_templates": list(self.template_cache.keys()),
            "cache_size": len(self.template_cache),
            "cache_enabled": True,
            "last_updated": datetime.now().isoformat()
        }

    def generate_email_with_locale(self, locale: str, user_data: Dict[str, Any], sections_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ロケール対応メール生成（最小実装）

        Args:
            locale: ロケール（ja, en, zh等）
            user_data: ユーザーデータ
            sections_data: セクションデータ

        Returns:
            Dict[str, Any]: 生成結果
        """
        # 最小実装：日本語のみサポート
        if locale != 'ja':
            raise EmailValidationError(f"Locale '{locale}' not supported yet")

        return self.generate_email(user_data, sections_data)

    def _get_template(self, template_name: str) -> Template:
        """
        テンプレート取得（キャッシュ機能付き）

        Args:
            template_name: テンプレート名

        Returns:
            Template: Jinja2テンプレート
        """
        if template_name in self.template_cache:
            self.generation_metrics["cache_hits"] += 1
            return self.template_cache[template_name]

        try:
            template = self.env.get_template(template_name)
            self.template_cache[template_name] = template
            self.generation_metrics["cache_misses"] += 1
            return template

        except Exception as e:
            raise EmailValidationError(f"Template '{template_name}' not found: {str(e)}")

    def _update_metrics(self, generation_time: float) -> None:
        """
        メトリクス更新

        Args:
            generation_time: 生成時間（ミリ秒）
        """
        self.generation_metrics["total_generated"] += 1
        self.generation_metrics["generation_time_ms"].append(generation_time)

        # メトリクス履歴を最大100件に制限
        if len(self.generation_metrics["generation_time_ms"]) > 100:
            self.generation_metrics["generation_time_ms"] = \
                self.generation_metrics["generation_time_ms"][-100:]


# シングルトンインスタンス
email_generator = EmailGenerator()