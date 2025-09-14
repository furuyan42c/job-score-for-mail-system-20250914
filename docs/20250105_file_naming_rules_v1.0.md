# ファイル命名規則

## 🎯 目的
- 最新版と過去版が一目で分かる
- 不要なファイル生成を防ぐ
- チーム全員が同じルールで作業

---

## 📝 基本ルール

### 1. 言語設定
- **英語**: コード関連、技術ドキュメント
- **日本語ローマ字は禁止**: NG例: `keiyakusho.md`

### 2. 文字規則
- **使用可能文字**: `a-z`, `0-9`, `-`, `_`, `.`
- **大文字禁止**: すべて小文字（`README.md`と`CLAUDE.md`は例外）
- **スペース禁止**: ハイフンかアンダースコアを使用

---

## 📅 バージョン管理ルール

### 日付付きファイル（仕様書・ER図）
```
[YYYYMMDD]_[内容]_[バージョン].[拡張子]

✅ 良い例：
- 20250904_er_diagram_v2.mmd
- 20250901_system_spec_v1.md
- 20250905_api_spec_draft.md

❌ 悪い例：
- er_new_modified.mmd （いつのか不明）
- spec_final_final.md （finalの連続）
- system_仕様書.md （日本語混在）
```

### バージョン番号付きファイル（継続更新するもの）
```
[内容]_v[メジャー].[マイナー].[拡張子]

✅ 良い例：
- system_specification_v2.0.md
- api_documentation_v1.3.md
- database_schema_v3.1.sql

❌ 悪い例：
- system_specification_v2.md （マイナー番号なし）
- api_v2_final.md （finalは使わない）
```

---

## 🗂️ カテゴリ別命名規則

| カテゴリ | 形式 | 例 |
|---------|------|-----|
| **仕様書** | `[日付]_[内容]_spec_v[番号].md` | `20250905_payment_spec_v1.0.md` |
| **ER図** | `[日付]_er_[内容].mmd` | `20250904_er_user_tables.mmd` |
| **API** | `api_[リソース]_v[番号].md` | `api_users_v2.0.md` |
| **設計書** | `design_[機能].md` | `design_authentication.md` |
| **議事録** | `[日付]_meeting_[内容].md` | `20250905_meeting_kickoff.md` |
| **テスト** | `test_[対象].[拡張子]` | `test_user_api.spec.ts` |

---

## 🚫 禁止事項

### 絶対に使わない名前
```
❌ untitled.md
❌ test.md
❌ temp.md
❌ new.md
❌ copy_of_[ファイル名]
❌ [ファイル名]_backup
❌ [ファイル名]_old
❌ [ファイル名]_最新
❌ final_final_[ファイル名]
```

### 自動生成ファイルの制限
```
# Claude Codeへの指示
- 新規ファイル作成前に必ず確認
- 一時ファイルは作らない
- テスト用ファイルは test/ ディレクトリに
- 下書きは draft_ プレフィックスを付ける
```

---

## 📁 アーカイブルール

### 古いファイルの扱い
```bash
# アーカイブディレクトリに移動
specs/archive/         # 古い仕様書
docs/archive/         # 古いドキュメント
backup/              # バックアップ全般

# ファイル名変更例
system_spec_v1.md → archive/20250901_system_spec_v1.md
```

### アーカイブ基準
- 新バージョンが作成されて旧版が不要になった
- プロジェクトで明確に使用しなくなった
- 空ファイルやドラフトで放置されている
- 重複する内容の新ファイルが作成された

---

## 🏷️ タグ・ステータス管理

### ファイル名に含めるステータス
```
_draft    # 下書き
_wip      # 作業中 (Work In Progress)
_review   # レビュー中
_approved # 承認済み
_deprecated # 非推奨

例：
- 20250905_api_spec_draft.md
- system_design_wip.md
- database_schema_approved.sql
```

---

## ✅ クイックリファレンス

### 新規作成時のチェックリスト
1. [ ] 日付が必要か？ → Yes: YYYYMMDD形式
2. [ ] バージョン管理が必要か？ → Yes: v1.0形式
3. [ ] 既存の似た名前のファイルはないか？
4. [ ] archive/に移動すべき古いファイルはないか？
5. [ ] ファイル名は内容を正確に表しているか？

### コマンド例
```bash
# 最新ファイルを探す
ls -la specs/*.md | grep -v archive | sort -r

# 古いファイルをアーカイブ
mv specs/old_spec.md specs/archive/20250901_old_spec.md

# 重複ファイルをチェック
find . -name "*.md" -exec basename {} \; | sort | uniq -d
```

---

## 🤖 Claude Code用ルール

```yaml
新規ファイル作成時:
  確認事項:
    - 既存ファイルの更新で対応できないか
    - ファイル名は命名規則に従っているか
    - 適切なディレクトリに配置されるか
  
  禁止事項:
    - untitled, temp, test などの名前
    - 日本語ファイル名
    - 連番だけのファイル名（file1.md, file2.md）
    
  推奨事項:
    - 更新の場合は既存ファイルを編集
    - 新規の場合は目的を明確にした名前
    - バージョンが必要な場合は v1.0 から開始
```

---

## 📋 実例

### 良いファイル構造
```
specs/
├── 20250905_system_specification_v2.0.md  # 最新
├── api_documentation_v1.3.md              # API仕様
├── business_requirements.md               # 固定文書
├── ER/
│   ├── 20250904_er_complete.mmd          # 最新ER図
│   └── archive/
│       └── 20250830_er_initial.mmd       # 過去版
└── archive/
    └── 20250901_system_specification_v1.0.md  # 旧版
```

### 悪いファイル構造
```
specs/
├── spec.md                  # 何の仕様か不明
├── spec_new.md             # newは意味がない
├── spec_new_modified.md    # 修正履歴が不明
├── spec_final.md           # finalは信用できない
├── システム仕様.md          # 日本語ファイル名
└── Copy of spec.md         # コピーは作らない
```

---

*最終更新: 2025-01-05*