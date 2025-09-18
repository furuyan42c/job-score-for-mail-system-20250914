"""Add T021 scoring tables

Revision ID: 002_t021_scoring
Revises: 001_initial
Create Date: 2025-09-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '002_t021_scoring'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """T021基礎スコア計算用のテーブルを作成"""

    # 1. エリア給与統計テーブル
    op.create_table(
        'area_salary_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prefecture_code', sa.String(3), nullable=False),
        sa.Column('city_code', sa.String(10), nullable=True),
        sa.Column('avg_salary', sa.Numeric(10, 2), nullable=False),
        sa.Column('std_salary', sa.Numeric(10, 2), nullable=False),
        sa.Column('job_count', sa.Integer(), nullable=False),
        sa.Column('salary_type', sa.String(20), server_default='hourly', nullable=True),
        sa.Column('employment_type_filter', sa.String(50), server_default='1,3,6,8', nullable=True),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prefecture_code', 'city_code', 'salary_type',
                          name='uq_area_salary_location_type')
    )

    op.create_index('idx_area_salary_stats_location', 'area_salary_stats',
                    ['prefecture_code', 'city_code'])
    op.create_index('idx_area_salary_stats_updated', 'area_salary_stats',
                    ['updated_at'], postgresql_using='btree')

    # 2. ユーザーアクション履歴テーブル
    op.create_table(
        'user_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('endcl_cd', sa.String(50), nullable=True),
        sa.Column('action_type', sa.String(20), nullable=False),
        sa.Column('action_timestamp', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('referrer', sa.String(200), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.CheckConstraint("action_type IN ('view', 'apply', 'application', 'click', 'favorite')",
                          name='ck_user_actions_type'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_user_actions_endcl_timestamp', 'user_actions',
                    ['endcl_cd', 'action_timestamp'], postgresql_using='btree')
    op.create_index('idx_user_actions_user_timestamp', 'user_actions',
                    ['user_id', 'action_timestamp'], postgresql_using='btree')
    op.create_index('idx_user_actions_type_timestamp', 'user_actions',
                    ['action_type', 'action_timestamp'], postgresql_using='btree')
    op.create_index('idx_user_actions_job_id', 'user_actions',
                    ['job_id'], postgresql_where=sa.text('job_id IS NOT NULL'))

    # 3. 企業人気度キャッシュテーブル
    op.create_table(
        'company_popularity_cache',
        sa.Column('endcl_cd', sa.String(50), nullable=False),
        sa.Column('views_360d', sa.Integer(), server_default='0', nullable=True),
        sa.Column('applications_360d', sa.Integer(), server_default='0', nullable=True),
        sa.Column('applications_7d', sa.Integer(), server_default='0', nullable=True),
        sa.Column('applications_30d', sa.Integer(), server_default='0', nullable=True),
        sa.Column('application_rate_360d', sa.Numeric(5, 4), server_default='0', nullable=True),
        sa.Column('application_rate_30d', sa.Numeric(5, 4), server_default='0', nullable=True),
        sa.Column('popularity_score', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('rank_in_prefecture', sa.Integer(), nullable=True),
        sa.Column('rank_overall', sa.Integer(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.PrimaryKeyConstraint('endcl_cd')
    )

    op.create_index('idx_company_popularity_score', 'company_popularity_cache',
                    ['popularity_score'], postgresql_using='btree')
    op.create_index('idx_company_popularity_updated', 'company_popularity_cache',
                    ['updated_at'], postgresql_using='btree')

    # 4. 求人フィー統計テーブル
    op.create_table(
        'job_fee_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prefecture_code', sa.String(3), nullable=True),
        sa.Column('city_code', sa.String(10), nullable=True),
        sa.Column('occupation_cd1', sa.Integer(), nullable=True),
        sa.Column('occupation_cd2', sa.Integer(), nullable=True),
        sa.Column('avg_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('median_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('std_fee', sa.Numeric(10, 2), nullable=True),
        sa.Column('job_count', sa.Integer(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prefecture_code', 'city_code', 'occupation_cd1', 'occupation_cd2',
                          name='uq_job_fee_stats_location_occupation')
    )

    op.create_index('idx_job_fee_stats_location', 'job_fee_stats',
                    ['prefecture_code', 'city_code'])
    op.create_index('idx_job_fee_stats_occupation', 'job_fee_stats',
                    ['occupation_cd1', 'occupation_cd2'])

    # 5. スコアリング実行ログテーブル
    op.create_table(
        'scoring_execution_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('scoring_version', sa.String(10), server_default='T021', nullable=True),
        sa.Column('basic_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('location_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('category_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('salary_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('feature_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('preference_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('popularity_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('composite_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('used_cache', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('fallback_used', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_scoring_log_user_job', 'scoring_execution_log',
                    ['user_id', 'job_id'])
    op.create_index('idx_scoring_log_created', 'scoring_execution_log',
                    ['created_at'], postgresql_using='btree')

    # 6. 初期データ投入（オプション）
    # このセクションは環境に応じてコメントアウトしてください
    if False:  # 本番環境では True に変更
        populate_initial_data()


def downgrade() -> None:
    """テーブルを削除してロールバック"""
    op.drop_table('scoring_execution_log')
    op.drop_table('job_fee_stats')
    op.drop_table('company_popularity_cache')
    op.drop_table('user_actions')
    op.drop_table('area_salary_stats')


def populate_initial_data():
    """初期データの投入（オプション）"""
    from sqlalchemy import text

    connection = op.get_bind()

    # エリア統計データの初期計算
    connection.execute(text("""
        INSERT INTO area_salary_stats (
            prefecture_code, city_code, avg_salary, std_salary, job_count
        )
        SELECT
            jl.prefecture_code,
            jl.city_code,
            AVG((j.min_salary + j.max_salary) / 2) as avg_salary,
            COALESCE(STDDEV((j.min_salary + j.max_salary) / 2), 200) as std_salary,
            COUNT(*) as job_count
        FROM jobs j
        JOIN job_locations jl ON j.job_id = jl.job_id
        WHERE j.min_salary > 0
            AND j.max_salary > 0
            AND j.employment_type_cd IN (1, 3, 6, 8)
        GROUP BY jl.prefecture_code, jl.city_code
        ON CONFLICT (prefecture_code, city_code, salary_type)
        DO UPDATE SET
            avg_salary = EXCLUDED.avg_salary,
            std_salary = EXCLUDED.std_salary,
            job_count = EXCLUDED.job_count,
            updated_at = CURRENT_TIMESTAMP
    """))

    # 企業人気度データの初期計算（user_actionsテーブルが存在する場合）
    try:
        connection.execute(text("""
            INSERT INTO company_popularity_cache (
                endcl_cd, views_360d, applications_360d, popularity_score
            )
            SELECT
                endcl_cd,
                COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) as views_360d,
                COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END) as applications_360d,
                CASE
                    WHEN COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) > 0
                    THEN LEAST(100,
                        (COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END)::decimal /
                         COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END)) * 100 * 6.67
                    )
                    ELSE 30
                END as popularity_score
            FROM user_actions
            WHERE action_timestamp > CURRENT_DATE - INTERVAL '360 days'
                AND endcl_cd IS NOT NULL
            GROUP BY endcl_cd
            ON CONFLICT (endcl_cd)
            DO UPDATE SET
                views_360d = EXCLUDED.views_360d,
                applications_360d = EXCLUDED.applications_360d,
                popularity_score = EXCLUDED.popularity_score,
                updated_at = CURRENT_TIMESTAMP
        """))
    except Exception as e:
        print(f"Warning: Could not populate company popularity cache: {e}")