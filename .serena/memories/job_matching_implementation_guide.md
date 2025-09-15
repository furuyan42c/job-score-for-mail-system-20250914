# バイト求人マッチングシステム実装ガイド作成完了

## 更新内容（2025-09-15）
docs/for-specify-prompt.md を完全に書き換えて、実践的な実装ガイドに変更。

## 主な改善点
1. **コピペ実行可能**: 各プロンプトをそのままコピペして実行可能
2. **実装順序を明確化**: Phase 1〜7の順番で依存関係を解決
3. **Supabase + Python特化**: フロントエンドを除き、バックエンド実装に集中
4. **具体的な成果物定義**: 各プロンプトで生成されるファイル名を明記

## システム構成
- **データベース**: Supabase（PostgreSQL）
- **バックエンド**: Python + FastAPI  
- **バッチ処理**: Python scripts with APScheduler
- **規模**: 10万求人 × 1万ユーザー = 日次40万件配信

## 実装フェーズ
1. **Phase 1**: Supabaseテーブル作成とマスターデータ投入
2. **Phase 2**: 求人データ処理（インポート、スコアリング、分類）
3. **Phase 3**: ユーザーマッチング（プロファイル生成、日次マッチング）
4. **Phase 4**: メール配信（内容生成、SendGrid/SES配信）
5. **Phase 5**: 分析・フィードバック（トラッキング、レポート）
6. **Phase 6**: 運用・保守（スケジューラ、ヘルスチェック）
7. **Phase 7**: 本番環境構築（Docker、K8s、CI/CD）

## テーブル構成（ER図準拠）
- マスターテーブル: 8テーブル
- 求人テーブル: 4テーブル（jobs, jobs_match_raw, jobs_contents_raw, job_enrichment）
- ユーザーテーブル: 3テーブル（users, user_actions, user_profiles）
- 配信テーブル: 3テーブル（user_job_mapping, daily_job_picks, daily_email_queue）

## 特徴
- 各プロンプトに --think-hard フラグを適切に配置
- パフォーマンス要件を明記（処理時間、メモリ使用量）
- エラーハンドリングとリトライ処理を標準装備
- 実装チェックリストとトラブルシューティング付き