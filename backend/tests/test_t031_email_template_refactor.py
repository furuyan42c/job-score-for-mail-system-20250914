"""
T031 Email Template Creation - REFACTOR Phase (TDD)
リファクタリング検証: 改善されたコード品質とエラーハンドリング

このテストファイルはREFACTORフェーズで追加された機能を検証します：
1. エラーハンドリングの強化
2. データ検証の改善
3. パフォーマンス最適化
4. 新機能の追加
5. コード品質の向上
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch


class TestEmailTemplateRefactor:
    """T031 Email Template Generation - REFACTOR Phase Tests"""

    def test_enhanced_error_handling(self):
        """
        REFACTOR: エラーハンドリングの強化テスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError, SectionValidationError

        generator = EmailGenerator()

        # 無効なユーザーデータのテスト
        with pytest.raises(EmailValidationError) as exc_info:
            generator.generate_email({}, {})

        assert exc_info.value.error_code == "MISSING_USER_FIELD"
        assert "name" in str(exc_info.value)

        # 無効なセクションデータのテスト
        with pytest.raises(SectionValidationError) as exc_info:
            generator.generate_email(
                {"name": "テスト", "email": "test@example.com"},
                {"invalid_section": []}
            )

        assert exc_info.value.error_code == "MISSING_SECTIONS"

    def test_data_validation_improvements(self):
        """
        REFACTOR: データ検証の改善テスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError

        generator = EmailGenerator()

        # 有効なデータでのテスト
        user_data = {
            "name": "テストユーザー",
            "email": "test@example.com"
        }

        sections_data = {
            "editorial_picks": [
                {"title": "求人1", "company": "会社1", "hourly_wage": "2000", "score": "95.5"}
            ],
            "high_salary": [],
            "nearby": [],
            "popular": [],
            "new_jobs": [],
            "recommended": []
        }

        result = generator.generate_email(user_data, sections_data)

        # データ正規化の確認
        processed_job = result['template_vars']['sections']['editorial_picks'][0]
        assert isinstance(processed_job['hourly_wage'], int)
        assert processed_job['hourly_wage'] == 2000
        assert isinstance(processed_job['score'], (int, float))
        assert 0 <= processed_job['score'] <= 100

    def test_quality_score_calculation(self):
        """
        REFACTOR: 品質スコア計算機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "品質テスト", "email": "quality@test.com"}
        sections_data = {
            "editorial_picks": [{"title": "求人1", "company": "会社1"}],
            "high_salary": [{"title": "求人2", "company": "会社2"}],
            "nearby": [{"title": "求人3", "company": "会社3"}],
            "popular": [{"title": "求人4", "company": "会社4"}],
            "new_jobs": [{"title": "求人5", "company": "会社5"}],
            "recommended": [{"title": "求人6", "company": "会社6"}]
        }

        result = generator.generate_email(user_data, sections_data)

        assert 'quality_score' in result
        assert 0 <= result['quality_score'] <= 100
        assert isinstance(result['quality_score'], (int, float))

    def test_enhanced_metrics(self):
        """
        REFACTOR: 強化されたメトリクス機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "メトリクステスト", "email": "metrics@test.com"}
        sections_data = {section: [] for section in [
            "editorial_picks", "high_salary", "nearby",
            "popular", "new_jobs", "recommended"
        ]}

        # 複数回実行してメトリクスを蓄積
        for i in range(3):
            generator.generate_email(user_data, sections_data)

        metrics = generator.get_generation_metrics()

        assert metrics['total_generated'] == 3
        assert 'average_generation_time_ms' in metrics
        assert 'success_rate' in metrics
        assert 'errors' in metrics
        assert metrics['success_rate'] == 1.0  # 100%成功率

    def test_template_caching_improvements(self):
        """
        REFACTOR: テンプレートキャッシング改善のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "キャッシュテスト", "email": "cache@test.com"}
        sections_data = {section: [] for section in [
            "editorial_picks", "high_salary", "nearby",
            "popular", "new_jobs", "recommended"
        ]}

        # 初回実行（キャッシュミス）
        generator.generate_email(user_data, sections_data)

        # 2回目実行（キャッシュヒット）
        generator.generate_email(user_data, sections_data)

        metrics = generator.get_generation_metrics()

        assert metrics['cache_hits'] > 0
        assert metrics['cache_misses'] > 0
        assert metrics['cache_hit_ratio'] > 0

    def test_batch_email_generation(self):
        """
        REFACTOR: バッチメール生成機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        requests = [
            {
                'user_data': {"name": f"ユーザー{i}", "email": f"user{i}@test.com"},
                'sections_data': {section: [] for section in [
                    "editorial_picks", "high_salary", "nearby",
                    "popular", "new_jobs", "recommended"
                ]}
            }
            for i in range(3)
        ]

        result = generator.generate_email_batch(requests)

        assert 'results' in result
        assert result['total_requests'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0
        assert len(result['results']) == 3

        # 各結果の確認
        for i, email_result in enumerate(result['results']):
            assert email_result['batch_index'] == i
            assert email_result['batch_success'] is True
            assert 'html_content' in email_result

    def test_email_preview_generation(self):
        """
        REFACTOR: メールプレビュー生成機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "プレビューテスト", "email": "preview@test.com"}
        sections_data = {
            "editorial_picks": [{"title": f"求人{i}", "company": f"会社{i}"} for i in range(5)],
            "high_salary": [{"title": f"高給求人{i}", "company": f"高給会社{i}"} for i in range(3)],
            "nearby": [],
            "popular": [],
            "new_jobs": [],
            "recommended": []
        }

        preview = generator.preview_email(user_data, sections_data)

        assert 'html_preview' in preview
        assert 'preview_vars' in preview
        assert preview['full_sections_available'] == 6
        assert preview['preview_sections_shown'] == 2  # 最初の2セクション
        assert 'estimated_full_size' in preview

    def test_template_syntax_validation(self):
        """
        REFACTOR: テンプレート構文検証機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        validation_result = generator.validate_template_syntax("email_template.html")

        assert 'template_name' in validation_result
        assert validation_result['syntax_valid'] is True
        assert validation_result['render_test_passed'] is True
        assert 'required_variables' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result

    def test_accessibility_improvements(self):
        """
        REFACTOR: アクセシビリティ改善のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "アクセシビリティテスト", "email": "a11y@test.com"}
        sections_data = {
            "editorial_picks": [{"title": "アクセシブル求人", "company": "アクセシブル会社"}],
            "high_salary": [],
            "nearby": [],
            "popular": [],
            "new_jobs": [],
            "recommended": []
        }

        result = generator.generate_email(user_data, sections_data)
        html_content = result['html_content']

        # アクセシビリティ要素の確認
        accessibility_features = [
            'role="region"',
            'aria-labelledby=',
            'aria-label=',
            'id="editorial-picks-heading"',
            'lang="ja"'
        ]

        for feature in accessibility_features:
            assert feature in html_content, f"Accessibility feature '{feature}' should be present"

    def test_responsive_design_enhancements(self):
        """
        REFACTOR: レスポンシブデザイン強化のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "レスポンシブテスト", "email": "responsive@test.com"}
        sections_data = {section: [] for section in [
            "editorial_picks", "high_salary", "nearby",
            "popular", "new_jobs", "recommended"
        ]}

        result = generator.generate_email(user_data, sections_data)
        html_content = result['html_content']

        # レスポンシブ要素の確認
        responsive_features = [
            '@media only screen and (max-width: 600px)',
            '@media only screen and (max-width: 480px)',
            'width: 100% !important',
            'max-width: 100% !important',
            'viewport'
        ]

        for feature in responsive_features:
            assert feature in html_content, f"Responsive feature '{feature}' should be present"

    def test_error_recovery_and_logging(self):
        """
        REFACTOR: エラー回復とログ機能のテスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError

        # 無効なテンプレートパスで初期化
        with pytest.raises(EmailValidationError) as exc_info:
            EmailGenerator(template_path="/invalid/path")

        assert exc_info.value.error_code == "TEMPLATE_DIR_NOT_FOUND"

    def test_internationalization_framework(self):
        """
        REFACTOR: 国際化フレームワークのテスト
        """
        from services.email_generator import EmailGenerator, EmailValidationError

        generator = EmailGenerator()

        user_data = {"name": "国際化テスト", "email": "i18n@test.com"}
        sections_data = {section: [] for section in [
            "editorial_picks", "high_salary", "nearby",
            "popular", "new_jobs", "recommended"
        ]}

        # 日本語（サポート済み）
        result_ja = generator.generate_email_with_locale('ja', user_data, sections_data)
        assert 'html_content' in result_ja

        # 英語（準備中）
        with pytest.raises(EmailValidationError) as exc_info:
            generator.generate_email_with_locale('en', user_data, sections_data)
        assert exc_info.value.error_code == "LOCALE_NOT_IMPLEMENTED"

    def test_cache_management(self):
        """
        REFACTOR: キャッシュ管理機能のテスト
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        user_data = {"name": "キャッシュ管理テスト", "email": "cache-mgmt@test.com"}
        sections_data = {section: [] for section in [
            "editorial_picks", "high_salary", "nearby",
            "popular", "new_jobs", "recommended"
        ]}

        # テンプレートをキャッシュに読み込み
        generator.generate_email(user_data, sections_data)

        # キャッシュクリーンアップ
        cleanup_result = generator.cleanup_cache()

        assert cleanup_result['cache_cleared'] is True
        assert cleanup_result['templates_removed'] > 0
        assert cleanup_result['cache_size_after'] == 0

    def test_comprehensive_integration(self):
        """
        REFACTOR: 総合統合テスト - すべての改善機能
        """
        from services.email_generator import EmailGenerator

        generator = EmailGenerator()

        # 複雑なテストデータ
        user_data = {
            "name": "統合テストユーザー",
            "email": "integration@refactor.com",
            "cta_url": "https://custom.example.com/jobs",
            "unsubscribe_url": "https://custom.example.com/unsubscribe"
        }

        sections_data = {
            "editorial_picks": [
                {"title": "編集部求人", "company": "編集部会社", "hourly_wage": 2500, "score": 95.5}
            ],
            "high_salary": [
                {"title": "高給求人", "company": "高給会社", "hourly_wage": 3500, "score": 92.0}
            ],
            "nearby": [
                {"title": "近場求人", "company": "近場会社", "hourly_wage": 2000, "score": 88.5}
            ],
            "popular": [
                {"title": "人気求人", "company": "人気会社", "hourly_wage": 2200, "score": 89.0}
            ],
            "new_jobs": [
                {"title": "新着求人", "company": "新着会社", "hourly_wage": 1800, "score": 85.0}
            ],
            "recommended": [
                {"title": "おすすめ求人", "company": "おすすめ会社", "hourly_wage": 2300, "score": 91.0}
            ]
        }

        # メイン生成テスト
        result = generator.generate_email(user_data, sections_data)

        # すべての強化された機能を確認
        assert 'html_content' in result
        assert 'quality_score' in result
        assert 'sections_count' in result
        assert 'template_name' in result

        # 品質スコアが合理的な範囲内
        assert 70 <= result['quality_score'] <= 100

        # セクション数の確認
        assert result['sections_count']['editorial_picks'] == 1
        assert sum(result['sections_count'].values()) == 6

        # カスタムURLの確認
        assert "https://custom.example.com/jobs" in result['html_content']
        assert "https://custom.example.com/unsubscribe" in result['html_content']

        # メトリクスの確認
        metrics = generator.get_generation_metrics()
        assert metrics['total_generated'] > 0
        assert metrics['success_rate'] > 0

        # プレビュー機能の確認
        preview = generator.preview_email(user_data, sections_data)
        assert 'html_preview' in preview

        # テンプレート検証の確認
        validation = generator.validate_template_syntax("email_template.html")
        assert validation['syntax_valid'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])