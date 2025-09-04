# Agent Communication Protocol v1.0

## エージェント間通信プロトコル仕様

このドキュメントは、すべてのエージェントが従うべき通信プロトコルと、エージェント間でのデータ共有・連携方法を定義します。

## 1. 共通ディレクトリ構造

```
/Users/furuyanaoki/Project/claude-code-mailsocre-app/
├── .claude/
│   ├── agents/               # エージェント定義
│   │   ├── shared/          # 共有リソース
│   │   └── *.md             # 各エージェント定義
│   └── agent-state/         # エージェント状態管理
│       ├── current-session.json
│       ├── task-queue.json
│       └── agent-results/
├── logs/                    # ログディレクトリ
│   ├── execution/
│   ├── errors/
│   ├── performance/
│   └── summary/
└── agent-workspace/         # エージェント作業領域
    ├── inbox/              # エージェント間メッセージ
    ├── shared-data/        # 共有データ
    └── checkpoints/        # チェックポイント
```

## 2. メッセージフォーマット

### 基本メッセージ構造
```json
{
  "message_id": "MSG-2025-08-25-001",
  "timestamp": "2025-08-25T10:30:45.123Z",
  "from_agent": "agent-orchestrator",
  "to_agent": "thorough-todo-executor",
  "message_type": "TASK_ASSIGN|RESULT|STATUS|ERROR|QUERY",
  "priority": "CRITICAL|HIGH|NORMAL|LOW",
  "correlation_id": "SESSION-2025-08-25-001",
  "payload": {
    // メッセージ固有のデータ
  },
  "metadata": {
    "retry_count": 0,
    "timeout_ms": 60000,  // Increased from 30s to 60s for complex tasks
    "requires_ack": true
  }
}
```

### メッセージタイプ定義

#### TASK_ASSIGN（タスク割り当て）
```json
{
  "message_type": "TASK_ASSIGN",
  "payload": {
    "task_id": "TASK-3.1",
    "task_name": "User Behavior Analysis",
    "task_description": "Implement user profiling system",
    "dependencies": ["TASK-1.9"],
    "estimated_duration_min": 20,  // Optimized estimation
    "required_capabilities": ["database", "analytics"],
    "input_data": {
      "source_tables": ["user_behaviors"],
      "target_output": "/agent-workspace/shared-data/user-profiles.json"
    },
    "success_criteria": {
      "tests_pass": true,
      "performance_target_ms": 1000
    }
  }
}
```

#### RESULT（実行結果）
```json
{
  "message_type": "RESULT",
  "payload": {
    "task_id": "TASK-3.1",
    "status": "SUCCESS|FAILURE|PARTIAL",
    "execution_time_ms": 25430,
    "output_location": "/agent-workspace/shared-data/task-3.1-output.json",
    "metrics": {
      "records_processed": 10000,
      "success_rate": 0.98,
      "memory_usage_mb": 512
    },
    "errors": [],
    "warnings": ["Performance target missed by 200ms"],
    "next_recommended_action": "Proceed to TASK-3.2"
  }
}
```

#### STATUS（状態更新）
```json
{
  "message_type": "STATUS",
  "payload": {
    "agent_status": "IDLE|BUSY|ERROR|OFFLINE",
    "current_task": "TASK-3.1",
    "progress_percent": 65,
    "remaining_time_estimate_min": 10,
    "resource_usage": {
      "cpu_percent": 45,
      "memory_mb": 1024,
      "active_connections": 5
    }
  }
}
```

#### ERROR（エラー通知）
```json
{
  "message_type": "ERROR",
  "payload": {
    "error_code": "DB_CONNECTION_FAILED",
    "error_level": "CRITICAL|MAJOR|MINOR|WARNING",
    "error_message": "Failed to connect to Supabase",
    "stack_trace": "...",
    "context": {
      "task_id": "TASK-3.1",
      "retry_attempts": 3
    },
    "recovery_action": "RETRY|SKIP|ROLLBACK|ESCALATE"
  }
}
```

## 3. エージェント登録システム

### エージェント登録情報
```json
{
  "agent_id": "supabase-specialist",
  "agent_type": "SPECIALIST",
  "capabilities": ["database", "optimization", "migration"],
  "status": "ACTIVE",
  "endpoint": "/agent-workspace/inbox/supabase-specialist/",
  "health_check_url": "/health",
  "max_concurrent_tasks": 3,
  "supported_message_types": ["TASK_ASSIGN", "QUERY"],
  "dependencies": [],
  "version": "1.0.0"
}
```

