#!/bin/bash

# Production deployment script for job matching system
# Usage: ./deploy.sh [environment] [version]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"
REGISTRY_URL="${REGISTRY_URL:-your-registry.com}"
IMAGE_NAME="job-matching"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check environment file
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_error "Environment file .env not found"
        log_info "Copy .env.docker to .env and configure for your environment"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Function to build Docker images
build_images() {
    log_info "Building Docker images..."

    # Build main application image
    docker build -t "${IMAGE_NAME}:${VERSION}" \
        -t "${IMAGE_NAME}:latest" \
        --target base \
        "${PROJECT_ROOT}/backend"

    # Build batch processor image
    docker build -t "${IMAGE_NAME}-batch:${VERSION}" \
        -t "${IMAGE_NAME}-batch:latest" \
        --target batch-processor \
        "${PROJECT_ROOT}/backend"

    log_success "Docker images built successfully"
}

# Function to run tests
run_tests() {
    log_info "Running tests..."

    # Create test environment
    docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" \
        -f "${PROJECT_ROOT}/docker-compose.test.yml" \
        up -d postgres redis

    # Wait for services to be ready
    sleep 10

    # Run tests
    docker run --rm \
        --network "$(basename "$PROJECT_ROOT")_job-matching-network" \
        -e DATABASE_URL="postgresql://postgres:password@postgres:5432/job_matching_test" \
        -e REDIS_URL="redis://:redispassword@redis:6379/1" \
        "${IMAGE_NAME}:${VERSION}" \
        python -m pytest tests/ -v --cov=app --cov-report=term-missing

    # Cleanup test environment
    docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" \
        -f "${PROJECT_ROOT}/docker-compose.test.yml" \
        down -v

    log_success "Tests passed"
}

# Function to deploy to production
deploy_production() {
    log_info "Deploying to production..."

    # Backup current database
    log_info "Creating database backup..."
    docker exec job-matching-postgres pg_dump -U postgres job_matching > \
        "${PROJECT_ROOT}/database/backups/pre-deploy-$(date +%Y%m%d_%H%M%S).sql"

    # Create deployment directory
    mkdir -p /opt/job-matching

    # Copy configuration files
    cp "${PROJECT_ROOT}/docker-compose.yml" /opt/job-matching/
    cp "${PROJECT_ROOT}/.env" /opt/job-matching/
    cp -r "${PROJECT_ROOT}/backend/monitoring" /opt/job-matching/

    # Pull latest images (if using registry)
    if [[ "${VERSION}" != "latest" ]]; then
        docker pull "${REGISTRY_URL}/${IMAGE_NAME}:${VERSION}" || build_images
        docker pull "${REGISTRY_URL}/${IMAGE_NAME}-batch:${VERSION}" || build_images
    fi

    # Deploy with blue-green deployment
    cd /opt/job-matching

    # Start new services
    docker-compose up -d --scale api=2 --scale batch-processor=1

    # Health check
    log_info "Performing health checks..."
    local retries=0
    local max_retries=30

    while [[ $retries -lt $max_retries ]]; do
        if curl -f "http://localhost:8000/health" > /dev/null 2>&1; then
            log_success "Health check passed"
            break
        fi
        sleep 10
        ((retries++))
        log_info "Waiting for services to be healthy... ($retries/$max_retries)"
    done

    if [[ $retries -eq $max_retries ]]; then
        log_error "Health check failed - rolling back"
        rollback_deployment
        exit 1
    fi

    # Update load balancer (if using one)
    # update_load_balancer

    log_success "Production deployment completed"
}

# Function to deploy to staging
deploy_staging() {
    log_info "Deploying to staging..."

    cd "${PROJECT_ROOT}"

    # Use override for staging
    docker-compose -f docker-compose.yml \
        -f docker-compose.staging.yml \
        up -d --build

    # Wait for services
    sleep 30

    # Run smoke tests
    docker run --rm \
        --network "$(basename "$PROJECT_ROOT")_job-matching-network" \
        "${IMAGE_NAME}:${VERSION}" \
        python -m pytest tests/smoke/ -v

    log_success "Staging deployment completed"
}

# Function to rollback deployment
rollback_deployment() {
    log_warn "Rolling back deployment..."

    # Get previous version from backup
    local backup_file=$(ls -t "${PROJECT_ROOT}/database/backups/" | head -n 2 | tail -n 1)

    if [[ -n "$backup_file" ]]; then
        log_info "Restoring database from backup: $backup_file"
        docker exec -i job-matching-postgres psql -U postgres -d job_matching < \
            "${PROJECT_ROOT}/database/backups/${backup_file}"
    fi

    # Restart previous containers
    docker-compose restart

    log_success "Rollback completed"
}

# Function to setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."

    # Create monitoring directories
    mkdir -p /opt/job-matching/monitoring/data/{prometheus,grafana,alertmanager}

    # Set proper permissions
    chown -R 472:472 /opt/job-matching/monitoring/data/grafana  # Grafana user
    chown -R 65534:65534 /opt/job-matching/monitoring/data/prometheus  # nobody user

    # Start monitoring services
    docker-compose up -d prometheus grafana alertmanager

    # Import Grafana dashboards
    sleep 30
    # curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3001/api/dashboards/db \
    #     -H "Content-Type: application/json" \
    #     -d @"${PROJECT_ROOT}/backend/monitoring/grafana/dashboards/batch-processing.json"

    log_success "Monitoring setup completed"
}

# Function to perform security scan
security_scan() {
    log_info "Running security scan..."

    # Scan Docker images for vulnerabilities
    if command -v trivy &> /dev/null; then
        trivy image "${IMAGE_NAME}:${VERSION}"
        trivy image "${IMAGE_NAME}-batch:${VERSION}"
    else
        log_warn "Trivy not installed - skipping security scan"
    fi

    # Check for secrets in code
    if command -v gitleaks &> /dev/null; then
        gitleaks detect --source="${PROJECT_ROOT}" --verbose
    else
        log_warn "Gitleaks not installed - skipping secrets scan"
    fi

    log_success "Security scan completed"
}

# Main deployment function
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT, version: $VERSION"

    check_prerequisites

    case "$ENVIRONMENT" in
        "production")
            security_scan
            build_images
            run_tests
            deploy_production
            setup_monitoring
            ;;
        "staging")
            build_images
            run_tests
            deploy_staging
            ;;
        "development")
            log_info "Development deployment - using docker-compose up"
            cd "${PROJECT_ROOT}"
            docker-compose up -d --build
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            log_info "Supported environments: production, staging, development"
            exit 1
            ;;
    esac

    log_success "Deployment completed successfully"
    log_info "Access points:"
    log_info "  - API: http://localhost:8000"
    log_info "  - Grafana: http://localhost:3001"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - AlertManager: http://localhost:9093"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    # Add cleanup logic here
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"