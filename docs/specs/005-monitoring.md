# Spec-005: Monitoring & Observability

**Status:** Approved
**Related Issue:** TD-005
**Effort:** 3-5 Days
**ADR:** [ADR-011](../adr/011-opentelemetry-observability-stack.md)

---

## Problem Statement

As we prepare to deploy the FastTodo application to a Kubernetes cluster, we lack essential observability capabilities:

1. **No Health Checks:** Kubernetes can't determine if pods are healthy or ready to serve traffic.
2. **No Distributed Tracing:** In a microservices architecture, we can't trace requests across services.
3. **No Metrics:** No visibility into request rates, latencies, or error rates.
4. **Limited Log Correlation:** While we have structured logging (Spec-004), logs aren't correlated with traces.

## Proposed Solution

Implement a comprehensive, self-hosted observability stack using **OpenTelemetry** as the unified instrumentation layer. This provides vendor-neutral telemetry that exports to open-source backends.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastTodo Application                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  OpenTelemetry SDK (auto + manual instrumentation)      │   │
│  │  • Traces: Request flow, DB calls, external APIs        │   │
│  │  • Metrics: Request count, latency, error rates         │   │
│  │  • Logs: Correlated with trace_id and span_id           │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────┘
                               │ OTLP (gRPC/HTTP)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector (K8s DaemonSet)            │
│  • Receives, processes, and exports telemetry                   │
│  • Batching, retry, and routing                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    Jaeger    │     │   Prometheus     │     │     Loki     │
│   (Traces)   │     │   (Metrics)      │     │    (Logs)    │
└──────┬───────┘     └────────┬─────────┘     └──────┬───────┘
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │     Grafana      │
                    │   (Dashboard)    │
                    └──────────────────┘
```

---

## API Changes

### New Endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /health` | Public | Liveness probe (app is running) |
| `GET /health/ready` | Public | Readiness probe (app can serve traffic) |
| `GET /metrics` | Internal | Prometheus metrics scrape endpoint |

### `/health` Response Format

```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T12:00:00Z",
  "version": "1.0.0"
}
```

### `/health/ready` Response Format

```json
{
  "status": "ready",
  "timestamp": "2026-01-18T12:00:00Z",
  "checks": {
    "database": "connected",
    "dependencies": "ok"
  }
}
```

### `/metrics` Response Format

Prometheus text format (scrape target):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/todo/",status="200"} 1234
```

---

## Data Model Changes

### New Response Schemas

| Schema | Fields | Purpose |
|--------|--------|---------|
| `HealthResponse` | `status`, `timestamp`, `version` | Liveness probe response |
| `ReadinessResponse` | `status`, `timestamp`, `checks` | Readiness probe response |

---

## Implementation Plan

### Phase 1: Health Checks (Day 1)

1. **Create health router** (`app/routers/health.py`)
   - `GET /health` - Basic liveness
   - `GET /health/ready` - DB connection check

2. **Add response schemas** (`app/models/health.py`)
   - `HealthResponse`, `ReadinessResponse`

3. **Register router** in `app/main.py`

### Phase 2: OpenTelemetry Instrumentation (Day 2-3)

1. **Add dependencies** to `requirements.txt`:
   - `opentelemetry-api`
   - `opentelemetry-sdk`
   - `opentelemetry-exporter-otlp`
   - `opentelemetry-instrumentation-fastapi`
   - `opentelemetry-instrumentation-pymongo`
   - `opentelemetry-instrumentation-logging`

2. **Create telemetry setup** (`app/utils/telemetry.py`)
   - Configure tracer provider
   - Configure meter provider
   - Configure OTLP exporter
   - Auto-instrument FastAPI, PyMongo

3. **Integrate with existing logging** (Spec-004)
   - Inject `trace_id` and `span_id` into structlog context
   - Ensure log correlation with traces

4. **Environment configuration**:
   - `OTEL_SERVICE_NAME`: Service identifier
   - `OTEL_EXPORTER_OTLP_ENDPOINT`: Collector endpoint
   - `OTEL_TRACES_SAMPLER`: Sampling strategy

### Phase 3: Prometheus Metrics (Day 3-4)

1. **Add dependency**:
   - `prometheus-fastapi-instrumentator`

2. **Instrument application** (`app/main.py`)
   - Request count, latency, status codes
   - Custom business metrics (see below)

3. **Expose `/metrics` endpoint** (internal network only)

---

## Custom Business Metrics

Beyond standard HTTP metrics, track application-specific KPIs:

### User Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `fasttodo_logins_total` | Counter | `status` (success/failed) | Total login attempts |
| `fasttodo_registrations_total` | Counter | - | New user registrations |

> [!NOTE]
> **DAU/WAU/MAU Calculation:** Active user counts (daily/weekly/monthly) are calculated at query time
> via PromQL on the `fasttodo_logins_total` counter, not exported as app metrics.
> Example: `count(increase(fasttodo_logins_total{status="success"}[24h]))`

> [!TIP]
> **Future: Session Tracking with Redis**
> If a Redis session store is introduced, we can add `fasttodo_sessions_active` gauge
> to track real-time active sessions. This requires stateful session management
> (storing session data in Redis with TTL) rather than pure stateless JWTs.

### Todo Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `fasttodo_todos_created_total` | Counter | - | Total todos created |
| `fasttodo_todos_completed_total` | Counter | - | Total todos marked complete |
| `fasttodo_todos_deleted_total` | Counter | - | Total todos deleted |
| `fasttodo_todos_per_user` | Histogram | - | Distribution of todos per user |

### AI Voice Assistant Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `fasttodo_ai_requests_total` | Counter | `status` (success/error) | AI API calls |
| `fasttodo_ai_tokens_used_total` | Counter | `type` (input/output) | Token consumption |
| `fasttodo_ai_latency_seconds` | Histogram | - | AI response time |
| `fasttodo_ai_errors_total` | Counter | `error_type` | AI failures by type |

### System Health Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `fasttodo_db_connections_active` | Gauge | - | Active MongoDB connections |
| `fasttodo_db_query_duration_seconds` | Histogram | `operation` | DB query latency |

### Phase 4: Documentation & Kubernetes Manifests (Day 4-5)

1. **Update ARCHITECTURE.md** with observability section
2. **Create K8s manifests** (in `k8s/` directory):
   - `otel-collector.yaml`
   - `jaeger.yaml`
   - `prometheus.yaml`
   - `grafana.yaml`

---

## Configuration

### New Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OTEL_SERVICE_NAME` | No | `fasttodo` | Service name for traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | `http://localhost:4317` | OTel Collector endpoint |
| `OTEL_TRACES_SAMPLER` | No | `parentbased_traceidratio` | Sampling strategy |
| `OTEL_TRACES_SAMPLER_ARG` | No | `1.0` | Sample 100% in dev |
| `ENABLE_METRICS` | No | `true` | Enable Prometheus metrics |

