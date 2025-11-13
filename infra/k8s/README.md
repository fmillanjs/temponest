# Kubernetes Deployment for TempoNest

This directory contains Kubernetes manifests for deploying TempoNest in production.

## Prerequisites

- Kubernetes 1.24+ cluster
- `kubectl` configured to access your cluster
- Helm 3+ (for cert-manager and Traefik)
- 16GB+ RAM available across nodes
- 100GB+ storage for persistent volumes

## Quick Start

### 1. Install Dependencies

```bash
# Install cert-manager (for SSL certificates)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install Traefik (ingress controller with load balancer)
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm install traefik traefik/traefik -n traefik --create-namespace
```

### 2. Configure Secrets

```bash
# Create namespace
kubectl apply -f 00-namespace.yaml

# Create secrets (edit values first)
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml with your actual values
kubectl apply -f secrets.yaml
```

### 3. Deploy Infrastructure

```bash
# Deploy in order
kubectl apply -f 01-configmaps.yaml
kubectl apply -f 02-storage.yaml
kubectl apply -f 03-databases.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n temponest --timeout=300s
```

### 4. Deploy Services

```bash
kubectl apply -f 04-services.yaml
kubectl apply -f 05-deployments.yaml

# Wait for deployments
kubectl wait --for=condition=available deployment --all -n temponest --timeout=600s
```

### 5. Deploy Ingress & Load Balancer

```bash
kubectl apply -f 06-ingress.yaml

# Get load balancer IP
kubectl get svc traefik -n traefik
```

### 6. Configure DNS

Point your domain to the load balancer IP:

```bash
# Get external IP
EXTERNAL_IP=$(kubectl get svc traefik -n traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add A records
api.temponest.com -> $EXTERNAL_IP
console.temponest.com -> $EXTERNAL_IP
langfuse.temponest.com -> $EXTERNAL_IP
```

## Directory Structure

```
infra/k8s/
├── README.md                    # This file
├── 00-namespace.yaml            # Namespace definition
├── 01-configmaps.yaml           # Configuration maps
├── 02-storage.yaml              # PersistentVolumeClaims
├── 03-databases.yaml            # PostgreSQL, Redis, Qdrant
├── 04-services.yaml             # Kubernetes Services
├── 05-deployments.yaml          # Application deployments
├── 06-ingress.yaml              # Traefik Ingress + Load Balancer
├── 07-autoscaling.yaml          # HorizontalPodAutoscaler
├── 08-monitoring.yaml           # Prometheus, Grafana
├── secrets.example.yaml         # Secret template (do not commit secrets.yaml)
└── kustomization.yaml           # Kustomize configuration
```

## Scaling

### Manual Scaling

```bash
# Scale agents service
kubectl scale deployment agents -n temponest --replicas=5

# Scale scheduler
kubectl scale deployment scheduler -n temponest --replicas=3
```

### Auto-Scaling

Auto-scaling is configured in `07-autoscaling.yaml`:

- **Agents**: 2-10 replicas based on CPU/memory
- **Scheduler**: 1-5 replicas
- **Approval**: 1-3 replicas

## Monitoring

```bash
# View logs
kubectl logs -f deployment/agents -n temponest

# Port-forward to Grafana
kubectl port-forward svc/grafana -n temponest 3001:3000

# Access metrics
kubectl port-forward svc/prometheus -n temponest 9090:9090
```

## Updating

```bash
# Update image
kubectl set image deployment/agents agents=temponest/agents:v1.1.0 -n temponest

# Rolling update (zero downtime)
kubectl rollout status deployment/agents -n temponest

# Rollback if needed
kubectl rollout undo deployment/agents -n temponest
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n temponest

# Describe problematic pod
kubectl describe pod <pod-name> -n temponest

# Check logs
kubectl logs <pod-name> -n temponest
```

### Database connection issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n temponest -- \
  psql -h postgres -U postgres -d agentic
```

### Ingress not working

```bash
# Check ingress status
kubectl get ingress -n temponest

# Check Traefik logs
kubectl logs -n traefik deployment/traefik
```

## Security

- Secrets are base64 encoded (use external secret management in production)
- Network policies isolate services
- RBAC limits service account permissions
- TLS certificates auto-renewed via cert-manager

## Backup & Restore

See [DATABASE_BACKUP_STRATEGY.md](../../docs/DATABASE_BACKUP_STRATEGY.md) for backup procedures.

## Cost Optimization

- Use node selectors for workload placement
- Enable cluster autoscaler
- Use spot/preemptible instances for non-critical workloads
- Set resource requests and limits appropriately

## Production Checklist

- [ ] Configure external secrets (Vault, AWS Secrets Manager)
- [ ] Set up backup automation
- [ ] Configure monitoring alerts
- [ ] Enable audit logging
- [ ] Set up log aggregation (ELK, Loki)
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up disaster recovery
- [ ] Test failover scenarios
- [ ] Document runbooks

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
