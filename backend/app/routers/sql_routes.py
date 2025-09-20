"""
SQL実行APIエンドポイント

読み取り専用のSQL実行機能を提供し、セキュリティ対策を実装
- SQLインジェクション対策
- 読み取り専用クエリのみ許可
- レート制限
- 監査ログ
"""

import re
import time
import logging
import hashlib
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

from app.core.database import get_db_read_only
from app.dependencies import security, get_redis, get_request_id

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# SECURITY CONSTANTS
# ============================================================================

# 許可されるSQL文のパターン（読み取り専用）
ALLOWED_SQL_PATTERNS = [
    r'^\s*SELECT\s+',
    r'^\s*SHOW\s+',
    r'^\s*DESCRIBE\s+',
    r'^\s*EXPLAIN\s+',
    r'^\s*WITH\s+.*SELECT\s+'
]

# ============================================================================
# SECURITY PATTERN DEFINITIONS (Organized by threat category)
# ============================================================================

# Core DDL/DML attacks - Prevents data modification and structure changes
CORE_DDL_DML_PATTERNS = [
    r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|REPLACE)\b',
    r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)',
]

# Stored procedure and command execution attacks
PROCEDURE_EXECUTION_PATTERNS = [
    r'\b(EXEC|EXECUTE|SP_|XP_)\b',
]

# Union-based injection patterns
UNION_INJECTION_PATTERNS = [
    r'\b(UNION\s+SELECT)\b',
]

# Comment-based evasion attacks
COMMENT_EVASION_PATTERNS = [
    r'--\s*$',  # SQL line comments
    r'/\*.*\*/',  # SQL block comments
]

# String manipulation injection functions
STRING_INJECTION_PATTERNS = [
    r'\b(CONCAT|SUBSTRING|ASCII|CHAR)\s*\(',
    r"'[^']*'[^']*'",  # Quote escape attempts
]

# Time-based blind injection patterns
TIME_BASED_INJECTION_PATTERNS = [
    r'\b(WAITFOR|SLEEP|DELAY)\b',
    r'\b(BENCHMARK|EXTRACTVALUE|UPDATEXML)\s*\(',
]

# File system access patterns
FILE_SYSTEM_PATTERNS = [
    r'\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b',
]

# Advanced blind injection patterns (T039 enhancement)
BLIND_INJECTION_PATTERNS = [
    r'\bEXISTS\s*\(',  # Subquery existence checks
    r'\b(MD5|SHA1|SHA2)\s*\(',  # Hash functions for blind injection
]

# Information gathering patterns
INFORMATION_GATHERING_PATTERNS = [
    r'\b(VERSION|USER|DATABASE|CURRENT_USER|SESSION_USER|SYSTEM_USER)\s*\(',
    r'\bINFORMATION_SCHEMA\b',
    r'\bSCHEMA_NAME\b',
    r'@@[a-zA-Z_]+',  # MySQL system variables
]

# Encoding bypass patterns
ENCODING_BYPASS_PATTERNS = [
    r'\b0x[0-9A-Fa-f]+',  # Hex literals
    r'%[0-9A-Fa-f]{2}',  # URL encoding
    r'\\u[0-9A-Fa-f]{4}',  # Unicode encoding
    r'\bFROM_BASE64\s*\(',  # Base64 decoding
    r'\bCONVERT\s*\(',  # Character set conversion
    r'\b(HEX|UNHEX)\s*\(',  # Hex conversion functions
]

# Privilege escalation patterns
PRIVILEGE_ESCALATION_PATTERNS = [
    r'\b(GRANT|REVOKE)\s+',
    r'\bCREATE\s+USER\b',
]

# System function patterns
SYSTEM_FUNCTION_PATTERNS = [
    r'\b(NOW|UNIX_TIMESTAMP|CONNECTION_ID)\s*\(',
]

# Combined dangerous patterns (all categories)
DANGEROUS_SQL_PATTERNS = (
    CORE_DDL_DML_PATTERNS +
    PROCEDURE_EXECUTION_PATTERNS +
    UNION_INJECTION_PATTERNS +
    COMMENT_EVASION_PATTERNS +
    STRING_INJECTION_PATTERNS +
    TIME_BASED_INJECTION_PATTERNS +
    FILE_SYSTEM_PATTERNS +
    BLIND_INJECTION_PATTERNS +
    INFORMATION_GATHERING_PATTERNS +
    ENCODING_BYPASS_PATTERNS +
    PRIVILEGE_ESCALATION_PATTERNS +
    SYSTEM_FUNCTION_PATTERNS
)

