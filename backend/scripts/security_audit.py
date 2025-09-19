#!/usr/bin/env python3
"""
Security Audit Script
セキュリティ監査スクリプト

OWASP Top 10対応の包括的セキュリティチェック
- 自動脆弱性スキャン
- 設定検証
- 依存関係チェック
- セキュリティベストプラクティス検証
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import httpx
from sqlalchemy import create_engine, text
import yaml

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """セキュリティ発見事項"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str  # SQL_INJECTION, XSS, AUTH, CONFIG, etc.
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None
    owasp_category: Optional[str] = None


class SecurityAuditor:
    """メインセキュリティ監査クラス"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings: List[SecurityFinding] = []
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """監査設定を読み込み"""
        config_path = self.project_root / "security_audit_config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {
            "skip_patterns": [
                "*/node_modules/*",
                "*/venv/*",
                "*/migrations/*",
                "*/.git/*",
                "*/test_*",
                "*/__pycache__/*"
            ],
            "sensitive_patterns": {
                "password": r'password["\s]*[:=]["\s]*[^"\s]+',
                "api_key": r'api[_-]?key["\s]*[:=]["\s]*[^"\s]+',
                "secret": r'secret["\s]*[:=]["\s]*[^"\s]+',
                "token": r'token["\s]*[:=]["\s]*[^"\s]+'
            }
        }

    async def run_full_audit(self) -> Dict[str, Any]:
        """完全セキュリティ監査を実行"""
        logger.info("Starting comprehensive security audit...")

        # 各監査項目を実行
        audit_results = {}

        # 1. 静的コード解析
        logger.info("Running static code analysis...")
        await self._static_code_analysis()

        # 2. 依存関係脆弱性チェック
        logger.info("Checking dependency vulnerabilities...")
        await self._dependency_vulnerability_check()

        # 3. 設定ファイル検証
        logger.info("Validating configuration files...")
        await self._configuration_validation()

        # 4. 認証・認可チェック
        logger.info("Checking authentication and authorization...")
        await self._auth_security_check()

        # 5. データベースセキュリティ
        logger.info("Checking database security...")
        await self._database_security_check()

        # 6. セキュリティヘッダーチェック
        logger.info("Checking security headers...")
        await self._security_headers_check()

        # 7. ファイルアクセス権限チェック
        logger.info("Checking file permissions...")
        await self._file_permissions_check()

        # 8. OWASP Top 10チェック
        logger.info("Running OWASP Top 10 checks...")
        await self._owasp_top10_check()

        # レポート生成
        audit_results = self._generate_report()

        logger.info(f"Security audit completed. Found {len(self.findings)} issues.")
        return audit_results

    async def _static_code_analysis(self):
        """静的コード解析"""

        # 危険なパターンの検索
        dangerous_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in SQL
                r'\.format\s*\(.*\)\s*\)',  # .format() in SQL
                r'f["\'].*\{.*\}.*["\']',  # f-strings in SQL
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']{1,}["\']',
                r'secret\s*=\s*["\'][^"\']{1,}["\']',
                r'api[_-]?key\s*=\s*["\'][^"\']{1,}["\']',
                r'token\s*=\s*["\'][^"\']{1,}["\']',
            ],
            'unsafe_deserialization': [
                r'pickle\.loads?',
                r'yaml\.load\s*\(',  # Should use safe_load
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'xss_vulnerable': [
                r'render_template_string\s*\(',
                r'Markup\s*\(',
                r'\.innerHTML\s*=',
            ]
        }

        for root, dirs, files in os.walk(self.project_root):
            # スキップパターンチェック
            if any(pattern in str(root) for pattern in self.config['skip_patterns']):
                continue

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.sql')):
                    file_path = Path(root) / file
                    await self._scan_file_for_patterns(file_path, dangerous_patterns)

    async def _scan_file_for_patterns(self, file_path: Path, patterns: Dict[str, List[str]]):
        """ファイル内のパターンスキャン"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            severity = self._get_severity_for_category(category)
                            self.findings.append(SecurityFinding(
                                severity=severity,
                                category=category.upper(),
                                title=f"Potential {category.replace('_', ' ')} vulnerability",
                                description=f"Suspicious pattern found: {pattern}",
                                file_path=str(file_path),
                                line_number=line_num,
                                recommendation=self._get_recommendation_for_category(category),
                                owasp_category=self._get_owasp_category(category)
                            ))

        except Exception as e:
            logger.warning(f"Could not scan file {file_path}: {e}")

    async def _dependency_vulnerability_check(self):
        """依存関係の脆弱性チェック"""
        try:
            # Python dependencies
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                await self._check_python_dependencies(requirements_file)

            # Node.js dependencies
            package_json = self.project_root / "package.json"
            if package_json.exists():
                await self._check_node_dependencies(package_json)

        except Exception as e:
            logger.error(f"Dependency vulnerability check failed: {e}")

    async def _check_python_dependencies(self, requirements_file: Path):
        """Python依存関係チェック"""
        try:
            # safety を使用した脆弱性チェック
            result = subprocess.run([
                sys.executable, "-m", "pip", "check"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.findings.append(SecurityFinding(
                    severity="MEDIUM",
                    category="DEPENDENCY",
                    title="Broken Python dependencies detected",
                    description=result.stdout + result.stderr,
                    file_path=str(requirements_file),
                    recommendation="Fix dependency conflicts",
                    owasp_category="A06:2021 – Vulnerable and Outdated Components"
                ))

            # 古いパッケージの検出
            old_packages = await self._detect_outdated_packages()
            for package, version, latest in old_packages:
                self.findings.append(SecurityFinding(
                    severity="LOW",
                    category="OUTDATED_DEPENDENCY",
                    title=f"Outdated package: {package}",
                    description=f"Current: {version}, Latest: {latest}",
                    file_path=str(requirements_file),
                    recommendation=f"Update {package} to latest version",
                    owasp_category="A06:2021 – Vulnerable and Outdated Components"
                ))

        except Exception as e:
            logger.error(f"Python dependency check failed: {e}")

    async def _detect_outdated_packages(self) -> List[Tuple[str, str, str]]:
        """古いパッケージを検出"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "list", "--outdated", "--format=json"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                return [(pkg['name'], pkg['version'], pkg['latest_version'])
                       for pkg in outdated]
        except Exception as e:
            logger.warning(f"Could not check outdated packages: {e}")

        return []

    async def _configuration_validation(self):
        """設定ファイルの検証"""
        config_files = [
            "config.py", "settings.py", ".env", "docker-compose.yml",
            "nginx.conf", "gunicorn.conf.py"
        ]

        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                await self._validate_config_file(file_path)

    async def _validate_config_file(self, file_path: Path):
        """個別設定ファイルの検証"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 危険な設定パターン
            dangerous_configs = {
                'debug_enabled': r'DEBUG\s*=\s*True',
                'weak_secret': r'SECRET_KEY\s*=\s*["\'][^"\']{1,16}["\']',
                'default_passwords': r'password\s*=\s*["\'](?:admin|password|123456)["\']',
                'insecure_cors': r'CORS_ALLOW_ALL_ORIGINS\s*=\s*True',
                'sql_echo': r'echo\s*=\s*True',
            }

            for check_name, pattern in dangerous_configs.items():
                if re.search(pattern, content, re.IGNORECASE):
                    self.findings.append(SecurityFinding(
                        severity="HIGH" if "debug" in check_name or "weak" in check_name else "MEDIUM",
                        category="CONFIGURATION",
                        title=f"Insecure configuration: {check_name}",
                        description=f"Potentially insecure setting found in {file_path.name}",
                        file_path=str(file_path),
                        recommendation=self._get_config_recommendation(check_name),
                        owasp_category="A05:2021 – Security Misconfiguration"
                    ))

        except Exception as e:
            logger.warning(f"Could not validate config file {file_path}: {e}")

    async def _auth_security_check(self):
        """認証・認可セキュリティチェック"""
        auth_files = [
            "app/middleware/auth.py",
            "app/utils/jwt.py",
            "app/routers/auth.py"
        ]

        for auth_file in auth_files:
            file_path = self.project_root / auth_file
            if file_path.exists():
                await self._check_auth_implementation(file_path)

    async def _check_auth_implementation(self, file_path: Path):
        """認証実装のチェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 認証関連のセキュリティチェック
            auth_checks = {
                'weak_algorithm': r'algorithm\s*=\s*["\'](?:none|HS256)["\']',
                'no_token_expiry': r'exp.*datetime\.utcnow\(\)\s*\+\s*timedelta\(\s*days\s*=\s*(?:[1-9]\d+|\d{3,})',
                'insecure_password_hash': r'hashlib\.(?:md5|sha1)',
                'timing_attack_vulnerable': r'==.*password',
            }

            for check_name, pattern in auth_checks.items():
                if re.search(pattern, content):
                    severity = "HIGH" if "weak" in check_name or "insecure" in check_name else "MEDIUM"
                    self.findings.append(SecurityFinding(
                        severity=severity,
                        category="AUTHENTICATION",
                        title=f"Authentication vulnerability: {check_name}",
                        description=f"Potential authentication issue in {file_path.name}",
                        file_path=str(file_path),
                        recommendation=self._get_auth_recommendation(check_name),
                        owasp_category="A07:2021 – Identification and Authentication Failures"
                    ))

        except Exception as e:
            logger.warning(f"Could not check auth file {file_path}: {e}")

    async def _database_security_check(self):
        """データベースセキュリティチェック"""
        try:
            # データベース設定ファイルをチェック
            db_files = ["app/core/database.py", "alembic.ini"]

            for db_file in db_files:
                file_path = self.project_root / db_file
                if file_path.exists():
                    await self._check_database_config(file_path)

            # マイグレーションファイルのチェック
            migrations_dir = self.project_root / "migrations" / "versions"
            if migrations_dir.exists():
                await self._check_migration_files(migrations_dir)

        except Exception as e:
            logger.error(f"Database security check failed: {e}")

    async def _check_database_config(self, file_path: Path):
        """データベース設定チェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            db_security_checks = {
                'hardcoded_credentials': r'postgresql://[^:]+:[^@]+@',
                'no_ssl': r'sslmode\s*=\s*disable',
                'sql_echo_enabled': r'echo\s*=\s*True',
                'weak_pool_settings': r'pool_size\s*=\s*[1-5]\b',
            }

            for check_name, pattern in db_security_checks.items():
                if re.search(pattern, content):
                    self.findings.append(SecurityFinding(
                        severity="HIGH" if "credentials" in check_name else "MEDIUM",
                        category="DATABASE_SECURITY",
                        title=f"Database security issue: {check_name}",
                        description=f"Database security concern in {file_path.name}",
                        file_path=str(file_path),
                        recommendation=self._get_db_recommendation(check_name),
                        owasp_category="A05:2021 – Security Misconfiguration"
                    ))

        except Exception as e:
            logger.warning(f"Could not check database config {file_path}: {e}")

    async def _check_migration_files(self, migrations_dir: Path):
        """マイグレーションファイルのチェック"""
        for migration_file in migrations_dir.glob("*.py"):
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 危険なマイグレーションパターン
                if re.search(r'DROP\s+TABLE', content, re.IGNORECASE):
                    self.findings.append(SecurityFinding(
                        severity="HIGH",
                        category="DATABASE_MIGRATION",
                        title="Destructive migration detected",
                        description="Migration contains DROP TABLE statement",
                        file_path=str(migration_file),
                        recommendation="Review migration for data loss risk",
                        owasp_category="A03:2021 – Injection"
                    ))

            except Exception as e:
                logger.warning(f"Could not check migration file {migration_file}: {e}")

    async def _security_headers_check(self):
        """セキュリティヘッダーのチェック"""
        # アプリケーションが実行中の場合、ヘッダーをチェック
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5.0)
                await self._validate_security_headers(response.headers)
        except Exception:
            logger.info("Application not running, skipping live header check")

    async def _validate_security_headers(self, headers: Dict[str, str]):
        """セキュリティヘッダーの検証"""
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # HTTPSで必要
            'Content-Security-Policy': None,
        }

        for header_name, expected_value in required_headers.items():
            if header_name not in headers:
                self.findings.append(SecurityFinding(
                    severity="MEDIUM",
                    category="SECURITY_HEADERS",
                    title=f"Missing security header: {header_name}",
                    description=f"Required security header {header_name} is missing",
                    recommendation=f"Add {header_name} header to improve security",
                    owasp_category="A05:2021 – Security Misconfiguration"
                ))

    async def _file_permissions_check(self):
        """ファイルアクセス権限チェック"""
        sensitive_files = [
            ".env", "config.py", "settings.py",
            "private_key.pem", "server.key"
        ]

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                await self._check_file_permissions(file_path)

    async def _check_file_permissions(self, file_path: Path):
        """個別ファイルの権限チェック"""
        try:
            stat = file_path.stat()
            mode = oct(stat.st_mode)[-3:]  # 最後の3桁を取得

            # 644以上の権限は危険
            if int(mode) > 644:
                self.findings.append(SecurityFinding(
                    severity="MEDIUM",
                    category="FILE_PERMISSIONS",
                    title=f"Overly permissive file permissions: {file_path.name}",
                    description=f"File has permissions {mode}, should be 600 or 644",
                    file_path=str(file_path),
                    recommendation="Change file permissions to 600 or 644",
                    owasp_category="A05:2021 – Security Misconfiguration"
                ))

        except Exception as e:
            logger.warning(f"Could not check permissions for {file_path}: {e}")

    async def _owasp_top10_check(self):
        """OWASP Top 10 2021チェック"""
        owasp_checks = [
            self._check_broken_access_control,
            self._check_cryptographic_failures,
            self._check_injection_vulnerabilities,
            self._check_insecure_design,
            self._check_security_misconfiguration,
            self._check_vulnerable_components,
            self._check_auth_failures,
            self._check_software_integrity_failures,
            self._check_logging_monitoring_failures,
            self._check_ssrf_vulnerabilities
        ]

        for check in owasp_checks:
            try:
                await check()
            except Exception as e:
                logger.error(f"OWASP check failed: {e}")

    async def _check_broken_access_control(self):
        """A01:2021 – Broken Access Control"""
        # 認可チェックの不備を検索
        auth_files = list(self.project_root.rglob("*.py"))

        for file_path in auth_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 権限チェックなしのエンドポイント
                if re.search(r'@app\.route.*\n(?!.*@.*auth|.*@.*login_required)', content):
                    self.findings.append(SecurityFinding(
                        severity="HIGH",
                        category="ACCESS_CONTROL",
                        title="Potential unprotected endpoint",
                        description="Route without authentication decorator found",
                        file_path=str(file_path),
                        recommendation="Add authentication/authorization checks",
                        owasp_category="A01:2021 – Broken Access Control"
                    ))

            except Exception:
                continue

    async def _check_cryptographic_failures(self):
        """A02:2021 – Cryptographic Failures"""
        crypto_patterns = {
            'weak_cipher': r'(?:DES|RC4|MD5|SHA1)(?:\(|\s)',
            'hardcoded_keys': r'(?:aes_key|encryption_key)\s*=\s*["\'][^"\']+["\']',
            'weak_random': r'random\.random\(\)|random\.choice',
        }

        for file_path in self.project_root.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern_name, pattern in crypto_patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        self.findings.append(SecurityFinding(
                            severity="HIGH",
                            category="CRYPTOGRAPHIC_FAILURE",
                            title=f"Cryptographic weakness: {pattern_name}",
                            description="Weak cryptographic implementation detected",
                            file_path=str(file_path),
                            recommendation="Use strong cryptographic algorithms",
                            owasp_category="A02:2021 – Cryptographic Failures"
                        ))

            except Exception:
                continue

    # 他のOWASP Top 10チェック関数（簡略化）
    async def _check_injection_vulnerabilities(self):
        """A03:2021 – Injection"""
        pass  # 既に static_code_analysis で実装済み

    async def _check_insecure_design(self):
        """A04:2021 – Insecure Design"""
        pass

    async def _check_security_misconfiguration(self):
        """A05:2021 – Security Misconfiguration"""
        pass  # 既に configuration_validation で実装済み

    async def _check_vulnerable_components(self):
        """A06:2021 – Vulnerable and Outdated Components"""
        pass  # 既に dependency_vulnerability_check で実装済み

    async def _check_auth_failures(self):
        """A07:2021 – Identification and Authentication Failures"""
        pass  # 既に auth_security_check で実装済み

    async def _check_software_integrity_failures(self):
        """A08:2021 – Software and Data Integrity Failures"""
        pass

    async def _check_logging_monitoring_failures(self):
        """A09:2021 – Security Logging and Monitoring Failures"""
        pass

    async def _check_ssrf_vulnerabilities(self):
        """A10:2021 – Server-Side Request Forgery (SSRF)"""
        pass

    def _generate_report(self) -> Dict[str, Any]:
        """監査レポートを生成"""
        severity_counts = {
            'CRITICAL': len([f for f in self.findings if f.severity == 'CRITICAL']),
            'HIGH': len([f for f in self.findings if f.severity == 'HIGH']),
            'MEDIUM': len([f for f in self.findings if f.severity == 'MEDIUM']),
            'LOW': len([f for f in self.findings if f.severity == 'LOW']),
            'INFO': len([f for f in self.findings if f.severity == 'INFO']),
        }

        category_counts = {}
        for finding in self.findings:
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1

        return {
            'audit_timestamp': time.time(),
            'total_findings': len(self.findings),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'findings': [asdict(f) for f in self.findings],
            'security_score': self._calculate_security_score(),
            'recommendations': self._get_prioritized_recommendations()
        }

    def _calculate_security_score(self) -> float:
        """セキュリティスコアを計算（0-100）"""
        if not self.findings:
            return 100.0

        penalty_weights = {
            'CRITICAL': 25,
            'HIGH': 15,
            'MEDIUM': 5,
            'LOW': 1,
            'INFO': 0
        }

        total_penalty = sum(penalty_weights.get(f.severity, 0) for f in self.findings)

        # 最大ペナルティを100として正規化
        max_penalty = 100
        score = max(0, 100 - (total_penalty / max_penalty * 100))

        return round(score, 2)

    def _get_prioritized_recommendations(self) -> List[str]:
        """優先度付き推奨事項"""
        recommendations = []

        critical_findings = [f for f in self.findings if f.severity == 'CRITICAL']
        if critical_findings:
            recommendations.append("🔴 CRITICAL: Address critical security vulnerabilities immediately")

        high_findings = [f for f in self.findings if f.severity == 'HIGH']
        if high_findings:
            recommendations.append("🟠 HIGH: Fix high-severity issues within 24 hours")

        # カテゴリ別の推奨事項
        auth_findings = [f for f in self.findings if 'AUTH' in f.category]
        if auth_findings:
            recommendations.append("🔐 Strengthen authentication and authorization mechanisms")

        config_findings = [f for f in self.findings if 'CONFIG' in f.category]
        if config_findings:
            recommendations.append("⚙️ Review and harden configuration settings")

        return recommendations

    # ヘルパーメソッド
    def _get_severity_for_category(self, category: str) -> str:
        severity_map = {
            'sql_injection': 'CRITICAL',
            'hardcoded_secrets': 'HIGH',
            'unsafe_deserialization': 'HIGH',
            'xss_vulnerable': 'HIGH',
        }
        return severity_map.get(category, 'MEDIUM')

    def _get_recommendation_for_category(self, category: str) -> str:
        recommendations = {
            'sql_injection': 'Use parameterized queries or ORM methods',
            'hardcoded_secrets': 'Use environment variables or secure key management',
            'unsafe_deserialization': 'Use safe serialization methods like JSON',
            'xss_vulnerable': 'Implement proper input sanitization and output encoding',
        }
        return recommendations.get(category, 'Review and fix the identified issue')

    def _get_owasp_category(self, category: str) -> str:
        owasp_map = {
            'sql_injection': 'A03:2021 – Injection',
            'hardcoded_secrets': 'A02:2021 – Cryptographic Failures',
            'unsafe_deserialization': 'A08:2021 – Software and Data Integrity Failures',
            'xss_vulnerable': 'A03:2021 – Injection',
        }
        return owasp_map.get(category, 'A05:2021 – Security Misconfiguration')

    def _get_config_recommendation(self, check_name: str) -> str:
        recommendations = {
            'debug_enabled': 'Set DEBUG=False in production',
            'weak_secret': 'Use a strong SECRET_KEY with at least 32 characters',
            'default_passwords': 'Change default passwords to strong, unique values',
            'insecure_cors': 'Configure CORS properly, avoid allowing all origins',
            'sql_echo': 'Disable SQL echo in production',
        }
        return recommendations.get(check_name, 'Review configuration setting')

    def _get_auth_recommendation(self, check_name: str) -> str:
        recommendations = {
            'weak_algorithm': 'Use strong algorithms like RS256 for JWT',
            'no_token_expiry': 'Set reasonable token expiration times',
            'insecure_password_hash': 'Use bcrypt or Argon2 for password hashing',
            'timing_attack_vulnerable': 'Use timing-safe comparison functions',
        }
        return recommendations.get(check_name, 'Review authentication implementation')

    def _get_db_recommendation(self, check_name: str) -> str:
        recommendations = {
            'hardcoded_credentials': 'Use environment variables for database credentials',
            'no_ssl': 'Enable SSL/TLS for database connections',
            'sql_echo_enabled': 'Disable SQL echo in production',
            'weak_pool_settings': 'Configure appropriate connection pool settings',
        }
        return recommendations.get(check_name, 'Review database configuration')


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='Security Audit Tool')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--output', default='security_audit_report.json', help='Output file')
    parser.add_argument('--format', choices=['json', 'html', 'txt'], default='json', help='Output format')

    args = parser.parse_args()

    auditor = SecurityAuditor(args.project_root)
    results = await auditor.run_full_audit()

    # レポート出力
    if args.format == 'json':
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    elif args.format == 'html':
        await generate_html_report(results, args.output)
    else:
        await generate_text_report(results, args.output)

    print(f"Security audit completed. Report saved to {args.output}")
    print(f"Security Score: {results['security_score']}/100")
    print(f"Total Findings: {results['total_findings']}")

    # 重要な問題がある場合は非ゼロで終了
    critical_or_high = results['severity_breakdown']['CRITICAL'] + results['severity_breakdown']['HIGH']
    if critical_or_high > 0:
        print(f"⚠️  Found {critical_or_high} critical/high severity issues!")
        sys.exit(1)


