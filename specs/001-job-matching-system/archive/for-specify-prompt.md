# 🚀 バイト求人マッチングシステム 実装完全ガイド
## コピペで完成！Supabase + Python実装手順

> **Version**: 2.0  
> **対象システム**: job-score-for-mail-system  
> **技術スタック**: Supabase + Python + FastAPI
> **想定規模**: 10万求人 × 1万ユーザー = 毎日40万件配信  
> **作成日**: 2025-09-15

## ⚡ システム概要
本ガイドは、以下のプロンプトを**順番にコピペ実行**することで、完全なバイト求人マッチングシステムが構築できる実装ガイドです。

### システムの主要機能
1. **データ取込**: CSVから10万件の求人データを日次インポート
2. **スコアリング**: SEOキーワードとユーザー行動に基づく求人評価
3. **マッチング**: 1万人のユーザーに最適な40件を自動選定
4. **メール配信**: パーソナライズされた求人メールを毎日配信
5. **フィードバック**: クリック・応募データを学習に活用

### 実装順序（重要）
以下の順番で実装することで依存関係を満たし、エラーなく構築できます：
1. Supabaseテーブル作成 → 2. マスターデータ投入 → 3. バッチ処理 → 4. API構築

---

## 📋 Phase 1: Supabase データベース構築

### 1.1 プロジェクト初期化とテーブル作成

```markdown
/specify --think-hard "
Supabase用のデータベーススキーマを作成してください。

ER図: docs/ER/20250904_er_complete_v2.0.mmd を参照

要件：
1. 全テーブルのCREATE TABLE文を生成（型定義は正確に）
2. 主キー、外部キー、インデックスを適切に設定
3. パフォーマンス最適化のための複合インデックス追加
4. RLS（Row Level Security）ポリシー設定

特に重要なテーブル：
- jobs: 10万件の求人データ（bigint job_id主キー）
- users: 1万人のユーザー（uuid user_id主キー）
- user_job_mapping: 日次40万件のマッピング
- daily_email_queue: 日次1万件のメール配信

成果物：
1. migrations/001_create_tables.sql（全テーブル作成SQL）
2. migrations/002_create_indexes.sql（インデックス作成SQL）
3. migrations/003_create_functions.sql（ストアドファンクション）
4. setup/supabase_client.py（Python接続クライアント）
"
```

### 1.2 マスターデータテーブル設定

```markdown
/specify "
マスターデータテーブルのCSVインポート機能を実装してください。

対象CSVファイル（data/ディレクトリ）：
- prefecture_view.csv → prefecture_master
- city_view.csv → city_master
- occupation_view.csv → occupation_master
- employment_type_view.csv → employment_type_master
- salary_type_view.csv → salary_type_master
- feature_view.csv → feature_master

要件：
1. CSVファイルを読み込んでSupabaseに一括インサート
2. 重複チェック（UPSERT処理）
3. データ型変換とバリデーション
4. エラーハンドリングとログ出力

成果物：
scripts/import_master_data.py
- 全マスターデータを一括インポート
- 実行コマンド: python scripts/import_master_data.py
"
```

---

## 📊 Phase 2: 求人データ処理パイプライン

### 2.1 求人データインポート

```markdown
/specify --think-hard "
求人データ（sample_job_data.csv）の日次インポートバッチを実装してください。

処理フロー：
1. CSVファイル読込（10万件想定）
2. データクレンジング
   - 文字コード変換（UTF-8統一）
   - NULL値処理
   - 不正データ除外
3. jobsテーブルへの投入
   - jobs_match_raw（マッチング用データ）
   - jobs_contents_raw（表示用データ）
4. feature_codes解析
   - カンマ区切りをリスト化
   - feature_masterと照合

パフォーマンス要件：
- 10万件を10分以内で処理
- メモリ使用量2GB以内
- バッチサイズ: 1000件単位

成果物：
batch/daily_job_import.py
- 実行: python batch/daily_job_import.py --date 2025-09-15
- ログ出力: logs/job_import_YYYYMMDD.log
"
```

### 2.2 求人スコアリング処理

