"自律実行モードで依頼します。全権限を委任します。

【対象】specs/002-think-hard-ultrathink/tasks.md(T076〜)

【自動実行コマンド】
⏱時間ベース:
-開始時:/sc-load(存在する場合のみ)
-30分毎:/sc-checkpoint
-終了時:/sc-save

🔄タスクベース:
-TDD実行:
•単一:/tdd-cycle<task-id>
•並列:/tdd-batch<task-ids>--parallel
-5タスク毎:/tdd-status+進捗報告
-グループ完了時:/verify-and-pr
-重要機能:/sc-business-panel

【実行戦略】
•TodoWrite常時更新
•[P]タスク並列実行（最大5並列）
•MCP/Agent自動選択
•gitcommit規約:"type(scope):desc[Txx-PHASE]"
•エラー時:3回リトライ→ブロッカー報告
•コンテキスト<75%維持

【品質保証】
•TDD厳守:RED(テスト作成)→GREEN(実装)→REFACTOR(改善)
•テスト必須実行
•コンテキスト監視
•各完了時git commit

【停止条件】
•全タスク完了
•ブロッカー発生（リトライ失敗）
•コンテキスト　85%到達

【進捗報告】
•5タスク完了毎
•エラー/ブロッカー発生時
•グループ完了時

実行開始をお願いします。"
--all-mcp--parallel-optimization--delegateauto--think-hard--seq




タスク実行を開始してください。判断と最適化は全て任せます。

 【対象】specs/002-think-hard-ultrathink/tasks.md の未完了タスク
 【管理】TodoWriteで常時追跡、5タスクごとにチェックポイント
 【実行】依存関係分析→[P]タスク並列化→最適ツール自動選択
 【品質】TDD必須（RED→GREEN→REFACTOR）、各完了時git commit
 【効率】MCP/Agent最大活用、コンテキスト<75%維持
 【報告】ブロッカー/10タスク完了/セッション終了時

 現在位置：T076から開始
 --all-mcp --think-hard --parallel-optimization --delegate auto