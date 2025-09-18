#!/bin/bash

# 10万件求人データ生成実行スクリプト
# Usage: ./run_data_generation.sh [environment]
# Environment: dev (default), staging, production

set -e  # エラー時に停止

# =============================================================================
# 設定
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BACKEND_DIR/logs"
VENV_PATH="$BACKEND_DIR/venv"

# 環境設定
ENVIRONMENT="${1:-dev}"
TOTAL_RECORDS="${2:-100000}"

# ログファイル設定
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/data_generation_${ENVIRONMENT}_${TIMESTAMP}.log"

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# 関数定義
# =============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "🚀 求人データ生成システム v1.0"
    echo "============================================================================"
    echo -e "${NC}"
    echo "環境: $ENVIRONMENT"
    echo "生成レコード数: $(printf "%'d" $TOTAL_RECORDS)件"
    echo "開始時刻: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "ログファイル: $LOG_FILE"
    echo ""
}

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    print_step "前提条件チェック中..."

    # Python仮想環境チェック
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Python仮想環境が見つかりません: $VENV_PATH"
        echo "以下のコマンドで仮想環境を作成してください:"
        echo "python3 -m venv $VENV_PATH"
        echo "source $VENV_PATH/bin/activate"
        echo "pip install -r requirements.txt"
        exit 1
    fi

    # ログディレクトリ作成
    mkdir -p "$LOG_DIR"

    # データベース接続テスト
    print_step "データベース接続テスト..."
    if ! python3 -c "import psycopg2; psycopg2.connect(host='${DB_HOST:-localhost}', port=${DB_PORT:-5432}, database='${DB_NAME:-mail_score_dev}', user='${DB_USER:-postgres}', password='${DB_PASSWORD:-password}').close()" 2>/dev/null; then
        print_error "データベース接続失敗"
        echo "環境変数を確認してください:"
        echo "DB_HOST=${DB_HOST:-localhost}"
        echo "DB_PORT=${DB_PORT:-5432}"
        echo "DB_NAME=${DB_NAME:-mail_score_dev}"
        echo "DB_USER=${DB_USER:-postgres}"
        exit 1
    fi

    print_success "前提条件チェック完了"
}

load_environment() {
    print_step "環境設定読み込み中..."

    # 環境ファイル読み込み
    ENV_FILE="$BACKEND_DIR/.env.$ENVIRONMENT"
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
        print_success "環境設定読み込み完了: $ENV_FILE"
    else
        print_warning "環境設定ファイルが見つかりません: $ENV_FILE"
        print_warning "デフォルト設定を使用します"
    fi

    # 必要な環境変数設定
    export DB_HOST="${DB_HOST:-localhost}"
    export DB_PORT="${DB_PORT:-5432}"
    export DB_NAME="${DB_NAME:-mail_score_dev}"
    export DB_USER="${DB_USER:-postgres}"
    export DB_PASSWORD="${DB_PASSWORD:-password}"
}

backup_existing_data() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_step "本番環境データバックアップ中..."

        BACKUP_FILE="$LOG_DIR/jobs_backup_${TIMESTAMP}.sql"
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                -t jobs --data-only --no-owner --no-privileges \
                > "$BACKUP_FILE" 2>/dev/null || true

        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            print_success "バックアップ完了: $BACKUP_FILE"
        else
            print_warning "バックアップファイルが作成されませんでした"
        fi
    fi
}

setup_master_data() {
    print_step "マスターデータセットアップ中..."

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    python3 scripts/setup_master_data.py 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "マスターデータセットアップ完了"
    else
        print_error "マスターデータセットアップ失敗"
        exit 1
    fi
}

generate_job_data() {
    print_step "$TOTAL_RECORDS件の求人データ生成開始..."

    START_TIME=$(date +%s)

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    # データ生成実行
    python3 scripts/generate_job_data.py 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        RATE=$((TOTAL_RECORDS / DURATION))

        print_success "求人データ生成完了"
        echo "実行時間: ${DURATION}秒"
        echo "生成速度: ${RATE} records/sec"

        # 目標達成チェック（5分 = 300秒）
        if [ $DURATION -le 300 ]; then
            print_success "パフォーマンス目標達成！（5分以内）"
        else
            print_warning "パフォーマンス目標未達成（5分超過）"
        fi
    else
        print_error "求人データ生成失敗"
        exit 1
    fi
}

