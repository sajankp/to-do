# 2. Rate Limiting Strategy

Date: 2025-11-26

## Status

Accepted

## Context

The application was vulnerable to brute force attacks on authentication endpoints and potential denial-of-service (DoS) attacks on API endpoints. We needed a mechanism to limit the number of requests a user or IP can make within a specific time window.

## Decision

We decided to implement rate limiting using the `slowapi` library, which is a port of Flask-Limiter for FastAPI.

### Key Decisions:

1.  **Library Choice**: `slowapi` was chosen because it integrates seamlessly with FastAPI/Starlette, supports various storage backends (Memory, Redis, Memcached), and offers flexible configuration (decorators, global limits).
2.  **Storage**: We use in-memory storage for development/testing and support Redis for production via the `REDIS_URL` environment variable.
3.  **Identification Strategy**:
    *   **Authenticated Users**: Rate limits are applied based on the `user_id` extracted from the JWT token.
    *   **Anonymous Users**: Rate limits are applied based on the IP address.
4.  **Limits**:
    *   **Auth Endpoints** (`/token`, `/user`): Strict limit (default 5/minute) to prevent brute force.
    *   **API Endpoints** (`/todo`): Moderate limit (default 100/minute) to ensure fair usage and prevent abuse.
5.  **Configuration**: Limits are configurable via environment variables (`RATE_LIMIT_AUTH`, `RATE_LIMIT_DEFAULT`).
6.  **Middleware**: We use `SlowAPIMiddleware` to enforce global default limits on all endpoints, while specific decorators are used for stricter limits on auth endpoints.
7.  **Headers**: Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) are disabled on successful responses to avoid compatibility issues with endpoints returning dictionaries (FastAPI automatically converts them to JSONResponse, but `slowapi` middleware runs before that). Headers are present on 429 responses.

## Consequences

### Positive
*   **Security**: significantly reduced risk of brute force and DoS attacks.
*   **Stability**: System is protected from traffic spikes.
*   **Flexibility**: Easy to adjust limits without code changes.

### Negative
*   **Complexity**: Added dependency (`slowapi`, `redis`).
*   **UX**: Users might encounter 429 errors if they exceed limits (client should handle this).
*   **Testing**: Tests need to mock rate limiting or handle 429 responses.

## Implementation Details

*   `app/utils/rate_limiter.py`: Centralized configuration and `Limiter` instance.
*   `app/main.py`: Middleware integration and exception handler.
*   `app/routers`: Decorators applied to specific endpoints.
