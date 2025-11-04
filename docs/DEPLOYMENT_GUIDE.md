# Temponest Agentic Platform - Production Deployment Guide

This guide covers deploying the Temponest agentic platform to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Database Setup](#database-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Scaling Guidelines](#scaling-guidelines)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [ ] Review infrastructure requirements
- [ ] Set up SSL/TLS certificates
- [ ] Configure environment variables
- [ ] Set up database with backups
- [ ] Configure authentication/authorization
- [ ] Set up monitoring and alerting
- [ ] Test in staging environment
- [ ] Prepare rollback plan
- [ ] Document deployment process
- [ ] Set up CI/CD pipeline

---

## Infrastructure Requirements

### Minimum Requirements (Small Deployment)

**Agent Service:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD

**Scheduler Service:**
- CPU: 1 core
- RAM: 2 GB
- Disk: 10 GB SSD

**PostgreSQL Database:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 50 GB SSD (with automatic backups)

**Qdrant Vector DB:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 50 GB SSD

**Monitoring Stack (Prometheus, Grafana, AlertManager):**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 50 GB SSD

### Recommended Requirements (Medium Deployment)

**Agent Service:**
- CPU: 4-8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- Instances: 2-3 (load balanced)

**Scheduler Service:**
- CPU: 2-4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- Instances: 2 (active-passive)

**PostgreSQL:**
- CPU: 4-8 cores
- RAM: 16 GB
- Disk: 200 GB SSD
- Setup: Primary + Standby replica

**Qdrant:**
- CPU: 4 cores
- RAM: 16 GB
- Disk: 200 GB SSD
- Setup: Cluster with 3 nodes

---

## Docker Deployment

### 1. Prepare Environment

**Create production environment file:**

```bash
# /home/doctor/temponest/.env.production
# Database
DATABASE_URL=postgresql://postgres:CHANGE_ME@agentic-db:5432/agentic_platform

# Qdrant
QDRANT_URL=http://agentic-qdrant:6333
QDRANT_API_KEY=CHANGE_ME

# Langfuse
LANGFUSE_PUBLIC_KEY=CHANGE_ME
LANGFUSE_SECRET_KEY=CHANGE_ME
LANGFUSE_HOST=http://agentic-langfuse:3000

# Security
SECRET_KEY=CHANGE_ME_TO_RANDOM_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=CHANGE_ME

# Model Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
DEFAULT_MODEL=llama3.2:latest

# Multi-Tenancy
ENABLE_MULTI_TENANCY=true
ENFORCE_TENANT_ISOLATION=true
```

### 2. Production Docker Compose

**Create `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  agentic-db:
    image: postgres:15
    container_name: agentic-db-prod
    restart: always
    environment:
      POSTGRES_DB: agentic_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data-prod:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - agentic-network-prod
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  agentic-qdrant:
    image: qdrant/qdrant:latest
    container_name: agentic-qdrant-prod
    restart: always
    volumes:
      - qdrant-data-prod:/qdrant/storage
    ports:
      - "6333:6333"
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    networks:
      - agentic-network-prod
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  agents:
    build:
      context: ../services/agents
      dockerfile: Dockerfile
    container_name: agentic-agents-prod
    restart: always
    env_file:
      - .env.production
    depends_on:
      - agentic-db
      - agentic-qdrant
    ports:
      - "9000:9000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - agentic-network-prod
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4'
          memory: 8G

  scheduler:
    build:
      context: ../services/scheduler
      dockerfile: Dockerfile
    container_name: agentic-scheduler-prod
    restart: always
    env_file:
      - .env.production
    depends_on:
      - agentic-db
      - agents
    ports:
      - "9003:9003"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - agentic-network-prod
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G

  prometheus:
    image: prom/prometheus:latest
    container_name: agentic-prometheus-prod
    restart: always
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=90d'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    ports:
      - "9091:9090"
    volumes:
      - ../infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ../infra/prometheus/alerts:/etc/prometheus/alerts
      - prometheus-data-prod:/prometheus
    networks:
      - agentic-network-prod
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  grafana:
    image: grafana/grafana:latest
    container_name: agentic-grafana-prod
    restart: always
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_SERVER_ROOT_URL=https://monitoring.yourdomain.com
    ports:
      - "3003:3000"
    volumes:
      - ../infra/grafana/provisioning:/etc/grafana/provisioning
      - ../infra/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data-prod:/var/lib/grafana
    networks:
      - agentic-network-prod
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

volumes:
  postgres-data-prod:
  qdrant-data-prod:
  prometheus-data-prod:
  grafana-data-prod:

networks:
  agentic-network-prod:
    driver: bridge
```

### 3. Deploy to Production

```bash
cd /home/doctor/temponest/docker

# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are healthy
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: temponest-prod
```

### 2. Database Deployment

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: temponest-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "agentic_platform"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: temponest-prod
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
  clusterIP: None
```

### 3. Agent Service Deployment

```yaml
# agents-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agents
  namespace: temponest-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agents
  template:
    metadata:
      labels:
        app: agents
    spec:
      containers:
      - name: agents
        image: your-registry/temponest-agents:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agents
  namespace: temponest-prod
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 9000
  selector:
    app: agents
```

### 4. Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: temponest-ingress
  namespace: temponest-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: temponest-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agents
            port:
              number: 80
```

### 5. Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f agents-deployment.yaml
kubectl apply -f scheduler-deployment.yaml
kubectl apply -f ingress.yaml

# Verify deployments
kubectl get pods -n temponest-prod
kubectl get services -n temponest-prod
kubectl get ingress -n temponest-prod
```

---

## Database Setup

### 1. Initialize Database

```bash
# Run migrations
docker exec -it agentic-db-prod psql -U postgres -d agentic_platform -f /schema/init.sql
```

### 2. Create Backup Script

```bash
#!/bin/bash
# /scripts/backup-db.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agentic_platform_$TIMESTAMP.sql.gz"

# Create backup
docker exec agentic-db-prod pg_dump -U postgres agentic_platform | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

### 3. Schedule Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /scripts/backup-db.sh
```

---

## Security Configuration

### 1. SSL/TLS Setup

```bash
# Generate SSL certificates (or use Let's Encrypt)
certbot certonly --standalone -d api.yourdomain.com
```

### 2. API Authentication

Configure JWT authentication in `.env.production`:

```bash
SECRET_KEY=your-very-long-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Network Security

```bash
# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 4. Secrets Management

Use environment-specific secrets:

```bash
# Never commit .env.production to version control
echo ".env.production" >> .gitignore

# Use secret management tools
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

---

## Monitoring Setup

### Access Monitoring Dashboards

- **Grafana:** https://monitoring.yourdomain.com
- **Prometheus:** https://prometheus.yourdomain.com
- **AlertManager:** https://alerts.yourdomain.com

### Configure Alerts

Edit `/infra/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'production-alerts'
    email_configs:
      - to: 'ops@yourdomain.com'
        from: 'alerts@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@yourdomain.com'
        auth_password: 'app-password'

    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#production-alerts'
```

---

## Scaling Guidelines

### Horizontal Scaling

**Agent Service:**
```bash
# Docker Swarm
docker service scale agents=5

# Kubernetes
kubectl scale deployment agents --replicas=5 -n temponest-prod
```

**Auto-scaling with Kubernetes:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agents-hpa
  namespace: temponest-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agents
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Backup and Recovery

### Automated Backups

```bash
# Backup script with retention
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d)

# Database
pg_dump -h localhost -U postgres agentic_platform > $BACKUP_DIR/db_$DATE.sql

# Qdrant
tar -czf $BACKUP_DIR/qdrant_$DATE.tar.gz /var/lib/qdrant

# Upload to S3
aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/temponest/ --recursive
```

### Disaster Recovery

```bash
# Restore database
psql -U postgres agentic_platform < backup.sql

# Restore Qdrant
tar -xzf qdrant_backup.tar.gz -C /var/lib/qdrant
```

---

## Troubleshooting

### Check Service Health

```bash
# All services
curl https://api.yourdomain.com/health

# Database connection
docker exec agentic-db-prod pg_isready

# Check logs
docker-compose logs agents -f --tail=100
```

### Common Issues

**High CPU Usage:**
```bash
# Check container stats
docker stats

# Scale up if needed
docker-compose up -d --scale agents=5
```

**Database Connection Pool Exhausted:**
```bash
# Increase pool size in config
# Check database connections
SELECT count(*) FROM pg_stat_activity;
```

---

## Post-Deployment

1. Verify all endpoints are accessible
2. Run smoke tests
3. Monitor metrics for 24 hours
4. Set up log aggregation
5. Document deployment
6. Train operations team
7. Set up on-call rotation

---

## Additional Resources

- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
