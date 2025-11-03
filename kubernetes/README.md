# Kubernetes Deployment Guide for Auth Microservice

This directory contains all Kubernetes manifests needed to deploy the auth microservice.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker image built and pushed to registry
- Ingress controller installed (nginx-ingress recommended)
- cert-manager (optional, for SSL certificates)

## Files Overview

```
kubernetes/
├── namespace.yaml              # Create auth-service namespace
├── configmap.yaml             # Non-sensitive configuration
├── secrets.yaml               # Sensitive data (DB credentials, JWT secret)
├── postgres-deployment.yaml   # PostgreSQL database deployment
├── auth-deployment.yaml       # Auth service deployment
├── auth-service.yaml          # Service for auth pods
├── auth-hpa.yaml              # Horizontal Pod Autoscaler
├── ingress.yaml               # Ingress for external access
├── network-policy.yaml        # Network security policies
├── service-monitor.yaml       # Prometheus monitoring (optional)
└── README.md                  # This file
```

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/auth-service:v1.0.0 .

# Push to registry
docker push your-registry/auth-service:v1.0.0

# Or use docker-compose to build
docker-compose build auth-service
docker tag auth-service:latest your-registry/auth-service:v1.0.0
docker push your-registry/auth-service:v1.0.0
```

### 2. Update Configuration

**Edit `secrets.yaml`:**
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Update secrets.yaml with:
# - DATABASE_URL
# - SECRET_KEY
# - POSTGRES_PASSWORD
```

**Edit `auth-deployment.yaml`:**
```yaml
# Replace with your actual image
image: your-registry/auth-service:v1.0.0
```

**Edit `ingress.yaml`:**
```yaml
# Replace with your domain
host: auth.yourdomain.com
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create secrets (do this first!)
kubectl apply -f kubernetes/secrets.yaml

# Create configmap
kubectl apply -f kubernetes/configmap.yaml

# Deploy PostgreSQL
kubectl apply -f kubernetes/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n auth-service --timeout=120s

# Deploy auth service
kubectl apply -f kubernetes/auth-deployment.yaml

# Create service
kubectl apply -f kubernetes/auth-service.yaml

# Deploy HPA (optional but recommended)
kubectl apply -f kubernetes/auth-hpa.yaml

# Deploy ingress (for external access)
kubectl apply -f kubernetes/ingress.yaml

# Deploy network policy (optional, for security)
kubectl apply -f kubernetes/network-policy.yaml

# Deploy service monitor (if using Prometheus)
kubectl apply -f kubernetes/service-monitor.yaml
```

### 4. Verify Deployment

```bash
# Check namespace
kubectl get all -n auth-service

# Check pods status
kubectl get pods -n auth-service -w

# Check logs
kubectl logs -f deployment/auth-service -n auth-service

# Check service
kubectl get svc -n auth-service

# Check ingress
kubectl get ingress -n auth-service

# Check HPA status
kubectl get hpa -n auth-service
```

### 5. Test the Service

```bash
# Port forward for local testing
kubectl port-forward svc/auth-service 8000:8000 -n auth-service

# Test health endpoint
curl http://localhost:8000/health

# Or test via ingress (if configured)
curl https://auth.yourdomain.com/health
```

## Deployment Order

**Important:** Deploy in this order:

1. ✅ namespace.yaml
2. ✅ secrets.yaml (edit first!)
3. ✅ configmap.yaml
4. ✅ postgres-deployment.yaml
5. ✅ Wait for PostgreSQL to be ready
6. ✅ auth-deployment.yaml
7. ✅ auth-service.yaml
8. ✅ auth-hpa.yaml
9. ✅ ingress.yaml
10. ✅ network-policy.yaml
11. ✅ service-monitor.yaml (optional)

## One-Command Deployment

```bash
# Apply all manifests in order
kubectl apply -f kubernetes/namespace.yaml && \
kubectl apply -f kubernetes/secrets.yaml && \
kubectl apply -f kubernetes/configmap.yaml && \
kubectl apply -f kubernetes/postgres-deployment.yaml && \
sleep 30 && \
kubectl apply -f kubernetes/auth-deployment.yaml && \
kubectl apply -f kubernetes/auth-service.yaml && \
kubectl apply -f kubernetes/auth-hpa.yaml && \
kubectl apply -f kubernetes/ingress.yaml && \
kubectl apply -f kubernetes/network-policy.yaml
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment auth-service --replicas=5 -n auth-service

# Check status
kubectl get pods -n auth-service
```

