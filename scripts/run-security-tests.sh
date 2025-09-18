#!/bin/bash

# Security Test Runner Script
# Comprehensive security testing for the job matching system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
REPORTS_DIR="$PROJECT_ROOT/reports/security"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."

    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        cd "$BACKEND_DIR"

        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi

        # Activate virtual environment
        source venv/bin/activate

        # Install dependencies
        pip install -r requirements.txt

        # Install security testing tools
        pip install safety bandit semgrep

        print_success "Python environment ready"
    else
        print_warning "No requirements.txt found, skipping Python setup"
    fi
}

# Function to setup Node.js environment
setup_node_env() {
    print_status "Setting up Node.js environment..."

    if [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"

        # Install dependencies
        npm install

        # Install security testing tools
        npm install -g audit-ci license-checker retire

        print_success "Node.js environment ready"
    else
        print_warning "No package.json found, skipping Node.js setup"
    fi
}

# Function to run backend security tests
run_backend_security_tests() {
    print_status "Running backend security tests..."

    cd "$BACKEND_DIR"

    # Activate Python virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Run pytest security tests
    print_status "Running pytest security tests..."
    pytest tests/security/ -v --tb=short --junit-xml="$REPORTS_DIR/backend-security-results.xml" || {
        print_error "Backend security tests failed"
        return 1
    }

    # Run Bandit security linter
    if command_exists bandit; then
        print_status "Running Bandit security linter..."
        bandit -r app/ -f json -o "$REPORTS_DIR/bandit-report.json" || {
            print_warning "Bandit found security issues"
        }
    fi

    # Run Python Safety check
    if command_exists safety; then
        print_status "Running Python Safety check..."
        safety check --json --output "$REPORTS_DIR/python-safety-report.json" || {
            print_warning "Python Safety found vulnerabilities"
        }
    fi

    # Run Semgrep security scan
    if command_exists semgrep; then
        print_status "Running Semgrep security scan..."
        semgrep --config=auto --json --output="$REPORTS_DIR/semgrep-report.json" app/ || {
            print_warning "Semgrep found security issues"
        }
    fi

    print_success "Backend security tests completed"
}

# Function to run frontend security tests
run_frontend_security_tests() {
    print_status "Running frontend security tests..."

    cd "$FRONTEND_DIR"

    # Run Playwright security tests
    if [ -f "playwright.config.ts" ]; then
        print_status "Running Playwright security tests..."
        npx playwright test tests/security/ --reporter=junit:"$REPORTS_DIR/frontend-security-results.xml" || {
            print_error "Frontend security tests failed"
            return 1
        }
    fi

    # Run npm audit
    print_status "Running npm audit..."
    npm audit --audit-level moderate --json > "$REPORTS_DIR/npm-audit-report.json" || {
        print_warning "npm audit found vulnerabilities"
    }

    # Run audit-ci for CI/CD integration
    if command_exists audit-ci; then
        print_status "Running audit-ci..."
        audit-ci --moderate || {
            print_warning "audit-ci found moderate vulnerabilities"
        }
    fi

    # Run Retire.js for known vulnerable JavaScript libraries
    if command_exists retire; then
        print_status "Running Retire.js scan..."
        retire --outputformat json --outputpath "$REPORTS_DIR/retire-report.json" || {
            print_warning "Retire.js found vulnerable libraries"
        }
    fi

    # Check licenses
    if command_exists license-checker; then
        print_status "Checking licenses..."
        license-checker --json > "$REPORTS_DIR/license-report.json"
    fi

    print_success "Frontend security tests completed"
}

# Function to run OWASP ZAP scan
run_zap_scan() {
    if [ "$SKIP_ZAP" = "true" ]; then
        print_warning "Skipping OWASP ZAP scan (SKIP_ZAP=true)"
        return 0
    fi

    print_status "Running OWASP ZAP security scan..."

    # Check if ZAP is available
    if command_exists zap.sh; then
        ZAP_CMD="zap.sh"
    elif command_exists docker; then
        print_status "Using Docker for OWASP ZAP..."

        # Check if target URL is provided
        TARGET_URL=${TARGET_URL:-"http://localhost:3000"}

        # Run ZAP baseline scan
        docker run -t owasp/zap2docker-stable zap-baseline.py \
            -t "$TARGET_URL" \
            -J "$REPORTS_DIR/zap-baseline-report.json" \
            -r "$REPORTS_DIR/zap-baseline-report.html" || {
            print_warning "OWASP ZAP baseline scan found issues"
        }

        return 0
    else
        print_warning "OWASP ZAP not available, skipping scan"
        return 0
    fi
}

# Function to run dependency checks
run_dependency_checks() {
    print_status "Running comprehensive dependency checks..."

    # Create dependency report
    echo "# Dependency Security Report" > "$REPORTS_DIR/dependency-summary.md"
    echo "Generated: $(date)" >> "$REPORTS_DIR/dependency-summary.md"
    echo "" >> "$REPORTS_DIR/dependency-summary.md"

    # Check Python dependencies
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        echo "## Python Dependencies" >> "$REPORTS_DIR/dependency-summary.md"

        cd "$BACKEND_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi

        # List installed packages
        pip list --format=json > "$REPORTS_DIR/python-packages.json"

        # Check for outdated packages
        pip list --outdated --format=json > "$REPORTS_DIR/python-outdated.json"

        echo "- Total packages: $(jq length "$REPORTS_DIR/python-packages.json")" >> "$REPORTS_DIR/dependency-summary.md"
        echo "- Outdated packages: $(jq length "$REPORTS_DIR/python-outdated.json")" >> "$REPORTS_DIR/dependency-summary.md"
    fi

    # Check Node.js dependencies
    if [ -f "$FRONTEND_DIR/package.json" ]; then
        echo "## Node.js Dependencies" >> "$REPORTS_DIR/dependency-summary.md"

        cd "$FRONTEND_DIR"

        # List installed packages
        npm list --json > "$REPORTS_DIR/npm-packages.json" 2>/dev/null || true

        # Check for outdated packages
        npm outdated --json > "$REPORTS_DIR/npm-outdated.json" 2>/dev/null || true

        echo "- Dependencies listed in package.json: $(jq '.dependencies | length' package.json)" >> "$REPORTS_DIR/dependency-summary.md"
        echo "- Dev dependencies: $(jq '.devDependencies | length' package.json)" >> "$REPORTS_DIR/dependency-summary.md"
    fi

    print_success "Dependency checks completed"
}

# Function to generate security summary report
generate_summary_report() {
    print_status "Generating security summary report..."

    SUMMARY_FILE="$REPORTS_DIR/security-summary.md"

    cat > "$SUMMARY_FILE" << EOF
# Security Test Summary Report

**Generated:** $(date)
**Project:** Job Matching System Security Tests

## Test Results Overview

### Backend Security Tests
- **SQL Injection Prevention:** $([ -f "$REPORTS_DIR/backend-security-results.xml" ] && echo "✅ Completed" || echo "❌ Failed")
- **Authentication & Authorization:** $([ -f "$REPORTS_DIR/backend-security-results.xml" ] && echo "✅ Completed" || echo "❌ Failed")
- **Data Encryption:** $([ -f "$REPORTS_DIR/backend-security-results.xml" ] && echo "✅ Completed" || echo "❌ Failed")
- **Vulnerability Scanning:** $([ -f "$REPORTS_DIR/backend-security-results.xml" ] && echo "✅ Completed" || echo "❌ Failed")
- **Compliance Testing:** $([ -f "$REPORTS_DIR/backend-security-results.xml" ] && echo "✅ Completed" || echo "❌ Failed")

### Frontend Security Tests
- **OWASP ZAP Integration:** $([ -f "$REPORTS_DIR/zap-baseline-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")
- **Dependency Vulnerability Checks:** $([ -f "$REPORTS_DIR/npm-audit-report.json" ] && echo "✅ Completed" || echo "❌ Failed")

### Security Tools Results
- **Bandit (Python):** $([ -f "$REPORTS_DIR/bandit-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")
- **Safety (Python):** $([ -f "$REPORTS_DIR/python-safety-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")
- **Semgrep:** $([ -f "$REPORTS_DIR/semgrep-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")
- **npm audit:** $([ -f "$REPORTS_DIR/npm-audit-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")
- **Retire.js:** $([ -f "$REPORTS_DIR/retire-report.json" ] && echo "✅ Completed" || echo "⚠️ Skipped")

## Files Generated
EOF

    # List all generated files
    echo "" >> "$SUMMARY_FILE"
    echo "### Report Files" >> "$SUMMARY_FILE"
    for file in "$REPORTS_DIR"/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            filesize=$(du -h "$file" | cut -f1)
            echo "- **$filename** ($filesize)" >> "$SUMMARY_FILE"
        fi
    done

    echo "" >> "$SUMMARY_FILE"
    echo "## Next Steps" >> "$SUMMARY_FILE"
    echo "1. Review all generated reports for security issues" >> "$SUMMARY_FILE"
    echo "2. Address any high or critical vulnerabilities found" >> "$SUMMARY_FILE"
    echo "3. Update dependencies with known vulnerabilities" >> "$SUMMARY_FILE"
    echo "4. Implement additional security controls as needed" >> "$SUMMARY_FILE"
    echo "5. Schedule regular security testing" >> "$SUMMARY_FILE"

    print_success "Security summary report generated: $SUMMARY_FILE"
}

# Function to check exit codes and determine overall result
check_overall_result() {
    local exit_code=0

    # Check for critical security issues
    if [ -f "$REPORTS_DIR/bandit-report.json" ]; then
        high_severity=$(jq '[.results[] | select(.issue_severity == "HIGH")] | length' "$REPORTS_DIR/bandit-report.json" 2>/dev/null || echo "0")
        if [ "$high_severity" -gt 0 ]; then
            print_error "Found $high_severity high-severity security issues in Bandit scan"
            exit_code=1
        fi
    fi

    if [ -f "$REPORTS_DIR/python-safety-report.json" ]; then
        vulnerabilities=$(jq '. | length' "$REPORTS_DIR/python-safety-report.json" 2>/dev/null || echo "0")
        if [ "$vulnerabilities" -gt 0 ]; then
            print_error "Found $vulnerabilities Python package vulnerabilities"
            exit_code=1
        fi
    fi

    if [ -f "$REPORTS_DIR/npm-audit-report.json" ]; then
        critical_vulns=$(jq '.metadata.vulnerabilities.critical' "$REPORTS_DIR/npm-audit-report.json" 2>/dev/null || echo "0")
        high_vulns=$(jq '.metadata.vulnerabilities.high' "$REPORTS_DIR/npm-audit-report.json" 2>/dev/null || echo "0")

        if [ "$critical_vulns" -gt 0 ]; then
            print_error "Found $critical_vulns critical npm vulnerabilities"
            exit_code=1
        fi

        if [ "$high_vulns" -gt 2 ]; then
            print_error "Found $high_vulns high-severity npm vulnerabilities (threshold: 2)"
            exit_code=1
        fi
    fi

    return $exit_code
}

# Main execution
main() {
    print_status "Starting comprehensive security testing..."
    print_status "Project root: $PROJECT_ROOT"
    print_status "Reports will be saved to: $REPORTS_DIR"

    # Setup environments
    setup_python_env
    setup_node_env

    # Run security tests
    run_backend_security_tests
    run_frontend_security_tests

    # Run additional security tools
    run_dependency_checks
    run_zap_scan

    # Generate summary
    generate_summary_report

    # Check overall result
    if check_overall_result; then
        print_success "All security tests completed successfully!"
        print_status "Review the reports in: $REPORTS_DIR"
        exit 0
    else
        print_error "Security tests found critical issues!"
        print_status "Review the reports in: $REPORTS_DIR"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --backend-only      Run only backend security tests"
        echo "  --frontend-only     Run only frontend security tests"
        echo "  --no-zap           Skip OWASP ZAP scan"
        echo ""
        echo "Environment variables:"
        echo "  TARGET_URL         Target URL for ZAP scan (default: http://localhost:3000)"
        echo "  SKIP_ZAP           Set to 'true' to skip ZAP scan"
        exit 0
        ;;
    --backend-only)
        setup_python_env
        run_backend_security_tests
        run_dependency_checks
        generate_summary_report
        check_overall_result
        exit $?
        ;;
    --frontend-only)
        setup_node_env
        run_frontend_security_tests
        run_dependency_checks
        generate_summary_report
        check_overall_result
        exit $?
        ;;
    --no-zap)
        export SKIP_ZAP=true
        main
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac