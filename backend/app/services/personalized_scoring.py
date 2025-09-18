"""
T023: パーソナライズスコア計算実装
implicit ALSによる協調フィルタリングを使用した個人化スコアリング

仕様書準拠の実装
- implicit ALSモデルによる協調フィルタリング
- ユーザープロファイルの潜在因子を使用
- 応募履歴に基づく推薦
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import scipy.sparse as sparse

try:
    from implicit.als import AlternatingLeastSquares as ALS
    IMPLICIT_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("implicit library not installed. Using fallback implementation.")
    IMPLICIT_AVAILABLE = False

from app.models.jobs import Job
from app.models.users import User, UserProfile

logger = logging.getLogger(__name__)


class PersonalizedScoringEngine:
    """
    T023仕様準拠のパーソナライズスコアリングエンジン
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._als_model = None
        self._user_item_matrix = None
        self._job_id_to_index = {}
        self._user_id_to_index = {}
        self._model_trained = False

    async def initialize_als_model(
        self,
        factors: int = 50,
        regularization: float = 0.01,
        iterations: int = 15,
        calculate_training_loss: bool = False,
        use_gpu: bool = False
    ):
        """
        ALSモデルの初期化

        Args:
            factors: 潜在因子の数
            regularization: 正則化パラメータ
            iterations: イテレーション数
            calculate_training_loss: 学習損失を計算するか
            use_gpu: GPU使用フラグ
        """
        if not IMPLICIT_AVAILABLE:
            logger.warning("implicit library not available. Using fallback.")
            return

        self._als_model = ALS(
            factors=factors,
            regularization=regularization,
            iterations=iterations,
            calculate_training_loss=calculate_training_loss,
            use_gpu=use_gpu,
            random_state=42
        )

        logger.info(
            f"ALS model initialized with factors={factors}, "
            f"regularization={regularization}, iterations={iterations}"
        )

    async def train_model(self, retrain: bool = False):
        """
        ユーザーの応募履歴を使用してALSモデルを学習

        Args:
            retrain: 再学習フラグ
        """
        if self._model_trained and not retrain:
            logger.info("Model already trained. Skipping training.")
            return

        if not IMPLICIT_AVAILABLE:
            logger.warning("implicit library not available. Using fallback scoring.")
            return

        # ユーザー・アイテム行列の構築
        await self._build_user_item_matrix()

        if self._user_item_matrix is None:
            logger.warning("No user-item matrix built. Cannot train model.")
            return

        # ALSモデルの学習
        logger.info("Training ALS model...")
        self._als_model.fit(self._user_item_matrix.T)
        self._model_trained = True
        logger.info("ALS model training completed")

    async def calculate_personalized_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile] = None
    ) -> float:
        """
        パーソナライズスコアの計算

        Args:
            user: ユーザー情報
            job: 求人情報
            user_profile: ユーザープロファイル

        Returns:
            パーソナライズスコア (0-100)
        """
        score = 50.0  # ベーススコア

        # ALSモデルによるスコアリング
        if IMPLICIT_AVAILABLE and self._model_trained:
            als_score = await self._calculate_als_score(user.user_id, job.job_id)
            score = als_score * 100  # 0-1を0-100に変換
        else:
            # フォールバック: ユーザープロファイルベースのスコアリング
            if user_profile:
                score = await self._calculate_profile_based_score(
                    user, job, user_profile
                )

        # スコアの範囲を0-100に制限
        score = min(100.0, max(0.0, score))

        logger.debug(
            f"Personalized score for user {user.user_id}, job {job.job_id}: {score:.1f}"
        )

        return score

    async def _calculate_als_score(
        self,
        user_id: int,
        job_id: int
    ) -> float:
        """
        ALSモデルを使用したスコア計算

        Args:
            user_id: ユーザーID
            job_id: 求人ID

        Returns:
            予測スコア (0-1)
        """
        if not self._model_trained or self._als_model is None:
            return 0.5

        # ユーザーとアイテムのインデックスを取得
        user_idx = self._user_id_to_index.get(user_id)
        job_idx = self._job_id_to_index.get(job_id)

        if user_idx is None or job_idx is None:
            # 新規ユーザーまたは新規求人の場合
            return 0.5

        try:
            # ALSモデルで予測
            user_factors = self._als_model.user_factors[user_idx]
            item_factors = self._als_model.item_factors[job_idx]
            score = np.dot(user_factors, item_factors)

            # シグモイド関数で0-1に正規化
            score = 1 / (1 + np.exp(-score))
            return float(score)

        except Exception as e:
            logger.error(f"Error calculating ALS score: {e}")
            return 0.5

    async def _calculate_profile_based_score(
        self,
        user: User,
        job: Job,
        user_profile: UserProfile
    ) -> float:
        """
        ユーザープロファイルベースのスコアリング（フォールバック）

        Args:
            user: ユーザー情報
            job: 求人情報
            user_profile: ユーザープロファイル

        Returns:
            プロファイルベースのスコア (0-100)
        """
        score = 50.0

        # 過去の応募パターン分析
        if user_profile.application_history:
            history_score = await self._analyze_application_history(
                user_profile.application_history, job
            )
            score += history_score * 0.3

        # クリックパターン分析
        if user_profile.click_history:
            click_score = await self._analyze_click_patterns(
                user_profile.click_history, job
            )
            score += click_score * 0.2

        # 潜在因子の使用（ALSなしでも利用可能な場合）
        if hasattr(user_profile, 'latent_factors') and user_profile.latent_factors:
            latent_score = self._calculate_latent_factor_score(
                user_profile.latent_factors, job
            )
            score += latent_score * 0.3

        return min(100.0, max(0.0, score))

    async def _build_user_item_matrix(self):
        """
        ユーザー・アイテム相互作用行列の構築
        """
        try:
            # 過去360日のユーザーアクションを取得
            cutoff_date = datetime.now() - timedelta(days=360)

            query = text("""
                SELECT
                    user_id,
                    job_id,
                    COUNT(*) as interaction_count,
                    MAX(CASE WHEN action_type = 'apply' THEN 5
                         WHEN action_type = 'click' THEN 2
                         WHEN action_type = 'view' THEN 1
                         ELSE 0 END) as interaction_weight
                FROM user_actions
                WHERE action_timestamp > :cutoff_date
                AND job_id IS NOT NULL
                GROUP BY user_id, job_id
                ORDER BY user_id, job_id
            """)

            result = await self.db.execute(query, {'cutoff_date': cutoff_date})
            interactions = result.fetchall()

            if not interactions:
                logger.warning("No user interactions found for building matrix")
                return

            # ユーザーとアイテムのユニークIDを収集
            users = set()
            jobs = set()
            data = []

            for row in interactions:
                users.add(row.user_id)
                jobs.add(row.job_id)
                # 重み = カウント × アクションタイプの重み
                weight = row.interaction_count * row.interaction_weight
                data.append((row.user_id, row.job_id, weight))

            # インデックスマッピングを作成
            self._user_id_to_index = {uid: i for i, uid in enumerate(sorted(users))}
            self._job_id_to_index = {jid: i for i, jid in enumerate(sorted(jobs))}

            # スパース行列の作成
            n_users = len(users)
            n_jobs = len(jobs)
            rows = []
            cols = []
            values = []

            for user_id, job_id, weight in data:
                rows.append(self._user_id_to_index[user_id])
                cols.append(self._job_id_to_index[job_id])
                values.append(weight)

            self._user_item_matrix = sparse.coo_matrix(
                (values, (rows, cols)),
                shape=(n_users, n_jobs)
            ).tocsr()

            logger.info(
                f"User-item matrix built: {n_users} users × {n_jobs} jobs, "
                f"{len(data)} interactions"
            )

        except Exception as e:
            logger.error(f"Error building user-item matrix: {e}")
            self._user_item_matrix = None

    async def _analyze_application_history(
        self,
        history: List[Dict[str, Any]],
        job: Job
    ) -> float:
        """
        応募履歴の分析

        Args:
            history: 応募履歴
            job: 求人情報

        Returns:
            履歴ベースのスコア (0-100)
        """
        if not history:
            return 0

        similarity_scores = []

        for past_application in history[-10:]:  # 直近10件を分析
            # カテゴリの類似性
            if (hasattr(job, 'category') and
                'category' in past_application and
                job.category.occupation_cd1 == past_application.get('category')):
                similarity_scores.append(30)

            # 給与レンジの類似性
            if (hasattr(job, 'salary') and
                'salary_range' in past_application):
                past_salary = past_application.get('salary_range', {})
                if (job.salary.min_salary >= past_salary.get('min', 0) * 0.8 and
                    job.salary.max_salary <= past_salary.get('max', float('inf')) * 1.2):
                    similarity_scores.append(20)

            # 勤務地の類似性
            if (hasattr(job, 'location') and
                'location' in past_application):
                past_loc = past_application.get('location', {})
                if job.location.prefecture_code == past_loc.get('prefecture'):
                    similarity_scores.append(15)

        return np.mean(similarity_scores) if similarity_scores else 0

    async def _analyze_click_patterns(
        self,
        click_history: List[Dict[str, Any]],
        job: Job
    ) -> float:
        """
        クリックパターンの分析

        Args:
            click_history: クリック履歴
            job: 求人情報

        Returns:
            クリックパターンベースのスコア (0-100)
        """
        if not click_history:
            return 0

        # 類似求人へのクリック数をカウント
        similar_clicks = 0
        total_recent_clicks = min(len(click_history), 50)

        for click in click_history[-50:]:  # 直近50クリックを分析
            # カテゴリが一致
            if (hasattr(job, 'category') and
                'category' in click and
                job.category.occupation_cd1 == click.get('category')):
                similar_clicks += 1

        # クリック率に基づくスコア
        if total_recent_clicks > 0:
            click_rate = similar_clicks / total_recent_clicks
            return click_rate * 100

        return 0

    def _calculate_latent_factor_score(
        self,
        latent_factors: List[float],
        job: Job
    ) -> float:
        """
        潜在因子を使用したスコア計算

        Args:
            latent_factors: ユーザーの潜在因子
            job: 求人情報

        Returns:
            潜在因子ベースのスコア (0-100)
        """
        if not latent_factors or len(latent_factors) < 10:
            return 0

        # 求人の特徴ベクトルを生成（簡易版）
        job_features = []

        # カテゴリコード
        if hasattr(job, 'category'):
            job_features.append(float(job.category.occupation_cd1 or 0) / 100)
        else:
            job_features.append(0)

        # 給与レベル
        if hasattr(job, 'salary') and job.salary:
            salary_level = min(job.salary.min_salary / 2000, 1.0)
            job_features.append(salary_level)
        else:
            job_features.append(0.5)

        # 特徴フラグ
        if hasattr(job, 'features') and job.features:
            job_features.extend([
                1.0 if job.features.has_daily_payment else 0.0,
                1.0 if job.features.has_no_experience else 0.0,
                1.0 if job.features.has_student_welcome else 0.0,
            ])
        else:
            job_features.extend([0.0, 0.0, 0.0])

        # パディング
        while len(job_features) < 10:
            job_features.append(0.0)

        # コサイン類似度の計算
        user_vec = np.array(latent_factors[:10])
        job_vec = np.array(job_features[:10])

        if np.linalg.norm(user_vec) > 0 and np.linalg.norm(job_vec) > 0:
            similarity = np.dot(user_vec, job_vec) / (
                np.linalg.norm(user_vec) * np.linalg.norm(job_vec)
            )
            # -1〜1を0〜100にマッピング
            return (similarity + 1) * 50

        return 25  # デフォルト値

    async def get_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        filter_already_applied: bool = True
    ) -> List[Tuple[int, float]]:
        """
        ユーザーへのおすすめ求人を取得

        Args:
            user_id: ユーザーID
            n_recommendations: 推薦数
            filter_already_applied: 既応募求人を除外するか

        Returns:
            [(job_id, score), ...]のリスト
        """
        if not IMPLICIT_AVAILABLE or not self._model_trained:
            logger.warning("Model not available. Returning empty recommendations.")
            return []

        user_idx = self._user_id_to_index.get(user_id)
        if user_idx is None:
            logger.warning(f"User {user_id} not found in training data")
            return []

        try:
            # ALSモデルで推薦を取得
            recommendations = self._als_model.recommend(
                userid=user_idx,
                user_items=self._user_item_matrix[user_idx],
                N=n_recommendations * 2,  # フィルタリング用に多めに取得
                filter_already_liked_items=filter_already_applied
            )

            # インデックスをjob_idに変換
            index_to_job_id = {v: k for k, v in self._job_id_to_index.items()}
            result = []

            for job_idx, score in recommendations:
                if job_idx in index_to_job_id:
                    result.append((index_to_job_id[job_idx], float(score)))

                if len(result) >= n_recommendations:
                    break

            return result

        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return []

    async def update_user_interaction(
        self,
        user_id: int,
        job_id: int,
        interaction_type: str,
        weight: float = 1.0
    ):
        """
        ユーザーインタラクションの更新（リアルタイム更新用）

        Args:
            user_id: ユーザーID
            job_id: 求人ID
            interaction_type: インタラクションタイプ
            weight: 重み
        """
        try:
            # user_actionsテーブルに記録
            query = text("""
                INSERT INTO user_actions
                (user_id, job_id, action_type, action_timestamp, metadata)
                VALUES
                (:user_id, :job_id, :action_type, :timestamp, :metadata)
            """)

            await self.db.execute(query, {
                'user_id': user_id,
                'job_id': job_id,
                'action_type': interaction_type,
                'timestamp': datetime.now(),
                'metadata': {'weight': weight}
            })

            await self.db.commit()

            # 定期的な再学習のトリガー判定
            if hasattr(self, '_interaction_count'):
                self._interaction_count += 1
                if self._interaction_count >= 1000:  # 1000件ごとに再学習
                    logger.info("Triggering model retraining due to interaction count")
                    await self.train_model(retrain=True)
                    self._interaction_count = 0
            else:
                self._interaction_count = 1

        except Exception as e:
            logger.error(f"Error updating user interaction: {e}")
            await self.db.rollback()