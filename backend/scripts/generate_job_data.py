#!/usr/bin/env python3
"""
10万件求人データ高速生成スクリプト
Target: 5分以内で10万件のリアルなデータを生成・投入

Performance Strategy:
- PostgreSQL COPY FROM for bulk insert
- Batch processing (5000 records/batch)
- Pre-generated lookup data caching
- Memory-efficient streaming generation
- Progress monitoring with ETA calculation
"""

import os
import sys
import time
import random
import logging
import psycopg2
from typing import Dict, List, Tuple, Generator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import json

# Add backend path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class GenerationConfig:
    """データ生成設定"""
    total_records: int = 100000
    batch_size: int = 5000
    parallel_workers: int = 4
    target_time_seconds: int = 300  # 5分
    memory_limit_mb: int = 512

    # データベース接続
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "mail_score_dev"
    db_user: str = "postgres"
    db_password: str = "password"

class JobDataGenerator:
    """高性能求人データ生成器"""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.logger = self._setup_logger()

        # データ分布設定
        self.distributions = self._load_data_distributions()

        # キャッシュ用辞書
        self.lookup_cache = {}

        # 進捗追跡
        self.start_time = None
        self.records_generated = 0

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/job_data_generation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _load_data_distributions(self) -> Dict:
        """データ分布パターンを定義"""
        return {
            # 都道府県分布（人口・経済活動に基づく）
            'prefecture_weights': {
                '13': 25.0,  # 東京都
                '27': 15.0,  # 大阪府
                '23': 8.0,   # 愛知県
                '14': 6.0,   # 神奈川県
                '28': 5.0,   # 兵庫県
                '12': 4.0,   # 千葉県
                '11': 4.0,   # 埼玉県
                '40': 3.0,   # 福岡県
                '01': 2.0,   # 北海道
                '22': 2.0,   # 静岡県
                # その他都道府県 26.0%
            },

            # 雇用形態分布
            'employment_type_weights': {
                1: 40.0,  # アルバイト
                3: 35.0,  # パート
                6: 15.0,  # 派遣
                8: 10.0,  # 契約
            },

            # 職種分布（需要の高い職種）
            'occupation_weights': {
                100: 15.0,  # 販売・接客
                200: 12.0,  # 飲食・フード
                300: 10.0,  # 軽作業・物流
                400: 8.0,   # 事務・オフィス
                500: 8.0,   # 営業
                600: 7.0,   # 配達・ドライバー
                700: 6.0,   # 清掃・整備
                800: 5.0,   # 教育・講師
                900: 4.0,   # 医療・介護
                1000: 3.0,  # IT・技術
                # その他 22.0%
            },

            # 給与分布（時給ベース）
            'salary_ranges': [
                (900, 1200, 30.0),   # 基本時給
                (1200, 1500, 40.0),  # 標準時給
                (1500, 2000, 20.0),  # 高時給
                (2000, 3000, 10.0),  # 特別高時給
            ],

            # fee分布（500円以上必須）
            'fee_ranges': [
                (501, 1000, 40.0),
                (1001, 2000, 35.0),
                (2001, 3500, 20.0),
                (3501, 5000, 5.0),
            ],

            # 特徴コード分布
            'feature_probabilities': {
                'D01': 0.35,  # 日払い
                'W01': 0.25,  # 週払い
                'N01': 0.45,  # 未経験歓迎
                'S01': 0.30,  # 学生歓迎
                'R01': 0.15,  # リモート可
                'T01': 0.40,  # 交通費支給
            }
        }

    def _get_db_connection(self) -> psycopg2.extensions.connection:
        """データベース接続を取得"""
        return psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password
        )

    def _load_master_data(self):
        """マスターデータをキャッシュに読み込み"""
        self.logger.info("マスターデータをキャッシュに読み込み中...")

        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # 都道府県マスター
                cur.execute("SELECT code, name, region FROM prefecture_master ORDER BY code")
                self.lookup_cache['prefectures'] = {row[0]: {'name': row[1], 'region': row[2]} for row in cur.fetchall()}

                # 市区町村マスター（主要都市のみ）
                cur.execute("""
                    SELECT code, pref_cd, name FROM city_master
                    WHERE pref_cd IN ('13', '27', '23', '14', '28', '12', '11', '40')
                    ORDER BY pref_cd, code
                """)
                cities_by_pref = {}
                for row in cur.fetchall():
                    pref_cd = row[1]
                    if pref_cd not in cities_by_pref:
                        cities_by_pref[pref_cd] = []
                    cities_by_pref[pref_cd].append({'code': row[0], 'name': row[2]})
                self.lookup_cache['cities_by_pref'] = cities_by_pref

                # 職種マスター
                cur.execute("SELECT code, name FROM occupation_master WHERE is_active = true ORDER BY code")
                self.lookup_cache['occupations'] = {row[0]: row[1] for row in cur.fetchall()}

                # 雇用形態マスター
                cur.execute("SELECT code, name FROM employment_type_master ORDER BY code")
                self.lookup_cache['employment_types'] = {row[0]: row[1] for row in cur.fetchall()}

        self.logger.info(f"マスターデータ読み込み完了: "
                        f"都道府県={len(self.lookup_cache['prefectures'])}, "
                        f"職種={len(self.lookup_cache['occupations'])}")

    def _weighted_choice(self, choices: Dict[str, float]) -> str:
        """重み付け選択"""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]

    def _generate_company_data(self) -> Tuple[str, str]:
        """企業データ生成"""
        company_types = [
            "株式会社", "有限会社", "合同会社", "協同組合", "NPO法人"
        ]

        company_names = [
            "グローバル", "テクノ", "サービス", "システム", "マーケティング",
            "コンサルティング", "ソリューション", "クリエイト", "イノベーション",
            "プロジェクト", "ネットワーク", "デジタル", "フューチャー", "スマート"
        ]

        endcl_cd = f"COMP{random.randint(100000, 999999)}"
        company_name = f"{random.choice(company_types)}{random.choice(company_names)}"

        return endcl_cd, company_name

    def _generate_location_data(self) -> Tuple[str, str, str]:
        """地域データ生成"""
        pref_cd = self._weighted_choice(self.distributions['prefecture_weights'])

        # 都市選択
        if pref_cd in self.lookup_cache['cities_by_pref']:
            city_data = random.choice(self.lookup_cache['cities_by_pref'][pref_cd])
            city_cd = city_data['code']
        else:
            # フォールバック: 県庁所在地想定
            city_cd = f"{pref_cd}01"

        # 駅名生成
        station_suffixes = ["駅", "前", "中央", "東", "西", "南", "北"]
        pref_name = self.lookup_cache['prefectures'][pref_cd]['name']
        station_name = f"{pref_name[:2]}{random.choice(station_suffixes)}"

        return pref_cd, city_cd, station_name

    def _generate_salary_data(self) -> Tuple[str, int, int]:
        """給与データ生成"""
        salary_type = "hourly"  # 時給ベース

        # 給与範囲選択
        ranges = self.distributions['salary_ranges']
        range_choice = random.choices(
            ranges,
            weights=[r[2] for r in ranges]
        )[0]

        min_salary = random.randint(range_choice[0], range_choice[1] - 100)
        max_salary = random.randint(min_salary + 50, range_choice[1])

        return salary_type, min_salary, max_salary

    def _generate_fee(self) -> int:
        """fee生成（500円以上必須）"""
        ranges = self.distributions['fee_ranges']
        range_choice = random.choices(
            ranges,
            weights=[r[2] for r in ranges]
        )[0]

        return random.randint(range_choice[0], range_choice[1])

    def _generate_features(self) -> List[str]:
        """特徴コード生成"""
        features = []
        for feature_code, probability in self.distributions['feature_probabilities'].items():
            if random.random() < probability:
                features.append(feature_code)
        return features

    def _generate_job_record(self, job_id: int) -> Dict:
        """1件の求人レコード生成"""
        endcl_cd, company_name = self._generate_company_data()
        pref_cd, city_cd, station_name = self._generate_location_data()
        salary_type, min_salary, max_salary = self._generate_salary_data()

        # 職種・雇用形態
        occupation_cd1 = int(self._weighted_choice(self.distributions['occupation_weights']))
        employment_type_cd = int(self._weighted_choice(self.distributions['employment_type_weights']))

        # 特徴とfee
        features = self._generate_features()
        fee = self._generate_fee()

        # 求人名生成
        occupation_name = self.lookup_cache['occupations'].get(occupation_cd1, "スタッフ")
        application_name = f"{occupation_name}募集【{station_name}エリア】"

        return {
            'job_id': job_id,
            'endcl_cd': endcl_cd,
            'company_name': company_name,
            'application_id': f"APP{job_id:08d}",
            'application_name': application_name,
            'pref_cd': pref_cd,
            'city_cd': city_cd,
            'station_name_eki': station_name,
            'address': f"{self.lookup_cache['prefectures'][pref_cd]['name']}内",
            'salary_type': salary_type,
            'min_salary': min_salary,
            'max_salary': max_salary,
            'fee': fee,
            'hours': f"{random.randint(6, 12)}時間/日",
            'work_days': "週3日〜5日",
            'occupation_cd1': occupation_cd1,
            'employment_type_cd': employment_type_cd,
            'feature_codes': features,
            'description': f"{occupation_name}のお仕事です。{station_name}エリアでの勤務となります。",
            'benefits': "交通費支給、制服貸与、社会保険完備",
        }

    def _generate_batch_data(self, start_id: int, batch_size: int) -> Generator[Dict, None, None]:
        """バッチデータ生成（メモリ効率化）"""
        for i in range(batch_size):
            yield self._generate_job_record(start_id + i)

    def _batch_to_csv_string(self, batch_data: List[Dict]) -> str:
        """バッチデータをCSV文字列に変換"""
        output = StringIO()

        for record in batch_data:
            # PostgreSQL COPY形式のタブ区切りデータ
            row = [
                str(record['job_id']),
                record['endcl_cd'],
                record['company_name'].replace('\t', ' ').replace('\n', ' '),
                record['application_id'],
                record['application_name'].replace('\t', ' ').replace('\n', ' '),
                record['pref_cd'],
                record['city_cd'],
                record['station_name_eki'],
                record['address'].replace('\t', ' ').replace('\n', ' '),
                '\\N',  # latitude (NULL)
                '\\N',  # longitude (NULL)
                record['salary_type'],
                str(record['min_salary']),
                str(record['max_salary']),
                str(record['fee']),
                record['hours'],
                record['work_days'],
                '\\N',  # shift_flexibility (NULL)
                str(record['occupation_cd1']),
                '\\N',  # occupation_cd2 (NULL)
                str(record['employment_type_cd']),
                '{' + ','.join(record['feature_codes']) + '}',  # PostgreSQL array format
                '\\N',  # search_keywords (NULL)
                record['description'].replace('\t', ' ').replace('\n', ' '),
                record['benefits'].replace('\t', ' ').replace('\n', ' '),
                'CURRENT_TIMESTAMP',
                '\\N',  # end_at (NULL)
                'true',  # is_active
                'CURRENT_TIMESTAMP',
                'CURRENT_TIMESTAMP'
            ]
            output.write('\t'.join(row) + '\n')

        return output.getvalue()

    def _insert_batch_via_copy(self, batch_data: List[Dict], batch_num: int):
        """COPY FROMを使用した高速バッチ挿入"""
        csv_data = self._batch_to_csv_string(batch_data)

        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # COPY FROM実行
                    copy_sql = """
                    COPY jobs (
                        job_id, endcl_cd, company_name, application_id, application_name,
                        pref_cd, city_cd, station_name_eki, address, latitude, longitude,
                        salary_type, min_salary, max_salary, fee, hours, work_days,
                        shift_flexibility, occupation_cd1, occupation_cd2, employment_type_cd,
                        feature_codes, search_keywords, description, benefits,
                        posting_date, end_at, is_active, created_at, updated_at
                    ) FROM STDIN WITH (FORMAT text, DELIMITER E'\\t', NULL '\\N')
                    """

                    cur.copy_expert(copy_sql, StringIO(csv_data))
                    conn.commit()

            self.records_generated += len(batch_data)
            self._log_progress(batch_num, len(batch_data))

        except Exception as e:
            self.logger.error(f"バッチ{batch_num}の挿入エラー: {str(e)}")
            raise

    def _log_progress(self, batch_num: int, batch_size: int):
        """進捗ログ出力"""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        rate = self.records_generated / elapsed if elapsed > 0 else 0
        eta_seconds = (self.config.total_records - self.records_generated) / rate if rate > 0 else 0
        eta_minutes = eta_seconds / 60

        progress_pct = (self.records_generated / self.config.total_records) * 100

        self.logger.info(
            f"バッチ{batch_num:02d}完了 | "
            f"進捗: {self.records_generated:,}/{self.config.total_records:,} ({progress_pct:.1f}%) | "
            f"速度: {rate:.0f} records/sec | "
            f"残り時間: {eta_minutes:.1f}分"
        )

    def generate_all_data(self):
        """全データ生成・投入実行"""
        self.logger.info(f"10万件求人データ生成開始（目標時間: {self.config.target_time_seconds}秒）")
        self.start_time = time.time()

        try:
            # 1. マスターデータ読み込み
            self._load_master_data()

            # 2. バッチ処理実行
            total_batches = (self.config.total_records + self.config.batch_size - 1) // self.config.batch_size

            for batch_num in range(1, total_batches + 1):
                start_id = (batch_num - 1) * self.config.batch_size + 1
                current_batch_size = min(
                    self.config.batch_size,
                    self.config.total_records - (batch_num - 1) * self.config.batch_size
                )

                # バッチデータ生成
                batch_data = list(self._generate_batch_data(start_id, current_batch_size))

                # データベース投入
                self._insert_batch_via_copy(batch_data, batch_num)

            # 3. 完了ログ
            total_time = time.time() - self.start_time
            avg_rate = self.records_generated / total_time

            self.logger.info(
                f"✅ データ生成完了！\n"
                f"  総レコード数: {self.records_generated:,}\n"
                f"  実行時間: {total_time:.1f}秒 ({total_time/60:.1f}分)\n"
                f"  平均速度: {avg_rate:.0f} records/sec\n"
                f"  目標達成: {'✅' if total_time <= self.config.target_time_seconds else '❌'}"
            )

        except Exception as e:
            self.logger.error(f"データ生成エラー: {str(e)}")
            raise

def main():
    """メイン実行関数"""
    config = GenerationConfig()

    # 環境変数から設定読み込み
    config.db_host = os.getenv('DB_HOST', 'localhost')
    config.db_name = os.getenv('DB_NAME', 'mail_score_dev')
    config.db_user = os.getenv('DB_USER', 'postgres')
    config.db_password = os.getenv('DB_PASSWORD', 'password')

    generator = JobDataGenerator(config)
    generator.generate_all_data()

if __name__ == "__main__":
    main()