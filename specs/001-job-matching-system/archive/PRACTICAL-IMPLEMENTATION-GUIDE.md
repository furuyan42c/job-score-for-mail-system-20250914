# 🎯 Job Matching System 実践的実装ガイド v2.0

**作成日**: 2025-09-17  
**目的**: 現実的で実行可能な段階的実装プロセス  
**推定時間**: 28-36時間（分割実行推奨）

---

## ⚠️ 実装可能性の検証結果

### 🔴 手動作業が必要な部分

1. **Supabase設定**（約30分）
   - プロジェクト作成（https://supabase.com）
   - API KEYの取得
   - データベース接続情報の確認
   - SQLエディタでのテーブル作成

2. **環境設定**（約15分）
   - `.env.local`ファイルの作成
   - Node.js/Python環境の準備
   - パッケージのインストール（npm/pip）

3. **外部サービス**（約15分）
   - OpenAI API KEYの取得（GPT-4使用）
   - Git初期設定

### 🟡 Claude Codeが自動化できる部分

- コード生成（100%）
- ファイル作成・編集（100%）
- テストコード作成（100%）
- ドキュメント生成（100%）

### 🟢 最適な実装戦略

**分割実行を強く推奨**：
- Phase単位で実行（1 Phaseずつ）
- 各Phase後に動作確認
- エラー発生時に修正しやすい

---

## 📊 改善版: 段階的実装プラン

### 🎯 準備フェーズ（手動: 1時間）

#### Step 1: Supabase準備
```markdown
【手動作業】
1. https://supabase.com でプロジェクト作成
2. プロジェクト名: "job-matching-system"
3. Region: Tokyo (ap-northeast-1)
4. Database Password: 安全なパスワードを設定

【取得する情報】
- SUPABASE_URL: https://xxxxx.supabase.co
- SUPABASE_ANON_KEY: eyJxxx...
- Database Host: db.xxxxx.supabase.co
- Database Password: 設定したパスワード
```

#### Step 2: 開発環境準備
```bash
# 手動実行
cd /Users/naoki/000_PROJECT/job-score-for-mail-system-20250914/

# Python環境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install fastapi uvicorn supabase-py pandas apscheduler

# Node.js環境
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install @supabase/supabase-js
```

#### Step 3: 環境変数設定
```bash
# backend/.env を作成
cat > backend/.env << EOF
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=postgresql://...
EOF

# frontend/.env.local を作成
cat > frontend/.env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=your_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key_here
EOF
```

---

## 🚀 Phase 1: データベース構築（Claude Code: 2時間）

### プロンプト 1.1: SQL生成とMigration
```markdown
==========================================
Phase 1: データベース構築を開始
==========================================

/sc:load

specs/001-job-matching-system/data-model.mdを読み込んで、
以下を生成してください：

1. database/migrations/001_create_tables.sqlを作成
   - 全テーブルのCREATE文
   - 適切なインデックス
   - 外部キー制約

2. database/migrations/002_create_functions.sqlを作成
   - スコアリング用の関数
   - トリガー関数

3. database/seeds/001_master_data.sqlを作成
   - prefecture_master
   - city_master  
   - occupation_master
   - employment_type_master

4. database/setup_database.md を作成
   - Supabaseでの実行手順
   - エラー対処法

--serena --seq

生成完了後、実行手順を表示してください。
```

### 手動実行: Supabaseでテーブル作成
```markdown
【手動作業】
1. Supabaseダッシュボードにログイン
2. SQL Editorを開く
3. 生成されたSQLを順番に実行：
   - 001_create_tables.sql
   - 002_create_functions.sql
   - 001_master_data.sql
4. Table Editorで確認
```

---

## 🚀 Phase 2: バックエンド基礎（Claude Code: 4時間）