### Auto-scaling (HPA)

The HPA is configured to:
- Minimum replicas: 3
- Maximum replicas: 10
- Scale based on CPU (70%) and Memory (80%)

```bash
# Check HPA status
kubectl get hpa -n auth-service

# Describe HPA for details
kubectl describe hpa auth-hpa -n auth-service
```

## Monitoring

### Check Logs

```bash
# All pods
kubectl logs -f deployment/auth-service -n auth-service

# Specific pod
kubectl logs -f <pod-name> -n auth-service

# Previous instance (if pod crashed)
kubectl logs <pod-name> -n auth-service --previous
```

### Check Metrics

```bash
# Pod metrics
kubectl top pods -n auth-service

# Node metrics
kubectl top nodes
```

### Check Events

```bash
# Recent events
kubectl get events -n auth-service --sort-by='.lastTimestamp'
```

## Updating the Service

### Rolling Update

```bash
# Update image
kubectl set image deployment/auth-service \
  auth-service=your-registry/auth-service:v1.0.1 \
  -n auth-service

# Check rollout status
kubectl rollout status deployment/auth-service -n auth-service

# Check history
kubectl rollout history deployment/auth-service -n auth-service
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/auth-service -n auth-service

# Rollback to specific revision
kubectl rollout undo deployment/auth-service --to-revision=2 -n auth-service
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n auth-service

# Check logs
kubectl logs <pod-name> -n auth-service

# Check events
kubectl get events -n auth-service --field-selector involvedObject.name=<pod-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -l app=postgres -n auth-service

# Check PostgreSQL logs
kubectl logs -f <postgres-pod-name> -n auth-service

# Test connection from auth pod
kubectl exec -it <auth-pod-name> -n auth-service -- \
  psql -h postgres-service -U auth_user -d auth_db
```

### Service Not Accessible

```bash
# Check service
kubectl get svc auth-service -n auth-service

# Check endpoints
kubectl get endpoints auth-service -n auth-service

# Check ingress
kubectl describe ingress auth-ingress -n auth-service
```

### Debug with Shell

```bash
# Get shell in running pod
kubectl exec -it <pod-name> -n auth-service -- /bin/sh

# Or use a debug container
kubectl debug <pod-name> -n auth-service -it --image=busybox
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace auth-service

# Or delete individually
kubectl delete -f kubernetes/
```

## Production Considerations

### 1. Secrets Management

**Don't use plain secrets.yaml in production!** Use:

- **Sealed Secrets**: Encrypt secrets before committing
  ```bash
  kubeseal --format=yaml < secrets.yaml > sealed-secrets.yaml
  kubectl apply -f sealed-secrets.yaml
  ```

- **External Secrets Operator**: Sync from Vault/AWS/Azure
  ```yaml
  apiVersion: external-secrets.io/v1beta1
  kind: ExternalSecret
  metadata:
    name: auth-secrets
  spec:
    secretStoreRef:
      name: vault-backend
      kind: SecretStore
    target:
      name: auth-secrets
    data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: database-url
  ```

### 2. Database

**Use managed PostgreSQL** instead of in-cluster:
- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases

Update `DATABASE_URL` in secrets to point to managed instance.

### 3. Persistent Volumes

**Use proper storage classes**:
```yaml
storageClassName: fast-ssd  # Use your cluster's storage class
```

### 4. Resource Limits

Adjust based on load testing:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### 5. High Availability

- Deploy across multiple availability zones
- Use pod disruption budgets
- Configure pod anti-affinity

```yaml
# Pod Disruption Budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: auth-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: auth
```

### 6. SSL Certificates

Install cert-manager for automatic SSL:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### 7. Monitoring

Install Prometheus & Grafana:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### 8. Logging

Use centralized logging:
- EFK Stack (Elasticsearch, Fluentd, Kibana)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Cloud provider logging (CloudWatch, Stackdriver)

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY }}/auth-service:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY }}/auth-service:${{ github.sha }}
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/auth-service \
          auth-service=${{ secrets.REGISTRY }}/auth-service:${{ github.sha }} \
          -n auth-service
```

## Support

For issues or questions:
1. Check pod logs: `kubectl logs -f deployment/auth-service -n auth-service`
2. Check events: `kubectl get events -n auth-service`
3. Review main README.md for application-specific issues
