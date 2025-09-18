# Makefile for Job Matching System DevOps Operations

.PHONY: help build up down logs test deploy monitor clean backup restore security

# Default environment
ENV ?= development
VERSION ?= latest

# Colors for help
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Job Matching System - DevOps Operations$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Build completed$(NC)"

up: ## Start all services in development mode
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started$(NC)"
	@echo "Access points:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Grafana: http://localhost:3001 (admin/dev123)"
	@echo "  - Prometheus: http://localhost:9090"

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Services stopped$(NC)"

logs: ## Follow logs from all services
	docker-compose logs -f

logs-batch: ## Follow logs from batch processor only
	docker-compose logs -f batch-processor

logs-api: ## Follow logs from API service only
	docker-compose logs -f api

# Testing Commands
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres redis
	@sleep 10
	docker run --rm \
		--network "$$(basename $$(pwd))_job-matching-network" \
		-e DATABASE_URL="postgresql://postgres:password@postgres:5432/job_matching_test" \
		-e REDIS_URL="redis://:redispassword@redis:6379/1" \
		job-matching:latest \
		python -m pytest tests/ -v
	docker-compose -f docker-compose.yml -f docker-compose.test.yml down -v
	@echo "$(GREEN)Tests completed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker run --rm \
		--network "$$(basename $$(pwd))_job-matching-network" \
		job-matching:latest \
		python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Deployment Commands
deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	./backend/scripts/deploy.sh staging $(VERSION)

deploy-production: ## Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(NC)"
	./backend/scripts/deploy.sh production $(VERSION)

# Monitoring Commands
monitor: ## Open monitoring dashboard
	@echo "$(BLUE)Opening monitoring dashboards...$(NC)"
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"
	@echo "AlertManager: http://localhost:9093"
	@if command -v open >/dev/null; then open http://localhost:3001; fi

monitor-status: ## Check monitoring system status
	@echo "$(BLUE)Checking monitoring status...$(NC)"
	./backend/scripts/batch_monitor.sh check

monitor-health: ## Run comprehensive health check
	@echo "$(BLUE)Running health checks...$(NC)"
	./backend/scripts/batch_monitor.sh health

# Database Commands
db-backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	mkdir -p ./database/backups
	docker exec job-matching-postgres pg_dump -U postgres job_matching > \
		./database/backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created$(NC)"

db-restore: ## Restore database from latest backup (use BACKUP_FILE=filename to specify)
	@echo "$(BLUE)Restoring database...$(NC)"
	@if [ -z "$(BACKUP_FILE)" ]; then \
		BACKUP_FILE=$$(ls -t ./database/backups/*.sql | head -n1); \
	else \
		BACKUP_FILE=./database/backups/$(BACKUP_FILE); \
	fi; \
	echo "Restoring from: $$BACKUP_FILE"; \
	docker exec -i job-matching-postgres psql -U postgres -d job_matching < $$BACKUP_FILE
	@echo "$(GREEN)Database restored$(NC)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker exec job-matching-api alembic upgrade head
	@echo "$(GREEN)Migrations completed$(NC)"

db-shell: ## Connect to database shell
	docker exec -it job-matching-postgres psql -U postgres -d job_matching

# Maintenance Commands
clean: ## Clean up unused Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)Cleanup completed$(NC)"

clean-all: ## Clean up all Docker resources (including images)
	@echo "$(YELLOW)WARNING: This will remove all unused Docker resources including images$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -af; \
		docker volume prune -f; \
		echo "$(GREEN)Deep cleanup completed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Services restarted$(NC)"

restart-batch: ## Restart batch processor only
	@echo "$(BLUE)Restarting batch processor...$(NC)"
	./backend/scripts/batch_monitor.sh restart

# Security Commands
security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	@if command -v trivy >/dev/null; then \
		trivy image job-matching:latest; \
		trivy image job-matching-batch:latest; \
	else \
		echo "$(YELLOW)Trivy not installed - install with: brew install aquasecurity/trivy/trivy$(NC)"; \
	fi
	@if command -v gitleaks >/dev/null; then \
		gitleaks detect --source=. --verbose; \
	else \
		echo "$(YELLOW)Gitleaks not installed - install with: brew install gitleaks$(NC)"; \
	fi

# Development Helpers
shell-api: ## Open shell in API container
	docker exec -it job-matching-api /bin/bash

shell-batch: ## Open shell in batch processor container
	docker exec -it job-matching-batch /bin/bash

shell-db: ## Open shell in database container
	docker exec -it job-matching-postgres /bin/bash

# File Operations
setup-env: ## Copy environment template and prompt for editing
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "$(GREEN)Created .env file from template$(NC)"; \
		echo "$(YELLOW)Please edit .env file with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

validate-env: ## Validate environment configuration
	@echo "$(BLUE)Validating environment configuration...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)ERROR: .env file not found$(NC)"; \
		exit 1; \
	fi
	@grep -q "POSTGRES_PASSWORD" .env || (echo "$(RED)ERROR: POSTGRES_PASSWORD not set$(NC)" && exit 1)
	@grep -q "REDIS_PASSWORD" .env || (echo "$(RED)ERROR: REDIS_PASSWORD not set$(NC)" && exit 1)
	@echo "$(GREEN)Environment validation passed$(NC)"

# Full stack operations
stack-up: validate-env ## Start full monitoring stack
	@echo "$(BLUE)Starting full monitoring stack...$(NC)"
	docker-compose --profile full-stack up -d
	@echo "$(GREEN)Full stack started$(NC)"
	@echo "Services available:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Grafana: http://localhost:3001"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Kibana: http://localhost:5601"
	@echo "  - AlertManager: http://localhost:9093"

stack-down: ## Stop full stack
	docker-compose --profile full-stack down

# Quick development setup
dev-setup: setup-env build up ## Quick development environment setup
	@echo "$(GREEN)Development environment ready!$(NC)"

# Production readiness check
production-check: validate-env security-scan test ## Run production readiness checks
	@echo "$(BLUE)Running production readiness checks...$(NC)"
	@echo "$(GREEN)Production readiness check completed$(NC)"