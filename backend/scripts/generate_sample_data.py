#!/usr/bin/env python3
"""
求人サンプルデータ生成スクリプト

10万件の求人データを効率的に生成してPostgreSQLに投入
処理時間目標: 5分以内
"""

import asyncio
import random
import logging
import time
import json
from typing import List, Dict, Any, Generator
from datetime import datetime, timedelta
from decimal import Decimal
import os
import sys
from io import StringIO

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from faker import Faker
import numpy as np

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# データベース接続URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/job_matching"
).replace('+asyncpg', '')  # asyncpgは+を除く

# =============================================================================
# 設定定数
# =============================================================================

# 生成設定
TOTAL_JOBS = 100000  # 生成する求人数
BATCH_SIZE = 5000    # バッチサイズ（メモリ効率とパフォーマンスのバランス）
PARALLEL_WORKERS = 4  # 並列ワーカー数

# データ分布設定
MIN_FEE = 501        # fee最小値（> 500）
MAX_FEE = 50000      # fee最大値

# 地域分布（人口比率ベース）
PREFECTURE_WEIGHTS = {
    '13': 0.15,  # 東京都 15%
    '27': 0.08,  # 大阪府 8%
    '14': 0.07,  # 神奈川県 7%
    '23': 0.06,  # 愛知県 6%
    '11': 0.05,  # 埼玉県 5%
    '12': 0.05,  # 千葉県 5%
    '40': 0.04,  # 福岡県 4%
    '28': 0.04,  # 兵庫県 4%
    '01': 0.03,  # 北海道 3%
    # その他は均等分布
}

# 職種分布（バイト市場の実態ベース）
OCCUPATION_WEIGHTS = {
    1: 0.25,   # 飲食・フード 25%
    2: 0.20,   # コンビニ・スーパー 20%
    3: 0.08,   # アパレル・ファッション 8%
    4: 0.12,   # 軽作業・物流 12%
    5: 0.08,   # 工場・製造 8%
    6: 0.07,   # 事務・データ入力 7%
    7: 0.05,   # コールセンター 5%
    8: 0.05,   # 営業・販売 5%
    9: 0.03,   # イベントスタッフ 3%
    10: 0.03,  # 教育・塾講師 3%
    11: 0.02,  # 介護・看護助手 2%
    12: 0.02,  # 清掃・ビルメンテナンス 2%
}

# 雇用形態分布（マッチング対象のみ）
EMPLOYMENT_TYPE_WEIGHTS = {
    1: 0.60,  # アルバイト 60%
    3: 0.30,  # パート 30%
    8: 0.10,  # 日雇い 10%
}

# 企業名パターン
COMPANY_PATTERNS = [
    "株式会社{}", "{}", "{}商店", "{}グループ",
    "{}ホールディングス", "{}カンパニー", "{}サービス",
    "有限会社{}", "{}システム", "{}フーズ",
    "{}ストア", "{}マート", "{}センター"
]

# 求人タイトルテンプレート
JOB_TITLE_TEMPLATES = {
    1: ["{}スタッフ", "ホール・キッチンスタッフ", "飲食店スタッフ", "調理補助"],
    2: ["コンビニスタッフ", "レジスタッフ", "品出しスタッフ", "{}店員"],
    3: ["アパレル販売員", "ファッション販売", "ショップスタッフ"],
    4: ["倉庫作業員", "仕分けスタッフ", "ピッキング作業", "梱包スタッフ"],
    5: ["工場作業員", "製造スタッフ", "ライン作業", "組立作業員"],
    6: ["データ入力", "一般事務", "事務アシスタント", "PCオペレーター"],
    7: ["コールセンター", "電話対応", "カスタマーサポート", "テレオペ"],
    8: ["営業スタッフ", "販売員", "セールススタッフ"],
    9: ["イベントスタッフ", "設営スタッフ", "運営スタッフ"],
    10: ["塾講師", "家庭教師", "教育スタッフ"],
    11: ["介護スタッフ", "看護助手", "ヘルパー"],
    12: ["清掃スタッフ", "ビル清掃", "メンテナンススタッフ"],
}

# =============================================================================
# データ生成関数
# =============================================================================

