# Project Roadmap

> **Philosophy:** Security and stability first, then architecture, then features.
> This project prioritizes production-readiness over feature velocity.

## Current Focus

**Phase 1: Production Readiness** - Ensuring the API is secure and observable before adding features.

---

## Phases

### Phase 0: Foundation ✅ Completed

| Category | Item | Status |
|----------|------|--------|
| **Core** | FastAPI project setup with Pydantic v2 | ✅ |
| **Core** | MongoDB integration with connection pooling | ✅ |
| **Core** | Todo CRUD operations with user isolation | ✅ |
| **Auth** | JWT authentication with refresh tokens | ✅ |
| **Auth** | Secure password hashing (bcrypt) | ✅ |
| **Auth** | Rate limiting on auth endpoints | ✅ |
| **Security** | CORS middleware with configurable origins | ✅ |
| **Security** | User data isolation enforcement | ✅ |
| **Infra** | Docker containerization (non-root, multi-stage) | ✅ |
| **Infra** | CI/CD with GitHub Actions | ✅ |
| **Quality** | Pre-commit hooks (Ruff linting/formatting) | ✅ |
| **Quality** | 80%+ test coverage achieved | ✅ |
| **Docs** | Spec-Driven Development workflow | ✅ |
| **Docs** | ADRs for architectural decisions | ✅ |


---

### Phase 1: Stability & Production Readiness ⬅️ Current

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| TD-003 | Security headers middleware (OWASP) | 4 hours | ✅ |
| TD-004 | Structured logging (structlog + configurable level) | 1 day | ✅ |
| TD-005 | Monitoring/Observability (OpenTelemetry + Prometheus) | 3-5 days | ✅ |
| TD-002 | Database indexes | 1 hour | 🔲 |
| TD-012 | Move password to request body | 2 hours | ✅ |
| TD-013 | Email uniqueness check | 1 hour | 🔲 |
| TD-006 | Gemini API backend proxy | 2 days | ✅ |
| TD-011 | Frontend token refresh | 1 day | 🔲 |

---

### Phase 2: Architecture (Short-term)

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| TD-001 | Migrate to Motor (async MongoDB) | 3 days | 🔲 |
| TD-008 | Repository pattern | 5 days | 🔲 |
| TD-009 | Service layer | 3 days | 🔲 |
| TD-010 | Frontend testing infrastructure | 2 days | 🔲 |
| TD-007 | Frontend linting Phase 1 | 2 hours | 🔲 |

---

### Phase 3: Features (Medium-term)

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| - | Email verification | 2 days | 🔲 |
| - | Password reset | 1 day | 🔲 |
| - | Pagination | 4 hours | 🔲 |
| TD-014 | API versioning | 2 days | 🔲 |
| TD-007a/b | Frontend linting Phase 2 & 3 | 12 hours | 🔲 |

---

### Phase 4: Advanced (Long-term)

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| - | 2FA & OAuth | 5 days | 🔲 |
| TD-015 | HttpOnly cookie tokens | 2 days | 🔲 |
| - | Kubernetes deployment | 3 days | 🔲 |
| - | Advanced dashboards & alerting | 2 days | 🔲 |

---

### Phase 5: Testing & Quality Assurance

> **Goal:** Comprehensive testing strategy following the industry-standard Testing Pyramid.
> Maximum reliability through layered testing and CI gates.

#### Testing Pyramid Overview

```
        ┌─────────────────┐
        │   E2E Tests     │  ← Slowest, run on main merge
        │  (Playwright)   │
        ├─────────────────┤
        │  Integration    │  ← Medium, run on PRs
        │  Tests (Real DB)│
        ├─────────────────┤
        │   Unit Tests    │  ← Fastest, run on every push
        │ (Mocked deps)   │
        └─────────────────┘
```