# 許可されるテーブル名パターン
ALLOWED_TABLES = [
    'jobs', 'users', 'user_actions', 'user_profiles',
    'company_popularity', 'job_enrichment', 'batch_jobs',
    'daily_email_queue', 'prefecture_master', 'city_master',
    'occupation_master', 'employment_type_master', 'feature_master',
    'semrush_keywords', 'job_keywords'
]

# レート制限設定
RATE_LIMIT_REQUESTS = 30  # 30分間のリクエスト数
RATE_LIMIT_WINDOW = 1800  # 30分（秒）
MAX_QUERY_EXECUTION_TIME = 30  # 最大クエリ実行時間（秒）
MAX_RESULT_ROWS = 1000  # 最大結果行数

# ============================================================================
# DATA MODELS
# ============================================================================

class SQLExecuteRequest(BaseModel):
    """SQL実行リクエスト"""
    query: str = Field(..., description="実行するSQLクエリ", max_length=5000)
    limit: Optional[int] = Field(100, description="結果の最大行数", le=MAX_RESULT_ROWS)
    explain_only: bool = Field(False, description="EXPLAIN実行のみ")
    cache_ttl: Optional[int] = Field(300, description="キャッシュTTL（秒）", le=3600)

    @validator('query')
    def validate_query(cls, query: str) -> str:
        """SQLクエリの検証"""
        if not query or not query.strip():
            raise ValueError("クエリが空です")

        # 長さチェック
        if len(query) > 5000:
            raise ValueError("クエリが長すぎます（最大5000文字）")

        return query.strip()

class SQLExecuteResponse(BaseModel):
    """SQL実行レスポンス"""
    success: bool
    query: str
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    from_cache: bool = False
    explain_plan: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

class SQLSecurityError(BaseModel):
    """SQLセキュリティエラー"""
    error_type: str
    message: str
    detected_patterns: List[str] = []
    timestamp: datetime
    query_hash: str

# ============================================================================
# SECURITY FUNCTIONS
# ============================================================================

# Pattern categories for better violation reporting
PATTERN_CATEGORIES = {
    'DDL_DML': (CORE_DDL_DML_PATTERNS, "データ変更操作が検出されました"),
    'PROCEDURE': (PROCEDURE_EXECUTION_PATTERNS, "ストアドプロシージャ実行が検出されました"),
    'UNION': (UNION_INJECTION_PATTERNS, "UNION インジェクションが検出されました"),
    'COMMENTS': (COMMENT_EVASION_PATTERNS, "SQLコメント回避が検出されました"),
    'STRING_MANIPULATION': (STRING_INJECTION_PATTERNS, "文字列操作インジェクションが検出されました"),
    'TIME_BASED': (TIME_BASED_INJECTION_PATTERNS, "時間ベースインジェクションが検出されました"),
    'FILE_SYSTEM': (FILE_SYSTEM_PATTERNS, "ファイルシステムアクセスが検出されました"),
    'BLIND_INJECTION': (BLIND_INJECTION_PATTERNS, "ブラインドインジェクションが検出されました"),
    'INFO_GATHERING': (INFORMATION_GATHERING_PATTERNS, "情報収集攻撃が検出されました"),
    'ENCODING': (ENCODING_BYPASS_PATTERNS, "エンコーディング回避が検出されました"),
    'PRIVILEGE': (PRIVILEGE_ESCALATION_PATTERNS, "権限昇格攻撃が検出されました"),
    'SYSTEM_FUNCTIONS': (SYSTEM_FUNCTION_PATTERNS, "システム関数アクセスが検出されました"),
}

def _normalize_query(query: str) -> str:
    """Normalize SQL query for security analysis"""
    return re.sub(r'\s+', ' ', query.upper().strip())

def _check_allowed_query_type(normalized_query: str) -> bool:
    """Check if query type is allowed (read-only operations)"""
    for pattern in ALLOWED_SQL_PATTERNS:
        if re.match(pattern, normalized_query, re.IGNORECASE):
            return True
    return False

def _detect_dangerous_patterns(normalized_query: str) -> List[str]:
    """Detect dangerous SQL patterns by category"""
    violations = []

    for category, (patterns, message) in PATTERN_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                violations.append(f"{message}: {pattern}")
                break  # Only report first match per category

    return violations