### プロンプト 2.1: FastAPI基盤
```markdown
==========================================
Phase 2: バックエンド基礎実装
==========================================

TodoWriteで以下のタスクを管理：
1. FastAPIプロジェクト構造作成
2. Pydanticモデル定義
3. データベース接続設定
4. 基本APIエンドポイント

backend/ディレクトリに以下を実装：

## 2.1 プロジェクト構造
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPIアプリケーション
│   ├── config.py        # 設定管理
│   ├── database.py      # Supabase接続
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py       # Jobモデル
│   │   ├── user.py      # Userモデル
│   │   └── scoring.py   # スコアリングモデル
│   └── routers/
│       ├── __init__.py
│       ├── jobs.py      # 求人API
│       └── health.py    # ヘルスチェック
└── requirements.txt

--serena --seq

実装後、以下のテストコードも作成：
- tests/test_connection.py
- tests/test_models.py
```

### プロンプト 2.2: スコアリングエンジン
```markdown
==========================================
Phase 2.2: スコアリングエンジン実装
==========================================

specs/001-job-matching-system/answers.mdを参照して、
backend/app/services/scoring_engine.pyを実装：

## 基礎スコア計算（重要度: 高）
def calculate_base_score(job: JobModel) -> float:
    """
    fee（応募促進費用）を中心とした基礎スコア
    - fee: 0-5000円 → 0-50点
    - 給与: 時給/日給の魅力度 → 0-30点  
    - アクセス: 駅からの距離 → 0-20点
    """

## SEOスコア計算
def calculate_seo_score(job: JobModel, user: UserModel) -> float:
    """
    マッチング要素のスコア
    - 地域マッチング
    - 職種カテゴリマッチング
    - 勤務条件適合度
    """

## パーソナライズスコア
def calculate_personal_score(job: JobModel, user_profile: UserProfile) -> float:
    """
    ユーザー固有の選好スコア
    - 過去の応募履歴
    - クリック履歴
    - 類似ユーザーの行動
    """

--seq --think-hard

テストケースも作成：
- tests/test_scoring.py
```

---

## 🚀 Phase 3: コア機能実装（Claude Code: 6時間）

### プロンプト 3.1: マッチングアルゴリズム
```markdown
==========================================
Phase 3: マッチングアルゴリズム実装
==========================================

backend/app/services/job_selector.pyを実装：

## 最適化選定ロジック
class JobSelector:
    def select_top_jobs(
        self,
        user_id: int,
        job_pool: List[Job],
        limit: int = 40
    ) -> List[Job]:
        """
        10万件から40件を効率的に選定
        
        処理フロー:
        1. 初期フィルタリング（有効期限、地域）
        2. スコア計算（3段階）
        3. カテゴリ分散の考慮
        4. 上位40件選定
        """

パフォーマンス要件:
- 1ユーザーあたり処理時間: 180ms以内
- メモリ使用量: 500MB以内

--seq --think-hard

最適化のポイント:
- NumPy/Pandasでベクトル化処理
- 事前計算されたスコアの活用
- インデックスの効果的利用
```

### プロンプト 3.2: バッチ処理
```markdown
==========================================
Phase 3.2: バッチ処理パイプライン
==========================================

backend/app/batch/daily_batch.pyを実装：

## 日次バッチ処理
class DailyBatchProcessor:
    def run_daily_batch(self):
        """
        毎日午前3時に実行
        
        処理ステップ:
        1. CSVインポート（10万件）
        2. データクレンジング
        3. スコア事前計算
        4. 全ユーザーマッチング（1万人）
        5. メール生成
        6. 配信準備
        
        目標: 30分以内で完了
        """

APSchedulerでスケジューリング設定も含む

--seq --serena

エラーハンドリングとモニタリング:
- 各ステップのログ記録
- エラー時のリトライ
- Slackへの通知（オプション）
```

---

## 🚀 Phase 4: フロントエンド（Claude Code: 4時間）

### プロンプト 4.1: SQL実行画面
```markdown
==========================================
Phase 4: SQL実行画面（最優先）
==========================================

frontend/app/monitoring/page.tsxを実装：

## SQL実行インターフェース
- Supabaseへの直接クエリ実行
- 結果のテーブル表示
- CSVエクスポート
- エラーハンドリング

コンポーネント構成:
- SQLEditor: Monaco Editorベース
- ResultTable: データグリッド表示
- ExportButton: CSV/JSON出力

セキュリティ考慮:
- 読み取り専用モード
- クエリ実行制限
- タイムアウト設定

--magic --c7

スタイリング:
- Tailwind CSS使用
- ダークモード対応
- レスポンシブデザイン
```

