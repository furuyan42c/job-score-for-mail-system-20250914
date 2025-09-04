# BaseAgentLogger - 全エージェント共通ログ基盤クラス

**クラスタイプ**: `shared-component`
**主要責務**: 全エージェント統一ログシステム・構造化ログ・パフォーマンス監視
**作成日時**: 2025-08-25
**バージョン**: 1.0.0

## 📋 **基盤クラス概要**

BaseAgentLoggerは、全エージェントが継承する統一ログ基盤クラスです。構造化ログ・パフォーマンス監視・エラートラッキング・ログローテーション機能を提供し、システム全体の一貫したログ管理を実現します。

### **コア機能**
- **統一ログディレクトリ管理**: エージェント別の標準化されたログ構造
- **構造化ログ出力**: JSON形式での一貫した分析可能ログ
- **パフォーマンス監視**: 実行時間・リソース使用量の自動追跡
- **エラー分類・追跡**: 重要度別エラー管理・スタックトレース保存
- **ログローテーション**: 自動ファイル管理・容量制御
- **統合監視支援**: 全エージェントログの統合分析機能

## 🔧 **BaseAgentLogger実装**

### **基盤クラス定義**
```python
import os
import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import threading
from pathlib import Path

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class LogEntry:
    """構造化ログエントリー標準フォーマット"""
    timestamp: str
    agent_name: str
    log_level: str
    event_type: str
    category: str
    message: str
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None
    execution_context: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス標準フォーマット"""
    timestamp: str
    agent_name: str
    metric_name: str
    metric_value: float
    measurement_unit: str
    context: Dict[str, Any]
    execution_id: Optional[str] = None

@dataclass
class ErrorReport:
    """エラーレポート標準フォーマット"""
    timestamp: str
    agent_name: str
    error_type: str
    error_message: str
    severity: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_action: Optional[str] = None
    error_id: Optional[str] = None

class BaseAgentLogger:
    """全エージェント共通ログ基盤クラス"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.log_base_path = "/Users/furuyanaoki/Project/claude-code-mailsocre-app/logs"
        self.session_id = self.generate_session_id()
        self.correlation_id = None
        self.lock = threading.Lock()

        # ログ設定
        self.max_log_file_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 30  # 30日分
        self.flush_interval = 5  # 5秒

        self.setup_agent_log_directories()
        self.initialize_log_rotation()

    def setup_agent_log_directories(self):
        """エージェント専用ログディレクトリの設定"""

        # 標準ディレクトリ構造
        standard_dirs = [
            f"{self.log_base_path}/{self.agent_name}/",
            f"{self.log_base_path}/{self.agent_name}/execution/",
            f"{self.log_base_path}/{self.agent_name}/errors/",
            f"{self.log_base_path}/{self.agent_name}/performance/",
            f"{self.log_base_path}/{self.agent_name}/summary/",
            f"{self.log_base_path}/{self.agent_name}/debug/"
        ]

        # エージェント特化ディレクトリ
        agent_specific_dirs = self.get_agent_specific_directories()
        all_dirs = standard_dirs + agent_specific_dirs

        for log_dir in all_dirs:
            Path(log_dir).mkdir(parents=True, exist_ok=True)

    def get_agent_specific_directories(self) -> List[str]:
        """エージェント特化ディレクトリの定義（サブクラスで実装）"""
        return []

    def generate_session_id(self) -> str:
        """セッションID生成"""
        return f"{self.agent_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"

    def set_correlation_id(self, correlation_id: str):
        """相関ID設定（エージェント間連携追跡用）"""
        self.correlation_id = correlation_id

    def log_structured_event(self, log_level: LogLevel, category: str, event_type: str,
                           message: str, event_data: Dict[str, Any] = None,
                           execution_context: Dict[str, Any] = None):
        """構造化イベントログ（全エージェント共通）"""

        if event_data is None:
            event_data = {}

        log_entry = LogEntry(
            timestamp=datetime.datetime.now().isoformat(),
            agent_name=self.agent_name,
            log_level=log_level.value,
            event_type=event_type,
            category=category,
            message=message,
            event_data=event_data,
            metadata={
                "log_version": "1.0",
                "session_id": self.session_id,
                "environment": os.getenv("ENVIRONMENT", "development"),
                "process_id": os.getpid()
            },
            correlation_id=self.correlation_id,
            execution_context=execution_context
        )

        self._write_structured_log(category, log_entry)

        # コンソール出力（DEBUGレベル以外）
        if log_level != LogLevel.DEBUG:
            self._write_console_log(log_entry)

    def log_performance_metric(self, metric_name: str, metric_value: float,
                              context: Dict[str, Any] = None, execution_id: str = None):
        """パフォーマンスメトリクスログ（全エージェント共通）"""

        if context is None:
            context = {}

        performance_metric = PerformanceMetric(
            timestamp=datetime.datetime.now().isoformat(),
            agent_name=self.agent_name,
            metric_name=metric_name,
            metric_value=metric_value,
            measurement_unit=self.get_metric_unit(metric_name),
            context=context,
            execution_id=execution_id or self.session_id
        )

        self._write_performance_log(performance_metric)

    def log_error_with_context(self, error_type: str, error_message: str,
                              context: Dict[str, Any] = None, stack_trace: str = None,
                              recovery_action: str = None):
        """コンテキスト付きエラーログ（全エージェント共通）"""

        if context is None:
            context = {}

        if stack_trace is None:
            stack_trace = traceback.format_exc()

        error_severity = self.determine_error_severity(error_type)

        error_report = ErrorReport(
            timestamp=datetime.datetime.now().isoformat(),
            agent_name=self.agent_name,
            error_type=error_type,
            error_message=error_message,
            severity=error_severity.name,
            context=context,
            stack_trace=stack_trace,
            recovery_action=recovery_action,
            error_id=self.generate_error_id()
        )

        self._write_error_log(error_report)

        # 重要なエラーは即座にアラート
        if error_severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._trigger_error_alert(error_report)

    def log_execution_start(self, operation_name: str, parameters: Dict[str, Any] = None):
        """操作開始ログ"""

        execution_context = {
            "operation_name": operation_name,
            "parameters": parameters or {},
            "start_time": datetime.datetime.now().isoformat(),
            "execution_id": self.generate_execution_id()
        }

        self.log_structured_event(
            LogLevel.INFO,
            "execution",
            "OPERATION_START",
            f"Starting operation: {operation_name}",
            event_data=execution_context,
            execution_context=execution_context
        )

        return execution_context["execution_id"]

    def log_execution_end(self, execution_id: str, operation_name: str,
                         success: bool, result: Dict[str, Any] = None,
                         execution_time_seconds: float = None):
        """操作終了ログ"""

        execution_context = {
            "operation_name": operation_name,
            "execution_id": execution_id,
            "success": success,
            "result": result or {},
            "end_time": datetime.datetime.now().isoformat(),
            "execution_time_seconds": execution_time_seconds
        }

        log_level = LogLevel.INFO if success else LogLevel.ERROR
        event_type = "OPERATION_SUCCESS" if success else "OPERATION_FAILURE"

        self.log_structured_event(
            log_level,
            "execution",
            event_type,
            f"Operation {operation_name} {'completed successfully' if success else 'failed'}",
            event_data=execution_context,
            execution_context=execution_context
        )

        # パフォーマンスメトリクス記録
        if execution_time_seconds is not None:
            self.log_performance_metric(
                f"{operation_name}_execution_time",
                execution_time_seconds,
                context={"success": success, "operation": operation_name},
                execution_id=execution_id
            )

    def _write_structured_log(self, category: str, log_entry: LogEntry):
        """構造化ログの書き込み"""

        with self.lock:
            try:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                log_file_path = f"{self.log_base_path}/{self.agent_name}/{category}/{date_str}-{category}.log"

                # ログローテーションチェック
                self._check_log_rotation(log_file_path)

                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    json.dump(asdict(log_entry), log_file, ensure_ascii=False, separators=(',', ':'))
                    log_file.write("\n")

            except Exception as e:
                print(f"Failed to write structured log: {str(e)}")

    def _write_performance_log(self, metric: PerformanceMetric):
        """パフォーマンスログの書き込み"""

        with self.lock:
            try:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                log_file_path = f"{self.log_base_path}/{self.agent_name}/performance/{date_str}-performance.log"

                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    json.dump(asdict(metric), log_file, ensure_ascii=False, separators=(',', ':'))
                    log_file.write("\n")

            except Exception as e:
                print(f"Failed to write performance log: {str(e)}")

    def _write_error_log(self, error_report: ErrorReport):
        """エラーログの書き込み"""

        with self.lock:
            try:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                log_file_path = f"{self.log_base_path}/{self.agent_name}/errors/{date_str}-errors.log"

                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    json.dump(asdict(error_report), log_file, ensure_ascii=False, separators=(',', ':'))
                    log_file.write("\n")

            except Exception as e:
                print(f"Failed to write error log: {str(e)}")

    def _write_console_log(self, log_entry: LogEntry):
        """コンソールログ出力"""

        console_message = f"[{log_entry.timestamp}] {log_entry.agent_name} {log_entry.log_level}: {log_entry.message}"

        if log_entry.log_level in ["ERROR", "CRITICAL"]:
            print(f"\033[91m{console_message}\033[0m")  # Red
        elif log_entry.log_level == "WARNING":
            print(f"\033[93m{console_message}\033[0m")  # Yellow
        else:
            print(console_message)

    def get_metric_unit(self, metric_name: str) -> str:
        """メトリクス単位の決定"""

        unit_mapping = {
            "_time": "seconds",
            "_count": "count",
            "_rate": "percentage",
            "_size": "bytes",
            "_score": "score",
            "_utilization": "percentage",
            "_latency": "milliseconds",
            "_throughput": "requests_per_second"
        }

        for suffix, unit in unit_mapping.items():
            if suffix in metric_name.lower():
                return unit

        return "value"

    def determine_error_severity(self, error_type: str) -> ErrorSeverity:
        """エラー重要度の判定"""

        critical_errors = [
            "system_failure", "data_corruption", "security_breach",
            "service_unavailable", "critical_exception"
        ]

        high_errors = [
            "operation_failure", "timeout_error", "connection_failure",
            "authentication_failure", "authorization_denied"
        ]

        medium_errors = [
            "validation_error", "configuration_error", "resource_limit",
            "deprecated_usage", "performance_degradation"
        ]

        error_type_lower = error_type.lower()

        if any(critical in error_type_lower for critical in critical_errors):
            return ErrorSeverity.CRITICAL
        elif any(high in error_type_lower for high in high_errors):
            return ErrorSeverity.HIGH
        elif any(medium in error_type_lower for medium in medium_errors):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def generate_execution_id(self) -> str:
        """実行ID生成"""
        return f"{self.agent_name}_exec_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    def generate_error_id(self) -> str:
        """エラーID生成"""
        return f"{self.agent_name}_err_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    def _check_log_rotation(self, log_file_path: str):
        """ログローテーションチェック"""

        if os.path.exists(log_file_path):
            file_size = os.path.getsize(log_file_path)
            if file_size > self.max_log_file_size:
                self._rotate_log_file(log_file_path)

    def _rotate_log_file(self, log_file_path: str):
        """ログファイルローテーション"""

        try:
            # バックアップファイル名生成
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            backup_path = f"{log_file_path}.{timestamp}.backup"

            # ファイル移動
            os.rename(log_file_path, backup_path)

            # 古いバックアップファイル削除
            self._cleanup_old_log_files(os.path.dirname(log_file_path))

        except Exception as e:
            print(f"Log rotation failed for {log_file_path}: {str(e)}")

    def _cleanup_old_log_files(self, log_directory: str):
        """古いログファイルのクリーンアップ"""

        try:
            import glob

            # .backupファイルの一覧取得
            backup_files = glob.glob(f"{log_directory}/*.backup")
            backup_files.sort(key=os.path.getctime, reverse=True)

            # 上限を超えたファイルを削除
            if len(backup_files) > self.max_log_files:
                for old_file in backup_files[self.max_log_files:]:
                    os.remove(old_file)

        except Exception as e:
            print(f"Log cleanup failed for {log_directory}: {str(e)}")

    def _trigger_error_alert(self, error_report: ErrorReport):
        """重要エラーのアラート送信"""

        # アラート機能の実装（実装依存）
        alert_message = f"[{error_report.severity}] {self.agent_name}: {error_report.error_message}"
        print(f"🚨 ALERT: {alert_message}")

        # 将来の拡張: Slack通知、メール送信、監視システム連携等

    def initialize_log_rotation(self):
        """ログローテーション初期化"""

        # 起動時に古いログファイルをクリーンアップ
        agent_log_dir = f"{self.log_base_path}/{self.agent_name}"
        if os.path.exists(agent_log_dir):
            for subdir in ["execution", "errors", "performance", "summary"]:
                subdir_path = os.path.join(agent_log_dir, subdir)
                if os.path.exists(subdir_path):
                    self._cleanup_old_log_files(subdir_path)

    def generate_daily_summary(self) -> Dict[str, Any]:
        """日次サマリーレポート生成"""

        summary = {
            "agent_name": self.agent_name,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "session_id": self.session_id,
            "summary_timestamp": datetime.datetime.now().isoformat(),
            "log_statistics": self._calculate_log_statistics(),
            "performance_summary": self._generate_performance_summary(),
            "error_summary": self._generate_error_summary(),
            "top_events": self._identify_top_events()
        }

        # サマリーファイル書き込み
        self._write_daily_summary(summary)

        return summary

    def _calculate_log_statistics(self) -> Dict[str, int]:
        """ログ統計計算"""

        # 実装簡略化のため基本統計のみ
        return {
            "total_events": 0,
            "info_events": 0,
            "warning_events": 0,
            "error_events": 0,
            "critical_events": 0
        }

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリー生成"""

        return {
            "average_execution_time": 0.0,
            "total_operations": 0,
            "success_rate": 0.0,
            "performance_trends": []
        }

    def _generate_error_summary(self) -> Dict[str, Any]:
        """エラーサマリー生成"""

        return {
            "total_errors": 0,
            "error_by_severity": {},
            "top_error_types": [],
            "resolution_rate": 0.0
        }

    def _identify_top_events(self) -> List[Dict[str, Any]]:
        """主要イベント特定"""

        return []

    def _write_daily_summary(self, summary: Dict[str, Any]):
        """日次サマリー書き込み"""

        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        summary_file_path = f"{self.log_base_path}/{self.agent_name}/summary/{date_str}-summary.json"

        try:
            with open(summary_file_path, "w", encoding="utf-8") as summary_file:
                json.dump(summary, summary_file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write daily summary: {str(e)}")

# 便利なデコレータ関数
def log_execution(logger: BaseAgentLogger, operation_name: str = None):
    """実行ログデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            execution_id = logger.log_execution_start(op_name, {"args": str(args), "kwargs": str(kwargs)})

            start_time = datetime.datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.datetime.now() - start_time).total_seconds()

                logger.log_execution_end(
                    execution_id, op_name, True,
                    {"result_type": type(result).__name__},
                    execution_time
                )

                return result

            except Exception as e:
                execution_time = (datetime.datetime.now() - start_time).total_seconds()

                logger.log_execution_end(
                    execution_id, op_name, False,
                    {"error": str(e)},
                    execution_time
                )

                logger.log_error_with_context(
                    "execution_exception",
                    str(e),
                    {"operation": op_name, "execution_id": execution_id}
                )

                raise

        return wrapper
    return decorator
```

