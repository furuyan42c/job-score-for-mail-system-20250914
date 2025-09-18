# Supabase Deployment Guide
> Task T074: Complete deployment configuration for production environment

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Security Best Practices](#security-best-practices)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Verify installation
supabase --version

# Login to Supabase
supabase login
```

### Project Setup
```bash
# Link to existing project
supabase link --project-ref your-project-ref

# Or create new project
supabase projects create job-matching-system
```

## Local Development

### Starting Local Environment
```bash
# Start Supabase locally
supabase start

# View local credentials
supabase status
```

### Running Migrations Locally
```bash
# Create new migration
supabase migration new migration_name

# Apply migrations
supabase db reset

# View migration status
supabase migration list
```

## Staging Deployment

### 1. Environment Configuration
```bash
# Copy staging template
cp .env.example .env.staging

# Edit staging configuration
vim .env.staging
```

### 2. Deploy to Staging
```bash
# Run deployment script
./supabase/deploy.sh staging

# Or manually deploy
supabase db push --db-url $STAGING_DATABASE_URL
supabase functions deploy
```

### 3. Verify Staging Deployment
```bash
# Check deployment status
supabase projects list
supabase db remote list

# Test API endpoint
curl https://your-staging-project.supabase.co/rest/v1/health
```

## Production Deployment

### 1. Pre-deployment Checklist
- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Database backup created
- [ ] Rollback plan prepared
- [ ] Team notified

### 2. Environment Setup
```bash
# Set production environment variables
cp .env.example .env.production

# Edit with production values
vim .env.production

# CRITICAL: Never commit .env.production to git
echo ".env.production" >> .gitignore
```

### 3. Production Deployment Steps
```bash
# Step 1: Create database backup
supabase db dump -f backups/prod-$(date +%Y%m%d).sql

# Step 2: Deploy to production
./supabase/deploy.sh production

# Step 3: Verify deployment
curl https://your-prod-project.supabase.co/rest/v1/health

# Step 4: Run smoke tests
npm run test:e2e:prod
```

### 4. Post-deployment Verification
```sql
-- Check table counts
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Verify RLS policies
SELECT
    schemaname,
    tablename,
    policyname
FROM pg_policies
WHERE schemaname = 'public';

-- Check active connections
SELECT count(*) FROM pg_stat_activity;
```

## Environment Variables

### Frontend (.env.local)
```bash
# Public Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Application
NEXT_PUBLIC_APP_NAME="Job Matching System"
NEXT_PUBLIC_APP_URL=https://your-domain.com
```

### Backend (.env.production)
```bash
# Supabase Service Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database Direct Connection
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Redis Cache
REDIS_URL=redis://your-redis-instance:6379
```

## Security Best Practices

### 1. API Key Management
```bash
# Store secrets in Supabase
supabase secrets set OPENAI_API_KEY="sk-..."
supabase secrets set SMTP_PASSWORD="..."

# List secrets (doesn't show values)
supabase secrets list
```

### 2. Row Level Security (RLS)
```sql
-- Verify RLS is enabled on all tables
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = false;
```

### 3. SSL/TLS Configuration
```bash
# Enforce SSL connections
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
```

### 4. Rate Limiting
```typescript
// Configure in supabase/functions/shared/rateLimit.ts
export const rateLimit = {
  authenticated: {
    requests: 1000,
    windowMs: 60000 // 1 minute
  },
  anonymous: {
    requests: 100,
    windowMs: 60000
  }
}
```

## Monitoring & Maintenance

### 1. Health Monitoring
```bash
# Setup health check endpoint
curl -X POST https://api.uptimerobot.com/v2/newMonitor \
  -d "api_key=YOUR_KEY" \
  -d "url=https://your-project.supabase.co/rest/v1/health"
```

### 2. Database Metrics
```sql
-- Monitor slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Log Analysis
```bash
# View recent logs
supabase logs --tail 100

# Filter by function
supabase functions logs execute_readonly_sql --tail 50

# Export logs
supabase logs --since "2024-01-01" --until "2024-01-31" > january-logs.txt
```

### 4. Backup Strategy
```bash
#!/bin/bash
# Daily backup script (add to cron)
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups"

# Database backup
supabase db dump -f "$BACKUP_DIR/db-$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db-$DATE.sql"

# Upload to S3
aws s3 cp "$BACKUP_DIR/db-$DATE.sql.gz" s3://your-backup-bucket/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

#### 1. Migration Failures
```bash
# Check migration status
supabase migration list

# Reset and retry
supabase db reset --linked

# Apply specific migration
supabase db push --migration 20250919000000_init.sql
```

#### 2. Connection Issues
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Check firewall rules
supabase network-restrictions list

# Add IP to allowlist
supabase network-restrictions add 0.0.0.0/0
```

#### 3. Performance Issues
```sql
-- Find missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1
ORDER BY n_distinct DESC;

-- Vacuum and analyze
VACUUM ANALYZE;
```

#### 4. RLS Policy Issues
```sql
-- Test RLS policies
SET ROLE authenticated;
SET request.jwt.claim.sub = 'user-uuid';

-- Try query as user
SELECT * FROM job_data LIMIT 1;

-- Reset role
RESET ROLE;
```

## Rollback Procedures

### Emergency Rollback
```bash
# Step 1: Stop traffic (update load balancer)
# Step 2: Restore database
supabase db restore --backup backups/prod-20240101.sql

# Step 3: Revert Edge Functions
git checkout previous-version
supabase functions deploy --all

# Step 4: Verify rollback
npm run test:smoke

# Step 5: Resume traffic
```

## Performance Optimization

### 1. Database Tuning
```sql
-- Connection pooling configuration
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';

-- Apply changes
SELECT pg_reload_conf();
```

### 2. Query Optimization
```sql
-- Create composite indexes
CREATE INDEX idx_job_data_location_wage
ON job_data(prefecture_cd, city_cd, hourly_wage);

-- Partial indexes for common queries
CREATE INDEX idx_active_jobs
ON job_data(created_at)
WHERE is_active = true;
```

### 3. Caching Strategy
```typescript
// Redis caching layer
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })

export async function getCachedQuery(key: string) {
  const cached = await redis.get(key)
  if (cached) return JSON.parse(cached)

  const result = await executeQuery()
  await redis.setex(key, 3600, JSON.stringify(result))
  return result
}
```

## CI/CD Integration

### GitHub Actions Deployment
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Supabase CLI
        run: |
          curl -L https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.deb -o supabase.deb
          sudo dpkg -i supabase.deb

      - name: Deploy to Supabase
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_PROJECT_ID: ${{ secrets.SUPABASE_PROJECT_ID }}
        run: |
          supabase link --project-ref $SUPABASE_PROJECT_ID
          supabase db push
          supabase functions deploy --all
```

## Support & Resources

### Official Documentation
- [Supabase Docs](https://supabase.com/docs)
- [Database Functions](https://supabase.com/docs/guides/database/functions)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Edge Functions](https://supabase.com/docs/guides/functions)

### Community
- [Discord](https://discord.supabase.com/)
- [GitHub Discussions](https://github.com/supabase/supabase/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/supabase)

### Emergency Contacts
- Status Page: https://status.supabase.com/
- Support Email: support@supabase.com
- Critical Issues: Use dashboard support chat

---

**Last Updated**: 2025-09-19
**Version**: 1.0.0
**Author**: Job Matching System Team