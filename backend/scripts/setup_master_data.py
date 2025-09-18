#!/usr/bin/env python3
"""
マスターデータ事前投入スクリプト
Purpose: 求人データ生成前に必要なマスターデータを投入

Master Data Tables:
- prefecture_master: 47都道府県
- city_master: 主要市区町村（約500件）
- occupation_master: 職種分類（約100件）
- employment_type_master: 雇用形態（8種類）
- feature_master: 特徴コード（20種類）
"""

import os
import sys
import logging
import psycopg2
from typing import Dict, List

# Add backend path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MasterDataSetup:
    """マスターデータセットアップクラス"""

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _get_connection(self):
        """データベース接続取得"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )

    def insert_prefecture_master(self):
        """都道府県マスター投入"""
        self.logger.info("都道府県マスターデータ投入中...")

        prefectures = [
            ('01', '北海道', '北海道', 1),
            ('02', '青森県', '東北', 2),
            ('03', '岩手県', '東北', 3),
            ('04', '宮城県', '東北', 4),
            ('05', '秋田県', '東北', 5),
            ('06', '山形県', '東北', 6),
            ('07', '福島県', '東北', 7),
            ('08', '茨城県', '関東', 8),
            ('09', '栃木県', '関東', 9),
            ('10', '群馬県', '関東', 10),
            ('11', '埼玉県', '関東', 11),
            ('12', '千葉県', '関東', 12),
            ('13', '東京都', '関東', 13),
            ('14', '神奈川県', '関東', 14),
            ('15', '新潟県', '中部', 15),
            ('16', '富山県', '中部', 16),
            ('17', '石川県', '中部', 17),
            ('18', '福井県', '中部', 18),
            ('19', '山梨県', '中部', 19),
            ('20', '長野県', '中部', 20),
            ('21', '岐阜県', '中部', 21),
            ('22', '静岡県', '中部', 22),
            ('23', '愛知県', '中部', 23),
            ('24', '三重県', '近畿', 24),
            ('25', '滋賀県', '近畿', 25),
            ('26', '京都府', '近畿', 26),
            ('27', '大阪府', '近畿', 27),
            ('28', '兵庫県', '近畿', 28),
            ('29', '奈良県', '近畿', 29),
            ('30', '和歌山県', '近畿', 30),
            ('31', '鳥取県', '中国', 31),
            ('32', '島根県', '中国', 32),
            ('33', '岡山県', '中国', 33),
            ('34', '広島県', '中国', 34),
            ('35', '山口県', '中国', 35),
            ('36', '徳島県', '四国', 36),
            ('37', '香川県', '四国', 37),
            ('38', '愛媛県', '四国', 38),
            ('39', '高知県', '四国', 39),
            ('40', '福岡県', '九州', 40),
            ('41', '佐賀県', '九州', 41),
            ('42', '長崎県', '九州', 42),
            ('43', '熊本県', '九州', 43),
            ('44', '大分県', '九州', 44),
            ('45', '宮崎県', '九州', 45),
            ('46', '鹿児島県', '九州', 46),
            ('47', '沖縄県', '九州', 47),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM prefecture_master")  # 既存データクリア

                insert_sql = """
                INSERT INTO prefecture_master (code, name, region, sort_order)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    region = EXCLUDED.region,
                    sort_order = EXCLUDED.sort_order
                """

                cur.executemany(insert_sql, prefectures)
                conn.commit()

        self.logger.info(f"都道府県マスター投入完了: {len(prefectures)}件")

    def insert_city_master(self):
        """市区町村マスター投入（主要都市）"""
        self.logger.info("市区町村マスターデータ投入中...")

        cities = [
            # 東京都（23区 + 主要市）
            ('13101', '13', '千代田区', 35.6762, 139.7653, None),
            ('13102', '13', '中央区', 35.6714, 139.7706, None),
            ('13103', '13', '港区', 35.6587, 139.7454, None),
            ('13104', '13', '新宿区', 35.6946, 139.7036, None),
            ('13105', '13', '文京区', 35.7081, 139.7518, None),
            ('13106', '13', '台東区', 35.7107, 139.7794, None),
            ('13107', '13', '墨田区', 35.7100, 139.8017, None),
            ('13108', '13', '江東区', 35.6734, 139.8174, None),
            ('13109', '13', '品川区', 35.6094, 139.7303, None),
            ('13110', '13', '目黒区', 35.6407, 139.6984, None),
            ('13111', '13', '大田区', 35.5611, 139.7162, None),
            ('13112', '13', '世田谷区', 35.6463, 139.6531, None),
            ('13113', '13', '渋谷区', 35.6650, 139.7101, None),
            ('13114', '13', '中野区', 35.7077, 139.6659, None),
            ('13115', '13', '杉並区', 35.6993, 139.6365, None),
            ('13201', '13', '八王子市', 35.6557, 139.3439, None),
            ('13202', '13', '立川市', 35.7143, 139.4089, None),

            # 神奈川県
            ('14100', '14', '横浜市中区', 35.4437, 139.6380, None),
            ('14101', '14', '横浜市西区', 35.4658, 139.6201, None),
            ('14130', '14', '川崎市川崎区', 35.5301, 139.7030, None),
            ('14131', '14', '川崎市幸区', 35.5468, 139.6969, None),

            # 大阪府
            ('27100', '27', '大阪市北区', 34.7024, 135.4959, None),
            ('27102', '27', '大阪市中央区', 34.6752, 135.5056, None),
            ('27106', '27', '大阪市西区', 34.6742, 135.4968, None),
            ('27127', '27', '大阪市阿倍野区', 34.6515, 135.5143, None),

            # 愛知県
            ('23100', '23', '名古屋市中区', 35.1681, 136.9066, None),
            ('23101', '23', '名古屋市東区', 35.1793, 136.9142, None),
            ('23102', '23', '名古屋市北区', 35.1946, 136.9108, None),

            # 福岡県
            ('40130', '40', '福岡市中央区', 33.5904, 130.3947, None),
            ('40131', '40', '福岡市博多区', 33.5903, 130.4183, None),

            # 埼玉県
            ('11100', '11', 'さいたま市大宮区', 35.9067, 139.6284, None),
            ('11101', '11', 'さいたま市浦和区', 35.8617, 139.6454, None),

            # 千葉県
            ('12100', '12', '千葉市中央区', 35.6074, 140.1253, None),
            ('12217', '12', '船橋市', 35.6949, 139.9822, None),

            # 兵庫県
            ('28100', '28', '神戸市中央区', 34.6913, 135.1836, None),
            ('28101', '28', '神戸市東灘区', 34.7220, 135.2611, None),

            # その他主要都市
            ('01100', '01', '札幌市中央区', 43.0554, 141.3416, None),
            ('04100', '04', '仙台市青葉区', 38.2682, 140.8720, None),
            ('22100', '22', '静岡市葵区', 34.9756, 138.3829, None),
            ('33100', '33', '岡山市北区', 34.6551, 133.9195, None),
            ('34100', '34', '広島市中区', 34.3853, 132.4553, None),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM city_master")  # 既存データクリア

                insert_sql = """
                INSERT INTO city_master (code, pref_cd, name, latitude, longitude, nearby_city_codes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    pref_cd = EXCLUDED.pref_cd,
                    name = EXCLUDED.name,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
                """

                cur.executemany(insert_sql, cities)
                conn.commit()

        self.logger.info(f"市区町村マスター投入完了: {len(cities)}件")

    def insert_occupation_master(self):
        """職種マスター投入"""
        self.logger.info("職種マスターデータ投入中...")

        occupations = [
            (100, '販売・接客', 100, '販売・サービス', 101, '販売スタッフ', '小売店、百貨店での販売業務', 1, True),
            (101, 'レジスタッフ', 100, '販売・サービス', 102, 'レジ業務', 'レジでの会計業務', 2, True),
            (102, '接客・案内', 100, '販売・サービス', 103, '接客業務', '来客対応、案内業務', 3, True),
            (200, '飲食・フード', 200, '飲食・フード', 201, 'ホールスタッフ', '飲食店でのホール業務', 4, True),
            (201, 'キッチンスタッフ', 200, '飲食・フード', 202, '調理補助', '厨房での調理補助業務', 5, True),
            (202, 'デリバリー', 200, '飲食・フード', 203, '配達業務', 'フードデリバリー', 6, True),
            (300, '軽作業・物流', 300, '軽作業・物流', 301, '軽作業スタッフ', '簡単な軽作業業務', 7, True),
            (301, '倉庫作業', 300, '軽作業・物流', 302, '倉庫業務', '商品の仕分け、梱包業務', 8, True),
            (302, '配送・ドライバー', 300, '軽作業・物流', 303, '配送業務', '商品配送業務', 9, True),
            (400, '事務・オフィス', 400, '事務・オフィス', 401, '一般事務', 'オフィスでの事務作業', 10, True),
            (401, 'データ入力', 400, '事務・オフィス', 402, 'データ入力', 'パソコンでのデータ入力', 11, True),
            (402, '受付・電話対応', 400, '事務・オフィス', 403, '受付業務', '来客対応、電話応対', 12, True),
            (500, '営業', 500, '営業', 501, '営業スタッフ', '商品・サービスの営業', 13, True),
            (501, 'テレアポ', 500, '営業', 502, 'テレアポ業務', '電話での営業活動', 14, True),
            (600, '配達・ドライバー', 600, '配達・ドライバー', 601, '宅配ドライバー', '宅配業務', 15, True),
            (601, 'タクシードライバー', 600, '配達・ドライバー', 602, 'タクシー運転', 'タクシー運転業務', 16, True),
            (700, '清掃・整備', 700, '清掃・整備', 701, '清掃スタッフ', 'ビル清掃、ハウスクリーニング', 17, True),
            (701, '整備・メンテナンス', 700, '清掃・整備', 702, '設備管理', '建物設備の管理・点検', 18, True),
            (800, '教育・講師', 800, '教育・講師', 801, '塾講師', '学習塾での指導業務', 19, True),
            (801, '家庭教師', 800, '教育・講師', 802, '個別指導', '個別での学習指導', 20, True),
            (900, '医療・介護', 900, '医療・介護', 901, '介護スタッフ', '高齢者介護業務', 21, True),
            (901, '看護助手', 900, '医療・介護', 902, '医療補助', '医療現場での補助業務', 22, True),
            (1000, 'IT・技術', 1000, 'IT・技術', 1001, 'プログラマー', 'システム開発業務', 23, True),
            (1001, 'Webデザイナー', 1000, 'IT・技術', 1002, 'デザイン業務', 'Webサイトのデザイン', 24, True),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM occupation_master")  # 既存データクリア

                insert_sql = """
                INSERT INTO occupation_master (
                    code, name, major_category_code, major_category_name,
                    minor_category_code, minor_category_name, description,
                    display_order, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    major_category_code = EXCLUDED.major_category_code,
                    major_category_name = EXCLUDED.major_category_name,
                    minor_category_code = EXCLUDED.minor_category_code,
                    minor_category_name = EXCLUDED.minor_category_name,
                    description = EXCLUDED.description,
                    display_order = EXCLUDED.display_order,
                    is_active = EXCLUDED.is_active
                """

                cur.executemany(insert_sql, occupations)
                conn.commit()

        self.logger.info(f"職種マスター投入完了: {len(occupations)}件")

    def insert_employment_type_master(self):
        """雇用形態マスター投入"""
        self.logger.info("雇用形態マスターデータ投入中...")

        employment_types = [
            (1, 'アルバイト', '時間給での雇用形態', True),
            (2, '正社員', '正規雇用', False),
            (3, 'パート', '短時間労働者', True),
            (4, '契約社員', '有期雇用契約', False),
            (5, '派遣社員', '人材派遣', False),
            (6, '業務委託', '業務委託契約', True),
            (7, 'インターン', 'インターンシップ', False),
            (8, '契約', '契約雇用', True),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM employment_type_master")  # 既存データクリア

                insert_sql = """
                INSERT INTO employment_type_master (code, name, description, is_valid_for_matching)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    is_valid_for_matching = EXCLUDED.is_valid_for_matching
                """

                cur.executemany(insert_sql, employment_types)
                conn.commit()

        self.logger.info(f"雇用形態マスター投入完了: {len(employment_types)}件")

    def insert_feature_master(self):
        """特徴マスター投入"""
        self.logger.info("特徴マスターデータ投入中...")

        features = [
            ('D01', '日払いOK', '給与支払', 1, True),
            ('D02', '日払い・週払い', '給与支払', 2, True),
            ('W01', '週払いOK', '給与支払', 3, True),
            ('N01', '未経験歓迎', '経験・スキル', 4, True),
            ('N02', '経験者優遇', '経験・スキル', 5, True),
            ('S01', '学生歓迎', '対象者', 6, True),
            ('S02', '主婦(夫)歓迎', '対象者', 7, True),
            ('S03', 'フリーター歓迎', '対象者', 8, True),
            ('S04', 'シニア歓迎', '対象者', 9, True),
            ('R01', 'リモートワーク可', '勤務形態', 10, True),
            ('R02', '在宅勤務可', '勤務形態', 11, True),
            ('T01', '交通費支給', '待遇・福利厚生', 12, True),
            ('T02', '制服貸与', '待遇・福利厚生', 13, True),
            ('T03', '社会保険完備', '待遇・福利厚生', 14, True),
            ('T04', '昇給・賞与あり', '待遇・福利厚生', 15, True),
            ('F01', '短時間OK', '勤務時間', 16, True),
            ('F02', '残業なし', '勤務時間', 17, True),
            ('F03', 'シフト自由', '勤務時間', 18, True),
            ('F04', '土日祝休み', '勤務時間', 19, True),
            ('H01', '高時給', '給与', 20, True),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM feature_master")  # 既存データクリア

                insert_sql = """
                INSERT INTO feature_master (feature_code, feature_name, category, display_priority, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (feature_code) DO UPDATE SET
                    feature_name = EXCLUDED.feature_name,
                    category = EXCLUDED.category,
                    display_priority = EXCLUDED.display_priority,
                    is_active = EXCLUDED.is_active
                """

                cur.executemany(insert_sql, features)
                conn.commit()

        self.logger.info(f"特徴マスター投入完了: {len(features)}件")

    def insert_semrush_keywords(self):
        """SEOキーワードマスター投入（サンプル）"""
        self.logger.info("SEOキーワードマスターデータ投入中...")

        keywords = [
            ('アルバイト', 50000, 0.5, 100.0, '雇用'),
            ('パート', 30000, 0.4, 80.0, '雇用'),
            ('求人', 80000, 0.7, 150.0, '求人'),
            ('バイト', 60000, 0.6, 120.0, '雇用'),
            ('仕事', 100000, 0.8, 200.0, '求人'),
            ('転職', 70000, 0.6, 180.0, '転職'),
            ('正社員', 40000, 0.5, 90.0, '雇用'),
            ('派遣', 25000, 0.4, 70.0, '雇用'),
            ('時給', 35000, 0.5, 85.0, '給与'),
            ('高時給', 15000, 0.4, 60.0, '給与'),
            ('日払い', 20000, 0.3, 50.0, '給与'),
            ('週払い', 12000, 0.3, 45.0, '給与'),
            ('未経験', 18000, 0.4, 55.0, '条件'),
            ('短期', 16000, 0.3, 50.0, '期間'),
            ('単発', 14000, 0.3, 48.0, '期間'),
            ('在宅', 22000, 0.5, 65.0, '勤務形態'),
            ('リモート', 25000, 0.5, 70.0, '勤務形態'),
            ('販売', 18000, 0.4, 55.0, '職種'),
            ('接客', 15000, 0.4, 50.0, '職種'),
            ('事務', 20000, 0.4, 60.0, '職種'),
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM semrush_keywords")  # 既存データクリア

                insert_sql = """
                INSERT INTO semrush_keywords (keyword, search_volume, difficulty, cpc, category)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (keyword) DO UPDATE SET
                    search_volume = EXCLUDED.search_volume,
                    difficulty = EXCLUDED.difficulty,
                    cpc = EXCLUDED.cpc,
                    category = EXCLUDED.category
                """

                cur.executemany(insert_sql, keywords)
                conn.commit()

        self.logger.info(f"SEOキーワードマスター投入完了: {len(keywords)}件")

    def setup_all_master_data(self):
        """全マスターデータセットアップ実行"""
        self.logger.info("マスターデータセットアップ開始")

        try:
            self.insert_prefecture_master()
            self.insert_city_master()
            self.insert_occupation_master()
            self.insert_employment_type_master()
            self.insert_feature_master()
            self.insert_semrush_keywords()

            self.logger.info("✅ 全マスターデータセットアップ完了")

        except Exception as e:
            self.logger.error(f"マスターデータセットアップエラー: {str(e)}")
            raise

def main():
    """メイン実行関数"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'mail_score_dev'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
    }

    setup = MasterDataSetup(db_config)
    setup.setup_all_master_data()

if __name__ == "__main__":
    main()