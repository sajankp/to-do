# Architecture Decision Records (ADR)

This directory contains records of significant architectural decisions made during the development of FastTodo.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. This helps understand why certain choices were made and their trade-offs.

## ADR Format

Each ADR follows this structure:
- **Title**: Short noun phrase
- **Status**: Proposed, Accepted, Deprecated, or Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision
- **Decision**: What is the change that we're actually proposing or doing
- **Consequences**: What becomes easier or more difficult as a result

## Index of ADRs

1. [ADR-001: Use FastAPI as Web Framework](001-fastapi-framework.md)
2. [ADR-002: Use MongoDB as Primary Database](002-mongodb-database.md)
3. [ADR-003: Migrate to Pydantic v2](003-pydantic-v2-migration.md)
4. [ADR-004: JWT-Based Authentication Strategy](004-jwt-authentication.md)
5. [ADR-005: Docker Multi-Stage Build with Non-Root User](005-docker-security.md)
6. [ADR-006: Pytest with Coverage for Testing](006-pytest-testing.md)
7. [ADR-007: Rate Limiting Implementation](007-rate-limiting.md)
8. [ADR-008: Gemini API Backend Proxy](008-gemini-api-backend-proxy.md)
9. [ADR-009: Add Todo Completion Status](009-add-todo-completion-status.md)

## How to Use

When making significant architectural decisions:
1. Create a new ADR file with the next number
2. Follow the ADR template format
3. Update this README with the new entry
4. Commit the ADR along with the implementation

## Related Resources

- [Main README](../../README.md)
- [Agent Context](../../AGENTS.md)
- [Test Plan](../test-plan.md)