```markdown
/specify --think-hard "
求人スコアリングアルゴリズムを実装してください。

スコア計算要素：
1. 基礎スコア（100点満点）
   - 時給の高さ: (時給 - エリア平均) / エリア平均 × 30点
   - アクセスの良さ: 駅からの距離で計算（1分=満点30点、10分=0点）
   - 福利厚生: feature_codes数 × 5点（最大30点）
   - 人気度: 過去の応募数 / 平均応募数 × 10点

2. SEOキーワードマッチング（最大100点）
   - semrush_keywordsテーブルとのマッチング
   - keyword_scoringテーブルの重み係数適用
   - 完全一致: 100点、部分一致: 50点

3. ユーザー個別スコア（最大100点）
   - user_profilesの応募履歴との類似度
   - 協調フィルタリング（類似ユーザーの応募パターン）

処理要件：
- 10万求人 × 1万ユーザー = 10億スコア計算
- 段階的処理（まず全体スコア、次に個別スコア）
- job_enrichmentテーブルに結果保存

成果物：
batch/calculate_job_scores.py
- 基礎スコア計算
- SEOスコア計算
- パーソナライズスコア計算
- 実行時間: 30分以内
"
```

### 2.3 カテゴリ分類処理

```markdown
/specify "
求人のカテゴリ自動分類システムを実装してください。

14のニーズカテゴリ分類：
1. テキストマッチング方式
   - 対象: application_name, company_name, salary, hours
   - キーワード定義: needs_category_masterテーブル
   
2. feature_code方式
   - 未経験歓迎: feature_code 103
   - 学生歓迎: feature_code 104
   
3. 数値比較方式
   - 高時給: エリア平均時給の1.2倍以上

12の職種カテゴリ分類：
- occupation_cd1の100番台単位で分類

成果物：
batch/categorize_jobs.py
- job_enrichmentのneeds_categories配列を更新
- occupation_categoryフィールドを更新
"
```

---

## 🎯 Phase 3: ユーザーマッチングシステム

### 3.1 ユーザープロファイル生成

```markdown
/specify --think-hard "
ユーザーの応募履歴からプロファイルを生成するシステムを実装してください。

プロファイル生成ロジック：
1. user_actionsテーブルから応募履歴を集計
2. 以下の項目を頻度順にカウント
   - 応募都道府県（pref_cd）
   - 応募市区町村（city_cd）
   - 応募職種（occupation_cd1,2,3）
   - 応募雇用形態（employment_type_cd）
   - 応募給与タイプ（salary_type_cd）
   - 応募特徴（feature_codes）
   - 応募企業（endcl_cd）

3. 統計情報の計算
   - 平均応募給与
   - 応募頻度（週次、月次）
   - 最終応募日からの経過日数

4. user_profilesテーブルを更新
   - フォーマット: 'コード:回数,コード:回数'
   - 例: '13:5,14:3,11:1'（東京5回、神奈川3回、埼玉1回）

成果物：
batch/generate_user_profiles.py
- 日次実行で差分更新
- 1万ユーザーを5分以内で処理
"
```

### 3.2 日次マッチング処理

```markdown
/specify --think-hard "
毎日のユーザー×求人マッチングを実行するバッチ処理を実装してください。

マッチングアルゴリズム：
1. 各ユーザーに対して求人をスコアリング
   - job_enrichmentの基礎スコア
   - user_profilesとの類似度スコア
   - 協調フィルタリングスコア

2. 選定ルール（各ユーザー40件）
   - TOP5: 最高スコア5件
   - 地域別TOP10: ユーザー居住都道府県の求人10件
   - 近隣TOP10: ユーザー居住市区町村と隣接市の求人10件
   - お得バイトTOP10: 特別な特典がある求人10件
   - 新着5件: 過去3日以内に登録された求人5件

3. 多様性の確保
   - 同一企業（endcl_cd）は最大5件まで
   - 職種カテゴリをバランスよく配分

4. user_job_mappingテーブルに保存
   - mapping_date: 配信日
   - personalized_score: 個別スコア
   - rank_in_user: ユーザー内順位
   - is_selected: 選定フラグ（40件のみtrue）

処理要件：
- 1万ユーザー × 10万求人を30分以内で処理
- メモリ効率的な処理（ユーザー単位でバッチ処理）

成果物：
batch/daily_matching.py
- 実行: python batch/daily_matching.py --date 2025-09-15
- daily_job_picksテーブルも同時更新
"
```

---

## 📧 Phase 4: メール配信システム

### 4.1 メール内容生成

```markdown
/specify --think-hard "
パーソナライズメール内容を生成するシステムを実装してください。

メール生成要件：
1. daily_job_picksから各ユーザーの40件を取得

2. LLMを使用した魅力的なタイトル生成
   - 求人タイトルを20文字に要約
   - キャッチーなフレーズ追加
   - 例: '【夕方4hで7,400円】駅ナカベーカリー品出し'

3. セクション別コンテンツ生成
   - TOP5: 詳細情報付き（給与、時間、特典）
   - 地域別TOP10: タイトルと給与のみ
   - 近隣TOP10: タイトルのみ
   - お得バイト: 特典を強調
   - 新着: NEW!マーク付き

4. daily_email_queueテーブルに保存
   - JSONBフィールドに構造化データ
   - HTMLテンプレートの変数として使用

LLM活用（OpenAI API）：
- 求人タイトルの要約
- キャッチフレーズ生成
- 特典の魅力的な表現

成果物：
batch/generate_emails.py
- 1万件のメールを15分で生成
- テンプレート: templates/email_template.html
"
```