class JobDataGenerator:
    """求人データジェネレーター"""

    def __init__(self):
        self.faker = Faker('ja_JP')
        self.master_data = {}
        self.company_names_cache = set()

    async def load_master_data(self, conn: asyncpg.Connection):
        """マスターデータを読み込み"""
        # 都道府県
        rows = await conn.fetch("SELECT code, name FROM prefecture_master")
        self.master_data['prefectures'] = {row['code']: row['name'] for row in rows}

        # 市区町村
        rows = await conn.fetch("SELECT code, pref_cd, name FROM city_master")
        self.master_data['cities'] = [(row['code'], row['pref_cd']) for row in rows]

        # 職種
        rows = await conn.fetch("SELECT code FROM occupation_master WHERE is_active = TRUE")
        self.master_data['occupations'] = [row['code'] for row in rows]

        # 雇用形態
        rows = await conn.fetch("SELECT code FROM employment_type_master WHERE is_valid_for_matching = TRUE")
        self.master_data['employment_types'] = [row['code'] for row in rows]

        # 特徴
        rows = await conn.fetch("SELECT feature_code FROM feature_master WHERE is_active = TRUE")
        self.master_data['features'] = [row['feature_code'] for row in rows]

        logger.info(f"📚 マスターデータ読込完了: {len(self.master_data['prefectures'])}都道府県")

    def generate_company_name(self) -> str:
        """ユニークな企業名を生成"""
        attempts = 0
        while attempts < 100:
            base_name = self.faker.company()
            pattern = random.choice(COMPANY_PATTERNS)
            company_name = pattern.format(base_name.replace('株式会社', '').replace('有限会社', ''))

            if company_name not in self.company_names_cache:
                self.company_names_cache.add(company_name)
                return company_name
            attempts += 1

        # フォールバック: タイムスタンプを付加
        unique_name = f"{base_name}_{int(time.time() * 1000) % 100000}"
        self.company_names_cache.add(unique_name)
        return unique_name

    def generate_endcl_cd(self, index: int) -> str:
        """企業コードを生成（COMPANY_XXXXX形式）"""
        return f"COMPANY_{index:06d}"

    def select_prefecture(self) -> str:
        """重み付けに基づいて都道府県を選択"""
        if random.random() < sum(PREFECTURE_WEIGHTS.values()):
            # 重み付け選択
            prefs = list(PREFECTURE_WEIGHTS.keys())
            weights = list(PREFECTURE_WEIGHTS.values())
            return np.random.choice(prefs, p=np.array(weights)/sum(weights))
        else:
            # ランダム選択
            return random.choice(list(self.master_data['prefectures'].keys()))

    def select_city(self, pref_cd: str) -> str:
        """都道府県に応じた市区町村を選択"""
        cities = [c[0] for c in self.master_data['cities'] if c[1] == pref_cd]
        if cities:
            return random.choice(cities)
        return f"{pref_cd}000"  # フォールバック

    def select_occupation(self) -> int:
        """重み付けに基づいて職種を選択"""
        occs = list(OCCUPATION_WEIGHTS.keys())
        weights = list(OCCUPATION_WEIGHTS.values())
        return np.random.choice(occs, p=weights)

    def select_employment_type(self) -> int:
        """重み付けに基づいて雇用形態を選択"""
        types = list(EMPLOYMENT_TYPE_WEIGHTS.keys())
        weights = list(EMPLOYMENT_TYPE_WEIGHTS.values())
        return np.random.choice(types, p=weights)

    def generate_salary(self, occupation: int) -> tuple:
        """職種に応じた給与を生成"""
        # 職種別の時給レンジ
        salary_ranges = {
            1: (950, 1500),    # 飲食
            2: (900, 1300),    # コンビニ
            3: (1000, 1600),   # アパレル
            4: (1000, 1800),   # 軽作業
            5: (1100, 2000),   # 工場
            6: (1000, 1500),   # 事務
            7: (1200, 1800),   # コールセンター
            8: (1100, 2000),   # 営業
            9: (1000, 1500),   # イベント
            10: (1500, 3000),  # 塾講師
            11: (1100, 1600),  # 介護
            12: (950, 1400),   # 清掃
        }

        min_range, max_range = salary_ranges.get(occupation, (1000, 1500))
        min_salary = random.randint(min_range, max_range - 200)
        max_salary = min_salary + random.randint(100, 500)

        return min_salary, max_salary

    def generate_features(self, salary_min: int) -> List[str]:
        """求人の特徴を生成"""
        features = []
        num_features = random.randint(3, 8)

        # 高時給の場合は必ず追加
        if salary_min >= 1200:
            features.append('F03')  # 高収入
            features.append('F04')  # 時給1200円以上

        # ランダムに特徴を追加
        available_features = [f for f in self.master_data['features'] if f not in features]
        features.extend(random.sample(available_features, min(num_features - len(features), len(available_features))))

        return features[:num_features]

    def generate_job_title(self, occupation: int, company_name: str) -> str:
        """職種に応じた求人タイトルを生成"""
        templates = JOB_TITLE_TEMPLATES.get(occupation, ["スタッフ募集"])
        template = random.choice(templates)

        if '{}' in template:
            return template.format(company_name.split('株式会社')[-1].split('有限会社')[-1][:10])
        return template

    def generate_catch_copy(self, features: List[str]) -> str:
        """キャッチコピーを生成"""
        copies = [
            "未経験OK！充実の研修でしっかりサポート",
            "高時給！がっつり稼げます",
            "週1日〜OK！自分のペースで働ける",
            "駅チカで通勤便利！",
            "社員登用あり！キャリアアップ可能",
            "日払いOK！すぐにお金が必要な方も安心",
            "シフト自由！プライベートも充実",
            "まかない付き！美味しい食事も楽しめる",
            "友達と一緒に応募OK！",
            "短期OK！1ヶ月から働ける"
        ]

        # 特徴に応じてキャッチコピーを選択
        if 'F01' in features:
            return "日払いOK！すぐにお金が必要な方必見！"
        elif 'F03' in features:
            return "高時給！月収25万円以上可能！"
        elif 'F10' in features:
            return "未経験大歓迎！丁寧な研修でスキルアップ！"

        return random.choice(copies)

    def generate_job_description(self, occupation: int, company_name: str) -> str:
        """求人説明文を生成"""
        base_descriptions = {
            1: f"{company_name}で一緒に働きませんか？接客や調理補助など、やりがいのあるお仕事です。",
            2: f"地域に愛される{company_name}でのお仕事。レジ・品出し・清掃など幅広い業務があります。",
            3: f"おしゃれな{company_name}で販売スタッフ募集！お客様に素敵な商品をご提案するお仕事です。",
            4: f"{company_name}の物流センターでの軽作業。重いものはありません。黙々と作業したい方に最適！",
            5: f"{company_name}の工場でのライン作業。簡単な組立や検査のお仕事です。",
            6: f"{company_name}での事務作業。PCを使った簡単なデータ入力がメインです。",
            7: f"{company_name}のコールセンターでお客様対応。研修充実で未経験でも安心！",
            8: f"{company_name}で営業・販売のお仕事。人と話すことが好きな方大歓迎！",
            9: f"各種イベントでの{company_name}スタッフ募集。楽しく働ける環境です！",
            10: f"{company_name}で講師募集。あなたの知識を活かして生徒の成長をサポート！",
            11: f"{company_name}での介護・看護補助。やりがいのある福祉のお仕事です。",
            12: f"{company_name}での清掃業務。きれいな環境づくりのお手伝い！",
        }

        base = base_descriptions.get(occupation, f"{company_name}でスタッフ募集中！")
        additions = [
            "\n\n【仕事内容】\n具体的な業務内容は面接時に詳しくご説明します。",
            "\n\n【こんな方歓迎】\n・明るく元気な方\n・コミュニケーションが好きな方\n・責任感のある方",
            "\n\n【待遇】\n交通費支給、制服貸与、社会保険完備（条件あり）",
            "\n\n【応募】\nまずはお気軽にご応募ください！履歴書不要の面接も可能です。"
        ]

        return base + random.choice(additions)

    def generate_work_hours(self, employment_type: int) -> str:
        """勤務時間を生成"""
        if employment_type == 1:  # アルバイト
            patterns = [
                "9:00～18:00", "10:00～19:00", "11:00～20:00",
                "17:00～22:00", "18:00～23:00", "シフト制"
            ]
        elif employment_type == 3:  # パート
            patterns = [
                "9:00～14:00", "10:00～15:00", "9:00～13:00",
                "13:00～17:00", "14:00～18:00"
            ]
        else:  # 日雇い
            patterns = [
                "8:00～17:00", "9:00～18:00", "日によって異なる"
            ]

        return random.choice(patterns)

    def generate_single_job(self, job_id: int, company_index: int) -> Dict[str, Any]:
        """1件の求人データを生成"""
        # 基本情報
        endcl_cd = self.generate_endcl_cd(company_index)
        company_name = self.generate_company_name()
        pref_cd = self.select_prefecture()
        city_cd = self.select_city(pref_cd)
        occupation = self.select_occupation()
        employment_type = self.select_employment_type()

        # 給与
        min_salary, max_salary = self.generate_salary(occupation)

        # 特徴
        features = self.generate_features(min_salary)

        # fee（応募促進費用）
        # 高時給や人気職種は高めのfee
        base_fee = random.randint(MIN_FEE, 5000)
        if min_salary >= 1500:
            base_fee += random.randint(1000, 3000)
        if occupation in [1, 2, 4]:  # 人気職種
            base_fee += random.randint(500, 2000)

        # 掲載日（過去30日〜未来7日）
        posting_date = datetime.now() + timedelta(days=random.randint(-30, 7))

        # その他のフィールド
        job_data = {
            'job_id': job_id,
            'endcl_cd': endcl_cd,
            'company_name': company_name,
            'title': self.generate_job_title(occupation, company_name),
            'catch_copy': self.generate_catch_copy(features),
            'job_description': self.generate_job_description(occupation, company_name),
            'pref_cd': pref_cd,
            'city_cd': city_cd,
            'station_name': f"{self.faker.city()}駅",
            'occupation_cd1': occupation,
            'occupation_cd2': None,
            'occupation_cd3': None,
            'employment_type_cd': employment_type,
            'min_salary': min_salary,
            'max_salary': max_salary,
            'salary_text': f"時給{min_salary}円〜{max_salary}円",
            'work_hours': self.generate_work_hours(employment_type),
            'work_days_min': random.randint(1, 3),
            'work_days_max': random.randint(4, 7),
            'feature_codes': features,
            'fee': base_fee,
            'posting_date': posting_date.date(),
            'valid_until': (posting_date + timedelta(days=60)).date(),
            'is_active': True,
            'view_count': random.randint(0, 10000),
            'application_count': random.randint(0, 100),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        return job_data

    def generate_batch(self, start_id: int, batch_size: int) -> Generator[Dict[str, Any], None, None]:
        """バッチ単位でデータを生成（ジェネレーター）"""
        company_index_start = start_id // 10  # 1企業あたり平均10求人

        for i in range(batch_size):
            job_id = start_id + i
            company_index = company_index_start + (i // 10)
            yield self.generate_single_job(job_id, company_index)

# =============================================================================
# データ投入関数
# =============================================================================

async def bulk_insert_jobs(conn: asyncpg.Connection, jobs: List[Dict[str, Any]]):
    """バルクインサートで求人データを投入"""
    # COPY用のデータを準備
    copy_data = []

    for job in jobs:
        # PostgreSQL配列形式に変換
        feature_codes_str = '{' + ','.join(job['feature_codes']) + '}'

        row = (
            job['job_id'],
            job['endcl_cd'],
            job['company_name'],
            job['title'],
            job['catch_copy'],
            job['job_description'],
            job['pref_cd'],
            job['city_cd'],
            job['station_name'],
            job['occupation_cd1'],
            job['occupation_cd2'],
            job['occupation_cd3'],
            job['employment_type_cd'],
            job['min_salary'],
            job['max_salary'],
            job['salary_text'],
            job['work_hours'],
            job['work_days_min'],
            job['work_days_max'],
            feature_codes_str,
            job['fee'],
            job['posting_date'],
            job['valid_until'],
            job['is_active'],
            job['view_count'],
            job['application_count'],
            job['created_at'],
            job['updated_at']
        )
        copy_data.append(row)

    # COPY文でバルクインサート
    await conn.copy_records_to_table(
        'jobs',
        records=copy_data,
        columns=[
            'job_id', 'endcl_cd', 'company_name', 'title', 'catch_copy',
            'job_description', 'pref_cd', 'city_cd', 'station_name',
            'occupation_cd1', 'occupation_cd2', 'occupation_cd3',
            'employment_type_cd', 'min_salary', 'max_salary', 'salary_text',
            'work_hours', 'work_days_min', 'work_days_max', 'feature_codes',
            'fee', 'posting_date', 'valid_until', 'is_active',
            'view_count', 'application_count', 'created_at', 'updated_at'
        ]
    )

async def process_batch(generator: JobDataGenerator, conn: asyncpg.Connection,
                       start_id: int, batch_size: int, batch_num: int, total_batches: int):
    """バッチを処理"""
    start_time = time.time()

    # データ生成
    jobs = list(generator.generate_batch(start_id, batch_size))

    # データ投入
    await bulk_insert_jobs(conn, jobs)

    # 進捗表示
    elapsed = time.time() - start_time
    speed = batch_size / elapsed

    logger.info(
        f"📦 バッチ {batch_num}/{total_batches} 完了 | "
        f"{batch_size:,}件 | {elapsed:.2f}秒 | "
        f"{speed:.0f} rec/s"
    )

    return batch_size

# =============================================================================
# メイン処理
# =============================================================================

async def main():
    """メイン処理"""
    total_start = time.time()

    logger.info("🚀 求人サンプルデータ生成を開始します")
    logger.info(f"📊 生成件数: {TOTAL_JOBS:,}件")
    logger.info(f"📦 バッチサイズ: {BATCH_SIZE:,}件")
    logger.info(f"⚡ 並列ワーカー: {PARALLEL_WORKERS}")

    # データベース接続
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # ジェネレーター初期化
        generator = JobDataGenerator()
        await generator.load_master_data(conn)

        # 既存データをクリア（オプション）
        if os.getenv('CLEAR_EXISTING', 'true').lower() == 'true':
            await conn.execute("TRUNCATE jobs CASCADE")
            logger.info("🗑️  既存データをクリアしました")

        # バッチ処理
        total_batches = TOTAL_JOBS // BATCH_SIZE
        total_inserted = 0

        for batch_num in range(1, total_batches + 1):
            start_id = (batch_num - 1) * BATCH_SIZE + 1

            inserted = await process_batch(
                generator, conn, start_id, BATCH_SIZE,
                batch_num, total_batches
            )
            total_inserted += inserted

            # 残り時間の推定
            elapsed_total = time.time() - total_start
            avg_speed = total_inserted / elapsed_total
            remaining = TOTAL_JOBS - total_inserted
            eta = remaining / avg_speed if avg_speed > 0 else 0

            if batch_num % 5 == 0:  # 5バッチごとに詳細表示
                logger.info(
                    f"⏱️  進捗: {total_inserted:,}/{TOTAL_JOBS:,} | "
                    f"平均速度: {avg_speed:.0f} rec/s | "
                    f"残り時間: {eta/60:.1f}分"
                )

        # 残りのレコード（端数）を処理
        remaining = TOTAL_JOBS - total_inserted
        if remaining > 0:
            start_id = total_inserted + 1
            await process_batch(
                generator, conn, start_id, remaining,
                total_batches + 1, total_batches + 1
            )
            total_inserted += remaining

        # 完了統計
        total_elapsed = time.time() - total_start

        # データ検証
        count = await conn.fetchval("SELECT COUNT(*) FROM jobs")
        fee_check = await conn.fetchval("SELECT COUNT(*) FROM jobs WHERE fee <= 500")

        logger.info("\n" + "=" * 60)
        logger.info("✅ データ生成完了！")
        logger.info(f"📊 生成件数: {total_inserted:,}件")
        logger.info(f"⏱️  処理時間: {total_elapsed:.2f}秒 ({total_elapsed/60:.1f}分)")
        logger.info(f"⚡ 平均速度: {total_inserted/total_elapsed:.0f} rec/s")
        logger.info(f"✔️  DB登録数: {count:,}件")
        logger.info(f"✔️  fee > 500: {count - fee_check:,}件 (100%)")
        logger.info("=" * 60)

        # 分布確認
        logger.info("\n📊 データ分布確認:")

        # 地域分布
        pref_dist = await conn.fetch("""
            SELECT p.name, COUNT(*) as cnt
            FROM jobs j
            JOIN prefecture_master p ON j.pref_cd = p.code
            GROUP BY p.name
            ORDER BY cnt DESC
            LIMIT 5
        """)
        logger.info("地域TOP5:")
        for row in pref_dist:
            logger.info(f"  {row['name']}: {row['cnt']:,}件")

        # 職種分布
        occ_dist = await conn.fetch("""
            SELECT o.name, COUNT(*) as cnt
            FROM jobs j
            JOIN occupation_master o ON j.occupation_cd1 = o.code
            GROUP BY o.name
            ORDER BY cnt DESC
            LIMIT 5
        """)
        logger.info("職種TOP5:")
        for row in occ_dist:
            logger.info(f"  {row['name']}: {row['cnt']:,}件")

    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        raise

    finally:
        await conn.close()

if __name__ == "__main__":
    # 生成数をコマンドライン引数から取得
    if len(sys.argv) > 1:
        try:
            TOTAL_JOBS = int(sys.argv[1])
        except ValueError:
            logger.error("引数は整数で指定してください")
            sys.exit(1)

    # 実行
    asyncio.run(main())