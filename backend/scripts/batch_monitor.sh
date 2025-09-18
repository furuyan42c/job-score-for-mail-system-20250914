#!/bin/bash

# Batch monitoring script for job matching system
# Usage: ./batch_monitor.sh [check|status|logs|restart|health]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
CONFIG_FILE="${PROJECT_ROOT}/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Notification settings
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_ALERTS="${EMAIL_ALERTS:-admin@company.com}"
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

# Service names
BATCH_SERVICE="job-matching-batch"
API_SERVICE="job-matching-api"
POSTGRES_SERVICE="job-matching-postgres"
REDIS_SERVICE="job-matching-redis"

# Function to log messages with timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Function to log colored messages
log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

# Function to send notifications
send_notification() {
    local message="$1"
    local severity="${2:-info}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL}" ]]; then
        local color="good"
        case "$severity" in
            "error"|"critical") color="danger" ;;
            "warn"|"warning") color="warning" ;;
        esac

        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"Batch Monitor Alert\",\"text\":\"$message\",\"ts\":\"$(date +%s)\"}]}" \
            "${SLACK_WEBHOOK_URL}" > /dev/null || true
    fi

    # Discord notification
    if [[ -n "${DISCORD_WEBHOOK_URL}" ]]; then
        curl -s -H "Content-Type: application/json" \
            -X POST -d "{\"content\":\"🤖 **Batch Monitor**: $message\"}" \
            "${DISCORD_WEBHOOK_URL}" > /dev/null || true
    fi

    # Email notification for critical issues
    if [[ "$severity" == "critical" || "$severity" == "error" ]] && command -v mail >/dev/null; then
        echo -e "Subject: [ALERT] Batch Processing Issue\n\nTimestamp: $timestamp\nSeverity: $severity\n\nMessage: $message" | \
            mail -s "[ALERT] Job Matching Batch Issue" "${EMAIL_ALERTS}" || true
    fi
}

# Function to check Docker container status
check_container_status() {
    local service_name="$1"
    if docker ps --filter "name=${service_name}" --format "table {{.Names}}\t{{.Status}}" | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to get container health status
get_container_health() {
    local service_name="$1"
    docker inspect "${service_name}" --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health-check"
}

# Function to check batch processing status
check_batch_status() {
    log_info "Checking batch processing status..."

    # Check if batch container is running
    if ! check_container_status "${BATCH_SERVICE}"; then
        log_error "Batch service is not running!"
        send_notification "Batch service ${BATCH_SERVICE} is not running" "critical"
        return 1
    fi

    # Check container health
    local health_status=$(get_container_health "${BATCH_SERVICE}")
    case "$health_status" in
        "healthy")
            log_success "Batch service is healthy"
            ;;
        "unhealthy")
            log_error "Batch service is unhealthy"
            send_notification "Batch service ${BATCH_SERVICE} is unhealthy" "error"
            return 1
            ;;
        "starting")
            log_warn "Batch service is starting up"
            ;;
        *)
            log_warn "Batch service health check not available"
            ;;
    esac

    # Check metrics endpoint
    if command -v curl >/dev/null; then
        if curl -s -f "http://localhost:8001/metrics" > /dev/null; then
            log_success "Metrics endpoint is accessible"
        else
            log_error "Metrics endpoint is not accessible"
            send_notification "Batch service metrics endpoint is not accessible" "error"
        fi
    fi

    return 0
}

# Function to monitor resource usage
monitor_resources() {
    log_info "Monitoring resource usage..."

    # Memory usage
    local memory_usage=$(docker stats "${BATCH_SERVICE}" --no-stream --format "table {{.MemUsage}}" | tail -n +2 | awk '{print $1}')
    local memory_limit=$(docker stats "${BATCH_SERVICE}" --no-stream --format "table {{.MemUsage}}" | tail -n +2 | awk '{print $3}')

    if [[ -n "$memory_usage" ]]; then
        log_info "Memory usage: ${memory_usage} / ${memory_limit}"
    fi

    # CPU usage
    local cpu_usage=$(docker stats "${BATCH_SERVICE}" --no-stream --format "table {{.CPUPerc}}" | tail -n +2)
    if [[ -n "$cpu_usage" ]]; then
        log_info "CPU usage: ${cpu_usage}"

        # Alert if CPU usage is high
        local cpu_num=$(echo "$cpu_usage" | sed 's/%//')
        if (( $(echo "$cpu_num > 90" | bc -l) )); then
            send_notification "High CPU usage detected: ${cpu_usage}" "warning"
        fi
    fi

    # Disk usage
    local disk_usage=$(df -h "${LOG_DIR}" | tail -1 | awk '{print $5}' | sed 's/%//')
    log_info "Log directory disk usage: ${disk_usage}%"

    if [[ $disk_usage -gt 80 ]]; then
        log_warn "High disk usage: ${disk_usage}%"
        send_notification "High disk usage in log directory: ${disk_usage}%" "warning"
    fi
}