## 4. 状態管理プロトコル

### セッション状態
```json
{
  "session_id": "SESSION-2025-08-25-001",
  "started_at": "2025-08-25T10:00:00Z",
  "orchestrator_pid": "agent-orchestrator",
  "active_agents": [
    {
      "agent_id": "thorough-todo-executor",
      "status": "BUSY",
      "current_task": "TASK-3.1"
    }
  ],
  "task_queue": ["TASK-3.2", "TASK-3.3"],
  "completed_tasks": ["TASK-1.1", "TASK-1.2"],
  "global_metrics": {
    "total_tasks": 54,
    "completed": 31,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

## 5. データ共有プロトコル

### 共有データ構造
```
/agent-workspace/shared-data/
├── task-outputs/           # タスク出力
│   ├── TASK-3.1/
│   │   ├── output.json
│   │   └── metadata.json
├── datasets/              # 共有データセット
│   ├── user-profiles.json
│   ├── job-scores.json
│   └── category-mappings.json
├── configs/               # 共有設定
│   ├── database-config.json
│   └── performance-targets.json
└── artifacts/            # 成果物
    ├── reports/
    └── exports/
```

### データアクセスルール
1. **書き込み**: 担当エージェントのみ
2. **読み取り**: すべてのエージェント
3. **ロック機構**: ファイルベースロック使用
4. **バージョニング**: タイムスタンプベース

## 6. エラーハンドリング

### エラーエスカレーション
```
Level 1: エージェント内でリトライ（3回まで）
Level 2: Orchestratorに通知、代替エージェント検討
Level 3: タスクスキップ、次タスクへ
Level 4: セッション停止、人間介入要請
```

### リカバリープロトコル
```json
{
  "recovery_strategy": {
    "RETRY": {
      "max_attempts": 3,
      "backoff_ms": [1000, 2000, 4000]
    },
    "FALLBACK": {
      "alternative_agent": "backup-executor"
    },
    "CHECKPOINT": {
      "restore_from": "/agent-workspace/checkpoints/latest"
    },
    "SKIP": {
      "log_reason": true,
      "continue_next": true
    }
  }
}
```

## 7. パフォーマンスモニタリング

### メトリクス収集
```json
{
  "metric_type": "TASK_PERFORMANCE",
  "agent_id": "thorough-todo-executor",
  "task_id": "TASK-3.1",
  "metrics": {
    "start_time": "2025-08-25T10:00:00Z",
    "end_time": "2025-08-25T10:30:00Z",
    "duration_ms": 1800000,
    "cpu_avg_percent": 45,
    "memory_peak_mb": 2048,
    "io_operations": 15000,
    "database_queries": 250,
    "api_calls": 10,
    "cache_hit_rate": 0.85
  }
}
```

## 8. セキュリティ

### 認証・認可
- エージェント間通信は内部のみ
- 外部API呼び出しは環境変数で管理
- センシティブデータは暗号化

### 監査ログ
```json
{
  "audit_event": "TASK_EXECUTION",
  "timestamp": "2025-08-25T10:30:00Z",
  "agent_id": "supabase-specialist",
  "action": "DATABASE_MIGRATION",
  "target": "user_behaviors",
  "result": "SUCCESS",
  "changes": ["Added index on user_id"]
}
```

## 9. 同期・非同期通信

### 同期通信（即座の応答が必要）
- health check
- capability query
- critical error notification

### 非同期通信（キューベース）
- task assignment
- result notification
- status updates

## 10. プロトコルバージョニング

現在のバージョン: 1.0.0

### 互換性ルール
- Major: 後方互換性なし
- Minor: 後方互換性あり、新機能追加
- Patch: バグ修正のみ

## 使用例

### Orchestratorからの Task割り当て
```bash
echo '{
  "message_id": "MSG-001",
  "from_agent": "agent-orchestrator",
  "to_agent": "thorough-todo-executor",
  "message_type": "TASK_ASSIGN",
  "payload": {
    "task_id": "TASK-3.1",
    "task_name": "Implement user profiling"
  }
}' > /agent-workspace/inbox/thorough-todo-executor/MSG-001.json
```

### エージェントからの結果報告
```bash
echo '{
  "message_id": "MSG-002",
  "from_agent": "thorough-todo-executor",
  "to_agent": "agent-orchestrator",
  "message_type": "RESULT",
  "payload": {
    "task_id": "TASK-3.1",
    "status": "SUCCESS"
  }
}' > /agent-workspace/inbox/agent-orchestrator/MSG-002.json
```
