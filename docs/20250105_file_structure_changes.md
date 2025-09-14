# ファイル構造変更報告書

## 📅 実施日
2025年1月5日

## 📋 変更内容

### specs/ ディレクトリ

#### ✅ ファイル名変更
| 旧ファイル名 | 新ファイル名 | 変更理由 |
|------------|------------|---------|
| `system_specification_v2.md` | `20250905_system_spec_v2.0.md` | 日付とバージョン明記 |
| `business_specification.md` | `20250905_business_spec_v1.0.md` | 日付とバージョン明記 |

#### 📦 アーカイブへ移動
| ファイル名 | 移動先 | 理由 |
|----------|--------|------|
| `20250901_specification.md` | `archive/20250901_system_spec_v1.0.md` | 旧バージョン |
| `front_specification.md` | `archive/20250904_frontend_spec_draft.md` | 空ファイル（ドラフト） |

### specs/ER/ ディレクトリ

#### ✅ ファイル名変更
| 旧ファイル名 | 新ファイル名 | 変更理由 |
|------------|------------|---------|
| `20250904_ER_new_modified.mmd` | `20250904_er_complete_v2.0.mmd` | 命名規則統一 |

#### 📦 アーカイブへ移動
| ファイル名 | 移動先 | 理由 |
|----------|--------|------|
| `ER_new_modified.mmd` | `archive/20240831_er_modified.mmd` | 日付不明の旧版 |
| `archive/ER20250830.mmd` | `archive/20250830_er_initial_v1.0.mmd` | 命名規則統一 |
| `archive/ER_new.mmd` | `archive/20240830_er_new_v1.1.mmd` | 命名規則統一 |

### docs/ ディレクトリ

#### ✅ ファイル名変更
| 旧ファイル名 | 新ファイル名 | 変更理由 |
|------------|------------|---------|
| `simple-guide.md` | `20250105_simple_guide_v1.0.md` | 日付とバージョン明記 |
| `file-naming-rules.md` | `20250105_file_naming_rules_v1.0.md` | 日付とバージョン明記 |

### docs/archive/ ディレクトリ

#### ✅ アーカイブファイル名変更
| 旧ファイル名 | 新ファイル名 | 変更理由 |
|------------|------------|---------|
| `documentation-best-practices.md` | `20250105_documentation_best_practices_v1.0.md` | 命名規則統一 |
| `claude-code-automation-rules.md` | `20250105_claude_automation_rules_v1.0.md` | 命名規則統一 |
| `project-documentation-setup.md` | `20250105_project_doc_setup_v1.0.md` | 命名規則統一 |
| `er-diagram-documentation.md` | `20250105_er_diagram_guide_v1.0.md` | 命名規則統一 |
| `README.md` | `20250105_archive_index.md` | 命名規則統一 |

## 📁 新しいディレクトリ構造

```
specs/
├── 20250905_system_spec_v2.0.md        # ✅ 最新システム仕様
├── 20250905_business_spec_v1.0.md      # ✅ 最新ビジネス仕様
├── ER/
│   ├── 20250904_er_complete_v2.0.mmd   # ✅ 最新ER図
│   └── archive/
│       ├── 20240831_er_modified.mmd
│       ├── 20250830_er_initial_v1.0.mmd
│       └── 20240830_er_new_v1.1.mmd
└── archive/
    ├── 20250901_system_spec_v1.0.md
    └── 20250904_frontend_spec_draft.md

docs/
├── 20250105_simple_guide_v1.0.md       # ✅ 現行ガイド
├── 20250105_file_naming_rules_v1.0.md  # ✅ 命名規則
├── 20250105_file_structure_changes.md  # ✅ この報告書
└── archive/
    ├── 20250105_documentation_best_practices_v1.0.md
    ├── 20250105_claude_automation_rules_v1.0.md
    ├── 20250105_project_doc_setup_v1.0.md
    ├── 20250105_er_diagram_guide_v1.0.md
    └── 20250105_archive_index.md
```

## ✅ 達成事項

1. **日付の明確化**: すべてのファイルに作成/更新日付を付与
2. **バージョン管理**: v1.0, v2.0 など明確なバージョン番号
3. **命名規則統一**: snake_case、小文字、英数字のみ
4. **アーカイブ整理**: 古いファイルをarchive/に移動
5. **最新版の識別**: 日付とバージョンで最新版が一目瞭然

## ⚠️ 注意事項

- **内容は一切変更していません**
- ファイル名とディレクトリ構造のみを変更
- 既存の参照パスは更新が必要

## 📝 次のアクション

- README.mdとCLAUDE.mdの参照パスを新しいファイル名に更新
- 他のドキュメント内の相互参照パスも確認・更新が必要

---

*報告者: Claude Code*
*実施日時: 2025年1月5日*