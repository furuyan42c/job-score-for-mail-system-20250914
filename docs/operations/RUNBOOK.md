# Mail Score System - Operations Runbook

## Quick Reference

### Emergency Contacts
- **On-Call Engineer**: ops-oncall@company.com
- **Site Reliability Team**: sre@company.com
- **Security Team**: security@company.com
- **Management Escalation**: engineering-manager@company.com

### System URLs
- **Production**: https://mailscore.com
- **Staging**: https://staging.mailscore.com
- **Monitoring**: https://grafana.mailscore.com
- **Status Page**: https://status.mailscore.com

---

## Common Operational Procedures

### 1. Application Restart

#### Restart Backend Service
```bash
# Check current status
kubectl get pods -n mail-score-production -l app.kubernetes.io/component=api

# Rolling restart (zero-downtime)
kubectl rollout restart deployment/mail-score-backend -n mail-score-production

# Monitor restart progress
kubectl rollout status deployment/mail-score-backend -n mail-score-production --timeout=300s

# Verify health
kubectl get pods -n mail-score-production -l app.kubernetes.io/component=api
curl -f https://api.mailscore.com/health
```

#### Restart Frontend Service
```bash
# Rolling restart
kubectl rollout restart deployment/mail-score-frontend -n mail-score-production

# Monitor restart
kubectl rollout status deployment/mail-score-frontend -n mail-score-production --timeout=300s

# Verify health
curl -f https://mailscore.com/api/health
```

### 2. Scaling Operations

#### Scale Up for High Traffic
```bash
# Scale backend (emergency scaling)
kubectl scale deployment mail-score-backend --replicas=10 -n mail-score-production

# Scale frontend
kubectl scale deployment mail-score-frontend --replicas=6 -n mail-score-production

# Monitor scaling
kubectl get pods -n mail-score-production -w

# Check HPA status
kubectl get hpa -n mail-score-production
```

#### Scale Down (Maintenance Window)
```bash
# Scale down backend
kubectl scale deployment mail-score-backend --replicas=2 -n mail-score-production

# Scale down frontend
kubectl scale deployment mail-score-frontend --replicas=1 -n mail-score-production

# Verify scaling
kubectl get pods -n mail-score-production
```

### 3. Database Operations

#### Database Health Check
```bash
# Check database pod status
kubectl get pods -n mail-score-production -l app.kubernetes.io/component=database

# Test database connectivity
kubectl run postgres-test --rm -i --tty \
  --image=postgres:15-alpine \
  --restart=Never \
  --namespace=mail-score-production -- \
  psql -h postgres-service -U postgres -d mail_score -c "SELECT 1;"

# Check database metrics
kubectl exec -it deployment/postgres -n mail-score-production -- \
  psql -U postgres -d mail_score -c "\l"
```

#### Database Backup (Manual)
```bash
# Create immediate backup
kubectl exec -it deployment/postgres -n mail-score-production -- \
  pg_dump -U postgres mail_score > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -la backup_*.sql
head -20 backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Log Analysis

#### View Application Logs
```bash
# Backend logs (last 100 lines)
kubectl logs deployment/mail-score-backend -n mail-score-production --tail=100

# Follow logs in real-time
kubectl logs -f deployment/mail-score-backend -n mail-score-production

# Frontend logs
kubectl logs deployment/mail-score-frontend -n mail-score-production --tail=100

# Filter error logs
kubectl logs deployment/mail-score-backend -n mail-score-production | grep ERROR
```

#### Search Logs with Kibana
```bash
# Open Kibana dashboard
# URL: https://kibana.mailscore.com

# Common search queries:
# Error logs: level:ERROR
# Slow requests: response_time:>1000
# Database errors: message:"database connection"
# User errors: status_code:4*
```

### 5. Performance Monitoring

#### Check Resource Usage
```bash
# Pod resource usage
kubectl top pods -n mail-score-production

# Node resource usage
kubectl top nodes

# Detailed pod metrics
kubectl describe pod <pod-name> -n mail-score-production
```

#### Monitor Key Metrics
```bash
# Check Prometheus metrics
curl -s "http://prometheus.mailscore.com:9090/api/v1/query?query=up"

# Application response time
curl -s "http://prometheus.mailscore.com:9090/api/v1/query?query=histogram_quantile(0.95,%20rate(http_request_duration_seconds_bucket[5m]))"

