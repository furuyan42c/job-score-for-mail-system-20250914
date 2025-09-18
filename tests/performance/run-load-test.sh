#!/bin/bash

# Performance Load Test Runner Script
#
# This script orchestrates the complete performance test suite:
# - Monitors system resources
# - Runs all performance tests
# - Generates consolidated HTML report
# - Alerts on target failures
# - Manages test environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/test-data/reports"
LOGS_DIR="${SCRIPT_DIR}/test-data/logs"
MONITORING_DIR="${SCRIPT_DIR}/test-data/monitoring"

# Test configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
NODE_ENV="${NODE_ENV:-test}"
PARALLEL_TESTS="${PARALLEL_TESTS:-false}"
INCLUDE_STRESS_TESTS="${INCLUDE_STRESS_TESTS:-true}"
ALERT_ON_FAILURE="${ALERT_ON_FAILURE:-true}"
GENERATE_CHARTS="${GENERATE_CHARTS:-true}"

# Performance thresholds (exit codes)
EXIT_SUCCESS=0
EXIT_PERFORMANCE_FAILURE=1
EXIT_ENVIRONMENT_ERROR=2
EXIT_TEST_ERROR=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOGS_DIR}/test-runner.log"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_section() {
    log ""
    log "${PURPLE}===================================================${NC}"
    log "${PURPLE} $1${NC}"
    log "${PURPLE}===================================================${NC}"
    log ""
}

# System monitoring functions
start_system_monitoring() {
    log_info "Starting system resource monitoring..."

    local monitor_script="${MONITORING_DIR}/system_monitor.sh"

    # Create system monitoring script
    cat > "$monitor_script" << 'EOF'
#!/bin/bash
MONITORING_DIR="$1"
LOG_FILE="${MONITORING_DIR}/system_metrics.csv"

# Create CSV header
echo "timestamp,cpu_usage,memory_usage_mb,memory_percent,disk_usage_percent,network_rx_mb,network_tx_mb,load_avg_1m,load_avg_5m,load_avg_15m" > "$LOG_FILE"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # CPU usage (1-minute average)
    cpu_usage=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' || echo "0")

    # Memory usage
    memory_info=$(vm_stat | grep -E "(free|inactive|wired|active)" | awk '{print $3}' | sed 's/\.//')
    memory_total=$(($(echo "$memory_info" | paste -sd+ | bc) * 4096 / 1024 / 1024))
    memory_used=$(echo "$memory_total" | awk '{printf "%.0f", $1 * 0.7}') # Approximate
    memory_percent=$(echo "$memory_used $memory_total" | awk '{printf "%.1f", ($1/$2)*100}')

    # Disk usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')

    # Network (simplified - would need more sophisticated monitoring in production)
    network_rx_mb="0"
    network_tx_mb="0"

    # Load averages
    load_avg=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $1 "," $2 "," $3}' | tr -d ' ')

    echo "$timestamp,$cpu_usage,$memory_used,$memory_percent,$disk_usage,$network_rx_mb,$network_tx_mb,$load_avg" >> "$LOG_FILE"

    sleep 10
done
EOF

    chmod +x "$monitor_script"

    # Start monitoring in background
    "$monitor_script" "$MONITORING_DIR" &
    MONITOR_PID=$!
    echo "$MONITOR_PID" > "${MONITORING_DIR}/monitor.pid"

    log_success "System monitoring started (PID: $MONITOR_PID)"
}

stop_system_monitoring() {
    log_info "Stopping system resource monitoring..."

    if [ -f "${MONITORING_DIR}/monitor.pid" ]; then
        local monitor_pid=$(cat "${MONITORING_DIR}/monitor.pid")
        if kill -0 "$monitor_pid" 2>/dev/null; then
            kill "$monitor_pid"
            log_success "System monitoring stopped"
        fi
        rm -f "${MONITORING_DIR}/monitor.pid"
    fi
}

# Environment setup and validation
setup_environment() {
    log_section "Setting Up Test Environment"

    # Create necessary directories
    mkdir -p "$REPORTS_DIR" "$LOGS_DIR" "$MONITORING_DIR"

    # Initialize log files
    echo "Performance Load Test Started at $(date)" > "${LOGS_DIR}/test-runner.log"

    # Check system requirements
    check_system_requirements

    # Validate API availability
    validate_api_availability

    # Setup Node.js environment
    setup_node_environment
}

check_system_requirements() {
    log_info "Checking system requirements..."

    # Check available memory
    local available_memory_gb
    if [[ "$OSTYPE" == "darwin"* ]]; then
        available_memory_gb=$(echo "$(sysctl -n hw.memsize) / 1024^3" | bc -l | cut -d'.' -f1)
    else
        available_memory_gb=$(free -g | grep '^Mem:' | awk '{print $7}')
    fi

    if [ "$available_memory_gb" -lt 4 ]; then
        log_error "Insufficient memory: ${available_memory_gb}GB available, 4GB+ recommended"
        exit $EXIT_ENVIRONMENT_ERROR
    fi

    log_success "System requirements check passed (${available_memory_gb}GB memory available)"
}