def _validate_table_access(normalized_query: str) -> List[str]:
    """Validate table access permissions"""
    violations = []

    # Extract CTE (Common Table Expression) names to avoid false positives
    cte_names = set()
    cte_pattern = r'\bWITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS'
    cte_matches = re.findall(cte_pattern, normalized_query, re.IGNORECASE)
    for cte_name in cte_matches:
        cte_names.add(cte_name.lower())

    # Check FROM clause tables (excluding CTEs)
    table_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    tables = re.findall(table_pattern, normalized_query, re.IGNORECASE)

    for table in tables:
        table_lower = table.lower()
        if table_lower not in ALLOWED_TABLES and table_lower not in cte_names:
            violations.append(f"許可されていないテーブル: {table}")

    # Check JOIN clause tables (excluding CTEs)
    join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    join_tables = re.findall(join_pattern, normalized_query, re.IGNORECASE)

    for table in join_tables:
        table_lower = table.lower()
        if table_lower not in ALLOWED_TABLES and table_lower not in cte_names:
            violations.append(f"JOINで許可されていないテーブル: {table}")

    return violations

def _validate_query_complexity(normalized_query: str) -> List[str]:
    """Validate query complexity limits"""
    violations = []

    # Subquery depth check
    subquery_depth = normalized_query.count('(SELECT')
    if subquery_depth > 3:
        violations.append("サブクエリの深さが制限を超えています（最大3階層）")

    # UNION count check
    if 'UNION' in normalized_query and 'SELECT' in normalized_query:
        union_count = normalized_query.count('UNION')
        if union_count > 2:
            violations.append("UNION句の使用が制限を超えています（最大2回）")

    return violations

def validate_sql_security(query: str) -> Tuple[bool, List[str]]:
    """
    SQLクエリのセキュリティ検証（T039拡張版）

    包括的なセキュリティチェックを実行し、カテゴリ別の詳細な違反情報を提供

    Args:
        query: 検証するSQLクエリ

    Returns:
        (is_safe, violations): 安全性フラグと違反リスト
    """
    violations = []

    # Query normalization
    normalized_query = _normalize_query(query)

    # 1. Query type validation (read-only check)
    if not _check_allowed_query_type(normalized_query):
        violations.append("許可されていないSQL文タイプです（読み取り専用のみ許可）")

    # 2. Dangerous pattern detection
    violations.extend(_detect_dangerous_patterns(normalized_query))

    # 3. Table access validation
    violations.extend(_validate_table_access(normalized_query))

    # 4. Query complexity validation
    violations.extend(_validate_query_complexity(normalized_query))

    is_safe = len(violations) == 0
    return is_safe, violations

async def check_rate_limit(
    redis_client,
    identifier: str,
    window: int = RATE_LIMIT_WINDOW,
    max_requests: int = RATE_LIMIT_REQUESTS
) -> Tuple[bool, int, int]:
    """
    レート制限チェック

    Args:
        redis_client: Redisクライアント
        identifier: ユーザー識別子
        window: 時間窓（秒）
        max_requests: 最大リクエスト数

    Returns:
        (is_allowed, current_count, remaining): 許可フラグ、現在のカウント、残り回数
    """
    key = f"rate_limit:sql:{identifier}"
    current_time = int(time.time())

    try:
        # 現在のカウントを取得
        current_count = await redis_client.get(key)
        current_count = int(current_count) if current_count else 0

        if current_count >= max_requests:
            remaining = 0
            return False, current_count, remaining

        # カウントを増加
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()

        current_count += 1
        remaining = max_requests - current_count

        return True, current_count, remaining

    except Exception as e:
        logger.error(f"Rate limit check failed: {str(e)}")
        # Redis障害時は制限を緩く設定
        return True, 0, max_requests

def generate_query_hash(query: str, user_id: str) -> str:
    """クエリのハッシュ値を生成（キャッシュキー用）"""
    content = f"{query}:{user_id}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