async def generate_html_report(results: Dict[str, Any], output_file: str):
    """HTML形式のレポート生成"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Audit Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
            .finding { margin: 10px 0; padding: 15px; border-left: 4px solid #ccc; }
            .critical { border-left-color: #d32f2f; background-color: #ffebee; }
            .high { border-left-color: #f57c00; background-color: #fff3e0; }
            .medium { border-left-color: #fbc02d; background-color: #fffde7; }
            .low { border-left-color: #388e3c; background-color: #e8f5e8; }
            .summary { display: flex; justify-content: space-around; margin: 20px 0; }
            .metric { text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Security Audit Report</h1>
            <p>Generated: {timestamp}</p>
            <p>Security Score: <strong>{score}/100</strong></p>
        </div>

        <div class="summary">
            <div class="metric">
                <h3>{critical}</h3>
                <p>Critical</p>
            </div>
            <div class="metric">
                <h3>{high}</h3>
                <p>High</p>
            </div>
            <div class="metric">
                <h3>{medium}</h3>
                <p>Medium</p>
            </div>
            <div class="metric">
                <h3>{low}</h3>
                <p>Low</p>
            </div>
        </div>

        <h2>Findings</h2>
        {findings_html}
    </body>
    </html>
    """

    findings_html = ""
    for finding in results['findings']:
        severity_class = finding['severity'].lower()
        findings_html += f"""
        <div class="finding {severity_class}">
            <h3>{finding['title']}</h3>
            <p><strong>Severity:</strong> {finding['severity']}</p>
            <p><strong>Category:</strong> {finding['category']}</p>
            <p><strong>Description:</strong> {finding['description']}</p>
            {f"<p><strong>File:</strong> {finding['file_path']}</p>" if finding['file_path'] else ""}
            {f"<p><strong>Recommendation:</strong> {finding['recommendation']}</p>" if finding['recommendation'] else ""}
        </div>
        """

    html_content = html_template.format(
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
        score=results['security_score'],
        critical=results['severity_breakdown']['CRITICAL'],
        high=results['severity_breakdown']['HIGH'],
        medium=results['severity_breakdown']['MEDIUM'],
        low=results['severity_breakdown']['LOW'],
        findings_html=findings_html
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


async def generate_text_report(results: Dict[str, Any], output_file: str):
    """テキスト形式のレポート生成"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("SECURITY AUDIT REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Security Score: {results['security_score']}/100\n")
        f.write(f"Total Findings: {results['total_findings']}\n\n")

        f.write("SEVERITY BREAKDOWN\n")
        f.write("-" * 20 + "\n")
        for severity, count in results['severity_breakdown'].items():
            f.write(f"{severity}: {count}\n")

        f.write("\nFINDINGS\n")
        f.write("-" * 20 + "\n\n")

        for i, finding in enumerate(results['findings'], 1):
            f.write(f"{i}. {finding['title']}\n")
            f.write(f"   Severity: {finding['severity']}\n")
            f.write(f"   Category: {finding['category']}\n")
            f.write(f"   Description: {finding['description']}\n")
            if finding['file_path']:
                f.write(f"   File: {finding['file_path']}\n")
            if finding['recommendation']:
                f.write(f"   Recommendation: {finding['recommendation']}\n")
            f.write("\n")


if __name__ == "__main__":
    asyncio.run(main())