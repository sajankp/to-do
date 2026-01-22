# ADR-011: OpenTelemetry Observability Stack

## Status

**Proposed** (2026-01-18)

## Context

The FastTodo application is being prepared for deployment to a self-hosted Kubernetes cluster. As the architecture may scale to multiple microservices, we need a comprehensive observability solution that provides:

1. **Distributed Tracing:** Track requests across services
2. **Metrics Collection:** Monitor performance and health
3. **Log Correlation:** Link logs to traces for debugging
4. **Kubernetes-Native:** Work seamlessly with K8s infrastructure

### Problem Statement

- No visibility into request flow or performance bottlenecks
- Logs exist (via Spec-004) but aren't correlated with traces
- No health endpoints for K8s probes
- Need vendor-neutral solution for self-hosted infrastructure

## Decision

We will implement **OpenTelemetry (OTel)** as the unified instrumentation layer, exporting to self-hosted open-source backends.

### Stack Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Instrumentation** | Collect telemetry from app | OpenTelemetry SDK |
| **Collection** | Receive, process, route data | OpenTelemetry Collector |
| **Tracing Backend** | Store and visualize traces | Jaeger |
| **Metrics Backend** | Time-series metrics storage | Prometheus |
| **Log Aggregation** | Centralized log storage | Loki |
| **Visualization** | Unified dashboard | Grafana |

### Why NOT Sentry?

Sentry is excellent for error tracking, but:
- Primarily designed for crash/error reporting, not full observability
- Adds vendor dependency for a feature OpenTelemetry handles
- Jaeger + Prometheus alerting covers error tracking use cases
- If needed later, OTel can export to Sentry (vendor-neutral)

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: OpenTelemetry + OSS Stack (Chosen)** | OTel → Jaeger/Prometheus/Loki/Grafana | Vendor-neutral, industry standard, free, full control, microservice-ready | More infrastructure to manage, steeper learning curve |
| B: Sentry + Prometheus | Sentry for errors, Prometheus for metrics | Easy error tracking | Sentry is paid at scale, no distributed tracing |
| C: Datadog/New Relic | Commercial APM | Easy setup, managed | Expensive, vendor lock-in, conflicts with self-hosted goal |
| D: Just Prometheus + Logs | Metrics + structured logs | Minimal setup | No distributed tracing, limited debugging |

## Consequences

### Positive

- **Vendor-neutral:** Can switch backends without code changes
- **Industry standard:** OpenTelemetry is CNCF graduated, widely adopted
- **Microservice-ready:** Distributed tracing across services from day one
- **Cost-effective:** All components are free and open-source
- **Full control:** Self-hosted means complete data ownership
- **Log correlation:** Traces link directly to logs via `trace_id`

### Negative

- **Infrastructure overhead:** Need to deploy Collector, Jaeger, Prometheus, Loki, Grafana
- **Learning curve:** OTel configuration can be complex initially
- **Operational burden:** Self-hosted means we manage upgrades/scaling

### Trade-offs Accepted

- Complexity vs Control: Control wins (we want self-hosted)
- Ease of Setup vs Flexibility: Flexibility wins (vendor-neutral)
- Cost vs Features: Free + full-featured is possible with OSS

## Implementation Notes

### OpenTelemetry Python Dependencies

```
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-pymongo
opentelemetry-instrumentation-logging
prometheus-fastapi-instrumentator
```

### Integration with Existing Logging (Spec-004)

The existing structlog setup will be enhanced to:
1. Inject `trace_id` and `span_id` into log context
2. Export logs to Loki via OTel Collector
3. Enable clicking from Grafana logs → Jaeger traces

### Kubernetes Deployment

OTel Collector will run as a DaemonSet, with backends in dedicated namespace:

```
namespace: observability
├── otel-collector (DaemonSet)
├── jaeger (Deployment)
├── prometheus (StatefulSet)
├── loki (StatefulSet)
└── grafana (Deployment)
```

## Related

- [Spec-005: Monitoring & Observability](../specs/005-monitoring.md)
- [Spec-004: Structured Logging](../specs/004-structured-logging.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
