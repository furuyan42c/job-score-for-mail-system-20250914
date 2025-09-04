# Agent-Orchestrator 統合システム使用ガイド

## 🎯 **概要**

Agent-Orchestratorが自動的にAgent-Orchestrator-DirectorとExpert Consultationを要請できる統合システムの使用方法。

## 🏗️ **システム構成**

```
Agent-Orchestrator (Master)
├── 通常エージェント管理
│   ├── thorough-todo-executor
│   ├── supabase-specialist
│   ├── batch-performance-optimizer
│   └── data-quality-guardian
│
├── 戦略的エスカレーション
│   ├── agent-orchestrator-director (戦略・品質監視)
│   └── expert-consultation (専門知識)
│
└── 自動判定システム
    ├── エスカレーション条件判定
    ├── Task tool自動実行
    └── 統合意思決定
```

## ⚡ **自動エスカレーション条件**

### Agent-Orchestrator-Director へのエスカレーション

| 条件 | 閾値/条件 | 例 |
|------|-----------|-----|
| **品質スコア低下** | < 0.8 | テストカバレッジ65% |
| **KPI性能劣化** | `kpi_trend == 'declining'` | バッチ処理時間90分→120分 |
| **エージェント連携問題** | 3つ以上の競合 | Git競合+リソース競合+スケジュール競合 |
| **フェーズ完了評価** | `phase_completion == True` | Phase 2完了時の総合評価 |
| **マイルストーン危険** | `milestone_risk_level` HIGH/CRITICAL | 1時間目標90分超過リスク |

### Expert Consultation への要請

| 条件 | 判定基準 | 例 |
|------|----------|-----|
| **技術的複雑度** | HIGH/CRITICAL レベル | 分散処理アーキテクチャ設計 |
| **知識ギャップ** | 知識不足領域の特定 | 高度なPostgreSQL最適化 |
| **アーキテクチャ決定** | 重要な設計判断 | データパーティション戦略 |
| **性能最適化** | 専門的チューニング | Supabase Edge Functions最適化 |
| **セキュリティ問題** | HIGH/CRITICAL 脆弱性 | RLS policy設計 |

## 🚀 **実際の使用例**

### 例1: フェーズ2完了時の自動評価

```bash
# Agent-Orchestratorでの実行
/agent agent-orchestrator "Phase 2のタスクが完了しました。全体評価を実施してください。"
```

**内部動作:**
1. Agent-Orchestratorが品質スコア0.75を検出（< 0.8）
2. `should_escalate_to_director()` が `True` を返す
3. 自動的にAgent-Orchestrator-Directorを呼び出し
4. 戦略的評価レポートを取得
5. 改善推奨事項を統合した総合回答を提供

### 例2: 複雑なパフォーマンス問題

```bash
# Agent-Orchestratorでの実行
/agent agent-orchestrator "1時間バッチ処理目標が困難です。現在90分かかっており、最適化が必要です。"
```

**内部動作:**
1. Agent-Orchestratorが複雑性レベルHIGH、知識ギャップを検出
2. `should_request_expert_consultation()` が `True` を返す
3. 自動的にExpert Consultationを要請
4. 専門的な最適化戦略を取得
5. 実行可能な改善計画を提示

### 例3: 複合的問題（戦略+専門両方）

```bash
# Agent-Orchestratorでの実行
/agent agent-orchestrator "品質問題とパフォーマンス問題が同時発生しています。システム全体の見直しが必要です。"
```

**内部動作:**
1. 戦略的監視が必要 → Agent-Orchestrator-Director呼び出し
2. Directorが専門知識も必要と判断 → Expert Consultation推奨
3. 両方の分析を統合した包括的解決策を提示

## 📋 **実践的な使用シナリオ**

### Phase 1完了時
```bash
/agent agent-orchestrator "Phase 1の全タスクが完了しました。次のPhaseに進む前に包括的な評価をお願いします。"
```

### 性能問題発生時
```bash
/agent agent-orchestrator "バッチ処理が60分目標を大幅に超過しています。根本的な改善が必要です。"
```

### エージェント間競合時
```bash
/agent agent-orchestrator "複数のエージェントでリソース競合が発生しています。調整戦略を立ててください。"
```

### 技術的課題時
```bash
/agent agent-orchestrator "Supabaseの高度な最適化が必要ですが、現在の知識では限界があります。"
```

## 🔧 **システムの利点**

### 1. **自動判断**
- ユーザーが明示的にエスカレーションを指示する必要なし
- Agent-Orchestratorが状況を分析して適切な戦略エージェントを自動選択

### 2. **統合された回答**
- 複数のエージェントからの情報を統合
- 一貫性のある包括的な解決策を提供

### 3. **効率性**
- 単一のAgent-Orchestratorへの指示で複雑な分析が可能
- エージェント間の手動連携が不要

### 4. **品質保証**
- 自動的な品質チェックとKPI監視
- 問題の早期発見と対応

## 💡 **ベストプラクティス**

### 1. **明確な状況説明**
Agent-Orchestratorに現在の状況を詳しく説明することで、より適切な判断が可能。

### 2. **定期的な評価**
フェーズ完了時やマイルストーン時に定期的な評価を実施。

### 3. **早期エスカレーション**
問題が複雑化する前に Agent-Orchestrator に相談。

### 4. **統合アプローチ**
個別エージェントよりもAgent-Orchestratorを通した統合アプローチを優先。

この統合システムにより、プロジェクト管理の効率性と品質が大幅に向上します。