---

## Test Strategy

> [!IMPORTANT]
> Tests MUST be written BEFORE implementation (TDD Red-Green-Refactor).

### Unit Tests (`app/tests/routers/test_health.py`)

| Test Case | Description |
|-----------|-------------|
| `test_health_returns_200` | Basic liveness probe |
| `test_health_response_schema` | Response matches `HealthResponse` |
| `test_readiness_returns_200_when_db_connected` | Happy path readiness |
| `test_readiness_returns_503_when_db_disconnected` | DB failure handling |
| `test_readiness_response_schema` | Response matches `ReadinessResponse` |

### Unit Tests (`app/tests/utils/test_telemetry.py`)

| Test Case | Description |
|-----------|-------------|
| `test_tracer_provider_configured` | Tracer is set up correctly |
| `test_otel_disabled_when_no_endpoint` | Graceful degradation |
| `test_trace_context_injected_in_logs` | Log correlation works |

### Integration Tests

| Test Case | Description |
|-----------|-------------|
| `test_metrics_endpoint_returns_prometheus_format` | `/metrics` scrape format |
| `test_request_creates_trace_span` | Trace spans are created |

### Manual Verification

1. **Health Checks:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/health/ready
   ```

2. **Metrics Scrape:**
   ```bash
   curl http://localhost:8000/metrics
   ```

3. **Trace Visualization:**
   - Deploy Jaeger locally via Docker
   - Make API requests
   - View traces in Jaeger UI at `http://localhost:16686`

---

## Open Questions

- [x] ~~Self-hosted vs managed observability?~~ → Self-hosted chosen
- [x] ~~Include Sentry for error tracking?~~ → No, use Jaeger + alerting
- [x] ~~Should `/metrics` be protected?~~ → Yes, internal network only (standard practice)
- [x] ~~What sampling rate for production traces?~~ → 10% (industry standard, adjust based on volume)
- [x] ~~Custom business metrics?~~ → Yes, see Custom Business Metrics section above

---

## Learning Resources

> [!TIP]
> **Recommended reading for understanding observability:**

| Topic | Resource |
|-------|----------|
| **OpenTelemetry Basics** | [OpenTelemetry Docs - Getting Started](https://opentelemetry.io/docs/concepts/) |
| **Distributed Tracing** | [Jaeger: Introduction to Distributed Tracing](https://www.jaegertracing.io/docs/latest/architecture/) |
| **Prometheus Best Practices** | [Prometheus: Metric and Label Naming](https://prometheus.io/docs/practices/naming/) |
| **Sampling Strategies** | [Honeycomb: Guide to Sampling](https://www.honeycomb.io/blog/guide-to-sampling-for-distributed-tracing) |
| **Observability Philosophy** | [Charity Majors: Observability Engineering (O'Reilly)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) |
| **K8s Observability** | [CNCF: Kubernetes Observability Primer](https://www.cncf.io/blog/2023/06/26/a-primer-on-kubernetes-observability/) |

---

## Related

- **ADR:** [ADR-011](../adr/011-opentelemetry-observability-stack.md)
- **Depends on:** [Spec-004: Structured Logging](004-structured-logging.md)
- **Roadmap:** TD-005 (Monitoring & Observability)