async def verify_sql_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    SQL実行権限の検証

    注意: 実際の実装では、より厳密な権限チェックが必要
    """
    try:
        # 簡易的な実装（本番では適切なJWT検証を実装）
        token = credentials.credentials

        # 最低限のトークン形式チェック
        if not token or len(token) < 20:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なアクセストークンです",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # トークンからユーザーIDを抽出（実際は JWT デコード）
        # 開発用のダミー実装
        if token.startswith("sql_"):
            user_id = token[4:20]  # sql_xxxxxxxxxxxxxxxx
            return user_id

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SQL実行権限がありません"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました"
        )

# ============================================================================
# AUDIT LOGGING
# ============================================================================

async def log_sql_execution(
    user_id: str,
    query: str,
    success: bool,
    execution_time: float,
    row_count: int = 0,
    error_message: str = None,
    redis_client = None
):
    """SQL実行の監査ログ"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
        "query_length": len(query),
        "success": success,
        "execution_time_ms": execution_time,
        "row_count": row_count,
        "error_message": error_message
    }

    # 構造化ログ出力
    if success:
        logger.info(f"SQL execution succeeded", extra=log_entry)
    else:
        logger.warning(f"SQL execution failed", extra=log_entry)

    # Redis に実行統計を保存（オプション）
    if redis_client:
        try:
            stats_key = f"sql_stats:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
            await redis_client.hincrby(stats_key, "total_queries", 1)
            if success:
                await redis_client.hincrby(stats_key, "successful_queries", 1)
            await redis_client.expire(stats_key, 86400 * 7)  # 7日間保持
        except Exception as e:
            logger.error(f"Failed to update SQL stats: {str(e)}")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/execute", response_model=SQLExecuteResponse)
async def execute_sql(
    request: SQLExecuteRequest,
    user_id: str = Depends(verify_sql_access_token),
    db: AsyncSession = Depends(get_db_read_only),
    redis_client = Depends(get_redis),
    request_id: str = Depends(get_request_id)
):
    """
    SQL実行エンドポイント（読み取り専用）

    セキュリティ機能:
    - SQL インジェクション対策
    - 読み取り専用クエリのみ
    - レート制限
    - 監査ログ
    """
    start_time = time.time()
    query = request.query

    # 1. レート制限チェック
    is_allowed, current_count, remaining = await check_rate_limit(
        redis_client, user_id
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"レート制限に達しました。{RATE_LIMIT_WINDOW//60}分後に再試行してください。",
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + RATE_LIMIT_WINDOW))
            }
        )

    # 2. SQLセキュリティ検証
    is_safe, violations = validate_sql_security(query)

    if not is_safe:
        # セキュリティ違反をログに記録
        security_error = SQLSecurityError(
            error_type="SECURITY_VIOLATION",
            message="危険なSQLパターンが検出されました",
            detected_patterns=violations,
            timestamp=datetime.now(),
            query_hash=generate_query_hash(query, user_id)
        )

        logger.warning(
            f"SQL security violation by user {user_id}",
            extra=security_error.dict()
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "セキュリティ違反",
                "violations": violations,
                "message": "許可されていないSQL文です"
            }
        )

    # 3. キャッシュチェック
    cache_key = f"sql_cache:{generate_query_hash(query, user_id)}"
    cached_result = None
    from_cache = False

    if request.cache_ttl and request.cache_ttl > 0:
        try:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                import json
                cached_data = json.loads(cached_result)
                from_cache = True

                await log_sql_execution(
                    user_id, query, True,
                    time.time() - start_time,
                    cached_data['row_count'],
                    redis_client=redis_client
                )

                return SQLExecuteResponse(
                    success=True,
                    query=query,
                    columns=cached_data['columns'],
                    rows=cached_data['rows'],
                    row_count=cached_data['row_count'],
                    execution_time_ms=(time.time() - start_time) * 1000,
                    from_cache=True,
                    metadata={
                        "request_id": request_id,
                        "user_id": user_id,
                        "rate_limit_remaining": remaining
                    }
                )
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")

    # 4. EXPLAIN実行（オプション）
    explain_plan = None
    if request.explain_only:
        try:
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            result = await db.execute(text(explain_query))
            explain_plan = result.fetchone()[0]
        except Exception as e:
            logger.warning(f"EXPLAIN execution failed: {str(e)}")

    # 5. SQL実行
    try:
        # クエリにLIMIT句を追加（安全性確保）
        limited_query = query
        if 'LIMIT' not in query.upper():
            limited_query = f"{query} LIMIT {request.limit}"

        # 実行時間制限付きでクエリを実行
        result = await asyncio.wait_for(
            db.execute(text(limited_query)),
            timeout=MAX_QUERY_EXECUTION_TIME
        )

        # 結果を取得
        rows = result.fetchall()
        columns = list(result.keys()) if rows else []

        # データを変換
        formatted_rows = []
        for row in rows[:request.limit]:
            formatted_rows.append([
                str(value) if value is not None else None
                for value in row
            ])

        execution_time = (time.time() - start_time) * 1000
        row_count = len(formatted_rows)

        # レスポンス作成
        response = SQLExecuteResponse(
            success=True,
            query=query,
            columns=columns,
            rows=formatted_rows,
            row_count=row_count,
            execution_time_ms=execution_time,
            from_cache=from_cache,
            explain_plan=explain_plan,
            metadata={
                "request_id": request_id,
                "user_id": user_id,
                "rate_limit_remaining": remaining,
                "limited_query": limited_query != query
            }
        )

        # 結果をキャッシュ
        if request.cache_ttl and request.cache_ttl > 0 and not from_cache:
            try:
                import json
                cache_data = {
                    "columns": columns,
                    "rows": formatted_rows,
                    "row_count": row_count
                }
                await redis_client.setex(
                    cache_key,
                    request.cache_ttl,
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {str(e)}")

        # 監査ログ
        await log_sql_execution(
            user_id, query, True, execution_time, row_count,
            redis_client=redis_client
        )

        return response

    except asyncio.TimeoutError:
        error_msg = f"クエリがタイムアウトしました（制限: {MAX_QUERY_EXECUTION_TIME}秒）"
        await log_sql_execution(
            user_id, query, False, (time.time() - start_time) * 1000,
            error_message=error_msg, redis_client=redis_client
        )

        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=error_msg
        )

    except Exception as e:
        error_msg = str(e)
        execution_time = (time.time() - start_time) * 1000

        await log_sql_execution(
            user_id, query, False, execution_time,
            error_message=error_msg, redis_client=redis_client
        )

        logger.error(f"SQL execution failed for user {user_id}: {error_msg}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"クエリ実行エラー: {error_msg}"
        )