# Function to check database connectivity
check_database() {
    log_info "Checking database connectivity..."

    if check_container_status "${POSTGRES_SERVICE}"; then
        log_success "PostgreSQL service is running"

        # Test database connection
        if docker exec "${POSTGRES_SERVICE}" pg_isready -q; then
            log_success "Database is accepting connections"
        else
            log_error "Database is not accepting connections"
            send_notification "PostgreSQL database is not accepting connections" "error"
            return 1
        fi
    else
        log_error "PostgreSQL service is not running"
        send_notification "PostgreSQL service is not running" "critical"
        return 1
    fi

    return 0
}

# Function to check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity..."

    if check_container_status "${REDIS_SERVICE}"; then
        log_success "Redis service is running"

        # Test Redis connection
        if docker exec "${REDIS_SERVICE}" redis-cli ping | grep -q "PONG"; then
            log_success "Redis is responding to ping"
        else
            log_error "Redis is not responding"
            send_notification "Redis is not responding to ping" "error"
            return 1
        fi
    else
        log_error "Redis service is not running"
        send_notification "Redis service is not running" "critical"
        return 1
    fi

    return 0
}

# Function to collect logs
collect_logs() {
    local log_file="${LOG_DIR}/batch_monitor_$(date +%Y%m%d_%H%M%S).log"

    log_info "Collecting logs to: $log_file"

    {
        echo "=== Batch Monitor Report ==="
        echo "Timestamp: $(date)"
        echo "Host: $(hostname)"
        echo ""

        echo "=== Container Status ==="
        docker ps --filter "name=job-matching" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""

        echo "=== Resource Usage ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
        echo ""

        echo "=== Recent Batch Logs ==="
        docker logs --tail=100 "${BATCH_SERVICE}" 2>&1 || echo "Failed to retrieve batch logs"
        echo ""

        echo "=== System Resources ==="
        df -h
        echo ""
        free -h
        echo ""

    } > "$log_file"

    log_success "Logs collected: $log_file"
}

# Function to restart batch service
restart_batch_service() {
    log_warn "Restarting batch service..."

    if docker restart "${BATCH_SERVICE}"; then
        log_success "Batch service restarted successfully"
        send_notification "Batch service ${BATCH_SERVICE} has been restarted" "info"

        # Wait for service to be healthy
        local retries=0
        local max_retries=30

        while [[ $retries -lt $max_retries ]]; do
            sleep 10
            if check_container_status "${BATCH_SERVICE}"; then
                local health=$(get_container_health "${BATCH_SERVICE}")
                if [[ "$health" == "healthy" || "$health" == "no-health-check" ]]; then
                    log_success "Service is healthy after restart"
                    return 0
                fi
            fi
            ((retries++))
            log_info "Waiting for service to become healthy... ($retries/$max_retries)"
        done

        log_error "Service did not become healthy within expected time"
        send_notification "Batch service restart completed but service is not healthy" "error"
        return 1
    else
        log_error "Failed to restart batch service"
        send_notification "Failed to restart batch service ${BATCH_SERVICE}" "error"
        return 1
    fi
}

# Function to perform comprehensive health check
comprehensive_health_check() {
    log_info "Starting comprehensive health check..."

    local overall_status=0

    # Check all services
    check_batch_status || overall_status=1
    check_database || overall_status=1
    check_redis || overall_status=1

    # Monitor resources
    monitor_resources

    # Check API service
    if check_container_status "${API_SERVICE}"; then
        log_success "API service is running"
    else
        log_error "API service is not running"
        overall_status=1
    fi

    # Summary
    if [[ $overall_status -eq 0 ]]; then
        log_success "All systems are healthy"
        return 0
    else
        log_error "Some systems are unhealthy"
        return 1
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND]

COMMANDS:
    check       - Perform comprehensive health check
    status      - Show current status of all services
    logs        - Collect and save logs
    restart     - Restart the batch processing service
    health      - Check health of batch service only
    resources   - Monitor resource usage
    help        - Show this help message

ENVIRONMENT VARIABLES:
    SLACK_WEBHOOK_URL   - Slack webhook for notifications
    DISCORD_WEBHOOK_URL - Discord webhook for notifications
    EMAIL_ALERTS        - Email address for critical alerts

EOF
}

# Main script logic
main() {
    local command="${1:-help}"

    # Ensure log directory exists
    mkdir -p "${LOG_DIR}"

    case "$command" in
        "check")
            comprehensive_health_check
            ;;
        "status")
            log_info "Current service status:"
            docker ps --filter "name=job-matching" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            ;;
        "logs")
            collect_logs
            ;;
        "restart")
            restart_batch_service
            ;;
        "health")
            check_batch_status
            ;;
        "resources")
            monitor_resources
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"