#### Testing Items

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| TD-022 | Integration tests with testcontainers (MongoDB) | 2 days | 🔲 |
| TD-016 | E2E testing with Playwright (full stack) | 2 days | 🔲 |
| TD-017 | Performance benchmarks (Locust/k6) | 1 day | 🔲 |
| TD-018 | OpenAPI contract testing | 1 day | 🔲 |
| TD-023 | CI gate: Integration tests on PR | 4 hours | 🔲 |
| TD-024 | CI gate: E2E tests on main merge | 4 hours | 🔲 |
| TD-025 | Nightly full test suite (scheduled) | 2 hours | 🔲 |

#### CI Gate Strategy

| Trigger | Unit Tests | Integration Tests | E2E Tests |
|---------|------------|-------------------|------------|
| Every push | ✅ Required | ❌ Skip | ❌ Skip |
| Pull Request | ✅ Required | ✅ Required | ❌ Skip |
| Merge to main | ✅ Required | ✅ Required | ✅ Required |
| Nightly scheduled | ✅ Required | ✅ Required | ✅ Required |
| Pre-release tag | ✅ Required | ✅ Required | ✅ Required |

---

### Phase 6: Portfolio Polish

> **Goal:** Demonstrate senior-level engineering practices for portfolio presentation.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| TD-019 | Standardized error responses (RFC 7807) | 4 hours | 🔲 |
| TD-020 | Database migration strategy | 2 days | 🔲 |
| TD-021 | Security audit logging | 4 hours | 🔲 |
| - | Demo video/GIF for README | 1 hour | 🔲 |
| - | React Query integration (frontend) | 1 day | 🔲 |
| - | Error Boundaries (frontend) | 2 hours | 🔲 |

---

## Technical Debt Registry

> Full details for each item are documented in [ARCHITECTURE.md](ARCHITECTURE.md#known-architectural-pitfalls).

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-001 | Migrate to async Motor | High | 3 days |
| TD-002 | Add database indexes | High | 1 hour |
| TD-003 | Security headers middleware | High | ✅ Complete |
| TD-004 | Structured logging (structlog + configurable level) | High | ✅ Complete |
| TD-005 | Monitoring/Observability (OpenTelemetry) | Critical | ✅ Complete |
| TD-006 | Gemini API backend proxy | High | ✅ Complete |
| TD-007 | Frontend linting - Phase 1 | High | 2 hours |
| TD-007a | Frontend linting - Phase 2 | Medium | 4 hours |
| TD-007b | Frontend linting - Phase 3 | Low | 8 hours |
| TD-008 | Repository pattern | Medium | 5 days |
| TD-009 | Service layer | Medium | 3 days |
| TD-010 | Frontend testing setup | Medium | 2 days |
| TD-011 | Token refresh | Medium | 1 day |
| TD-012 | Move password to request body | Done | ✅ Complete |
| TD-013 | Email uniqueness check | Low | 1 hour |
| TD-014 | API versioning | Low | 2 days |
| TD-015 | HttpOnly cookie tokens | Low | 2 days |
| TD-016 | E2E testing (Playwright) | High | 2 days |
| TD-017 | Performance benchmarks | Medium | 1 day |
| TD-018 | OpenAPI contract testing | Medium | 1 day |
| TD-019 | Standardized errors (RFC 7807) | Medium | 4 hours |
| TD-020 | Database migration strategy | Medium | 2 days |
| TD-021 | Security audit logging | Medium | 4 hours |
| TD-022 | Integration tests (testcontainers) | High | 2 days |
| TD-023 | CI gate: Integration on PR | High | 4 hours |
| TD-024 | CI gate: E2E on main merge | High | 4 hours |
| TD-025 | Nightly full test suite | Medium | 2 hours |

---

## Prioritization Rationale

**Why Security/Stability First?**
- Addressing security issues after launch is 10x more costly
- Observability enables faster debugging of future issues
- Stable foundation enables confident feature development

**Why Repository Pattern Before Features?**
- Clean architecture makes features easier to add
- Testing is simpler with proper separation of concerns
- Technical debt compounds if architecture is neglected

---

*Last updated: 2026-02-15*