# Error rate
curl -s "http://prometheus.mailscore.com:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])"
```

---

## Incident Response Procedures

### Priority 1 - Service Outage

#### Immediate Actions (0-5 minutes)
1. **Acknowledge the incident**
   ```bash
   # Check overall system status
   kubectl get pods -n mail-score-production
   kubectl get services -n mail-score-production
   curl -f https://mailscore.com/health || echo "FRONTEND DOWN"
   curl -f https://api.mailscore.com/health || echo "BACKEND DOWN"
   ```

2. **Activate incident response**
   ```bash
   # Post to Slack
   # Message: "P1 INCIDENT: Service outage detected. Investigating..."

   # Update status page
   curl -X POST "https://api.statuspage.io/v1/pages/PAGE_ID/incidents" \
     -H "Authorization: OAuth TOKEN" \
     -d '{"incident":{"name":"Service Outage","status":"investigating"}}'
   ```

#### Investigation (5-15 minutes)
1. **Check infrastructure**
   ```bash
   # Kubernetes cluster health
   kubectl cluster-info
   kubectl get nodes

   # Check for failed pods
   kubectl get pods -n mail-score-production | grep -v Running

   # Check recent events
   kubectl get events -n mail-score-production --sort-by='.lastTimestamp' | tail -20
   ```

2. **Check application health**
   ```bash
   # Database connectivity
   kubectl exec -it deployment/postgres -n mail-score-production -- \
     pg_isready -U postgres

   # Redis connectivity
   kubectl exec -it deployment/redis -n mail-score-production -- \
     redis-cli ping

   # Application logs for errors
   kubectl logs deployment/mail-score-backend -n mail-score-production --tail=50 | grep ERROR
   ```

#### Recovery Actions
1. **Quick fixes**
   ```bash
   # Restart failed services
   kubectl rollout restart deployment/mail-score-backend -n mail-score-production
   kubectl rollout restart deployment/mail-score-frontend -n mail-score-production

   # Scale up if needed
   kubectl scale deployment mail-score-backend --replicas=5 -n mail-score-production
   ```

2. **Emergency rollback if recent deployment**
   ```bash
   # Check recent deployments
   kubectl rollout history deployment/mail-score-backend -n mail-score-production

   # Rollback to previous version
   kubectl rollout undo deployment/mail-score-backend -n mail-score-production
   kubectl rollout undo deployment/mail-score-frontend -n mail-score-production
   ```

### Priority 2 - Performance Degradation

#### Investigation Steps
1. **Check metrics**
   ```bash
   # CPU and memory usage
   kubectl top pods -n mail-score-production

   # Check HPA status
   kubectl get hpa -n mail-score-production

   # Response time analysis
   curl -s "http://prometheus.mailscore.com:9090/api/v1/query?query=histogram_quantile(0.95,%20rate(http_request_duration_seconds_bucket[5m]))"
   ```

2. **Database performance**
   ```bash
   # Check database connections
   kubectl exec -it deployment/postgres -n mail-score-production -- \
     psql -U postgres -d mail_score -c "SELECT count(*) FROM pg_stat_activity;"

   # Check slow queries
   kubectl exec -it deployment/postgres -n mail-score-production -- \
     psql -U postgres -d mail_score -c "SELECT query, query_start, state FROM pg_stat_activity WHERE state != 'idle';"
   ```

#### Mitigation Actions
1. **Scale resources**
   ```bash
   # Horizontal scaling
   kubectl scale deployment mail-score-backend --replicas=8 -n mail-score-production

   # Adjust HPA if needed
   kubectl patch hpa backend-hpa -n mail-score-production -p '{"spec":{"maxReplicas":15}}'
   ```

2. **Cache optimization**
   ```bash
   # Check Redis memory usage
   kubectl exec -it deployment/redis -n mail-score-production -- \
     redis-cli info memory

   # Clear cache if needed (USE WITH CAUTION)
   kubectl exec -it deployment/redis -n mail-score-production -- \
     redis-cli flushdb
   ```

---

## Maintenance Procedures

### Scheduled Maintenance

#### Pre-Maintenance Checklist
- [ ] Schedule announced 24h in advance
- [ ] Backup completed successfully
- [ ] Maintenance window confirmed with stakeholders
- [ ] Rollback plan prepared
- [ ] Monitoring alerts adjusted

#### Maintenance Window Process
1. **Enable maintenance mode**
   ```bash
   # Update frontend to show maintenance page
   kubectl patch configmap frontend-config -n mail-score-production \
     -p '{"data":{"MAINTENANCE_MODE":"true"}}'

   # Restart frontend
   kubectl rollout restart deployment/mail-score-frontend -n mail-score-production
   ```

2. **Perform maintenance tasks**
   ```bash
   # Scale down non-essential services
   kubectl scale deployment mail-score-backend --replicas=1 -n mail-score-production

   # Update configurations
   # Apply patches
   # Run migrations
   ```

3. **Disable maintenance mode**
   ```bash
   # Disable maintenance mode
   kubectl patch configmap frontend-config -n mail-score-production \
     -p '{"data":{"MAINTENANCE_MODE":"false"}}'

   # Scale back to normal
   kubectl scale deployment mail-score-backend --replicas=3 -n mail-score-production

   # Restart services
   kubectl rollout restart deployment/mail-score-frontend -n mail-score-production
   ```

### Security Updates

#### Emergency Security Patch
1. **Immediate assessment**
   ```bash
   # Check vulnerability impact
   trivy image mail-score-backend:latest

   # Review security advisories
   # Assess criticality and exposure
   ```

2. **Emergency deployment**
   ```bash
   # Build patched image
   docker build -t mail-score-backend:security-patch ./backend
   docker push ghcr.io/repo/mail-score-backend:security-patch

   # Deploy immediately
   kubectl set image deployment/mail-score-backend \
     backend=ghcr.io/repo/mail-score-backend:security-patch \
     -n mail-score-production

   # Monitor deployment
   kubectl rollout status deployment/mail-score-backend -n mail-score-production
   ```

---

## Disaster Recovery

### Complete System Recovery

#### Phase 1: Assessment (0-15 minutes)
1. **Determine scope of failure**
   ```bash
   # Check cluster status
   kubectl cluster-info
   kubectl get nodes

   # Check external dependencies
   curl -f https://api.external-service.com/health

   # Assess data integrity
   kubectl exec -it deployment/postgres -n mail-score-production -- \
     psql -U postgres -d mail_score -c "SELECT COUNT(*) FROM users;"
   ```

#### Phase 2: Emergency Response (15-30 minutes)
1. **Activate disaster recovery**
   ```bash
   # Switch DNS to maintenance page
   # Notify stakeholders
   # Activate backup region if available
   ```

2. **Begin recovery**
   ```bash
   # Restore from backup
   kubectl apply -f disaster-recovery/

   # Restore database
   kubectl exec -i deployment/postgres -n mail-score-production -- \
     psql -U postgres -d mail_score < latest-backup.sql
   ```

#### Phase 3: Service Restoration (30-60 minutes)
1. **Verify system integrity**
   ```bash
   # Check all pods are running
   kubectl get pods -n mail-score-production

   # Verify database consistency
   kubectl exec -it deployment/postgres -n mail-score-production -- \
     psql -U postgres -d mail_score -c "\dt"

   # Test critical functionality
   curl -f https://api.mailscore.com/health
   curl -f https://mailscore.com/api/health
   ```

2. **Gradual traffic restoration**
   ```bash
   # Update DNS to restore traffic
   # Monitor error rates and performance
   # Verify user functionality
   ```

---

## Monitoring and Alerting

### Key Dashboards

#### System Health Dashboard
- URL: https://grafana.mailscore.com/d/system-health
- Metrics: CPU, Memory, Network, Disk
- Refresh: 30 seconds

#### Application Performance Dashboard
- URL: https://grafana.mailscore.com/d/app-performance
- Metrics: Response time, Throughput, Error rate
- Refresh: 15 seconds

### Alert Response

#### Critical Alerts
```bash
# High Error Rate
# Investigation: Check application logs, database connectivity
kubectl logs deployment/mail-score-backend -n mail-score-production | grep ERROR

