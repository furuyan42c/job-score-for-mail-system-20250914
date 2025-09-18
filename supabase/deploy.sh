#!/bin/bash

# =============================================================================
# T074: Supabase Production Deployment Script
# Description: Deploy Supabase to production environment
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="job-matching-system"
ENVIRONMENT="${1:-staging}"  # Default to staging if not specified

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if supabase CLI is installed
    if ! command -v supabase &> /dev/null; then
        print_error "Supabase CLI is not installed"
        exit 1
    fi

    # Check if logged in to Supabase
    if ! supabase projects list &> /dev/null; then
        print_error "Not logged in to Supabase. Run: supabase login"
        exit 1
    fi

    # Check environment file
    if [ "$ENVIRONMENT" == "production" ]; then
        if [ ! -f ".env.production" ]; then
            print_error ".env.production file not found"
            exit 1
        fi
        source .env.production
    else
        if [ ! -f ".env.staging" ]; then
            print_warning ".env.staging file not found, using defaults"
        else
            source .env.staging
        fi
    fi

    print_status "Prerequisites check completed"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."

    # Push database schema to remote
    supabase db push

    # Verify migrations
    supabase migration list

    print_status "Migrations completed successfully"
}

# Function to deploy Edge Functions
deploy_functions() {
    print_status "Deploying Edge Functions..."

    # Check if functions directory exists
    if [ -d "supabase/functions" ]; then
        # Deploy all functions
        for function_dir in supabase/functions/*/; do
            if [ -d "$function_dir" ]; then
                function_name=$(basename "$function_dir")
                print_status "Deploying function: $function_name"
                supabase functions deploy "$function_name"
            fi
        done
    else
        print_warning "No Edge Functions to deploy"
    fi

    print_status "Edge Functions deployment completed"
}

# Function to configure storage buckets
configure_storage() {
    print_status "Configuring storage buckets..."

    # Create storage buckets if they don't exist
    buckets=("avatars" "documents" "exports")

    for bucket in "${buckets[@]}"; do
        print_status "Configuring bucket: $bucket"

        # Create bucket via SQL (as Supabase CLI doesn't have direct bucket creation)
        supabase db execute --sql "
            INSERT INTO storage.buckets (id, name, public)
            VALUES ('$bucket', '$bucket', false)
            ON CONFLICT (id) DO NOTHING;
        " || print_warning "Bucket $bucket might already exist"
    done

    print_status "Storage configuration completed"
}

# Function to set environment secrets
set_secrets() {
    print_status "Setting environment secrets..."

    if [ "$ENVIRONMENT" == "production" ]; then
        # Set production secrets
        supabase secrets set SMTP_HOST="$PROD_SMTP_HOST" \
            SMTP_USER="$PROD_SMTP_USER" \
            SMTP_PASSWORD="$PROD_SMTP_PASSWORD" \
            OPENAI_API_KEY="$PROD_OPENAI_API_KEY" \
            SENTRY_DSN="$PROD_SENTRY_DSN" \
            REDIS_URL="$PROD_REDIS_URL"
    fi

    print_status "Secrets configuration completed"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."

    # Check database connection
    if supabase db remote list &> /dev/null; then
        print_status "✓ Database connection verified"
    else
        print_error "✗ Database connection failed"
        exit 1
    fi

    # Check API health
    if [ -n "$NEXT_PUBLIC_SUPABASE_URL" ]; then
        if curl -s "$NEXT_PUBLIC_SUPABASE_URL/health" | grep -q "healthy"; then
            print_status "✓ API health check passed"
        else
            print_warning "⚠ API health check failed or not accessible"
        fi
    fi

    print_status "Deployment verification completed"
}

# Function to create database backup
backup_database() {
    print_status "Creating database backup..."

    BACKUP_NAME="${PROJECT_NAME}_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql"

    # Create backup
    supabase db dump -f "backups/$BACKUP_NAME"

    print_status "Database backup created: backups/$BACKUP_NAME"
}

# Function to display deployment summary
show_summary() {
    echo ""
    echo "======================================================"
    echo " Deployment Summary"
    echo "======================================================"
    echo " Project: $PROJECT_NAME"
    echo " Environment: $ENVIRONMENT"
    echo " Timestamp: $(date)"

    if [ -n "$NEXT_PUBLIC_SUPABASE_URL" ]; then
        echo " API URL: $NEXT_PUBLIC_SUPABASE_URL"
    fi

    echo "======================================================"
    echo ""

    print_status "Deployment completed successfully! 🎉"

    echo ""
    echo "Next steps:"
    echo "1. Update your application environment variables"
    echo "2. Test the deployment thoroughly"
    echo "3. Monitor logs and metrics"
    echo "4. Set up alerts and monitoring"
}

# Main deployment flow
main() {
    echo "======================================================"
    echo " Supabase Production Deployment"
    echo " Environment: $ENVIRONMENT"
    echo "======================================================"
    echo ""

    # Confirmation for production
    if [ "$ENVIRONMENT" == "production" ]; then
        print_warning "You are about to deploy to PRODUCTION!"
        read -p "Are you sure? (yes/no): " confirmation
        if [ "$confirmation" != "yes" ]; then
            print_error "Deployment cancelled"
            exit 0
        fi
    fi

    # Run deployment steps
    check_prerequisites

    if [ "$ENVIRONMENT" == "production" ]; then
        backup_database
    fi

    run_migrations
    deploy_functions
    configure_storage
    set_secrets
    verify_deployment
    show_summary
}

# Handle script arguments
case "$1" in
    production)
        ENVIRONMENT="production"
        main
        ;;
    staging)
        ENVIRONMENT="staging"
        main
        ;;
    rollback)
        print_status "Rolling back to previous version..."
        supabase db reset
        print_status "Rollback completed"
        ;;
    status)
        print_status "Checking deployment status..."
        supabase projects list
        supabase db remote list
        ;;
    help|--help|-h)
        echo "Usage: $0 [production|staging|rollback|status|help]"
        echo ""
        echo "Commands:"
        echo "  production  - Deploy to production environment"
        echo "  staging     - Deploy to staging environment (default)"
        echo "  rollback    - Rollback to previous version"
        echo "  status      - Check deployment status"
        echo "  help        - Show this help message"
        ;;
    *)
        ENVIRONMENT="staging"
        main
        ;;
esac