### プロンプト 4.2: 管理ダッシュボード
```markdown
==========================================
Phase 4.2: 管理ダッシュボード
==========================================

frontend/app/dashboard/page.tsxを実装：

## ダッシュボードコンポーネント
- バッチ処理状況
- システムメトリクス
- エラーログ表示

リアルタイム更新:
- WebSocket or Server-Sent Events
- 5秒ごとの自動更新

--magic --c7
```

---

## 🚀 Phase 5: 統合テスト（Claude Code: 2時間）

### プロンプト 5.1: E2Eテスト
```markdown
==========================================
Phase 5: 統合テスト作成
==========================================

tests/integration/にE2Eテストを作成：

1. test_full_pipeline.py
   - CSV読み込み → スコアリング → 選定 → メール生成

2. test_performance.py  
   - 10万件×1万人のスケールテスト
   - 30分以内完了の検証

3. test_api.py
   - APIエンドポイントのテスト

--play --seq

カバレッジ目標: 80%以上
```

---

## ✅ Phase 6: 検証と最適化（Claude Code: 2時間）

### プロンプト 6.1: 最終検証
```markdown
==========================================
Phase 6: 最終検証と最適化
==========================================

/verify-and-pr 001-job-matching-system --comprehensive --play

以下を確認：
1. 全テスト合格
2. パフォーマンス基準達成
3. セキュリティチェック
4. コード品質

/sc:business-panel @specs/001-job-matching-system/spec.md
ビジネス価値の検証

/sc:optimize --target performance
最適化の実施

/sc:checkpoint "実装完了"
/sc:save
```

---

## 📋 実行チェックリスト

### Phase 0: 準備（手動）
- [ ] Supabase プロジェクト作成
- [ ] API KEY取得・設定
- [ ] Python/Node.js環境構築
- [ ] 環境変数ファイル作成

### Phase 1: DB構築
- [ ] SQLファイル生成（Claude Code）
- [ ] Supabaseで実行（手動）
- [ ] テーブル作成確認

### Phase 2: バックエンド基礎
- [ ] FastAPI構造作成
- [ ] モデル定義
- [ ] スコアリングエンジン

### Phase 3: コア機能
- [ ] マッチングアルゴリズム
- [ ] バッチ処理

### Phase 4: フロントエンド
- [ ] SQL実行画面
- [ ] ダッシュボード

### Phase 5: テスト
- [ ] 統合テスト
- [ ] パフォーマンステスト

### Phase 6: 最終確認
- [ ] 品質検証
- [ ] 最適化
- [ ] ドキュメント

---

## 🚨 トラブルシューティング

### Supabase接続エラー
```python
# backend/app/database.py で確認
from supabase import create_client
import os

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase credentials not found")
```

### メモリ不足（大量データ処理）
```python
# チャンク処理の実装
def process_in_chunks(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]
```

### 処理時間超過
```python
# 並列処理の活用
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_user, users)
```

---

## 📝 推奨実行順序

1. **Day 1（8時間）**
   - 準備フェーズ（1時間）
   - Phase 1: DB構築（2時間）
   - Phase 2: バックエンド基礎（4時間）
   - 動作確認（1時間）

2. **Day 2（8時間）**
   - Phase 3: コア機能（6時間）
   - Phase 4の一部: SQL実行画面（2時間）

3. **Day 3（6時間）**
   - Phase 4完了: フロントエンド（2時間）
   - Phase 5: テスト（2時間）
   - Phase 6: 検証・最適化（2時間）

4. **Day 4（予備）**
   - バグ修正
   - 追加機能
   - ドキュメント整備

---

*このガイドに従って、確実に実装を進めてください*
*各Phase完了後は必ず動作確認を行ってから次に進んでください*