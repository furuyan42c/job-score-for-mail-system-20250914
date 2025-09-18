# 🚀 バイト求人マッチングシステム 運用マニュアル

## 目次
1. [システム概要](#システム概要)
2. [環境構成](#環境構成)
3. [デプロイメント手順](#デプロイメント手順)
4. [運用手順](#運用手順)
5. [監視とアラート](#監視とアラート)
6. [トラブルシューティング](#トラブルシューティング)
7. [スケーリング](#スケーリング)
8. [バックアップとリカバリ](#バックアップとリカバリ)
9. [セキュリティ](#セキュリティ)
10. [メンテナンス](#メンテナンス)

---

## システム概要

### アーキテクチャ
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL │
│   (Next.js) │     │  (FastAPI)  │     │  (Supabase) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │   S3/CDN    │
                    │   (Cache)   │     │  (Storage)  │
                    └─────────────┘     └─────────────┘
```

### コンポーネント
- **Frontend**: Next.js 14 (App Router)
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL 15 / Supabase
- **Cache**: Redis 7
- **Queue**: Celery + Redis
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack
- **Error Tracking**: Sentry

---

## 環境構成

### 環境変数設定

#### 必須環境変数
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# Security
SECRET_KEY=your-secret-key-minimum-32-chars
JWT_SECRET_KEY=your-jwt-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@example.com

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 環境別設定

#### Development
```bash
cp .env.example .env
# Edit .env with development values
docker-compose up -d
```

#### Staging
```bash
cp .env.staging.example .env
# Edit .env with staging values
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

#### Production
```bash
cp .env.production.example .env
# Edit .env with production values
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## デプロイメント手順

### 初回デプロイ

#### 1. インフラ準備
```bash
# AWS リソースの作成
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Supabase プロジェクトの作成
supabase init
supabase start
```

#### 2. データベース初期化
```bash
# マイグレーション実行
cd backend
alembic upgrade head

# 初期データ投入
python scripts/seed_master_data.py
python scripts/generate_sample_data.py
```

#### 3. アプリケーションデプロイ
```bash
# Docker イメージビルド
docker build -t job-matching-backend:latest ./backend
docker build -t job-matching-frontend:latest ./frontend

# コンテナ起動
docker-compose up -d

# ヘルスチェック
curl http://localhost:8000/health
```

### 更新デプロイ

#### Blue-Green デプロイメント
```bash
# 新バージョンのビルド
docker build -t job-matching-backend:v2.0.0 ./backend
docker build -t job-matching-frontend:v2.0.0 ./frontend

# 新環境起動（Green）
docker-compose -p green up -d

# ヘルスチェック
./scripts/health_check.sh green

# トラフィック切り替え
./scripts/switch_traffic.sh green

# 旧環境停止（Blue）
docker-compose -p blue down
```

#### ローリングアップデート
```bash
# Kubernetes でのローリングアップデート
kubectl set image deployment/backend backend=job-matching-backend:v2.0.0
kubectl rollout status deployment/backend

kubectl set image deployment/frontend frontend=job-matching-frontend:v2.0.0
kubectl rollout status deployment/frontend
```

---

## 運用手順

### 日次運用

#### 1. システム状態確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# メトリクス確認
curl http://localhost:8000/metrics

# ログ確認
docker-compose logs --tail=100 -f backend
```

#### 2. バッチ処理実行
```bash
# 日次マッチング処理
curl -X POST http://localhost:8000/api/v1/batch/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"batch_type": "daily_matching"}'

# ステータス確認
curl http://localhost:8000/api/v1/batch/status/batch-id
```

#### 3. データバックアップ
```bash
# データベースバックアップ
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# S3へアップロード
aws s3 cp backup_$(date +%Y%m%d).sql s3://backup-bucket/
```

### 週次運用

#### 1. パフォーマンス分析
```sql
-- スロークエリ確認
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC;

-- インデックス使用状況
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

#### 2. セキュリティ監査
```bash
# 依存関係の脆弱性チェック
cd backend && safety check
cd frontend && npm audit

# アクセスログ分析
./scripts/analyze_access_logs.sh
```

### 月次運用

#### 1. キャパシティプランニング
```bash
# リソース使用状況レポート
./scripts/generate_capacity_report.sh

# 成長予測
python scripts/predict_growth.py
```

#### 2. ディザスタリカバリテスト
```bash
# バックアップからの復元テスト
./scripts/disaster_recovery_test.sh
```

---

## 監視とアラート

### メトリクス監視

#### Prometheus設定
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics

  - job_name: 'batch-processor'
    static_configs:
      - targets: ['batch-processor:8001']
```

#### 主要メトリクス
- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 100ms (p95)
- **Error Rate**: < 0.1%
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%
- **Disk Usage**: < 85%

### アラート設定

#### Critical アラート（即時対応）
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}%"

- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  annotations:
    summary: "Database is down"
```

#### Warning アラート（営業時間内対応）
```yaml
- alert: HighMemoryUsage
  expr: memory_usage_percent > 80
  for: 10m
  annotations:
    summary: "Memory usage is high"

- alert: SlowQueries
  expr: database_query_duration_seconds > 1
  for: 5m
```

### ログ管理

#### ログレベル
- **ERROR**: エラー発生（要調査）
- **WARNING**: 警告（監視継続）
- **INFO**: 通常動作
- **DEBUG**: デバッグ情報（開発環境のみ）

#### ログ分析クエリ
```json
// Kibana でのエラー検索
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

---

## トラブルシューティング

### よくある問題と対処法

#### 1. API レスポンスが遅い
```bash
# 原因調査
# 1. スロークエリの確認
docker exec -it postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 2. Redis接続確認
redis-cli ping

# 3. CPU/メモリ確認
docker stats

# 対処法
# - インデックス追加
# - クエリ最適化
# - キャッシュ戦略見直し
# - スケールアウト
```

#### 2. データベース接続エラー
```bash
# 接続プール状態確認
curl http://localhost:8000/system-info | jq .database.pool_stats

# 対処法
# - 接続プールサイズ調整
export DB_POOL_SIZE=30
export DB_MAX_OVERFLOW=50

# - データベース再起動
docker-compose restart postgres
```

#### 3. メモリリーク
```bash
# メモリ使用状況確認
docker exec backend ps aux --sort=-rss | head

# Python メモリプロファイリング
python -m memory_profiler app/main.py

# 対処法
# - アプリケーション再起動
docker-compose restart backend

# - メモリリーク箇所の特定と修正
```

#### 4. バッチ処理失敗
```bash
# ログ確認
docker logs batch-processor --tail=1000 | grep ERROR

# 手動リトライ
curl -X POST http://localhost:8000/api/v1/batch/retry/batch-id

# データ整合性チェック
python scripts/check_data_integrity.py
```

### 緊急対応手順

#### システム完全停止時
```bash
# 1. ステータス確認
docker-compose ps
systemctl status nginx

# 2. サービス再起動
docker-compose down
docker-compose up -d

# 3. ログ収集
./scripts/collect_emergency_logs.sh

# 4. インシデント報告
./scripts/create_incident_report.sh
```

#### データ破損時
```bash
# 1. 影響範囲確認
psql $DATABASE_URL -c "SELECT COUNT(*) FROM corrupted_table;"

# 2. バックアップから復元
pg_restore -d $DATABASE_URL backup_latest.sql

# 3. 差分データ適用
python scripts/apply_delta_data.py
```

---

## スケーリング

### 垂直スケーリング

#### リソース増強
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'  # 2.0 → 4.0
          memory: 4GB   # 2GB → 4GB
```

### 水平スケーリング

#### Backend スケールアウト
```bash
# Docker Swarm
docker service scale backend=5

# Kubernetes
kubectl scale deployment backend --replicas=5

# 負荷分散設定
upstream backend_servers {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    server backend4:8000;
    server backend5:8000;
}
```

#### Database レプリケーション
```sql
-- プライマリ設定
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_keep_segments = 64;

-- レプリカ追加
pg_basebackup -h primary -D /var/lib/postgresql/data -P -U replicator
```

### オートスケーリング

#### AWS Auto Scaling
```yaml
# terraform/autoscaling.tf
resource "aws_autoscaling_group" "backend" {
  min_size             = 2
  max_size             = 10
  desired_capacity     = 3

  target_group_arns    = [aws_lb_target_group.backend.arn]
  health_check_type    = "ELB"

  tag {
    key                 = "Name"
    value               = "backend-asg"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "backend_cpu" {
  name                   = "backend-cpu-policy"
  autoscaling_group_name = aws_autoscaling_group.backend.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

---

## バックアップとリカバリ

### バックアップ戦略

#### 自動バックアップ
```bash
# crontab -e
# 日次バックアップ（深夜2時）
0 2 * * * /scripts/daily_backup.sh

# 週次フルバックアップ（日曜深夜）
0 3 * * 0 /scripts/weekly_full_backup.sh

# 月次アーカイブ（月初）
0 4 1 * * /scripts/monthly_archive.sh
```

#### バックアップスクリプト
```bash
#!/bin/bash
# daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
S3_BUCKET="s3://backup-bucket"

# Database backup
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Redis backup
redis-cli --rdb $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3
aws s3 sync $BACKUP_DIR $S3_BUCKET/daily/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### リカバリ手順

#### Point-in-Time Recovery
```bash
# 1. WALアーカイブから特定時点まで復元
pg_basebackup -D /var/lib/postgresql/recovery -R

# 2. recovery.conf 設定
cat > /var/lib/postgresql/recovery/recovery.conf <<EOF
restore_command = 'cp /archive/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 3. PostgreSQL 起動
pg_ctl start -D /var/lib/postgresql/recovery
```

#### 災害復旧
```bash
# 1. 新環境構築
terraform apply -auto-approve

# 2. 最新バックアップ取得
aws s3 cp s3://backup-bucket/latest/db_backup.sql.gz .

# 3. データ復元
gunzip -c db_backup.sql.gz | psql $NEW_DATABASE_URL

# 4. アプリケーションデプロイ
kubectl apply -f k8s/

# 5. DNS切り替え
aws route53 change-resource-record-sets --hosted-zone-id Z123 --change-batch file://dns-failover.json
```

---

## セキュリティ

### セキュリティチェックリスト

#### アプリケーションセキュリティ
- [ ] HTTPS通信の強制
- [ ] SQLインジェクション対策
- [ ] XSS対策
- [ ] CSRF対策
- [ ] 認証・認可の実装
- [ ] レート制限
- [ ] 入力検証
- [ ] エラーメッセージの適切な処理

#### インフラセキュリティ
- [ ] ファイアウォール設定
- [ ] ネットワークセグメンテーション
- [ ] 最小権限の原則
- [ ] 定期的なパッチ適用
- [ ] ログ監視
- [ ] 侵入検知システム

### セキュリティ監査

#### 定期監査スクリプト
```bash
#!/bin/bash
# security_audit.sh

echo "=== Security Audit Report ===="
date

# 1. 依存関係の脆弱性チェック
echo "## Python Dependencies"
cd backend && safety check

echo "## Node Dependencies"
cd ../frontend && npm audit

# 2. オープンポートチェック
echo "## Open Ports"
nmap -p- localhost

# 3. SSL証明書チェック
echo "## SSL Certificate"
openssl s_client -connect example.com:443 -servername example.com < /dev/null

# 4. アクセスログ分析
echo "## Suspicious Access"
grep -E "(\.\./|SELECT|UNION|DROP)" /var/log/nginx/access.log | tail -20

# 5. 権限チェック
echo "## File Permissions"
find /app -type f -perm /o+w -ls
```

---

## メンテナンス

### 定期メンテナンス

#### 月次メンテナンス
```bash
# 1. システムアップデート
apt-get update && apt-get upgrade -y

# 2. Docker イメージ更新
docker-compose pull
docker-compose up -d

# 3. ログローテーション
logrotate -f /etc/logrotate.conf

# 4. 不要データクリーンアップ
python scripts/cleanup_old_data.py

# 5. インデックス再構築
psql $DATABASE_URL -c "REINDEX DATABASE job_matching;"
```

### バージョンアップグレード

#### マイナーバージョンアップ
```bash
# 1. 変更内容確認
git diff v1.2.0..v1.3.0

# 2. テスト環境で検証
docker-compose -f docker-compose.test.yml up
pytest tests/

# 3. 本番適用
./scripts/rolling_update.sh v1.3.0
```

#### メジャーバージョンアップ
```bash
# 1. 互換性チェック
python scripts/check_compatibility.py v2.0.0

# 2. データマイグレーション準備
alembic revision --autogenerate -m "v2.0.0 migration"

# 3. メンテナンスモード
./scripts/enable_maintenance_mode.sh

# 4. バックアップ
./scripts/full_backup.sh

# 5. アップグレード実行
./scripts/major_upgrade.sh v2.0.0

# 6. 動作確認
./scripts/smoke_test.sh

# 7. メンテナンスモード解除
./scripts/disable_maintenance_mode.sh
```

---

## 付録

### 便利なコマンド集

```bash
# ログ検索
docker-compose logs backend | grep ERROR

# リアルタイムメトリクス
watch -n 1 'curl -s localhost:8000/metrics | grep http_requests'

# データベース接続
docker exec -it postgres psql -U postgres -d job_matching

# Redis CLI
docker exec -it redis redis-cli

# バッチ実行状況
curl localhost:8000/api/v1/batch/status | jq

# ヘルスチェックループ
while true; do curl -s localhost:8000/health | jq .status; sleep 5; done
```

### 連絡先

#### エスカレーション
1. **L1 サポート**: support@example.com
2. **L2 エンジニア**: eng-team@example.com
3. **L3 アーキテクト**: architect@example.com
4. **緊急連絡**: +81-90-XXXX-XXXX

#### 外部ベンダー
- **AWS サポート**: https://console.aws.amazon.com/support
- **Supabase サポート**: support@supabase.com
- **Sentry**: https://sentry.io/support

---

最終更新: 2025-09-19
バージョン: 1.0.0