# Security Test Suite

This directory contains comprehensive security tests for the job matching system, covering both backend and frontend security concerns.

## Test Categories

### Backend Security Tests (Python)

1. **SQL Injection Prevention** (`backend/tests/security/test_sql_injection.py`)
   - Parameterized query validation
   - Input sanitization testing
   - Common injection pattern testing
   - Error message information disclosure prevention
   - Database schema protection

2. **Authentication & Authorization** (`backend/tests/security/test_authentication.py`)
   - JWT token security
   - Password strength requirements
   - Brute force protection
   - Session management security
   - Role-based access control (RBAC)
   - Multi-factor authentication support

3. **Data Encryption** (`backend/tests/security/test_data_encryption.py`)
   - PII data encryption at rest
   - TLS/SSL communication verification
   - Password hashing (bcrypt) validation
   - Sensitive data masking in logs
   - Encryption key management
   - Backup encryption

4. **Vulnerability Scanning** (`backend/tests/security/test_vulnerability_scan.py`)
   - XSS (Cross-Site Scripting) prevention
   - CSRF token validation
   - Security headers implementation
   - Directory traversal prevention
   - File upload security
   - Rate limiting verification
   - Input validation across endpoints

5. **Compliance Testing** (`backend/tests/security/test_compliance.py`)
   - GDPR compliance (data subject rights)
   - Privacy by design principles
   - Data retention policies
   - Consent management
   - Data breach response procedures

### Frontend Security Tests (TypeScript)

1. **OWASP ZAP Integration** (`frontend/tests/security/owasp-zap-scan.test.ts`)
   - Automated security scanning with OWASP ZAP
   - OWASP Top 10 vulnerability detection
   - Security report generation
   - Integration with CI/CD pipeline

2. **Dependency Vulnerability Checks** (`frontend/tests/security/dependency-check.test.ts`)
   - npm audit for JavaScript packages
   - Python safety check integration
   - License compliance checking
   - Malicious package detection
   - Outdated dependency identification

## Running Security Tests

### Backend Tests

Run all backend security tests:
```bash
cd backend
pytest tests/security/ -v
```

Run specific test categories:
```bash
# SQL injection tests
pytest tests/security/test_sql_injection.py -v

# Authentication tests
pytest tests/security/test_authentication.py -v

# Data encryption tests
pytest tests/security/test_data_encryption.py -v

# Vulnerability scan tests
pytest tests/security/test_vulnerability_scan.py -v

# Compliance tests
pytest tests/security/test_compliance.py -v
```

### Frontend Tests

Run frontend security tests:
```bash
cd frontend
npm run test:security
```

Or with Playwright:
```bash
npx playwright test tests/security/
```

### Dependency Vulnerability Checks

Run dependency security checks:
```bash
# JavaScript dependencies
npm audit
npm audit fix

# Python dependencies (if using safety)
pip install safety
safety check

# Generate comprehensive security report
node tests/security/dependency-check.test.ts
```

### OWASP ZAP Scanning

Prerequisites:
1. Install OWASP ZAP
2. Start ZAP proxy on localhost:8080
3. Set environment variables:

```bash
export ZAP_API_KEY="your-api-key"
export ZAP_URL="http://localhost:8080"
export TARGET_URL="http://localhost:3000"
```

Run ZAP security scan:
```bash
npx playwright test tests/security/owasp-zap-scan.test.ts
```

## Security Test Configuration

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost/testdb"

# JWT
JWT_SECRET_KEY="test-secret-key"
JWT_ALGORITHM="HS256"

# ZAP Integration
ZAP_API_KEY="test-api-key"
ZAP_URL="http://localhost:8080"
TARGET_URL="http://localhost:3000"

# Security Thresholds
MAX_CRITICAL_VULNERABILITIES=0
MAX_HIGH_VULNERABILITIES=2
MAX_MODERATE_VULNERABILITIES=10
```

### Test Data

Security tests use dedicated test data that includes:
- Common attack payloads
- Malicious file samples
- Invalid input patterns
- Edge cases for boundary testing

### Reporting

Security test results are saved to:
- `backend/reports/security/` - Python test reports
- `frontend/reports/security/` - TypeScript test reports
- `reports/zap-security-report.html` - OWASP ZAP scan results
- `reports/dependency-security-report.json` - Dependency vulnerability report

## Security Standards

### Password Security
- Minimum 12 characters
- Must include uppercase, lowercase, numbers
- Bcrypt with cost factor ≥ 12
- No common passwords allowed

### Data Protection
- PII encrypted at rest (AES-256)
- TLS 1.2+ for data in transit
- Sensitive data masked in logs
- Secure key management

### Authentication
- JWT with secure algorithms (HS256/RS256)
- Session timeout enforcement
- Brute force protection
- Multi-factor authentication support

### Authorization
- Role-based access control
- Principle of least privilege
- Cross-user data isolation
- Admin function protection

### Input Validation
- All inputs sanitized
- SQL injection prevention
- XSS protection
- File upload restrictions
- Rate limiting implemented

### Security Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

## Compliance Requirements

### GDPR Compliance
- Right of access (Article 15)
- Right to rectification (Article 16)
- Right to erasure (Article 17)
- Right to data portability (Article 20)
- Consent management
- Data breach notification procedures

### Security Best Practices
- OWASP Top 10 protection
- Secure development lifecycle
- Regular security assessments
- Vulnerability management
- Incident response procedures

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  security-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run Backend Security Tests
      run: |
        cd backend
        pip install -r requirements.txt
        pytest tests/security/ --junit-xml=security-results.xml

    - name: Run Frontend Security Tests
      run: |
        cd frontend
        npm install
        npm run test:security

    - name: Run Dependency Audit
      run: |
        npm audit --audit-level moderate
        pip install safety
        safety check

    - name: OWASP ZAP Scan
      run: |
        docker run -t owasp/zap2docker-stable zap-baseline.py \
          -t http://localhost:3000
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database is running
   - Check DATABASE_URL environment variable
   - Verify database permissions

2. **ZAP Integration Issues**
   - Install OWASP ZAP
   - Start ZAP proxy
   - Configure API key
   - Check firewall settings

3. **Dependency Scan Failures**
   - Update npm/pip to latest versions
   - Clear package cache
   - Check network connectivity for vulnerability databases

4. **Test Environment Setup**
   - Use dedicated test environment
   - Isolate from production data
   - Configure appropriate test credentials

### Performance Considerations

- Security tests may take longer than unit tests
- ZAP scans can take 10-30 minutes
- Dependency scans require network access
- Some tests may need dedicated resources

## Maintenance

### Regular Updates
- Update vulnerability databases monthly
- Review and update test cases quarterly
- Update security standards annually
- Monitor for new threat patterns

### Metrics Tracking
- Track security test coverage
- Monitor vulnerability trends
- Measure remediation time
- Assess compliance status

For questions or issues with security tests, contact the security team or review the project documentation.