#!/usr/bin/env python3
"""
マスターデータ投入スクリプト

都道府県、市区町村、職種、雇用形態、特徴などのマスターデータをDBに投入
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
import os
import sys

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# データベース接続URL（環境変数から取得）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/job_matching"
)

# =============================================================================
# マスターデータ定義
# =============================================================================

# 都道府県マスター（JIS X 0401準拠）
PREFECTURE_DATA = [
    {'code': '01', 'name': '北海道', 'region': '北海道', 'sort_order': 1},
    {'code': '02', 'name': '青森県', 'region': '東北', 'sort_order': 2},
    {'code': '03', 'name': '岩手県', 'region': '東北', 'sort_order': 3},
    {'code': '04', 'name': '宮城県', 'region': '東北', 'sort_order': 4},
    {'code': '05', 'name': '秋田県', 'region': '東北', 'sort_order': 5},
    {'code': '06', 'name': '山形県', 'region': '東北', 'sort_order': 6},
    {'code': '07', 'name': '福島県', 'region': '東北', 'sort_order': 7},
    {'code': '08', 'name': '茨城県', 'region': '関東', 'sort_order': 8},
    {'code': '09', 'name': '栃木県', 'region': '関東', 'sort_order': 9},
    {'code': '10', 'name': '群馬県', 'region': '関東', 'sort_order': 10},
    {'code': '11', 'name': '埼玉県', 'region': '関東', 'sort_order': 11},
    {'code': '12', 'name': '千葉県', 'region': '関東', 'sort_order': 12},
    {'code': '13', 'name': '東京都', 'region': '関東', 'sort_order': 13},
    {'code': '14', 'name': '神奈川県', 'region': '関東', 'sort_order': 14},
    {'code': '15', 'name': '新潟県', 'region': '中部', 'sort_order': 15},
    {'code': '16', 'name': '富山県', 'region': '中部', 'sort_order': 16},
    {'code': '17', 'name': '石川県', 'region': '中部', 'sort_order': 17},
    {'code': '18', 'name': '福井県', 'region': '中部', 'sort_order': 18},
    {'code': '19', 'name': '山梨県', 'region': '中部', 'sort_order': 19},
    {'code': '20', 'name': '長野県', 'region': '中部', 'sort_order': 20},
    {'code': '21', 'name': '岐阜県', 'region': '中部', 'sort_order': 21},
    {'code': '22', 'name': '静岡県', 'region': '中部', 'sort_order': 22},
    {'code': '23', 'name': '愛知県', 'region': '中部', 'sort_order': 23},
    {'code': '24', 'name': '三重県', 'region': '関西', 'sort_order': 24},
    {'code': '25', 'name': '滋賀県', 'region': '関西', 'sort_order': 25},
    {'code': '26', 'name': '京都府', 'region': '関西', 'sort_order': 26},
    {'code': '27', 'name': '大阪府', 'region': '関西', 'sort_order': 27},
    {'code': '28', 'name': '兵庫県', 'region': '関西', 'sort_order': 28},
    {'code': '29', 'name': '奈良県', 'region': '関西', 'sort_order': 29},
    {'code': '30', 'name': '和歌山県', 'region': '関西', 'sort_order': 30},
    {'code': '31', 'name': '鳥取県', 'region': '中国', 'sort_order': 31},
    {'code': '32', 'name': '島根県', 'region': '中国', 'sort_order': 32},
    {'code': '33', 'name': '岡山県', 'region': '中国', 'sort_order': 33},
    {'code': '34', 'name': '広島県', 'region': '中国', 'sort_order': 34},
    {'code': '35', 'name': '山口県', 'region': '中国', 'sort_order': 35},
    {'code': '36', 'name': '徳島県', 'region': '四国', 'sort_order': 36},
    {'code': '37', 'name': '香川県', 'region': '四国', 'sort_order': 37},
    {'code': '38', 'name': '愛媛県', 'region': '四国', 'sort_order': 38},
    {'code': '39', 'name': '高知県', 'region': '四国', 'sort_order': 39},
    {'code': '40', 'name': '福岡県', 'region': '九州', 'sort_order': 40},
    {'code': '41', 'name': '佐賀県', 'region': '九州', 'sort_order': 41},
    {'code': '42', 'name': '長崎県', 'region': '九州', 'sort_order': 42},
    {'code': '43', 'name': '熊本県', 'region': '九州', 'sort_order': 43},
    {'code': '44', 'name': '大分県', 'region': '九州', 'sort_order': 44},
    {'code': '45', 'name': '宮崎県', 'region': '九州', 'sort_order': 45},
    {'code': '46', 'name': '鹿児島県', 'region': '九州', 'sort_order': 46},
    {'code': '47', 'name': '沖縄県', 'region': '沖縄', 'sort_order': 47},
]

# 主要都市マスター（サンプル）
CITY_DATA = [
    # 東京都
    {'code': '13101', 'pref_cd': '13', 'name': '千代田区', 'latitude': 35.6940, 'longitude': 139.7535},
    {'code': '13102', 'pref_cd': '13', 'name': '中央区', 'latitude': 35.6707, 'longitude': 139.7720},
    {'code': '13103', 'pref_cd': '13', 'name': '港区', 'latitude': 35.6581, 'longitude': 139.7514},
    {'code': '13104', 'pref_cd': '13', 'name': '新宿区', 'latitude': 35.6938, 'longitude': 139.7036},
    {'code': '13105', 'pref_cd': '13', 'name': '文京区', 'latitude': 35.7081, 'longitude': 139.7522},
    {'code': '13106', 'pref_cd': '13', 'name': '台東区', 'latitude': 35.7125, 'longitude': 139.7800},
    {'code': '13107', 'pref_cd': '13', 'name': '墨田区', 'latitude': 35.7107, 'longitude': 139.8013},
    {'code': '13108', 'pref_cd': '13', 'name': '江東区', 'latitude': 35.6730, 'longitude': 139.8172},
    {'code': '13109', 'pref_cd': '13', 'name': '品川区', 'latitude': 35.6089, 'longitude': 139.7305},
    {'code': '13110', 'pref_cd': '13', 'name': '目黒区', 'latitude': 35.6414, 'longitude': 139.6982},
    {'code': '13111', 'pref_cd': '13', 'name': '大田区', 'latitude': 35.5612, 'longitude': 139.7160},
    {'code': '13112', 'pref_cd': '13', 'name': '世田谷区', 'latitude': 35.6464, 'longitude': 139.6530},
    {'code': '13113', 'pref_cd': '13', 'name': '渋谷区', 'latitude': 35.6640, 'longitude': 139.6982},
    # 大阪府
    {'code': '27100', 'pref_cd': '27', 'name': '大阪市', 'latitude': 34.6937, 'longitude': 135.5022},
    {'code': '27140', 'pref_cd': '27', 'name': '堺市', 'latitude': 34.5733, 'longitude': 135.4830},
    # 愛知県
    {'code': '23100', 'pref_cd': '23', 'name': '名古屋市', 'latitude': 35.1815, 'longitude': 136.9066},
    # 福岡県
    {'code': '40130', 'pref_cd': '40', 'name': '福岡市', 'latitude': 33.5904, 'longitude': 130.4017},
    {'code': '40100', 'pref_cd': '40', 'name': '北九州市', 'latitude': 33.8834, 'longitude': 130.8752},
]

# 職種マスター（バイト・パート向け主要カテゴリ）
OCCUPATION_DATA = [
    {'code': 1, 'name': '飲食・フード', 'major_category_code': 1, 'major_category_name': 'サービス業', 'display_order': 1},
    {'code': 2, 'name': 'コンビニ・スーパー', 'major_category_code': 2, 'major_category_name': '販売・小売', 'display_order': 2},
    {'code': 3, 'name': 'アパレル・ファッション', 'major_category_code': 2, 'major_category_name': '販売・小売', 'display_order': 3},
    {'code': 4, 'name': '軽作業・物流', 'major_category_code': 3, 'major_category_name': '作業・物流', 'display_order': 4},
    {'code': 5, 'name': '工場・製造', 'major_category_code': 3, 'major_category_name': '作業・物流', 'display_order': 5},
    {'code': 6, 'name': '事務・データ入力', 'major_category_code': 4, 'major_category_name': 'オフィスワーク', 'display_order': 6},
    {'code': 7, 'name': 'コールセンター', 'major_category_code': 4, 'major_category_name': 'オフィスワーク', 'display_order': 7},
    {'code': 8, 'name': '営業・販売', 'major_category_code': 5, 'major_category_name': '営業・販売', 'display_order': 8},
    {'code': 9, 'name': 'イベントスタッフ', 'major_category_code': 6, 'major_category_name': 'イベント・エンタメ', 'display_order': 9},
    {'code': 10, 'name': '教育・塾講師', 'major_category_code': 7, 'major_category_name': '教育・医療・福祉', 'display_order': 10},
    {'code': 11, 'name': '介護・看護助手', 'major_category_code': 7, 'major_category_name': '教育・医療・福祉', 'display_order': 11},
    {'code': 12, 'name': '清掃・ビルメンテナンス', 'major_category_code': 8, 'major_category_name': '清掃・設備', 'display_order': 12},
    {'code': 13, 'name': '配達・ドライバー', 'major_category_code': 9, 'major_category_name': '運輸・配送', 'display_order': 13},
    {'code': 14, 'name': 'IT・プログラマー', 'major_category_code': 10, 'major_category_name': 'IT・技術', 'display_order': 14},
    {'code': 15, 'name': 'デザイン・クリエイティブ', 'major_category_code': 11, 'major_category_name': 'クリエイティブ', 'display_order': 15},
]

# 雇用形態マスター
EMPLOYMENT_TYPE_DATA = [
    {'code': 1, 'name': 'アルバイト', 'description': '短期・長期アルバイト', 'is_valid_for_matching': True},
    {'code': 2, 'name': '正社員', 'description': '正規雇用', 'is_valid_for_matching': False},
    {'code': 3, 'name': 'パート', 'description': 'パートタイム勤務', 'is_valid_for_matching': True},
    {'code': 4, 'name': '契約社員', 'description': '期間契約社員', 'is_valid_for_matching': False},
    {'code': 5, 'name': '派遣社員', 'description': '派遣スタッフ', 'is_valid_for_matching': False},
    {'code': 6, 'name': '業務委託', 'description': 'フリーランス・業務委託', 'is_valid_for_matching': False},
    {'code': 7, 'name': 'インターン', 'description': 'インターンシップ', 'is_valid_for_matching': False},
    {'code': 8, 'name': '日雇い', 'description': '日払い・単発バイト', 'is_valid_for_matching': True},
]

# 特徴マスター
FEATURE_DATA = [
    # 給与・待遇
    {'feature_code': 'F01', 'feature_name': '日払いOK', 'category': '給与・待遇', 'display_priority': 1},
    {'feature_code': 'F02', 'feature_name': '週払いOK', 'category': '給与・待遇', 'display_priority': 2},
    {'feature_code': 'F03', 'feature_name': '高収入', 'category': '給与・待遇', 'display_priority': 3},
    {'feature_code': 'F04', 'feature_name': '時給1200円以上', 'category': '給与・待遇', 'display_priority': 4},
    {'feature_code': 'F05', 'feature_name': '交通費支給', 'category': '給与・待遇', 'display_priority': 5},
    {'feature_code': 'F06', 'feature_name': '昇給あり', 'category': '給与・待遇', 'display_priority': 6},
    {'feature_code': 'F07', 'feature_name': 'ボーナス・賞与あり', 'category': '給与・待遇', 'display_priority': 7},

    # 勤務条件
    {'feature_code': 'F10', 'feature_name': '未経験OK', 'category': '勤務条件', 'display_priority': 10},
    {'feature_code': 'F11', 'feature_name': '学生歓迎', 'category': '勤務条件', 'display_priority': 11},
    {'feature_code': 'F12', 'feature_name': '主婦(夫)歓迎', 'category': '勤務条件', 'display_priority': 12},
    {'feature_code': 'F13', 'feature_name': 'フリーター歓迎', 'category': '勤務条件', 'display_priority': 13},
    {'feature_code': 'F14', 'feature_name': 'シニア歓迎', 'category': '勤務条件', 'display_priority': 14},
    {'feature_code': 'F15', 'feature_name': '外国人OK', 'category': '勤務条件', 'display_priority': 15},

    # シフト・時間
    {'feature_code': 'F20', 'feature_name': 'シフト自由', 'category': 'シフト・時間', 'display_priority': 20},
    {'feature_code': 'F21', 'feature_name': '週1日〜OK', 'category': 'シフト・時間', 'display_priority': 21},
    {'feature_code': 'F22', 'feature_name': '短時間OK', 'category': 'シフト・時間', 'display_priority': 22},
    {'feature_code': 'F23', 'feature_name': '土日祝のみOK', 'category': 'シフト・時間', 'display_priority': 23},
    {'feature_code': 'F24', 'feature_name': '平日のみOK', 'category': 'シフト・時間', 'display_priority': 24},
    {'feature_code': 'F25', 'feature_name': '朝のみOK', 'category': 'シフト・時間', 'display_priority': 25},
    {'feature_code': 'F26', 'feature_name': '夜のみOK', 'category': 'シフト・時間', 'display_priority': 26},
    {'feature_code': 'F27', 'feature_name': '深夜勤務', 'category': 'シフト・時間', 'display_priority': 27},

    # 立地・環境
    {'feature_code': 'F30', 'feature_name': '駅チカ', 'category': '立地・環境', 'display_priority': 30},
    {'feature_code': 'F31', 'feature_name': '車通勤OK', 'category': '立地・環境', 'display_priority': 31},
    {'feature_code': 'F32', 'feature_name': 'バイク通勤OK', 'category': '立地・環境', 'display_priority': 32},
    {'feature_code': 'F33', 'feature_name': '在宅ワーク', 'category': '立地・環境', 'display_priority': 33},

    # 待遇・福利厚生
    {'feature_code': 'F40', 'feature_name': '社員登用あり', 'category': '待遇・福利厚生', 'display_priority': 40},
    {'feature_code': 'F41', 'feature_name': '研修あり', 'category': '待遇・福利厚生', 'display_priority': 41},
    {'feature_code': 'F42', 'feature_name': '制服貸与', 'category': '待遇・福利厚生', 'display_priority': 42},
    {'feature_code': 'F43', 'feature_name': 'まかない・食事補助', 'category': '待遇・福利厚生', 'display_priority': 43},
    {'feature_code': 'F44', 'feature_name': '社会保険完備', 'category': '待遇・福利厚生', 'display_priority': 44},
    {'feature_code': 'F45', 'feature_name': '社割あり', 'category': '待遇・福利厚生', 'display_priority': 45},
]

# SEMRUSHキーワードマスター（サンプル）
SEMRUSH_KEYWORDS_DATA = [
    {'keyword': 'コンビニ バイト', 'search_volume': 74000, 'keyword_difficulty': 45, 'intent': 'Commercial', 'category': 'コンビニ'},
    {'keyword': 'バイト 高校生', 'search_volume': 60500, 'keyword_difficulty': 42, 'intent': 'Informational', 'category': '学生'},
    {'keyword': '日払い バイト', 'search_volume': 49500, 'keyword_difficulty': 48, 'intent': 'Transactional', 'category': '日払い'},
    {'keyword': '短期 バイト', 'search_volume': 40500, 'keyword_difficulty': 46, 'intent': 'Commercial', 'category': '短期'},
    {'keyword': '高時給 バイト', 'search_volume': 33100, 'keyword_difficulty': 50, 'intent': 'Commercial', 'category': '高時給'},
    {'keyword': '週1 バイト', 'search_volume': 27100, 'keyword_difficulty': 41, 'intent': 'Navigational', 'category': 'シフト'},
    {'keyword': '在宅 バイト', 'search_volume': 22200, 'keyword_difficulty': 52, 'intent': 'Commercial', 'category': '在宅'},
    {'keyword': 'データ入力 バイト', 'search_volume': 18100, 'keyword_difficulty': 44, 'intent': 'Commercial', 'category': '事務'},
    {'keyword': '軽作業 バイト', 'search_volume': 14800, 'keyword_difficulty': 43, 'intent': 'Commercial', 'category': '軽作業'},
    {'keyword': 'イベントスタッフ バイト', 'search_volume': 12100, 'keyword_difficulty': 40, 'intent': 'Commercial', 'category': 'イベント'},
]

# =============================================================================
# データ投入関数
# =============================================================================

async def insert_prefecture_data(session: AsyncSession):
    """都道府県マスターデータを投入"""
    try:
        # 既存データをクリア
        await session.execute(text("TRUNCATE prefecture_master CASCADE"))

        # データ投入
        for pref in PREFECTURE_DATA:
            query = text("""
                INSERT INTO prefecture_master (code, name, region, sort_order)
                VALUES (:code, :name, :region, :sort_order)
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name,
                    region = EXCLUDED.region,
                    sort_order = EXCLUDED.sort_order
            """)
            await session.execute(query, pref)

        await session.commit()
        logger.info(f"✅ 都道府県マスター: {len(PREFECTURE_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 都道府県マスター投入エラー: {e}")
        raise

async def insert_city_data(session: AsyncSession):
    """市区町村マスターデータを投入"""
    try:
        # データ投入
        for city in CITY_DATA:
            query = text("""
                INSERT INTO city_master (code, pref_cd, name, latitude, longitude)
                VALUES (:code, :pref_cd, :name, :latitude, :longitude)
                ON CONFLICT (code) DO UPDATE
                SET pref_cd = EXCLUDED.pref_cd,
                    name = EXCLUDED.name,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
            """)
            await session.execute(query, city)

        await session.commit()
        logger.info(f"✅ 市区町村マスター: {len(CITY_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 市区町村マスター投入エラー: {e}")
        raise

async def insert_occupation_data(session: AsyncSession):
    """職種マスターデータを投入"""
    try:
        # 既存データをクリア
        await session.execute(text("TRUNCATE occupation_master CASCADE"))

        # データ投入
        for occ in OCCUPATION_DATA:
            query = text("""
                INSERT INTO occupation_master (
                    code, name, major_category_code, major_category_name,
                    minor_category_code, minor_category_name, description,
                    display_order, is_active
                ) VALUES (
                    :code, :name, :major_category_code, :major_category_name,
                    NULL, NULL, NULL, :display_order, TRUE
                )
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name,
                    major_category_code = EXCLUDED.major_category_code,
                    major_category_name = EXCLUDED.major_category_name,
                    display_order = EXCLUDED.display_order
            """)
            await session.execute(query, occ)

        await session.commit()
        logger.info(f"✅ 職種マスター: {len(OCCUPATION_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 職種マスター投入エラー: {e}")
        raise

async def insert_employment_type_data(session: AsyncSession):
    """雇用形態マスターデータを投入"""
    try:
        # 既存データをクリア
        await session.execute(text("TRUNCATE employment_type_master CASCADE"))

        # データ投入
        for emp in EMPLOYMENT_TYPE_DATA:
            query = text("""
                INSERT INTO employment_type_master (
                    code, name, description, is_valid_for_matching
                ) VALUES (
                    :code, :name, :description, :is_valid_for_matching
                )
                ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    is_valid_for_matching = EXCLUDED.is_valid_for_matching
            """)
            await session.execute(query, emp)

        await session.commit()
        logger.info(f"✅ 雇用形態マスター: {len(EMPLOYMENT_TYPE_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 雇用形態マスター投入エラー: {e}")
        raise

async def insert_feature_data(session: AsyncSession):
    """特徴マスターデータを投入"""
    try:
        # 既存データをクリア
        await session.execute(text("TRUNCATE feature_master CASCADE"))

        # データ投入
        for feature in FEATURE_DATA:
            query = text("""
                INSERT INTO feature_master (
                    feature_code, feature_name, category, display_priority, is_active
                ) VALUES (
                    :feature_code, :feature_name, :category, :display_priority, TRUE
                )
                ON CONFLICT (feature_code) DO UPDATE
                SET feature_name = EXCLUDED.feature_name,
                    category = EXCLUDED.category,
                    display_priority = EXCLUDED.display_priority
            """)
            await session.execute(query, feature)

        await session.commit()
        logger.info(f"✅ 特徴マスター: {len(FEATURE_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 特徴マスター投入エラー: {e}")
        raise

async def insert_semrush_keywords_data(session: AsyncSession):
    """SEMRUSHキーワードデータを投入"""
    try:
        # データ投入
        for keyword in SEMRUSH_KEYWORDS_DATA:
            query = text("""
                INSERT INTO semrush_keywords (
                    keyword, search_volume, keyword_difficulty, intent, category
                ) VALUES (
                    :keyword, :search_volume, :keyword_difficulty, :intent, :category
                )
                ON CONFLICT (keyword) DO UPDATE
                SET search_volume = EXCLUDED.search_volume,
                    keyword_difficulty = EXCLUDED.keyword_difficulty,
                    intent = EXCLUDED.intent,
                    category = EXCLUDED.category
            """)
            await session.execute(query, keyword)

        await session.commit()
        logger.info(f"✅ SEMRUSHキーワード: {len(SEMRUSH_KEYWORDS_DATA)}件投入完了")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ SEMRUSHキーワード投入エラー: {e}")
        raise

async def verify_data(session: AsyncSession):
    """投入データの検証"""
    try:
        # 各テーブルのレコード数を確認
        checks = [
            ("prefecture_master", "都道府県"),
            ("city_master", "市区町村"),
            ("occupation_master", "職種"),
            ("employment_type_master", "雇用形態"),
            ("feature_master", "特徴"),
            ("semrush_keywords", "SEMRUSHキーワード"),
        ]

        logger.info("\n📊 データ投入結果:")
        logger.info("-" * 50)

        for table_name, label in checks:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            count = result.scalar()
            logger.info(f"  {label:20s}: {count:,}件")

        logger.info("-" * 50)

    except Exception as e:
        logger.error(f"❌ データ検証エラー: {e}")
        raise

# =============================================================================
# メイン処理
# =============================================================================

async def main():
    """メイン処理"""
    logger.info("🚀 マスターデータ投入を開始します")
    logger.info(f"📍 データベース: {DATABASE_URL.split('@')[-1]}")

    # データベースエンジン作成
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10
    )

    # セッション作成
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # 各マスターデータを投入
            await insert_prefecture_data(session)
            await insert_city_data(session)
            await insert_occupation_data(session)
            await insert_employment_type_data(session)
            await insert_feature_data(session)
            await insert_semrush_keywords_data(session)

            # データ検証
            await verify_data(session)

            logger.info("\n✅ マスターデータ投入が正常に完了しました！")

        except Exception as e:
            logger.error(f"\n❌ マスターデータ投入に失敗しました: {e}")
            raise

        finally:
            await engine.dispose()

if __name__ == "__main__":
    # スクリプトを実行
    asyncio.run(main())