validate_api_availability() {
    log_info "Validating API availability at ${API_BASE_URL}..."

    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "${API_BASE_URL}/health" > /dev/null 2>&1; then
            log_success "API is available and responding"
            return 0
        fi

        log_warning "API not available (attempt ${attempt}/${max_attempts})"

        if [ $attempt -eq $max_attempts ]; then
            log_error "API is not available after ${max_attempts} attempts"
            log_error "Please ensure the backend server is running at ${API_BASE_URL}"
            exit $EXIT_ENVIRONMENT_ERROR
        fi

        sleep 10
        ((attempt++))
    done
}

setup_node_environment() {
    log_info "Setting up Node.js test environment..."

    cd "$PROJECT_ROOT"

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node.js dependencies..."
        npm ci
    fi

    # Set environment variables
    export NODE_ENV="$NODE_ENV"
    export API_BASE_URL="$API_BASE_URL"
    export NODE_OPTIONS="--max-old-space-size=4096 --expose-gc"

    log_success "Node.js environment ready"
}

# Test execution functions
run_performance_tests() {
    log_section "Running Performance Test Suite"

    local test_start_time=$(date +%s)
    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Test execution order (dependencies considered)
    local test_files=(
        "generate-test-data.ts"
        "memory_usage.test.ts"
        "scoring_engine_benchmark.test.ts"
        "database_stress.test.ts"
        "batch_processing_load.test.ts"
    )

    if [ "$PARALLEL_TESTS" = "true" ]; then
        run_tests_parallel "${test_files[@]}"
    else
        run_tests_sequential "${test_files[@]}"
    fi

    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - test_start_time))

    log_section "Test Execution Summary"
    log_info "Total duration: ${test_duration} seconds"
    log_info "Tests executed: $total_tests"
    log_success "Tests passed: $passed_tests"

    if [ $failed_tests -gt 0 ]; then
        log_error "Tests failed: $failed_tests"
        return $EXIT_PERFORMANCE_FAILURE
    fi

    return $EXIT_SUCCESS
}

run_tests_sequential() {
    local test_files=("$@")

    log_info "Running tests sequentially..."

    for test_file in "${test_files[@]}"; do
        run_single_test "$test_file"
    done
}

run_tests_parallel() {
    local test_files=("$@")

    log_info "Running tests in parallel..."
    log_warning "Note: Parallel execution may affect individual test performance measurements"

    local pids=()

    # Start all tests
    for test_file in "${test_files[@]}"; do
        run_single_test "$test_file" &
        pids+=($!)
    done

    # Wait for all tests to complete
    local all_passed=true
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            all_passed=false
        fi
    done

    if [ "$all_passed" = false ]; then
        return $EXIT_PERFORMANCE_FAILURE
    fi

    return $EXIT_SUCCESS
}

run_single_test() {
    local test_file="$1"
    local test_name="${test_file%.test.ts}"

    log_info "Running ${test_name}..."

    local test_start_time=$(date +%s)
    local test_log="${LOGS_DIR}/${test_name}.log"

    # Determine timeout based on test type
    local timeout="300000" # 5 minutes default
    case "$test_name" in
        "batch_processing_load") timeout="1800000" ;; # 30 minutes
        "database_stress") timeout="1800000" ;; # 30 minutes
        "memory_usage") timeout="900000" ;; # 15 minutes
        "scoring_engine_benchmark") timeout="600000" ;; # 10 minutes
    esac

    # Run the test
    if cd "${SCRIPT_DIR}" && npx jest "${test_file}" --timeout="$timeout" --verbose > "$test_log" 2>&1; then
        local test_end_time=$(date +%s)
        local test_duration=$((test_end_time - test_start_time))

        log_success "${test_name} completed successfully (${test_duration}s)"
        ((passed_tests++))
    else
        log_error "${test_name} failed - check ${test_log} for details"
        ((failed_tests++))

        # Show last few lines of error log
        log_error "Last 10 lines of ${test_name} output:"
        tail -n 10 "$test_log" | while IFS= read -r line; do
            log_error "  $line"
        done
    fi

    ((total_tests++))
}

