# 技術リサーチ結果: バイト求人マッチングシステム

**作成日**: 2025-09-15  
**ステータス**: 完了  
**対象**: 10万求人×1万ユーザーの日次マッチングシステム

## 1. Supabase Python Client

### 決定
- **採用**: `supabase-py` v2.x を使用
- **バージョン**: 最新安定版 (2.x系)

### 根拠
- PostgreSQL互換でスケーラブル
- リアルタイムサブスクリプション対応
- RLS（Row Level Security）で安全なデータアクセス
- Python公式クライアントの安定性

### ベストプラクティス
```python
# 接続プール管理
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# バッチ挿入（1000件単位）
def batch_insert(data, table, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        supabase.table(table).insert(batch).execute()
```

### 検討された代替案
- Firebase: リアルタイム性は高いがSQL互換性が低い
- 直接PostgreSQL: 管理コストが高い
- DynamoDB: NoSQLのため複雑なクエリに不向き

## 2. Pandas最適化（10万件処理）

### 決定
- **採用**: pandas 2.x with PyArrow backend
- **メモリ管理**: chunking + dtype最適化

### 根拠
- PyArrowで2-3倍のメモリ効率改善
- 10万件を4GB以内で処理可能
- NumPyとの高い互換性

### 最適化戦略
```python
# メモリ効率的な読み込み
import pandas as pd

# カテゴリ型で最大80%メモリ削減
dtype_dict = {
    'job_id': 'uint32',
    'company_name': 'category',
    'prefecture': 'category',
    'salary': 'uint32'
}

# チャンク処理
chunk_size = 10000
for chunk in pd.read_csv('jobs.csv', 
                         chunksize=chunk_size,
                         dtype=dtype_dict):
    process_chunk(chunk)
```

### 検討された代替案
- Dask: オーバーヘッドが大きい（10万件には不要）
- Polars: 高速だが生態系が未成熟
- Pure Python: 処理速度が30分を超える

## 3. 協調フィルタリング実装

### 決定
- **採用**: scikit-learn + implicit library
- **アルゴリズム**: ALS (Alternating Least Squares)

### 根拠
- 暗黙的フィードバック（応募履歴）に最適
- 1万ユーザー×10万アイテムで高速（<5分）
- スパース行列対応でメモリ効率的

### 実装アプローチ
```python
from implicit.als import AlternatingLeastSquares
import scipy.sparse as sparse

# ユーザー×求人の相互作用行列
user_item_matrix = sparse.csr_matrix((
    interactions['score'],
    (interactions['user_id'], interactions['job_id'])
))

# モデル訓練
model = AlternatingLeastSquares(
    factors=50,
    regularization=0.01,
    iterations=15
)
model.fit(user_item_matrix)

# 推薦生成
recommendations = model.recommend(
    userid=user_id,
    user_items=user_item_matrix[user_id],
    N=40,
    filter_already_liked_items=True
)
```

### 検討された代替案
- TensorFlow Recommenders: 過剰な複雑性
- LightFM: ハイブリッド推薦には良いが必要以上
- Content-based only: パーソナライゼーション不足

## 4. バッチ処理スケジューリング

### 決定
- **採用**: APScheduler with PostgreSQL jobstore
- **実行時刻**: 毎日6:00 AM

### 根拠
- Supabaseと同じDBで状態管理
- 失敗時の自動リトライ機能
- 分散実行対応（将来の拡張性）

### 設定例
```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url=SUPABASE_URL)
}

scheduler = BlockingScheduler(
    jobstores=jobstores,
    job_defaults={
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 900
    }
)

scheduler.add_job(
    daily_matching_job,
    'cron',
    hour=6,
    minute=0,
    id='daily_matching',
    replace_existing=True
)
```

### 検討された代替案
- Cron: エラーハンドリングが貧弱
- Celery: 別途メッセージキューが必要
- AWS Lambda: ベンダーロックイン

## 5. Next.js SQL監視インターフェース

### 決定
- **採用**: Next.js 14 App Router + Supabase JS Client
- **UIライブラリ**: shadcn/ui + Tailwind CSS

### 根拠
- App Routerでサーバーコンポーネント活用
- Supabaseとのシームレスな統合
- リアルタイム更新対応

### アーキテクチャ
```typescript
// app/api/sql/route.ts
import { createClient } from '@supabase/supabase-js'

export async function POST(request: Request) {
  const { query } = await request.json()
  
  // 読み取り専用クエリのみ許可
  if (!query.toLowerCase().startsWith('select')) {
    return Response.json({ error: 'Only SELECT queries allowed' })
  }
  
  const { data, error } = await supabase
    .rpc('execute_readonly_query', { query_text: query })
  
  return Response.json({ data, error })
}
```

### 検討された代替案
- Retool: 高コスト、カスタマイズ性低い
- Metabase: 別途インフラが必要
- Custom React: Next.jsの方が機能豊富

## 6. パフォーマンス目標達成戦略

### 30分以内での処理完了

#### 並列処理設計
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# CPU数-1で並列実行
n_workers = max(1, multiprocessing.cpu_count() - 1)

with ProcessPoolExecutor(max_workers=n_workers) as executor:
    # ユーザーを分割して並列処理
    user_chunks = np.array_split(all_users, n_workers)
    futures = [
        executor.submit(process_user_batch, chunk)
        for chunk in user_chunks
    ]
```

#### 処理時間内訳（目標）
- データ読み込み: 2分
- スコアリング計算: 8分
- マッチング処理: 15分
- メール生成: 4分
- DB書き込み: 1分
- **合計: 30分**

### メモリ4GB制約

#### メモリ使用量計画
- Pandas DataFrame: 1.5GB
- スパース行列: 800MB
- 推薦モデル: 500MB
- 作業メモリ: 1.2GB
- **合計: 4GB**

## 7. エラーハンドリング＆監視

### 決定
- **ログ**: structlog for structured logging
- **監視**: Supabase built-in monitoring
- **アラート**: Email通知（エラー時）

### 実装方針
```python
import structlog

logger = structlog.get_logger()

def safe_batch_process():
    try:
        # 処理実行
        result = process_batch()
        logger.info("batch_success", 
                   processed=result['count'],
                   duration=result['time'])
    except Exception as e:
        logger.error("batch_failure",
                    error=str(e),
                    traceback=traceback.format_exc())
        # 3回リトライ
        retry_with_backoff()
```

## 8. データ整合性保証

### 決定
- **トランザクション**: Supabase transaction support
- **バックアップ**: 日次自動バックアップ
- **検証**: 処理前後のデータ数確認

### チェックポイント
1. CSV読み込み後: レコード数確認
2. スコアリング後: NULL値チェック
3. マッチング後: 各ユーザー40件確認
4. DB書き込み後: トランザクション成功確認

## まとめ

### 技術スタック確定
- **バックエンド**: Python 3.11 + Supabase
- **データ処理**: Pandas 2.x + PyArrow
- **推薦**: scikit-learn + implicit
- **スケジューラ**: APScheduler
- **フロントエンド**: Next.js 14 + Supabase JS
- **監視**: structlog + Supabase monitoring

### リスクと対策
1. **メモリ不足**: チャンク処理で対応
2. **処理時間超過**: 並列化で対応
3. **DB接続エラー**: 接続プール管理で対応
4. **データ不整合**: トランザクション使用

### 次のステップ
→ Phase 1: data-model.md、contracts/、quickstart.mdの作成