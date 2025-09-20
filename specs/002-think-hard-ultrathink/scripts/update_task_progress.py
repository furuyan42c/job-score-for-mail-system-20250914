#!/usr/bin/env python3
"""
タスク進捗更新スクリプト
tasks.mdファイルを解析し、進捗状況を自動計算してダッシュボードを更新する
"""

import re
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Task:
    id: str
    name: str
    progress: int
    quality: int
    status: str
    priority: str
    group: str

@dataclass
class GroupStats:
    name: str
    total_tasks: int
    completed: int
    in_progress: int
    not_started: int
    progress_percent: int
    quality_percent: int
    estimated_hours: int

def parse_task_header(line: str) -> Tuple[str, str, int, int, str, str]:
    """タスクヘッダー行をパース"""
    # 例: #### T001: データベーススキーマ作成 [100%] [Q:95%] [✅DONE] [🟢P3]
    pattern = r'#### (T\d+): (.+?) \[(\d+)%\] \[Q:(\d+)%\] \[(.+?)\] \[(.+?)\]'
    match = re.match(pattern, line)
    if match:
        return (
            match.group(1),  # Task ID
            match.group(2),  # Task name
            int(match.group(3)),  # Progress %
            int(match.group(4)),  # Quality %
            match.group(5),  # Status
            match.group(6)   # Priority
        )
    return None

def calculate_group_stats(tasks: List[Task]) -> GroupStats:
    """グループごとの統計を計算"""
    if not tasks:
        return GroupStats("", 0, 0, 0, 0, 0, 0, 0)

    completed = sum(1 for t in tasks if t.progress == 100)
    in_progress = sum(1 for t in tasks if 0 < t.progress < 100)
    not_started = sum(1 for t in tasks if t.progress == 0)

    avg_progress = sum(t.progress for t in tasks) // len(tasks) if tasks else 0
    avg_quality = sum(t.quality for t in tasks) // len(tasks) if tasks else 0

    # 推定時間（簡易計算）
    estimated_hours = not_started * 2 + in_progress * 1

    return GroupStats(
        name=tasks[0].group if tasks else "",
        total_tasks=len(tasks),
        completed=completed,
        in_progress=in_progress,
        not_started=not_started,
        progress_percent=avg_progress,
        quality_percent=avg_quality,
        estimated_hours=estimated_hours
    )

def update_dashboard(file_path: str):
    """tasks.mdファイルのダッシュボードを更新"""

    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # タスクを解析
    tasks_by_group = defaultdict(list)
    current_group = ""

    for i, line in enumerate(lines):
        # グループヘッダーを検出
        if line.startswith("## Group"):
            group_match = re.match(r'## Group ([A-E]):', line)
            if group_match:
                current_group = f"Group {group_match.group(1)}"

        # タスクヘッダーを検出
        if line.startswith("#### T"):
            task_info = parse_task_header(line)
            if task_info:
                task = Task(
                    id=task_info[0],
                    name=task_info[1],
                    progress=task_info[2],
                    quality=task_info[3],
                    status=task_info[4],
                    priority=task_info[5],
                    group=current_group
                )
                tasks_by_group[current_group].append(task)

    # グループごとの統計を計算
    group_stats = {}
    for group_name, tasks in tasks_by_group.items():
        if group_name:  # 空のグループを除外
            stats = calculate_group_stats(tasks)
            group_stats[group_name] = stats

    # ダッシュボードテーブルを生成
    dashboard_lines = []
    dashboard_lines.append("| Group | タスク数 | 完了 | 進行中 | 未着手 | 進捗% | 品質% | 推定残時間 |\n")
    dashboard_lines.append("|-------|---------|------|--------|---------|-------|-------|-----------|")

    total_tasks = 0
    total_completed = 0
    total_in_progress = 0
    total_not_started = 0
    total_hours = 0

    # グループ順序を定義
    group_order = ["Group A", "Group B", "Group C", "Group D", "Group E"]
    group_labels = {
        "Group A": "A: インフラ",
        "Group B": "B: コア実装",
        "Group C": "C: 統合",
        "Group D": "D: テスト",
        "Group E": "E: 本番"
    }

    for group in group_order:
        if group in group_stats:
            stats = group_stats[group]
            label = group_labels.get(group, group)
            dashboard_lines.append(
                f"| {label} | {stats.total_tasks} | {stats.completed} | "
                f"{stats.in_progress} | {stats.not_started} | {stats.progress_percent}% | "
                f"{stats.quality_percent}% | {stats.estimated_hours}h |\n"
            )
            total_tasks += stats.total_tasks
            total_completed += stats.completed
            total_in_progress += stats.in_progress
            total_not_started += stats.not_started
            total_hours += stats.estimated_hours

    # 合計行を追加
    total_progress = (total_completed * 100) // total_tasks if total_tasks else 0
    total_quality = sum(s.quality_percent for s in group_stats.values()) // len(group_stats) if group_stats else 0

    dashboard_lines.append(
        f"| **合計** | **{total_tasks}** | **{total_completed}** | "
        f"**{total_in_progress}** | **{total_not_started}** | **{total_progress}%** | "
        f"**{total_quality}%** | **{total_hours}h** |\n"
    )

    # ファイルのダッシュボード部分を更新
    dashboard_start = -1
    dashboard_end = -1

    for i, line in enumerate(lines):
        if "## 📊 タスク進捗ダッシュボード" in line:
            dashboard_start = i
        if dashboard_start >= 0 and line.startswith("### ") and i > dashboard_start:
            dashboard_end = i
            break

    if dashboard_start >= 0 and dashboard_end >= 0:
        # ダッシュボード部分を置き換え
        new_lines = lines[:dashboard_start+2]  # ヘッダーを保持
        new_lines.extend(dashboard_lines)
        new_lines.append("\n")
        new_lines.extend(lines[dashboard_end:])

        # ファイルを書き戻す
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"✅ ダッシュボードを更新しました")
        print(f"  - 総タスク数: {total_tasks}")
        print(f"  - 完了: {total_completed} ({total_progress}%)")
        print(f"  - 進行中: {total_in_progress}")
        print(f"  - 未着手: {total_not_started}")
        print(f"  - 推定残時間: {total_hours}h")
    else:
        print("⚠️ ダッシュボードセクションが見つかりませんでした")

def main():
    # tasks.mdファイルのパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tasks_file = os.path.join(base_dir, "tasks.md")

    if not os.path.exists(tasks_file):
        print(f"❌ ファイルが見つかりません: {tasks_file}")
        return

    update_dashboard(tasks_file)

if __name__ == "__main__":
    main()