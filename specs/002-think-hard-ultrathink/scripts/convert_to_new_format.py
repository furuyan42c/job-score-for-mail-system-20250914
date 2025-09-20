#!/usr/bin/env python3
"""
タスクを新フォーマットに変換するスクリプト
旧フォーマットのタスクを新しい統一フォーマットに自動変換
"""

import re
import sys
from pathlib import Path

def extract_task_info(task_content):
    """タスク情報を抽出"""
    info = {
        'id': '',
        'name': '',
        'progress': 0,
        'quality': 0,
        'status': '⏳TODO',
        'priority': '🟢P3',
        'description': '',
        'files': [],
        'dependencies': [],
        'mcp': '',
        'tdd_phases': {
            'red': False,
            'green': False,
            'refactor': False
        },
        'blockers': [],
        'completion_criteria': []
    }

    # タスクID と名前
    match = re.search(r'^####\s+(T\d+):\s+(.+?)(?:\s+\[.*?\])*\s*$', task_content, re.MULTILINE)
    if match:
        info['id'] = match.group(1)
        info['name'] = match.group(2).strip()

    # 説明
    desc_match = re.search(r'-\s+\*\*説明\*\*:\s+(.+?)(?:\n|$)', task_content)
    if desc_match:
        info['description'] = desc_match.group(1).strip()

    # ファイル
    file_matches = re.findall(r'-\s+\*\*ファイル\*\*:\s+`(.+?)`', task_content)
    info['files'] = file_matches

    # 依存関係
    dep_match = re.search(r'-\s+\*\*依存\*\*:\s+(.+?)(?:\n|$)', task_content)
    if dep_match:
        deps_text = dep_match.group(1)
        if deps_text.lower() != 'なし':
            info['dependencies'] = [d.strip() for d in deps_text.split(',')]

    # MCP
    mcp_match = re.search(r'-\s+\*\*MCP\*\*:\s+(.+?)(?:\n|$)', task_content)
    if mcp_match:
        info['mcp'] = mcp_match.group(1).strip()

    # TDDフェーズ
    if '[✅RED]' in task_content or '[✅COMPLETE]' in task_content:
        info['tdd_phases']['red'] = True
        info['progress'] = 25
    if '[✅GREEN]' in task_content:
        info['tdd_phases']['green'] = True
        info['progress'] = 50
    if '[✅REFACTOR]' in task_content:
        info['tdd_phases']['refactor'] = True
        info['progress'] = 75
    if '[✅COMPLETE]' in task_content:
        info['progress'] = 100
        info['status'] = '✅DONE'

    # ステータス判定
    if '[x]' in task_content or info['progress'] > 0:
        if info['progress'] == 100:
            info['status'] = '✅DONE'
            info['quality'] = 90  # デフォルト品質
        elif info['progress'] == 75:
            info['status'] = '🔄REFACTOR'
            info['quality'] = 85
        elif info['progress'] == 50:
            info['status'] = '🟢GREEN'
            info['quality'] = 70
        elif info['progress'] == 25:
            info['status'] = '🔴RED'
            info['quality'] = 50

    # 優先度
    if '🔴' in task_content:
        info['priority'] = '🔴P1'
    elif '🟡' in task_content:
        info['priority'] = '🟡P2'
    elif '🟢' in task_content:
        info['priority'] = '🟢P3'

    return info

def format_new_task(info):
    """新フォーマットでタスクを生成"""
    output = []

    # ヘッダー
    output.append(f"#### {info['id']}: {info['name']} [{info['progress']}%] [Q:{info['quality']}%] [{info['status']}] [{info['priority']}]")
    output.append("")

    # タスク内容
    output.append(f"📝 **タスク内容**: {info['description']}")
    output.append("")

    # 進捗状況
    output.append("📊 **進捗状況**:")
    if info['progress'] >= 25:
        output.append(f"- ✅ RED (25%): テスト作成完了")
    else:
        output.append(f"- ⏳ RED (0%): 未着手")

    if info['progress'] >= 50:
        output.append(f"- ✅ GREEN (50%): 最小実装完了")
    else:
        output.append(f"- ⏳ GREEN (0%): 未着手")

    if info['progress'] >= 75:
        output.append(f"- ✅ REFACTOR (75%): 改善完了")
    else:
        output.append(f"- ⏳ REFACTOR (0%): 未着手")

    if info['progress'] >= 100:
        output.append(f"- ✅ DONE (100%): 完了")
    else:
        output.append(f"- ⏳ DONE (0%): 未完了")
    output.append("")

    # 必須ファイル
    output.append("📁 **必須ファイル**:")
    if info['files']:
        for file_path in info['files']:
            if Path(f"/Users/furuyanaoki/Project/new.mail.score/{file_path}").exists():
                output.append(f"実装: {file_path} [✅存在]")
            else:
                output.append(f"実装: {file_path} [🟡作成予定]")
    else:
        output.append("実装: （未定義） [🟡作成予定]")
    output.append("")

    # 依存関係
    output.append("🔗 **依存関係**:")
    if info['dependencies']:
        output.append(f"前提: {', '.join(info['dependencies'])}")
    else:
        output.append("前提: なし")
    output.append("ブロック中: （要確認）")
    output.append("変更時要確認: （要確認）")
    output.append("")

    # MCP設定
    if info['mcp']:
        output.append(f"🔧 **MCP設定**: {info['mcp']}")
        output.append("")

    # 完了条件
    output.append("✅ **完了条件**:")
    output.append("- [ ] テスト作成")
    output.append("- [ ] 実装完了")
    output.append("- [ ] コードレビュー")
    output.append("- [ ] ドキュメント更新")
    output.append("")

    return '\n'.join(output)

def process_tasks_file(file_path):
    """タスクファイルを処理して新フォーマットに変換"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # タスクを分割
    task_pattern = r'(####\s+T\d+:.+?)(?=####\s+T\d+:|$)'
    tasks = re.findall(task_pattern, content, re.DOTALL)

    converted_tasks = []
    for task_content in tasks:
        info = extract_task_info(task_content)
        if info['id']:
            converted = format_new_task(info)
            converted_tasks.append(converted)

    return converted_tasks

if __name__ == "__main__":
    file_path = "/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"

    print("🔄 タスクを新フォーマットに変換中...")
    converted = process_tasks_file(file_path)

    # プレビュー表示
    print(f"\n✅ {len(converted)}個のタスクを変換しました")
    print("\n--- サンプル変換結果 (最初の3タスク) ---")
    for i, task in enumerate(converted[:3]):
        print(f"\n--- タスク {i+1} ---")
        print(task)

    # 確認
    response = input("\n変換を実行しますか？ (y/n): ")
    if response.lower() == 'y':
        output_path = file_path.replace('.md', '_converted.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(converted))
        print(f"✅ 変換済みファイル: {output_path}")