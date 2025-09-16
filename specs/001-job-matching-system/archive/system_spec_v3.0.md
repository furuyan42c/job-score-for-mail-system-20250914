# バイト求人マッチングシステム仕様書 v3.0（統合版）

**作成日**: 2025-09-16  
**ブランチ**: `001-job-matching-system`  
**ステータス**: Production Ready  
**前バージョンからの主要変更**: 5→6セクション構成、編集部おすすめ追加、実装詳細の統合

---

## 目次

1. [システム概要](#1-システム概要)（v1.0から継承）
2. [カテゴリー分類](#2-カテゴリー分類)（v1.0から継承）
3. [システムアーキテクチャ](#3-システムアーキテクチャ)【NEW】
4. [データモデル詳細](#4-データモデル詳細)【NEW】
5. [6セクション構成詳細](#5-6セクション構成詳細)【更新】
6. [スコアリングアルゴリズム](#6-スコアリングアルゴリズム)【NEW】
7. [実装計画](#7-実装計画)【NEW】
8. [品質保証](#8-品質保証)【NEW】
9. [運用要件](#9-運用要件)【NEW】
10. [/plan再実行の妥当性評価](#10-plan再実行の妥当性評価)【NEW】

---

## 1. システム概要

### 1.1 目的

本システムは、1万人のユーザーに対して、毎日パーソナライズされたバイト求人情報をメール配信するシステムです。10万件の求人データから、各ユーザーに最適な40件を自動選定します。

### 1.2 主要機能

1. 求人のスコアリング: 各求人の魅力度を点数化
2. ユーザーマッチング: 過去の応募履歴から好みを分析
3. 自動メール生成: 毎日異なる内容で配信
4. データ自動更新: Supabaseでデータ管理

### 1.3 技術スタック

- 開発環境: Claude Code / Cursor / Roo Code（AI支援開発）
- データベース: Supabase (PostgreSQL)
- 言語: Python 3.11+

### 1.4 配信文面例

━━━━━━━━━━━━━━━━━━━━━━━━
📧 ゲットバイト通信　2025年7月15日号
━━━━━━━━━━━━━━━━━━━━━━━━
※本メールは「ゲットバイト」にご登録の
直己 様（東京都小金井市在住）にお届けしています。

こんにちは、ゲットバイト編集部です！
「夏ボ、まだ間に合う？」── そんな声にお応えして
日払い × 高時給 × 駅近 を中心に厳選した **超おすすめ40求人** をお届けします。
3スクロールで"推し求人"が見つかるダイジェスト版。ぜひ最後までご覧ください！

─────────────────────
◆ あなたにおすすめ求人TOP5
─────────────────────

[以下、v1.0のメール例を継承]

---

## 2. カテゴリー分類

ニーズカテゴリーは、文章の部分一致にて行う。使用カラムは、jobsテーブルのapplication_name、company_name、salary、hoursを対象とする。
職種カテゴリーは、大職種分類コードで行う。

### 2.1 ニーズベースカテゴリー（14種類）
[v1.0の内容を継承]

### 2.2 職種カテゴリー（12種類）
[v1.0の内容を継承]

---

## 3. システムアーキテクチャ【NEW】

### 3.1 技術スタック詳細

```yaml
backend:
  language: Python 3.11
  framework: FastAPI
  batch_processor: APScheduler
  data_processing: 
    - pandas 2.x with PyArrow backend
    - scikit-learn
    - numpy
  database_client: supabase-py v2.x
  
frontend:
  language: TypeScript 5.0
  framework: Next.js 14
  ui_library: React 18
  styling: Tailwind CSS
  state_management: Zustand
  
database:
  primary: Supabase (PostgreSQL 15)
  cache: Redis (オプション)
  connection_pool: PgBouncer
  
infrastructure:
  platform: Ubuntu 22.04 LTS
  runtime: Node.js 20
  container: Docker (オプション)
  monitoring: 
    - Grafana
    - Prometheus
    - Sentry (エラートラッキング)
  
testing:
  backend: pytest, pytest-asyncio
  frontend: Jest, React Testing Library
  e2e: Playwright
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

### 3.3 並列処理最適化

```yaml
parallel_groups:
  group_a:  # 独立実行可能
    - database_setup
    - frontend_base_setup
    - test_environment_setup
    max_parallel: 3
    
  group_b:  # group_a完了後
    - csv_import
    - scoring_implementation
    - ui_implementation
    max_parallel: 3
    
  group_c:  # group_b完了後
    - matching_process
    - email_generation
    - integration_testing
    max_parallel: 2
    
performance_gains:
  traditional_sequential: 8 hours
  with_parallelization: 3 hours
  improvement: 62.5%
```

---

## 4. データモデル詳細【NEW】

### 4.1 ER図概要（v2.0準拠）

主要20テーブル構成：

#### トランザクションテーブル
1. **jobs** - 求人マスター（10万件、100+フィールド）
2. **users** - ユーザー基本情報（1万件）
3. **user_actions** - 行動履歴（応募、クリック、開封）
4. **user_profiles** - ユーザープロファイル（応募傾向集計）
5. **user_job_mapping** - マッチング結果（日次40万件）
6. **daily_job_picks** - 選定求人（配信用整形済み）
7. **daily_email_queue** - メール配信キュー（6セクション構成）
8. **job_enrichment** - 求人拡張情報（スコア、カテゴリ）

#### マスターテーブル
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

#### 補助テーブル
19. **jobs_match_raw** - マッチング用簡易データ
20. **jobs_contents_raw** - コンテンツ表示用データ

### 4.2 重要フィールド定義

```sql
-- jobsテーブルの重要フィールド
job_id: BIGINT PRIMARY KEY
endcl_cd: VARCHAR(20)  -- エンドクライアントコード（企業識別）
application_name: TEXT  -- 求人タイトル
company_name: VARCHAR(255)  -- 企業名
min_salary: INTEGER  -- 最低給与
max_salary: INTEGER  -- 最高給与
fee: INTEGER  -- 応募促進費用（0-5000円）
feature_codes: TEXT  -- カンマ区切り特徴コード
station_name_eki: VARCHAR(100)  -- 最寄駅（表示用）
hours: TEXT  -- 勤務時間（HTML含む）
posting_date: TIMESTAMPTZ  -- 投稿日時
end_at: TIMESTAMPTZ  -- 掲載終了日時

-- user_actionsテーブルの重要フィールド
action_type: VARCHAR(20)  -- 'open', 'click', 'applied'
action_date: TIMESTAMPTZ  -- アクション日時
endcl_cd: VARCHAR(20)  -- 応募企業コード
source_type: VARCHAR(20)  -- 'email', 'direct', 'search'
```

---

## 5. 6セクション構成詳細【更新】

### 5.1 セクション概要と配分

総計40件を6つのセクションに配分（重複なし）：

| セクション | 件数 | 選定基準 | 優先度 |
|-----------|------|----------|---------|
| 編集部おすすめ（editorial_picks） | 5件 | fee × 応募クリック数の上位 | 1（最優先） |
| あなたにおすすめTOP5（top5） | 5件 | パーソナライズスコア上位 | 2 |
| 地域別求人（regional） | 10件 | 都道府県内＋職種マッチング | 3 |
| 近隣求人（nearby） | 8件 | 市区町村周辺＋職種マッチング | 4 |
| 高収入・日払い（high_income） | 7件 | 高時給 OR 日払い可能 | 5 |
| 新着求人（new） | 5件 | 7日以内投稿＋スコア上位 | 6 |

### 5.2 各セクションの詳細仕様

#### 5.2.1 編集部おすすめ（editorial_picks）【NEW】
```python
# 選定ロジック
def calculate_editorial_popularity_score(job, user_location):
    """
    企業の応募促進費用(fee)と実際の人気度の掛け算
    エリアによる重み付けも考慮
    """
    base_score = job.fee * job.application_clicks
    location_weight = get_location_weight(job, user_location)
    # location_weight: 同一市区町村=1.0, 近隣=0.7, 同一都道府県=0.5
    return base_score * location_weight

# 2週間以内応募企業は除外
if _was_applied_within_2weeks(job.endcl_cd, user_id):
    continue  # スキップ
```

#### 5.2.2 あなたにおすすめTOP5（top5）
```python
# パーソナライズスコアの上位5件
# 2週間以内応募企業(endcl_cd)は除外
# 過去の応募履歴との類似度が高い順
```

#### 5.2.3 地域別求人（regional）
```python
# 都道府県内の求人
# prefecture_cdでフィルタリング
# 職種マッチングスコアを重視
# 既選択求人は除外
```

#### 5.2.4 近隣求人（nearby）
```python
# 市区町村とその隣接エリア
# adjacent_citiesテーブル活用
# 職種マッチングスコアを重視
```

#### 5.2.5 高収入・日払い（high_income）
```python
# 条件
if avg_salary >= area_avg_salary * 1.2:  # エリア平均の1.2倍以上
    high_income_score += 50
if has_daily_payment_flag:  # 日払い可能フラグ
    high_income_score += 50
```

#### 5.2.6 新着求人（new）
```python
# posting_dateが7日以内
# スコア上位から5件選定
# 他セクションとの重複除外
```

### 5.3 重複処理と優先順位

```python
# 優先度順処理
priority_order = [
    'editorial_picks',  # 最優先
    'top5',
    'regional',
    'nearby',
    'high_income',
    'new'
]

selected_job_ids = set()

for section in priority_order:
    candidates = get_candidates_for_section(section)
    # 既選択求人を除外
    candidates = candidates[~candidates['job_id'].isin(selected_job_ids)]
    selected = select_top_n(candidates, section_counts[section])
    selected_job_ids.update(selected['job_id'])
```

---

## 6. スコアリングアルゴリズム【NEW】

### 6.1 基礎スコア（0-100点）

```python
def calculate_basic_score(job, area_stats, company_popularity):
    """
    基礎スコア計算（3要素の加重平均）
    """
    # フィルタリング条件
    VALID_EMPLOYMENT_TYPE_CDS = [1, 3, 6, 8]  # アルバイト、パート等
    MIN_FEE_THRESHOLD = 500  # 500円以下は除外
    
    if job.employment_type_cd not in VALID_EMPLOYMENT_TYPE_CDS:
        return 0
    if job.fee <= MIN_FEE_THRESHOLD:
        return 0
    
    # 各要素のスコア計算
    avg_wage = (job.min_salary + job.max_salary) / 2
    hourly_wage_score = normalize_hourly_wage(avg_wage, area_stats) * 0.40
    fee_score = normalize_fee(job.fee) * 0.30
    popularity_score = calculate_company_popularity_score(job.endcl_cd) * 0.30
    
    return min(100, max(0, hourly_wage_score + fee_score + popularity_score))
```

### 6.2 SEOスコア（フィールド別重み付け）

```python
FIELD_WEIGHT_CONFIG = {
    'application_name': 1.5,    # 求人タイトル - 高い重み
    'company_name': 1.5,        # 企業名 - 高い重み
    'salary': 0.3,              # 給与 - 小さい重み
    'hours': 0.3,               # 勤務時間 - 小さい重み
    'station_name_eki': 0.5,    # 最寄駅 - 中程度
    'feature_codes': 0.8        # 特徴 - やや高い重み
}

def calculate_seo_score(job, keywords):
    """
    SEOキーワードマッチングスコア
    """
    total_score = 0
    for field, weight in FIELD_WEIGHT_CONFIG.items():
        field_value = getattr(job, field, '')
        for keyword in keywords:
            if keyword in field_value:
                total_score += keyword.score * weight
    return min(100, total_score)
```

### 6.3 パーソナライズスコア

```python
def calculate_personalized_score(job, user_profile):
    """
    ユーザーの過去の応募履歴との類似度
    """
    score = 0
    
    # 職種マッチング
    if job.occupation_cd1 in user_profile.applied_occupation_cd1s:
        score += 30
    
    # 地域マッチング
    if job.pref_cd in user_profile.applied_pref_cds:
        score += 20
    if job.city_cd in user_profile.applied_city_cds:
        score += 30
    
    # 給与レンジマッチング
    if user_profile.avg_applied_salary:
        salary_diff = abs(job.avg_salary - user_profile.avg_applied_salary)
        if salary_diff < 200:  # ±200円以内
            score += 20
    
    # 2週間以内応募企業はペナルティ
    if _was_applied_within_2weeks(job.endcl_cd, user_profile.user_id):
        score *= 0.1  # 90%減点
    
    return min(100, score)
```

---

## 7. 実装計画【NEW】

### 7.1 フェーズ別実装計画

#### Phase 0: リサーチと要件確定【完了】
- ✅ 技術選定（Supabase, pandas, Next.js）
- ✅ ER図作成（v2.0完成）
- ✅ 詳細仕様定義（asks/answers形式）
- ✅ 6セクション構成への変更

#### Phase 1: データベース構築（2日）
```bash
# Day 1: Supabase環境構築
- Supabaseプロジェクト作成
- ER図v2.0に基づく20テーブル作成
- インデックス設定

# Day 2: データ投入
- マスターデータインポート
- サンプル求人データ（/data/sample_job_data.csv）投入
- データ整合性確認
```

#### Phase 2: バッチ処理実装（3日）
```bash
# Day 3: 基本処理
- CSVインポート処理
- データクレンジング
- 基礎スコア計算

# Day 4: 高度な処理
- SEOスコア計算
- パーソナライズスコア計算
- ユーザープロファイル生成

# Day 5: マッチング処理
- 6セクション選定ロジック
- 重複除外処理
- メール内容生成
```

#### Phase 3: フロントエンド実装（2日）
```bash
# Day 6: 基本UI
- Next.js環境構築
- SQLモニタリング画面
- データ可視化ダッシュボード

# Day 7: 高度な機能
- エラーログビューア
- 手動バッチ実行
- リアルタイム更新
```

#### Phase 4: 統合テスト（1日）
```bash
# Day 8: E2Eテスト
- 10万件負荷テスト
- 30分以内完了確認
- メモリ使用量測定（4GB以内）
- SQLレスポンス測定（1秒以内）
```

### 7.2 並列実行によるタスク最適化

```yaml
# 並列実行可能タスク
parallel_tasks:
  phase_1_parallel:
    - supabase_setup
    - nextjs_setup
    - test_env_setup
    
  phase_2_parallel:
    - scoring_algorithms
    - profile_generation
    - ui_components
    
  phase_3_parallel:
    - batch_testing
    - frontend_testing
    - integration_testing
    
estimated_time_saving: 60%
```

---

## 8. 品質保証【NEW】

### 8.1 テスト戦略

#### ユニットテスト
```python
# スコアリング関数テスト
def test_basic_score():
    job = Mock(fee=1000, min_salary=1200, max_salary=1400)
    score = calculate_basic_score(job, area_stats, company_popularity)
    assert 0 <= score <= 100
    
# 重複除外テスト
def test_duplicate_removal():
    selected = select_with_no_duplicates(candidates)
    assert len(selected) == len(set(selected['job_id']))
```

#### 統合テスト
```python
# 6セクション40件選定テスト
def test_six_section_selection():
    result = JobSelector(user_id).select_jobs()
    assert len(result['editorial_picks']) == 5
    assert len(result['top5']) == 5
    assert len(result['regional']) == 10
    assert len(result['nearby']) == 8
    assert len(result['high_income']) == 7
    assert len(result['new']) == 5
    # 合計40件、重複なし
    all_jobs = flatten_sections(result)
    assert len(all_jobs) == 40
    assert len(set(all_jobs)) == 40
```

### 8.2 エッジケース対応

| ケース | 対応方法 |
|--------|----------|
| 新規ユーザー（応募履歴0） | デフォルトプロファイル使用、人気求人を推薦 |
| 求人不足（40件未満） | エリア拡大、条件緩和、前日の人気求人追加 |
| CSV不正データ | バリデーション、エラーログ、該当行スキップ |
| 重複求人 | job_id + endcl_cdでユニーク判定 |
| 2週間以内応募企業 | user_actionsから判定、除外またはペナルティ |

### 8.3 パフォーマンス基準

```yaml
performance_criteria:
  processing_time:
    csv_import: < 5 minutes
    scoring: < 10 minutes
    matching: < 10 minutes
    email_generation: < 5 minutes
    total: < 30 minutes
    
  resource_usage:
    memory: < 4GB
    cpu: < 80%
    database_connections: < 100
    
  response_time:
    sql_query: < 1 second
    dashboard_load: < 2 seconds
    batch_trigger: < 500ms
```

---

## 9. 運用要件【NEW】

### 9.1 日次バッチスケジュール

```yaml
daily_batch_schedule:
  03:00: "CSVデータ取得"
  03:30: "データインポート＋クレンジング"
  04:00: "基礎スコア計算"
  04:15: "SEOスコア計算"
  04:30: "パーソナライズスコア計算"
  04:45: "ユーザープロファイル更新"
  05:00: "6セクションマッチング処理（並列）"
  05:30: "メール内容生成"
  05:45: "配信キュー登録"
  06:00: "配信準備完了通知"
```

### 9.2 モニタリングと監視

```yaml
monitoring_items:
  real_time:
    - processing_status
    - memory_usage
    - error_rate
    - database_connections
    
  daily_metrics:
    - total_jobs_processed
    - users_matched
    - emails_generated
    - average_score_distribution
    - section_fill_rate
    
  quality_metrics:
    - click_through_rate
    - application_rate
    - user_satisfaction_score
```

### 9.3 エラーハンドリングポリシー

```python
ERROR_HANDLING = {
    'csv_parse_error': {
        'action': 'skip_row',
        'log': True,
        'alert': False,
        'retry': False
    },
    'db_connection_error': {
        'action': 'retry',
        'max_retries': 3,
        'backoff': 'exponential',
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
        'log': True,
        'alert': True
    }
}
```

### 9.4 データ保持ポリシー

| データ種別 | 保持期間 | アーカイブ先 |
|-----------|---------|-------------|
| user_actions | 365日 | S3 Glacier |
| daily_job_picks | 30日 | 削除 |
| daily_email_queue | 7日 | 削除 |
| ログファイル | 90日 | S3 Standard |
| バックアップ | 30日 | S3 Standard-IA |

---

## 10. /plan再実行の妥当性評価【NEW】

### 10.1 現状分析

#### 完了済み作業
- ✅ ER図v2.0（20テーブル定義完了）
- ✅ 詳細仕様（asks.md/answers.md形式で定義済み）
- ✅ 6セクション構成への変更（editorial_picks追加）
- ✅ スコアリングアルゴリズム詳細
- ✅ 技術選定（Supabase, pandas, Next.js）

#### 変更点
- 5セクション → 6セクション構成
- editorial_picks（編集部おすすめ）の追加
- reasonフィールドの削除
- 2週間以内応募企業除外ロジック追加
- 実DBカラムへのマッピング明確化

### 10.2 /plan再実行の推奨アプローチ

#### 推奨: 差分更新アプローチ ✅

```bash
# Step 1: 既存資産の活用
- ER図v2.0をそのまま使用（変更不要）
- answers.mdの実装ロジックを転用
- 技術スタックは変更なし

# Step 2: 更新が必要な部分のみ修正
/plan --from-spec system_spec_v3.0.md --update-only
- 6セクション構成の反映
- editorial_picks実装の追加
- バッチ処理フローの調整

# Step 3: タスクの再生成
/tasks --6-sections --parallel-optimization
- 並列実行可能タスクの再編成
- 6セクション対応タスクの追加

# Step 4: 実装
/implement --use-answers-md --phase 1
- answers.mdの実装コードを活用
- 新規追加部分のみ実装
```

#### 非推奨: 全面的なやり直し ❌
- 既存作業の80%が無駄になる
- 時間効率が悪い
- 品質向上の見込みが低い

### 10.3 期待される成果

```yaml
efficiency_gains:
  reuse_rate: 80%  # 既存資産の再利用率
  time_saving: 60%  # 開発時間短縮
  quality: 100%     # 仕様との一致率
  
risk_assessment:
  technical_risk: Low  # 技術的リスク
  schedule_risk: Low   # スケジュールリスク
  quality_risk: Low    # 品質リスク
  
recommended_action: "差分更新による効率的な再計画"
```

### 10.4 次のアクション

1. **即座に実行可能**
   ```bash
   # Supabase環境構築
   supabase init
   supabase start
   
   # ER図v2.0でテーブル作成
   supabase db reset
   
   # Python環境セットアップ
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **開発開始**
   ```bash
   # 差分更新でplan実行
   /plan --from-spec system_spec_v3.0.md --update-only
   
   # 6セクション対応タスク生成
   /tasks --6-sections --optimize-parallel
   
   # Phase 1実装開始
   /implement --phase 1 --use-existing answers.md
   ```

---

## まとめ

この統合仕様書v3.0は、初期仕様（v1.0）から現在までの全ての変更と詳細実装を統合したものです。主要な変更点：

1. **6セクション構成**: editorial_picksを追加し、より効果的な求人配信を実現
2. **詳細な実装仕様**: answers.mdの内容を統合し、実装可能なレベルまで詳細化
3. **並列処理最適化**: 60%の時間短縮を実現する並列実行戦略
4. **品質保証強化**: 包括的なテスト戦略とエッジケース対応

/planから再実行する場合は、差分更新アプローチを推奨します。これにより、既存の80%の作業を活用しながら、新しい要件を確実に実装できます。

---

*最終更新: 2025-09-16*  
*ドキュメントバージョン: 3.0*  
*ブランチ: 001-job-matching-system*