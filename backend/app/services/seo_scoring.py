"""
T022: SEOスコア計算実装
SEMRUSHキーワードとのマッチングによるSEOスコアリング

仕様書準拠の実装
- キーワード前処理とバリエーション生成
- フィールドごとの重み付け
- 検索ボリュームベースのスコアリング
"""

import logging
import unicodedata
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import pandas as pd

from app.models.jobs import Job

logger = logging.getLogger(__name__)

# フィールドごとのSEOスコア重み定義
FIELD_WEIGHT_CONFIG = {
    'application_name': 1.5,    # 高い重み
    'company_name': 1.5,        # 高い重み
    'catch_copy': 1.0,          # 標準的な重み
    'salary': 0.3,              # 小さい重み
    'hours': 0.3,               # 小さい重み
    'features': 0.7,            # 中程度の重み
    'station_name_eki': 0.5     # 中程度の重み
}


class SEOScoringEngine:
    """
    T022仕様準拠のSEOスコアリングエンジン
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._keywords_cache = None
        self._processed_keywords_cache = None

    async def preprocess_semrush_keywords(self, semrush_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        SEMRUSHキーワードの前処理と加工

        Args:
            semrush_data: SEMRUSHデータフレーム（省略時はDBから取得）

        Returns:
            処理済みキーワードのDataFrame
        """
        # キャッシュチェック
        if self._processed_keywords_cache is not None:
            return self._processed_keywords_cache

        # DBからデータ取得（semrush_dataが渡されない場合）
        if semrush_data is None:
            semrush_data = await self._load_semrush_keywords()

        processed_keywords = []

        for _, row in semrush_data.iterrows():
            keyword = row['keyword'].lower()

            # キーワードの分解と正規化
            # 例: "コンビニ バイト" → ["コンビニ", "バイト", "コンビニバイト"]
            parts = keyword.split()
            variations = [
                keyword,  # 元のキーワード
                ''.join(parts),  # スペースなし版
                ' '.join(parts),  # スペースあり版
            ]

            # 各バリエーションを登録
            for var in variations:
                if var:  # 空文字列を除外
                    processed_keywords.append({
                        'keyword_id': row.get('id', None),
                        'original': row['keyword'],
                        'processed': var,
                        'volume': row.get('volume', 0),
                        'difficulty': row.get('keyword_difficulty', 50),
                        'intent': row.get('intent', 'Informational')
                    })

        result_df = pd.DataFrame(processed_keywords)
        self._processed_keywords_cache = result_df
        return result_df

    async def calculate_seo_score(
        self,
        job: Job,
        processed_keywords_df: Optional[pd.DataFrame] = None
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        SEOスコアの計算（フィールドごとの重み付け対応）

        Args:
            job: 求人情報
            processed_keywords_df: 処理済みキーワードDataFrame

        Returns:
            (SEOスコア, マッチしたキーワードリスト)
        """
        # キーワードデータの準備
        if processed_keywords_df is None:
            processed_keywords_df = await self.preprocess_semrush_keywords()

        seo_score = 0
        matched_keywords = []

        # 各フィールドのテキストを準備
        field_texts = self._prepare_field_texts(job)

        # キーワードマッチングとスコア計算
        for _, keyword_row in processed_keywords_df.iterrows():
            keyword = keyword_row['processed']
            matched = False
            max_field_score = 0
            matched_field = None

            # 各フィールドでキーワードをチェック
            for field_name, field_text in field_texts.items():
                if keyword in field_text:
                    # スコア計算
                    field_score = self._calculate_keyword_field_score(
                        keyword_row, field_name
                    )

                    # 最も高いスコアのフィールドを採用
                    if field_score > max_field_score:
                        max_field_score = field_score
                        matched_field = field_name
                        matched = True

            if matched:
                seo_score += max_field_score
                matched_keywords.append({
                    'keyword': keyword_row['original'],
                    'volume': keyword_row['volume'],
                    'score': max_field_score,
                    'matched_field': matched_field
                })

                # 最大7個のキーワードまで
                if len(matched_keywords) >= 7:
                    break

        # 最大100点に正規化
        normalized_score = min(100, seo_score)

        logger.debug(
            f"SEO Score for job {job.job_id}: {normalized_score:.1f}, "
            f"Matched keywords: {len(matched_keywords)}"
        )

        return normalized_score, matched_keywords

    def _prepare_field_texts(self, job: Job) -> Dict[str, str]:
        """
        求人データから検索対象フィールドのテキストを準備

        Args:
            job: 求人情報

        Returns:
            フィールド名とテキストのマップ
        """
        field_texts = {}

        # 求人の各フィールドを正規化して取得
        field_mapping = {
            'application_name': 'title',  # 求人タイトル
            'company_name': 'company_name',
            'catch_copy': 'catch_copy',
            'salary': 'salary_text',
            'hours': 'work_hours',
            'features': 'features_text',
            'station_name_eki': 'station_name'
        }

        for field_name, job_attr in field_mapping.items():
            text = None

            # ネストされたオブジェクトの処理
            if '.' in job_attr:
                parts = job_attr.split('.')
                obj = job
                for part in parts:
                    obj = getattr(obj, part, None)
                    if obj is None:
                        break
                text = obj
            else:
                # 直接アクセス
                if hasattr(job, job_attr):
                    text = getattr(job, job_attr)
                # 特殊ケースの処理
                elif job_attr == 'salary_text' and hasattr(job, 'salary'):
                    if job.salary:
                        text = f"{job.salary.min_salary}円〜{job.salary.max_salary}円"
                elif job_attr == 'work_hours' and hasattr(job, 'work_conditions'):
                    if job.work_conditions:
                        text = job.work_conditions.work_hours
                elif job_attr == 'features_text' and hasattr(job, 'features'):
                    if job.features:
                        features_list = []
                        if job.features.has_daily_payment:
                            features_list.append("日払い")
                        if job.features.has_no_experience:
                            features_list.append("未経験OK")
                        if job.features.has_student_welcome:
                            features_list.append("学生歓迎")
                        text = " ".join(features_list)
                elif job_attr == 'station_name' and hasattr(job, 'location'):
                    if job.location and job.location.station_name:
                        text = job.location.station_name

            field_texts[field_name] = self._normalize_text(text)

        return field_texts

    def _normalize_text(self, text: Any) -> str:
        """
        全角・半角を統一してテキストを正規化

        Args:
            text: 入力テキスト

        Returns:
            正規化されたテキスト
        """
        if text is None:
            return ''
        return unicodedata.normalize('NFKC', str(text)).lower()

    def _calculate_keyword_field_score(
        self,
        keyword_row: pd.Series,
        field_name: str
    ) -> float:
        """
        キーワードとフィールドの組み合わせからスコアを計算

        Args:
            keyword_row: キーワード情報
            field_name: フィールド名

        Returns:
            計算されたスコア
        """
        volume = keyword_row['volume']
        intent = keyword_row['intent']

        # 基本スコア（ボリュームベース）
        if volume >= 10000:
            base_score = 15
        elif volume >= 5000:
            base_score = 10
        elif volume >= 1000:
            base_score = 7
        elif volume >= 500:
            base_score = 5
        else:
            base_score = 3

        # 検索意図による調整
        intent_multiplier = {
            'Commercial': 1.5,      # 商用意図は高価値
            'Transactional': 1.3,   # 取引意図も価値高
            'Informational': 1.0,   # 情報意図は標準
            'Navigational': 0.8     # ナビゲーション意図は低め
        }.get(intent, 1.0)

        # フィールド重みを適用
        field_weight = FIELD_WEIGHT_CONFIG.get(field_name, 1.0)
        field_score = base_score * intent_multiplier * field_weight

        return field_score

    async def save_keyword_scoring(
        self,
        job_id: int,
        matched_keywords: List[Dict[str, Any]],
        processed_keywords_df: Optional[pd.DataFrame] = None
    ):
        """
        keyword_scoringテーブルへのデータ保存

        Args:
            job_id: 求人ID
            matched_keywords: マッチしたキーワードリスト
            processed_keywords_df: 処理済みキーワードDataFrame
        """
        if not matched_keywords:
            return

        try:
            # バルクインサート用のデータ準備
            scoring_records = []

            for match in matched_keywords:
                scoring_records.append({
                    'job_id': job_id,
                    'keyword': match['keyword'],
                    'processed_keyword': match.get('processed_keyword', match['keyword']),
                    'base_score': match['score'],
                    'matched_field': match.get('matched_field', ''),
                    'field_weight': FIELD_WEIGHT_CONFIG.get(match.get('matched_field', ''), 1.0),
                    'volume': match.get('volume', 0),
                    'processed_at': datetime.now()
                })

            # バルクインサート
            if scoring_records:
                query = text("""
                    INSERT INTO keyword_scoring
                    (job_id, keyword, processed_keyword, base_score,
                     matched_field, field_weight, volume, processed_at)
                    VALUES
                    (:job_id, :keyword, :processed_keyword, :base_score,
                     :matched_field, :field_weight, :volume, :processed_at)
                    ON CONFLICT (job_id, keyword)
                    DO UPDATE SET
                        base_score = EXCLUDED.base_score,
                        matched_field = EXCLUDED.matched_field,
                        field_weight = EXCLUDED.field_weight,
                        processed_at = EXCLUDED.processed_at
                """)

                for record in scoring_records:
                    await self.db.execute(query, record)

                await self.db.commit()

                logger.info(f"Saved {len(scoring_records)} keyword scores for job {job_id}")

        except Exception as e:
            logger.error(f"Error saving keyword scoring for job {job_id}: {e}")
            await self.db.rollback()

    async def _load_semrush_keywords(self) -> pd.DataFrame:
        """
        データベースからSEMRUSHキーワードデータを読み込み

        Returns:
            SEMRUSHキーワードのDataFrame
        """
        try:
            result = await self.db.execute(text("""
                SELECT
                    id,
                    keyword,
                    volume,
                    keyword_difficulty,
                    intent,
                    cpc,
                    competition
                FROM semrush_keywords
                WHERE is_active = true
                ORDER BY volume DESC
                LIMIT 10000
            """))

            rows = result.fetchall()

            if not rows:
                logger.warning("No SEMRUSH keywords found in database")
                # デフォルトキーワードを返す
                return pd.DataFrame({
                    'id': [1, 2, 3],
                    'keyword': ['バイト', 'アルバイト', '求人'],
                    'volume': [10000, 8000, 5000],
                    'keyword_difficulty': [50, 45, 40],
                    'intent': ['Informational', 'Commercial', 'Transactional']
                })

            # DataFrameに変換
            data = [{
                'id': row.id,
                'keyword': row.keyword,
                'volume': row.volume,
                'keyword_difficulty': row.keyword_difficulty,
                'intent': row.intent
            } for row in rows]

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error loading SEMRUSH keywords: {e}")
            # エラー時はデフォルトデータを返す
            return pd.DataFrame({
                'id': [1],
                'keyword': ['バイト'],
                'volume': [1000],
                'keyword_difficulty': [50],
                'intent': ['Informational']
            })

    async def batch_calculate_seo_scores(
        self,
        jobs: List[Job]
    ) -> Dict[int, Tuple[float, List[Dict[str, Any]]]]:
        """
        バッチでSEOスコアを計算

        Args:
            jobs: 求人リスト

        Returns:
            job_id -> (スコア, マッチキーワード)のマップ
        """
        # キーワードを一度だけ読み込み
        processed_keywords_df = await self.preprocess_semrush_keywords()

        results = {}
        for job in jobs:
            score, keywords = await self.calculate_seo_score(job, processed_keywords_df)
            results[job.job_id] = (score, keywords)

        return results