# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the FastTodo observability stack.

## Prerequisites

- Kubernetes cluster (v1.21+)
- `kubectl` configured
- `envsubst` utility (usually pre-installed on Linux/Mac)

## Deployment Methods

### Option 1: Environment Variable Substitution (Recommended)

This is the standard Kubernetes approach for handling secrets in manifests.

```bash
# Set required environment variables
export GRAFANA_ADMIN_PASSWORD="your-secure-password"

# Deploy with environment variable substitution
# Safety check: Ensure password is set
[ -z "$GRAFANA_ADMIN_PASSWORD" ] && { echo "Error: GRAFANA_ADMIN_PASSWORD is not set"; exit 1; }

envsubst < k8s/grafana.yaml | kubectl apply -f -
envsubst < k8s/prometheus.yaml | kubectl apply -f -
envsubst < k8s/loki.yaml | kubectl apply -f -
envsubst < k8s/otel-collector.yaml | kubectl apply -f -
envsubst < k8s/jaeger.yaml | kubectl apply -f -
```

### Option 2: CI/CD Pipeline (GitHub Actions, GitLab CI)

Store secrets as GitHub Secrets or CI/CD variables and substitute during deployment:

```yaml
# Example GitHub Actions workflow
- name: Deploy to Kubernetes
  env:
    GRAFANA_ADMIN_PASSWORD: ${{ secrets.GRAFANA_ADMIN_PASSWORD }}
  run: |
    envsubst < k8s/grafana.yaml | kubectl apply -f -
```

### Option 3: External Secrets Operator (Production)

For production environments, use [External Secrets Operator](https://external-secrets.io/) with:
- HashiCorp Vault
- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault

Example with External Secrets Operator:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: grafana-admin-secret
  namespace: observability
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: grafana-admin-secret
  data:
  - secretKey: admin-password
    remoteRef:
      key: observability/grafana
      property: admin-password
```

### Option 4: Manual Secret Creation (Development Only)

For local development/testing:

```bash
kubectl create secret generic grafana-admin-secret \
  --from-literal=admin-password='development-password' \
  -n observability
```

## Deployment Order

1. Create namespace:
   ```bash
   kubectl create namespace observability
   ```

2. Deploy components in this order:
   ```bash
   # 1. Loki (log aggregation)
   kubectl apply -f k8s/loki.yaml

   # 2. Jaeger (distributed tracing)
   kubectl apply -f k8s/jaeger.yaml

   # 3. Prometheus (metrics)
   kubectl apply -f k8s/prometheus.yaml

   # 4. OpenTelemetry Collector
   kubectl apply -f k8s/otel-collector.yaml

   # 5. Grafana (dashboards) - requires GRAFANA_ADMIN_PASSWORD
   export GRAFANA_ADMIN_PASSWORD="your-password"
   envsubst < k8s/grafana.yaml | kubectl apply -f -
   ```

## Accessing Services

After deployment, access services using port-forwarding:

```bash
# Grafana (port 3000)
kubectl port-forward -n observability svc/grafana 3000:3000

# Jaeger UI (port 16686)
kubectl port-forward -n observability svc/jaeger-query 16686:16686

# Prometheus (port 9090)
kubectl port-forward -n observability svc/prometheus 9090:9090
```

Or configure Ingress for production access.

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for secret substitution
3. **Rotate secrets regularly** in production
4. **Use RBAC** to limit access to secrets
5. **Enable audit logging** for secret access
6. **Use External Secrets Operator** for production deployments

## Cleanup

```bash
kubectl delete namespace observability
```
