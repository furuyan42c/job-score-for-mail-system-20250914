# Supabase Real-time Integration - Deployment Guide

## T069-T074: Complete Supabase Real-time System

This guide covers the complete deployment of the Supabase real-time integration system including real-time subscriptions, storage operations, edge functions, and production configuration.

## 🏗️ Architecture Overview

### Components Implemented

1. **T069: Real-time Query Execution Service** (`app/services/realtime_service.py`)
   - WebSocket connection management
   - Real-time subscription handling
   - Live data streaming
   - Connection statistics and monitoring

2. **T070: Supabase Real-time Integration** (`app/core/supabase_realtime.py`)
   - Channel management for different event types
   - Event routing and processing
   - Rate limiting and buffering
   - Comprehensive metrics collection

3. **T071: Storage Service** (`app/services/storage_service.py`)
   - File upload/download operations
   - CSV import and processing
   - Email attachment handling
   - Storage bucket management

4. **T072: Edge Functions** (`supabase/functions/`)
   - Background job processor
   - Email sender service
   - Score calculation engine
   - Serverless function deployment

5. **T073: E2E Tests** (`tests/e2e/test_supabase_integration.py`)
   - Comprehensive integration testing
   - Real-time functionality validation
   - Storage operation testing
   - Edge function integration tests

6. **T074: Deployment Configuration**
   - Production-ready Supabase configuration
   - Database migrations and seed data
   - Deployment scripts and environment setup

## 🚀 Quick Deployment

### Prerequisites

1. **Supabase CLI**: Install the Supabase CLI
   ```bash
   npm install -g supabase
   ```

2. **Environment Variables**: Copy and configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase project details
   ```

3. **Supabase Project**: Create a new Supabase project at [supabase.com](https://supabase.com)

### Deployment Steps

1. **Initialize and Link Project**
   ```bash
   # Make deployment script executable
   chmod +x scripts/deploy_supabase.sh

   # Initialize project
   ./scripts/deploy_supabase.sh -e development init
   ```

2. **Run Database Migrations**
   ```bash
   # Apply all migrations
   ./scripts/deploy_supabase.sh -e development migrate
   ```

3. **Deploy Edge Functions**
   ```bash
   # Deploy all edge functions
   ./scripts/deploy_supabase.sh -e development deploy-functions
   ```

4. **Full Deployment** (all-in-one)
   ```bash
   # Complete deployment with seed data
   ./scripts/deploy_supabase.sh -e development full-deploy
   ```

5. **Verify Deployment**
   ```bash
   # Run health check
   ./scripts/deploy_supabase.sh health-check
   ```

## 📋 Configuration Details

### Supabase Configuration (`supabase/config.toml`)

```toml
[api]
enabled = true
port = 54321
max_rows = 1000

[realtime]
enabled = true
max_events_per_second = 100
max_concurrent_users = 1000

[storage]
enabled = true
file_size_limit = "100MB"

[edge_functions]
enabled = true
```

### Database Schema

The system creates the following tables:

- `background_jobs` - Job queue management
- `email_logs` - Email sending tracking
- `score_calculations` - Score computation results
- `file_metadata` - File upload metadata
- `email_config` - Email service configuration
- `email_templates` - Email template storage
- `system_config` - System configuration
- `performance_metrics` - Performance monitoring
- `data_imports` - Data import tracking

### Row Level Security (RLS)

All tables have RLS enabled with policies for:
- User data isolation
- Service role administrative access
- Authenticated user permissions

## 🔧 Service Configuration

### Real-time Service

```python
from app.services.realtime_service import get_realtime_service
from app.core.supabase_realtime import get_channel_manager

# Initialize services
realtime_service = get_realtime_service()
channel_manager = get_channel_manager()

# Set up default channels
await setup_realtime_channels()
```

### Storage Service

```python
from app.services.storage_service import get_storage_service

# Initialize storage
storage_service = get_storage_service()

# Upload file
result = await storage_service.upload_file(
    file_data=file_bytes,
    filename="data.csv",
    user_id=user_id
)
```

### Edge Functions

Access edge functions at:
- `https://your-project.supabase.co/functions/v1/background-job-processor`
- `https://your-project.supabase.co/functions/v1/email-sender`
- `https://your-project.supabase.co/functions/v1/score-calculator`

## 🧪 Testing

### Run E2E Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all E2E tests
pytest tests/e2e/test_supabase_integration.py -v

