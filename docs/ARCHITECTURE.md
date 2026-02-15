# FastTodo System Specification

> **Living Document** | Last Updated: 2026-01-18
> This is the canonical reference for the FastTodo system architecture, design decisions, and known challenges.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Component Specifications](#component-specifications)
4. [API Contract](#api-contract)
5. [Data Models](#data-models)
6. [Security Architecture](#security-architecture)
7. [Known Architectural Pitfalls](#known-architectural-pitfalls)
8. [Technical Debt Registry](#technical-debt-registry)
9. [Evolution Roadmap](#evolution-roadmap)

---

> [!CAUTION]
> ## 🚨 Development Workflow - READ THIS FIRST
>
> **For AI Agents and Developers:**
> This ARCHITECTURE.md is the **single source of truth** for the **current system state**. It describes what IS, not what WILL be.
>
> **Correct workflow for architectural changes:**
> ```
> 1. Create Spec (docs/specs/) - Document WHAT to build and HOW
> 2. Create ADR (docs/adr/) - Document WHY this approach
> 3. Get approval, implement code
> 4. Update ARCHITECTURE.md - NOW it reflects reality
> ```
>
> **❌ DO NOT:**
> - Update ARCHITECTURE.md before implementation (plans ≠ reality)
> - Document future plans in ARCHITECTURE.md (use specs/roadmap instead)
> - Create code before Spec + ADR for architectural changes
>
> **✅ DO:**
> - Keep ARCHITECTURE.md in sync with implemented code
> - Document current architectural concerns in "Known Architectural Pitfalls"
> - Add planned changes to ROADMAP.md, not here
> - Update ARCHITECTURE.md in the same PR as the implementation
>
> **Why:** This prevents documentation drift. ARCHITECTURE.md always reflects the running system, making it trustworthy for new developers and future maintainers.

---

## System Overview

### Purpose
FastTodo is a production-grade todo management application demonstrating modern web development practices with AI-assisted development workflows.

### Repositories

| Repository | Purpose | Tech Stack |
|------------|---------|------------|
| [sajankp/to-do](https://github.com/sajankp/to-do) | Backend API | FastAPI, MongoDB, Python 3.13 |
| [sajankp/to-do-frontend](https://github.com/sajankp/to-do-frontend) | Web Client | React 19, TypeScript, Vite |

### Deployment

| Environment | Backend | Frontend |
|-------------|---------|----------|
| Production | https://to-do-4w0k.onrender.com | TBD |
| Local Dev | http://localhost:8000 | http://localhost:3000 |

---

## Architecture

### System Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[React Web App]
        VOICE[Voice Assistant<br/>Gemini AI]
    end

    subgraph "API Layer"
        GW[FastAPI Gateway]
        MW[Middleware Stack]
        RATE[Rate Limiter]
        CORS[CORS Handler]
        AUTH_MW[Auth Middleware]
    end

    subgraph "Business Layer"
        AUTH[Auth Router]
        TODO[Todo Router]
        USER[User Router]
        AI[AI Stream Proxy]

    end

    subgraph "Data Layer"
        MONGO[(MongoDB Atlas)]
        GEMINI[Gemini API]
    end

    subgraph "Observability Layer"
        OTEL[OTel Collector]
        PROM[Prometheus]
        JAEGER[Jaeger]
        LOKI[Loki]
        GRAFANA[Grafana]
    end

    WEB --> GW
    VOICE --> GW
    GW --> MW
    MW --> RATE
    MW --> CORS
    MW --> AUTH_MW
    AUTH_MW --> AUTH
    AUTH_MW --> TODO
    AUTH_MW --> USER
    AUTH_MW --> AI

    AUTH --> MONGO
    TODO --> MONGO
    USER --> MONGO
    AI --> GEMINI

    GW -.-> OTEL
    AUTH -.-> OTEL
    TODO -.-> OTEL
    USER -.-> OTEL
    AI -.-> OTEL

    OTEL --> PROM
    OTEL --> JAEGER
    OTEL --> LOKI
    PROM --> GRAFANA
    JAEGER --> GRAFANA
    LOKI --> GRAFANA

```

### Current Architecture Pattern

**Monolithic API with Direct Database Access**

```
Routers → MongoDB (Direct)
```

This is the simplest pattern but has limitations at scale.

### Target Architecture Pattern

**Layered Architecture with Repository Pattern**

```
Routers → Services → Repositories → MongoDB
```

This provides:
- Testability (mock repositories)
- Separation of concerns
- Database abstraction

---

## Component Specifications

### Backend Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `main.py` | `app/main.py` | Application entry, middleware stack, root endpoints |
| `config.py` | `app/config.py` | Environment configuration via Pydantic Settings |
| `security.py` | `app/middleware/security.py` | Security headers middleware (OWASP) |
| `logging.py` | `app/middleware/logging.py` | Structured logging middleware (Trace ID, Session ID) |
| `auth.py` | `app/routers/auth.py` | JWT token creation, password hashing, user lookup |
| `todo.py` | `app/routers/todo.py` | Todo CRUD operations |
| `user.py` | `app/routers/user.py` | User profile endpoints |
| `ai_stream.py` | `app/routers/ai_stream.py` | WebSocket proxy for Gemini Live |
| `mongodb.py` | `app/database/mongodb.py` | MongoDB client initialization |

### Frontend Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `App.tsx` | Root | Auth state management, route switching |
| `AuthForm.tsx` | `components/` | Login/registration forms |
| `TodoList.tsx` | `components/` | Todo CRUD UI, filtering, search |
| `VoiceAssistant.tsx` | `components/` | Gemini AI voice control |
| `api.ts` | `services/` | API client, auth headers, error handling |

---

## API Contract

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant DB as MongoDB

    Note over C,A: Registration
    C->>A: POST /user (body: {username, email, password})
    A->>DB: Insert user (hashed password)
    A-->>C: true

    Note over C,A: Login
    C->>A: POST /token (form: username, password)
    A->>DB: Find user, verify password
    A-->>C: {access_token, refresh_token}

    Note over C,A: Authenticated Request
    C->>A: GET /todo (Authorization: Bearer token)
    A->>A: Validate token, extract user_id
    A->>DB: Find todos by user_id
    A-->>C: [todos]

    Note over C,A: Token Refresh
    C->>A: POST /token/refresh?refresh_token=X
    A->>A: Validate refresh token
    A-->>C: {new access_token}
```

### Endpoints Summary

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| POST | `/token` | ❌ | 5/min | Login, get tokens |
| POST | `/token/refresh` | ❌ | 5/min | Refresh access token |
| POST | `/user` | ❌ | 5/min | Register new user |
| GET | `/user/me` | ✅ | 100/min | Get current user profile |
| GET | `/todo/` | ✅ | 100/min | List user's todos |
| POST | `/todo/` | ✅ | 100/min | Create todo |
| GET | `/todo/{id}` | ✅ | 100/min | Get specific todo |
| PATCH | `/todo/{id}` | ✅ | 100/min | Update todo |
| DELETE | `/todo/{id}` | ✅ | 100/min | Delete todo |
| GET | `/health` | ✅ | - | Health check |

---

## Data Models

### User Model

```python
class UserInDB:
    id: ObjectId           # MongoDB _id
    username: str          # Unique, required
    email: EmailStr        # Unique, required
    hashed_password: str   # bcrypt hash
    is_verified: bool      # Email verification status (default: False)
    disabled: bool         # Account status (default: False)
    created_at: datetime   # Auto-set
    updated_at: datetime   # Auto-updated
```

### Todo Model

```python
class TodoInDB:
    id: ObjectId           # MongoDB _id
    user_id: ObjectId      # Owner reference
    title: str             # 1-100 chars, required
    description: str       # 0-500 chars
    due_date: datetime     # Optional, must be future
    priority: Enum         # low | medium | high
    completed: bool        # Completion status (default: False)
    created_at: datetime   # Auto-set
    updated_at: datetime   # Auto-updated
```

### Model Relationships

```mermaid
erDiagram
    USER ||--o{ TODO : "owns"
    USER {
        ObjectId id PK
        string username UK
        string email UK
        string hashed_password
        boolean is_verified
        boolean disabled
    }
    TODO {
        ObjectId id PK
        ObjectId user_id FK
        string title
        string description
        datetime due_date
        enum priority
    }
```

---

## Security Architecture

### Authentication

| Aspect | Implementation |
|--------|----------------|
| Algorithm | HS256 (HMAC-SHA256) |
| Access Token TTL | 30 minutes |
| Refresh Token TTL | 1 hour |
| Password Hashing | bcrypt with salt |
| Token Storage | Client-side (localStorage) |

### Authorization

| Rule | Implementation |
|------|----------------|
| User Isolation | Todos filtered by `user_id` from JWT |
| Ownership Check | Update/delete verify `todo.user_id == request.user_id` |
| Middleware | All routes except whitelist require valid JWT |

### Rate Limiting

| Endpoint Type | Limit | Strategy |
|---------------|-------|----------|
| Auth endpoints | 5/minute | IP-based |
| API endpoints | 100/minute | IP-based |
| Storage | In-memory (Redis optional) |

---

## Known Architectural Pitfalls

> [!CAUTION]
> These are architectural concerns that should be addressed before scaling.

### 1. (TD-001) Synchronous Database Operations

**Current State:**
```python
# All DB calls block the event loop
result = request.app.todo.insert_one(todo_dict)  # Blocking!
```
**Risk:**
- Under high load, blocked threads exhaust worker pool
- 100+ concurrent users could cause timeouts
- FastAPI's async benefits negated

**Mitigation:**
- Migrate to Motor (async MongoDB driver)
- Requires all route handlers become `async def`
- Estimated effort: 2-3 days

---

### 2. (TD-002) No Database Indexes

**Current State:**
- No indexes defined on collections
- Every query does collection scan

**Risk:**
- O(n) query time as data grows
- 10,000+ todos = noticeable latency

**Mitigation:**
```python
# Recommended indexes
todos.create_index([("user_id", 1)])
todos.create_index([("user_id", 1), ("priority", 1)])
todos.create_index([("user_id", 1), ("due_date", 1)])
users.create_index([("username", 1)], unique=True)
users.create_index([("email", 1)], unique=True)
```

---

### 3. (TD-003) Token in localStorage (XSS Vulnerable)

**Current State:**
```typescript
localStorage.setItem('token', response.access_token);
```

**Risk:**
- XSS attack can steal tokens
- No way to revoke tokens server-side

**Mitigation Options:**
1. **HttpOnly cookies** - Prevents XSS access
2. **Token rotation** - Limit damage window
3. **Token blacklist** - Server-side revocation

---

### 4. (TD-004) No Email Uniqueness Enforcement

**Current State:**
```python
def create_user(username: str, email: str, password: str):
    # No check for duplicate email
    user = CreateUser(username=username, email=email, ...)
    result = request.app.user.insert_one(user.model_dump())
```

**Risk:**
- Same email can register multiple times
- Password reset will be ambiguous
- Email verification won't work properly

**Mitigation:**
1. Add unique index on email field
2. Check before insert, return 409 Conflict
3. Consider username uniqueness too

---

### 5. (TD-005) Missing Request Validation Limits

**Current State:**
- No max request body size
- No timeout on long-running requests

**Risk:**
- Large payload DoS attacks
- Memory exhaustion

**Mitigation:**
```python
# In uvicorn/nginx config
limit_request_body_size = 1MB
request_timeout = 30s
```

---

### 6. (TD-008) Frontend Token Refresh Not Implemented

**Current State:**
```typescript
// Token expires → User silently logged out
// No automatic refresh attempt
```

**Risk:**
- Poor UX (30-min session hard limit)
- Users lose work if editing when token expires

**Mitigation:**
```typescript
// Intercept 401, attempt refresh, retry request
const fetchWithAuth = async (url, options) => {
  let response = await fetch(url, options);
  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) response = await fetch(url, options);
  }
  return response;
};
```

---

### 7. (TD-009) No API Versioning

**Current State:**
```
GET /todo/
```

**Risk:**
- Breaking changes affect all clients
- No deprecation path

**Mitigation:**
```
GET /v1/todo/
GET /v2/todo/  # New format
```

---







---



### 11. (TD-005) Missing Monitoring & Observability [RESOLVED]
**Status:** Implemented (Spec-005)

**Implementation:**
- **Metrics:** OpenTelemetry + Prometheus (internal `/metrics`)
- **Tracing:** OpenTelemetry + Jaeger (sampled at 10%)
- **Logs:** Structlog + OpenTelemetry + Loki (correlated with traces)
- **Deployment:** Kubernetes manifests in `k8s/`



---

### 12. (TD-007) Frontend Linting & Code Quality Enforcement

**Current State:**
- Backend has `.pre-commit-config.yaml` with Ruff linting
- Frontend has **no** pre-commit hooks or linting enforcement
- No consistent code formatting

**Risk:**
- Code quality drift
- Inconsistent formatting across contributors
- Bugs that linters would catch

**Proposed Solution for Discussion:**

#### Setup ESLint + Prettier + Husky

```json
// package.json additions
{
  "devDependencies": {
    "eslint": "^9.0.0",
    "@typescript-eslint/eslint-plugin": "^8.0.0",
    "@typescript-eslint/parser": "^8.0.0",
    "prettier": "^3.0.0",
    "husky": "^9.0.0",
    "lint-staged": "^15.0.0"
  },
  "scripts": {
    "lint": "eslint . --ext ts,tsx",
    "format": "prettier --write \"**/*.{ts,tsx,json,md}\"",
    "prepare": "husky install"
  }
}
```

#### Pre-commit Hook
```bash
# .husky/pre-commit
npm run lint
npm run format
```

**Assessment Results (2025-12-21):**

Ran strict ESLint + TypeScript on current codebase:
- **ESLint**: 13 errors across 4 files
  - 8× `no-explicit-any` (mostly in VoiceAssistant.tsx with Gemini SDK)
  - 5× `no-unused-vars` (simple cleanup)
- **TypeScript --strict**: 50+ errors, but mostly due to missing `@types/react`

**Decision: ✅ Phased Approach (Not Strict Upfront)**

The codebase is relatively clean (only 13 linting issues). Enforcing strict rules immediately would be too aggressive for experimental features like voice assistant.

**Phase 1: Foundation (Week 1)**
- Install missing type definitions (`@types/react`, `@types/react-dom`)
- Add Prettier for consistent formatting
- Add commitlint for conventional commit enforcement
- Fix 5 unused import errors

**Phase 2: Gradual Strictness (Week 2-3)**
- Add ESLint with **warnings** (not errors) for `any` types
- Fix 2 easy `any` errors in `api.ts` and `AuthForm.tsx`
- Leave VoiceAssistant `any` types temporarily (complex Gemini SDK)

**Phase 3: Full Enforcement (Month 2)**
- Enable strict TypeScript mode
- Properly type Gemini SDK interactions
- Add pre-commit hooks that block on errors

**Rationale:**
- Backend can be stricter (Python + Ruff are simpler)
- Frontend has external SDKs with complex types
- Voice assistant is experimental/AI-generated code
- Incremental improvement > all-or-nothing

---

## Architectural Decisions Summary

> [!NOTE]
> Individual architectural decisions are documented in [ADRs](adr/).
> See [ADR Index](adr/README.md) for the complete list (ADR-001 through ADR-009).

---

## Technical Debt & Roadmap

> [!NOTE]
> Technical debt registry and evolution roadmap are maintained in [ROADMAP.md](ROADMAP.md).

---

## Cross-References

- [Backend README](../README.md)
- [Agent Context](../AGENTS.md)
- [Project Roadmap](ROADMAP.md)
- [ADRs](adr/)
- [API Documentation](https://to-do-4w0k.onrender.com/docs)
- [Frontend Repository](https://github.com/sajankp/to-do-frontend)

---

*This document should be updated when architectural decisions are made or pitfalls are addressed.*
