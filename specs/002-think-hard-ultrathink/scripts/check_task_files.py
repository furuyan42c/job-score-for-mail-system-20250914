#!/usr/bin/env python3
"""
タスク関連ファイル存在チェックスクリプト
tasks.mdファイルで参照されているファイルの存在を確認する
"""

import re
import os
from typing import List, Dict, Tuple
from pathlib import Path

# プロジェクトのベースディレクトリ
PROJECT_ROOT = Path("/Users/furuyanaoki/Project/new.mail.score")

def parse_task_files(content: str) -> Dict[str, List[str]]:
    """タスク内のファイルパスを抽出"""
    files_by_task = {}
    current_task = None

    lines = content.split('\n')
    for line in lines:
        # タスクIDを検出
        task_match = re.match(r'#### (T\d+):', line)
        if task_match:
            current_task = task_match.group(1)
            files_by_task[current_task] = []

        # ファイルパスを検出
        if current_task:
            # 実装ファイル、テストファイル、仕様書などのパスを抽出
            file_patterns = [
                r'実装:\s*([^\s\[]+)',
                r'テスト:\s*([^\s\[]+)',
                r'仕様書:\s*([^\s\[]+)',
                r'`([^`]+\.(py|sql|md|ts|tsx|js|jsx|yaml|yml|json))`',
                r'- \*\*ファイル\*\*:\s*`([^`]+)`'
            ]

            for pattern in file_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    file_path = match[0] if isinstance(match, tuple) else match
                    if file_path and not file_path.startswith('http'):
                        files_by_task[current_task].append(file_path)

    return files_by_task

def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """ファイルの存在を確認"""
    # 相対パスを絶対パスに変換
    if not file_path.startswith('/'):
        full_path = PROJECT_ROOT / file_path
    else:
        full_path = Path(file_path)

    exists = full_path.exists()
    status = "✅存在" if exists else "🔴不明"

    return exists, status

def analyze_dependencies(content: str) -> Dict[str, Dict[str, List[str]]]:
    """タスク間の依存関係を解析"""
    dependencies = {}
    current_task = None

    lines = content.split('\n')
    for line in lines:
        # タスクIDを検出
        task_match = re.match(r'#### (T\d+):', line)
        if task_match:
            current_task = task_match.group(1)
            dependencies[current_task] = {
                'upstream': [],
                'downstream': [],
                'cascade': []
            }

        if current_task:
            # 依存関係を抽出
            if '前提:' in line or '⬆️' in line:
                deps = re.findall(r'T\d+', line)
                dependencies[current_task]['upstream'].extend(deps)
            elif 'ブロック中:' in line or '⬇️' in line:
                deps = re.findall(r'T\d+', line)
                dependencies[current_task]['downstream'].extend(deps)
            elif '変更時要確認:' in line or '🔄' in line:
                deps = re.findall(r'T\d+', line)
                dependencies[current_task]['cascade'].extend(deps)

    return dependencies

def generate_report(files_by_task: Dict[str, List[str]],
                   dependencies: Dict[str, Dict[str, List[str]]]) -> str:
    """チェック結果のレポートを生成"""
    report_lines = []
    report_lines.append("# ファイル存在チェックレポート\n")
    report_lines.append(f"チェック日時: {os.popen('date').read().strip()}\n\n")

    # サマリー
    total_tasks = len(files_by_task)
    total_files = sum(len(files) for files in files_by_task.values())
    existing_files = 0
    missing_files = 0

    # 各タスクのファイルをチェック
    report_lines.append("## タスク別ファイル状態\n\n")

    for task_id in sorted(files_by_task.keys()):
        files = list(set(files_by_task[task_id]))  # 重複除去
        if files:
            report_lines.append(f"### {task_id}\n")

            for file_path in files:
                exists, status = check_file_exists(file_path)
                if exists:
                    existing_files += 1
                else:
                    missing_files += 1

                report_lines.append(f"- {status} `{file_path}`\n")

            # 依存関係情報を追加
            if task_id in dependencies:
                deps = dependencies[task_id]
                if deps['upstream']:
                    report_lines.append(f"  - ⬆️ 前提: {', '.join(deps['upstream'])}\n")
                if deps['downstream']:
                    report_lines.append(f"  - ⬇️ ブロック: {', '.join(deps['downstream'])}\n")
                if deps['cascade']:
                    report_lines.append(f"  - 🔄 連鎖: {', '.join(deps['cascade'])}\n")

            report_lines.append("\n")

    # サマリーを先頭に追加
    summary = [
        "## 📊 サマリー\n\n",
        f"- 総タスク数: {total_tasks}\n",
        f"- 総ファイル参照数: {total_files}\n",
        f"- ✅ 存在確認: {existing_files} ({existing_files*100//total_files if total_files else 0}%)\n",
        f"- 🔴 不明: {missing_files} ({missing_files*100//total_files if total_files else 0}%)\n\n"
    ]

    # 不足ファイルのリスト
    if missing_files > 0:
        summary.append("## ⚠️ 作成が必要なファイル\n\n")
        for task_id in sorted(files_by_task.keys()):
            files = list(set(files_by_task[task_id]))
            for file_path in files:
                exists, _ = check_file_exists(file_path)
                if not exists:
                    summary.append(f"- [ ] {task_id}: `{file_path}`\n")
        summary.append("\n")

    return ''.join(summary + report_lines)

def main():
    # tasks.mdファイルのパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tasks_file = os.path.join(base_dir, "tasks.md")

    if not os.path.exists(tasks_file):
        print(f"❌ ファイルが見つかりません: {tasks_file}")
        return

    # ファイルを読み込み
    with open(tasks_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # ファイルパスを抽出
    files_by_task = parse_task_files(content)

    # 依存関係を解析
    dependencies = analyze_dependencies(content)

    # レポートを生成
    report = generate_report(files_by_task, dependencies)

    # レポートを保存
    report_file = os.path.join(base_dir, "file_check_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ ファイルチェック完了")
    print(f"📄 レポート: {report_file}")

    # サマリーを表示
    total_files = sum(len(files) for files in files_by_task.values())
    existing_files = 0
    missing_files = 0

    for task_id, files in files_by_task.items():
        for file_path in set(files):
            exists, _ = check_file_exists(file_path)
            if exists:
                existing_files += 1
            else:
                missing_files += 1

    print(f"\n📊 サマリー:")
    print(f"  - 総ファイル参照数: {total_files}")
    print(f"  - ✅ 存在: {existing_files}")
    print(f"  - 🔴 不明: {missing_files}")

if __name__ == "__main__":
    main()