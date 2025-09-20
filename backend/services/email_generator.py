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
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
from jinja2 import Template, FileSystemLoader, Environment, TemplateNotFound
from dataclasses import dataclass, field


@dataclass
class EmailGenerationMetrics:
    """メール生成メトリクス"""
    total_generated: int = 0
    generation_times: List[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0

    @property
    def average_generation_time(self) -> float:
        """平均生成時間（ミリ秒）"""
        return sum(self.generation_times) / len(self.generation_times) if self.generation_times else 0.0

    @property
    def cache_hit_ratio(self) -> float:
        """キャッシュヒット率"""
        total_requests = self.cache_hits + self.cache_misses
        return self.cache_hits / total_requests if total_requests > 0 else 0.0


class EmailValidationError(Exception):
    """メールバリデーションエラー"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = datetime.now().isoformat()


class TemplateRenderError(EmailValidationError):
    """テンプレートレンダリングエラー"""
    pass


class SectionValidationError(EmailValidationError):
    """セクションバリデーションエラー"""
    pass


class EmailGenerator:
    """メールテンプレート生成サービス"""

    def __init__(self, template_path: Optional[str] = None, cache_size: int = 100):
        # パスの設定
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = Path(__file__).parent.parent / "templates"

        # パスの検証
        if not self.template_path.exists():
            raise EmailValidationError(
                f"Template directory does not exist: {self.template_path}",
                "TEMPLATE_DIR_NOT_FOUND"
            )

        # キャッシュ設定
        self.template_cache = {}
        self.cache_size = cache_size

        # メトリクス
        self.metrics = EmailGenerationMetrics()

        # ロガー設定
        self.logger = logging.getLogger(__name__)

        # 必須セクション定義
        self.required_sections = {
            'editorial_picks', 'high_salary', 'nearby',
            'popular', 'new_jobs', 'recommended'
        }

        # Jinja2環境の設定
        try:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_path)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
            # カスタムフィルターの追加
            self.env.filters['currency'] = self._format_currency
            self.env.filters['truncate_smart'] = self._truncate_smart
        except Exception as e:
            raise EmailValidationError(
                f"Failed to initialize Jinja2 environment: {str(e)}",
                "JINJA_INIT_ERROR"
            )

    def generate_email(self, user_data: Dict[str, Any], sections_data: Dict[str, List[Dict[str, Any]]],
                      template_name: str = "email_template.html") -> Dict[str, Any]:
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
            # 入力データのバリデーション
            self._validate_user_data(user_data)
            self._validate_sections_data(sections_data)

            # テンプレートの読み込み
            template = self._get_template(template_name)

            # セクションデータの前処理
            processed_sections = self._process_sections_data(sections_data)

            # テンプレート変数の準備
            template_vars = self._prepare_template_vars(user_data, processed_sections)

            # HTMLレンダリング
            html_content = self._render_template(template, template_vars)

            # 後処理とメトリクス更新
            generation_time = (time.time() - start_time) * 1000
            self._update_metrics(generation_time, success=True)

            # 結果の構築
            result = {
                "html_content": html_content,
                "template_vars": template_vars,
                "size_bytes": self.calculate_email_size(html_content),
                "generation_time_ms": generation_time,
                "timestamp": datetime.now().isoformat(),
                "template_name": template_name,
                "sections_count": {k: len(v) for k, v in sections_data.items()},
                "quality_score": self._calculate_quality_score(html_content, sections_data)
            }

            self.logger.info(f"Email generated successfully for user {user_data.get('name', 'unknown')}")
            return result

        except EmailValidationError:
            self._update_metrics(0, success=False)
            raise
        except Exception as e:
            self._update_metrics(0, success=False)
            self.logger.error(f"Unexpected error in email generation: {str(e)}")
            raise EmailValidationError(
                f"Email generation failed due to unexpected error: {str(e)}",
                "UNEXPECTED_ERROR"
            )

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
        return {
            "total_generated": self.metrics.total_generated,
            "average_generation_time_ms": round(self.metrics.average_generation_time, 2),
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_ratio": round(self.metrics.cache_hit_ratio, 3),
            "errors": self.metrics.errors,
            "success_rate": round(
                self.metrics.total_generated / max(1, self.metrics.total_generated + self.metrics.errors),
                3
            ),
            "last_updated": datetime.now().isoformat()
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
        ロケール対応メール生成

        Args:
            locale: ロケール（ja, en, zh等）
            user_data: ユーザーデータ
            sections_data: セクションデータ

        Returns:
            Dict[str, Any]: 生成結果
        """
        supported_locales = {
            'ja': 'email_template.html',
            'en': 'email_template_en.html',  # 将来の拡張用
        }

        if locale not in supported_locales:
            self.logger.warning(f"Unsupported locale '{locale}', falling back to 'ja'")
            locale = 'ja'

        template_name = supported_locales[locale]

        # ロケール固有の処理
        if locale == 'ja':
            return self.generate_email(user_data, sections_data, template_name)
        else:
            # 将来の拡張: 他言語対応
            raise EmailValidationError(
                f"Locale '{locale}' is not fully implemented yet",
                "LOCALE_NOT_IMPLEMENTED"
            )

    def generate_email_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        バッチメール生成

        Args:
            requests: 生成リクエストのリスト

        Returns:
            List[Dict[str, Any]]: 生成結果のリスト
        """
        results = []
        start_time = time.time()

        for i, request in enumerate(requests):
            try:
                user_data = request.get('user_data', {})
                sections_data = request.get('sections_data', {})
                template_name = request.get('template_name', 'email_template.html')

                result = self.generate_email(user_data, sections_data, template_name)
                result['batch_index'] = i
                result['batch_success'] = True
                results.append(result)

            except Exception as e:
                self.logger.error(f"Batch generation failed for request {i}: {str(e)}")
                results.append({
                    'batch_index': i,
                    'batch_success': False,
                    'error': str(e),
                    'error_code': getattr(e, 'error_code', 'BATCH_GENERATION_ERROR'),
                    'timestamp': datetime.now().isoformat()
                })

        total_time = (time.time() - start_time) * 1000

        return {
            'results': results,
            'total_requests': len(requests),
            'successful': sum(1 for r in results if r.get('batch_success', False)),
            'failed': sum(1 for r in results if not r.get('batch_success', False)),
            'total_time_ms': total_time,
            'average_time_per_email': total_time / len(requests) if requests else 0
        }

    def preview_email(self, user_data: Dict[str, Any], sections_data: Dict[str, Any],
                     template_name: str = "email_template.html") -> Dict[str, Any]:
        """
        メールプレビュー生成（実際の送信なし）

        Args:
            user_data: ユーザーデータ
            sections_data: セクションデータ
            template_name: テンプレート名

        Returns:
            Dict[str, Any]: プレビュー情報
        """
        try:
            # プレビュー用の軽量生成
            template = self._get_template(template_name)
            template_vars = self._prepare_template_vars(user_data, sections_data)

            # プレビュー用の短縮HTML（最初の2セクションのみ）
            preview_sections = {}
            section_names = list(sections_data.keys())
            for section_name in section_names[:2]:  # 最初の2セクションのみ
                preview_sections[section_name] = sections_data[section_name][:2]  # 各セクション2件まで

            preview_vars = template_vars.copy()
            preview_vars['sections'] = preview_sections
            preview_vars['is_preview'] = True

            html_preview = template.render(preview_vars)

            return {
                'html_preview': html_preview,
                'preview_vars': preview_vars,
                'full_sections_available': len(sections_data),
                'preview_sections_shown': len(preview_sections),
                'estimated_full_size': self.calculate_email_size(html_preview) * 3,  # 概算
                'preview_generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            raise EmailValidationError(
                f"Preview generation failed: {str(e)}",
                "PREVIEW_GENERATION_ERROR"
            )

    def validate_template_syntax(self, template_name: str) -> Dict[str, Any]:
        """
        テンプレート構文の詳細検証

        Args:
            template_name: 検証するテンプレート名

        Returns:
            Dict[str, Any]: 検証結果
        """
        validation_result = {
            'template_name': template_name,
            'syntax_valid': False,
            'required_variables': [],
            'optional_variables': [],
            'missing_variables': [],
            'render_test_passed': False,
            'errors': [],
            'warnings': []
        }

        try:
            template = self._get_template(template_name)

            # 必須変数の定義
            required_vars = {
                'user_name', 'greeting', 'user_email', 'sections',
                'cta_url', 'unsubscribe_url'
            }

            # テスト用のコンテキスト
            test_context = {
                'user_name': 'テストユーザー',
                'greeting': 'こんにちは',
                'user_email': 'test@example.com',
                'sections': {section: [] for section in self.required_sections},
                'cta_url': 'http://example.com',
                'unsubscribe_url': 'http://example.com/unsubscribe',
                'generated_at': '2025年1月1日',
                'total_jobs': 0
            }

            # レンダリングテスト
            rendered = template.render(test_context)
            validation_result['syntax_valid'] = True
            validation_result['render_test_passed'] = True

            # 変数使用状況の分析
            template_source = template.source if hasattr(template, 'source') else ""
            validation_result['required_variables'] = list(required_vars)

            # 基本的な品質チェック
            if len(rendered) < 1000:
                validation_result['warnings'].append("Generated HTML seems too short")

            if '@media' not in rendered:
                validation_result['warnings'].append("No responsive design detected")

        except Exception as e:
            validation_result['errors'].append(str(e))
            validation_result['syntax_valid'] = False

        return validation_result

    def cleanup_cache(self) -> Dict[str, Any]:
        """
        キャッシュクリーンアップ

        Returns:
            Dict[str, Any]: クリーンアップ結果
        """
        cache_size_before = len(self.template_cache)
        self.template_cache.clear()

        return {
            'cache_cleared': True,
            'templates_removed': cache_size_before,
            'cache_size_after': 0,
            'cleanup_timestamp': datetime.now().isoformat()
        }

    def _get_template(self, template_name: str) -> Template:
        """
        テンプレート取得（キャッシュ機能付き）

        Args:
            template_name: テンプレート名

        Returns:
            Template: Jinja2テンプレート
        """
        if template_name in self.template_cache:
            self.metrics.cache_hits += 1
            return self.template_cache[template_name]

        try:
            template = self.env.get_template(template_name)

            # キャッシュサイズ管理
            self._manage_cache()
            self.template_cache[template_name] = template
            self.metrics.cache_misses += 1

            self.logger.debug(f"Template '{template_name}' loaded and cached")
            return template

        except TemplateNotFound:
            raise EmailValidationError(
                f"Template '{template_name}' not found in {self.template_path}",
                "TEMPLATE_NOT_FOUND"
            )
        except Exception as e:
            raise EmailValidationError(
                f"Failed to load template '{template_name}': {str(e)}",
                "TEMPLATE_LOAD_ERROR"
            )

    def _validate_user_data(self, user_data: Dict[str, Any]) -> None:
        """ユーザーデータの妥当性検証"""
        if not isinstance(user_data, dict):
            raise EmailValidationError("User data must be a dictionary", "INVALID_USER_DATA")

        required_fields = ["name", "email"]
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise EmailValidationError(f"Required field '{field}' is missing or empty", "MISSING_USER_FIELD")

        # Email形式の簡単な検証
        email = user_data.get("email", "")
        if "@" not in email or "." not in email:
            raise EmailValidationError("Invalid email format", "INVALID_EMAIL_FORMAT")

    def _validate_sections_data(self, sections_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """セクションデータの妥当性検証"""
        if not isinstance(sections_data, dict):
            raise SectionValidationError("Sections data must be a dictionary", "INVALID_SECTIONS_TYPE")

        # 必須セクションの確認
        missing_sections = self.required_sections - set(sections_data.keys())
        if missing_sections:
            raise SectionValidationError(
                f"Missing required sections: {missing_sections}",
                "MISSING_SECTIONS"
            )

        # 各セクションのデータ構造を検証
        for section_name, jobs in sections_data.items():
            if not isinstance(jobs, list):
                raise SectionValidationError(
                    f"Section '{section_name}' must be a list",
                    "INVALID_SECTION_TYPE"
                )

            for i, job in enumerate(jobs):
                if not isinstance(job, dict):
                    raise SectionValidationError(
                        f"Job {i} in section '{section_name}' must be a dictionary",
                        "INVALID_JOB_TYPE"
                    )

                required_job_fields = ["title", "company"]
                for field in required_job_fields:
                    if field not in job:
                        raise SectionValidationError(
                            f"Job {i} in section '{section_name}' missing required field '{field}'",
                            "MISSING_JOB_FIELD"
                        )

    def _process_sections_data(self, sections_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """セクションデータの前処理"""
        processed = {}

        for section_name, jobs in sections_data.items():
            processed_jobs = []

            for job in jobs:
                processed_job = job.copy()

                # デフォルト値の設定
                processed_job.setdefault("hourly_wage", 0)
                processed_job.setdefault("score", 0)
                processed_job.setdefault("location", "未指定")

                # データの正規化
                if "hourly_wage" in processed_job:
                    try:
                        processed_job["hourly_wage"] = int(processed_job["hourly_wage"])
                    except (ValueError, TypeError):
                        processed_job["hourly_wage"] = 0

                if "score" in processed_job:
                    try:
                        score = float(processed_job["score"])
                        processed_job["score"] = max(0, min(100, score))  # 0-100の範囲に制限
                    except (ValueError, TypeError):
                        processed_job["score"] = 0

                processed_jobs.append(processed_job)

            # セクションごとの制限（最大5件）
            processed[section_name] = processed_jobs[:5]

        return processed

    def _prepare_template_vars(self, user_data: Dict[str, Any], sections_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """テンプレート変数の準備"""
        # 時刻による挨拶の決定
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "おはようございます"
        elif 12 <= current_hour < 18:
            greeting = "こんにちは"
        else:
            greeting = "こんばんは"

        return {
            "user_name": user_data["name"],
            "greeting": greeting,
            "user_email": user_data["email"],
            "sections": sections_data,
            "cta_url": user_data.get("cta_url", "https://example.com/jobs"),
            "unsubscribe_url": user_data.get("unsubscribe_url", "https://example.com/unsubscribe"),
            "generated_at": datetime.now().strftime("%Y年%m月%d日"),
            "total_jobs": sum(len(jobs) for jobs in sections_data.values())
        }

    def _render_template(self, template: Template, template_vars: Dict[str, Any]) -> str:
        """テンプレートのレンダリング"""
        try:
            return template.render(template_vars)
        except Exception as e:
            raise TemplateRenderError(
                f"Template rendering failed: {str(e)}",
                "TEMPLATE_RENDER_ERROR"
            )

    def _calculate_quality_score(self, html_content: str, sections_data: Dict[str, List[Dict[str, Any]]]) -> float:
        """メール品質スコアの計算"""
        score = 0.0

        # HTML長さによるスコア (適切な長さ: 5KB - 50KB)
        content_length = len(html_content.encode('utf-8'))
        if 5000 <= content_length <= 50000:
            score += 25.0
        elif content_length < 5000:
            score += (content_length / 5000) * 25.0
        else:
            score += max(0, 25.0 - (content_length - 50000) / 1000)

        # セクション充実度によるスコア
        total_jobs = sum(len(jobs) for jobs in sections_data.values())
        if total_jobs >= 6:  # 各セクション1件以上
            score += 25.0
        else:
            score += (total_jobs / 6) * 25.0

        # セクションバランスによるスコア
        section_counts = [len(jobs) for jobs in sections_data.values() if len(jobs) > 0]
        if section_counts:
            balance_score = 1.0 - (max(section_counts) - min(section_counts)) / max(section_counts)
            score += balance_score * 25.0

        # 基本的な品質チェック
        quality_indicators = [
            "viewport" in html_content,  # レスポンシブ対応
            "@media" in html_content,    # メディアクエリ
            "role=" in html_content,     # アクセシビリティ
            "aria-" in html_content      # ARIA属性
        ]
        score += sum(quality_indicators) * 6.25  # 25.0 / 4

        return min(100.0, score)

    def _format_currency(self, value: Union[int, float]) -> str:
        """通貨フォーマット（カスタムフィルター）"""
        try:
            return f"¥{int(value):,}"
        except (ValueError, TypeError):
            return "¥0"

    def _truncate_smart(self, text: str, length: int = 50) -> str:
        """スマートな文字列切り詰め（カスタムフィルター）"""
        if len(text) <= length:
            return text
        return text[:length-3] + "..."

    def _update_metrics(self, generation_time: float, success: bool = True) -> None:
        """メトリクス更新"""
        if success:
            self.metrics.total_generated += 1
            self.metrics.generation_times.append(generation_time)

            # 履歴を最大100件に制限
            if len(self.metrics.generation_times) > 100:
                self.metrics.generation_times = self.metrics.generation_times[-100:]
        else:
            self.metrics.errors += 1

    def _manage_cache(self) -> None:
        """キャッシュサイズ管理"""
        if len(self.template_cache) > self.cache_size:
            # LRU風の削除（実装を簡略化）
            oldest_key = next(iter(self.template_cache))
            del self.template_cache[oldest_key]


# シングルトンインスタンス
email_generator = EmailGenerator()