## 🔧 **使用方法・継承例**

### **基本的な使用方法**
```python
# エージェント初期化時
class MyAgent:
    def __init__(self):
        self.logger = BaseAgentLogger("my-agent")

    def perform_operation(self):
        # 操作開始ログ
        execution_id = self.logger.log_execution_start("data_processing", {"batch_size": 1000})

        try:
            # 何らかの処理
            result = self.process_data()

            # 成功ログ
            self.logger.log_execution_end(execution_id, "data_processing", True, {"processed": len(result)})

            # パフォーマンスメトリクス
            self.logger.log_performance_metric("processing_throughput", len(result), {"batch_size": 1000})

            return result

        except Exception as e:
            # 失敗ログ
            self.logger.log_execution_end(execution_id, "data_processing", False, {"error": str(e)})
            self.logger.log_error_with_context("processing_error", str(e), {"batch_size": 1000})
            raise

# デコレータ使用例
@log_execution(logger, "critical_operation")
def critical_function():
    # 実装...
    pass
```

### **カスタムログ機能追加**
```python
class CustomAgentLogger(BaseAgentLogger):
    """カスタムエージェント用Logger"""

    def get_agent_specific_directories(self) -> List[str]:
        """カスタムディレクトリ追加"""
        return [
            f"{self.log_base_path}/{self.agent_name}/custom-category/",
            f"{self.log_base_path}/{self.agent_name}/business-events/"
        ]

    def log_business_event(self, event_name: str, event_data: Dict[str, Any]):
        """ビジネスイベント専用ログ"""
        self.log_structured_event(
            LogLevel.INFO,
            "business-events",
            "BUSINESS_EVENT",
            f"Business event: {event_name}",
            event_data=event_data
        )
```

