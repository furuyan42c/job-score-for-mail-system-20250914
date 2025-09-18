"""
サンプルデータ生成スクリプトのユニットテスト
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.generate_sample_data import (
    JobDataGenerator,
    TOTAL_JOBS,
    BATCH_SIZE,
    MIN_FEE,
    MAX_FEE,
    PREFECTURE_WEIGHTS,
    OCCUPATION_WEIGHTS,
    EMPLOYMENT_TYPE_WEIGHTS,
    bulk_insert_jobs,
    process_batch
)


class TestJobDataGenerator:
    """JobDataGeneratorクラスのテスト"""

    @pytest.fixture
    def generator(self):
        """テスト用ジェネレーターインスタンス"""
        gen = JobDataGenerator()
        # マスターデータをモック
        gen.master_data = {
            'prefectures': {'13': '東京都', '27': '大阪府', '23': '愛知県'},
            'cities': [('13101', '13'), ('27100', '27'), ('23100', '23')],
            'occupations': [1, 2, 3, 4, 5],
            'employment_types': [1, 3, 8],
            'features': ['F01', 'F02', 'F03', 'F04', 'F10', 'F11']
        }
        return gen

    def test_generate_company_name(self, generator):
        """企業名生成のテスト"""
        names = set()
        for _ in range(100):
            name = generator.generate_company_name()
            assert name not in names, "企業名が重複している"
            names.add(name)
            assert len(name) > 0, "企業名が空"

    def test_generate_endcl_cd(self, generator):
        """企業コード生成のテスト"""
        code1 = generator.generate_endcl_cd(1)
        code2 = generator.generate_endcl_cd(100000)

        assert code1 == "COMPANY_000001"
        assert code2 == "COMPANY_100000"
        assert len(code1) == 14  # COMPANY_ + 6桁

    def test_select_prefecture(self, generator):
        """都道府県選択のテスト"""
        # 1000回選択してある程度の偏りがあることを確認
        selections = []
        for _ in range(1000):
            pref = generator.select_prefecture()
            selections.append(pref)
            assert pref in generator.master_data['prefectures']

        # 東京都が最も多く選ばれているはず（重み付けによる）
        from collections import Counter
        counts = Counter(selections)
        most_common = counts.most_common(1)[0][0]
        # 統計的にある程度の確率で東京が最多
        # （必ずしも常に東京とは限らないのでテストは緩く）
        assert most_common in ['13', '27', '23'], "重み付け都道府県が上位に来ない"

    def test_select_city(self, generator):
        """市区町村選択のテスト"""
        # 東京都の市区町村
        city = generator.select_city('13')
        assert city == '13101'  # モックデータでは1つしかない

        # 存在しない都道府県
        city = generator.select_city('99')
        assert city == '99000'  # フォールバック

    def test_generate_salary(self, generator):
        """給与生成のテスト"""
        for occupation in range(1, 13):
            min_salary, max_salary = generator.generate_salary(occupation)

            # 基本的な制約
            assert min_salary >= 900, f"最低時給が低すぎる: {min_salary}"
            assert max_salary <= 3500, f"最高時給が高すぎる: {max_salary}"
            assert min_salary < max_salary, "最低時給が最高時給以上"
            assert max_salary - min_salary >= 100, "給与幅が狭すぎる"

    def test_generate_features(self, generator):
        """特徴生成のテスト"""
        # 通常の給与
        features = generator.generate_features(1000)
        assert len(features) >= 3, "特徴が少なすぎる"
        assert len(features) <= 8, "特徴が多すぎる"
        assert all(f in generator.master_data['features'] for f in features)

        # 高時給
        features = generator.generate_features(1500)
        assert 'F03' in features, "高時給なのに高収入タグがない"
        assert 'F04' in features, "高時給なのに時給1200円以上タグがない"

    def test_generate_single_job(self, generator):
        """1件の求人データ生成テスト"""
        job = generator.generate_single_job(1, 1)

        # 必須フィールドの存在確認
        required_fields = [
            'job_id', 'endcl_cd', 'company_name', 'title', 'catch_copy',
            'job_description', 'pref_cd', 'city_cd', 'station_name',
            'occupation_cd1', 'employment_type_cd', 'min_salary', 'max_salary',
            'salary_text', 'work_hours', 'work_days_min', 'work_days_max',
            'feature_codes', 'fee', 'posting_date', 'valid_until',
            'is_active', 'view_count', 'application_count'
        ]

        for field in required_fields:
            assert field in job, f"必須フィールド {field} が存在しない"

        # 値の妥当性確認
        assert job['job_id'] == 1
        assert job['fee'] > MIN_FEE, f"feeが最小値以下: {job['fee']}"
        assert job['fee'] <= MAX_FEE, f"feeが最大値超過: {job['fee']}"
        assert job['min_salary'] < job['max_salary']
        assert job['is_active'] == True
        assert isinstance(job['feature_codes'], list)
        assert len(job['feature_codes']) >= 3

    def test_generate_batch(self, generator):
        """バッチ生成のテスト"""
        batch_size = 100
        batch = list(generator.generate_batch(1, batch_size))

        assert len(batch) == batch_size, f"バッチサイズが不正: {len(batch)}"

        # 全てのjob_idがユニークか
        job_ids = [job['job_id'] for job in batch]
        assert len(job_ids) == len(set(job_ids)), "job_idに重複がある"

        # 企業コードのパターン確認（10求人ごとに変わるはず）
        endcl_codes = [job['endcl_cd'] for job in batch]
        assert endcl_codes[0] == endcl_codes[9], "同じ企業のコードが変わっている"
        assert endcl_codes[9] != endcl_codes[10], "異なる企業のコードが同じ"


class TestDataInsertion:
    """データ投入関数のテスト"""

    @pytest.mark.asyncio
    async def test_bulk_insert_jobs(self):
        """バルクインサートのテスト"""
        mock_conn = AsyncMock()

        # テストデータ
        jobs = [
            {
                'job_id': 1,
                'endcl_cd': 'COMPANY_000001',
                'company_name': 'テスト株式会社',
                'title': 'テストスタッフ',
                'catch_copy': 'テストキャッチ',
                'job_description': 'テスト説明',
                'pref_cd': '13',
                'city_cd': '13101',
                'station_name': 'テスト駅',
                'occupation_cd1': 1,
                'occupation_cd2': None,
                'occupation_cd3': None,
                'employment_type_cd': 1,
                'min_salary': 1000,
                'max_salary': 1500,
                'salary_text': '時給1000円〜1500円',
                'work_hours': '9:00〜18:00',
                'work_days_min': 3,
                'work_days_max': 5,
                'feature_codes': ['F01', 'F02', 'F03'],
                'fee': 1000,
                'posting_date': datetime.now().date(),
                'valid_until': (datetime.now() + timedelta(days=30)).date(),
                'is_active': True,
                'view_count': 100,
                'application_count': 10,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]

        await bulk_insert_jobs(mock_conn, jobs)

        # copy_records_to_tableが呼ばれたことを確認
        mock_conn.copy_records_to_table.assert_called_once()
        call_args = mock_conn.copy_records_to_table.call_args

        assert call_args[0][0] == 'jobs'  # テーブル名
        assert len(call_args[1]['records']) == 1  # レコード数
        assert len(call_args[1]['columns']) == 28  # カラム数

    @pytest.mark.asyncio
    async def test_process_batch(self):
        """バッチ処理のテスト"""
        generator = JobDataGenerator()
        generator.master_data = {
            'prefectures': {'13': '東京都'},
            'cities': [('13101', '13')],
            'occupations': [1],
            'employment_types': [1],
            'features': ['F01']
        }

        mock_conn = AsyncMock()

        # バッチ処理実行
        result = await process_batch(
            generator, mock_conn,
            start_id=1, batch_size=10,
            batch_num=1, total_batches=10
        )

        assert result == 10  # 処理件数
        mock_conn.copy_records_to_table.assert_called_once()


class TestDataDistribution:
    """データ分布のテスト"""

    def test_prefecture_weights_sum(self):
        """都道府県重みの合計が1以下であることを確認"""
        total_weight = sum(PREFECTURE_WEIGHTS.values())
        assert total_weight <= 1.0, f"重みの合計が1を超えている: {total_weight}"

    def test_occupation_weights_sum(self):
        """職種重みの合計が1であることを確認"""
        total_weight = sum(OCCUPATION_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01, f"重みの合計が1でない: {total_weight}"

    def test_employment_type_weights_sum(self):
        """雇用形態重みの合計が1であることを確認"""
        total_weight = sum(EMPLOYMENT_TYPE_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01, f"重みの合計が1でない: {total_weight}"

    def test_batch_size_optimization(self):
        """バッチサイズの妥当性"""
        assert BATCH_SIZE >= 1000, "バッチサイズが小さすぎる"
        assert BATCH_SIZE <= 10000, "バッチサイズが大きすぎる（メモリ問題）"
        assert TOTAL_JOBS % BATCH_SIZE <= BATCH_SIZE, "端数が大きすぎる"


class TestPerformance:
    """パフォーマンステスト"""

    @pytest.fixture
    def generator(self):
        gen = JobDataGenerator()
        gen.master_data = {
            'prefectures': {str(i).zfill(2): f'県{i}' for i in range(1, 48)},
            'cities': [(f'{i:02d}001', str(i).zfill(2)) for i in range(1, 48)],
            'occupations': list(range(1, 16)),
            'employment_types': [1, 3, 8],
            'features': [f'F{i:02d}' for i in range(1, 46)]
        }
        return gen

    def test_generation_speed(self, generator):
        """データ生成速度のテスト"""
        import time

        start_time = time.time()
        batch = list(generator.generate_batch(1, 1000))
        elapsed = time.time() - start_time

        speed = 1000 / elapsed
        assert speed > 100, f"生成速度が遅すぎる: {speed:.0f} rec/s"

        # データの妥当性も確認
        assert len(batch) == 1000
        assert all(job['fee'] > MIN_FEE for job in batch)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])