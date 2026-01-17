# Spec-004: Structured Logging with Structlog

**Status:** Approved
**Related Issue:** TD-004
**Effort:** 1 Day

---

## Problem Statement

Currently, the application uses Python's standard `logging` module with default formatting. This presents several issues in a production environment:
1.  **Parsing Difficulty:** Plain text logs are hard to parse programmatically by log aggregators (like ELK, Datadog, or Grafana Loki).
2.  **Missing Context:** It's difficult to correlate logs across a single request (missing Request IDs) or trace user actions.
3.  **Inconsistent Format:** Third-party libraries (uvicorn, pymongo) have their own logging formats, making the logs messy.

## Proposed Solution

Replace the standard logging configuration with **structlog** to implement structured, JSON-formatted logging.

### Key Features
1.  **JSON Output:** Logs will be output as JSON objects in production.
2.  **Pretty Printing:** Colorful human-readable logs for local development.
3.  **Session Tracking:**
    -   Implement `sid` (Session ID) claim in JWTs.
    -   Log `sid` instead of `user_id` to balance observability with privacy.
4.  **Context Binding:** Bind `request_id`, `sid`, `method`, `path`, and `client_ip` to log entries.

---

## Implementation Plan

### 1. Dependencies
Add `structlog` to `requirements.txt`.

### 2. Auth Updates (`app/routers/auth.py`)
-   Update `create_token` to accept an optional `sid`.
-   If no `sid` is provided (new login), generate a UUID4.
-   Include `sid` in the JWT payload.

### 3. Configuration (`app/utils/logging.py`)
Create a central logging configuration module that:
-   Configures `structlog` processors.
-   Configures standard library logging to sink into structlog.
-   Switches between `ConsoleRenderer` (Dev) and `JSONRenderer` (Prod).

### 4. Middleware (`app/middleware/logging.py`)
Implement `StructlogMiddleware` that:
-   Generates `request_id` (UUID).
-   Extracts `sid` from the JWT (if present).
-   Binds context variables.
-   Logs request start/finish.

### 5. Integration (`app/main.py`)
-   Initialize logging on startup.
-   Add the middleware.

---

## Verification Plan

### Automated Tests
- Verify that the middleware adds `request_id` to response headers.
- Verify that logs are captured and contain expected keys (mocking stdout/stderr).

### Manual Verification
- **Local Dev:** Run `uvicorn`, interact with API, and verify pretty colorful logs in terminal.
- **Production Simulation:** Set `ENV=production`, run app, and verify logs are single-line JSON objects.
