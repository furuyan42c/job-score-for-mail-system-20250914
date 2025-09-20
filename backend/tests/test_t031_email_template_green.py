"""
T031 Email Template Creation - GREEN Phase (TDD)
テスト実行: メールテンプレート生成機能（6セクション構造）

GREEN Phaseテスト: 最小実装でテストをパス
"""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch


class TestEmailTemplateGenerationGreen:
    """T031 Email Template Generation - GREEN Phase Tests"""

    def test_email_generator_service_import(self):
        """
        GREEN: EmailGeneratorサービスクラスのインポートが成功すること
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_email')

    def test_email_template_file_structure(self):
        """
        GREEN: email_template.htmlファイルが6セクション構造を持つことを確認
        """
        template_path = "/Users/furuyanaoki/Project/new.mail.score/backend/templates/email_template.html"

        assert os.path.exists(template_path), "Email template file should exist"

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 6つのセクションが存在することを確認
        required_sections = [
            'editorial_picks',
            'high_salary',
            'nearby',
            'popular',
            'new_jobs',
            'recommended'
        ]

        for section in required_sections:
            assert section in content, f"Section '{section}' should exist in template"

    def test_generate_email_with_six_sections(self):
        """
        GREEN: 6セクション構造でメールを生成する機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        # テストデータ
        user_data = {
            "id": 1,
            "name": "田中太郎",
            "email": "tanaka@example.com",
            "preferences": {"location": "東京", "category": "IT"}
        }

        sections_data = {
            "editorial_picks": [
                {"title": "Webデザイナー", "company": "テスト会社1", "hourly_wage": 2000, "score": 95}
            ],
            "high_salary": [
                {"title": "システムエンジニア", "company": "テスト会社2", "hourly_wage": 3000, "score": 90}
            ],
            "nearby": [
                {"title": "データアナリスト", "company": "テスト会社3", "hourly_wage": 2500, "score": 85}
            ],
            "popular": [
                {"title": "プロジェクトマネージャー", "company": "テスト会社4", "hourly_wage": 2800, "score": 88}
            ],
            "new_jobs": [
                {"title": "フロントエンドエンジニア", "company": "テスト会社5", "hourly_wage": 2200, "score": 82}
            ],
            "recommended": [
                {"title": "バックエンドエンジニア", "company": "テスト会社6", "hourly_wage": 2600, "score": 87}
            ]
        }

        result = generator.generate_email(user_data, sections_data)

        # 生成結果の確認
        assert 'html_content' in result
        assert 'template_vars' in result
        assert 'size_bytes' in result
        assert 'generation_time_ms' in result
        assert result['size_bytes'] > 0
        assert result['generation_time_ms'] >= 0

    def test_email_template_responsive_design(self):
        """
        GREEN: レスポンシブデザインのCSSが含まれていることを確認
        """
        template_path = "/Users/furuyanaoki/Project/new.mail.score/backend/templates/email_template.html"

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # レスポンシブデザインの要素を確認
        responsive_elements = [
            'max-width',
            'viewport',
            '@media'
        ]

        for element in responsive_elements:
            assert element in content, f"Responsive element '{element}' should be present"

    def test_dynamic_content_insertion(self):
        """
        GREEN: 動的コンテンツ挿入機能のテスト
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        # 動的コンテンツのテスト
        template_vars = {
            "user_name": "テストユーザー",
            "greeting": "おはようございます",
            "cta_url": "https://example.com/jobs",
            "unsubscribe_url": "https://example.com/unsubscribe",
            "sections": {
                "editorial_picks": [],
                "high_salary": [],
                "nearby": [],
                "popular": [],
                "new_jobs": [],
                "recommended": []
            }
        }

        result = generator.insert_dynamic_content(template_vars)

        assert 'rendered_content' in result
        assert result['insertion_success'] is True
        assert 'variables_used' in result
        assert len(result['variables_used']) > 0

    def test_email_validation_structure(self):
        """
        GREEN: 生成されたメールの構造検証機能のテスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError
        generator = EmailGenerator()

        # 正しい構造のテストデータ
        valid_data = {
            "sections": {
                "editorial_picks": [],
                "high_salary": [],
                "nearby": [],
                "popular": [],
                "new_jobs": [],
                "recommended": []
            }
        }

        # バリデーションが成功することを確認
        result = generator.validate_email_structure(valid_data)
        assert result is True

        # 不正な構造のテストデータ
        invalid_data = {"invalid": "structure"}

        # バリデーションが失敗することを確認
        with pytest.raises(EmailValidationError):
            generator.validate_email_structure(invalid_data)

    def test_email_size_calculation(self):
        """
        GREEN: メールサイズ計算機能のテスト
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        html_content = "<html><body>Test content</body></html>"
        size = generator.calculate_email_size(html_content)

        assert isinstance(size, int)
        assert size > 0
        assert size == len(html_content.encode('utf-8'))

    def test_email_performance_metrics(self):
        """
        GREEN: メール生成パフォーマンスメトリクスのテスト
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        metrics = generator.get_generation_metrics()

        assert 'total_generated' in metrics
        assert 'average_generation_time_ms' in metrics
        assert 'cache_hits' in metrics
        assert 'cache_misses' in metrics
        assert 'cache_hit_ratio' in metrics
        assert isinstance(metrics['total_generated'], int)

    def test_template_caching_mechanism(self):
        """
        GREEN: テンプレートキャッシュ機能のテスト
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        cache_status = generator.get_template_cache_status()

        assert 'cached_templates' in cache_status
        assert 'cache_size' in cache_status
        assert 'cache_enabled' in cache_status
        assert cache_status['cache_enabled'] is True

    def test_email_snapshot_comparison(self):
        """
        GREEN: スナップショットテスト機能の基本動作
        """
        # スナップショットディレクトリが存在することを確認
        snapshot_dir = "/Users/furuyanaoki/Project/new.mail.score/backend/tests/snapshots"
        assert os.path.exists(snapshot_dir), "Snapshot directory should exist"

        # テンプレート生成のテスト
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        test_data = {
            "name": "スナップショットテスト",
            "email": "snapshot@test.com"
        }
        sections_data = {
            "editorial_picks": [
                {"title": "テスト求人", "company": "テスト会社", "hourly_wage": 1500, "score": 80}
            ],
            "high_salary": [],
            "nearby": [],
            "popular": [],
            "new_jobs": [],
            "recommended": []
        }

        result = generator.generate_email(test_data, sections_data)
        assert 'html_content' in result

    def test_email_template_syntax_validation(self):
        """
        GREEN: Jinja2テンプレート構文の妥当性検証
        """
        from jinja2 import Template

        template_path = "/Users/furuyanaoki/Project/new.mail.score/backend/templates/email_template.html"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Jinja2テンプレートとして解析可能かテスト
        template = Template(template_content)

        # テスト用のコンテキスト
        test_context = {
            'user_name': 'テスト',
            'greeting': 'こんにちは',
            'user_email': 'test@example.com',
            'sections': {
                'editorial_picks': [],
                'high_salary': [],
                'nearby': [],
                'popular': [],
                'new_jobs': [],
                'recommended': []
            },
            'cta_url': 'http://example.com',
            'unsubscribe_url': 'http://example.com/unsubscribe'
        }

        # レンダリングテスト
        rendered = template.render(test_context)
        assert len(rendered) > 0

    def test_email_accessibility_features(self):
        """
        GREEN: アクセシビリティ機能の基本実装
        """
        template_path = "/Users/furuyanaoki/Project/new.mail.score/backend/templates/email_template.html"

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 基本的なアクセシビリティ要素をチェック
        assert 'lang=' in content, "Language attribute should be present"
        assert 'role=' in content, "ARIA roles should be present"
        assert 'aria-label' in content, "ARIA labels should be present"

    def test_email_internationalization_basic(self):
        """
        GREEN: 国際化（i18n）基本サポートのテスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError
        generator = EmailGenerator()

        # 日本語ロケールのテスト（サポートされている）
        try:
            result = generator.generate_email_with_locale(
                'ja',
                {"name": "テスト", "email": "test@example.com"},
                {
                    "editorial_picks": [],
                    "high_salary": [],
                    "nearby": [],
                    "popular": [],
                    "new_jobs": [],
                    "recommended": []
                }
            )
            assert 'html_content' in result
        except Exception as e:
            pytest.fail(f"Japanese locale should be supported: {e}")

        # 未サポートのロケールのテスト
        with pytest.raises(EmailValidationError):
            generator.generate_email_with_locale('en', {}, {})

    def test_integration_email_generation_full_cycle(self):
        """
        GREEN: 統合テスト - フル機能でのメール生成
        """
        from services.email_generator import EmailGenerator
        generator = EmailGenerator()

        # 完全なテストデータ
        user_data = {
            "id": 1,
            "name": "統合テストユーザー",
            "email": "integration@test.com",
            "preferences": {
                "location": "東京都",
                "category": "IT・エンジニア",
                "salary_min": 1500
            }
        }

        sections_data = {
            "editorial_picks": [
                {"title": "編集部おすすめ求人", "company": "編集部会社", "hourly_wage": 2500, "score": 98}
            ],
            "high_salary": [
                {"title": "高給与求人", "company": "高給会社", "hourly_wage": 3500, "score": 92}
            ],
            "nearby": [
                {"title": "近場求人", "company": "近場会社", "hourly_wage": 2000, "score": 85}
            ],
            "popular": [
                {"title": "人気求人", "company": "人気会社", "hourly_wage": 2200, "score": 88}
            ],
            "new_jobs": [
                {"title": "新着求人", "company": "新着会社", "hourly_wage": 1800, "score": 78}
            ],
            "recommended": [
                {"title": "おすすめ求人", "company": "おすすめ会社", "hourly_wage": 2300, "score": 89}
            ]
        }

        # メール生成実行
        result = generator.generate_email(user_data, sections_data)

        # 結果検証
        assert 'html_content' in result
        assert 'template_vars' in result
        assert 'size_bytes' in result
        assert 'generation_time_ms' in result

        # HTML内容の確認
        html = result['html_content']
        assert '統合テストユーザー' in html
        assert '編集部おすすめ求人' in html
        assert '高給与求人' in html
        assert '近場求人' in html
        assert '人気求人' in html
        assert '新着求人' in html
        assert 'おすすめ求人' in html

        # パフォーマンス確認
        assert result['generation_time_ms'] < 5000  # 5秒以内
        assert result['size_bytes'] > 1000  # 1KB以上


if __name__ == "__main__":
    pytest.main([__file__, "-v"])