## 📊 **ログ分析・監視機能**

### **ログ分析ユーティリティ**
```python
class LogAnalyzer:
    """ログ分析・監視ユーティリティ"""

    @staticmethod
    def analyze_agent_performance(agent_name: str, date_range: tuple) -> Dict[str, Any]:
        """エージェントパフォーマンス分析"""
        # パフォーマンスログの解析実装
        pass

    @staticmethod
    def generate_error_trends(agent_name: str, days: int = 7) -> Dict[str, Any]:
        """エラートレンド分析"""
        # エラーログの傾向分析実装
        pass

    @staticmethod
    def create_system_dashboard_data() -> Dict[str, Any]:
        """システムダッシュボード用データ生成"""
        # 全エージェントログの統合分析実装
        pass
```

## ⚙️ **設定・カスタマイズ**

### **ログ設定**
```python
class LogConfig:
    # ファイルサイズ・ローテーション
    MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LOG_FILES = 30  # 30日分

    # パフォーマンス設定
    FLUSH_INTERVAL = 5  # 5秒
    BATCH_SIZE = 100  # バッチ書き込み

    # アラート設定
    ENABLE_CONSOLE_ALERTS = True
    ENABLE_FILE_ALERTS = True
    CRITICAL_ERROR_NOTIFICATION = True
```

---

**BaseAgentLoggerにより、全エージェントで統一された高品質なログ管理・分析・監視機能が提供され、システム全体の運用効率と問題解決能力が大幅に向上します。**
