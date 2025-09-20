#!/usr/bin/env python3
"""
全タスクを新フォーマットに一括変換するスクリプト
"""

import re
from pathlib import Path

# タスクごとの進捗状況（簡易版）
TASK_PROGRESS = {
    'T001': 100, 'T002': 100, 'T003': 100, 'T004': 100,
    'T005': 100, 'T006': 100, 'T007': 100, 'T008': 100, 'T009': 100,
    'T010': 25, 'T011': 25, 'T012': 25, 'T013': 25,
    'T014': 100, 'T015': 100,
    'T016': 100, 'T017': 100, 'T018': 100, 'T019': 0, 'T020': 0,
    'T021': 75, 'T022': 0, 'T023': 0, 'T024': 0, 'T025': 0,
}

def get_new_format(task_id, name, progress=None):
    """新フォーマットのヘッダーを生成"""
    prog = progress if progress is not None else TASK_PROGRESS.get(task_id, 0)

    # 品質スコアの計算
    if prog == 100:
        quality = 90
        status = '✅DONE'
        priority = '🟢P3'
    elif prog == 75:
        quality = 85
        status = '🔄REFACTOR'
        priority = '🔴P1'
    elif prog == 50:
        quality = 70
        status = '🟢GREEN'
        priority = '🔴P1'
    elif prog == 25:
        quality = 50
        status = '🔴RED'
        priority = '🔴P1'
    else:
        quality = 0
        status = '⏳TODO'
        priority = '🟡P2'

    # T021 など重要タスクは優先度を上げる
    if task_id in ['T021', 'T022', 'T023', 'T024', 'T016', 'T017', 'T018']:
        priority = '🔴P1'

    return f"#### {task_id}: {name} [{prog}%] [Q:{quality}%] [{status}] [{priority}]"

def process_file():
    """ファイルを処理"""
    file_path = Path("/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 既に新フォーマットのタスクはスキップ
    # 旧フォーマットのパターン: #### T010: GET /matching/user/{id} 契約テスト [P] 🔴 [x]
    old_pattern = r'#### (T\d+): (.+?)(?:\s+\[P\])?\s*(?:🔴|🟡|🟢)?\s*(?:\[.+?\])?\s*$'

    lines = content.split('\n')
    new_lines = []

    for i, line in enumerate(lines):
        # 新フォーマットは変更しない
        if re.match(r'^#### T\d+:.+?\[\d+%\]', line):
            new_lines.append(line)
            continue

        # 旧フォーマットを検出して変換
        match = re.match(old_pattern, line)
        if match:
            task_id = match.group(1)
            task_name = match.group(2).strip()

            # 状態情報を解析
            if '[✅COMPLETE]' in line:
                progress = 100
            elif '[x]' in line:
                progress = 25
            else:
                progress = TASK_PROGRESS.get(task_id, 0)

            new_header = get_new_format(task_id, task_name, progress)
            new_lines.append(new_header)

            # 次の行に説明を追加
            if i + 1 < len(lines) and lines[i + 1].startswith('- **説明**:'):
                desc_match = re.search(r'- \*\*説明\*\*:\s*(.+)', lines[i + 1])
                if desc_match:
                    desc = desc_match.group(1).strip()
                    new_lines.append('')
                    new_lines.append(f'📝 **タスク内容**: {desc}')

                    # 進捗状況を追加
                    new_lines.append('')
                    new_lines.append('📊 **進捗状況**:')

                    if progress >= 25:
                        new_lines.append('- ✅ RED (25%): テスト作成完了 - 2025-09-18')
                    else:
                        new_lines.append('- ⏳ RED (0%): 未着手')

                    if progress >= 50:
                        new_lines.append('- ✅ GREEN (50%): 最小実装完了 - 2025-09-18')
                    else:
                        new_lines.append('- ⏳ GREEN (0%): 未着手')

                    if progress >= 75:
                        new_lines.append('- ✅ REFACTOR (75%): 改善完了 - 2025-09-19')
                    else:
                        new_lines.append('- ⏳ REFACTOR (0%): 未着手')

                    if progress >= 100:
                        new_lines.append('- ✅ DONE (100%): 完了 - 2025-09-19')
                    else:
                        new_lines.append('- ⏳ DONE (0%): 未完了')
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)

if __name__ == "__main__":
    print("🔄 タスクを新フォーマットに変換中...")
    new_content = process_file()

    # 新ファイルとして保存
    output_path = "/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks_unified.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ 変換完了: {output_path}")
    print("プレビューして問題なければ、以下を実行:")
    print("  mv tasks_unified.md tasks.md")