#!/usr/bin/env python3
"""
Simple Security Test Runner
簡易セキュリティテスト実行ツール

依存関係を最小限に抑えたセキュリティテスト実行ツール
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class SimpleSecurityChecker:
    """簡易セキュリティチェッカー"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings = []

    def run_checks(self) -> Dict[str, Any]:
        """セキュリティチェックを実行"""
        print("🔍 Running security checks...")

        # 1. ハードコードされた秘密情報チェック
        print("  - Checking for hardcoded secrets...")
        self._check_hardcoded_secrets()

        # 2. SQLインジェクション脆弱性チェック
        print("  - Checking for SQL injection vulnerabilities...")
        self._check_sql_injection_patterns()

        # 3. 設定ファイルチェック
        print("  - Checking configuration files...")
        self._check_configuration()

        # 4. ファイル権限チェック
        print("  - Checking file permissions...")
        self._check_file_permissions()

        return self._generate_report()

    def _check_hardcoded_secrets(self):
        """ハードコードされた秘密情報をチェック"""
        secret_patterns = {
            'password': r'password\s*=\s*["\'][^"\']{1,}["\']',
            'api_key': r'api[_-]?key\s*=\s*["\'][^"\']{1,}["\']',
            'secret': r'secret\s*=\s*["\'][^"\']{1,}["\']',
            'token': r'token\s*=\s*["\'][^"\']{1,}["\']',
        }

        for file_path in self.project_root.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern_name, pattern in secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # 環境変数の使用は除外
                            if 'os.getenv' in line or 'settings.' in line:
                                continue

                            self.findings.append({
                                'severity': 'HIGH',
                                'category': 'HARDCODED_SECRET',
                                'title': f'Potential hardcoded {pattern_name}',
                                'file': str(file_path),
                                'line': line_num,
                                'description': f'Line contains potential hardcoded {pattern_name}'
                            })

            except Exception:
                continue

    def _check_sql_injection_patterns(self):
        """SQLインジェクション脆弱性パターンをチェック"""
        dangerous_patterns = [
            r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in SQL
            r'\.format\s*\(.*\)\s*\)',  # .format() in SQL
            r'f["\'].*\{.*\}.*["\']',  # f-strings in SQL (may be dangerous)
        ]

        for file_path in self.project_root.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern in dangerous_patterns:
                        if re.search(pattern, line):
                            self.findings.append({
                                'severity': 'CRITICAL',
                                'category': 'SQL_INJECTION',
                                'title': 'Potential SQL injection vulnerability',
                                'file': str(file_path),
                                'line': line_num,
                                'description': 'Suspicious SQL pattern found'
                            })

            except Exception:
                continue

    def _check_configuration(self):
        """設定ファイルをチェック"""
        config_files = ['.env', 'config.py', 'settings.py']

        for config_file in config_files:
            file_path = self.project_root / config_file
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 危険な設定パターン
                if re.search(r'DEBUG\s*=\s*True', content):
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'category': 'CONFIGURATION',
                        'title': 'Debug mode enabled',
                        'file': str(file_path),
                        'description': 'DEBUG=True found in configuration'
                    })

                if re.search(r'SECRET_KEY\s*=\s*["\'][^"\']{1,16}["\']', content):
                    self.findings.append({
                        'severity': 'HIGH',
                        'category': 'CONFIGURATION',
                        'title': 'Weak secret key',
                        'file': str(file_path),
                        'description': 'SECRET_KEY appears to be too short'
                    })

            except Exception:
                continue

    def _check_file_permissions(self):
        """ファイル権限をチェック"""
        sensitive_files = ['.env', 'config.py', 'settings.py']

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                continue

            try:
                stat = file_path.stat()
                mode = oct(stat.st_mode)[-3:]

                # 644より緩い権限は警告
                if int(mode) > 644:
                    self.findings.append({
                        'severity': 'MEDIUM',
                        'category': 'FILE_PERMISSIONS',
                        'title': f'Overly permissive file permissions: {file_name}',
                        'file': str(file_path),
                        'description': f'File has permissions {mode}'
                    })

            except Exception:
                continue

    def _should_skip_file(self, file_path: Path) -> bool:
        """ファイルをスキップすべきかチェック"""
        skip_patterns = [
            'node_modules',
            'venv',
            '.git',
            '__pycache__',
            'migrations',
            'test_'
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _generate_report(self) -> Dict[str, Any]:
        """レポートを生成"""
        severity_counts = {
            'CRITICAL': len([f for f in self.findings if f['severity'] == 'CRITICAL']),
            'HIGH': len([f for f in self.findings if f['severity'] == 'HIGH']),
            'MEDIUM': len([f for f in self.findings if f['severity'] == 'MEDIUM']),
            'LOW': len([f for f in self.findings if f['severity'] == 'LOW']),
        }

        # セキュリティスコア計算
        penalty_weights = {'CRITICAL': 25, 'HIGH': 15, 'MEDIUM': 5, 'LOW': 1}
        total_penalty = sum(severity_counts[severity] * weight for severity, weight in penalty_weights.items())
        security_score = max(0, 100 - total_penalty)

        return {
            'timestamp': time.time(),
            'total_findings': len(self.findings),
            'severity_breakdown': severity_counts,
            'security_score': security_score,
            'findings': self.findings,
            'summary': self._generate_summary(severity_counts, security_score)
        }

    def _generate_summary(self, severity_counts: Dict[str, int], score: float) -> str:
        """サマリーを生成"""
        total_critical_high = severity_counts['CRITICAL'] + severity_counts['HIGH']

        if total_critical_high == 0:
            return f"✅ Good security posture (Score: {score}/100). No critical issues found."
        elif total_critical_high <= 2:
            return f"⚠️ Few security issues detected (Score: {score}/100). Address high-priority items."
        else:
            return f"🚨 Multiple security issues detected (Score: {score}/100). Immediate attention required."


def main():
    """メイン実行関数"""
    print("🛡️ Simple Security Checker")
    print("=" * 40)

    # プロジェクトルートを取得
    project_root = os.getcwd()

    # セキュリティチェック実行
    checker = SimpleSecurityChecker(project_root)
    results = checker.run_checks()

    # 結果表示
    print(f"\n📊 Security Check Results")
    print("-" * 30)
    print(f"Security Score: {results['security_score']}/100")
    print(f"Total Findings: {results['total_findings']}")

    print("\nSeverity Breakdown:")
    for severity, count in results['severity_breakdown'].items():
        if count > 0:
            print(f"  {severity}: {count}")

    print(f"\n{results['summary']}")

    # 詳細な発見事項を表示
    if results['findings']:
        print(f"\n🔍 Detailed Findings:")
        for i, finding in enumerate(results['findings'][:5], 1):  # 最初の5件のみ表示
            print(f"\n{i}. {finding['title']} ({finding['severity']})")
            print(f"   File: {finding['file']}")
            if 'line' in finding:
                print(f"   Line: {finding['line']}")
            print(f"   Description: {finding['description']}")

        if len(results['findings']) > 5:
            print(f"\n... and {len(results['findings']) - 5} more findings")

    # レポートファイル出力
    report_file = 'simple_security_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # 高重要度の問題がある場合は警告で終了
    critical_high = results['severity_breakdown']['CRITICAL'] + results['severity_breakdown']['HIGH']
    if critical_high > 0:
        print(f"\n⚠️ Found {critical_high} critical/high severity issues!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())