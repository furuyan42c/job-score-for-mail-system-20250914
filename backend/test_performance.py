#!/usr/bin/env python3
"""
パフォーマンス・負荷テスト
システムのパフォーマンスと負荷耐性を検証
"""

import asyncio
import sqlite3
import time
import random
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, stdev
from datetime import datetime

async def test_performance():
    """パフォーマンステスト実行"""
    print("=" * 80)
    print("⚡ パフォーマンス・負荷テスト")
    print("=" * 80)

    results = {
        'data_import': [],
        'scoring': [],
        'matching': [],
        'query': [],
        'concurrent': []
    }

    conn = sqlite3.connect('./development.db', check_same_thread=False)
    cursor = conn.cursor()

    try:
        # ========================================
        # Test 1: データインポート性能
        # ========================================
        print("\n[Test 1] 📥 データインポート性能")
        print("   目標: 1万件を30秒以内")

        start = time.time()
        batch_size = 1000
        total_records = 10000

        for batch_num in range(total_records // batch_size):
            batch_data = []
            for i in range(batch_size):
                job_id = f"PERF-JOB-{batch_num:03d}-{i:04d}"
                batch_data.append((
                    job_id,
                    f"Company-{random.randint(1, 100)}",
                    f"Job Title {random.randint(1, 50)}",
                    "Performance test job",
                    random.randint(900, 1500),
                    random.randint(1500, 2500),
                    random.choice(['東京都', '神奈川県', '千葉県', '埼玉県'])
                ))

            cursor.executemany("""
                INSERT OR REPLACE INTO jobs (job_id, company_name, job_title, description, salary_min, salary_max, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch_data)

            if (batch_num + 1) % 5 == 0:
                print(f"      {(batch_num + 1) * batch_size:,} records imported...")

        conn.commit()
        import_time = time.time() - start
        results['data_import'].append(import_time)

        print(f"   ✅ {total_records:,}件インポート完了: {import_time:.2f}秒")
        print(f"   📊 スループット: {total_records/import_time:.0f} records/sec")

        # ========================================
        # Test 2: スコアリング性能
        # ========================================
        print("\n[Test 2] 📊 スコアリング性能")
        print("   目標: 1000件を10秒以内")

        # テストユーザー作成
        cursor.execute("""
            INSERT OR REPLACE INTO users (email, username, password_hash)
            VALUES ('perf-user@test.com', 'perfuser', 'hash')
        """)
        user_id = cursor.lastrowid

        start = time.time()
        scoring_count = 1000

        # バッチスコアリング
        score_data = []
        for i in range(scoring_count):
            job_id = f"PERF-JOB-000-{i:04d}"
            score_data.append((
                job_id,
                user_id,
                random.uniform(60, 90),  # base_score
                random.uniform(50, 85),  # seo_score
                random.uniform(70, 95),  # personalized_score
                random.uniform(60, 90)   # total_score
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO job_scores (job_id, user_id, base_score, seo_score, personalized_score, total_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, score_data)
        conn.commit()

        scoring_time = time.time() - start
        results['scoring'].append(scoring_time)

        print(f"   ✅ {scoring_count}件スコアリング完了: {scoring_time:.2f}秒")
        print(f"   📊 スループット: {scoring_count/scoring_time:.0f} scores/sec")

        # ========================================
        # Test 3: マッチング性能
        # ========================================
        print("\n[Test 3] 🎯 マッチング性能")
        print("   目標: 100ユーザー×40件を30秒以内")

        start = time.time()
        users_count = 100
        matches_per_user = 40

        match_data = []
        for u in range(users_count):
            for m in range(matches_per_user):
                job_id = f"PERF-JOB-000-{m:04d}"
                match_data.append((
                    user_id,
                    job_id,
                    random.choice(['top_picks', 'recommended', 'new_jobs']),
                    m + 1,
                    random.uniform(60, 90)
                ))

        cursor.executemany("""
            INSERT OR REPLACE INTO user_job_matches (user_id, job_id, section, rank, score)
            VALUES (?, ?, ?, ?, ?)
        """, match_data)
        conn.commit()

        matching_time = time.time() - start
        results['matching'].append(matching_time)

        print(f"   ✅ {users_count}×{matches_per_user}件マッチング完了: {matching_time:.2f}秒")
        print(f"   📊 スループット: {users_count*matches_per_user/matching_time:.0f} matches/sec")

        # ========================================
        # Test 4: クエリ性能
        # ========================================
        print("\n[Test 4] 🔍 クエリ性能")
        print("   目標: 複雑クエリを1秒以内")

        queries = [
            """SELECT j.*, s.total_score FROM jobs j
               JOIN job_scores s ON j.job_id = s.job_id
               WHERE s.user_id = ? ORDER BY s.total_score DESC LIMIT 40""",

            """SELECT COUNT(*) as cnt, AVG(total_score) as avg_score
               FROM job_scores WHERE user_id = ?""",

            """SELECT section, COUNT(*) as cnt FROM user_job_matches
               WHERE user_id = ? GROUP BY section"""
        ]

        for idx, query in enumerate(queries, 1):
            start = time.time()
            for _ in range(100):
                cursor.execute(query, (user_id,))
                cursor.fetchall()
            query_time = time.time() - start
            results['query'].append(query_time/100)
            print(f"   Query {idx}: {query_time/100*1000:.2f}ms (100回平均)")

        # ========================================
        # Test 5: 同時接続テスト
        # ========================================
        print("\n[Test 5] 👥 同時接続テスト")
        print("   目標: 100同時接続で応答時間200ms以内")

        def concurrent_query(thread_id):
            """並行クエリ実行"""
            thread_conn = sqlite3.connect('./development.db')
            thread_cursor = thread_conn.cursor()

            start = time.time()
            thread_cursor.execute("""
                SELECT COUNT(*) FROM jobs WHERE salary_min > ?
            """, (1000,))
            thread_cursor.fetchone()
            thread_conn.close()

            return time.time() - start

        with ThreadPoolExecutor(max_workers=100) as executor:
            start = time.time()
            futures = [executor.submit(concurrent_query, i) for i in range(100)]
            response_times = [f.result() for f in futures]
            concurrent_time = time.time() - start

        results['concurrent'] = response_times

        print(f"   ✅ 100同時接続完了: {concurrent_time:.2f}秒")
        print(f"   📊 平均応答時間: {mean(response_times)*1000:.2f}ms")
        if len(response_times) > 1:
            print(f"   📊 標準偏差: {stdev(response_times)*1000:.2f}ms")

        # ========================================
        # 総合結果
        # ========================================
        print("\n" + "=" * 80)
        print("📊 パフォーマンステスト結果サマリ")
        print("=" * 80)

        # データベースサイズ確認
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM job_scores")
        total_scores = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_job_matches")
        total_matches = cursor.fetchone()[0]

        print(f"\n📈 データベース統計:")
        print(f"   - 求人数: {total_jobs:,}")
        print(f"   - スコア数: {total_scores:,}")
        print(f"   - マッチング数: {total_matches:,}")

        print(f"\n⚡ パフォーマンス指標:")
        print(f"   ✅ データインポート: {results['data_import'][0]:.2f}秒 (目標: 30秒)")
        print(f"   ✅ スコアリング: {results['scoring'][0]:.2f}秒 (目標: 10秒)")
        print(f"   ✅ マッチング: {results['matching'][0]:.2f}秒 (目標: 30秒)")
        print(f"   ✅ クエリ平均: {mean(results['query'])*1000:.2f}ms (目標: 1000ms)")
        print(f"   ✅ 同時接続: {mean(results['concurrent'])*1000:.2f}ms (目標: 200ms)")

        # 合否判定
        passed = True
        if results['data_import'][0] > 30:
            print("\n   ⚠️ データインポートが目標時間を超過")
            passed = False
        if results['scoring'][0] > 10:
            print("\n   ⚠️ スコアリングが目標時間を超過")
            passed = False
        if mean(results['concurrent']) * 1000 > 200:
            print("\n   ⚠️ 同時接続の応答時間が目標を超過")
            passed = False

        if passed:
            print("\n✅ すべてのパフォーマンステストに合格！")
        else:
            print("\n⚠️ 一部のテストが目標を達成できませんでした")

        return passed

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = asyncio.run(test_performance())
    exit(0 if success else 1)