@router.get("/allowed-tables")
async def get_allowed_tables(
    user_id: str = Depends(verify_sql_access_token)
):
    """利用可能なテーブル一覧を取得"""
    return {
        "allowed_tables": ALLOWED_TABLES,
        "total_count": len(ALLOWED_TABLES),
        "description": "これらのテーブルに対してSELECT文を実行できます"
    }

@router.get("/usage-stats")
async def get_usage_stats(
    user_id: str = Depends(verify_sql_access_token),
    redis_client = Depends(get_redis)
):
    """SQL実行統計の取得"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        stats_key = f"sql_stats:{user_id}:{today}"

        stats = await redis_client.hgetall(stats_key)

        # レート制限情報
        rate_limit_key = f"rate_limit:sql:{user_id}"
        current_count = await redis_client.get(rate_limit_key)
        current_count = int(current_count) if current_count else 0

        return {
            "today_stats": {
                "total_queries": int(stats.get("total_queries", 0)),
                "successful_queries": int(stats.get("successful_queries", 0)),
                "error_rate": (
                    1 - int(stats.get("successful_queries", 0)) /
                    max(int(stats.get("total_queries", 1)), 1)
                ) * 100
            },
            "rate_limit": {
                "current_count": current_count,
                "max_requests": RATE_LIMIT_REQUESTS,
                "remaining": max(0, RATE_LIMIT_REQUESTS - current_count),
                "window_minutes": RATE_LIMIT_WINDOW // 60
            },
            "limits": {
                "max_execution_time_seconds": MAX_QUERY_EXECUTION_TIME,
                "max_result_rows": MAX_RESULT_ROWS,
                "max_query_length": 5000
            }
        }

    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="統計情報の取得に失敗しました"
        )

@router.post("/validate")
async def validate_sql_query(
    request: SQLExecuteRequest,
    user_id: str = Depends(verify_sql_access_token)
):
    """SQLクエリの事前検証（実行せずに安全性をチェック）"""
    is_safe, violations = validate_sql_security(request.query)

    return {
        "is_safe": is_safe,
        "violations": violations,
        "query_length": len(request.query),
        "estimated_complexity": "low" if len(request.query) < 500 else "medium" if len(request.query) < 2000 else "high",
        "recommendations": [
            "LIMIT句を使用して結果数を制限してください",
            "インデックスが効くように WHERE句を適切に設計してください",
            "複雑なJOINは避け、必要に応じて複数のクエリに分割してください"
        ] if is_safe else []
    }