### 4.2 メール配信処理

```markdown
/specify "
SendGrid/AWS SESを使用したメール配信システムを実装してください。

配信要件：
1. daily_email_queueから未送信メールを取得
2. HTMLメールとして整形
3. 配信実行
   - バッチサイズ: 100件/分（配信制限対策）
   - リトライ処理（3回まで）
   - エラーハンドリング

4. 配信結果の記録
   - delivery_status更新（sent/failed）
   - sent_at タイムスタンプ
   - エラーログ記録

5. バウンス処理
   - ハードバウンス: users.is_active = false
   - ソフトバウンス: リトライキューに追加

成果物：
batch/send_daily_emails.py
- 毎朝6時実行
- 1万件を30分で配信完了
- 配信レポート生成
"
```

---

## 📈 Phase 5: 分析・フィードバックシステム

### 5.1 アクショントラッキング

```markdown
/specify "
ユーザーのクリック・応募行動を記録するAPIを実装してください。

FastAPI エンドポイント：
1. POST /api/track/click
   - job_id, user_id, source_type, section
   - user_actionsテーブルに記録

2. POST /api/track/apply
   - job_id, user_id, source_queue_id
   - 応募時の求人情報も保存

3. GET /api/stats/user/{user_id}
   - ユーザーの行動統計

4. GET /api/stats/job/{job_id}
   - 求人のパフォーマンス統計

トラッキング情報：
- デバイス情報
- クリック位置（TOP5の何番目か等）
- 経過時間（メール送信からの時間）

成果物：
api/tracking.py
- FastAPIアプリケーション
- 非同期処理でレスポンス高速化
"
```

### 5.2 レポート生成

```markdown
/specify "
日次・週次・月次レポートを生成するシステムを実装してください。

レポート内容：
1. 配信統計
   - 配信成功率
   - 開封率
   - クリック率
   - 応募率

2. 求人パフォーマンス
   - スコア別のクリック率
   - カテゴリ別の応募率
   - 企業別のパフォーマンス

3. ユーザー分析
   - アクティブユーザー数
   - 応募傾向の変化
   - 離脱ユーザー分析

出力形式：
- PDF レポート
- CSVデータ
- ダッシュボード用JSON

成果物：
batch/generate_reports.py
- 日次: 毎朝8時
- 週次: 月曜9時
- 月次: 1日10時
"
```

---

## 🔧 Phase 6: 運用・保守ツール

### 6.1 バッチ処理スケジューラ

```markdown
/specify "
全バッチ処理を管理するスケジューラを実装してください。

スケジュール：
03:00 - データインポート（daily_job_import.py）
03:30 - スコア計算（calculate_job_scores.py）
04:00 - カテゴリ分類（categorize_jobs.py）
04:30 - ユーザープロファイル更新（generate_user_profiles.py）
05:00 - マッチング処理（daily_matching.py）
05:30 - メール生成（generate_emails.py）
06:00 - メール配信（send_daily_emails.py）
08:00 - レポート生成（generate_reports.py）

要件：
- Airflow または APScheduler使用
- 依存関係管理
- エラー時の通知
- リトライ処理

成果物：
scheduler/daily_pipeline.py
- DAG定義またはスケジュール設定
- 監視ダッシュボード
"
```

### 6.2 データ検証・ヘルスチェック

```markdown
/specify "
システムの健全性を監視するヘルスチェックツールを実装してください。

チェック項目：
1. データ整合性
   - 求人数の異常検知
   - 重複データチェック
   - 外部キー整合性

2. パフォーマンス監視
   - バッチ処理時間
   - API レスポンスタイム
   - データベース負荷

3. ビジネスKPI
   - 配信成功率が95%以上
   - クリック率が20%以上
   - 日次アクティブユーザー5000人以上

4. アラート
   - Slack/Email通知
   - 重要度別のアラート設定

成果物：
monitoring/health_check.py
- 10分ごとに実行
- ダッシュボード表示
- アラート自動送信
"
```

---

## 🚀 Phase 7: 本番環境構築

### 7.1 環境構築スクリプト

