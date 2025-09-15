# クイックスタートガイド: バイト求人マッチングシステム

**バージョン**: 1.0.0  
**最終更新**: 2025-09-15  
**所要時間**: 約30分（初回セットアップ）

## 📋 前提条件

- Python 3.11+ がインストール済み
- Node.js 20+ がインストール済み
- Supabaseアカウント作成済み
- Git がインストール済み

## 🚀 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/job-matching-system.git
cd job-matching-system
```

### 2. Supabaseプロジェクトの作成

#### 2.1 Supabase CLIのインストール
```bash
# macOS
brew install supabase/tap/supabase

# その他のOS
npm install -g supabase
```

#### 2.2 プロジェクト初期化
```bash
supabase init
supabase start
```

#### 2.3 環境変数の設定
```bash
# .env.localファイルを作成
cat > .env.local << EOF
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
EOF
```

### 3. データベースセットアップ

#### 3.1 マイグレーション実行
```bash
# データベーススキーマの作成
supabase db push

# または個別実行
supabase migration up
```

#### 3.2 マスターデータ投入
```bash
# マスターデータのインポート
python scripts/import_master_data.py
```

#### 3.3 サンプル求人データ投入
```bash
# テスト用データ（sample_job_data.csv）のインポート
python scripts/import_sample_jobs.py \
  --file data/sample_job_data.csv \
  --batch-size 1000
```

### 4. Pythonバックエンドセットアップ

#### 4.1 仮想環境作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 4.2 依存関係インストール
```bash
pip install -r requirements.txt
```

#### 4.3 初回スコアリング実行
```bash
# 求人データのスコアリング
python src/batch/scoring.py --initial-run

# 確認
python -c "
from src.db import get_supabase_client
client = get_supabase_client()
result = client.table('job_enrichment').select('count').execute()
print(f'スコアリング完了: {result.data[0]['count']}件')
"
```

### 5. Next.js フロントエンドセットアップ

#### 5.1 依存関係インストール
```bash
cd frontend
npm install
```

#### 5.2 開発サーバー起動
```bash
npm run dev
```

#### 5.3 アクセス確認
```
http://localhost:3000/monitoring
```

## 🔄 日次バッチ処理の実行

### 手動実行（開発時）

```bash
# 完全な日次処理フロー
python src/batch/daily_batch.py --date 2025-09-15

# または個別実行
python src/batch/scoring.py
python src/batch/matching.py
python src/batch/email_generation.py
```

### 処理の確認

```bash
# 処理状況確認
python scripts/check_batch_status.py --date 2025-09-15

# 出力例:
# ✅ スコアリング: 100,000件完了
# ✅ マッチング: 10,000ユーザー処理完了
# ✅ メール生成: 10,000件生成完了
# 処理時間: 28分15秒
```

## 🧪 動作確認テスト

### 1. データベース接続確認

```python
# Python shell で実行
from src.db import get_supabase_client

client = get_supabase_client()
response = client.table('jobs').select('count').execute()
print(f"求人データ: {response.data[0]['count']}件")
```

### 2. API動作確認

```bash
# ヘルスチェック
curl http://localhost:3000/api/monitoring/health

# 統計情報取得
curl http://localhost:3000/api/monitoring/stats

# テストユーザーのマッチング結果確認
curl http://localhost:3000/api/matching/results/1
```

### 3. SQL監視インターフェース確認

1. ブラウザで http://localhost:3000/monitoring を開く
2. 以下のクエリを実行:

```sql
-- アクティブな求人数
SELECT COUNT(*) FROM jobs WHERE is_active = true;

-- ユーザー別マッチング数
SELECT user_id, COUNT(*) as match_count 
FROM daily_job_picks 
WHERE pick_date = CURRENT_DATE 
GROUP BY user_id 
LIMIT 10;

-- スコア分布
SELECT 
  CASE 
    WHEN basic_score >= 80 THEN '80-100'
    WHEN basic_score >= 60 THEN '60-80'
    WHEN basic_score >= 40 THEN '40-60'
    ELSE '0-40'
  END as score_range,
  COUNT(*) as count
FROM job_enrichment
GROUP BY score_range
ORDER BY score_range;
```

## 📊 パフォーマンス検証

### メモリ使用量確認
```bash
# バッチ処理中のメモリ監視
python scripts/monitor_performance.py --process daily_batch

# 期待値: < 4GB
```

### 処理時間測定
```bash
# タイミング付き実行
time python src/batch/daily_batch.py --date 2025-09-15

# 期待値: < 30分
```

### 並列処理の確認
```bash
# ワーカー数を指定して実行
python src/batch/matching.py --workers 5 --debug

# ログで並列実行を確認
# [INFO] Starting 5 parallel workers...
# [INFO] Worker 1: Processing users 1-2000
# [INFO] Worker 2: Processing users 2001-4000
# ...
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. Supabase接続エラー
```bash
# エラー: "Connection refused"
# 解決:
supabase status  # 起動確認
supabase start   # 再起動
```

#### 2. メモリ不足エラー
```bash
# エラー: "MemoryError"
# 解決: バッチサイズを調整
python src/batch/scoring.py --batch-size 500
```

#### 3. インポートエラー
```bash
# エラー: "ModuleNotFoundError"
# 解決:
pip install -r requirements.txt --upgrade
```

#### 4. Next.js ビルドエラー
```bash
# エラー: "Module not found"
# 解決:
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

## 📚 次のステップ

### 開発を続ける場合

1. **テスト実行**
   ```bash
   pytest tests/
   npm test
   ```

2. **本番環境設定**
   - Supabase Cloudプロジェクト作成
   - 環境変数を本番用に更新
   - GitHub Actionsでデプロイ設定

3. **監視設定**
   - ログ収集設定
   - アラート設定
   - パフォーマンス監視

### カスタマイズポイント

- **スコアリングアルゴリズム**: `src/scoring/algorithms.py`
- **マッチングロジック**: `src/matching/recommender.py`
- **メールテンプレート**: `templates/email/`
- **SQL監視画面**: `frontend/app/monitoring/`

## 📞 サポート

問題が解決しない場合は、以下をご確認ください:

- [ドキュメント](docs/)
- [Issues](https://github.com/your-org/job-matching-system/issues)
- [Wiki](https://github.com/your-org/job-matching-system/wiki)

---

**Happy Matching! 🎉**