verify_data_quality() {
    print_step "データ品質検証中..."

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    # 品質検証SQLクエリ実行
    python3 -c "
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

with conn.cursor() as cur:
    # 総レコード数
    cur.execute('SELECT COUNT(*) FROM jobs WHERE is_active = true')
    total_count = cur.fetchone()[0]
    print(f'総レコード数: {total_count:,}件')

    # fee制約違反チェック
    cur.execute('SELECT COUNT(*) FROM jobs WHERE fee <= 500 OR fee > 5000')
    fee_violations = cur.fetchone()[0]
    print(f'fee制約違反: {fee_violations}件')

    # NULL値チェック
    cur.execute('SELECT COUNT(*) FROM jobs WHERE endcl_cd IS NULL OR company_name IS NULL')
    null_violations = cur.fetchone()[0]
    print(f'必須項目NULL: {null_violations}件')

    # 地域分布確認
    cur.execute('SELECT pref_cd, COUNT(*) FROM jobs GROUP BY pref_cd ORDER BY COUNT(*) DESC LIMIT 5')
    print('地域分布（TOP5):')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]:,}件')

conn.close()
" 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "データ品質検証完了"
    else
        print_error "データ品質検証失敗"
        exit 1
    fi
}

run_performance_benchmark() {
    if [ "$3" = "--benchmark" ]; then
        print_step "パフォーマンスベンチマーク実行中..."

        cd "$BACKEND_DIR"
        source "$VENV_PATH/bin/activate"

        python3 scripts/benchmark_data_generation.py 2>&1 | tee -a "$LOG_FILE"

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "ベンチマーク完了"
            echo "結果: /tmp/benchmark_results/"
        else
            print_warning "ベンチマーク実行でエラーが発生しました"
        fi
    fi
}

cleanup_and_optimize() {
    print_step "最適化とクリーンアップ中..."

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    python3 -c "
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

with conn.cursor() as cur:
    # 統計情報更新
    print('統計情報更新中...')
    cur.execute('ANALYZE jobs')

    # インデックス再構築（必要に応じて）
    print('インデックス最適化中...')
    cur.execute('REINDEX INDEX CONCURRENTLY idx_jobs_active_date')

    conn.commit()

conn.close()
print('最適化完了')
" 2>&1 | tee -a "$LOG_FILE"

    print_success "最適化とクリーンアップ完了"
}

print_final_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "============================================================================"
    echo "🎉 求人データ生成完了！"
    echo "============================================================================"
    echo -e "${NC}"
    echo "環境: $ENVIRONMENT"
    echo "生成レコード数: $(printf "%'d" $TOTAL_RECORDS)件"
    echo "完了時刻: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "ログファイル: $LOG_FILE"
    echo ""
    echo "次のステップ:"
    echo "1. データ品質の最終確認"
    echo "2. アプリケーションでの動作テスト"
    echo "3. パフォーマンステストの実行"
    echo ""
}

# =============================================================================
# メイン実行
# =============================================================================

main() {
    # ヘッダー表示
    print_header

    # 実行確認（本番環境のみ）
    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${YELLOW}⚠️  本番環境でのデータ生成を実行しようとしています。${NC}"
        echo -e "${YELLOW}   既存のjobsテーブルのデータが削除される可能性があります。${NC}"
        read -p "続行しますか？ (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_error "実行を中止しました"
            exit 1
        fi
    fi

    # 実行ステップ
    check_prerequisites
    load_environment
    backup_existing_data
    setup_master_data
    generate_job_data
    verify_data_quality
    run_performance_benchmark "$@"
    cleanup_and_optimize
    print_final_summary
}

# スクリプト実行
main "$@"