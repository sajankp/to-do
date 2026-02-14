# Local Observability Stack

This document explains how to run the FastTodo application with a complete observability stack in your local Docker Compose environment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastTodo Application (Port 8000)             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  OpenTelemetry SDK (auto + manual instrumentation)       │   │
│  │  • Traces: Request flow, DB calls                        │   │
│  │  • Metrics: HTTP metrics, custom business metrics        │   │
│  │  • Logs: Correlated with trace_id                        │   │
│  └────────────────────────┬─────────────────────────────────┘   │
└─────────────────────────────┼────────────────────────────────────┘
                              │ OTLP HTTP (port 4318)
                              │                    ┌──────────────────┐
                              │                    │   Prometheus     │
                              │                    │   (Port 9090)    │
                              │                    │ Scrapes /metrics │
                              │                    └────────┬─────────┘
                              ▼                             │
┌─────────────────────────────────────────────────────────────────┐
│         OpenTelemetry Collector (Ports 4317, 4318)              │
│  • Receives telemetry via OTLP                                  │
│  • Routes traces → Jaeger, logs → Loki                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────┐             ┌──────────────┐
       │    Jaeger    │             │     Loki     │
       │ (Port 16686) │             │ (Port 3100)  │
       └──────┬───────┘             └──────┬───────┘
              │                            │
              └────────────┬───────────────┘
                           ▼
                ┌──────────────────┐
                │     Grafana      │
                │   (Port 3000)    │
                └──────────────────┘
```

## Services

### Application Stack
- **FastTodo App** - http://localhost:8000
- **MongoDB** - localhost:27017

### Observability Stack
- **Grafana** - http://localhost:3000 (admin/admin)
- **Jaeger UI** - http://localhost:16686
- **Prometheus** - http://localhost:9090
- **OpenTelemetry Collector** - localhost:4317 (gRPC), localhost:4318 (HTTP) [traces + logs only]

## Quick Start

### 1. Start All Services

```bash
docker compose up --build
```

### 2. Generate Some Activity

```bash
# Health check
curl http://localhost:8000/health

# Create a user
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"pass123"}'

# Create a todo
curl -X POST http://localhost:8000/todo/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  # Note: Replace YOUR_TOKEN with the access_token received from /token endpoint
  -d '{"title":"Test Todo","description":"Testing observability"}'
```

### 3. View Observability Data

#### Traces in Jaeger
1. Open http://localhost:16686
2. Select Service: **fasttodo**
3. Click "Find Traces"
4. You'll see:
   - HTTP request spans (FastAPI)
   - MongoDB operation spans (insert, find, update, delete)
   - Full request flow with timing

#### Metrics in Prometheus
1. Open http://localhost:9090
2. Try these queries:
   ```promql
   # HTTP request rate
   rate(http_requests_total[1m])

   # User registrations
   fasttodo_registrations_total

   # Todo operations
   rate(fasttodo_todos_created_total[5m])
   ```

#### Unified Dashboard in Grafana
1. Open http://localhost:3000 (login: admin/admin)
2. Datasources are pre-configured:
   - Prometheus (metrics)
   - Jaeger (traces)
   - Loki (logs)
3. Create dashboards or import community dashboards

## MongoDB Tracing

**Important:** The MongoDB client is created AFTER OpenTelemetry instrumentation to ensure database operations are traced.

### Verifying MongoDB Traces

```bash
# Make a request that hits the database
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -d '{"username":"trace_test","email":"test@test.com","password":"test123"}'

# Check Jaeger UI - you should see:
# - POST /user (HTTP span)
# - todo_db.insert (MongoDB span) ✓
```

The MongoDB span will include:
- `db.system`: "mongodb"
- `db.statement`: "insert" / "find" / "update" / "delete"
- `db.name`: "fasttodo_dev"
- `db.mongodb.collection`: "user" or "todo"

## Custom Metrics

The application exposes custom business metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `fasttodo_logins_total` | Counter | Login attempts (labels: status) |
| `fasttodo_registrations_total` | Counter | User registrations |
| `fasttodo_todos_created_total` | Counter | Todos created |
| `fasttodo_todos_completed_total` | Counter | Todos marked complete |
| `fasttodo_todos_deleted_total` | Counter | Todos deleted |

## Configuration

### Environment Variables

The following OpenTelemetry env vars are configured in `docker compose.yml`:

```yaml
OTEL_SERVICE_NAME: fasttodo
OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318
OTEL_TRACES_SAMPLER: always_on
```

### Sampling

- **Local/Dev**: `always_on` (100% of traces)
- **Production**: Should use `parentbased_traceidratio` with 10% sample rate

## Troubleshooting

### No MongoDB Traces?

Check that PyMongo instrumentation is registered:

```bash
docker compose logs app | grep "PyMongo instrumentation"
```

Expected output:
```
✓ PyMongo instrumentation registered. Command listeners: 1
```

### Services Not Starting?

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Reset environment
./scripts/reset_docker.sh
```

### Port Conflicts?

If ports 3000, 9090, 16686, etc. are already in use, edit `docker compose.yml` to change the host port mappings:

```yaml
ports:
  - "3001:3000"  # Change Grafana to port 3001
```

## Development Workflow

### Rebuilding After Code Changes

```bash
# Rebuild and restart
docker compose up --build

# Or just restart app service
docker compose restart app
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f otel-collector
```

### Cleaning Up

```bash
# Stop services
docker compose down

# Remove volumes (data will be lost!)
docker compose down -v

# Full reset
./scripts/reset_docker.sh
```

## Production Deployment (Kubernetes)

For production Kubernetes deployment, see the manifests in `k8s/`:
- `k8s/otel-collector.yaml` - DaemonSet for OTel Collector
- `k8s/jaeger.yaml` - Jaeger deployment
- `k8s/prometheus.yaml` - Prometheus StatefulSet
- `k8s/grafana.yaml` - Grafana with datasources

Apply to cluster:
```bash
kubectl apply -f k8s/
```

## Resources

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

## Related Documentation

- [Spec-005: Monitoring & Observability](docs/specs/005-monitoring.md)
- [ADR-011: OpenTelemetry Observability Stack](docs/adr/011-opentelemetry-observability-stack.md)