```markdown
/specify "
本番環境を自動構築するセットアップスクリプトを作成してください。

セットアップ内容：
1. Python環境構築
   - requirements.txt生成
   - 仮想環境作成
   - 依存パッケージインストール

2. Supabase設定
   - 環境変数設定（.env）
   - データベース初期化
   - RLSポリシー適用

3. ディレクトリ構造作成
   batch/
   api/
   scripts/
   logs/
   data/
   templates/

4. 初期データ投入
   - マスターデータインポート
   - サンプルデータ投入（テスト用）

5. cron設定
   - バッチ処理のcron登録
   - ログローテーション設定

成果物：
setup.sh
- ワンコマンドで環境構築完了
- README.md（セットアップ手順書）
"
```

### 7.2 デプロイメント設定

```markdown
/specify "
Docker/Kubernetes用のデプロイメント設定を作成してください。

要件：
1. Dockerfile
   - Python 3.11ベース
   - 必要なパッケージインストール
   - バッチ処理とAPI両対応

2. docker-compose.yml
   - アプリケーションコンテナ
   - PostgreSQL（ローカル開発用）
   - Redis（キャッシュ用）

3. k8s/
   - deployment.yaml（アプリケーション）
   - cronjob.yaml（バッチ処理）
   - service.yaml（API公開）
   - configmap.yaml（設定）
   - secret.yaml（認証情報）

4. CI/CD
   - .github/workflows/deploy.yml
   - 自動テスト実行
   - イメージビルド
   - デプロイ

成果物：
- Dockerfile
- docker-compose.yml
- k8s/ディレクトリ
- .github/workflows/deploy.yml
"
```

---

## 📝 実装チェックリスト

### Phase 1: データベース ✅
- [ ] Supabaseプロジェクト作成
- [ ] テーブル作成（migrations実行）
- [ ] マスターデータインポート
- [ ] 接続テスト

### Phase 2: 求人処理 ✅
- [ ] CSVインポート処理
- [ ] スコアリング実装
- [ ] カテゴリ分類実装
- [ ] バッチテスト実行

### Phase 3: マッチング ✅
- [ ] プロファイル生成
- [ ] マッチングアルゴリズム
- [ ] 選定ルール実装
- [ ] パフォーマンステスト

### Phase 4: メール配信 ✅
- [ ] メール生成処理
- [ ] SendGrid/SES設定
- [ ] 配信処理実装
- [ ] テスト配信

### Phase 5: 分析 ✅
- [ ] トラッキングAPI
- [ ] レポート生成
- [ ] ダッシュボード
- [ ] KPI監視

### Phase 6: 運用 ✅
- [ ] スケジューラ設定
- [ ] ヘルスチェック
- [ ] アラート設定
- [ ] ログ管理

### Phase 7: 本番環境 ✅
- [ ] 環境構築スクリプト
- [ ] Docker化
- [ ] K8s設定
- [ ] CI/CD設定

---

## 🎯 クイックスタート（最速実装パス）

最小構成で動作確認したい場合の実装順序：

```bash
# 1. 環境準備（5分）
python -m venv venv
source venv/bin/activate
pip install supabase pandas fastapi

# 2. Supabase設定（10分）
# Supabaseダッシュボードでプロジェクト作成
# .envファイルに認証情報設定

# 3. 最小構成の実装（30分）
/specify "最小構成のMVPを実装:
- jobsテーブルのみ作成
- CSVインポート（1000件）
- 簡単なスコアリング
- TOP10選定
- コンソール出力"

# 4. 動作確認
python mvp_demo.py
```

---

## 🔍 トラブルシューティング

### よくある問題と解決法

#### Supabase接続エラー
```python
# .env ファイル確認
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-anon-key

# 接続テスト
from supabase import create_client
client = create_client(url, key)
```

#### メモリ不足（大量データ処理時）
```python
# チャンク処理に変更
for chunk in pd.read_csv('large_file.csv', chunksize=1000):
    process_chunk(chunk)
```

#### 処理速度が遅い
```python
# 並列処理を使用
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(process_user, users)
```

---

## 📚 参考資料

- [Supabase Python Documentation](https://supabase.com/docs/reference/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- システム仕様書: `docs/20250901_system_spec_v1.0.md`
- ER図: `docs/ER/20250904_er_complete_v2.0.mmd`

---

## 💡 実装のコツ

1. **段階的実装**: まず最小構成で動作確認してから機能追加
2. **ログ活用**: 全処理にログ出力を入れてデバッグを容易に
3. **テストデータ**: 本番の1/100スケールでテスト（1000求人×100ユーザー）
4. **パフォーマンス**: ボトルネックをプロファイリングで特定
5. **エラー処理**: 必ずtry-exceptとリトライ処理を実装

---

*このガイドに従って実装すれば、確実に動作するシステムが構築できます。*
*各プロンプトをコピペして実行し、生成されたコードを順次実装してください。*