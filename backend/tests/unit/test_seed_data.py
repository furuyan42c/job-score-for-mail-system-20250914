"""
マスターデータ投入スクリプトのユニットテスト
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# テスト対象のモジュールをインポート
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.seed_master_data import (
    PREFECTURE_DATA,
    CITY_DATA,
    OCCUPATION_DATA,
    EMPLOYMENT_TYPE_DATA,
    FEATURE_DATA,
    SEMRUSH_KEYWORDS_DATA,
    insert_prefecture_data,
    insert_city_data,
    insert_occupation_data,
    insert_employment_type_data,
    insert_feature_data,
    insert_semrush_keywords_data,
    verify_data
)


class TestMasterData:
    """マスターデータの妥当性テスト"""

    def test_prefecture_data_completeness(self):
        """47都道府県が全て定義されているか"""
        assert len(PREFECTURE_DATA) == 47, "都道府県は47個必要"

        # 都道府県コードの重複チェック
        codes = [p['code'] for p in PREFECTURE_DATA]
        assert len(codes) == len(set(codes)), "都道府県コードに重複がある"

        # 必須フィールドの存在確認
        for pref in PREFECTURE_DATA:
            assert 'code' in pref
            assert 'name' in pref
            assert 'region' in pref
            assert 'sort_order' in pref

    def test_city_data_structure(self):
        """市区町村データの構造が正しいか"""
        assert len(CITY_DATA) > 0, "市区町村データが存在しない"

        for city in CITY_DATA:
            assert 'code' in city
            assert 'pref_cd' in city
            assert 'name' in city
            assert 'latitude' in city
            assert 'longitude' in city

            # 都道府県コードの妥当性
            assert len(city['pref_cd']) == 2
            assert city['pref_cd'] in [p['code'] for p in PREFECTURE_DATA]

            # 緯度経度の範囲チェック
            assert 20 <= city['latitude'] <= 46, f"緯度が日本の範囲外: {city['latitude']}"
            assert 120 <= city['longitude'] <= 150, f"経度が日本の範囲外: {city['longitude']}"

    def test_occupation_data_validity(self):
        """職種データの妥当性"""
        assert len(OCCUPATION_DATA) >= 10, "職種は最低10個必要"

        # コードの重複チェック
        codes = [o['code'] for o in OCCUPATION_DATA]
        assert len(codes) == len(set(codes)), "職種コードに重複がある"

        # display_orderの連続性
        orders = sorted([o['display_order'] for o in OCCUPATION_DATA])
        assert orders == list(range(1, len(OCCUPATION_DATA) + 1)), "display_orderが連続していない"

    def test_employment_type_data_validity(self):
        """雇用形態データの妥当性"""
        assert len(EMPLOYMENT_TYPE_DATA) >= 5, "雇用形態は最低5個必要"

        # マッチング対象の確認（アルバイト、パート、日雇い）
        matching_types = [e for e in EMPLOYMENT_TYPE_DATA if e['is_valid_for_matching']]
        assert len(matching_types) >= 2, "マッチング対象の雇用形態が少なすぎる"

        # アルバイトとパートが含まれているか
        type_names = [e['name'] for e in EMPLOYMENT_TYPE_DATA]
        assert 'アルバイト' in type_names, "アルバイトが含まれていない"
        assert 'パート' in type_names, "パートが含まれていない"

    def test_feature_data_structure(self):
        """特徴データの構造確認"""
        assert len(FEATURE_DATA) >= 20, "特徴は最低20個必要"

        # feature_codeのフォーマット確認（F + 数字2桁）
        for feature in FEATURE_DATA:
            assert feature['feature_code'].startswith('F'), f"不正なfeature_code: {feature['feature_code']}"
            assert len(feature['feature_code']) == 3, f"feature_codeの長さが不正: {feature['feature_code']}"

        # カテゴリの確認
        categories = set(f['category'] for f in FEATURE_DATA)
        expected_categories = {'給与・待遇', '勤務条件', 'シフト・時間', '立地・環境', '待遇・福利厚生'}
        assert expected_categories.issubset(categories), f"必須カテゴリが不足: {expected_categories - categories}"

    def test_semrush_keywords_validity(self):
        """SEMRUSHキーワードデータの妥当性"""
        assert len(SEMRUSH_KEYWORDS_DATA) >= 5, "キーワードは最低5個必要"

        for keyword in SEMRUSH_KEYWORDS_DATA:
            assert 'keyword' in keyword
            assert 'search_volume' in keyword
            assert 'keyword_difficulty' in keyword
            assert 'intent' in keyword
            assert 'category' in keyword

            # 数値の範囲チェック
            assert keyword['search_volume'] > 0, f"検索ボリュームが0以下: {keyword['keyword']}"
            assert 0 <= keyword['keyword_difficulty'] <= 100, f"難易度が範囲外: {keyword['keyword_difficulty']}"
            assert keyword['intent'] in ['Commercial', 'Informational', 'Transactional', 'Navigational']


@pytest.mark.asyncio
class TestDataInsertionFunctions:
    """データ投入関数のテスト"""

    async def test_insert_prefecture_data(self):
        """都道府県データ投入のテスト"""
        mock_session = AsyncMock()

        await insert_prefecture_data(mock_session)

        # TRUNCATEとINSERTが呼ばれたか確認
        assert mock_session.execute.call_count >= len(PREFECTURE_DATA) + 1  # TRUNCATE + INSERTs
        assert mock_session.commit.called

    async def test_insert_city_data(self):
        """市区町村データ投入のテスト"""
        mock_session = AsyncMock()

        await insert_city_data(mock_session)

        # INSERTが呼ばれたか確認
        assert mock_session.execute.call_count == len(CITY_DATA)
        assert mock_session.commit.called

    async def test_insert_occupation_data(self):
        """職種データ投入のテスト"""
        mock_session = AsyncMock()

        await insert_occupation_data(mock_session)

        # TRUNCATEとINSERTが呼ばれたか確認
        assert mock_session.execute.call_count >= len(OCCUPATION_DATA) + 1
        assert mock_session.commit.called

    async def test_insert_employment_type_data(self):
        """雇用形態データ投入のテスト"""
        mock_session = AsyncMock()

        await insert_employment_type_data(mock_session)

        # TRUNCATEとINSERTが呼ばれたか確認
        assert mock_session.execute.call_count >= len(EMPLOYMENT_TYPE_DATA) + 1
        assert mock_session.commit.called

    async def test_insert_feature_data(self):
        """特徴データ投入のテスト"""
        mock_session = AsyncMock()

        await insert_feature_data(mock_session)

        # TRUNCATEとINSERTが呼ばれたか確認
        assert mock_session.execute.call_count >= len(FEATURE_DATA) + 1
        assert mock_session.commit.called

    async def test_insert_semrush_keywords_data(self):
        """SEMRUSHキーワードデータ投入のテスト"""
        mock_session = AsyncMock()

        await insert_semrush_keywords_data(mock_session)

        # INSERTが呼ばれたか確認
        assert mock_session.execute.call_count == len(SEMRUSH_KEYWORDS_DATA)
        assert mock_session.commit.called

    async def test_error_handling(self):
        """エラーハンドリングのテスト"""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            await insert_prefecture_data(mock_session)

        assert "Database error" in str(exc_info.value)
        assert mock_session.rollback.called

    async def test_verify_data(self):
        """データ検証のテスト"""
        mock_session = AsyncMock()

        # モックの結果を設定
        mock_result = MagicMock()
        mock_result.scalar.return_value = 47
        mock_session.execute.return_value = mock_result

        # エラーなく実行できることを確認
        await verify_data(mock_session)

        # 各テーブルのカウントクエリが実行されたか
        assert mock_session.execute.call_count >= 6  # 6テーブル分


class TestDataConsistency:
    """データ整合性のテスト"""

    def test_prefecture_code_format(self):
        """都道府県コードのフォーマット確認（2桁の数字）"""
        for pref in PREFECTURE_DATA:
            assert len(pref['code']) == 2
            assert pref['code'].isdigit()
            assert 1 <= int(pref['code']) <= 47

    def test_city_code_format(self):
        """市区町村コードのフォーマット確認（5桁）"""
        for city in CITY_DATA:
            assert len(city['code']) == 5
            assert city['code'].isdigit()

    def test_employment_type_matching_logic(self):
        """マッチング対象の雇用形態ロジック確認"""
        # コード1（アルバイト）、3（パート）、8（日雇い）がマッチング対象
        matching_codes = {1, 3, 8}

        for emp in EMPLOYMENT_TYPE_DATA:
            if emp['code'] in matching_codes:
                assert emp['is_valid_for_matching'] == True, f"コード{emp['code']}はマッチング対象であるべき"

    def test_feature_code_uniqueness(self):
        """特徴コードの一意性確認"""
        codes = [f['feature_code'] for f in FEATURE_DATA]
        assert len(codes) == len(set(codes)), "特徴コードに重複がある"

    def test_keyword_intent_values(self):
        """キーワードのintent値の妥当性"""
        valid_intents = {'Commercial', 'Informational', 'Transactional', 'Navigational'}

        for keyword in SEMRUSH_KEYWORDS_DATA:
            assert keyword['intent'] in valid_intents, f"無効なintent: {keyword['intent']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])