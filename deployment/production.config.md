# T072: 本番環境向けデプロイメント設定
## Production Deployment Configuration for Supabase Integration

## 📋 Overview
This document contains the production deployment configuration for the mail scoring system with Supabase integration.

## 🎯 Deployment Architecture

### Frontend (Next.js)
- **Platform**: Vercel / Netlify / AWS Amplify
- **Environment**: Production
- **Node Version**: 18.x or higher

### Backend (Supabase)
- **Platform**: Supabase Cloud
- **Region**: ap-northeast-1 (Tokyo)
- **Database**: PostgreSQL 15+
- **Realtime**: Enabled

## 🔐 Environment Variables

### Frontend (.env.production)
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT_ID].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[YOUR_ANON_KEY]

# Application Settings
NEXT_PUBLIC_APP_URL=https://your-domain.com
NEXT_PUBLIC_API_TIMEOUT=30000

# Feature Flags
NEXT_PUBLIC_ENABLE_REALTIME=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### Backend (Supabase Dashboard)
```sql
-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_data ENABLE ROW LEVEL SECURITY;

-- Create policies (if needed for public access)
CREATE POLICY "Public read access" ON prefecture_master
  FOR SELECT USING (true);

CREATE POLICY "Public read access" ON city_master
  FOR SELECT USING (true);
```

## 📦 Deployment Steps

### 1. Supabase Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Create new project (if not exists)
supabase projects create mail-scoring-system

# Link local project
supabase link --project-ref [PROJECT_ID]

# Push database schema
supabase db push

# Push migrations
supabase migration up
```

### 2. Database Migration
```bash
# Export local data (if needed)
pg_dump -h localhost -p 54322 -U postgres -d postgres > backup.sql

# Import to production
psql -h [SUPABASE_HOST] -U postgres -d postgres < backup.sql
```

### 3. Frontend Deployment (Vercel)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to production
cd frontend
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

### 4. Frontend Deployment (Alternative: Docker)
```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./

# Set environment
ENV NODE_ENV=production

EXPOSE 3000
CMD ["npm", "start"]
```

## 🔒 Security Configuration

### Content Security Policy
```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: `
              default-src 'self';
              script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.supabase.co;
              style-src 'self' 'unsafe-inline';
              img-src 'self' data: https:;
              connect-src 'self' https://*.supabase.co wss://*.supabase.co;
              font-src 'self' data:;
            `.replace(/\n/g, '')
          }
        ]
      }
    ]
  }
}
```

### Rate Limiting
```typescript
// lib/rateLimit.ts
import { RateLimiterMemory } from 'rate-limiter-flexible'

const rateLimiter = new RateLimiterMemory({
  points: 100, // Number of requests
  duration: 60, // Per 60 seconds
})

export async function rateLimit(identifier: string) {
  try {
    await rateLimiter.consume(identifier)
    return true
  } catch {
    return false
  }
}
```

## 🚀 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm test
      - run: npm run lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      # Deploy to Supabase
      - name: Deploy Database
        run: |
          npm install -g supabase
          supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_PROJECT_ID: ${{ secrets.SUPABASE_PROJECT_ID }}

      # Deploy to Vercel
      - name: Deploy Frontend
        run: |
          npm install -g vercel
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

## 📊 Monitoring & Logging

### Application Monitoring
```typescript
// lib/monitoring.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
})

export function logError(error: Error, context?: any) {
  console.error(error)
  Sentry.captureException(error, { extra: context })
}
```

### Database Monitoring
```sql
-- Create monitoring views
CREATE VIEW database_stats AS
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_live_tup AS row_count,
  n_dead_tup AS dead_rows,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔄 Backup & Recovery

### Automated Backups
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${DATE}.sql"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/

# Clean old backups (keep last 30 days)
find . -name "backup_*.sql" -mtime +30 -delete
```

### Recovery Procedure
```bash
# Restore from backup
psql $DATABASE_URL < backup_20240101_120000.sql

# Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

## 🏗️ Scaling Configuration

### Database Connection Pooling
```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  {
    db: {
      schema: 'public',
    },
    auth: {
      persistSession: true,
    },
    global: {
      headers: {
        'x-application-name': 'mail-scoring-system'
      }
    }
  }
)
```

### Edge Functions (Optional)
```typescript
// supabase/functions/query-optimizer/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const { query } = await req.json()

  // Optimize query execution
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const { data, error } = await supabase.rpc('execute_optimized_query', {
    query_text: query
  })

  return new Response(JSON.stringify({ data, error }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

## 📝 Health Checks

### API Health Check
```typescript
// pages/api/health.ts
export default async function handler(req, res) {
  try {
    // Check Supabase connection
    const { error } = await supabase.from('prefecture_master').select('count').single()

    if (error) throw error

    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'connected',
        realtime: 'active'
      }
    })
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    })
  }
}
```

## 🔍 Performance Optimization

### Database Indexes
```sql
-- Create indexes for common queries
CREATE INDEX idx_jobs_prefecture ON jobs(prefecture_cd);
CREATE INDEX idx_jobs_city ON jobs(city_cd);
CREATE INDEX idx_jobs_score ON jobs(score DESC);
CREATE INDEX idx_user_actions_user ON user_actions(user_id);
CREATE INDEX idx_user_actions_date ON user_actions(action_date);
```

### Next.js Optimization
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['your-domain.com'],
    formats: ['image/avif', 'image/webp'],
  },
  swcMinify: true,
  experimental: {
    optimizeCss: true,
  }
}
```

## 🚨 Rollback Strategy

### Database Rollback
```bash
# Rollback last migration
supabase migration down

# Restore from backup point
psql $DATABASE_URL < backup_before_deploy.sql
```

### Frontend Rollback (Vercel)
```bash
# List deployments
vercel ls

# Rollback to previous deployment
vercel rollback [DEPLOYMENT_ID]
```

## 📌 Post-Deployment Checklist

- [ ] Verify all environment variables are set
- [ ] Test database connections
- [ ] Verify real-time subscriptions work
- [ ] Check API rate limits
- [ ] Test health check endpoints
- [ ] Verify SSL certificates
- [ ] Check CORS configuration
- [ ] Test error logging
- [ ] Verify backup automation
- [ ] Check monitoring dashboards
- [ ] Test rollback procedure
- [ ] Update DNS records
- [ ] Clear CDN cache
- [ ] Notify team of deployment

## 🔗 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Vercel Documentation](https://vercel.com/docs)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)

---
*Last Updated: 2025-09-18*
*Version: 1.0.0*