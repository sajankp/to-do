# Spec: Local Development Environment & Observability

## Status
In Review

## Problem Statement
The current local development setup is fragmented. The backend runs via `docker-compose` (or locally), while the frontend must be run separately. Additionally, the planned Observability Stack (Spec-005) requires multiple services (Jaeger, Prometheus, Loki, Grafana, OpenTelemetry Collector) to be orchestrated for effective local testing and verification. We need a unified `docker-compose` configuration that runs the entire stack ("everything"), enabling comprehensive local testing of the application and its observability features.

## Proposed Solution
Create a robust `docker-compose.yml` that orchestrates:
1.  **Frontend**: A new containerized version of the React/Vite frontend.
2.  **Backend**: The existing FastAPI application (enhanced with Prometheus metrics per Spec-005 Phase 3).
3.  **Database**: MongoDB (existing).
4.  **Observability Stack**:
    - **OpenTelemetry Collector**: To receive traces, metrics, and logs.
    - **Jaeger**: For distributed tracing.
    - **Prometheus**: For metrics collection.
    - **Loki**: For log aggregation.
    - **Grafana**: For visualization (pre-configured with datasources).

This setup will allow "one-command" startup (`docker-compose up --build`) and local verification of the full feature set.

## API Changes
No new API changes beyond those already defined in Spec-005 (e.g., `/metrics`, `/health`).

## Implementation Plan

### 1. Frontend Dockerization
- Create `Dockerfile` in `../to-do-frontend`.
- Use a lightweight node image for development (or Nginx for production-like preview, but development mode is preferred for local testing).

### 2. Observability Configuration
- Create `config/` directory in the backend repo.
- Add configuration files:
    - `otel-collector-config.yaml`
    - `prometheus.yaml`
    - `loki-config.yaml`
    - `grafana/provisioning/datasources/datasource.yaml`

### 3. Backend Instrumentation (Spec-005 Phase 3)
- Add `prometheus-fastapi-instrumentator` to `requirements.txt`.
- Update `app/main.py` to instrument the app and expose `/metrics`.
- Add Custom Metrics (Logins, Todos, AI Usage) as defined in Spec-005.

### 4. Docker Compose Update
- Update `docker-compose.yml` to include all services.
- Ensure proper networking and volume mounts.
- Set environment variables for OTel endpoint and Mongo URI.

### 5. Kubernetes Manifests (Spec-005 Phase 4)
- Create `k8s/` directory.
- Add manifests for `otel-collector`, `prometheus`, `jaeger`, `grafana`, `loki`.

## Current Implementation Notes (as of 2026-02-15)

- `docker-compose.yml` orchestrates backend, MongoDB, and the observability stack (OTel Collector, Jaeger, Prometheus, Loki, Grafana).
- Frontend is not containerized in this repo; there is no frontend service in `docker-compose.yml`.
- Observability config files live at repo root (`otel-collector-config.yaml`, `prometheus.yml`, `grafana-datasources.yml`) rather than under a `config/` directory.

## Test Strategy

### Automated Tests
- **Backend**: Existing tests + new tests for `/metrics` endpoint (Spec-005).
- **Integration**: Verify services can communicate (e.g., App -> Mongo, App -> OTel Collector).

### Manual Verification
1.  Run `docker-compose up --build`.
2.  **Frontend**: Access `http://localhost:5173` (or configured port). Verify it loads and fetches data from backend.
3.  **Backend**: `curl http://localhost:8000/health` returns 200.
4.  **Metrics**: `curl http://localhost:8000/metrics` returns Prometheus text format.
5.  **Grafana**: Access `http://localhost:3000`. Verify datasources (Prometheus, Jaeger, Loki) are active.
6.  **Jaeger**: Access `http://localhost:16686`. Verify traces from API requests appear.

## Open Questions
- [x] **Frontend Port**: Will verify if 5173 is accessible or needs mapping. -> Yes, will map 5173:5173.
- [x] **Frontend Connection**: How does frontend talk to backend? -> `vite.config.ts` proxy or env var. `docker-compose` service name `app` works internally, but browser access needs localhost. We will configure frontend to use localhost:8000 for API calls since it runs in browser.

## Related
- **Spec-005**: [Monitoring & Observability](005-monitoring.md)
- **ADR-011**: [OpenTelemetry Observability Stack](../adr/011-opentelemetry-observability-stack.md)