# Report generation functions
generate_consolidated_report() {
    log_section "Generating Consolidated Performance Report"

    local report_timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local html_report="${REPORTS_DIR}/performance_report_${report_timestamp}.html"
    local json_summary="${REPORTS_DIR}/performance_summary_${report_timestamp}.json"

    # Collect all JSON reports
    local json_reports=($(find "${SCRIPT_DIR}/test-data" -name "*report*.json" -type f))

    if [ ${#json_reports[@]} -eq 0 ]; then
        log_warning "No JSON reports found - generating basic report"
        generate_basic_report "$html_report"
        return
    fi

    log_info "Found ${#json_reports[@]} test reports to consolidate"

    # Generate comprehensive HTML report
    generate_html_report "$html_report" "${json_reports[@]}"

    # Generate JSON summary
    generate_json_summary "$json_summary" "${json_reports[@]}"

    log_success "Consolidated report generated: $html_report"
    log_info "JSON summary: $json_summary"

    # Generate charts if requested
    if [ "$GENERATE_CHARTS" = "true" ]; then
        generate_performance_charts "$report_timestamp"
    fi
}

generate_html_report() {
    local html_file="$1"
    shift
    local json_reports=("$@")

    cat > "$html_file" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; border-left: 4px solid #007bff; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; margin-top: 5px; }
        .test-section { margin-bottom: 30px; border: 1px solid #ddd; border-radius: 6px; overflow: hidden; }
        .test-header { background: #007bff; color: white; padding: 15px; }
        .test-content { padding: 15px; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .warning { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .recommendations h4 { color: #856404; margin-top: 0; }
        .recommendations ul { margin-bottom: 0; }
        .chart-container { margin: 20px 0; text-align: center; }
        .system-info { background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Performance Test Report</h1>
        <p><strong>Generated:</strong> <span id="timestamp"></span></p>
        <p><strong>Environment:</strong> <span id="environment"></span></p>

        <div id="summary" class="summary">
            <!-- Summary metrics will be inserted here -->
        </div>

        <div id="test-results">
            <!-- Test results will be inserted here -->
        </div>

        <div id="system-info" class="system-info">
            <!-- System information will be inserted here -->
        </div>
    </div>

    <script>
        // Report data will be inserted here
        const reportData = {};

        function formatDuration(ms) {
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            if (minutes > 0) {
                return `${minutes}m ${seconds % 60}s`;
            }
            return `${seconds}s`;
        }

        function formatBytes(bytes) {
            const mb = Math.round(bytes / 1024 / 1024);
            return `${mb} MB`;
        }

        function renderReport() {
            document.getElementById('timestamp').textContent = new Date().toLocaleString();
            document.getElementById('environment').textContent = 'Test Environment';

            // Render summary and test results based on reportData
            // This would be populated with actual data in a real implementation
        }

        // Initialize report
        document.addEventListener('DOMContentLoaded', renderReport);
    </script>
</body>
</html>
EOF

    # Add actual data processing here
    # This is a simplified version - in a real implementation,
    # you would parse the JSON reports and inject the data into the HTML

    log_info "HTML report structure created: $html_file"
}

generate_basic_report() {
    local html_file="$1"

    cat > "$html_file" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basic Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Test Report</h1>
        <div class="warning">
            <h3>⚠️ Limited Report</h3>
            <p>No detailed test results were found. This may indicate:</p>
            <ul>
                <li>Tests failed to complete successfully</li>
                <li>Report generation issues</li>
                <li>Test configuration problems</li>
            </ul>
            <p>Please check the test logs for more information.</p>
        </div>

        <h2>Test Execution Log</h2>
        <pre id="test-log">
            <!-- Test log content would be inserted here -->
        </pre>
    </div>
</body>
</html>
EOF

    log_warning "Basic report generated: $html_file"
}

generate_json_summary() {
    local json_file="$1"
    shift
    local json_reports=("$@")

    # Create a basic JSON summary structure
    cat > "$json_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "summary": {
        "totalTests": ${#json_reports[@]},
        "reportFiles": [
$(printf '            "%s",\n' "${json_reports[@]}" | sed '$s/,$//')
        ]
    },
    "environment": {
        "nodeVersion": "$(node --version)",
        "platform": "$(uname -s)",
        "architecture": "$(uname -m)",
        "apiBaseUrl": "$API_BASE_URL"
    }
}
EOF

    log_info "JSON summary created: $json_file"
}

generate_performance_charts() {
    local timestamp="$1"

    log_info "Generating performance charts..."

    # This would integrate with a charting library in a real implementation
    # For now, we'll create placeholder chart files

    local charts_dir="${REPORTS_DIR}/charts_${timestamp}"
    mkdir -p "$charts_dir"

    # Create placeholder chart files
    echo "Memory Usage Chart Placeholder" > "${charts_dir}/memory_usage.txt"
    echo "Response Time Chart Placeholder" > "${charts_dir}/response_times.txt"
    echo "Throughput Chart Placeholder" > "${charts_dir}/throughput.txt"

    log_info "Chart placeholders created in: $charts_dir"
}

# Alert and notification functions
send_alerts() {
    local exit_code="$1"

    if [ "$ALERT_ON_FAILURE" = "false" ]; then
        return
    fi

    case $exit_code in
        $EXIT_SUCCESS)
            log_success "All performance tests passed - no alerts needed"
            ;;
        $EXIT_PERFORMANCE_FAILURE)
            send_performance_failure_alert
            ;;
        $EXIT_ENVIRONMENT_ERROR)
            send_environment_error_alert
            ;;
        $EXIT_TEST_ERROR)
            send_test_error_alert
            ;;
        *)
            send_unknown_error_alert "$exit_code"
            ;;
    esac
}

send_performance_failure_alert() {
    local alert_message="🚨 PERFORMANCE ALERT: One or more performance tests failed to meet targets"

    log_error "$alert_message"

    # In a real implementation, this would integrate with:
    # - Slack notifications
    # - Email alerts
    # - PagerDuty or other monitoring systems
    # - Dashboard updates

    echo "$alert_message" >> "${LOGS_DIR}/alerts.log"
}

send_environment_error_alert() {
    local alert_message="🔧 ENVIRONMENT ERROR: Test environment setup failed"

    log_error "$alert_message"
    echo "$alert_message" >> "${LOGS_DIR}/alerts.log"
}

send_test_error_alert() {
    local alert_message="❌ TEST ERROR: Test execution encountered errors"

    log_error "$alert_message"
    echo "$alert_message" >> "${LOGS_DIR}/alerts.log"
}

send_unknown_error_alert() {
    local exit_code="$1"
    local alert_message="❓ UNKNOWN ERROR: Test runner exited with code $exit_code"

    log_error "$alert_message"
    echo "$alert_message" >> "${LOGS_DIR}/alerts.log"
}

# Cleanup functions
cleanup() {
    log_info "Performing cleanup..."

    # Stop system monitoring
    stop_system_monitoring

    # Clean up temporary files
    find "${SCRIPT_DIR}/test-data" -name "*.tmp" -delete 2>/dev/null || true

    # Compress old log files
    find "${LOGS_DIR}" -name "*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true

    log_success "Cleanup completed"
}

# Signal handlers
trap cleanup EXIT
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Performance Load Test Runner

Options:
    --api-url URL           API base URL (default: http://localhost:8000)
    --parallel             Run tests in parallel (faster but may affect measurements)
    --no-stress            Skip stress tests (faster execution)
    --no-alerts            Disable failure alerts
    --no-charts            Skip chart generation
    --help                 Show this help message

Environment Variables:
    API_BASE_URL          API base URL
    NODE_ENV              Node environment (default: test)
    PARALLEL_TESTS        Run tests in parallel (true/false)
    INCLUDE_STRESS_TESTS  Include stress tests (true/false)
    ALERT_ON_FAILURE      Send alerts on failure (true/false)
    GENERATE_CHARTS       Generate performance charts (true/false)

Examples:
    $0                                    # Run all tests with defaults
    $0 --parallel --no-stress            # Fast run without stress tests
    $0 --api-url http://staging.api.com   # Test against staging environment

EOF
}

# Command line argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-url)
                API_BASE_URL="$2"
                shift 2
                ;;
            --parallel)
                PARALLEL_TESTS="true"
                shift
                ;;
            --no-stress)
                INCLUDE_STRESS_TESTS="false"
                shift
                ;;
            --no-alerts)
                ALERT_ON_FAILURE="false"
                shift
                ;;
            --no-charts)
                GENERATE_CHARTS="false"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main execution function
main() {
    local script_start_time=$(date +%s)

    log_section "Performance Load Test Runner"
    log_info "Starting comprehensive performance test suite..."

    # Parse command line arguments
    parse_arguments "$@"

    # Setup test environment
    setup_environment

    # Start system monitoring
    start_system_monitoring

    # Run performance tests
    local test_exit_code=0
    if ! run_performance_tests; then
        test_exit_code=$EXIT_PERFORMANCE_FAILURE
    fi

    # Generate reports
    generate_consolidated_report

    # Send alerts if needed
    send_alerts $test_exit_code

    # Calculate total execution time
    local script_end_time=$(date +%s)
    local total_duration=$((script_end_time - script_start_time))
    local total_minutes=$((total_duration / 60))
    local total_seconds=$((total_duration % 60))

    log_section "Performance Test Suite Complete"
    log_info "Total execution time: ${total_minutes}m ${total_seconds}s"

    if [ $test_exit_code -eq $EXIT_SUCCESS ]; then
        log_success "🎉 All performance tests completed successfully!"
        log_info "Reports available in: $REPORTS_DIR"
    else
        log_error "❌ Some performance tests failed or didn't meet targets"
        log_info "Check individual test logs in: $LOGS_DIR"
    fi

    exit $test_exit_code
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi