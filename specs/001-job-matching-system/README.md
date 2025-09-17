# 📚 Job Matching System 実装ガイド

**最終更新**: 2025-09-17

## 🎯 使用すべきファイル

### ✅ 推奨（最新版）
**`ULTIMATE-IMPLEMENTATION-GUIDE.md`** - 統合版完全実装ガイド v4.0
- Spec-Kitコマンド完備（/specify, /plan, /tasks）
- エージェント並列実行対応
- 3つの実装オプション（フル/MVP/緊急）
- GPT-5 nano対応確認済み
- 手動作業明確化

### 📁 その他のファイル（参考用）

| ファイル名 | 用途 | ステータス |
|-----------|------|-----------|
| `PRACTICAL-IMPLEMENTATION-GUIDE.md` | 段階的実装の詳細手順 | 参考用 |
| `command-reference-guide.md` | コマンドリファレンス | 現役 |
| `implementation-workflow-prompt.md` | 詳細なワークフロー | 参考用 |
| `VALIDATION-REPORT.md` | 実装可能性検証レポート | 現役 |
| `EXECUTE-NOW-PROMPT.md` | 旧実行プロンプト | **非推奨** |
| `OPTIMIZED-EXECUTION-PROMPT.md` | 旧最適化版 | **非推奨** |

---

## 🚀 クイックスタート

### Step 1: 手動準備（1時間）
```bash
# Supabaseプロジェクト作成
# API KEY取得
# 環境変数設定
```

### Step 2: 実装開始
```markdown
# ULTIMATE-IMPLEMENTATION-GUIDE.mdを開く
# 実装オプションを選択：
- Option A: フル実装（4日間）← 推奨
- Option B: MVP（8時間）
- Option C: 緊急（2時間）

# 選択したオプションのプロンプトをコピー
# Claude Codeで実行
```

---

## 📊 実装オプション比較

| オプション | 時間 | 機能範囲 | 品質 | 推奨対象 |
|-----------|------|----------|------|----------|
| **A: フル実装** | 28-36時間<br>(4日分割) | 全機能実装<br>10万件×1万人 | 高品質<br>テスト完備 | 本番環境向け |
| **B: MVP** | 8時間 | 基本機能<br>1000件×100人 | 中品質<br>基本テスト | プロトタイプ |
| **C: 緊急** | 2時間 | SQL実行画面のみ | 最小限 | デモ・検証用 |

---

## 🔧 技術スタック

### 確認済み
- **Backend**: Python 3.11 + FastAPI + Supabase
- **Frontend**: Next.js 14 + TypeScript 5
- **AI**: GPT-5 nano（2025年8月リリース済み）
- **Database**: Supabase（PostgreSQL）
- **Batch**: APScheduler

### MCP活用
- **Sequential**: 複雑な分析
- **Serena**: コード操作
- **Magic**: UI生成
- **Context7**: ドキュメント参照
- **Playwright**: E2Eテスト

---

## 💡 成功のポイント

1. **必ず手動準備を完了**してから開始
2. **Phase単位で実行**（一度に全部は実行しない）
3. **Task toolでエージェント並列実行**を活用
4. **30分ごとに/sc:checkpoint**で進捗保存
5. **エラー時はroot-cause-analyst**で原因分析

---

## 📝 仕様書

### コア仕様
- `comprehensive_integrated_specification_final_v5.0.md` - 統合仕様書
- `data-model.md` - データモデル定義（14テーブル）
- `answers.md` - 実装詳細Q&A

### データモデル
- ERD: `20250904_er_complete_v2.0.mmd`
- テーブル数: 14
- 主要エンティティ: jobs, users, scoring, email

---

## 🆘 サポート

### よくある質問
- **Q: どのファイルから始めるべき？**
  - A: `ULTIMATE-IMPLEMENTATION-GUIDE.md`を使用

- **Q: Supabase設定は自動化できる？**
  - A: できません。手動で約30分必要

- **Q: 一度に全部実装できる？**
  - A: 推奨しません。Phase単位で分割実行

### トラブルシューティング
問題が発生したら：
1. `VALIDATION-REPORT.md`で既知の問題確認
2. `command-reference-guide.md`でコマンド確認
3. エラー分析用エージェント活用

---

*Job Matching System実装の全ての情報はこのディレクトリに集約されています*