# Database Down
# Investigation: Check postgres pod, network connectivity
kubectl get pods -n mail-score-production -l app.kubernetes.io/component=database
kubectl describe pod postgres-* -n mail-score-production

# Memory Usage High
# Action: Scale up pods or investigate memory leaks
kubectl top pods -n mail-score-production
kubectl scale deployment mail-score-backend --replicas=6 -n mail-score-production
```

#### Warning Alerts
```bash
# Slow Response Time
# Investigation: Check resource usage, database performance
kubectl top pods -n mail-score-production
kubectl exec -it deployment/postgres -n mail-score-production -- \
  psql -U postgres -d mail_score -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# High CPU Usage
# Action: Scale horizontally or investigate performance bottlenecks
kubectl get hpa -n mail-score-production
kubectl scale deployment mail-score-backend --replicas=8 -n mail-score-production
```

---

## Contact Information

### Escalation Matrix

| Level | Role | Contact | Response Time |
|-------|------|---------|---------------|
| L1 | On-Call Engineer | ops-oncall@company.com | 15 minutes |
| L2 | Senior SRE | sre-senior@company.com | 30 minutes |
| L3 | Engineering Manager | eng-manager@company.com | 1 hour |
| L4 | CTO | cto@company.com | 2 hours |

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| Cloud Provider | support@cloudprovider.com | Infrastructure issues |
| DNS Provider | support@dnsprovider.com | DNS problems |
| Certificate Authority | support@certprovider.com | SSL/TLS issues |
| Monitoring Service | support@monitoring.com | Monitoring platform issues |

---

*Last Updated: $(date)*
*Version: 1.0.0*
*Next Review: $(date -d '+3 months')*