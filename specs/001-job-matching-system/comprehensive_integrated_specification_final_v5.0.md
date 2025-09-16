# バイト求人マッチングシステム 最終統合仕様書 v5.0

**作成日**: 2025-09-16  
**文書タイプ**: 最終統合仕様書（全バージョン・全ファイル統合版）  
**ステータス**: Production Ready  
**対象読者**: 開発チーム、プロジェクトマネージャー、ステークホルダー  
**統合元**: v1.0, v3.0, v4.0, answers.md, asks.md, data-model.md, plan.md, tasks.md, research.md, quickstart.md

---

## 目次

1. [エグゼクティブサマリー](#1-エグゼクティブサマリー)
2. [システム概要](#2-システム概要)
3. [技術アーキテクチャ](#3-技術アーキテクチャ)
4. [データモデル設計](#4-データモデル設計)
5. [コア機能詳細](#5-コア機能詳細)
6. [スコアリングアルゴリズム詳細](#6-スコアリングアルゴリズム詳細)
7. [6セクションメール構成](#7-6セクションメール構成)
8. [バッチ処理パイプライン](#8-バッチ処理パイプライン)
9. [モニタリングシステム](#9-モニタリングシステム)
10. [実装計画](#10-実装計画)
11. [品質保証](#11-品質保証)
12. [運用要件](#12-運用要件)
13. [クイックスタートガイド](#13-クイックスタートガイド)
14. [付録](#14-付録)

---

## 1. エグゼクティブサマリー

### 1.1 プロジェクト概要
本システムは、10万件のバイト求人データから1万人のユーザーそれぞれに最適な40件を毎日自動選定し、パーソナライズされたメール配信準備を行う大規模マッチングシステムです。

### 1.2 ビジネス価値
- **応募率向上**: 従来比150%の応募率向上を目標
- **ユーザー満足度**: パーソナライゼーションによる関連性の高い求人提供
- **運用効率化**: 完全自動化により手動作業を排除

### 1.3 主要成果物
- 毎日1万通のパーソナライズメール生成（6セクション×40求人）
- リアルタイムSQLモニタリングダッシュボード
- 30分以内の全処理完了保証

### 1.4 主要変更点（v4.0→v5.0）
- **実装詳細の完全統合**: answers.mdの全実装コードを統合
- **GPT-5 nano統合**: メール件名生成の詳細実装
- **継続的検証戦略**: tasks.mdのCHECKポイント手法統合
- **MCPサーバー活用**: Sequential, Serena, Magic等の効果的活用戦略
- **クイックスタートガイド**: 30分セットアップ手順の統合

---

## 2. システム概要

### 2.1 システムの目的
求職者により良いバイト求人情報を届けることで、マッチング精度を向上させ、応募率と採用成功率を最大化する。

### 2.2 主要機能一覧

| 機能カテゴリ | 機能名 | 説明 |
|------------|--------|------|
| データ処理 | CSVインポート | 10万件の求人データを日次でインポート |
| スコアリング | 3段階スコア計算 | 基礎・SEO・パーソナライズスコアの算出 |
| カテゴリ分類 | 自動分類 | 14ニーズ×12職種カテゴリへの分類 |
| マッチング | 最適化選定 | 各ユーザーに最適な40件を選定 |
| メール生成 | 6セクション構成 | パーソナライズされたHTML生成 |
| モニタリング | SQL実行画面 | リアルタイムデータ確認 |

### 2.3 システム利用者

#### エンドユーザー（求職者）
- **規模**: 1万人
- **特徴**: 18-65歳、アルバイト・パート希望者
- **地域**: 全国（主に都市部）

#### システム管理者
- **規模**: 5-10名
- **役割**: データ監視、エラー対応、パフォーマンス管理

### 2.4 配信メール例（6セクション構成）

```
━━━━━━━━━━━━━━━━━━━━━━━━
📧 ゲットバイト通信　2025年7月15日号
━━━━━━━━━━━━━━━━━━━━━━━━
※本メールは「ゲットバイト」にご登録の
直己 様（東京都小金井市在住）にお届けしています。

こんにちは、ゲットバイト編集部です！
「夏ボ、まだ間に合う？」── そんな声にお応えして
日払い × 高時給 × 駅近 を中心に厳選した **超おすすめ40求人** をお届けします。

─────────────────────
◆ 編集部おすすめ人気バイト TOP5【NEW】
─────────────────────
[fee×応募数で選定された注目求人]

─────────────────────
◆ あなたにおすすめ求人 TOP5
─────────────────────
[パーソナライズスコア上位求人]

◆ 東京都おすすめ求人 TOP10
[都道府県内＋職種マッチング]

◆ 小金井市で人気のバイト 8選
[市区町村周辺求人]

◆ 編集部おすすめ "高収入・日払い" TOP7
[高時給 OR 日払い可能求人]

◆ 新着求人 TOP5
[7日以内投稿求人]

[以下、6セクション続く...]
```

---

## 3. 技術アーキテクチャ

### 3.1 技術スタック詳細

```yaml
backend:
  language: Python 3.11
  framework: FastAPI
  batch_processor: APScheduler
  data_processing: 
    - pandas 2.x with PyArrow backend
    - scikit-learn 1.3+
    - numpy 1.24+
    - implicit 0.7+ (協調フィルタリング)
  ai_integration:
    - openai 1.0+ (GPT-5 nano)
    - fallback: rule-based generation
  database_client: supabase-py v2.x
  testing: pytest, pytest-asyncio
  
frontend:
  language: TypeScript 5.0
  framework: Next.js 14 (App Router)
  ui_library: React 18
  styling: Tailwind CSS 3.3
  state_management: Zustand 4.4
  data_fetching: SWR 2.2
  testing: Jest, React Testing Library
  
database:
  primary: Supabase (PostgreSQL 15)
  connection_pool: PgBouncer
  backup: Daily snapshots
  
infrastructure:
  platform: Ubuntu 22.04 LTS
  runtime: Node.js 20 LTS
  containerization: Docker (optional)
  monitoring: 
    - Grafana (メトリクス可視化)
    - Prometheus (メトリクス収集)
    - Sentry (エラートラッキング)
```

### 3.2 システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Batch Process (03:00-06:00)          │
├─────────────────┬──────────────────┬────────────────────────┤
│   Phase 1       │     Phase 2      │      Phase 3           │
│   Data Import   │     Scoring      │      Matching          │
│   CSV→DB        │  3 algorithms    │    10K users           │
│   (100K jobs)   │  (Basic,SEO,     │    (40 jobs/user)      │
│                 │   Personalized)  │                        │
└─────────────────┴──────────────────┴────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Email Generation (Phase 4)                   │
│          6 Sections × 40 Jobs = Personalized Content         │
│   ┌──────────────────────────────────────────────────┐      │
│   │ 1. Editorial Picks (5)  - fee × clicks          │      │
│   │ 2. TOP5 (5)            - Personalized score     │      │
│   │ 3. Regional (10)       - Prefecture match       │      │
│   │ 4. Nearby (8)          - City area match        │      │
│   │ 5. High Income (7)     - Salary/Daily pay       │      │
│   │ 6. New (5)             - Within 7 days          │      │
│   └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                SQL Monitoring Interface                       │
│                    (Next.js + Supabase)                      │
│   - Real-time query execution                                │
│   - Data visualization dashboard                             │
│   - Error log viewer                                         │
│   - Manual batch trigger                                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 並列処理最適化戦略

```yaml
parallel_groups:
  group_a:  # 独立実行可能
    - database_setup
    - frontend_base_setup
    - test_environment_setup
    max_parallel: 3
    estimated_time: 20分（通常1時間）
    
  group_b:  # group_a完了後
    - csv_import
    - scoring_implementation
    - ui_implementation
    max_parallel: 3
    estimated_time: 1時間（通常3時間）
    
  group_c:  # group_b完了後
    - matching_process
    - email_generation
    - integration_testing
    max_parallel: 2
    estimated_time: 1.5時間（通常3時間）
    
performance_gains:
  traditional_sequential: 8時間
  with_parallelization: 3時間
  improvement: 62.5%
```

### 3.4 MCPサーバー活用戦略

| サーバー | 用途 | 対象タスク | 効率向上 |
|----------|------|-----------|---------
| **Sequential** | 複雑な分析、システム設計 | T011-T025 (テスト設計) | 30-50% |
| **Serena** | 大規模コード操作、シンボル管理 | T026-T045 (実装) | 40-60% |
| **Magic** | UI コンポーネント生成 | T051-T055 (Frontend) | 50-70% |
| **Context7** | ライブラリドキュメント参照 | T003, T036-T040 (依存関係) | 20-30% |
| **Playwright** | E2Eテスト | T056-T057 (統合テスト) | 60-80% |

---

## 4. データモデル設計

### 4.1 ER図概要

```mermaid
erDiagram
    users ||--o{ user_actions : "performs"
    users ||--o{ user_profiles : "has"
    users ||--o{ user_job_mapping : "matches"
    jobs ||--o{ job_enrichment : "has"
    jobs ||--o{ user_job_mapping : "recommended"
    user_job_mapping ||--o{ daily_job_picks : "selected"
    daily_job_picks ||--o{ daily_email_queue : "generates"
    
    jobs }o--|| prefecture_master : "located_in"
    jobs }o--|| city_master : "located_in"
    jobs }o--|| occupation_master : "categorized_as"
    jobs }o--|| employment_type_master : "has_type"
```

### 4.2 主要テーブル定義（20テーブル）

#### トランザクションテーブル（8）
1. **jobs** - 求人マスター（10万件、100+フィールド）
2. **users** - ユーザー基本情報（1万件）
3. **user_actions** - 行動履歴（応募、クリック、開封）
4. **user_profiles** - ユーザープロファイル（応募傾向集計）
5. **user_job_mapping** - マッチング結果（日次40万件）
6. **daily_job_picks** - 選定求人（配信用整形済み）
7. **daily_email_queue** - メール配信キュー（6セクション構成）
8. **job_enrichment** - 求人拡張情報（スコア、カテゴリ）

#### マスターテーブル（10）
9. **occupation_master** - 職種マスター（大中小分類）
10. **prefecture_master** - 都道府県マスター
11. **city_master** - 市区町村マスター
12. **adjacent_cities** - 隣接市区町村関係
13. **employment_type_master** - 雇用形態（アルバイト、パート等）
14. **salary_type_master** - 給与タイプ（時給、日給、月給）
15. **feature_master** - 特徴マスター（100+種類）
16. **needs_category_master** - ニーズカテゴリ定義
17. **semrush_keywords** - SEOキーワード
18. **keyword_scoring** - キーワードスコアリング

#### 補助テーブル（2）
19. **jobs_match_raw** - マッチング用簡易データ
20. **jobs_contents_raw** - コンテンツ表示用データ

### 4.3 重要フィールド定義

```sql
-- jobsテーブルの重要フィールド（100+フィールドから抜粋）
CREATE TABLE jobs (
    job_id BIGINT PRIMARY KEY,
    endcl_cd VARCHAR(20),  -- エンドクライアントコード（企業識別）
    application_name TEXT,  -- 求人タイトル
    company_name VARCHAR(255),
    
    -- 給与情報
    min_salary INTEGER,
    max_salary INTEGER,
    fee INTEGER,  -- 応募促進費用（0-5000円）
    
    -- 場所情報
    pref_cd CHAR(2),
    city_cd VARCHAR(5),
    station_name_eki VARCHAR(100),
    
    -- カテゴリ
    occupation_cd1 INTEGER,  -- 大分類
    employment_type_cd INTEGER,  -- 雇用形態
    
    -- 特徴
    feature_codes TEXT,  -- カンマ区切り
    hours TEXT,  -- 勤務時間（HTML含む可能性）
    
    -- 日付
    posting_date TIMESTAMPTZ,
    end_at TIMESTAMPTZ
);

-- user_profilesテーブル（集計データ）
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY,
    total_applications INTEGER,
    
    -- 頻度データ（"コード:回数,コード:回数"形式）
    applied_pref_cds TEXT,  -- "13:5,14:3"
    applied_city_cds TEXT,
    applied_occupation_cd1s TEXT,
    applied_employment_type_cds TEXT,
    applied_endcl_cds TEXT,
    
    -- 統計データ（JSON形式）
    applied_salary_stats JSONB,  -- {"avg": 1200, "min": 1000, "max": 2000}
    
    profile_updated_at TIMESTAMPTZ
);
```

### 4.4 インデックス戦略

#### 高頻度クエリ用インデックス
```sql
-- 地域検索用
CREATE INDEX idx_jobs_location ON jobs (pref_cd, city_cd, posting_date);

-- カテゴリ検索用
CREATE INDEX idx_jobs_category ON jobs (occupation_cd1, employment_type_cd);

-- ユーザーマッチング用
CREATE INDEX idx_user_job_mapping_user ON user_job_mapping (user_id, match_date, match_score DESC);

-- スコアランキング用
CREATE INDEX idx_job_enrichment_scores ON job_enrichment (basic_score DESC, seo_score DESC);
```

### 4.5 パーティショニング戦略

```sql
-- 時系列パーティション
-- user_actions: 月単位パーティション
CREATE TABLE user_actions_202509 PARTITION OF user_actions
FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

-- user_job_mapping: 週単位パーティション
CREATE TABLE user_job_mapping_w38 PARTITION OF user_job_mapping
FOR VALUES FROM ('2025-09-15') TO ('2025-09-22');

-- 保持期間
-- user_actions: 6ヶ月
-- user_job_mapping: 1ヶ月
-- daily_email_queue: 7日
```

---

## 5. コア機能詳細

### 5.1 求人データインポート機能

#### 機能概要
日次で10万件のCSVデータをインポートし、データクレンジングとバリデーションを実行。

#### 実装詳細

```python
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

def import_jobs_csv(csv_path: str, batch_size: int = 1000) -> Dict[str, int]:
    """
    CSVデータのバッチインポート処理
    
    Args:
        csv_path: CSVファイルパス
        batch_size: バッチサイズ（デフォルト1000件）
        
    Returns:
        処理結果統計
    """
    logger = logging.getLogger(__name__)
    stats = {'total': 0, 'imported': 0, 'skipped': 0, 'errors': 0}
    
    # メモリ効率的な読み込み設定
    dtype_config = {
        'job_id': 'uint32',
        'endcl_cd': 'category',
        'pref_cd': 'category',
        'city_cd': 'category',
        'occupation_cd1': 'uint16',
        'employment_type_cd': 'uint8',
        'min_salary': 'uint32',
        'max_salary': 'uint32',
        'fee': 'uint16'
    }
    
    try:
        # 1. CSVを1000件単位でチャンク読み込み
        for chunk_num, chunk in enumerate(pd.read_csv(
            csv_path, 
            chunksize=batch_size,
            dtype=dtype_config,
            low_memory=False
        )):
            logger.info(f"Processing chunk {chunk_num + 1}, size: {len(chunk)}")
            
            # 2. データクレンジング
            chunk = clean_salary_data(chunk)
            chunk = validate_location_data(chunk)
            chunk = parse_feature_codes(chunk)
            
            # 3. バリデーション
            valid_chunk = apply_business_rules(chunk)
            
            # 4. Supabaseへ一括挿入
            if len(valid_chunk) > 0:
                insert_result = batch_insert_jobs(valid_chunk)
                stats['imported'] += insert_result['success']
                stats['errors'] += insert_result['errors']
            
            stats['total'] += len(chunk)
            stats['skipped'] += len(chunk) - len(valid_chunk)
            
            # 5. メモリクリーンアップ
            del chunk, valid_chunk
            
            logger.info(f"Chunk {chunk_num + 1} completed: {stats}")
            
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise
        
    return stats

def clean_salary_data(df: pd.DataFrame) -> pd.DataFrame:
    """給与データの正規化"""
    # 給与の異常値処理
    df.loc[df['min_salary'] > 5000, 'min_salary'] = np.nan
    df.loc[df['max_salary'] > 5000, 'max_salary'] = np.nan
    df.loc[df['min_salary'] < 800, 'min_salary'] = np.nan
    
    # 最低賃金チェック（都道府県別）
    prefecture_min_wages = load_prefecture_min_wages()
    for pref_cd, min_wage in prefecture_min_wages.items():
        mask = (df['pref_cd'] == pref_cd) & (df['min_salary'] < min_wage)
        df.loc[mask, 'min_salary'] = min_wage
    
    return df

def validate_location_data(df: pd.DataFrame) -> pd.DataFrame:
    """場所データの検証"""
    # 都道府県コード検証
    valid_pref_cds = get_valid_prefecture_codes()
    df = df[df['pref_cd'].isin(valid_pref_cds)]
    
    # 市区町村コード検証
    valid_city_mapping = get_prefecture_city_mapping()
    for _, row in df.iterrows():
        if row['city_cd'] not in valid_city_mapping.get(row['pref_cd'], []):
            df.drop(row.name, inplace=True)
    
    return df

def parse_feature_codes(df: pd.DataFrame) -> pd.DataFrame:
    """特徴コードの展開"""
    # カンマ区切りの特徴コードを配列に変換
    df['feature_list'] = df['feature_codes'].str.split(',').fillna([])
    
    # 特徴フラグの作成
    feature_mappings = {
        'daily_payment': ['103', '日払い'],
        'weekly_payment': ['104', '週払い'],
        'no_experience': ['105', '未経験'],
        'student_welcome': ['106', '学生歓迎'],
        'remote_work': ['107', '在宅']
    }
    
    for feature_name, codes in feature_mappings.items():
        df[f'has_{feature_name}'] = df['feature_list'].apply(
            lambda x: any(code in str(x) for code in codes)
        )
    
    return df

def apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """ビジネスルールの適用"""
    # 1. 雇用形態フィルタ（アルバイト、パート等のみ）
    valid_employment_types = [1, 3, 6, 8]
    df = df[df['employment_type_cd'].isin(valid_employment_types)]
    
    # 2. 応募促進費用フィルタ（500円以上）
    df = df[df['fee'] >= 500]
    
    # 3. 投稿日チェック（30日以内）
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    df['posting_date'] = pd.to_datetime(df['posting_date'])
    df = df[df['posting_date'] >= cutoff_date]
    
    # 4. 重複チェック（job_id + endcl_cd）
    df = df.drop_duplicates(subset=['job_id', 'endcl_cd'])
    
    return df

def batch_insert_jobs(df: pd.DataFrame) -> Dict[str, int]:
    """Supabaseへのバッチ挿入"""
    from src.db import get_supabase_client
    
    client = get_supabase_client()
    records = df.to_dict('records')
    result = {'success': 0, 'errors': 0}
    
    try:
        # upsert処理（重複時は更新）
        response = client.table('jobs').upsert(
            records,
            on_conflict='job_id,endcl_cd'
        ).execute()
        
        result['success'] = len(records)
        logging.info(f"Successfully inserted {len(records)} jobs")
        
    except Exception as e:
        result['errors'] = len(records)
        logging.error(f"Batch insert failed: {str(e)}")
        
    return result
```

### 5.2 カテゴリ自動分類

#### 14ニーズベースカテゴリ

| カテゴリ名 | 判定ロジック | 対象フィールド | 実装例 |
|-----------|------------|--------------|--------|
| 日払い・週払い | キーワード検索 | application_name, salary, features | `has_daily_payment OR contains("日払い")` |
| 短期・単発OK | キーワード検索 | application_name, hours | `contains("短期", "単発", "1日")` |
| 高時給 | エリア平均×1.2以上 | min_salary, max_salary | `avg_salary >= area_avg * 1.2` |
| シフト自由 | キーワード検索 | hours, features | `contains("シフト自由", "週1")` |
| 未経験歓迎 | feature_code: 103 | feature_codes | `"103" in feature_codes` |
| 在宅・リモート | キーワード検索 | application_name, features | `contains("在宅", "リモート")` |
| 学生歓迎 | feature_code: 104 | feature_codes | `"104" in feature_codes` |
| 高校生歓迎 | キーワード検索 | application_name, features | `contains("高校生")` |
| 主婦歓迎 | キーワード＋時間帯 | features, hours | `contains("主婦") AND daytime_hours` |
| シニア歓迎 | キーワード検索 | application_name, features | `contains("シニア", "60歳")` |
| 土日のみOK | キーワード検索 | hours | `contains("土日のみ")` |
| 副業・WワークOK | キーワード検索 | application_name, features | `contains("副業", "Wワーク")` |
| 交通費支給 | フラグ確認 | feature_codes | `"108" in feature_codes` |
| 即日勤務OK | キーワード検索 | application_name | `contains("即日")` |

#### 実装コード

```python
def categorize_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """求人の自動カテゴリ分類"""
    
    # ニーズカテゴリの判定
    needs_categories = []
    
    for index, job in df.iterrows():
        job_categories = []
        
        # 1. 日払い・週払い
        if (job.get('has_daily_payment', False) or 
            any(keyword in str(job.get('application_name', '')).lower() 
                for keyword in ['日払い', '週払い'])):
            job_categories.append('日払い・週払い')
        
        # 2. 短期・単発OK
        if any(keyword in str(job.get('application_name', '')).lower() 
               for keyword in ['短期', '単発', '1日のみ']):
            job_categories.append('短期・単発OK')
        
        # 3. 高時給（エリア平均×1.2以上）
        avg_salary = (job.get('min_salary', 0) + job.get('max_salary', 0)) / 2
        area_avg = get_area_average_salary(job.get('pref_cd'))
        if avg_salary >= area_avg * 1.2:
            job_categories.append('高時給')
        
        # 4. シフト自由
        hours_text = str(job.get('hours', '')).lower()
        if any(keyword in hours_text for keyword in ['シフト自由', '週1', '週2']):
            job_categories.append('シフト自由')
        
        # 5. 未経験歓迎
        if '103' in str(job.get('feature_codes', '')):
            job_categories.append('未経験歓迎')
        
        # 6. 在宅・リモート
        if any(keyword in str(job.get('application_name', '')).lower()
               for keyword in ['在宅', 'リモート', 'テレワーク']):
            job_categories.append('在宅・リモート')
        
        # 7. 学生歓迎
        if '104' in str(job.get('feature_codes', '')):
            job_categories.append('学生歓迎')
        
        # 8. 高校生歓迎
        if '高校生' in str(job.get('application_name', '')):
            job_categories.append('高校生歓迎')
        
        # 9. 主婦歓迎（キーワード＋時間帯）
        if ('主婦' in str(job.get('application_name', '')) and
            is_daytime_shift(job.get('hours', ''))):
            job_categories.append('主婦歓迎')
        
        # 10. シニア歓迎
        if any(keyword in str(job.get('application_name', '')).lower()
               for keyword in ['シニア', '60歳', '年齢不問']):
            job_categories.append('シニア歓迎')
        
        # 11. 土日のみOK
        if '土日のみ' in str(job.get('hours', '')):
            job_categories.append('土日のみOK')
        
        # 12. 副業・WワークOK
        if any(keyword in str(job.get('application_name', '')).lower()
               for keyword in ['副業', 'wワーク', 'ダブルワーク']):
            job_categories.append('副業・WワークOK')
        
        # 13. 交通費支給
        if '108' in str(job.get('feature_codes', '')):
            job_categories.append('交通費支給')
        
        # 14. 即日勤務OK
        if '即日' in str(job.get('application_name', '')):
            job_categories.append('即日勤務OK')
        
        needs_categories.append(','.join(job_categories))
    
    df['needs_categories'] = needs_categories
    
    # 職種カテゴリの判定
    df['occupation_category'] = df['occupation_cd1'].apply(
        lambda x: get_occupation_category_name(x)
    )
    
    return df

def get_area_average_salary(pref_cd: str) -> float:
    """都道府県別平均時給の取得"""
    # 都道府県別平均時給データ（実際はDBから取得）
    average_salaries = {
        '13': 1200,  # 東京都
        '14': 1100,  # 神奈川県
        '27': 1050,  # 大阪府
        # その他の都道府県...
    }
    return average_salaries.get(pref_cd, 1000)  # デフォルト1000円

def is_daytime_shift(hours_text: str) -> bool:
    """日中シフトかどうかの判定"""
    if not hours_text:
        return False
    
    # 9:00-17:00のような時間帯を検出
    import re
    daytime_patterns = [
        r'[89][:：]\d{2}.*1[4-7][:：]\d{2}',  # 8:00-16:00等
        r'10[:：]\d{2}.*1[56][:：]\d{2}',    # 10:00-15:00等
    ]
    
    return any(re.search(pattern, hours_text) for pattern in daytime_patterns)
```

#### 12職種カテゴリ

| コード | カテゴリ名 | 含まれる職種 |
|--------|-----------|------------|
| 100 | 飲食・フード系 | ホール、キッチン、カフェ |
| 200 | 販売・サービス系 | アパレル、コンビニ、スーパー |
| 300 | 配送・ドライバー系 | 宅配、引越し、デリバリー |
| 400 | オフィスワーク系 | 事務、データ入力、受付 |
| 500 | 医療・介護・保育系 | 看護助手、介護、保育補助 |
| 600 | 軽作業・工場系 | 梱包、仕分け、検品 |
| 700 | 美容・理容系 | 美容師アシスタント、エステ |
| 800 | 教育系 | 塾講師、家庭教師 |
| 900 | エンタメ系 | イベント、遊園地、カラオケ |
| 1000 | イベント・キャンペーン系 | 設営、運営、PR |
| 1100 | IT・クリエイティブ系 | Web制作、デザイン、動画編集 |
| 1200+ | その他 | 上記以外の職種 |

---

## 6. スコアリングアルゴリズム詳細

### 6.1 基礎スコア（Basic Score）

```python
def calculate_basic_score(job, area_stats, company_popularity):
    """
    基礎スコア計算（0-100点）
    構成要素：時給40%、応募単価報酬30%、企業人気度30%
    """
    # フィルタリング条件
    VALID_EMPLOYMENT_TYPE_CDS = [1, 3, 6, 8]  # アルバイト、パート等
    MIN_FEE_THRESHOLD = 500  # 500円以下は除外
    
    if job.employment_type_cd not in VALID_EMPLOYMENT_TYPE_CDS:
        return 0
    if job.fee <= MIN_FEE_THRESHOLD:
        return 0
    
    # 時給スコア（エリア平均基準）- 40%
    avg_wage = (job.min_salary + job.max_salary) / 2 if job.max_salary else job.min_salary
    area_average = area_stats.get(job.pref_cd, 1000)  # デフォルト1000円
    
    if avg_wage >= area_average * 1.5:  # 1.5倍以上
        hourly_wage_score = 100
    elif avg_wage >= area_average * 1.2:  # 1.2倍以上
        hourly_wage_score = 80
    elif avg_wage >= area_average:  # 平均以上
        hourly_wage_score = 60
    else:  # 平均未満
        hourly_wage_score = max(0, (avg_wage / area_average) * 60)
    
    # 応募単価報酬スコア - 30%
    fee_score = normalize_fee(job.fee)
    
    # 企業人気度スコア（360日間の応募率）- 30%
    popularity_score = calculate_company_popularity_score(
        job.endcl_cd, company_popularity
    )
    
    # 加重平均
    basic_score = (
        hourly_wage_score * 0.40 +
        fee_score * 0.30 +
        popularity_score * 0.30
    )
    
    return min(100, max(0, basic_score))

def normalize_fee(fee):
    """
    応募単価報酬の正規化
    500円以下: 0点、5000円以上: 100点
    """
    if fee <= 500:
        return 0
    elif fee >= 5000:
        return 100
    else:
        return (fee - 500) / (5000 - 500) * 100

def calculate_company_popularity_score(endcl_cd, company_popularity):
    """
    企業人気度スコア計算
    過去360日間の応募率に基づく
    """
    if endcl_cd not in company_popularity:
        return 30  # デフォルトスコア
    
    stats = company_popularity[endcl_cd]
    application_rate = stats.get('application_rate', 0)
    
    if application_rate >= 0.15:  # 15%以上
        return 100
    elif application_rate >= 0.10:  # 10%以上
        return 80
    elif application_rate >= 0.05:  # 5%以上
        return 60
    elif application_rate >= 0.02:  # 2%以上
        return 40
    else:
        return 20
```

### 6.2 SEOスコア

```python
# フィールド別重み付け設定
FIELD_WEIGHT_CONFIG = {
    'application_name': 1.5,    # 求人タイトル - 高い重み
    'company_name': 1.5,        # 企業名 - 高い重み
    'salary': 0.3,              # 給与 - 小さい重み
    'hours': 0.3,               # 勤務時間 - 小さい重み
    'station_name_eki': 0.5,    # 最寄駅 - 中程度
    'feature_codes': 0.8        # 特徴 - やや高い重み
}

def calculate_seo_score(job, keywords_df):
    """
    SEOキーワードマッチングスコア（0-100点）
    """
    total_score = 0
    matched_keywords = []
    
    for field_name, weight in FIELD_WEIGHT_CONFIG.items():
        field_value = normalize_text(getattr(job, field_name, ''))
        
        for _, keyword_row in keywords_df.iterrows():
            keyword = keyword_row['processed']  # 正規化済みキーワード
            
            if keyword in field_value:
                # 検索ボリュームに基づく基本スコア
                volume = keyword_row['volume']
                if volume >= 10000:
                    base_score = 15
                elif volume >= 5000:
                    base_score = 10
                elif volume >= 1000:
                    base_score = 7
                else:
                    base_score = 3
                
                # フィールド重みを適用
                field_score = base_score * weight
                total_score += field_score
                matched_keywords.append({
                    'keyword': keyword_row['keyword'],
                    'field': field_name,
                    'score': field_score
                })
                
                # 最大7キーワードまで
                if len(matched_keywords) >= 7:
                    break
        
        if len(matched_keywords) >= 7:
            break
    
    return min(100, total_score), matched_keywords

def normalize_text(text):
    """テキストの正規化"""
    if not text:
        return ''
    
    import re
    
    # HTMLタグの除去
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # 改行・タブの除去
    text = re.sub(r'[\r\n\t]', ' ', text)
    
    # 複数スペースを単一スペースに
    text = re.sub(r'\s+', ' ', text)
    
    # 小文字化
    text = text.lower().strip()
    
    return text

def load_semrush_keywords():
    """SEMrushキーワードの読み込み"""
    from src.db import get_supabase_client
    
    client = get_supabase_client()
    
    # キーワードマスターから取得
    response = client.table('semrush_keywords').select(
        'keyword', 'processed', 'volume', 'difficulty'
    ).order('volume', desc=True).limit(1000).execute()
    
    import pandas as pd
    return pd.DataFrame(response.data)
```

### 6.3 パーソナライズスコア

```python
def calculate_personalized_score(job, user_profile):
    """
    ユーザープロファイルベースのパーソナライズスコア（0-100点）
    """
    if not user_profile or user_profile.total_applications == 0:
        return 50  # デフォルトスコア
    
    score_components = []
    weights = []
    
    # 都道府県マッチング（20%）
    if user_profile.applied_pref_cds:
        pref_matches = calculate_location_match(
            job.pref_cd, 
            parse_frequency_string(user_profile.applied_pref_cds)
        )
        score_components.append(pref_matches)
        weights.append(0.20)
    
    # 市区町村マッチング（15%）
    if user_profile.applied_city_cds:
        city_matches = calculate_location_match(
            job.city_cd,
            parse_frequency_string(user_profile.applied_city_cds)
        )
        score_components.append(city_matches)
        weights.append(0.15)
    
    # 職種マッチング（20%）
    if user_profile.applied_occupation_cd1s:
        occupation_matches = calculate_category_match(
            job.occupation_cd1,
            parse_frequency_string(user_profile.applied_occupation_cd1s)
        )
        score_components.append(occupation_matches)
        weights.append(0.20)
    
    # 給与レンジマッチング（15%）
    if user_profile.applied_salary_stats:
        import json
        salary_stats = json.loads(user_profile.applied_salary_stats)
        salary_matches = calculate_salary_range_match(
            job.min_salary, job.max_salary, salary_stats
        )
        score_components.append(salary_matches)
        weights.append(0.15)
    
    # エンドクライアント重複チェック（15%）
    # 2週間以内応募企業にはペナルティ
    if user_profile.applied_endcl_cds:
        endcl_freq = parse_frequency_string(user_profile.applied_endcl_cds)
        if was_applied_within_2weeks(job.endcl_cd, user_profile.user_id):
            score_components.append(10)  # 大幅減点
        else:
            score_components.append(50)  # 通常スコア
        weights.append(0.15)
    
    # 雇用形態マッチング（15%）
    if user_profile.applied_employment_type_cds:
        employment_matches = calculate_category_match(
            job.employment_type_cd,
            parse_frequency_string(user_profile.applied_employment_type_cds)
        )
        score_components.append(employment_matches)
        weights.append(0.15)
    
    # 重み付き平均
    if score_components:
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(score_components, weights))
        final_score = weighted_score / total_weight if total_weight > 0 else 50
    else:
        final_score = 50
    
    return min(100, max(0, final_score))

def parse_frequency_string(freq_str):
    """
    頻度文字列のパース
    "13:5,14:3" -> {13: 5, 14: 3}
    """
    if not freq_str:
        return {}
    
    result = {}
    try:
        for pair in freq_str.split(','):
            if ':' in pair:
                code, count = pair.split(':')
                result[code.strip()] = int(count.strip())
    except (ValueError, AttributeError):
        pass
    
    return result

def calculate_location_match(job_location, user_frequencies):
    """場所マッチングスコアの計算"""
    if str(job_location) in user_frequencies:
        frequency = user_frequencies[str(job_location)]
        total_applications = sum(user_frequencies.values())
        match_rate = frequency / total_applications
        
        # マッチ率に基づいてスコア計算
        if match_rate >= 0.5:  # 50%以上
            return 100
        elif match_rate >= 0.3:  # 30%以上
            return 80
        elif match_rate >= 0.1:  # 10%以上
            return 60
        else:
            return 40
    else:
        return 20  # 未経験地域

def calculate_salary_range_match(job_min, job_max, user_salary_stats):
    """給与レンジマッチングスコアの計算"""
    user_avg = user_salary_stats.get('avg', 0)
    user_min = user_salary_stats.get('min', 0)
    user_max = user_salary_stats.get('max', 0)
    
    if not user_avg:
        return 50  # デフォルト
    
    job_avg = (job_min + job_max) / 2 if job_max else job_min
    
    # 給与差の割合を計算
    diff_ratio = abs(job_avg - user_avg) / user_avg if user_avg > 0 else 1
    
    if diff_ratio <= 0.1:  # ±10%以内
        return 100
    elif diff_ratio <= 0.2:  # ±20%以内
        return 80
    elif diff_ratio <= 0.3:  # ±30%以内
        return 60
    else:
        return 30

def was_applied_within_2weeks(endcl_cd, user_id):
    """2週間以内の応募履歴チェック"""
    from src.db import get_supabase_client
    from datetime import datetime, timedelta
    
    client = get_supabase_client()
    
    cutoff_date = datetime.now() - timedelta(days=14)
    
    response = client.table('user_actions').select('action_id').match({
        'user_id': user_id,
        'endcl_cd': endcl_cd,
        'action_type': 'applied'
    }).gte('action_timestamp', cutoff_date.isoformat()).execute()
    
    return len(response.data) > 0
```

---

## 7. 6セクションメール構成

### 7.1 セクション構成と選定ロジック

| # | セクション名 | 件数 | 選定基準 | 優先度 |
|---|------------|------|---------|--------|
| 1 | 編集部おすすめ (editorial_picks) | 5件 | fee × 応募クリック数 | 最高 |
| 2 | あなたにおすすめTOP5 (top5) | 5件 | パーソナライズスコア上位 | 高 |
| 3 | 地域別求人 (regional) | 10件 | 都道府県内＋職種マッチ | 中 |
| 4 | 近隣求人 (nearby) | 8件 | 市区町村周辺 | 中 |
| 5 | 高収入・日払い (high_income) | 7件 | 高時給 OR 日払い可 | 低 |
| 6 | 新着求人 (new) | 5件 | 7日以内投稿 | 最低 |

### 7.2 重複除外処理

```python
def select_40_jobs_with_sections(user_id, all_candidates):
    """
    40件選定（6セクション、重複なし）
    """
    # 優先順位順に処理
    priority_order = [
        'editorial_picks',  # 最優先
        'top5',
        'regional',
        'nearby',
        'high_income',
        'new'
    ]
    
    section_counts = {
        'editorial_picks': 5,
        'top5': 5,
        'regional': 10,
        'nearby': 8,
        'high_income': 7,
        'new': 5
    }
    
    selected_job_ids = set()
    section_results = {}
    
    for section in priority_order:
        # セクション候補を取得
        candidates = get_candidates_for_section(section, user_id, all_candidates)
        
        # 既選択求人を除外
        candidates = candidates[~candidates['job_id'].isin(selected_job_ids)]
        
        # 必要件数を選定
        section_count = section_counts[section]
        
        if len(candidates) >= section_count:
            if section == 'editorial_picks':
                selected = candidates.nlargest(section_count, 'editorial_score')
            elif section == 'top5':
                selected = candidates.nlargest(section_count, 'personalized_score')
            else:
                selected = candidates.nlargest(section_count, 'total_score')
        else:
            # 不足分は他のセクションから補完
            selected = candidates
            shortage = section_count - len(candidates)
            
            # 補完候補（既選択を除く）
            fallback_candidates = all_candidates[
                ~all_candidates['job_id'].isin(selected_job_ids) &
                ~all_candidates['job_id'].isin(candidates['job_id'])
            ]
            
            if len(fallback_candidates) >= shortage:
                fallback = fallback_candidates.nlargest(shortage, 'total_score')
                selected = pd.concat([selected, fallback])
        
        # 結果を保存
        section_results[section] = selected
        selected_job_ids.update(selected['job_id'])
        
        logging.info(f"Section {section}: selected {len(selected)} jobs")
    
    # 総件数確認
    total_selected = sum(len(jobs) for jobs in section_results.values())
    logging.info(f"Total jobs selected: {total_selected}")
    
    return section_results

def get_candidates_for_section(section, user_id, all_candidates):
    """セクション別候補取得"""
    
    user_profile = get_user_profile(user_id)
    
    if section == 'editorial_picks':
        # 編集部おすすめ: fee × クリック数順
        candidates = all_candidates.copy()
        candidates['editorial_score'] = calculate_editorial_popularity_score(
            candidates, user_profile
        )
        return candidates[candidates['editorial_score'] > 0]
    
    elif section == 'top5':
        # TOP5: パーソナライズスコア順
        return all_candidates.nlargest(50, 'personalized_score')
    
    elif section == 'regional':
        # 地域別: 都道府県一致
        user_pref = user_profile.get('pref_cd') if user_profile else None
        if user_pref:
            regional_jobs = all_candidates[
                all_candidates['pref_cd'] == user_pref
            ]
            return regional_jobs.nlargest(20, 'total_score')
        else:
            return all_candidates.nlargest(20, 'total_score')
    
    elif section == 'nearby':
        # 近隣: 市区町村＋隣接エリア
        user_city = user_profile.get('city_cd') if user_profile else None
        if user_city:
            # 隣接市区町村を取得
            adjacent_cities = get_adjacent_cities(user_city)
            nearby_jobs = all_candidates[
                all_candidates['city_cd'].isin([user_city] + adjacent_cities)
            ]
            return nearby_jobs.nlargest(15, 'total_score')
        else:
            return all_candidates.nlargest(15, 'total_score')
    
    elif section == 'high_income':
        # 高収入・日払い
        high_income_jobs = all_candidates[
            (all_candidates['is_high_salary'] == True) |
            (all_candidates['has_daily_payment'] == True)
        ]
        return high_income_jobs.nlargest(15, 'total_score')
    
    elif section == 'new':
        # 新着: 7日以内
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=7)
        new_jobs = all_candidates[
            all_candidates['posting_date'] >= cutoff_date
        ]
        return new_jobs.nlargest(15, 'total_score')
    
    return all_candidates.head(0)  # 空のDataFrame
```

### 7.3 編集部おすすめロジック（NEW）

```python
def calculate_editorial_popularity_score(candidates_df, user_profile):
    """
    編集部おすすめスコア計算
    fee（応募促進費用）× 実際の応募クリック数
    """
    scores = []
    
    for _, job in candidates_df.iterrows():
        # 基本スコア = fee × 応募クリック数
        fee = job.get('fee', 0)
        recent_applications = get_recent_application_count(job['job_id'])
        
        base_score = fee * recent_applications
        
        # 地域による重み付け
        location_weight = get_location_weight(job, user_profile)
        # 同一市区町村: 1.0
        # 近隣市区町村: 0.7
        # 同一都道府県: 0.5
        # その他: 0.3
        
        # 2週間以内応募企業は除外
        if was_applied_within_2weeks(job['endcl_cd'], user_profile.get('user_id')):
            final_score = 0
        else:
            final_score = base_score * location_weight
        
        scores.append(final_score)
    
    return scores

def get_recent_application_count(job_id):
    """最近30日間の応募数取得"""
    from src.db import get_supabase_client
    from datetime import datetime, timedelta
    
    client = get_supabase_client()
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    response = client.table('user_actions').select('action_id').match({
        'job_id': job_id,
        'action_type': 'applied'
    }).gte('action_timestamp', cutoff_date.isoformat()).execute()
    
    return len(response.data)

def get_location_weight(job, user_profile):
    """地域による重み付け計算"""
    if not user_profile:
        return 0.3
    
    user_city = user_profile.get('city_cd')
    user_pref = user_profile.get('pref_cd')
    
    job_city = job.get('city_cd')
    job_pref = job.get('pref_cd')
    
    if user_city and job_city == user_city:
        return 1.0  # 同一市区町村
    
    if user_city and job_city in get_adjacent_cities(user_city):
        return 0.7  # 近隣市区町村
    
    if user_pref and job_pref == user_pref:
        return 0.5  # 同一都道府県
    
    return 0.3  # その他

def get_adjacent_cities(city_cd):
    """隣接市区町村の取得"""
    from src.db import get_supabase_client
    
    client = get_supabase_client()
    
    response = client.table('adjacent_cities').select('adjacent_city_cd').match({
        'city_cd': city_cd
    }).execute()
    
    return [row['adjacent_city_cd'] for row in response.data]
```

### 7.4 GPT-5 nano統合による件名生成

```python
import openai
from typing import Optional, Dict, Any
import logging

class EmailSubjectGenerator:
    """GPT-5 nanoを使用したメール件名生成"""
    
    def __init__(self):
        self.client = openai.OpenAI()
        self.logger = logging.getLogger(__name__)
    
    def generate_subject(self, user_profile: Dict, selected_jobs: Dict) -> str:
        """
        パーソナライズされたメール件名を生成
        
        Args:
            user_profile: ユーザープロファイル情報
            selected_jobs: 6セクションの選定求人
            
        Returns:
            生成されたメール件名
        """
        try:
            # プロンプトの構築
            prompt = self._build_prompt(user_profile, selected_jobs)
            
            # GPT-5 nano呼び出し
            response = self.client.chat.completions.create(
                model="gpt-5-nano",  # 実際のモデル名に置き換え
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは日本のアルバイト求人メールの件名を作成する専門家です。魅力的で開封率の高い件名を50文字以内で作成してください。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.7,
                top_p=0.9
            )
            
            subject = response.choices[0].message.content.strip()
            
            # 文字数制限チェック
            if len(subject) > 50:
                subject = subject[:47] + "..."
            
            self.logger.info(f"Generated subject: {subject}")
            return subject
            
        except Exception as e:
            self.logger.error(f"GPT-5 nano error: {str(e)}")
            # フォールバック処理
            return self._generate_fallback_subject(user_profile, selected_jobs)
    
    def _build_prompt(self, user_profile: Dict, selected_jobs: Dict) -> str:
        """プロンプト構築"""
        
        # ユーザー情報
        location = f"{user_profile.get('prefecture_name', '')} {user_profile.get('city_name', '')}"
        age_group = user_profile.get('age_group', '')
        
        # 求人の特徴抽出
        editorial_picks = selected_jobs.get('editorial_picks', [])
        top_jobs = selected_jobs.get('top5', [])
        
        # 主要キーワード抽出
        keywords = []
        high_salary_count = 0
        daily_payment_count = 0
        
        for job in editorial_picks + top_jobs[:3]:  # 上位8件から特徴抽出
            if job.get('is_high_salary'):
                high_salary_count += 1
            if job.get('has_daily_payment'):
                daily_payment_count += 1
            
            # 業界キーワード
            occupation = job.get('occupation_category_name', '')
            if occupation and occupation not in keywords:
                keywords.append(occupation)
        
        # プロンプト構築
        prompt_parts = [
            f"ユーザー情報: {location}在住、{age_group}",
            f"求人の特徴: {', '.join(keywords[:2])}が中心",
        ]
        
        if high_salary_count >= 3:
            prompt_parts.append("高時給案件多数")
        if daily_payment_count >= 3:
            prompt_parts.append("日払い可能求人多数")
        
        prompt_parts.extend([
            "今日の日付を含めて、魅力的で開封したくなるメール件名を作成してください。",
            "季節感や緊急性を演出し、40求人の価値を伝えてください。"
        ])
        
        return " ".join(prompt_parts)
    
    def _generate_fallback_subject(self, user_profile: Dict, selected_jobs: Dict) -> str:
        """フォールバック件名生成（ルールベース）"""
        
        from datetime import datetime
        import random
        
        # 基本テンプレート
        templates = [
            "🎯 {location}で見つけた！高時給バイト{count}件",
            "💰 {location}限定！今すぐ稼げるバイト{count}選",
            "⚡ {today}更新！{location}の厳選バイト{count}件",
            "🔥 {location}で大人気！おすすめバイト{count}件",
            "✨ {location}在住必見！今週のバイト{count}件"
        ]
        
        # 変数設定
        location = user_profile.get('prefecture_name', '全国')
        count = "40"
        today = datetime.now().strftime("%m/%d")
        
        # ランダム選択
        template = random.choice(templates)
        subject = template.format(location=location, count=count, today=today)
        
        return subject
    
    def generate_batch_subjects(self, user_profiles: list, selected_jobs_list: list) -> list:
        """バッチでの件名生成"""
        subjects = []
        
        for user_profile, selected_jobs in zip(user_profiles, selected_jobs_list):
            try:
                subject = self.generate_subject(user_profile, selected_jobs)
                subjects.append(subject)
            except Exception as e:
                self.logger.error(f"Failed to generate subject for user {user_profile.get('user_id')}: {str(e)}")
                # フォールバック
                subjects.append(self._generate_fallback_subject(user_profile, selected_jobs))
        
        return subjects

# 使用例
def generate_email_content(user_id, selected_jobs):
    """メール内容の生成"""
    
    user_profile = get_user_profile(user_id)
    
    # 件名生成
    generator = EmailSubjectGenerator()
    subject = generator.generate_subject(user_profile, selected_jobs)
    
    # HTML内容生成
    html_content = build_html_email_content(user_profile, selected_jobs)
    
    return {
        'user_id': user_id,
        'subject': subject,
        'html_content': html_content,
        'sections': {
            'editorial_picks': len(selected_jobs.get('editorial_picks', [])),
            'top5': len(selected_jobs.get('top5', [])),
            'regional': len(selected_jobs.get('regional', [])),
            'nearby': len(selected_jobs.get('nearby', [])),
            'high_income': len(selected_jobs.get('high_income', [])),
            'new': len(selected_jobs.get('new', []))
        }
    }
```

---

## 8. バッチ処理パイプライン

### 8.1 日次処理スケジュール

```yaml
daily_batch_schedule:
  03:00-03:30: "Phase 1: データインポート"
    - CSVデータ取得
    - データクレンジング
    - Supabaseへの一括投入
    
  03:30-04:30: "Phase 2: スコアリング"
    - 基礎スコア計算（時給、fee、人気度）
    - SEOスコア計算（キーワードマッチング）
    - パーソナライズベーススコア計算
    - job_enrichmentテーブル更新
    
  04:30-05:30: "Phase 3: マッチング"
    - ユーザープロファイル更新
    - 10万×1万のマッチング計算（並列5ワーカー）
    - user_job_mapping作成（40万レコード）
    - 各ユーザー40件選定（6セクション）
    
  05:30-06:00: "Phase 4: メール生成"
    - 6セクションHTMLコンテンツ生成
    - パーソナライズ件名生成（GPT-5 nano）
    - daily_email_queueへの格納
    - 配信準備完了通知
```

### 8.2 並列処理実装

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import logging
from typing import List, Dict, Any
import time

class ParallelBatchProcessor:
    """並列バッチ処理マネージャー"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(5, mp.cpu_count())
        self.logger = logging.getLogger(__name__)
    
    def run_daily_batch(self) -> Dict[str, Any]:
        """日次バッチ処理の実行"""
        
        start_time = time.time()
        self.logger.info(f"Starting daily batch with {self.max_workers} workers")
        
        try:
            # Phase 1: データインポート（単一プロセス）
            import_stats = self._run_data_import()
            
            # Phase 2: スコアリング（並列処理）
            scoring_stats = self._run_parallel_scoring()
            
            # Phase 3: マッチング（並列処理）
            matching_stats = self._run_parallel_matching()
            
            # Phase 4: メール生成（並列処理）
            email_stats = self._run_parallel_email_generation()
            
            elapsed_time = time.time() - start_time
            
            result = {
                'success': True,
                'elapsed_time': elapsed_time,
                'phases': {
                    'import': import_stats,
                    'scoring': scoring_stats,
                    'matching': matching_stats,
                    'email_generation': email_stats
                }
            }
            
            self.logger.info(f"Batch completed successfully in {elapsed_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise
    
    def _run_data_import(self) -> Dict[str, int]:
        """データインポートフェーズ"""
        
        self.logger.info("Phase 1: Starting data import")
        
        # サンプルデータの場合のパス
        csv_path = '/Users/naoki/000_PROJECT/job-score-for-mail-system-20250914/data/sample_job_data.csv'
        
        from .import_jobs import import_jobs_csv
        stats = import_jobs_csv(csv_path, batch_size=1000)
        
        self.logger.info(f"Data import completed: {stats}")
        return stats
    
    def _run_parallel_scoring(self) -> Dict[str, Any]:
        """スコアリングフェーズ（並列処理）"""
        
        self.logger.info("Phase 2: Starting parallel scoring")
        
        # 求人データを取得
        jobs_df = self._get_jobs_for_processing()
        
        # ユーザー数で分割
        job_chunks = self._split_dataframe(jobs_df, self.max_workers)
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._process_scoring_batch, chunk, i)
                for i, chunk in enumerate(job_chunks)
            ]
            
            # 結果収集
            results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=600)  # 10分タイムアウト
                    results.append(result)
                    self.logger.info(f"Scoring chunk {i} completed: {result}")
                except Exception as e:
                    self.logger.error(f"Scoring chunk {i} failed: {str(e)}")
                    raise
        
        # 統計情報集計
        total_scored = sum(r['scored'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        
        return {
            'total_scored': total_scored,
            'total_errors': total_errors,
            'chunks': len(results)
        }
    
    def _run_parallel_matching(self) -> Dict[str, Any]:
        """マッチングフェーズ（並列処理）"""
        
        self.logger.info("Phase 3: Starting parallel matching")
        
        # ユーザーリストを取得
        users = self._get_active_users()
        
        # ユーザーを分割
        user_chunks = self._split_list(users, self.max_workers)
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._process_matching_batch, chunk, i)
                for i, chunk in enumerate(user_chunks)
            ]
            
            # 結果収集
            results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=900)  # 15分タイムアウト
                    results.append(result)
                    self.logger.info(f"Matching chunk {i} completed: {result}")
                except Exception as e:
                    self.logger.error(f"Matching chunk {i} failed: {str(e)}")
                    raise
        
        # 統計情報集計
        total_users = sum(r['users_processed'] for r in results)
        total_matches = sum(r['matches_created'] for r in results)
        
        return {
            'total_users': total_users,
            'total_matches': total_matches,
            'chunks': len(results)
        }
    
    def _run_parallel_email_generation(self) -> Dict[str, Any]:
        """メール生成フェーズ（並列処理）"""
        
        self.logger.info("Phase 4: Starting parallel email generation")
        
        # ユーザーの選定済み求人を取得
        user_job_mappings = self._get_daily_job_picks()
        
        # ユーザーごとに分割
        user_chunks = self._split_list(user_job_mappings, self.max_workers)
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._process_email_generation_batch, chunk, i)
                for i, chunk in enumerate(user_chunks)
            ]
            
            # 結果収集
            results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5分タイムアウト
                    results.append(result)
                    self.logger.info(f"Email generation chunk {i} completed: {result}")
                except Exception as e:
                    self.logger.error(f"Email generation chunk {i} failed: {str(e)}")
                    raise
        
        # 統計情報集計
        total_emails = sum(r['emails_generated'] for r in results)
        
        return {
            'total_emails': total_emails,
            'chunks': len(results)
        }
    
    def _process_scoring_batch(self, jobs_chunk: List[Dict], chunk_id: int) -> Dict[str, int]:
        """スコアリングバッチ処理"""
        
        from .scoring import ScoringEngine
        
        engine = ScoringEngine()
        scored = 0
        errors = 0
        
        for job in jobs_chunk:
            try:
                scores = engine.calculate_all_scores(job)
                engine.save_job_enrichment(job['job_id'], scores)
                scored += 1
            except Exception as e:
                logging.error(f"Scoring failed for job {job.get('job_id')}: {str(e)}")
                errors += 1
        
        return {'scored': scored, 'errors': errors, 'chunk_id': chunk_id}
    
    def _process_matching_batch(self, users_chunk: List[Dict], chunk_id: int) -> Dict[str, int]:
        """マッチングバッチ処理"""
        
        from .matching import MatchingEngine
        
        engine = MatchingEngine()
        users_processed = 0
        matches_created = 0
        
        for user in users_chunk:
            try:
                # ユーザーの40件選定
                selected_jobs = engine.select_40_jobs_for_user(user['user_id'])
                
                # 結果を保存
                engine.save_daily_job_picks(user['user_id'], selected_jobs)
                
                users_processed += 1
                matches_created += sum(len(jobs) for jobs in selected_jobs.values())
                
            except Exception as e:
                logging.error(f"Matching failed for user {user.get('user_id')}: {str(e)}")
        
        return {
            'users_processed': users_processed, 
            'matches_created': matches_created,
            'chunk_id': chunk_id
        }
    
    def _process_email_generation_batch(self, user_mappings_chunk: List[Dict], chunk_id: int) -> Dict[str, int]:
        """メール生成バッチ処理"""
        
        from .email_generation import EmailGenerator
        
        generator = EmailGenerator()
        emails_generated = 0
        
        for mapping in user_mappings_chunk:
            try:
                # メール内容生成
                email_content = generator.generate_email_content(
                    mapping['user_id'], 
                    mapping['selected_jobs']
                )
                
                # 配信キューに保存
                generator.save_to_email_queue(email_content)
                
                emails_generated += 1
                
            except Exception as e:
                logging.error(f"Email generation failed for user {mapping.get('user_id')}: {str(e)}")
        
        return {'emails_generated': emails_generated, 'chunk_id': chunk_id}
    
    def _split_dataframe(self, df, num_chunks):
        """DataFrameの分割"""
        import numpy as np
        return np.array_split(df, num_chunks)
    
    def _split_list(self, lst, num_chunks):
        """リストの分割"""
        chunk_size = len(lst) // num_chunks
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    def _get_jobs_for_processing(self):
        """処理対象求人の取得"""
        from src.db import get_supabase_client
        
        client = get_supabase_client()
        
        response = client.table('jobs').select(
            'job_id, endcl_cd, application_name, company_name, '
            'min_salary, max_salary, fee, pref_cd, city_cd, '
            'occupation_cd1, employment_type_cd, feature_codes, '
            'posting_date'
        ).eq('is_active', True).execute()
        
        return response.data
    
    def _get_active_users(self):
        """アクティブユーザーの取得"""
        from src.db import get_supabase_client
        
        client = get_supabase_client()
        
        response = client.table('users').select(
            'user_id, pref_cd, city_cd'
        ).eq('is_active', True).eq('email_subscription', True).execute()
        
        return response.data
    
    def _get_daily_job_picks(self):
        """日次選定求人の取得"""
        from src.db import get_supabase_client
        from datetime import date
        
        client = get_supabase_client()
        
        today = date.today()
        
        response = client.table('daily_job_picks').select(
            'user_id, job_id, section, section_rank'
        ).eq('pick_date', today).execute()
        
        # ユーザーごとにグループ化
        user_mappings = {}
        for pick in response.data:
            user_id = pick['user_id']
            if user_id not in user_mappings:
                user_mappings[user_id] = {
                    'user_id': user_id,
                    'selected_jobs': {}
                }
            
            section = pick['section']
            if section not in user_mappings[user_id]['selected_jobs']:
                user_mappings[user_id]['selected_jobs'][section] = []
            
            user_mappings[user_id]['selected_jobs'][section].append(pick)
        
        return list(user_mappings.values())

# 使用例
def run_daily_batch():
    """日次バッチ処理の実行"""
    
    processor = ParallelBatchProcessor(max_workers=5)
    
    try:
        result = processor.run_daily_batch()
        
        print(f"✅ Batch completed successfully")
        print(f"⏱️  Total time: {result['elapsed_time']:.2f} seconds")
        print(f"📊 Import: {result['phases']['import']}")
        print(f"🎯 Scoring: {result['phases']['scoring']}")
        print(f"🔄 Matching: {result['phases']['matching']}")
        print(f"📧 Email generation: {result['phases']['email_generation']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Batch failed: {str(e)}")
        raise

if __name__ == '__main__':
    run_daily_batch()
```

### 8.3 エラーハンドリング

```python
ERROR_HANDLING_CONFIG = {
    'csv_parse_error': {
        'action': 'skip_row',
        'log': True,
        'alert': False,
        'retry': False
    },
    'db_connection_error': {
        'action': 'retry',
        'max_retries': 3,
        'backoff': 'exponential',  # 1秒→2秒→4秒
        'log': True,
        'alert': True
    },
    'matching_failure': {
        'action': 'fallback',
        'fallback_strategy': 'use_previous_day',
        'log': True,
        'alert': True
    },
    'memory_overflow': {
        'action': 'graceful_degradation',
        'strategy': 'process_in_chunks',
        'chunk_size': 1000,
        'log': True,
        'alert': True
    },
    'gpt_api_error': {
        'action': 'fallback',
        'fallback_strategy': 'rule_based_generation',
        'log': True,
        'alert': False
    }
}

class BatchErrorHandler:
    """バッチ処理エラーハンドラー"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_sender = AlertSender()
    
    def handle_error(self, error_type: str, context: Dict[str, Any], exception: Exception) -> bool:
        """
        エラーハンドリング
        
        Returns:
            bool: 処理を続行するかどうか
        """
        config = ERROR_HANDLING_CONFIG.get(error_type, {})
        action = config.get('action', 'fail')
        
        # ログ記録
        if config.get('log', True):
            self.logger.error(
                f"Error occurred: {error_type}",
                extra={
                    'context': context,
                    'exception': str(exception),
                    'action': action
                }
            )
        
        # アラート送信
        if config.get('alert', False):
            self.alert_sender.send_error_alert(error_type, context, exception)
        
        # アクション実行
        if action == 'skip_row':
            return True  # 処理続行
        
        elif action == 'retry':
            return self._handle_retry(config, context, exception)
        
        elif action == 'fallback':
            return self._handle_fallback(config, context, exception)
        
        elif action == 'graceful_degradation':
            return self._handle_degradation(config, context, exception)
        
        else:  # fail
            return False
    
    def _handle_retry(self, config: Dict, context: Dict, exception: Exception) -> bool:
        """リトライ処理"""
        max_retries = config.get('max_retries', 3)
        current_attempt = context.get('attempt', 0)
        
        if current_attempt >= max_retries:
            self.logger.error(f"Max retries ({max_retries}) exceeded")
            return False
        
        # バックオフ
        backoff_type = config.get('backoff', 'linear')
        if backoff_type == 'exponential':
            delay = 2 ** current_attempt
        else:
            delay = current_attempt + 1
        
        self.logger.info(f"Retrying in {delay} seconds (attempt {current_attempt + 1})")
        time.sleep(delay)
        
        return True
    
    def _handle_fallback(self, config: Dict, context: Dict, exception: Exception) -> bool:
        """フォールバック処理"""
        strategy = config.get('fallback_strategy')
        
        if strategy == 'use_previous_day':
            return self._use_previous_day_data(context)
        elif strategy == 'rule_based_generation':
            return self._use_rule_based_generation(context)
        else:
            return False
    
    def _handle_degradation(self, config: Dict, context: Dict, exception: Exception) -> bool:
        """段階的処理縮小"""
        strategy = config.get('strategy')
        
        if strategy == 'process_in_chunks':
            new_chunk_size = config.get('chunk_size', 1000)
            context['chunk_size'] = min(context.get('chunk_size', 5000), new_chunk_size)
            self.logger.info(f"Reducing chunk size to {new_chunk_size}")
            return True
        
        return False
    
    def _use_previous_day_data(self, context: Dict) -> bool:
        """前日データの使用"""
        # 実装省略
        return True
    
    def _use_rule_based_generation(self, context: Dict) -> bool:
        """ルールベース生成へのフォールバック"""
        # 実装省略
        return True

class AlertSender:
    """アラート送信"""
    
    def send_error_alert(self, error_type: str, context: Dict, exception: Exception):
        """エラーアラートの送信"""
        # Slack、メール等への通知実装
        pass
```

---

## 9. モニタリングシステム

### 9.1 SQLモニタリングインターフェース

#### 基本機能
- リアルタイムSQLクエリ実行（SELECT専用）
- データ可視化ダッシュボード
- エラーログビューア
- バッチ処理状況モニター

#### 実装例（Next.js）

```typescript
// app/monitoring/query/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Play, Download } from 'lucide-react'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

interface QueryResult {
  data: any[] | null
  error: string | null
  execution_time: number
  rows_affected: number
}

export default function QueryPage() {
  const [query, setQuery] = useState('SELECT COUNT(*) FROM jobs WHERE is_active = true;')
  const [results, setResults] = useState<QueryResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState<string[]>([])

  // クエリ実行
  const executeQuery = async () => {
    if (!query.trim()) return

    // セキュリティチェック
    if (!query.toLowerCase().trim().startsWith('select')) {
      setResults({
        data: null,
        error: 'SELECT文のみ実行可能です',
        execution_time: 0,
        rows_affected: 0
      })
      return
    }

    setIsLoading(true)
    const startTime = performance.now()

    try {
      const { data, error } = await supabase
        .rpc('execute_readonly_query', { query_text: query })

      const executionTime = performance.now() - startTime

      setResults({
        data: data || [],
        error: error?.message || null,
        execution_time: executionTime,
        rows_affected: data?.length || 0
      })

      // 履歴に追加
      if (!error) {
        setHistory(prev => [query, ...prev.slice(0, 9)]) // 最新10件
      }

    } catch (err) {
      setResults({
        data: null,
        error: `実行エラー: ${err instanceof Error ? err.message : 'Unknown error'}`,
        execution_time: performance.now() - startTime,
        rows_affected: 0
      })
    } finally {
      setIsLoading(false)
    }
  }

  // よく使うクエリ
  const commonQueries = [
    {
      name: 'アクティブ求人数',
      query: 'SELECT COUNT(*) as active_jobs FROM jobs WHERE is_active = true;'
    },
    {
      name: '今日のマッチング状況',
      query: `SELECT 
        COUNT(DISTINCT user_id) as users_matched,
        COUNT(*) as total_matches
      FROM daily_job_picks 
      WHERE pick_date = CURRENT_DATE;`
    },
    {
      name: 'スコア分布',
      query: `SELECT 
        CASE 
          WHEN basic_score >= 80 THEN '80-100'
          WHEN basic_score >= 60 THEN '60-80'
          WHEN basic_score >= 40 THEN '40-60'
          ELSE '0-40'
        END as score_range,
        COUNT(*) as count
      FROM job_enrichment
      GROUP BY score_range
      ORDER BY score_range;`
    },
    {
      name: 'セクション別件数',
      query: `SELECT 
        section,
        COUNT(*) as job_count
      FROM daily_job_picks 
      WHERE pick_date = CURRENT_DATE
      GROUP BY section;`
    }
  ]

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            SQLクエリ実行
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">SQLクエリ</label>
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="SELECT文を入力してください..."
              className="font-mono text-sm h-32"
            />
          </div>
          
          <div className="flex gap-2">
            <Button onClick={executeQuery} disabled={isLoading}>
              {isLoading ? '実行中...' : '実行'}
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setQuery('')}
            >
              クリア
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* よく使うクエリ */}
      <Card>
        <CardHeader>
          <CardTitle>よく使うクエリ</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {commonQueries.map((item, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => setQuery(item.query)}
                className="text-left h-auto p-2"
              >
                {item.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 実行結果 */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              実行結果
              <div className="text-sm text-muted-foreground">
                実行時間: {results.execution_time.toFixed(2)}ms | 
                行数: {results.rows_affected}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {results.error ? (
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                {results.error}
              </div>
            ) : results.data && results.data.length > 0 ? (
              <div className="space-y-4">
                <div className="overflow-auto max-h-96">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(results.data[0]).map((column) => (
                          <TableHead key={column}>{column}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.data.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, cellIndex) => (
                            <TableCell key={cellIndex} className="font-mono text-sm">
                              {String(value)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                
                {results.data.length > 10 && (
                  <div className="text-sm text-muted-foreground">
                    最初の{Math.min(results.data.length, 100)}行を表示
                  </div>
                )}
              </div>
            ) : (
              <div className="text-muted-foreground">データがありません</div>
            )}
          </CardContent>
        </Card>
      )}

      {/* クエリ履歴 */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>実行履歴</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((historyQuery, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  className="w-full text-left h-auto p-2 font-mono text-sm"
                  onClick={() => setQuery(historyQuery)}
                >
                  {historyQuery}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

### 9.2 監視メトリクス

#### リアルタイム監視項目
- 処理ステータス（実行中/完了/エラー）
- メモリ使用量（4GB閾値）
- エラー率（1%閾値）
- データベース接続数（100接続上限）

#### 日次メトリクス
- 処理求人数: 10万件
- マッチングユーザー数: 1万人
- 生成メール数: 1万通
- 平均スコア分布
- セクション充足率

#### 品質メトリクス
- クリック率（CTR）
- 応募率（CVR）
- ユーザー満足度スコア
- 配信停止率

### 9.3 アラート設定

```yaml
alert_conditions:
  critical:
    - condition: "processing_time > 30 minutes"
      action: ["email", "slack", "pager"]
    - condition: "memory_usage > 4GB"
      action: ["email", "slack"]
    - condition: "error_rate > 1%"
      action: ["email", "slack"]
      
  warning:
    - condition: "processing_time > 20 minutes"
      action: ["email"]
    - condition: "memory_usage > 3GB"
      action: ["log"]
    - condition: "matched_users < 9000"
      action: ["email"]
```

---

## 10. 実装計画

### 10.1 フェーズ別実装スケジュール

| フェーズ | 期間 | 主要タスク | 成果物 |
|---------|------|-----------|--------|
| Phase 0 | 1日 | 要件確定、技術調査 | research.md ✅ |
| Phase 1 | 2日 | DB構築、データ投入 | 20テーブル作成 |
| Phase 2 | 3日 | バッチ処理実装 | スコアリング、マッチング |
| Phase 3 | 2日 | Frontend実装 | モニタリング画面 |
| Phase 4 | 1日 | 統合テスト | E2Eテスト完了 |
| Phase 5 | 1日 | 最適化、文書化 | 本番準備完了 |

### 10.2 タスク並列化戦略

```mermaid
gantt
    title 実装タイムライン（並列実行）
    dateFormat  YYYY-MM-DD
    section Phase1
    DB構築           :a1, 2025-09-17, 1d
    データ投入       :a2, after a1, 1d
    Frontend環境     :a3, 2025-09-17, 1d
    
    section Phase2
    スコアリング     :b1, after a2, 1.5d
    マッチング       :b2, after b1, 1.5d
    UI基本実装       :b3, after a3, 2d
    
    section Phase3
    メール生成       :c1, after b2, 1d
    UI高度機能       :c2, after b3, 1d
    
    section Phase4
    統合テスト       :d1, after c1 c2, 1d
```

### 10.3 継続的検証戦略（tasks.mdから統合）

#### 検証チェックポイント
- **T010完了時点**: データベース構造を確認可能
- **T010-B完了時点**: SQLクエリ実行画面で検証開始可能
- **T036-CHECK**: CSVインポート結果を即座に確認
- **T037-CHECK**: スコア計算結果を即座に確認
- **T038-CHECK**: カテゴリ分類結果を即座に確認
- **T039-CHECK**: マッチング結果を即座に確認
- **T040-CHECK**: メール生成結果を即座に確認

#### 検証用SQLクエリ

```sql
-- T036-CHECK: CSVインポート動作確認
SELECT COUNT(*) FROM jobs WHERE created_at >= CURRENT_DATE;
-- Expected: sample_job_data.csvの件数と一致

SELECT job_id, application_name, company_name FROM jobs LIMIT 5;
-- データが正しくインポートされていることを確認

-- T037-CHECK: スコア計算確認
SELECT job_id, basic_score, seo_score, personalized_score 
FROM job_enrichment LIMIT 10;
-- 3種類のスコアが計算されていることを確認

SELECT AVG(basic_score), MIN(basic_score), MAX(basic_score) 
FROM job_enrichment;
-- スコアの分布が妥当か確認

-- T038-CHECK: カテゴリ分類確認
SELECT need_category_id, COUNT(*) as job_count 
FROM job_need_categories 
GROUP BY need_category_id;
-- 14カテゴリに分類されていることを確認

-- T039-CHECK: マッチング結果確認
SELECT user_id, COUNT(*) as match_count 
FROM user_job_mapping 
WHERE created_at >= CURRENT_DATE 
GROUP BY user_id LIMIT 10;
-- 各ユーザーに約40件マッチしていることを確認

SELECT section_type, COUNT(*) as job_count 
FROM daily_job_picks 
WHERE user_id = 1 
GROUP BY section_type;
-- editorial_picks:5件, TOP5:5件, regional:10件, nearby:8件, high_income:7件, new:5件

-- T040-CHECK: メール生成確認
SELECT user_id, LENGTH(email_content) as content_size 
FROM daily_email_queue 
WHERE created_at >= CURRENT_DATE 
LIMIT 10;
-- HTMLコンテンツが生成されていることを確認

SELECT COUNT(*) FROM daily_email_queue 
WHERE created_at >= CURRENT_DATE;
-- 全ユーザー分生成されていることを確認
```

### 10.4 技術的意思決定記録

| 決定事項 | 選択 | 根拠 | 代替案 |
|---------|------|------|--------|
| バッチ処理言語 | Python | pandasの効率性 | Node.js |
| Frontend FW | Next.js 14 | App Router、RSC | Remix |
| DB | Supabase | リアルタイム、認証 | Firebase |
| スコアリング | 実数計算 | シンプル、高速 | 機械学習 |
| 並列処理 | 5ワーカー | CPU/メモリバランス | 10ワーカー |
| AI統合 | GPT-5 nano | 日本語最適化 | GPT-4 |

---

## 11. 品質保証

### 11.1 テスト戦略

#### テストピラミッド
```
        /E2E\         5%（5テスト）
       /統合 \       25%（25テスト）
      /      \
     /契約    \     30%（30テスト）
    /_________ \
   /   単体     \   40%（40テスト）
```

#### TDD実装フロー
1. RED: テスト作成（失敗確認）
2. GREEN: 最小実装（テスト通過）
3. REFACTOR: リファクタリング

### 11.2 パフォーマンステスト

```python
# 負荷テストシナリオ
def test_full_batch_performance():
    """
    10万求人×1万ユーザーの負荷テスト
    """
    # 準備
    load_test_data(jobs=100000, users=10000)
    
    # 実行時間測定
    start_time = time.time()
    result = run_daily_batch()
    elapsed_time = time.time() - start_time
    
    # アサーション
    assert elapsed_time < 1800  # 30分以内
    assert get_memory_usage() < 4 * 1024 * 1024 * 1024  # 4GB以内
    assert len(result['emails']) == 10000  # 全ユーザー分生成
    assert all(len(e['jobs']) == 40 for e in result['emails'])  # 40件選定

def test_scoring_performance():
    """スコアリング性能テスト"""
    jobs = load_test_jobs(10000)
    
    start_time = time.time()
    scores = calculate_scores_batch(jobs)
    elapsed_time = time.time() - start_time
    
    # 1万件を5分以内
    assert elapsed_time < 300
    assert len(scores) == len(jobs)
    assert all(0 <= score['total_score'] <= 100 for score in scores)

def test_matching_performance():
    """マッチング性能テスト"""
    users = load_test_users(1000)  # 1000ユーザーでテスト
    jobs = load_test_jobs(10000)
    
    start_time = time.time()
    matches = run_matching_batch(users, jobs)
    elapsed_time = time.time() - start_time
    
    # 1000ユーザーを1分以内
    assert elapsed_time < 60
    assert len(matches) == len(users)
    assert all(len(match['selected_jobs']) == 40 for match in matches)
```

### 11.3 エッジケース対応

| ケース | 発生条件 | 対応方法 | テスト |
|--------|---------|---------|--------|
| 新規ユーザー | 応募履歴0 | デフォルトプロファイル使用 | ✅ |
| 求人不足 | <40件該当 | エリア拡大、条件緩和 | ✅ |
| CSV不正 | フォーマットエラー | 該当行スキップ、ログ | ✅ |
| 重複求人 | 同一job_id | upsert処理 | ✅ |
| メモリ不足 | >4GB使用 | チャンク処理切替 | ✅ |
| GPT API障害 | AI服務停止 | ルールベース生成へフォールバック | ✅ |

### 11.4 品質メトリクス

```python
# 品質メトリクス計算
def calculate_quality_metrics(batch_result):
    """品質メトリクスの計算"""
    
    metrics = {}
    
    # データ品質
    metrics['data_quality'] = {
        'import_success_rate': batch_result['import']['imported'] / batch_result['import']['total'],
        'scoring_coverage': batch_result['scoring']['scored'] / batch_result['import']['imported'],
        'matching_completion_rate': batch_result['matching']['users'] / 10000
    }
    
    # パフォーマンス品質
    metrics['performance'] = {
        'total_processing_time': batch_result['elapsed_time'],
        'memory_efficiency': get_peak_memory_usage() / (4 * 1024 * 1024 * 1024),  # 4GB比
        'throughput': batch_result['matching']['matches'] / batch_result['elapsed_time']
    }
    
    # コンテンツ品質
    metrics['content_quality'] = {
        'email_generation_success_rate': batch_result['email_generation']['emails'] / 10000,
        'avg_personalized_score': calculate_avg_personalized_score(),
        'section_coverage': calculate_section_coverage()
    }
    
    return metrics

def validate_6_section_structure(selected_jobs):
    """6セクション構造の検証"""
    expected_sections = {
        'editorial_picks': 5,
        'top5': 5,
        'regional': 10,
        'nearby': 8,
        'high_income': 7,
        'new': 5
    }
    
    # セクション存在確認
    for section, expected_count in expected_sections.items():
        assert section in selected_jobs
        actual_count = len(selected_jobs[section])
        assert actual_count <= expected_count, f"{section}: expected <={expected_count}, got {actual_count}"
    
    # 重複チェック
    all_job_ids = []
    for section_jobs in selected_jobs.values():
        all_job_ids.extend([job['job_id'] for job in section_jobs])
    
    assert len(all_job_ids) == len(set(all_job_ids)), "Duplicate jobs found across sections"
    
    # 総件数チェック
    total_jobs = sum(len(jobs) for jobs in selected_jobs.values())
    assert total_jobs == 40, f"Expected 40 total jobs, got {total_jobs}"
```

---

## 12. 運用要件

### 12.1 インフラ要件

| 項目 | 要件 | 推奨 |
|------|------|------|
| CPU | 4コア以上 | 8コア |
| メモリ | 8GB以上 | 16GB |
| ストレージ | 100GB以上 | 200GB SSD |
| ネットワーク | 100Mbps以上 | 1Gbps |
| OS | Ubuntu 22.04 | - |
| データベース | PostgreSQL 15 | - |

### 12.2 バックアップ戦略

```yaml
backup_policy:
  database:
    frequency: daily
    retention: 30 days
    method: pg_dump
    storage: S3
    
  application:
    frequency: weekly
    retention: 90 days
    method: full snapshot
    
  logs:
    frequency: continuous
    retention: 90 days
    method: log shipping
    storage: CloudWatch
```

### 12.3 災害復旧計画

| メトリクス | 目標値 | 実現方法 |
|-----------|--------|---------
| RTO | 4時間 | ホットスタンバイ |
| RPO | 1時間 | 増分バックアップ |
| 可用性 | 99.5% | 冗長構成 |

### 12.4 データ保持ポリシー

| データ種別 | 保持期間 | アーカイブ先 | 削除方法 |
|-----------|---------|-------------|----------|
| user_actions | 365日 | S3 Glacier | 自動削除 |
| daily_job_picks | 30日 | なし | 物理削除 |
| daily_email_queue | 7日 | なし | 物理削除 |
| ログファイル | 90日 | S3 Standard | 自動移行 |
| バックアップ | 30日 | S3 Standard-IA | 手動削除 |

---

## 13. クイックスタートガイド

### 13.1 前提条件

- Python 3.11+ がインストール済み
- Node.js 20+ がインストール済み
- Supabaseアカウント作成済み
- Git がインストール済み

### 13.2 30分セットアップ手順

#### Step 1: リポジトリのクローン (2分)

```bash
git clone https://github.com/your-org/job-matching-system.git
cd job-matching-system
```

#### Step 2: Supabaseプロジェクトの作成 (5分)

```bash
# Supabase CLIのインストール
npm install -g supabase

# プロジェクト初期化
supabase init
supabase start

# 環境変数の設定
cat > .env.local << EOF
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
EOF
```

#### Step 3: データベースセットアップ (8分)

```bash
# マイグレーション実行
supabase db push

# マスターデータ投入
python scripts/import_master_data.py

# サンプル求人データ投入
python scripts/import_sample_jobs.py \
  --file data/sample_job_data.csv \
  --batch-size 1000
```

#### Step 4: Pythonバックエンドセットアップ (8分)

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 初回スコアリング実行
python src/batch/scoring.py --initial-run
```

#### Step 5: Next.js フロントエンドセットアップ (5分)

```bash
cd frontend
npm install
npm run dev
```

#### Step 6: 動作確認 (2分)

```bash
# アクセス確認
curl http://localhost:3000/api/monitoring/health

# SQLモニタリング画面
# ブラウザで http://localhost:3000/monitoring を開く

# テストクエリ実行
SELECT COUNT(*) FROM jobs WHERE is_active = true;
```

### 13.3 動作確認テスト

#### データベース接続確認

```python
# Python shell で実行
from src.db import get_supabase_client

client = get_supabase_client()
response = client.table('jobs').select('count').execute()
print(f"求人データ: {response.data[0]['count']}件")
```

#### API動作確認

```bash
# ヘルスチェック
curl http://localhost:3000/api/monitoring/health

# 統計情報取得
curl http://localhost:3000/api/monitoring/stats

# テストユーザーのマッチング結果確認
curl http://localhost:3000/api/matching/results/1
```

---

## 14. 付録

### 14.1 用語集

| 用語 | 説明 |
|------|------|
| endcl_cd | エンドクライアントコード（企業の一意識別子） |
| fee | 応募促進費用（企業が支払う応募単価） |
| occupation_cd1 | 職種大分類コード |
| pref_cd | 都道府県コード |
| city_cd | 市区町村コード |
| editorial_picks | 編集部おすすめセクション（v3.0で追加） |
| GPT-5 nano | OpenAIの軽量AI モデル（メール件名生成用） |

### 14.2 参照ドキュメント

- **ER図**: [`20250904_er_complete_v2.0.mmd`](./20250904_er_complete_v2.0.mmd)
- **サンプルデータ**: [`sample_job_data.csv`](../../data/sample_job_data.csv)
- **職種マスター**: [`occupation_view.csv`](../../data/occupation_view.csv)
- **雇用形態マスター**: [`employment_type_view.csv`](../../data/employment_type_view.csv)

### 14.3 APIエンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| /jobs/import | POST | CSV一括インポート |
| /jobs/scoring | POST | スコア計算実行 |
| /jobs/categorize | POST | カテゴリ分類実行 |
| /matching/execute | POST | マッチング処理実行 |
| /matching/results/:userId | GET | マッチング結果取得 |
| /email/generate | POST | メール生成（単体） |
| /email/batch-generate | POST | メール一括生成 |
| /monitoring/query | POST | SQLクエリ実行 |
| /monitoring/stats | GET | 統計情報取得 |
| /monitoring/health | GET | ヘルスチェック |

### 14.4 環境変数設定

```bash
# .env.local
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# バッチ処理設定
BATCH_SIZE=1000
PARALLEL_WORKERS=5
MAX_MEMORY_GB=4
BATCH_SCHEDULE="0 3 * * *"  # 毎日03:00

# モニタリング設定
MONITORING_PORT=3001
ALERT_EMAIL=admin@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# AI設定（メール件名生成）
OPENAI_API_KEY=sk-...
GPT5_NANO_MAX_TOKENS=50
GPT5_NANO_TEMPERATURE=0.7
```

### 14.5 トラブルシューティング

| 問題 | 原因 | 解決方法 |
|------|------|---------
| バッチ処理が30分超過 | データ量増加 | ワーカー数増加、インデックス最適化 |
| メモリ不足エラー | チャンクサイズ大 | BATCH_SIZE を500に削減 |
| スコア計算が0 | fee≤500 | fee閾値の調整検討 |
| マッチング結果<40件 | 条件厳しすぎ | エリア拡大、条件緩和 |
| SQLタイムアウト | インデックス不足 | EXPLAIN分析、インデックス追加 |
| GPT API エラー | レート制限 | リトライ処理、フォールバック実行 |

### 14.6 今後の拡張計画

#### Phase 1（3ヶ月以内）
- メール配信システム連携（SendGrid/SES）
- A/Bテスト機能
- レコメンドアルゴリズムのML化

#### Phase 2（6ヶ月以内）
- リアルタイムマッチング
- プッシュ通知対応
- モバイルアプリ開発

#### Phase 3（12ヶ月以内）
- 多言語対応
- 企業向け管理画面
- AIチャットボット統合

### 14.7 パフォーマンス最適化ガイド

#### メモリ最適化

```python
# Pandas最適化設定
dtype_config = {
    'job_id': 'uint32',
    'endcl_cd': 'category',
    'pref_cd': 'category',
    'city_cd': 'category',
    'min_salary': 'uint32',
    'max_salary': 'uint32',
    'fee': 'uint16'
}

# PyArrow backend使用
pd.options.mode.string_storage = "pyarrow"
```

#### 処理時間最適化

```python
# 並列処理設定
import multiprocessing as mp
max_workers = min(5, mp.cpu_count())

# チャンク処理最適化
optimal_chunk_size = min(1000, total_records // max_workers)
```

### 14.8 セキュリティガイドライン

#### SQL インジェクション対策

```typescript
// SELECT文のみ許可
if (!query.toLowerCase().trim().startsWith('select')) {
  throw new Error('SELECT文のみ実行可能です');
}

// パラメータ化クエリ使用
const { data } = await supabase
  .rpc('execute_safe_query', { query_text: query });
```

#### 認証・認可

```python
# Supabase RLS（Row Level Security）使用
CREATE POLICY "Users can only access their own data" ON user_profiles
FOR ALL USING (auth.uid() = user_id);
```

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| v1.0 | 2025-09-01 | 初版作成（5セクション構成） | - |
| v2.0 | 2025-09-04 | ER図完成、詳細設計追加 | - |
| v3.0 | 2025-09-16 | 6セクション構成変更、editorial_picks追加 | - |
| v4.0 | 2025-09-16 | 完全統合版、実装詳細追加 | Claude Code |
| v5.0 | 2025-09-16 | **最終統合版**、全ファイル統合、GPT-5 nano統合、継続的検証戦略 | Claude Code |

---

**🎯 最終統合仕様書 v5.0 完成**

*このドキュメントは、バイト求人マッチングシステムの全ての仕様・実装詳細・運用要件を記載した最終統合版です。*  
*v1.0からv4.0の全バージョン、answers.md、asks.md、data-model.md、plan.md、tasks.md、research.md、quickstart.md等の全情報を統合し、実装可能な完全仕様書として作成されています。*

*問題や提案がある場合は GitHub Issues へお願いいたします。*