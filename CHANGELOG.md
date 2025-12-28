# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Spec-Driven Development workflow with feature specs in `docs/specs/`
- Documentation index at `docs/README.md`
- Troubleshooting guide at `docs/TROUBLESHOOTING.md`

### Changed
- Refactored user registration to use JSON body instead of query parameters (security fix)
- Consolidated documentation structure with cross-references

### Fixed
- Security: Password no longer exposed in query strings during registration

---

## [0.1.0] - 2025-12-28

### Added
- **Core Features**
  - FastAPI project with Pydantic v2 models
  - MongoDB integration with connection pooling
  - Todo CRUD operations with user isolation
  - User registration and authentication

- **Authentication & Security**
  - JWT-based authentication (access + refresh tokens)
  - Secure password hashing with bcrypt
  - Rate limiting on authentication endpoints (5/minute)
  - CORS middleware with configurable origins

- **Infrastructure**
  - Docker containerization (non-root, minimal base image)
  - CI/CD pipeline with GitHub Actions
  - Pre-commit hooks (Ruff linting, conventional commits)

- **Documentation**
  - ADRs for all architectural decisions (ADR-001 through ADR-009)
  - Comprehensive ARCHITECTURE.md specification
  - AGENTS.md quick reference for AI agents
  - Test plan and troubleshooting guides

- **Testing**
  - Comprehensive test suite with 80%+ coverage
  - Integration tests for user-todo associations
  - Automated coverage reporting

### Technical Decisions
- See [ADRs](docs/adr/) for rationale behind:
  - FastAPI framework selection (ADR-001)
  - MongoDB as database (ADR-002)
  - Pydantic v2 migration (ADR-003)
  - JWT authentication approach (ADR-004)
  - Docker security practices (ADR-005)

---

[Unreleased]: https://github.com/sajankp/to-do/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sajankp/to-do/releases/tag/v0.1.0