# Run specific test categories
pytest tests/e2e/test_supabase_integration.py::TestSupabaseIntegration::test_realtime_subscription_lifecycle -v
```

### Load Testing

```bash
# Run load tests (marked as slow)
pytest tests/e2e/test_supabase_integration.py -m slow -v
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints

The system provides comprehensive health monitoring:

```python
# Supabase client health
client = get_supabase_client()
health_data = await client.health_check()

# Service statistics
realtime_stats = realtime_service.get_service_stats()
storage_stats = storage_service.get_storage_stats()
channel_stats = channel_manager.get_service_stats()
```

### Performance Metrics

Monitor key metrics:
- Connection pool statistics
- Real-time message processing rates
- Storage operation performance
- Edge function execution times

## 🔐 Security Considerations

### Environment Variables

Required environment variables:
- `SUPABASE_URL`: Project URL
- `SUPABASE_ANON_KEY`: Anonymous key for client-side operations
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for server-side operations (keep secret)

### RLS Policies

- Users can only access their own data
- Service role has administrative access
- All tables have appropriate RLS policies

### Edge Function Security

- JWT verification enabled for all functions
- CORS properly configured
- Input validation and sanitization

## 🚀 Production Deployment

### Environment-Specific Configuration

```bash
# Production deployment
./scripts/deploy_supabase.sh -e production full-deploy

# Staging deployment
./scripts/deploy_supabase.sh -e staging full-deploy
```

### Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates in place
- [ ] Database migrations applied
- [ ] Edge functions deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Rate limiting configured

## 📈 Scaling Considerations

### Real-time Scaling

- Connection limits: 1000 concurrent (configurable)
- Message rate limits: 100 events/second (configurable)
- Channel management with automatic cleanup

### Storage Scaling

- File size limits: 100MB default (configurable)
- Bucket organization by user and file type
- Automatic cleanup of expired files

### Edge Function Scaling

- Stateless function design
- Automatic scaling based on demand
- Error handling and retry logic

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failures**
   ```bash
   # Check Supabase status
   ./scripts/deploy_supabase.sh status

   # Verify environment variables
   echo $SUPABASE_URL
   ```

2. **Migration Errors**
   ```bash
   # Check migration status
   supabase migration list

   # Reset database (development only)
   supabase db reset
   ```

3. **Edge Function Deployment Issues**
   ```bash
   # Check function logs
   supabase functions logs background-job-processor

   # Redeploy specific function
   supabase functions deploy email-sender --verify-jwt
   ```

### Debug Mode

Enable verbose logging:
```bash
./scripts/deploy_supabase.sh -v health-check
```

## 📚 API Documentation

### Real-time Subscriptions

```python
# Subscribe to job updates
subscription_id = await realtime_service.create_subscription(
    subscription_type=SubscriptionType.JOB_UPDATES,
    table_name="jobs",
    connection_id=connection_id,
    user_id=user_id
)
```

### Storage Operations

```python
# Upload file
upload_result = await storage_service.upload_file(
    file_data=file_bytes,
    filename="document.pdf",
    bucket_name="files",
    user_id=user_id
)

# Download file
success, file_bytes, metadata = await storage_service.download_file(file_id)
```

### Edge Function Calls

```python
# Background job processing
job_payload = {
    "job_id": job_id,
    "job_type": "email_processing",
    "data": {"email_id": email_id, "action": "extract_entities"}
}

response = requests.post(
    f"{supabase_url}/functions/v1/background-job-processor",
    json=job_payload,
    headers={"Authorization": f"Bearer {service_role_key}"}
)
```

## 🔄 Maintenance

### Regular Maintenance Tasks

1. **Cleanup Expired Files**
   ```python
   cleaned_count = await storage_service.cleanup_expired_files()
   ```

2. **Monitor Performance**
   ```python
   performance_summary = await get_performance_summary()
   ```

3. **Update Statistics**
   ```python
   stats = realtime_service.get_service_stats()
   ```

### Backup and Recovery

- Database backups handled by Supabase
- File storage backups through Supabase Storage
- Configuration backups in version control

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Supabase documentation
3. Check system logs and health endpoints
4. Verify environment configuration

## 🔄 Updates and Versioning

The system is designed for incremental updates:
- Database migrations for schema changes
- Edge function redeployment for logic updates
- Configuration updates through environment variables
- Backward compatibility maintained where possible