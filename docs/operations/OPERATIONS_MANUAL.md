# Mail Score System - Operations Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Deployment Guide](#deployment-guide)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Backup & Recovery](#backup--recovery)
6. [Scaling](#scaling)
7. [Security](#security)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)
10. [Emergency Procedures](#emergency-procedures)

## System Overview

The Mail Score System is a cloud-native application that analyzes and scores email content. The system consists of:

- **Frontend**: Next.js application serving the user interface
- **Backend**: FastAPI application handling API requests and ML processing
- **Database**: PostgreSQL for data persistence
- **Cache**: Redis for session management and caching
- **Infrastructure**: Kubernetes on cloud provider (AWS/GCP/Azure)

### Key Metrics
- **Target Uptime**: 99.9%
- **Response Time**: < 200ms (95th percentile)
- **Throughput**: 1000 requests/second
- **Recovery Time Objective (RTO)**: 15 minutes
- **Recovery Point Objective (RPO)**: 1 hour

## Architecture

### System Components

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Internet  │────│Load Balancer│────│   Ingress   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────────────────────┐
                   │                             │
              ┌────▼────┐                  ┌────▼────┐
              │Frontend │                  │Backend  │
              │(Next.js)│                  │(FastAPI)│
              └─────────┘                  └────┬────┘
                                                │
                   ┌─────────────────────────────┐
                   │                             │
              ┌────▼────┐                  ┌────▼────┐
              │PostgreSQL│                  │  Redis  │
              │Database │                  │ Cache   │
              └─────────┘                  └─────────┘
```

### Network Architecture
- **External**: Internet → Load Balancer → Kubernetes Ingress
- **Internal**: Pod-to-Pod communication via Kubernetes Services
- **Database**: Private subnet with no external access

## Deployment Guide

### Prerequisites

1. **Kubernetes Cluster** (v1.28+)
2. **kubectl** configured with cluster access
3. **Docker** registry access (GitHub Container Registry)
4. **Certificates** for HTTPS (Let's Encrypt or manual)

### Environment Setup

#### Development Environment
```bash
# Local development with Docker Compose
git clone <repository>
cd mail-score-system
cp .env.example .env.local
docker-compose up -d
```

#### Staging Environment
```bash
# Deploy to staging
kubectl apply -f k8s/base/namespace.yaml
kustomize build k8s/overlays/staging | kubectl apply -f -

# Verify deployment
kubectl get pods -n mail-score-staging
kubectl get services -n mail-score-staging
```

#### Production Environment
```bash
# Deploy to production
kubectl create namespace mail-score-production
kustomize build k8s/overlays/prod | kubectl apply -f -

# Verify deployment
kubectl get pods -n mail-score-production
kubectl rollout status deployment/mail-score-backend -n mail-score-production
```

### Configuration Management

#### Environment Variables
| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `DATABASE_URL` | Local PostgreSQL | Staging DB | Production DB |
| `REDIS_URL` | Local Redis | Staging Redis | Production Redis |
| `LOG_LEVEL` | DEBUG | INFO | WARNING |
| `WORKERS` | 2 | 4 | 8 |

#### Secrets Management
```bash
# Create secrets
kubectl create secret generic backend-secret \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=SECRET_KEY="..." \
  -n mail-score-production

# Update secrets
kubectl patch secret backend-secret \
  -p='{"data":{"DATABASE_URL":"<base64-encoded-value>"}}' \
  -n mail-score-production
```

## Monitoring & Alerting

### Prometheus Metrics

#### Application Metrics
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration
- `mail_score_processing_time`: ML processing time
- `database_connections_active`: Active DB connections

#### Infrastructure Metrics
- `node_cpu_seconds_total`: CPU usage
- `node_memory_MemAvailable_bytes`: Available memory
- `kube_pod_status_ready`: Pod readiness status

### Grafana Dashboards

#### System Overview Dashboard
- Overall system health
- Request rate and error rate
- Response time percentiles
- Resource utilization

#### Application Dashboard
- Mail processing metrics
- Database performance
- Cache hit rates
- Error tracking

### Alert Rules

#### Critical Alerts
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"

- alert: DatabaseDown
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Database is down"
```

#### Warning Alerts
```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.2
  for: 10m
  labels:
    severity: warning

- alert: SlowResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  labels:
    severity: warning
```

### Log Management

#### Log Aggregation (ELK Stack)
```bash
# View application logs
kubectl logs -f deployment/mail-score-backend -n mail-score-production

# Search logs in Kibana
GET /logstash-*/_search
{
  "query": {
    "match": {
      "level": "ERROR"
    }
  }
}
```

## Backup & Recovery

### Database Backup

#### Automated Backup
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_${DATE}.sql
aws s3 cp backup_${DATE}.sql s3://backups/postgres/
```

#### Point-in-Time Recovery
```bash
# Restore from backup
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME backup_20240101_120000.sql

# Verify restoration
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"
```

### Application State Backup

#### Configuration Backup
```bash
# Backup Kubernetes configs
kubectl get all -n mail-score-production -o yaml > k8s-backup.yaml

# Backup secrets (encrypted)
kubectl get secrets -n mail-score-production -o yaml > secrets-backup.yaml
```

### Disaster Recovery Procedures

#### Complete System Failure
1. **Assessment** (0-5 minutes)
   - Verify scope of failure
   - Check monitoring systems
   - Activate incident response team

2. **Emergency Response** (5-15 minutes)
   - Switch to maintenance mode
   - Redirect traffic to backup region
   - Begin restoration process

3. **Recovery** (15-60 minutes)
   - Restore infrastructure
   - Deploy application from latest images
   - Restore database from backup
   - Verify system functionality

## Scaling

### Horizontal Pod Autoscaling

#### Backend Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mail-score-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

#### Frontend Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mail-score-frontend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling

#### Resource Limits
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Database Scaling

#### Read Replicas
```bash
# Configure read replica
kubectl apply -f k8s/postgres-read-replica.yaml

# Update application to use read replica for queries
DATABASE_READ_URL=postgresql://user:pass@postgres-read:5432/db
```

## Security

### Container Security

#### Image Scanning
```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image mail-score-backend:latest
```

#### Security Policies
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  runAsUser:
    rule: 'MustRunAsNonRoot'
  fsGroup:
    rule: 'RunAsAny'
```

### Network Security

#### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### SSL/TLS Configuration

#### Certificate Management
```bash
# Install cert-manager
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.8.0/cert-manager.yaml

# Configure Let's Encrypt
kubectl apply -f k8s/cert-manager/cluster-issuer.yaml
```

## Troubleshooting

### Common Issues

#### Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n mail-score-production

# View pod logs
kubectl logs <pod-name> -n mail-score-production

# Describe pod for events
kubectl describe pod <pod-name> -n mail-score-production
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl run postgres-client --rm -it --image=postgres:15 -- \
  psql -h postgres-service -U postgres -d mail_score

# Check service endpoints
kubectl get endpoints postgres-service -n mail-score-production
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n mail-score-production
kubectl top nodes

# View HPA status
kubectl get hpa -n mail-score-production
```

### Debugging Tools

#### Port Forwarding
```bash
# Forward database port
kubectl port-forward service/postgres-service 5432:5432 -n mail-score-production

# Forward application port
kubectl port-forward service/backend-service 8000:8000 -n mail-score-production
```

#### Exec into Containers
```bash
# Access backend container
kubectl exec -it deployment/mail-score-backend -n mail-score-production -- /bin/sh

# Access database container
kubectl exec -it deployment/postgres -n mail-score-production -- psql -U postgres
```

## Maintenance

### Routine Maintenance

#### Weekly Tasks
- [ ] Review monitoring alerts
- [ ] Check resource utilization
- [ ] Verify backup integrity
- [ ] Update security patches

#### Monthly Tasks
- [ ] Security vulnerability assessment
- [ ] Performance optimization review
- [ ] Capacity planning review
- [ ] Documentation updates

### Update Procedures

#### Application Updates
```bash
# Update to new version
kubectl set image deployment/mail-score-backend \
  backend=ghcr.io/repo/mail-score-backend:v1.1.0 \
  -n mail-score-production

# Monitor rollout
kubectl rollout status deployment/mail-score-backend -n mail-score-production
```

#### Security Updates
```bash
# Update base images
docker build --pull -t mail-score-backend:latest ./backend
docker push ghcr.io/repo/mail-score-backend:latest

# Deploy updated images
kubectl rollout restart deployment/mail-score-backend -n mail-score-production
```

## Emergency Procedures

### Incident Response

#### Severity Levels
- **P0 (Critical)**: Complete system outage
- **P1 (High)**: Significant functionality impaired
- **P2 (Medium)**: Minor functionality impaired
- **P3 (Low)**: Cosmetic issues

#### Response Timeline
- **P0**: 15 minutes acknowledgment, 1 hour resolution
- **P1**: 30 minutes acknowledgment, 4 hours resolution
- **P2**: 2 hours acknowledgment, 24 hours resolution
- **P3**: 1 day acknowledgment, 1 week resolution

### Rollback Procedures

#### Application Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/mail-score-backend -n mail-score-production

# Rollback to specific revision
kubectl rollout undo deployment/mail-score-backend --to-revision=2 -n mail-score-production

# Verify rollback
kubectl rollout status deployment/mail-score-backend -n mail-score-production
```

#### Database Rollback
```bash
# Stop application
kubectl scale deployment/mail-score-backend --replicas=0 -n mail-score-production

# Restore database
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME backup_before_update.sql

# Restart application
kubectl scale deployment/mail-score-backend --replicas=3 -n mail-score-production
```

### Communication Plan

#### Stakeholder Notification
1. **Internal Team**: Slack #incidents channel
2. **Management**: Email + Phone call for P0/P1
3. **Users**: Status page update
4. **Customers**: Email notification for extended outages

#### Status Page Updates
```bash
# Update status page
curl -X POST "https://api.statuspage.io/v1/pages/PAGE_ID/incidents" \
  -H "Authorization: OAuth TOKEN" \
  -d '{"incident":{"name":"Service Degradation","status":"investigating"}}'
```

---

## Contact Information

### On-Call Rotation
- **Primary**: ops-primary@company.com
- **Secondary**: ops-secondary@company.com
- **Escalation**: engineering-manager@company.com

### External Vendors
- **Cloud Provider**: support@cloudprovider.com
- **DNS Provider**: support@dnsprovider.com
- **Monitoring**: support@monitoringservice.com

---

*Last Updated: $(date)*
*Version: 1.0.0*